import streamlit as st
from backend.company_loader import load_companies_from_tab
from backend.site_finder import find_sites_for_companies
from backend.gpt_analyzer import analyze_sites_from_results

def render_search_tab():
    st.header("📥 Завантаження назв компаній з іншої вкладки")

    source_tab = st.text_input("Введи назву вкладки з компаніями:")
    if st.button("Зчитати компанії та доповнити вкладку 'компанії'"):
        if source_tab:
            try:
                logs, count = load_companies_from_tab(source_tab, st.secrets["spreadsheet_id"])
                st.success(f"✅ Додано нових компаній: {count}")
                st.markdown("### 📋 Журнал обробки:")
                for msg in logs:
                    st.markdown(msg)
            except Exception as e:
                st.error(f"❌ Помилка: {e}")

    st.header("🌐 Пошук сайтів за назвами компаній")

    max_to_check = st.selectbox("Скільки компаній обробити за раз:", options=list(range(1, 21)), index=0)
    if st.button("🔍 Почати пошук сайтів"):
        try:
            logs = find_sites_for_companies(max_to_check, st.secrets["spreadsheet_id"])
            st.success("🏁 Пошук завершено.")
            for msg in logs:
                st.markdown(msg)
        except Exception as e:
            st.error(f"❌ Помилка під час пошуку сайтів: {e}")

    st.header("🧠 GPT-Аналіз сайтів з вкладки 'результати'")

    if st.button("🔍 Запустити аналіз (до 20 нових записів)"):
        try:
            logs = analyze_sites_from_results(st.secrets["spreadsheet_id"], limit=20)
            st.success("✅ GPT проаналізував сайти.")
            for msg in logs:
                st.markdown(msg)
        except Exception as e:
            st.error(f"❌ Помилка GPT-аналізу: {e}")
