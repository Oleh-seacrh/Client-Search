import openai
import re
import time
from urllib.parse import urlparse
import streamlit as st

# Отримання OpenAI API ключа із secrets.toml
openai.api_key = st.secrets["openai_api_key"]

def call_gpt(prompt: str, model: str = "gpt-4", max_tokens: int = 300, retries: int = 3, delay: float = 2.0) -> str:
    """
    Викликає OpenAI GPT з заданим промптом і повертає відповідь у вигляді тексту.
    """
    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Ти GPT, який аналізує бізнес-сайти. Відповідай коротко і структуровано."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"[GPT Error] Спроба {attempt+1}/{retries}: {e}")
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
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""
