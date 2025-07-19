from openai import OpenAI

def get_key(filename):
    with open(filename, 'r') as file:
        return file.read().strip()

client = OpenAI(api_key=get_key("creds/OPENAI_API_KEY.txt"))
# thread_message = client.beta.threads.messages.create(
#   "thread_pfUo4nlclE41YHqZJaI1BSMQ",
#   role="user",
#   content="How does AI work? Explain it in simple terms.",
# )

thread_messages = client.beta.threads.messages.list("thread_pfUo4nlclE41YHqZJaI1BSMQ")
print(thread_messages.data)