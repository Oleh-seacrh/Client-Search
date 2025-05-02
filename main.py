import streamlit as st
import requests
import openai
import pandas as pd

# 🔐 Читання секретів із Streamlit Cloud
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
CSE_ID = st.secrets["CSE_ID"]

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def google_search(query):
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={CSE_ID}&q={query}"
    response = requests.get(url)
    return response.json().get("items", [])

def is_blocked(title, snippet, link):
    BLOCKED_KEYWORDS = ["agfa", "carestream", "fujifilm", "official", "manufacturer", "corporate", "global"]
    combined = f"{title} {snippet} {link}".lower()
    return any(word in combined for word in BLOCKED_KEYWORDS)

def analyze_with_gpt(title, snippet, link):
    prompt = f"""
    Ти допомагаєш аналізувати результати пошуку, щоб визначити, чи сайт може бути потенційним клієнтом для медичної продукції (Agfa, Fujifilm, Carestream).

    🔹 Назва: {title}
    🔹 Опис: {snippet}
    🔹 Лінк: {link}

    Відповідай коротко: Так або Ні — і коротке пояснення (1 речення).
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
        results = google_search(query)
        all_data = []

        for item in results:
            title = item["title"]
            link = item["link"]
            snippet = item.get("snippet", "")

            if is_blocked(title, snippet, link):
                continue

            try:
                gpt_response = analyze_with_gpt(title, snippet, link)
            except Exception as e:
                gpt_response = f"Помилка: {e}"

            all_data.append({
                "Назва": title,
                "Посилання": link,
                "Опис": snippet,
                "GPT-висновок": gpt_response
            })

        if not all_data:
            st.warning("Немає результатів після фільтрації.")
        else:
            df = pd.DataFrame(all_data)
            st.success("Готово!")
            st.dataframe(df)
            df.to_csv("gpt_google_results.csv", index=False, encoding="utf-8-sig")
            st.download_button("⬇️ Завантажити CSV", data=df.to_csv(index=False, encoding="utf-8-sig"), file_name="gpt_google_results.csv", mime="text/csv")
