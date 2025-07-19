from openai import OpenAI
import sqlite3
from db.db import add_thread, get_messages, add_message

def get_key(filename):
    with open(filename, 'r') as file:
        return file.read().strip()

client = OpenAI(api_key="creds/OPENAI_API_KEY.txt")

# # Create a new assistant (only once)
# assistant = client.beta.assistants.create(
#     name="Ai Mentor Testing",
#     instructions="You are a spiritual guru. I generally speak very less, just a few words. You should be able to understand my feelings and emotions and respond accordingly.",
#     model="gpt-4-1106-preview",  # e.g., GPT-4 preview model
#     tools=[]
# )

# # Or list and fetch by name if already exists
# all_assistants = client.beta.assistants.list(limit=10)
# assistant = next((a for a in all_assistants.data if a.name=="Ai Mentor Testing"), assistant)

# retrieve the assistant by ID
assistant = client.beta.assistants.retrieve("asst_qsS2QSKmqjlfHUDgJcYqcgOc")


import streamlit as st

st.sidebar.title("Threads")
threads = [row[0] for row in sqlite3.connect("chat.db").cursor().execute("SELECT id FROM threads").fetchall()]
selected_thread = st.sidebar.radio("Select thread", options=threads + ["[New Thread]"])

if selected_thread == "[New Thread]":
    new_thread = client.beta.threads.create()
    add_thread(new_thread.id)
    st.session_state.thread_id = new_thread.id
else:
    st.session_state.thread_id = selected_thread
    

if "thread_id" not in st.session_state:
    st.session_state.thread_id = threads[0] if threads else None

st.title(f"Chat – Thread: {st.session_state.thread_id}")
for role, content in get_messages(st.session_state.thread_id):
    if role == "user":
        st.markdown(f"**You:** {content}")
    else:
        st.markdown(f"**Assistant:** {content}")

user_input = st.text_input("Ask something:", placeholder="Type your message here...")
if st.button("Send"):
    # Send user message to API and database
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input
    )
    add_message(st.session_state.thread_id, "user", user_input)

    # Stream assistant response and display in real-time
    reply_box = st.empty()
    reply_text = ""
    stream = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant.id,
        stream=True
    )
    for event in stream:
        if event.__class__.__name__ == "ThreadMessageDelta":
            delta = event.data.delta.content[0].text.value
            reply_text += delta
            reply_box.markdown(f"**Assistant:** {reply_text}")

    # Persist assistant response and refresh UI
    add_message(st.session_state.thread_id, "assistant", reply_text)
    st.rerun()