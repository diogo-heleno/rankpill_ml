from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LocaleCfg:
code: str # e.g., "pt-pt"
base: str # e.g., "https://www.m21global.com/pt"
slug_lang: str # slug language root e.g., "/pt/", "/es/"
name: str


# Base sites per locale
LOCALES: Dict[str, LocaleCfg] = {
"en": LocaleCfg("en", "https://www.m21global.com/en", "/en/", "English"),
"pt-pt": LocaleCfg("pt-pt", "https://www.m21global.com/pt", "/pt/", "Português (Portugal)"),
"pt-ao": LocaleCfg("pt-ao", "https://www.m21global.com/ao", "/ao/", "Português (Angola)"),
"pt-br": LocaleCfg("pt-br", "https://www.m21global.com/br", "/br/", "Português (Brasil)"),
"es": LocaleCfg("es", "https://www.m21global.com/es", "/es/", "Español"),
"fr": LocaleCfg("fr", "https://www.m21global.com/fr", "/fr/", "Français"),
}


# Link pools per locale (rotate to ensure at least one per paragraph)
LINK_POOLS: Dict[str, List[str]] = {
"en": [
"/en/company/", "/en/certified-translation-company/", "/en/iso-certification/",
"/en/why-choose-a-translation-company/", "/en/services/", "/en/contact/"
],
"pt-pt": [
"/pt/empresa-de-traducao-certificada/",
"/pt/certificacao-iso/",
"/pt/porque-escolher-uma-empresa-de-traducoes/",
"/pt/servicos/", "/pt/contactos/"
],
"pt-ao": [
"/ao/empresa-de-traducao/", "/ao/servicos/", "/ao/contactos/"
],
"pt-br": [
"/br/empresa-de-traducao/", "/br/servicos/", "/br/contato/"
],
"es": [
"/es/empresa/", "/es/servicios/", "/es/certificacion-iso/",
"/es/por-que-elegir-una-empresa-de-traduccion/", "/es/contacto/"
],
"fr": [
"/fr/entreprise/", "/fr/services/", "/fr/certification-iso/",
"/fr/pourquoi-choisir-une-entreprise-de-traduction/", "/fr/contact/"
],
}


SUPPORTED = list(LOCALES.keys())
