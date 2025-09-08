import os, imaplib, email, smtplib, re, sys, time
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# ---- OpenAI (GPT-5) ----
from openai import OpenAI
OPENAI_MODEL = "gpt-5"  # per your request
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---- Gmail creds (repo secrets) ----
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT_SSL = 465
IMAP_HOST = "imap.gmail.com"
GMAIL_USER = os.getenv("OUTPUT_EMAIL_USERNAME")
GMAIL_PASS = os.getenv("OUTPUT_EMAIL_PASSWORD")
SEND_TO     = os.getenv("OUTPUT_EMAIL_TO")

# ------------ Helpers ------------
LANG_CODES = ["EN", "PT-PT", "PT-AO", "PT-BR", "ES", "FR"]

def lang_base(lang: str) -> str:
    """Return the correct site base path for internal links."""
    m = {
        "PT-PT": "/pt/",
        "PT-AO": "/ao/",
        "PT-BR": "/br/",
        "ES": "/es/",
        "FR": "/fr/",
        "EN": "/en/",
    }
    return m.get(lang, "/en/")

def get_md_from_latest_unseen():
    """Fetch the newest UNSEEN email that has a .md attachment; return (content, subject, uid)."""
    imap = imaplib.IMAP4_SSL(IMAP_HOST)
    imap.login(GMAIL_USER, GMAIL_PASS)
    imap.select("inbox")
    typ, data = imap.search(None, 'UNSEEN')
    if typ != "OK" or not data or not data[0]:
        imap.logout()
        return None, None, None

    ids = data[0].split()
    latest_id = ids[-1]
    typ, msg_data = imap.fetch(latest_id, "(RFC822)")
    if typ != "OK":
        imap.logout()
        return None, None, None

    raw = email.message_from_bytes(msg_data[0][1])
    subject = raw.get("Subject", "")
    # try body-as-md first if no attachment
    article_md = None

    for part in raw.walk():
        fn = part.get_filename() or ""
        ctype = part.get_content_type() or ""
        if fn.lower().endswith(".md") or ctype == "text/markdown":
            article_md = part.get_payload(decode=True).decode(errors="ignore")
            break

    if not article_md:
        # fallback: if the email body is text/plain or text/html, pull text and treat as markdown
        for part in raw.walk():
            if part.get_content_type() == "text/plain":
                article_md = part.get_payload(decode=True).decode(errors="ignore")
                break
        if not article_md:
            for part in raw.walk():
                if part.get_content_type() == "text/html":
                    html = part.get_payload(decode=True).decode(errors="ignore")
                    # naive HTML -> text
                    article_md = re.sub(r"<[^>]+>", "", html)

    imap.logout()
    return article_md, subject, latest_id

def mark_seen(uid: bytes):
    try:
        imap = imaplib.IMAP4_SSL(IMAP_HOST)
        imap.login(GMAIL_USER, GMAIL_PASS)
        imap.select("inbox")
        imap.store(uid, '+FLAGS', '\\Seen')
        imap.logout()
    except Exception:
        pass

def extract_keyword(subject: str) -> str:
    """
    If you include something like 'keyword: tradução certificada' in the subject,
    we’ll pick it up. Otherwise default to 'tradução de documentos'.
    """
    m = re.search(r"keyword\s*:\s*(.+)$", subject, re.I)
    return m.group(1).strip() if m else "tradução de documentos"

FULL_PROMPT = """
Quero que atues como **especialista de conteúdo SEO e tradução para blogs da M21Global**. Vou dar-te:

- Um artigo já feito (pode não estar formatado em Markdown).
- A keyword principal.
- A língua de destino (PT-PT, PT-BR, PT-AO, ES, FR, EN).

### A tua tarefa é:

#### Parte 1 – Artigo

1. **Traduzir e adaptar** o artigo para a língua pedida, mantendo o tom profissional e humano usado no blog da M21Global.
2. **Destacar a keyword principal** várias vezes de forma natural e SEO-friendly.
3. **Inserir links internos estratégicos para páginas da M21Global**, consoante a língua:
    - /pt/ → português de Portugal
    - /br/ → português do Brasil
    - /ao/ → português de Angola
    - /es/ → espanhol
    - /fr/ → francês
    - /en/ → inglês
4. Os links devem ser usados de forma natural, **integrados no texto em Markdown**, e é **OBRIGATÓRIO que cada parágrafo tenha pelo menos 1 link interno** para a versão correta do site da M21Global.
    - ⚠️ Se algum parágrafo não tiver link interno, reescreve-o até ter.
5. Converter todo o conteúdo para **Markdown pronto a publicar** no blog.
6. No final, acrescentar uma **FAQ com 4 perguntas e respostas**, focadas na keyword dada.

#### Parte 2 – SEO (RankMath)

Gerar automaticamente:
- **SEO Title** (máx. 60 caracteres, keyword no início, ano quando relevante).
- **Meta Description** (máx. 160 caracteres, keyword incluída).
- **Slug** (URL amigável com a keyword, ex: `/es/traduccion-certificado-de-nacimiento/`).

---
**IMPORTANTE PARA O MODELO:**
- Mantém o tom e estilo do blog da M21Global (profissional, claro, humano).
- Inclui pelo menos **1 link interno por parágrafo** usando o prefixo de língua correto fornecido.
- Produz APENAS Markdown final (sem explicações).
"""

def call_gpt(article_md: str, keyword: str, lang: str) -> str:
    site_prefix = lang_base(lang)
    user_msg = (
        f"Artigo (EN ou texto livre):\n{article_md}\n\n"
        f"Keyword principal: {keyword}\n"
        f"Língua de destino: {lang}\n"
        f"Prefixo base para links internos: {site_prefix}\n"
        "Reforço: cada parágrafo TEM de conter pelo menos 1 link interno com este prefixo."
    )
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": FULL_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content

def send_results(files_dict: dict, subject_hint: str):
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = SEND_TO
    msg["Subject"] = f"[M21Global] 6 versões em Markdown — {subject_hint or 'artigo'}"

    msg.attach(MIMEText("Segue em anexo as 6 versões (EN, PT-PT, PT-AO, PT-BR, ES, FR).", "plain"))

    for fn, content in files_dict.items():
        part = MIMEBase("application", "octet-stream")
        part.set_payload(content.encode("utf-8"))
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{fn}"')
        msg.attach(part)

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT_SSL) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)

def main():
    article_md, subject, uid = get_md_from_latest_unseen()
    if not article_md:
        print("No new markdown email found.")
        return

    keyword = extract_keyword(subject)
    outputs = {}

    # First improve EN (keeps same pipeline rules, tone + internal links to /en/)
    for lang in LANG_CODES:
        md = call_gpt(article_md, keyword, lang)
        safe_slug_part = lang.lower().replace("-", "")
        outputs[f"article_{safe_slug_part}.md"] = md

    send_results(outputs, subject or keyword)

    # mark email as seen so it isn't reprocessed
    if uid:
        mark_seen(uid)

if __name__ == "__main__":
    for var in ["OPENAI_API_KEY","OUTPUT_EMAIL_USERNAME","OUTPUT_EMAIL_PASSWORD","OUTPUT_EMAIL_TO"]:
        if not os.getenv(var):
            print(f"Missing env var: {var}", file=sys.stderr)
    main()
