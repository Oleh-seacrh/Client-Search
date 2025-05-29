import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from streamlit.runtime.secrets import get_secret
import pandas as pd
from urllib.parse import urlparse

from backend.gsheet_service import get_gsheet_client
from backend.prompts import prompt_is_company_website
from backend.utils import get_page_text

def simplify_url(link: str) -> str:
    parsed = urlparse(link)
    return f"{parsed.scheme}://{parsed.netloc}"

def find_sites_for_companies(max_to_check: int, spreadsheet_id: str) -> list[str]:
    gc = get_gsheet_client()
    sh = gc.open_by_key(spreadsheet_id)

    # Отримуємо компанії
    company_sheet = sh.worksheet("компанії")
    data = company_sheet.get_all_values()
    headers = data[0]

    # Додаємо колонку "Статус", якщо немає
    if "Статус" not in headers:
        company_sheet.update_cell(1, 2, "Статус")
        headers.append("Статус")

    # Підготуємо вкладку "результати"
    try:
        results_sheet = sh.worksheet("результати")
    except:
        results_sheet = sh.add_worksheet(title="результати", rows="1000", cols="5")
        results_sheet.append_row(["Компанія", "Сайт", "Назва з Google", "Сторінка", "Дата"], value_input_option="USER_ENTERED")

    companies = data[1:]
    to_process = []
    for i, row in enumerate(companies, start=2):
        name = row[0].strip()
        status = row[1].strip() if len(row) > 1 else ""
        if name and not status:
            to_process.append((i, name))
        if len(to_process) >= max_to_check:
            break

    log_output = []
    for row_index, name in to_process:
        try:
            params = {
                "key": get_secret("GOOGLE_API_KEY"),
                "cx": get_secret("CSE_ID"),
                "q": name,
                "num": 10
            }
            resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
            items = resp.json().get("items", [])

            found = False
            debug_log = []

            for item in items[:5]:
                title = item.get("title", "")
                link = item.get("link", "")
                simplified = simplify_url(link)
                page_text = get_page_text(simplified)

                gpt_response = prompt_is_company_website(name, page_text, simplified)

                debug_log.append(f"🔗 **{title}** — `{simplified}`\nGPT: _{gpt_response}_")

                if "так" in gpt_response.lower():
                    today = pd.Timestamp.now().strftime("%Y-%m-%d")
                    company_sheet.update_cell(row_index, 2, "Знайдено")
                    results_sheet.append_row([name, simplified, title, "1", today], value_input_option="USER_ENTERED")
                    log_output.append(f"✅ **{name}** → `{simplified}`")
                    found = True
                    break

            if not found:
                company_sheet.update_cell(row_index, 2, "Не знайдено")
                log_output.append(f"⚠️ **{name}** — сайт не підтверджено GPT")
                for entry in debug_log:
                    log_output.append(entry)

        except Exception as e:
            log_output.append(f"❌ Помилка при обробці {name}: {e}")

    return log_output
