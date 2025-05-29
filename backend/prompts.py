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
    Назва: {title}
    Опис: {description}
    URL результату: {url}

    Чи це офіційний сайт компанії (а не агрегатор, магазин, маркетплейс, блог чи форум)?

    Відповідь: Сайт компанії: Так або Сайт компанії: Ні
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
