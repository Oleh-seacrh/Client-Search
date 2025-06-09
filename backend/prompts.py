def prompt_is_potential_client(title, description, url, website=None):
    return f"""
    Назва: {title}
    Опис: {description}
    URL результату: {url}
    Вебсайт компанії: {website or "Не вказано"}

    Чи виглядає ця компанія як потенційний клієнт для компанії, яка продає медичні або NDT рентген-плівки?

    Відповідь тільки: Клієнт: Так або Клієнт: Ні
    """

def prompt_is_company_website(title, description, url):
    return f"""
    Назва компанії: {title}
    Опис сторінки: {description}
    URL: {url}

    Завдання:
    Визнач, чи цей сайт є офіційним сайтом компанії. Ігноруй маркетплейси, каталоги, Вікіпедію, агрегатори, посередників, форуми чи сайти-партнери.

    Бери до уваги тільки:
    - Згадку назви компанії на сайті
    - Логотип або контакти компанії
    - Відповідність назви компанії домену (наприклад, carestream → carestream.com)

    Якщо таких ознак немає — вважай, що це не сайт компанії.

    Відповідь строго у форматі:
    Сайт компанії: Так або Сайт компанії: Ні
    """

def prompt_get_category(title, description, url):
    return f"""
    Назва: {title}
    Опис: {description}
    URL результату: {url}

    Який тип компанії? Обери одну з категорій: Medical / NDT / Other

    Відповідь: Категорія: ...
    """

def prompt_get_country(description, url):
    return f"""
    Опис компанії або фрагмент: {description}
    URL: {url}

    В якій країні, найімовірніше, розташована ця компанія?

    Відповідь: Країна: ...
    """
def get_new_clients_from_tab(tab_name: str):
    import openai
    import pandas as pd

    gc = get_gsheet_client()
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])

    # Завантажуємо існуючі клієнти
    ws_client = sh.worksheet("Client")
    client_data = ws_client.get_all_records()
    client_df = pd.DataFrame(client_data)
    existing_emails = set(client_df["Email"].str.lower().fillna(""))
    existing_websites = set(client_df["Website"].str.lower().fillna(""))

    # Джерело по табу
    source_map = {
        "Аналіз": "Search",
        "результати": "TradeAtlas",
        "Email": "Email"
    }
    source = source_map.get(tab_name, "Unknown")

    # Завантажуємо нові дані
    ws_source = sh.worksheet(tab_name)
    source_data = ws_source.get_all_records()
    new_df = pd.DataFrame(source_data)

    # Формуємо JSON для GPT
    companies = []
    for row in new_df.to_dict("records"):
        website = str(row.get("Сайт") or row.get("Website") or "").strip().lower()
        email = str(row.get("Email") or row.get("Пошта") or "").strip().lower()

        if website in existing_websites or email in existing_emails:
            continue  # вже є

        companies.append({
            "Company": row.get("Назва компанії") or row.get("Company") or "",
            "Website": website,
            "Email": email,
            "Contact person": row.get("Contact person") or "",
            "Brand": row.get("Brand") or "",
            "Product": row.get("Product") or row.get("Продукт") or "",
            "Quantity": row.get("Quantity") or row.get("Кількість") or "",
            "Country": row.get("Country") or row.get("Країна") or "",
            "Source": source,
            "Status": "Новий",
            "Deal value": ""
        })

    return companies
