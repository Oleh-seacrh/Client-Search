import requests
import pandas as pd
from urllib.parse import urlparse
from backend.gsheet_service import get_gsheet_client, get_worksheet_by_name, read_existing_websites, append_rows
from backend.prompts import prompt_is_company_website
from backend.utils import get_page_text, call_gpt, simplify_url
import streamlit as st


def get_google_search_params(query: str) -> dict:
    return {
        "key": st.secrets["GOOGLE_API_KEY"],
        "cx": st.secrets["CSE_ID"],
        "q": query,
        "num": 10
    }


def find_company_websites(limit: int, spreadsheet_id: str) -> list[str]:
    """
    Шукає сайти компаній з вкладки 'Client' (ті, у кого порожній 'Website'),
    і додає підтверджені GPT-сайти назад у вкладку.
    """
    gc = get_gsheet_client()
    sh = gc.open_by_key(spreadsheet_id)

    ws = get_worksheet_by_name(sh, "Client")
    df = pd.DataFrame(ws.get_all_records())

    # Компанії без сайту
    df = df.fillna("")
    candidates = df[df["Website"] == ""].copy()
    if candidates.empty:
        return ["✅ No companies without websites."]

    existing_websites = set(df["Website"].str.lower())
    processed = 0
    logs = []

    for idx, row in candidates.iterrows():
        if processed >= limit:
            break

        name = row["Company"]
        if not name:
            continue

        try:
            params = get_google_search_params(name)
            resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
            items = resp.json().get("items", [])

            found = False
            debug_log = []

            for item in items[:5]:
                title = item.get("title", "")
                link = item.get("link", "")
                simplified = simplify_url(link)
                page_text = get_page_text(simplified)

                gpt_prompt = prompt_is_company_website(name, page_text, simplified)
                gpt_response = call_gpt(gpt_prompt)

                debug_log.append(f"🔗 **{title}** — {simplified}\nGPT: _{gpt_response}_")

                if "yes" in gpt_response.lower():
                    ws.update_cell(idx + 2, df.columns.get_loc("Website") + 1, simplified)
                    ws.update_cell(idx + 2, df.columns.get_loc("Source") + 1, "website_search")
                    ws.update_cell(idx + 2, df.columns.get_loc("Status") + 1, "Found")
                    logs.append(f"✅ **{name}** → {simplified}")
                    found = True
                    break

            if not found:
                ws.update_cell(idx + 2, df.columns.get_loc("Status") + 1, "Not found")
                logs.append(f"⚠️ **{name}** — no confirmed site")
                logs.extend(debug_log)

        except Exception as e:
            logs.append(f"❌ Error processing {name}: {e}")

        processed += 1

    return logs
