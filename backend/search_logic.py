from backend.prompts import (
    prompt_is_potential_client,
    prompt_is_company_website,
    prompt_get_category,
    prompt_get_country
)

from backend.utils import call_gpt, extract_email, simplify_url


def analyze_site(result: dict) -> dict:
    """
    Приймає 1 результат пошуку {title, description, link}
    Виконує GPT-аналіз + email-видобуток
    Повертає розширений dict з усіма колонками
    """

    title = result.get("title", "")
    description = result.get("description", "")
    link = result.get("link", "")
    simplified_url = simplify_url(link)

    # GPT перевірки
    try:
        gpt_client = call_gpt(prompt_is_potential_client(title, description, link))
        gpt_company = call_gpt(prompt_is_company_website(title, description, link))
        gpt_category = call_gpt(prompt_get_category(title, description, link))
        gpt_country = call_gpt(prompt_get_country(description, link))
    except Exception as e:
        gpt_client = gpt_company = gpt_category = gpt_country = "GPT Error"

    # Витяг email (наразі — з опису, можна розширити до HTML у майбутньому)
    email = extract_email(description)

    return {
        "Назва": title,
        "Сайт": simplified_url,
        "Email": email,
        "Категорія": gpt_category.replace("Категорія:", "").strip(),
        "Країна": gpt_country.replace("Країна:", "").strip(),
        "GPT: Клієнт": gpt_client.replace("Клієнт:", "").strip(),
        "GPT: Сайт компанії": gpt_company.replace("Сайт компанії:", "").strip(),
        "Опис": description,
        "Джерело": link
    }

