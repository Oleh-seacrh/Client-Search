
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
    num_results = st.slider("Кількість результатів", min_value=10, max_value=100, value=10, step=10)
with col2:
    start_index = st.number_input("Починати з результату №", min_value=1, max_value=91, value=1, step=10)

filter_yes_only = st.checkbox("Показати лише 'Клієнт: Так'")

start = st.button("Пошук")

if start and query:
    with st.spinner("Пошук та GPT-аналіз..."):
        params = {
            "key": GOOGLE_API_KEY,
            "cx": CSE_ID,
            "q": query,
            "num": num_results,
            "start": start_index
        }
        results = requests.get("https://www.googleapis.com/customsearch/v1", params=params).json().get("items", [])
        all_data = []

        for item in results:
            title = item["title"]
            raw_link = item["link"]
            link = simplify_url(raw_link)
            snippet = item.get("snippet", "")
            email = extract_email(title + " " + snippet)

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
            if filter_yes_only:
                df = df[df["GPT-висновок"].str.startswith("Так")]

            if df.empty:
                st.info("Немає результатів, які відповідають фільтру 'Клієнт: Так'")
            else:
                st.success("Готово!")
                for i in range(len(df)):
                    with st.expander(f"🔗 {df.iloc[i]['Назва']}"):
                        st.markdown(f"**Домашня сторінка:** [{df.iloc[i]['Домашня сторінка']}]({df.iloc[i]['Домашня сторінка']})")
                        st.markdown(f"**Пошта:** {df.iloc[i]['Пошта']}")
                        st.markdown(f"**Тип:** {df.iloc[i]['Тип']}")
                        st.markdown(f"**GPT-висновок:** {df.iloc[i]['GPT-висновок']}")
                        st.markdown(f"**Опис:** {df.iloc[i]['Опис']}")
                        st.markdown("---")

                st.download_button("⬇️ Завантажити CSV", data=df.to_csv(index=False, encoding="utf-8-sig"), file_name="gpt_google_results.csv", mime="text/csv")
