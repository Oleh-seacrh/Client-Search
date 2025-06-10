import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
from backend.search_logic import perform_search_and_analysis
from backend.gsheet_service import get_gsheet_client, get_worksheet_by_name
from backend.company_loader import get_new_clients_from_tab
from backend.gpt_analyzer import analyze_sites_from_client_tab

# App config
st.set_page_config(page_title="SAM – Search and Analysis Machine", layout="wide")
st.title("🔍 Search and Analysis Machine")

gsheet_id = st.secrets["spreadsheet_id"]

# Tabs
tab1, tab2, tab3 = st.tabs(["🔎 Search", "📇 CRM", "🧠 GPT Analysis"])


# 🔎 TAB 1 — Search
with tab1:
    st.subheader("Search websites by keyword")

    keyword = st.text_input("Enter search keyword:")
    num_results = st.slider("Number of results:", min_value=10, max_value=100, step=10, value=20)

    col1, col2 = st.columns(2)
    with col1:
        from_result = st.number_input("Start from result #", min_value=0, value=0, step=10)

    with col2:
        only_new = st.checkbox("Only analyze new websites", value=True)

    if st.button("Start Search", key="start_site_search") and keyword:
        with st.spinner("Searching and analyzing..."):
            gc = get_gsheet_client()
            results = perform_search_and_analysis(keyword, gc, gsheet_id, only_new, num_results, from_result)
            st.success(f"✅ Saved {len(results)} new entries.")

# 📇 TAB 2 — CRM
with tab2:
    st.subheader("Client Database (tab: 'Client')")

    try:
        gc = get_gsheet_client()
        sheet = gc.open_by_key(gsheet_id)
        ws = get_worksheet_by_name(sheet, "Client")
        data = ws.get_all_records()
        df = pd.DataFrame(data)

        filter_yes = st.checkbox("Show only potential clients (Client: Yes)", value=False)
        if filter_yes:
            df = df[df["Client"].str.lower() == "yes"]

        st.dataframe(df)

    except Exception as e:
        st.error(f"❌ Failed to load data: {e}")

# 🧠 TAB 3 — GPT Analysis
with tab3:
    st.subheader("Run GPT analysis on new client records")

    if st.button("Analyze up to 20 new records", key="analyze_client_tab"):
        with st.spinner("GPT analyzing..."):
            logs = analyze_sites_from_client_tab(gsheet_id, limit=20)
            for log in logs:
                st.markdown(log)
