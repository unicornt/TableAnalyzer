import os
from openai import OpenAI
from flask import Flask, request, jsonify, send_file, send_from_directory
import base64
import io
import magic
import time
import random
import string
from flask_cors import CORS
import json
from pathlib import Path

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


class ExcelToDuckDB:
    def __init__(self, excel_file):
        self.excel_file = excel_file
        self.fields = []
        self.data_types = []

    def parse_excel(self, sheet_name=0):
        """
        解析 Excel 表中的第一行特征字段和数据类型。
        """
        # 读取 Excel 文件
        self.df = pd.read_excel(self.excel_file, sheet_name=sheet_name)

        # 获取字段名称
        self.fields = list(self.df.columns)

        # 推断字段的数据类型
        for field in self.fields:
            sample_type = self.df[field].dropna().iloc[0] if not self.df[field].dropna().empty else ""
            if isinstance(sample_type, int):
                self.data_types.append("INTEGER")
            elif isinstance(sample_type, float):
                self.data_types.append("FLOAT")
            elif isinstance(sample_type, str):
                self.data_types.append("TEXT")
            else:
                self.data_types.append("TEXT")  # 默认类型

    def create_duckdb_table(self, table_name="excel_table"):
        """
        根据解析的字段和数据类型创建 DuckDB 表。
        """
        if not self.fields or not self.data_types:
            raise ValueError("请先调用 parse_excel 方法解析字段和数据类型。")

        # 创建 DuckDB 表的 SQL 语句
        columns_definition = ", ".join(
            f"{field} {data_type}" for field, data_type in zip(self.fields, self.data_types)
        )
        create_table_sql = f"CREATE TABLE {table_name} ({columns_definition});"

        # 执行 SQL 语句创建表
        self.conn = duckdb.connect()
        self.conn.execute(create_table_sql)
        print(f"DuckDB 表 {table_name} 创建成功。")
        return self.conn

    def insert_data_into_duckdb(self, table_name="excel_table"):
        """
        将 Excel 数据插入到 DuckDB 表中。
        """
        if not hasattr(self, 'df') or self.df is None:
            raise ValueError("请先调用 parse_excel 方法读取 Excel 数据。")
        if not hasattr(self, 'conn') or self.conn is None:
            raise ValueError("请先调用 create_duckdb_table 方法创建 DuckDB 表。")

        # 转换数据为适合插入的格式
        for index, row in self.df.iterrows():
            values = tuple(row.values)
            placeholders = ", ".join(["?" for _ in values])
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders});"
            self.conn.execute(insert_sql, values)

        print(f"Excel 数据成功插入到 DuckDB 表 {table_name} 中。")


client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)
font_file = client.files.create(
    file=open("NotoSansCJK-Regular.ttc", "rb"),
    purpose='user_data'
)

