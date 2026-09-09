#!/usr/bin/env python3
"""
Monitor de 'Destino Oculto 3' de Wingo.

Revisa:
  1. La página principal de wingo.com y páginas relevantes de wingo.com
  2. Noticias recientes vía Google News RSS
  3. (Opcional) Un feed RSS de Instagram/Twitter si lo configuras (ver README)

Si encuentra la palabra clave "destino oculto" combinada con un indicio de
lanzamiento (compra, tiquetes, disponible, reserva, 3ra, tercera, "ya puedes"),
manda una alerta a Telegram y guarda el estado para no repetir la alarma.

Variables de entorno requeridas (se configuran como Secrets en GitHub Actions):
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
"""

import os
import re
import sys
import json
import time
import hashlib
import requests
import feedparser
from bs4 import BeautifulSoup

STATE_FILE = "state.json"

# --- Fuentes a revisar --------------------------------------------------

WEB_SOURCES = [
    "https://www.wingo.com",
    "https://www.wingo.com/co/es-co",  # variante regional, ajusta si redirige distinto
]

# Búsquedas de noticias vía Google News RSS (sin necesidad de API key)
NEWS_QUERIES = [
    "Destino Oculto Wingo",
    "Wingo Destino Oculto 3",
    "Wingo Corona destino oculto",
]

# Palabras que indican que YA se puede comprar / se lanzó (no solo que se habla del pasado)
LAUNCH_HINTS = [
    "ya puedes", "ya está disponible", "compra tus tiquetes", "reserva ya",
    "disponible desde hoy", "edición 3", "tercera edición", "destino oculto 3",
    "cupos limitados", "adquiere tu tiquete", "compra ahora",
]

KEYWORD = "destino oculto"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"alerted": False, "seen_hashes": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_telegram(message: str):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, data={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }, timeout=15)
    resp.raise_for_status()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def check_website(url: str, state: dict) -> list:
    """Descarga una página y busca la keyword + indicios de lanzamiento."""
    hits = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f"[web] error consultando {url}: {e}")
        return hits

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(separator=" ", strip=True).lower()

    if KEYWORD in text:
        # busca fragmentos de contexto alrededor de cada aparición
        for m in re.finditer(KEYWORD, text):
            start = max(0, m.start() - 80)
            end = min(len(text), m.end() + 80)
            snippet = text[start:end]
            h = text_hash(url + snippet)
            if h in state["seen_hashes"]:
                continue
            has_launch_hint = any(hint in snippet for hint in LAUNCH_HINTS)
            if has_launch_hint:
                hits.append({
                    "source": url,
                    "snippet": snippet,
                    "hash": h,
                })
    return hits


def check_news(state: dict) -> list:
    """Revisa Google News RSS para cada query configurada."""
    hits = []
    for q in NEWS_QUERIES:
        rss_url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=es-419&gl=CO&ceid=CO:es-419"
        try:
            feed = feedparser.parse(rss_url)
        except Exception as e:
            print(f"[news] error con query '{q}': {e}")
            continue

        for entry in feed.entries[:15]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            combined = f"{title} {summary}".lower()
            if KEYWORD not in combined:
                continue
            has_launch_hint = any(hint in combined for hint in LAUNCH_HINTS)
            if not has_launch_hint:
                continue
            h = text_hash(entry.get("link", "") + title)
            if h in state["seen_hashes"]:
                continue
            hits.append({
                "source": entry.get("link", rss_url),
                "snippet": title,
                "hash": h,
            })
    return hits


def main():
    state = load_state()

    if state.get("alerted"):
        print("Ya se envió la alerta anteriormente. No se vuelve a notificar.")
        print("(Si quieres reactivar el monitoreo, borra state.json o pon 'alerted': false)")
        return

    all_hits = []
    for url in WEB_SOURCES:
        all_hits.extend(check_website(url, state))

    all_hits.extend(check_news(state))

    if not all_hits:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Sin novedades.")
        return

    # Manda una alerta (agrupando todos los hallazgos de esta corrida)
    lines = ["🚨 <b>¡Posible lanzamiento de Destino Oculto detectado!</b>", ""]
    for hit in all_hits:
        lines.append(f"• {hit['snippet']}")
        lines.append(f"  Fuente: {hit['source']}")
        lines.append("")
        state["seen_hashes"].append(hit["hash"])

    lines.append("Ve a wingo.com YA, esto se agota en minutos.")
    message = "\n".join(lines)

    send_telegram(message)
    state["alerted"] = True
    save_state(state)
    print("Alerta enviada y estado guardado.")


if __name__ == "__main__":
    main()
