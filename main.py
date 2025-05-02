
import streamlit as st
import requests
import openai
import pandas as pd
import re
from urllib.parse import urlparse
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Секрети
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GSHEET_JSON = st.secrets["GSHEET_SERVICE_ACCOUNT"]
GSHEET_SPREADSHEET_ID = "1S0nkJYXrVTsMHmeOC-uvMWnrw_yQi5z8NzRsJEcBjc0"

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(GSHEET_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def simplify_url(link):
    parsed = urlparse(link)
    return f"{parsed.scheme}://{parsed.netloc}"

def extract_email(text):
    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return emails[0] if emails else "—"

def analyze_with_gpt(title, snippet, link):
    prompt = f"""
    Ти допомагаєш визначити, чи сайт може бути потенційним клієнтом для медичної продукції (Agfa, Fujifilm, Carestream).

    🔹 Назва: {title}
    🔹 Опис: {snippet}
    🔹 Лінк: {link}

    1️⃣ Чи може це бути потенційний клієнт? (Так / Ні + коротке пояснення)

    2️⃣ Який тип організації це ймовірно?
    (Вибери один: дистриб’ютор / лікарня / медичний центр / виробник / інше)

    Відповідай у форматі:
    Клієнт: Так/Ні — [пояснення]
    Тип: [тип організації]
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

st.set_page_config(page_title="Пошук клієнтів GPT", layout="wide")
st.title("🔍 Пошук потенційних клієнтів через Google + GPT")

query = st.text_input("Введи ключові слова:")

col1, col2 = st.columns(2)
with col1:
    num_results = st.slider("Кількість результатів", min_value=1, max_value=100, value=10, step=1)
with col2:
    start_index = st.number_input("Починати з результату №", min_value=1, max_value=91, value=1, step=10)

start = st.button("Пошук")

if start and query:
    tab_name = query.strip().lower().replace("/", "_")[:30]
    with st.spinner("Пошук та GPT-аналіз..."):
        params = {
            "key": st.secrets["GOOGLE_API_KEY"],
            "cx": st.secrets["CSE_ID"],
            "q": query,
            "num": num_results,
            "start": start_index
        }
        results = requests.get("https://www.googleapis.com/customsearch/v1", params=params).json().get("items", [])

        gc = get_gsheet_client()
        sh = gc.open_by_key(GSHEET_SPREADSHEET_ID)

        try:
            sheet = sh.worksheet(tab_name)
        except:
            sheet = sh.add_worksheet(title=tab_name, rows="1000", cols="4")
            sheet.append_row(["Назва компанії", "Сайт", "Пошта", "Відгук GPT"])

        existing_links = set(sheet.col_values(2))

        for item in results:
            title = item["title"]
            raw_link = item["link"]
            link = simplify_url(raw_link)
            if link in existing_links:
                continue

            snippet = item.get("snippet", "")
            email = extract_email(title + " " + snippet)

            try:
                gpt_response = analyze_with_gpt(title, snippet, link)
            except Exception as e:
                gpt_response = f"Помилка: {e}"

            if gpt_response.strip().startswith("Так"):
                sheet.append_row([title, link, email, gpt_response], value_input_option="USER_ENTERED")
                existing_links.add(link)

        st.success(f"✅ Дані додано до вкладки '{tab_name}', без перезапису")
