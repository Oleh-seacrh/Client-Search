
import streamlit as st
import requests
import openai
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

def analyze_with_gpt(title, snippet, link):
    prompt = f"""
    Ви є асистентом з продажів у компанії, яка займається постачанням рентген-плівки, касет, принтерів та медичних витратних матеріалів.

    Вебсайт компанії: https://www.xraymedem.com

    Ваше завдання — оцінити, чи сайт, знайдений через Google, є потенційним клієнтом для нашої продукції.

    🔹 Назва (Google): {title}
    🔹 Опис: {snippet}
    🔹 Лінк: {link}

    ❗ ВАЖЛИВО:
    Всі, хто згадує або продає рентген-плівку, касети, медичні принтери — є потенційними клієнтами.
    Це включає конкурентів, реселерів, постачальників і дистриб’юторів.
    ❌ Не враховуйте лише офіційні представництва виробника (наприклад, "Fujifilm India", якщо це підрозділ бренду).
    ✅ Навіть офіційні дистриб’ютори — це потенційні клієнти.

    Дайте відповідь у форматі:
    Назва компанії: ...
    Клієнт: Так/Ні — ...
    Тип: ...
    Пошта: ...
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
            sheet = sh.add_worksheet(title=tab_name, rows="1000", cols="5")
            sheet.append_row(["Назва компанії", "Сайт", "Пошта", "Тип", "Відгук GPT"])

        existing_links = set(sheet.col_values(2))

        for item in results:
            title = item["title"]
            raw_link = item["link"]
            link = simplify_url(raw_link)
            if link in existing_links:
                continue

            snippet = item.get("snippet", "")

            try:
                gpt_response = analyze_with_gpt(title, snippet, link)
            except Exception as e:
                gpt_response = f"Помилка: {e}"

            st.markdown(f"### 🔎 [{title}]({link})")
            st.markdown("🧠 **GPT:**")
            st.code(gpt_response, language="markdown")

            if "Клієнт: Так" in gpt_response:
                name_match = re.search(r"Назва компанії: (.+)", gpt_response)
                type_match = re.search(r"Тип: (.+)", gpt_response)
                email_match = re.search(r"Пошта: (.+)", gpt_response)

                name = name_match.group(1).strip() if name_match else title
                org_type = type_match.group(1).strip() if type_match else "—"
                email = email_match.group(1).strip() if email_match else "—"

                sheet.append_row([name, link, email, org_type, gpt_response], value_input_option="USER_ENTERED")
                existing_links.add(link)

        st.success(f"✅ Дані збережено до вкладки '{tab_name}' (з email, типом і фільтром по 'Клієнт: Так')")
