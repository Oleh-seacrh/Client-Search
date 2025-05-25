import streamlit as st
import requests
import re
from urllib.parse import urlparse
import json
from bs4 import BeautifulSoup
import openai
import pandas as pd
import unicodedata
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

st.set_page_config(page_title="Search and Analysis Machine (SAM)", layout="wide")

# Меню вкладок
section = st.sidebar.radio("📂 Обери режим:", [
    "🔑 Пошук по ключовим словам",
    "📋 Пошук по табличці",
    "🤝 Клієнти"
])

# Вкладка: Пошук по ключовим словам
if section == "🔑 Пошук по ключовим словам":
    st.header("🔑 Пошук по ключовим словам")
    st.info("Тут буде реалізовано пошук сайтів через введення ключових слів вручну")

# Вкладка: Пошук по табличці
elif section == "📋 Пошук по табличці":
    st.header("📋 Пошук сайтів за назвами з таблиці")
    st.info("Цей розділ автоматично обробляє список компаній із Google Таблиці")

# Вкладка: Клієнти
elif section == "🤝 Клієнти":
    st.header("🤝 Перспективні клієнти")
    st.info("GPT-аналіз визначив ці компанії як потенційних клієнтів")
