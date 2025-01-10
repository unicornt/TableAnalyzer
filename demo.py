import requests
import magic

# 发送Excel文件到/generate_image
def send_excel_to_generate_image(excel_file_path):
    url = 'http://10.177.44.113:5000/upload'
    with open(excel_file_path, 'rb') as f:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(excel_file_path)
        print(mime_type)
        files = {'file': f}
        # print(files['file'].content_type)
        response = requests.post(url, files=files)

    if response.status_code == 200:
        print("Send file Success")
    else:
        print("Error:", response.json())

# 发送字符串到/generate_chart并接收返回的图像
def send_string_to_generate_chart(description):
    url = 'http://10.177.44.113:5000/chat'
    payload = {'user_input': description, 'use_file': 1}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        with open('generated_chart.png', 'wb') as img_file:
            img_file.write(response.content)
        print("Chart saved as 'generated_chart.png'")
    else:
        print("Error:", response.json())

# 发送字符串到/generate_chart并接收返回的图像
def send_string_to_chat(description):
    url = 'http://10.177.44.113:5000/chat'
    payload = {'user_input': description, 'use_file': 0}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print(response.json()['message'])
        # print("Chart saved as 'generated_chart.png'")
    else:
        print("Error:", response.json())

def send_image_to_chat(image_path):
    url = 'http://10.177.44.113:5000/upload'
    with open(image_path, 'rb') as f:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(image_path)
        print(mime_type)
        files = {'file': f}
        # print(files['file'].content_type)
        response = requests.post(url, files=files)

    if response.status_code == 200:
        print("Send file Success")
    else:
        print("Error:", response.json())

def send_string_to_chat_use_img(description):
    url = 'http://10.177.44.113:5000/chat'
    payload = {'user_input': description, 'use_file': 1}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print(response.json()['message'])
        # print("Chart saved as 'generated_chart.png'")
    else:
        print("Error:", response.json())
# 使用例子1:根据表格生成图片
excel_file_path = 'student_grades.csv'
send_excel_to_generate_image(excel_file_path)
description = "展示总评75分以上的学生数量按成绩的分布"
# description = "用折线图展示总评最高的同学所有作业分数的变化"
# # description = "展示各个期末考试和期中考试分差的学生数量分布"
# # description = "就学生总评，从60分开始到100分，每10分为一个区间画个饼图"
send_string_to_generate_chart(description)

# 使用例子2:对话
send_string_to_chat("为我讲个笑话")

# 使用例子3:根据图片生成文字
send_image_to_chat("my-image.png")
send_string_to_chat_use_img("请描述图片中的信息")