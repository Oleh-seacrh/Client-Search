import streamlit as st
from process_emails import process_email_batch

def render_email_process_tab():
    st.subheader("📨 Обробка нових листів (IMAP + GPT)")

    if st.button("🔍 Обробити 5 нових листів"):
        with st.spinner("Обробка... GPT працює..."):
            try:
                process_email_batch(limit=5)
                st.success("✅ Обробка завершена. Дані збережено в Google Sheets.")
            except Exception as e:
                st.error(f"❌ Помилка: {e}")
