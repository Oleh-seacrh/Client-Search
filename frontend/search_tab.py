import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from backend.company_loader import get_new_clients_from_tab
from backend.site_finder import find_company_websites
from backend.gpt_analyzer import analyze_sites_from_client_tab
from backend.gsheet_service import get_gsheet_client, append_rows
import pandas as pd


def render_search_tab():
    st.header("📥 Load companies from another sheet")

    source_tab = st.text_input("Enter the name of the source sheet:")
    if st.button("📤 Import companies to 'Client'"):
        if source_tab:
            try:
                new_clients = get_new_clients_from_tab(source_tab)
                if not new_clients:
                    st.success("✅ No new companies found.")
                else:
                    df_new = pd.DataFrame(new_clients)
                    st.dataframe(df_new)

                    if st.button("✅ Append to Client"):
                        ws = get_gsheet_client().open_by_key(st.secrets["spreadsheet_id"]).worksheet("Client")
                        ws.append_rows(df_new.values.tolist(), value_input_option="USER_ENTERED")
                        st.success("🎉 Added to Client!")
            except Exception as e:
                st.error(f"❌ Error while loading companies: {e}")

    st.header("🌐 Find websites for companies")

    max_to_check = st.selectbox("How many companies to process at once:", options=list(range(1, 21)), index=0)
    if st.button("🔍 Start website search"):
        try:
            logs = find_company_websites(max_to_check, st.secrets["spreadsheet_id"])
            st.success("🏁 Website search completed.")
            for msg in logs:
                st.markdown(msg)
        except Exception as e:
            st.error(f"❌ Error while searching websites: {e}")

    st.header("🧠 GPT Analysis from 'Client' tab")

    if st.button("🤖 Run GPT analysis (up to 20 new records)"):
        try:
            logs = analyze_sites_from_client_tab(st.secrets["spreadsheet_id"], limit=20)
            st.success("✅ GPT analysis complete.")
            for msg in logs:
                st.markdown(msg)
        except Exception as e:
            st.error(f"❌ GPT error: {e}")
