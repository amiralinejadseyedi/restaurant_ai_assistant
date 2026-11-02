
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL")

if not api_key or not model:
    raise ValueError("API key or model is missing from .env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "سلام! در یک جمله خودت را معرفی کن.",
            }
        ],
        max_tokens=100,
    )

    print("AI response:")
    print(response.choices[0].message.content)

except Exception as error:
    print("Request failed:", type(error).__name__)
    print(error)
