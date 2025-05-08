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
    start_options = list(range(1, 101, 10))
    start_index = st.selectbox("Сторінка результатів:", options=start_options, index=0)

start = st.button("Пошук")

if start and query:
    st.markdown("🔁 **Тригер активовано — виконується пошук...**")  # DEBUG

    with st.spinner("Пошук сайтів..."):
        params = {
            "key": st.secrets["GOOGLE_API_KEY"],
            "cx": st.secrets["CSE_ID"],
            "q": query,
            "num": num_results,
            "start": start_index
        }
        results = requests.get("https://www.googleapis.com/customsearch/v1", params=params).json().get("items", [])

        page_number = ((start_index - 1) // num_results) + 1

        st.markdown(f"### 🔍 Результати для: **{query}**")
        st.markdown(f"➡️ **Сторінка №{page_number}** (start_index = `{start_index}`, результатів отримано: `{len(results)}`)")

        gc = get_gsheet_client()
        sh = gc.open_by_key(GSHEET_SPREADSHEET_ID)

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
                st.markdown(f"🔁 Пропущено (вже є): `{simplified}`")
                continue

            st.markdown(f"✅ Додано: **{title}** — `{simplified}`")

            search_sheet.append_row(
                [query, title, simplified, page_number, st.session_state.get("current_date", "")],
                value_input_option="USER_ENTERED"
            )
            existing_links.add(simplified)
            new_count += 1

        st.success(f"🟢 Додано {new_count} нових сайтів на сторінці {page_number}")



        
        # --------------------- GPT-Аналіз нових сайтів ---------------------
client = openai.OpenAI(api_key=OPENAI_API_KEY)

st.header("🤖 GPT-Аналіз нових сайтів")

# Функція для парсингу тексту сайту
def get_page_text(url):
    try:
        response = requests.get(url, timeout=7)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text(separator=" ")
        return ' '.join(text.split())[:2000]  # обмеження до 2000 символів
    except Exception as e:
        return f"Не вдалося отримати текст сайту: {e}"

# Скільки сайтів аналізувати за раз
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

        try:
            analysis_sheet = sh.worksheet("Аналіз")
        except:
            analysis_sheet = sh.add_worksheet(title="Аналіз", rows="1000", cols="8")
            analysis_sheet.append_row(
                ["Назва", "Сайт", "Ключові слова", "Висновок", "Потенційний клієнт", "Сторінка", "Дата", "Статус GPT"],
                value_input_option="USER_ENTERED"
            )

        records = search_sheet.get_all_records()
        analyzed_sites = set()
        existing_analysis = analysis_sheet.get_all_records()
        for r in existing_analysis:
            site_val = r.get("Сайт", "").strip().lower()
            if site_val:
                analyzed_sites.add(site_val)

        analyzed_count = 0
        for idx, row in enumerate(records, start=2):
            if analyzed_count >= num_to_analyze:
                break

            title = row.get("Назва", "")
            site = simplify_url(row.get("Сайт", "").strip().lower())
            keywords = row.get("Ключові слова", "")
            page = row.get("Сторінка", "")
            date = row.get("Дата", "")

            if site in analyzed_sites:
                continue

            try:
                site_text = get_page_text(site)

                prompt = f"""
                Ти — асистент з продажу компанії, яка постачає рентген-плівку, касети, медичні принтери та витратні матеріали.

                Назва компанії: {title}
                Сайт: {site}
                Ключові слова: {keywords}
                Контент сайту (обмежено): {site_text}

                Завдання:
                - Визначи, чи компанія є потенційним клієнтом (Так/Ні).
                - Якщо Так, вкажи її тип (наприклад: дистриб’ютор, постачальник).
                - Дай короткий висновок — одне речення, наприклад: "Так, дистриб’ютор, працює з вашими товарами."

                Формат:
                Потенційний клієнт: Так/Ні
                Висновок: (одне речення)
                """

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )

                content = response.choices[0].message.content.strip()

                try:
                    client_match = re.search(r"Потенційний клієнт:\s*(Так|Ні)", content)
                    summary_match = re.search(r"Висновок:\s*(.+)", content)

                    is_client = client_match.group(1) if client_match else "-"
                    summary = summary_match.group(1).strip() if summary_match else content
                except Exception as parse_error:
                    is_client = "-"
                    summary = f"GPT format error: {parse_error}"

                status = "Аналізовано"

            except Exception as e:
                is_client = "-"
                summary = f"Помилка: {e}"
                status = "Помилка"

            # Додаємо до "Аналіз" чітко в 8 колонок
            analysis_row = [
                title or "-",     # Назва
                site or "-",      # Сайт
                keywords or "-",  # Ключові слова
                summary or "-",   # Висновок
                is_client or "-", # Потенційний клієнт
                page or "-",      # Сторінка
                date or "-",      # Дата
                status or "-"     # Статус GPT
            ]
            analysis_sheet.append_row(analysis_row, value_input_option="USER_ENTERED")
                        # Після запису в "Аналіз" оновлюємо статус в "Пошуки"
            try:
                search_sheet.update_cell(idx, 7, status)
            except Exception as update_error:
                st.warning(f"Не вдалося оновити статус для '{title}': {update_error}")


            analyzed_sites.add(site)
            analyzed_count += 1

        st.success(f"✅ GPT-аналіз виконано для {analyzed_count} нових записів.")

