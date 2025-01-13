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
                mime = magic.Magic(mime=True)
                mime_type = mime.from_buffer(open(file_url, "rb").read())
                # 将文件上传到 OpenAI 服务器
                file = client.files.create(
                    file=open(file_url, "rb"),
                    purpose='assistants'
                )
                print("upload file to openai")

                # 创建一个线程
                thread = client.beta.threads.create()

                # 创建一条消息
                message = client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=instruction,
                    attachments=[{ "file_id": file.id , "tools": [{"type": "code_interpreter"}]}, { "file_id": font_file.id , "tools": [{"type": "code_interpreter"}]}],
                )
                print("send message, start run")

                run = client.beta.threads.runs.create_and_poll(
                    thread_id=thread.id,
                    assistant_id='asst_fFJuBohoNBuvAwqhHXzZwBDC',
                    instructions=f"""
                    请认真对待用户的要求，有以下几点注意事项：
                    1. 可以适当减少展示图片的横纵坐标的标签显示以保证不会过密。
                    2. 标题和坐标的标签尽可能使用中文。
                    3. 重点注意：第二个文件为字体文件，图表生成过程的字体选择该字体文件。
                    4. 第一个文件为表格文件，表格文件类型为{mime_type}。
                    """
                )
                print("finish run")

                messages = client.beta.threads.messages.list( # 查看thread.id中的message
                    thread_id=thread.id
                )
                print("===============================")
                print("get messages")

                messages.data = sorted(messages.data, key=lambda x: x.created_at, reverse=True)

                messages_data = messages.data

                # 获取最后一条消息
                last_message = messages_data[0] if messages_data else None

                # 打印最后一条消息
                print(last_message)
                print("===============================")
                image_file_ids = []

                for item in last_message.content:
                    if item.type == "image_file":
                        image_file_ids.append(item.image_file.file_id)

                print(image_file_ids)
                if len(image_file_ids) == 0:
                    return jsonify({"choices": [
                        {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": str(last_message.content[0].text.value),
                            "refusal": None
                        },
                        "logprobs": None,
                        "finish_reason": "stop"
                        }
                    ]})
                else:
                    image_data = client.files.content(image_file_ids[0])
                    image_data_bytes = image_data.read()
                    mime = magic.Magic(mime=True)
                    mime_type = mime.from_buffer(image_data_bytes)
                    base64_image = base64.b64encode(image_data_bytes).decode("utf-8")
                    # 返回生成的图像
                    return jsonify({"choices": [
                        {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": str(last_message.content[1].text.value)+f"<BZIMAGE>data:{mime_type};base64,{base64_image}",
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
