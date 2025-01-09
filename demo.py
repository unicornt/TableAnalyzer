import requests

# 发送Excel文件到/generate_image
def send_excel_to_generate_image(excel_file_path):
    url = 'http://127.0.0.1:5001/upload_excel'
    with open(excel_file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        print("Send file Success")
    else:
        print("Error:", response.json())

# 发送字符串到/generate_chart并接收返回的图像
def send_string_to_generate_chart(description):
    url = 'http://127.0.0.1:5001/generate_chart'
    payload = {'input': description}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        with open('generated_chart.png', 'wb') as img_file:
            img_file.write(response.content)
        print("Chart saved as 'generated_chart.png'")
    else:
        print("Error:", response.json())

# 使用例子
excel_file_path = 'data/student_grades.xlsx'
send_excel_to_generate_image(excel_file_path)

description = "展示总评75分以上的学生数量按成绩的分布"
send_string_to_generate_chart(description)
