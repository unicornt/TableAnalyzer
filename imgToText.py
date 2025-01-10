from openai import OpenAI
import os
import openai

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)


# Upload a file with an "assistants" purpose
file = client.files.create(
    file=open("my-image.png", "rb"),
    purpose='user_data'
)

# Create an assistant using the file ID
assistant = client.beta.assistants.create(
    instructions="你是一个非常严谨的数据分析专家。",
    model="gpt-4o",
    tools=[{"type": "code_interpreter"}],
    tool_resources={
        "code_interpreter": {
            "file_ids": [file.id]
        }
    }
)
thread = client.beta.threads.create()

# 创建一条消息
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    # content="展示总评最高的五位学生的作业分数的变化。",
    content="请描述图片中的信息",
    attachments=[{ "file_id": file.id , "tools": [{"type": "code_interpreter"}]}],
)
print(message)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant.id,
    instructions="请认真对待用户的要求"
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