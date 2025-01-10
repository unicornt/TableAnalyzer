import os
from openai import OpenAI
from flask import Flask, request, jsonify, send_file
import base64
import io
import magic
import time
import random
import string

# 初始化 Flask 应用
app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # 接收上传的文件
        file = request.files['file']
        timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
    
        # 生成一个随机的字符串（可自定义长度）
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        
        # 组合时间戳和随机字符串，确保文件名唯一
        filename = f"{timestamp}_{random_str}"
        with open(filename, "wb") as f:
            f.write(file.read())
        return jsonify({'code': 1, 'message': "success", 'data': {'file_url': filename}}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/chat', methods=['POST'])
def response():
    global mime_type
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY')
    )
    data = request.get_json()
    messages = data.get('messages', [])
    content = messages[0].get("content", "")
    instruction = None
    file_url = None
    file_type = None
    for item in content:
        if item['type'] == 'text':
            instruction = item['text']
            print(f"User Instruction: {instruction}")
        elif item['type'] == 'image':
            file_url = item['file_url']
            file_type = 0
            print(f"Image URL: {file_url}")
        elif item['type'] == 'table':
            file_url = item['file_url']
            file_type = 1
            print(f"Table URL: {file_url}")
    if file_url != None:
        if mime_type == None:
            return jsonify({'error': 'No file uploaded'}), 400
        # file_extension = uploaded_file.filename.split('.')[-1].lower()
        try:
            # 从请求中获取指令和文件 ID
            if file_type == 1:
                # 将文件上传到 OpenAI 服务器
                file = client.files.create(
                    file=open(file_url, "rb"),
                    purpose='assistants'
                )
                font_file = client.files.create(
                    file=open("NotoSansCJK-Regular.ttc", "rb"),
                    purpose='user_data'
                )

                # Create an assistant using the file ID
                assistant = client.beta.assistants.create(
                    instructions="你是一个非常严谨的数据分析专家。下面你会就这个表格被提出一些可视化的要求，表格类型为{mime_type}，请按照要求根据表格中的内容编写代码以生成可视化的图表。",
                    model="gpt-4o",
                    tools=[{"type": "code_interpreter"}],
                    tool_resources={
                        "code_interpreter": {
                            "file_ids": [file.id]
                        }
                    }
                )
                # 创建一个线程
                thread = client.beta.threads.create()

                # 创建一条消息
                message = client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=instruction,
                    attachments=[{ "file_id": file.id , "tools": [{"type": "code_interpreter"}]}, { "file_id": font_file.id , "tools": [{"type": "code_interpreter"}]}],
                )
                print(message)

                run = client.beta.threads.runs.create_and_poll(
                    thread_id=thread.id,
                    assistant_id=assistant.id,
                    instructions="""
                    请认真对待用户的要求，有以下几点注意事项：
                    1. 可以适当减少展示图片的横纵坐标的标签显示以保证不会过密。
                    2. 标题和坐标的标签尽可能使用中文。
                    3. 重点注意：第二个文件为字体文件，图表生成过程的字体选择该字体文件。
                    4. 第一个文件为表格文件，表格文件类型为{mime_type}。
                    5. 不需要确认文件格式是否正确，如果读取失败直接返回失败提示。
                    """
                )
                print(run)

                messages = client.beta.threads.messages.list( # 查看thread.id中的message
                thread_id=thread.id
                )
                print("===============================")
                print(messages)
                print("===============================")

                messages.data = sorted(messages.data, key=lambda x: x.created_at, reverse=True)

                messages_data = messages.data

                # 获取最后一条消息
                last_message = messages_data[0] if messages_data else None

                # 打印最后一条消息
                print(last_message)
                image_file_ids = []

                for item in last_message.content:
                    if item.type == "image_file":
                        image_file_ids.append(item.image_file.file_id)

                print(image_file_ids)

                image_data = client.files.content(image_file_ids[0])
                image_data_bytes = image_data.read()
                image_io = io.BytesIO(image_data_bytes)
                
                # 返回生成的图像
                return send_file(
                    image_io,
                    mimetype='image/png',  # 或者你可以根据实际文件类型设置
                    as_attachment=True,
                    download_name="generated_image.png"  # 设置下载的文件名
                )
            elif file_type == 0:
                base64_image = base64.b64encode(open(file_url, "rb").read()).decode("utf-8")
                response = client.chat.completions.create(
                    model="gpt-4o",
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
                return jsonify({'message': str(response.choices[0].message.content)}), 200
            else:
                return jsonify({'error': 'Unsupported file type'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
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
            return jsonify({'message': str(response.choices[0].message.content)}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
