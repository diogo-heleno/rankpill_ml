import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




def generate_markdown(system: str, prompt: str) -> str:
resp = client.chat.completions.create(
model=MODEL,
messages=[
{"role": "system", "content": system},
{"role": "user", "content": prompt},
],
temperature=0.6,
)
return resp.choices[0].message.content