# 初始化 Flask 应用
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app) # 允许跨域请求
SERVER_IP = os.getenv('SERVER_IP')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # 接收上传的文件
        file = request.files['file']
        print(file)
        suff = Path(file.filename).suffix
        timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    
        # 生成一个随机的字符串（可自定义长度）
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        
        # 组合时间戳和随机字符串，确保文件名唯一
        filename = f"{timestamp}_{random_str}{suff}"
        with open(f"{UPLOAD_FOLDER}/{filename}", "wb") as f:
            f.write(file.read())
        print(f"Save file to {filename}")
        return jsonify({'code': 1, 'message': "success", 'data': {'file_url': f"{SERVER_IP}/uploads/{filename}"}}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/chat/completions', methods=['POST'])
def response():
    # print(request.data)
    data = request.get_json()
    print(data)
    messages = data.get('messages', [])
    instruction = None
    file_url = None
    file_type = None
    global client
    global font_file
    for message in messages:
        if message.get("role", "") != "user":
            continue
        content = message.get("content", "")
        if isinstance(content, str):
            instruction = content
            break
        for item in content:
            # print(item)
            if item['type'] == 'text':
                instruction = item['text']
            elif item['type'] == 'image':
                file_url = UPLOAD_FOLDER+"/"+os.path.basename(item['file'])
                file_type = 0
            elif item['type'] == 'table':
                file_url = UPLOAD_FOLDER+"/"+os.path.basename(item['file'])
                file_type = 1
        print(f"User Instruction: {instruction}")
        print(f"URL: {file_url}")
        # print(f"Table URL: {file_url}")

    if file_url != None:
        # file_extension = uploaded_file.filename.split('.')[-1].lower()
        try:
            print(f"File type is {file_type}")
            # 从请求中获取指令和文件 ID
            if file_type == 1:
                print("Table file")
                excel_to_duckdb = ExcelToDuckDB(file_url)
                excel_to_duckdb.parse_excel()

                # 创建 DuckDB 表
                conn=excel_to_duckdb.create_duckdb_table(table_name="test_table")
                excel_to_duckdb.insert_data_into_duckdb("test_table")

                def gen_chart(user_input):
                    ## 获取表字段信息
                    table_info = conn.execute("PRAGMA table_info('test_table');").fetchall()

                    # 提取前三个字段
                    filtered_table_info = [(row[0], row[1], row[2]) for row in table_info]

                    from openai import OpenAI
                    import os

                    client = OpenAI(
                        api_key=os.getenv('OPENAI_API_KEY')
                    )
                    from jinja2 import Template
                    def get_title_sql(filtered_table_info, user_input, table_name):
                        """
                        :user_input
                        :return: 生成的响应内容
                        """

                        # 定义对话模板
                        _DEFAULT_RESULT_ZH = """
                        
                        你是一个非常严谨的数据分析专家,同时精通duckdb的使用。请结合已知duckdb表数据的结构信息，在满足下面约束条件下， 生成对应的 duckdb sql 数据分析。
                    约束条件:
                        1.请充分理解用户的问题，使用duckdb sql的方式进行分析， 分析内容按下面要求的输出格式返回，sql请输出在对应的sql参数中
                        2.重点 ：请检查你生成的sql，不要使用没在数据结构中的表名 和 字段 ，不得修改和使用不存在的表数据的结构 和 字段
                        3.优先使用数据分析的方式回答，如果用户问题不涉及数据分析内容，你可以按你的理解进行回答
                        4.输出内容中sql部分转换为：<name>[数据展示方式]</name><sql>[正确的duckdb数据分析sql]</sql> 这样的格式，参考返回格式要求
                        5.保证查询结果的字段个数等于2。
                        6.每个字段的查询结果为数字的情况下，应该按照从小到大的顺序排列。如果两个字段的结果均为数字，以第一个字段为准排序。
                        7.数据展示方式包括：折线图、柱状图、散点图、饼图
                        
                    请一步一步思考，给出结果，无需输出其他解释信息，并确保你的结果内容格式如下:
                        <name>[数据展示方式]</name><sql>[正确的duckdb数据分析sql]</sql>

                    已知表名 和 字段如下：
                        表名 ：
                        {{table_name}}
                        字段：
                        {{filtered_table_info}}

                    用户问题：{{user_input}}  ， 请使用上述已知 表名 和  字段 ，生成对应可执行的的sql语句。

                    请自己检查生成的sql语句中所有字段是否与 duckdb表的字段 中的一致，表名是一致， 否则你将收到惩罚 ，并重新生成。
                        
                        """
                        
                        # 渲染模板
                        template = Template(_DEFAULT_RESULT_ZH).render(filtered_table_info = filtered_table_info,  user_input=user_input,table_name=table_name)
                        
                        # 调用模型进行聊天
                        response = client.chat.completions.create(
                        messages=[
                            {"role": "user", "content": template},
                        ],
                        model="gpt-4o",
                    )
                        return response.choices[0].message.content.replace("&gt;", ">").replace("&lt;", "<")

                    # user_input = request.get_json()['input']

                    table_name = "test_table"
                    title_sql = get_title_sql(filtered_table_info, user_input,table_name)
                    print(title_sql)

                    # 解析sql函数
                    import re

                    def parse_fixed_structure(input_str):
                        """
                        解析固定结构字符串，提取 name 和 sql 内容，保存为键值对。
                        
                        :param input_str: 待解析的字符串
                        :return: 包含 name 和 sql 的字典
                        """
                        # 定义正则表达式模式
                        name_pattern = r"<name>(.*?)</name>"
                        sql_pattern = r"<sql>(.*?)</sql>"

                        # 提取 name 和 sql
                        name_match = re.search(name_pattern, input_str)
                        sql_match = re.search(sql_pattern, input_str, re.DOTALL)  # 使用 re.DOTALL 处理多行匹配

                        # 构造结果字典
                        result = {
                            "name": name_match.group(1) if name_match else None,
                            "sql": sql_match.group(1).strip() if sql_match else None  # 去除多余的换行和空格
                        }
                        return result

                    result = parse_fixed_structure(title_sql)
                    print(result["name"],result["sql"])

                    import re

                    def parse_sql_fields(sql):
                        """
                        解析 SQL 语句中的查询字段。

                        :param sql: SQL 查询语句，例如 "SELECT Day, AvgTemperature FROM test_table;"
                        :return: 包含字段名的数组，例如 ['Day', 'AvgTemperature']
                        """
                        # 使用正则表达式提取 SELECT 和 FROM 之间的字段部分
                        match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE | re.DOTALL)
                        if not match:
                            raise ValueError("无法解析 SQL 语句，确保语句格式为 'SELECT ... FROM ...'")
                        
                        # 获取字段部分并去除空格
                        fields_part = match.group(1).strip()

                        # 将字段按逗号分隔，去除每个字段的多余空格
                        fields = [field.strip() for field in fields_part.split(',')]
                        return fields

                    # 字段
                    fields = parse_sql_fields(result["sql"])
                    print(fields)

                    # 数据
                    data = conn.execute(result["sql"]).fetchall()
                    print(data)

                    # 渲染函数
                    import matplotlib.pyplot as plt
                    from mpl_toolkits.mplot3d import Axes3D
                    from matplotlib.ticker import MaxNLocator

                    def get_graph_code(tab_name, file_name):
                        """
                        :user_input
                        :return: 生成的响应内容
                        """

                        # 定义对话模板
                        _DEFAULT_RESULT_ZH = """
                        
                        你是一个非常严谨的程序员,精通python3和matplotlib的使用。请根据给定数据，在满足下面约束条件下， 生成一段python3代码来生成要求的图表。
                    约束条件:
                        1.严格遵循要求的数据展示方式，数据展示方式将包括：折线图、柱状图、散点图、饼图。
                        2.如果展示方式为折线图、柱状图或者散点图，确保横轴和纵轴上展示的标签个数不超过6个，建议使用matplotlib.ticker包中的MaxNLocator。
                        3.重点：你不需要在代码中定义x和y，这两个变量已经被定义，你可以在代码中直接使用这两个类型为list的变量。
                        4.检查x和y中的元素是否为浮点数。如果是，则添加代码将数据精确到小数点后两位。
                        5.结合用户的要求并根据这两组数据的字段名称，选择合适的中文横纵坐标名和图表标题，请注意都需要是中文。
                        6.重点：输出内容不要包含markdown语法，内容的格式严格按照：<name>[图表标题]</name><python>[正确的python3代码]</python> 这样的格式，参考返回格式要求。
                        7.重点：添加这条语句以保证生成的图片兼容中文： plt.rcParams['font.family'] = fm.FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name()
                        8.设置figsize为(10, 8)。
                        9.不需要显示图片，即删除“plt.show()”这句代码，将图片储存在"{file_name}"中
                        
                    请一步一步思考，给出结果，无需输出其他解释信息，并确保你的结果内容格式如下:
                        <name>[图表标题]</name><python>[正确的python3代码]</python>

                    已知数据展示类型如下：
                        用户的要求：
                        {{user_input}}
                        数据展示类型 ：
                        {{tab_name}}
                        x轴数据的字段名称：
                        {{fields[0]}}
                        y轴数据的字段名称：
                        {{fields[1]}}

                    用户问题：根据已知数据，生成一段python3代码，该代码可以生成以列表x为横轴，列表y为纵轴的图表，图表类型按照数据展示类型的要求，横纵坐标轴的名称和图表标题都需要是中文。

                    请自己检查生成的python3代码是否合法，同时不要定义x和y，否则你将收到惩罚 ，并重新生成。
                        
                        """
                        
                        # 渲染模板
                        template = Template(_DEFAULT_RESULT_ZH).render(tab_name=tab_name, fields=fields)
                        
                        # 调用模型进行聊天
                        response = client.chat.completions.create(
                        messages=[
                            {"role": "user", "content": template},
                        ],
                        model="gpt-4o",
                    )
                        return response.choices[0].message.content.replace("&gt;", ">").replace("&lt;", "<")
                    
                    # 二维数据结果渲染
                    def parse_fixed_python_structure(input_str):
                        """
                        解析固定结构字符串，提取 name 和 python 内容，保存为键值对。
                        
                        :param input_str: 待解析的字符串
                        :return: 包含 name 和 python 的字典
                        """
                        # 定义正则表达式模式
                        name_pattern = r"<name>(.*?)</name>"
                        python_pattern = r"<python>(.*?)</python>"

                        # 提取 name 和 sql
                        name_match = re.search(name_pattern, input_str)
                        python_match = re.search(python_pattern, input_str, re.DOTALL)  # 使用 re.DOTALL 处理多行匹配

                        # 构造结果字典
                        result = {
                            "name": name_match.group(1) if name_match else None,
                            "python": python_match.group(1).strip() if python_match else None  # 去除多余的换行和空格
                        }
                        return result

                    title = result["name"]
                    timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
                    random_str = timestamp+''.join(random.choices(string.ascii_letters + string.digits, k=4))+".png"
                    result = get_graph_code(title, random_str)
                    parse_result = parse_fixed_python_structure(result)
                    print(parse_result['python'])
                    x = [item[0] for item in data]  # 转换为字符串类型，适用于分类轴
                    y = [item[1] for item in data]
                    # img=None
                    exec(parse_result['python'])
                
                    # 生成一个随机的字符串（可自定义长度）
                    return random_str
                image_path = gen_chart(instruction)
                image_data_bytes = open(image_path, "rb").read()
                mime = magic.Magic(mime=True)
                mime_type = mime.from_buffer(image_data_bytes)
                base64_image = base64.b64encode(image_data_bytes).decode("utf-8")
                # 返回生成的图像
                return jsonify({"choices": [
                    {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": str("按照要求为您生成了图片，请查看。")+f"<BZIMAGE>data:{mime_type};base64,{base64_image}",
                        "refusal": None
                    },
                    "logprobs": None,
                    "finish_reason": "stop"
                    }
                ]})
            elif file_type == 0:
                image_data_bytes = open(file_url, "rb").read()
                mime = magic.Magic(mime=True)
                mime_type = mime.from_buffer(image_data_bytes)
                base64_image = base64.b64encode(image_data_bytes).decode("utf-8")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": instruction,
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                                },
                            ],
                        }
                    ],
                )
                print(f"data:{mime_type};base64,{base64_image}")
                print(response)
                return jsonify({"choices": [
                        {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": str(response.choices[0].message.content),
                            "refusal": None
                        },
                        "logprobs": None,
                        "finish_reason": "stop"
                        }
                    ]})
                # return jsonify({"type": "message", 'message': str(response.choices[0].message.content)}), 200
            else:
                return jsonify({
                    "object": "error",
                    "message": str(e),
                    "type": 'Unsupported file type',
                    "param": None,
                    "code": 400
                    })
                # return jsonify({'error': 'Unsupported file type'}), 400
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({
                "object": "error",
                "message": str(e),
                "type": "NotFoundError",
                "param": None,
                "code": 400
                })
    else:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": instruction,
                            },
                        ],
                    }
                ],
            )
            print(response)
            # print(response.choices[0].message.content)
            return jsonify({"choices": [
                        {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": str(response.choices[0].message.content),
                            "refusal": None
                        },
                        "logprobs": None,
                        "finish_reason": "stop"
                        }
                    ]})
            # return jsonify({"type": "message", 'message': str(response.choices[0].message.content)}), 200
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({
                "object": "error",
                "message": str(e),
                "type": "NotFoundError",
                "param": None,
                "code": 400
                })
            # return jsonify({'error': }), 400

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
