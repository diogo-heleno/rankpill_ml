import argparse


def process_article(en_article: str, keyword_pt: str) -> dict:
outputs = {}
out_dir = todays_out_dir()


# Locales order
locales = ["en", "pt-pt", "pt-ao", "pt-br", "es", "fr"]


for code in locales:
cfg = LOCALES[code]
prompt = ARTICLE_PROMPT.format(
keyword=keyword_pt,
lang_name=cfg.name,
lang_code=cfg.code,
base=cfg.base,
slug_lang=cfg.slug_lang,
article=en_article,
)
md = generate_markdown(SYSTEM_STYLE, prompt)
md = ensure_links_per_paragraph(md, code)
path = write_output(md, code, out_dir)
outputs[code] = path


# Optionally send email
_email_outputs(list(outputs.values()))
return outputs




# --- Flask routes ---


@app.post("/rankpill/webhook")
def rankpill_webhook():
payload = request.get_json(force=True, silent=True) or {}
article = payload.get("body") or payload.get("article") or ""
keyword = payload.get("keyword", "tradução certificada")
if not article.strip():
return jsonify({"ok": False, "error": "missing article body"}), 400
files = process_article(article, keyword)
return jsonify({"ok": True, "files": files})




# --- CLI for local use ---
if __name__ == "__main__":
parser = argparse.ArgumentParser()
parser.add_argument("--file", help="path to EN article (md or txt)")
parser.add_argument("--keyword", default="tradução certificada")
parser.add_argument("--serve", action="store_true", help="run webhook server")
args = parser.parse_args()


if args.serve or not args.file:
app.run(host="0.0.0.0", port=5000, debug=os.getenv("APP_DEBUG", "true").lower()=="true")
else:
with open(args.file, "r", encoding="utf-8") as f:
article = f.read()
out = process_article(article, args.keyword)
print(json.dumps(out, indent=2, ensure_ascii=False))
