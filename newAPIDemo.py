from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

# Upload a file with an "assistants" purpose
file = client.files.create(
    file=open("data/student_grades.xlsx", "rb"),
    purpose='assistants'
)

# Create an assistant using the file ID
assistant = client.beta.assistants.create(
    instructions="你是一个非常严谨的数据分析专家。下面你会就这个表格被提出一些可视化的要求, 请按照要求根据表格中的内容编写代码以生成可视化的图表",
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
    content="展示总评最高的五位学生的作业分数的变化"
)
print(message)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="请认真对待用户的要求，同时尽可能使用中文，生成的图表中使用 Heiti TC 字体。"
)
print(run)

messages = client.beta.threads.messages.list( # 查看thread.id中的message
  thread_id=thread.id
)
print("===============================")
print(messages)
print("===============================")

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

with open("./my-image.png", "wb") as file:
  file.write(image_data_bytes)