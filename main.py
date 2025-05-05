import streamlit as st
import requests
import re
from urllib.parse import urlparse
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Секрети
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GSHEET_JSON = st.secrets["GSHEET_SERVICE_ACCOUNT"]
GSHEET_SPREADSHEET_ID = "1S0nkJYXrVTsMHmeOC-uvMWnrw_yQi5z8NzRsJEcBjc0"

# Підключення до Google Sheets
def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(GSHEET_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# Спрощення URL
def simplify_url(link):
    parsed = urlparse(link)
    return f"{parsed.scheme}://{parsed.netloc}"

# Інтерфейс
st.set_page_config(page_title="Пошук сайтів", layout="wide")
st.title("🔍 Пошук сайтів без аналізу")

query = st.text_input("Введи ключові слова:")
col1, col2 = st.columns(2)
with col1:
    num_results = st.slider("Кількість результатів", min_value=1, max_value=100, value=10, step=1)
with col2:
    start_index = st.number_input("Починати з результату №", min_value=1, max_value=91, value=1, step=10)

start = st.button("Пошук")

if start and query:
    tab_name = query.strip().lower().replace("/", "_")[:30]
    with st.spinner("Пошук сайтів..."):
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
            sheet = sh.add_worksheet(title=tab_name, rows="1000", cols="6")
            sheet.append_row(["Назва компанії", "Сайт", "Пошта", "Тип", "Країна", "Статус"], value_input_option="USER_ENTERED")

        existing_links = set(sheet.col_values(2))
        new_count = 0

        for item in results:
            title = item.get("title", "")
            raw_link = item.get("link", "")
            simplified = simplify_url(raw_link)

            if simplified in existing_links:
                continue

            # Додаємо без аналізу
            sheet.append_row([title, simplified, "-", "-", "-", "-"], value_input_option="USER_ENTERED")
            existing_links.add(simplified)
            new_count += 1

        st.success(f"✅ Додано {new_count} нових сайтів до вкладки '{tab_name}'. GPT-аналіз поки не використовується.")
