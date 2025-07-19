from google import genai
from google.genai import types

def get_key(filename):
    with open(filename, 'r') as file:
        return file.read().strip()

client = genai.Client(api_key=get_key("../../creds/GEMINI_API_KEY.txt"))
print("Client initialized successfully.")

# Only for videos of size <20Mb
video_file_name = "/Users/iamsohan/Downloads/test.mp4"
video_bytes = open(video_file_name, 'rb').read()

response = client.models.generate_content(
    model='models/gemini-2.0-flash',
    contents=types.Content(
        parts=[
            types.Part(
                inline_data=types.Blob(data=video_bytes, mime_type='video/mp4')
            ),
            types.Part(text='tell me more')
        ]
    )
)

print(response.text)
print("Response received successfully.")