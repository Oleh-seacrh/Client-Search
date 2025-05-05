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
st.title("🔍 Пошук сайтів без аналізу (тільки вкладка 'Пошуки')")

query = st.text_input("Введи ключові слова:")
col1, col2 = st.columns(2)
with col1:
    num_results = st.slider("Кількість результатів", min_value=1, max_value=100, value=10, step=1)
with col2:
    start_index = st.number_input("Починати з результату №", min_value=1, max_value=91, value=1, step=10)

start = st.button("Пошук")

if start and query:
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

        # Отримуємо або створюємо вкладку "Пошуки"
        try:
            search_sheet = sh.worksheet("Пошуки")
        except:
            search_sheet = sh.add_worksheet(title="Пошуки", rows="1000", cols="5")
            search_sheet.append_row(["Ключові слова", "Назва", "Сайт", "Сторінка", "Дата"], value_input_option="USER_ENTERED")

        existing_links = set(search_sheet.col_values(3))
        new_count = 0

        for item in results:
            title = item.get("title", "")
            raw_link = item.get("link", "")
            simplified = simplify_url(raw_link)

            if simplified in existing_links:
                continue

            search_sheet.append_row([query, title, simplified, start_index, st.session_state.get("current_date", "")], value_input_option="USER_ENTERED")
            existing_links.add(simplified)
            new_count += 1

        st.success(f"✅ Додано {new_count} нових сайтів до вкладки 'Пошуки'.")
        
        # --------------------- GPT-Аналіз нових сайтів ---------------------
st.header("🤖 GPT-Аналіз нових сайтів")

num_to_analyze = st.slider("Скільки записів аналізувати за раз", min_value=1, max_value=50, value=10)

if st.button("Аналізувати нові записи GPT"):
    with st.spinner("Проводиться GPT-аналіз..."):
        gc = get_gsheet_client()
        sh = gc.open_by_key(GSHEET_SPREADSHEET_ID)

        try:
            search_sheet = sh.worksheet("Пошуки")
        except:
            st.error("Вкладка 'Пошуки' не знайдена.")
            st.stop()

        # Читаємо всі дані з Пошуків
        records = search_sheet.get_all_records()
        rows_to_analyze = []
        for idx, row in enumerate(records, start=2):  # з другої, бо перша — заголовки
            gpt_field = str(row.get("GPT-відповідь", "")).strip().lower()
            if not gpt_field or gpt_field in ["-", "очікує"]:
                rows_to_analyze.append((idx, row))
            if len(rows_to_analyze) >= num_to_analyze:
                break

        if not rows_to_analyze:
            st.info("Немає записів для аналізу.")
            st.stop()

        # Створюємо або відкриваємо вкладку 'Аналіз'
        try:
            analysis_sheet = sh.worksheet("Аналіз")
        except:
            analysis_sheet = sh.add_worksheet(title="Аналіз", rows="1000", cols="7")
            analysis_sheet.append_row(["Назва", "Сайт", "Ключові слова", "GPT-відповідь", "Сторінка", "Дата", "Статус GPT"], value_input_option="USER_ENTERED")

        for idx, row in rows_to_analyze:
            title = row.get("Назва", "")
            site = row.get("Сайт", "")
            keywords = row.get("Ключові слова", "")
            snippet = ""  # Поки не зберігаємо snippet — додати пізніше, якщо потрібно
            page = row.get("Сторінка", "")
            date = row.get("Дата", "")

            # GPT-запит
            try:
                prompt = f"""
                Ти — асистент з продажу рентген-плівки, касет та медичних витратників.
                Чи може наступна компанія бути потенційним клієнтом?

                Назва: {title}
                Сайт: {site}
                Ключові слова пошуку: {keywords}

                Відповідь у форматі:
                Назва компанії: ...
                Клієнт: Так/Ні — коротке пояснення
                Тип: (одне слово)
                Країна: (одне слово)
                Пошта: ...
                """
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                gpt_result = response.choices[0].message.content
                status = "Аналізовано"
            except Exception as e:
                gpt_result = f"Помилка: {e}"
                status = "Помилка"

            # Запис у вкладку 'Аналіз'
            analysis_sheet.append_row([title, site, keywords, gpt_result, page, date, status], value_input_option="USER_ENTERED")

            # Оновлюємо у вкладці 'Пошуки' поле GPT-відповіді
            search_sheet.update_cell(idx, 6, gpt_result)  # колонка 6 — GPT-відповідь
            search_sheet.update_cell(idx, 7, status)       # колонка 7 — Статус

        st.success(f"✅ GPT-аналіз виконано для {len(rows_to_analyze)} записів.")

