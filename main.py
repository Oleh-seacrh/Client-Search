import streamlit as st
import requests
import openai
import pandas as pd
import re
from urllib.parse import urlparse

# 🔐 Секрети зі Streamlit Cloud
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
CSE_ID = st.secrets["CSE_ID"]

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Очищення до головної сторінки
def simplify_url(link):
    parsed = urlparse(link)
    return f"{parsed.scheme}://{parsed.netloc}"

# Витягування першої пошти зі snippet
def extract_email(text):
    match = re.search(r"[\w\.-]+@[\w\.-]+", text)
    return match.group(0) if match else "—"

# GPT-аналіз з додатковими питаннями
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
start = st.button("Пошук")

if start and query:
    with st.spinner("Пошук та GPT-аналіз..."):
        results = requests.get(f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={CSE_ID}&q={query}").json().get("items", [])
        all_data = []

        for item in results:
            title = item["title"]
            link = simplify_url(item["link"])
            snippet = item.get("snippet", "")
            email = extract_email(snippet)

            try:
                gpt_response = analyze_with_gpt(title, snippet, link)
                client_result, org_type = gpt_response.split("Тип:", 1)
                client_result = client_result.strip().replace("Клієнт:", "").strip()
                org_type = org_type.strip()
            except Exception as e:
                client_result = f"Помилка: {e}"
                org_type = "Невизначено"

            all_data.append({
                "Назва": title,
                "Домашня сторінка": link,
                "Пошта": email,
                "Тип": org_type,
                "GPT-висновок": client_result,
                "Опис": snippet
            })

        if not all_data:
            st.warning("Немає результатів.")
        else:
            df = pd.DataFrame(all_data)
            st.success("Готово!")
            for row in df.itertuples(index=False):
                with st.expander(f"🔗 {row.Назва}"):
                    st.markdown(f"**Домашня сторінка:** [{row.Посилання}]({row.Посилання})")
                    st.markdown(f"**Пошта:** {row.Пошта}")
                    st.markdown(f"**Тип:** {row.Тип}")
                    st.markdown(f"**GPT-висновок:** {row._5}")
                    st.markdown(f"**Опис:** {row.Опис}")
                    st.markdown("---")

            st.download_button("⬇️ Завантажити CSV", data=df.to_csv(index=False, encoding="utf-8-sig"), file_name="gpt_google_results.csv", mime="text/csv")