# --------------------- Завантаження назв компаній з вкладки ---------------------
st.header("📥 Завантаження назв компаній з іншої вкладки")

source_tab = st.text_input("Введи назву вкладки з компаніями:")
load_companies = st.button("Зчитати компанії та доповнити вкладку 'компанії'")

if load_companies and source_tab:
    try:
        gc = get_gsheet_client()
        sh = gc.open_by_key(GSHEET_SPREADSHEET_ID)
        ws = sh.worksheet(source_tab)
        data = ws.col_values(1)[1:]  # Пропускаємо заголовок

        # Отримуємо або створюємо вкладку "компанії"
        try:
            company_sheet = sh.worksheet("компанії")
            existing = set(name.strip().upper() for name in company_sheet.col_values(1)[1:])
        except:
            company_sheet = sh.add_worksheet(title="компанії", rows="1000", cols="1")
            company_sheet.update("A1", [["Компанії"]])
            existing = set()

        log_output = []
        new_entries = []

        for name in data:
            if not name:
                continue
            original = name
            name = name.strip().lower()
            for prefix in ["фоп", "тов", "пп"]:
                if name.startswith(prefix):
                    name = name[len(prefix):].strip()
            name = name.replace("«", "").replace("»", "").replace("\"", "")
            name = ' '.join(name.split())
            if len(name) > 2:
                cleaned = name.upper()
                if cleaned in existing or cleaned in [x[0] for x in new_entries]:
                    log_output.append(f"🔁 Пропущено повтор: {original}")
                else:
                    new_entries.append([cleaned])
                    log_output.append(f"➕ Додано: {cleaned}")

        if new_entries:
            next_row = len(existing) + 2  # +2 бо заголовок + 1-based
            company_sheet.update(f"A{next_row}:A{next_row + len(new_entries) - 1}", new_entries)

        st.success(f"✅ Додано нових компаній: {len(new_entries)}")
        st.markdown("### 📋 Журнал обробки:")
        for msg in log_output:
            st.markdown(msg)

    except Exception as e:
        st.error(f"❌ Помилка: {e}")
       # --------------------- Пошук сайтів за назвами з вкладки "компанії" ---------------------

st.header("🌐 Пошук сайтів за назвами компаній")

max_to_check = st.selectbox("Скільки компаній обробити за раз:", options=list(range(1, 21)), index=0)
start_search = st.button("🔍 Почати пошук сайтів")

if start_search:
    try:
        gc = get_gsheet_client()
        sh = gc.open_by_key(GSHEET_SPREADSHEET_ID)

        company_sheet = sh.worksheet("компанії")
        data = company_sheet.get_all_values()
        headers = data[0]

        # Додаємо колонку "Статус", якщо її немає
        if "Статус" not in headers:
            company_sheet.update_cell(1, 2, "Статус")
            headers.append("Статус")

        companies = data[1:]
        to_process = []
        for i, row in enumerate(companies, start=2):
            name = row[0].strip()
            status = row[1].strip() if len(row) > 1 else ""
            if name and not status:
                to_process.append((i, name))
            if len(to_process) >= max_to_check:
                break

        st.markdown(f"🔎 Залишилось до обробки: **{len(to_process)}** компаній")

        for row_index, name in to_process:
            debug_log = []
            params = {
                "key": st.secrets["GOOGLE_API_KEY"],
                "cx": st.secrets["CSE_ID"],
                "q": name,
                "num": 10
            }
            try:
                resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
                items = resp.json().get("items", [])

                found = False
                for item in items[:5]:
                    title = item.get("title", "")
                    link = item.get("link", "")
                    simplified = simplify_url(link)
                    page_text = get_page_text(simplified)

                    gpt_prompt = f"""
Ти — аналітик. Визначи, чи сайт належить компанії.

Назва компанії: {name}
Сайт: {simplified}
Опис сайту: {page_text}

Відповідай коротко:
Чи належить сайт цій компанії? Відповідь: Так або Ні.
"""
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": gpt_prompt}]
                        )
                        gpt_answer = response.choices[0].message.content.strip()
                    except Exception as gpt_err:
                        gpt_answer = f"GPT error: {gpt_err}"

                    debug_log.append(f"🔗 **{title}** — `{simplified}`\nGPT: _{gpt_answer}_")

                    if "так" in gpt_answer.lower():
                        company_sheet.update_cell(row_index, 2, "Знайдено")
                        st.markdown(f"✅ **{name}** → `{simplified}`")
                        found = True
                        break

                if not found:
                    company_sheet.update_cell(row_index, 2, "Не знайдено")
                    st.markdown(f"⚠️ **{name}** — сайт не підтверджено GPT")
                    with st.expander(f"📄 Перевірено сайти для: {name}"):
                        for entry in debug_log:
                            st.markdown(entry)

            except Exception as e:
                st.warning(f"❌ Помилка при обробці {name}: {e}")

        st.success(f"🏁 Пошук завершено. Оброблено: {len(to_process)} компаній.")

    except Exception as e:
        st.error(f"❌ Загальна помилка: {e}")
