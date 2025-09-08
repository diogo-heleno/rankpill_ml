import os
import imaplib
import email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def fetch_latest_markdown():
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(os.getenv("OUTPUT_EMAIL_USERNAME"), os.getenv("OUTPUT_EMAIL_PASSWORD"))
    imap.select("inbox")

    status, messages = imap.search(None, "UNSEEN")
    if status != "OK" or not messages[0]:
        return None

    latest_id = messages[0].split()[-1]
    status, msg_data = imap.fetch(latest_id, "(RFC822)")
    raw_email = email.message_from_bytes(msg_data[0][1])

    for part in raw_email.walk():
        if part.get_content_type() == "text/markdown" or part.get_filename().endswith(".md"):
            return part.get_payload(decode=True).decode()

    return None

def process_article(article_text, keyword, target_lang):
    system_prompt = f"""
    Quero que atues como especialista de conteúdo SEO e tradução para blogs da M21Global...
    """
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Artigo:\n{article_text}\n\nKeyword: {keyword}\nLíngua: {target_lang}"}
        ]
    )
    return response.choices[0].message.content

def send_results(files):
    msg = MIMEMultipart()
    msg["From"] = os.getenv("OUTPUT_EMAIL_USERNAME")
    msg["To"] = os.getenv("OUTPUT_EMAIL_TO")
    msg["Subject"] = "Translated Articles"

    for filename, content in files.items():
        part = MIMEBase("application", "octet-stream")
        part.set_payload(content.encode())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.getenv("OUTPUT_EMAIL_USERNAME"), os.getenv("OUTPUT_EMAIL_PASSWORD"))
        server.send_message(msg)

if __name__ == "__main__":
    article = fetch_latest_markdown()
    if article:
        outputs = {}
        for lang in ["EN", "PT-PT", "PT-AO", "PT-BR", "ES", "FR"]:
            outputs[f"article_{lang}.md"] = process_article(article, "tradução de documentos", lang)
        send_results(outputs)
