from openai import OpenAI

def get_key(filename):
    with open(filename, 'r') as file:
        return file.read().strip()

client = OpenAI(api_key=get_key("creds/OPENAI_API_KEY.txt"))

assistant = client.beta.assistants.create(
  name="Math Tutor",
  instructions="You are a personal math tutor. Write and run code to answer math questions.",
  tools=[{"type": "code_interpreter"}],
  model="gpt-4o",
)

thread = client.beta.threads.create()

message = client.beta.threads.messages.create(
  thread_id=thread.id,
  role="user",
  content="I need to solve the equation `3x + 11 = 14`. Can you help me?"
)

print("----------------")
print("assistant ID:",assistant.id)
print("thread ID:", thread.id)
print("----------------")