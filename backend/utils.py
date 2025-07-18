import re
import time
from urllib.parse import urlparse
import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI


# Ініціалізуємо OpenAI клієнт
client = OpenAI(api_key=st.secrets["openai_api_key"])


def call_gpt(prompt: str, model: str = "gpt-4", max_tokens: int = 300, retries: int = 3, delay: float = 2.0) -> str:
    """
    Викликає OpenAI GPT (версія openai >= 1.0.0) з ретраями.
    """
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are GPT that analyzes business websites. Answer concisely and in structured format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[GPT Error] Attempt {attempt+1}/{retries}: {e}")
            time.sleep(delay)
    return "GPT Error"


def simplify_url(link: str) -> str:
    """
    Спрощує URL до формату https://site.com
    """
    try:
        parsed = urlparse(link)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return link  # fallback


def extract_email(text: str) -> str:
    """
    Витягує першу email-адресу з тексту (або повертає порожнє значення)
    """
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""


def get_page_text(url: str, timeout: int = 5) -> str:
    """
    Отримує текст сторінки за URL, без HTML тегів.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, timeout=timeout, headers=headers)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return text[:3000]  # обмеження для GPT
    except Exception as e:
        return f"[Error fetching page: {e}]"
