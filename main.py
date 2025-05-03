
# Оновлено: нормалізація email, країни та відгуку GPT
import streamlit as st
import requests
import openai
import re
from urllib.parse import urlparse
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GSHEET_JSON = st.secrets["GSHEET_SERVICE_ACCOUNT"]
GSHEET_SPREADSHEET_ID = "1S0nkJYXrVTsMHmeOC-uvMWnrw_yQi5z8NzRsJEcBjc0"

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def extract_email_and_country(gpt_response):
    import re
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", gpt_response)
    email = email_match.group(0).strip() if email_match else "-"

    country_match = re.search(r"Країна: ([^\n\r]+)", gpt_response)
    country = country_match.group(1).strip() if country_match else "-"

    if any(x in country.lower() for x in ["не вдалося", "важко", "невідомо", "невизначено"]):
        country = "-"

    if any(x in email.lower() for x in ["не вказано", "інформацію", "email не знайдено"]):
        email = "-"

    return email, country


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
    Ти — асистент з продажу в компанії, яка займається постачанням рентген-плівки, касет, принтерів та медичних витратних матеріалів.

Вебсайт нашої компанії: https://www.xraymedem.com

 Завдання:
На основі інформації нижче (назви, опису та сторінки), визнач:
— Чи може компанія бути нашим потенційним клієнтом?
— Її тип (тільки одне слово: дистриб'ютор, реселер, виробник, постачальник, платформа тощо)
— Країну (одним словом: наприклад, Китай, Індія, США, Оман...)

 Вхідні дані:
Назва (Google): {title}  
Опис: {snippet}  
Лінк: {link}

 ВАЖЛИВО:
— Потенційні клієнти: всі, хто продає або згадує рентген-плівку, касети, медичні принтери.  
— Це можуть бути: дистриб’ютори, реселери, постачальники, конкуренти.  
— Не вважати клієнтом офіційне представництво виробника (наприклад, "Fujifilm India", якщо це підрозділ бренду).  
— Навіть офіційні дистриб’ютори бренду — це наші потенційні клієнти.

 Визначення країни — за такими ознаками:
— домен сайту (.cn, .in, .ua, .com тощо)  
— назва міста або країни в описі (наприклад: Shenzhen, China)  
— міжнародний код телефону (+86 = Китай)  
— згадка в назві або структурі (наприклад "India Pvt Ltd")

 Формат відповіді:
Назва компанії: ...  
Клієнт: Так/Ні — (пояснення)  
Тип: ... (одним словом)  
Пошта: ...  
Країна: ... (одним словом, лише назва країни)
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

st.set_page_config(page_title="Пошук клієнтів GPT", layout="wide")
st.title("🔍 Пошук")

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
            sheet = sh.add_worksheet(title=tab_name, rows="1000", cols="6")
            sheet.append_row(["Назва компанії", "Сайт", "Пошта", "Тип", "Країна", "Відгук GPT"])

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
    client_match = re.search(r"Клієнт: (Так|Ні)", gpt_response)

    name = name_match.group(1).strip() if name_match else title
    org_type = type_match.group(1).strip() if type_match else "-"
    client_status = f"Клієнт: {client_match.group(1)}" if client_match else "-"

    email, country = extract_email_and_country(gpt_response)

    if email.lower().startswith("інформація"):
        email = "-"
    if country.lower().startswith("інформація"):
        country = "-"

    sheet.append_row([name, link, email, org_type, country, client_status], value_input_option="USER_ENTERED")
    existing_links.add(link)

        st.success(f"✅ Дані збережено до вкладки '{tab_name}' з країною, типом і фільтром по 'Клієнт: Так'")
