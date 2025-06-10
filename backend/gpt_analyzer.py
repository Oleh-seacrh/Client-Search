import re
from backend.utils import gpt_call
from backend.gsheet_service import get_gsheet_client
from backend.prompts import prompt_get_category, prompt_is_potential_client


def analyze_sites_from_client_tab(spreadsheet_id: str, limit: int = 20) -> list[str]:
    gc = get_gsheet_client()
    sh = gc.open_by_key(spreadsheet_id)

    try:
        sheet = sh.worksheet("Client")
    except:
        return ["❌ Sheet 'Client' not found."]

    data = sheet.get_all_values()
    headers = data[0]
    rows = data[1:]

    # Ensure required columns exist
    required_cols = ["Category", "GPT", "Client"]
    missing_cols = [col for col in required_cols if col not in headers]

    if missing_cols:
        headers += missing_cols
        sheet.update("A1", [headers])
        # Re-read to get updated structure
        data = sheet.get_all_values()
        headers = data[0]
        rows = data[1:]

    # Indexes of required columns
    col_count = len(headers)
    col_index = {h: i for i, h in enumerate(headers)}
    analyze_indices = []

    for i, row in enumerate(rows):
        # Condition: missing any of [Category, GPT, Client]
        row_extended = row + [""] * (col_count - len(row))
        if not row_extended[col_index["Category"]].strip() or not row_extended[col_index["Client"]].strip():
            analyze_indices.append(i + 2)  # 1-based, with header row
        if len(analyze_indices) >= limit:
            break

    logs = []
    for row_num in analyze_indices:
        row = sheet.row_values(row_num)
        title = row[col_index.get("Company", 0)]
        url = row[col_index.get("Website", 1)]

        try:
            category_prompt = prompt_get_category(title, "", url)
            verdict_prompt = prompt_is_potential_client(title, "", url, url)

            category_response = gpt_call(category_prompt)
            verdict_response = gpt_call(verdict_prompt)
        except Exception as e:
            logs.append(f"❌ GPT error on `{title}`: {e}")
            continue

        # Extract GPT answers
        category = "-"
        verdict = "-"
        gpt_comment = ""

        cat_match = re.search(r"Category:\s*(.*)", category_response)
        if cat_match:
            category = cat_match.group(1).strip()

        verdict_match = re.search(r"Client:\s*(.*)", verdict_response)
        if verdict_match:
            verdict = verdict_match.group(1).strip()
            gpt_comment = verdict_response.strip()

        # Update cells
        sheet.update_cell(row_num, col_index["Category"] + 1, category)
        sheet.update_cell(row_num, col_index["Client"] + 1, verdict)
        sheet.update_cell(row_num, col_index["GPT"] + 1, gpt_comment)

        logs.append(f"🔍 `{title}` → `{category}` / `{verdict}`")

    return logs
