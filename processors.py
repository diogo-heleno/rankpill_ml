import os
import re
from datetime import datetime
from typing import Tuple
from locales import LOCALES, LINK_POOLS


PARA_SPLIT = re.compile(r"\n\s*\n")
LINK_PATTERN = re.compile(r"\[[^\]]+\]\([^\)]+\)")




def ensure_links_per_paragraph(md: str, locale_code: str) -> str:
"""Guarantee ≥1 internal link per paragraph. If missing, append a natural sentence with a link.
"""
base = LOCALES[locale_code].base
pool = LINK_POOLS[locale_code]
pool_idx = 0


paragraphs = PARA_SPLIT.split(md.strip())
fixed = []
for p in paragraphs:
if LINK_PATTERN.search(p):
fixed.append(p)
continue
# Inject a default sentence with a rotating link
link_path = pool[pool_idx % len(pool)]
pool_idx += 1
full = f"{base}{link_path}"
injection = f"\n\nPara detalhes, veja os nossos [serviços]({full})."
fixed.append(p + injection)
return "\n\n\n".join(fixed)




def write_output(md: str, locale_code: str, out_dir: str) -> str:
os.makedirs(out_dir, exist_ok=True)
path = os.path.join(out_dir, f"{locale_code}.md")
with open(path, "w", encoding="utf-8") as f:
f.write(md.strip() + "\n")
return path




def todays_out_dir() -> str:
return os.path.join("out", datetime.now().strftime("%Y-%m-%d"))
