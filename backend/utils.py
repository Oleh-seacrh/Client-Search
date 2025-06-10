import re
import time
from urllib.parse import urlparse
import streamlit as st
import requests
from bs4 import BeautifulSoup


def call_gpt(prompt: str, model: str = "gpt-4", max_tokens: int = 300, retries: int = 3, delay: float = 2.0) -> str:
    """
    Calls OpenAI GPT with retries and a default short system prompt.
    """
    import openai
    openai.api_key = st.secrets["openai_api_key"]

    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are GPT that analyzes business websites. Answer concisely and in structured format."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"[GPT Error] Attempt {attempt+1}/{retries}: {e}")
            time.sleep(delay)
    return "GPT Error"


def simplify_url(link: str) -> str:
    """
    Simplifies a URL to scheme://domain.
    """
    try:
        parsed = urlparse(link)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return link  # fallback


def extract_email(text: str) -> str:
    """
    Extracts the first email found in the given text.
    """
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""


def get_page_text(url: str, timeout: int = 5) -> str:
    """
    Downloads and cleans text content from a web page.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, timeout=timeout, headers=headers)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return text[:3000]  # limit to 3000 chars for GPT context
    except Exception as e:
        return f"[Error fetching page: {e}]"
