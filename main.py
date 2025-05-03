
import streamlit as st
import openai
import requests
from bs4 import BeautifulSoup
import re
import os
import gspread
from google.oauth2.service_account import Credentials

# Налаштування OpenAI
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Налаштування Google Sheets
GSHEET_SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
GSHEET_CREDS = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=GSHEET_SCOPE)
GSHEET_SPREADSHEET_ID = st.secrets["GSHEET_SPREADSHEET_ID"]
gc = gspread.authorize(GSHEET_CREDS)
sh = gc.open_by_key(GSHEET_SPREADSHEET_ID)

# Створити вкладку за ключовим словом, якщо її не існує
def get_or_create_worksheet(keyword):
    try:
        worksheet = sh.worksheet(keyword)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=keyword, rows="1000", cols="20")
        worksheet.append_row(["Назва компанії", "Сайт", "Пошта", "Тип", "Країна", "Відгук GPT"])
    return worksheet

# Отримати домен сайту
def extract_homepage(url):
    match = re.search(r"(https?://[^/]+)", url)
    return match.group(1) if match else url

# Отримати текст із сайту
def fetch_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        return ""

# Отримати email зі сторінки
def extract_email_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", response.text))
        return list(emails)[0] if emails else "-"
    except:
        return "-"

# Згенерувати висновок GPT
def analyze_with_gpt(context, site_text, url):
    prompt = f"""
Вивчи сайт компанії за адресою: {url}.
Контекст: ми займаємось продажем рентген-плівки, більше на сайті: {context}
1. Чи може компанія бути нашим потенційним клієнтом? (тільки якщо вона не є виробником плівки, а також не є офіційним представництвом виробника, наприклад Fujifilm India).
2. Визнач хто ця компанія (тип: дистриб'ютор, реселер, клініка, виробник і т.д.).
3. Визнач країну (з контенту або контактів).
4. Визнач пошту (якщо є).

Формат відповіді:
Клієнт: Так/Ні — коротке обґрунтування.
Тип: ...
Пошта: ...
Країна: ...
"""

   try:
    completion = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ти аналізуєш контент сайту і визначаєш потенційних клієнтів."},
            {"role": "user", "content": prompt + "\n\nКонтент сайту:\n" + site_text[:4000]}
        ]
    )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Помилка: {str(e)}"

# Побудова інтерфейсу
st.title("🔍 Пошук потенційних клієнтів через Google + GPT")
keyword = st.text_input("Введи ключові слова:")
limit = st.slider("Кількість результатів", 1, 50, 10)
start = st.number_input("Починати з результату №", 1, 100, 1)
search_button = st.button("Пошук")

if search_button and keyword:
    from googlesearch import search
    worksheet = get_or_create_worksheet(keyword)
    homepage_set = set([row[1] for row in worksheet.get_all_values()[1:]])

    for url in search(keyword, num_results=limit, start=start - 1):
        homepage = extract_homepage(url)
        if homepage in homepage_set:
            continue

        site_text = fetch_text_from_url(url)
        email = extract_email_from_url(url)
        gpt_response = analyze_with_gpt("https://www.xraymedem.com/", site_text, url)

        # Витягуємо ключові частини
        client_match = re.search(r"Клієнт: (Так|Ні)(.*?)\n", gpt_response)
        is_client = client_match.group(1) if client_match else "Ні"

        if is_client == "Так":
            company_name = homepage.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "").split(".")[0].capitalize()
            company_type_match = re.search(r"Тип: (.*?)\n", gpt_response)
            company_type = company_type_match.group(1).strip() if company_type_match else "-"

            email_match = re.search(r"Пошта: ([^\n]+)", gpt_response)
            email = email_match.group(1).strip() if email_match else "-"
            if "не вказано" in email.lower() or "інформацію" in email.lower():
                email = "-"

            country_match = re.search(r"Країна: ([^\n]+)", gpt_response)
            country = country_match.group(1).strip() if country_match else "-"
            if "не вдалося" in country.lower() or "важко" in country.lower():
                country = "-"

            worksheet.append_row([company_name, homepage, email, company_type, country, gpt_response])
            st.success(f"✅ Додано: {company_name}")

    st.success("Готово!")
