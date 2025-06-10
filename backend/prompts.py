def prompt_is_potential_client(title: str, description: str, url: str, website: str = None) -> str:
    return f"""
    Company Name: {title}
    Description: {description}
    Search Result URL: {url}
    Website: {website or "Not specified"}

    Is this company a potential client for a business that sells medical or NDT X-ray films?

    Respond only in this format:
    Client: Yes or Client: No
    """


def prompt_is_company_website(title: str, description: str, url: str) -> str:
    return f"""
    Company Name: {title}
    Page Description: {description}
    URL: {url}

    Task:
    Determine whether this is the official website of the company. Ignore marketplaces, directories, Wikipedia, aggregators, partners, or forums.

    Consider only:
    - The company name being explicitly mentioned on the page
    - Company logo or direct contact details
    - Domain matching the company name (e.g., carestream → carestream.com)

    If none of these are found, assume it's not the official website.

    Respond only in this format:
    Company Website: Yes or Company Website: No
    """


def prompt_get_category(title: str, description: str, url: str) -> str:
    return f"""
    Company Name: {title}
    Description: {description}
    URL: {url}

    What type of company is this? Choose one of the following categories:
    Medical / NDT / Other

    Response format:
    Category: ...
    """


def prompt_get_country(description: str, url: str) -> str:
    return f"""
    Description or snippet about the company: {description}
    URL: {url}

    In which country is this company most likely located?

    Response format:
    Country: ...
    """
