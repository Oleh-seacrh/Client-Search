import imaplib
import email
from email.header import decode_header
import hashlib
import re
import openai
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# =================== НАЛАШТУВАННЯ ====================

EMAIL_ACCOUNT = "sales@xraymedem.com"
EMAIL_PASSWORD = st.secrets["email_password"]  # додай у secrets.toml
IMAP_SERVER = "mail.dhosting.pl"
IMAP_FOLDER = "INBOX"
SPREADSHEET_ID = st.secrets["spreadsheet_id"]
OPENAI_API_KEY = st.secrets["openai_api_key"]

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)

HEADERS = [
    "Email", "Сайт", "Телефон", "Бренд", "Продукт",
    "Кількість", "Хто звернувся", "Повний текст", "Hash"
]

# =================== GPT АНАЛІЗ ======================

openai.api_key = OPENAI_API_KEY

def analyze_with_gpt(text):
    prompt = f"""
Проаналізуй наступний текст листа. Поверни Python-словник з ключами:
- "бренд"
- "продукт"
- "кількість"
- "ініціатор" (хто першим звернувся: "Клієнт" або "Ми")

Ось текст:
{text}
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    try:
        result = eval(response.choices[0].message["content"])
        return result
    except:
        return {}

# =================== EMAIL + HASH ======================

def clean(text):
    return re.sub(r'\s+', ' ', text).strip()

def extract_email_address(from_field):
    match = re.search(r'[\w\.-]+@[\w\.-]+', from_field)
    return match.group(0) if match else ""

def extract_url(text):
    match = re.search(r'https?://[^\s]+', text)
    return match.group(0) if match else ""

def extract_phone(text):
    match = re.search(r'\+?\d[\d\s\-\(\)]{7,}', text)
    return match.group(0) if match else ""

def generate_hash(sender, subject, body):
    key = f"{sender}|{subject}|{body[:500]}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()

# =================== GOOGLE SHEETS ======================

def get_existing_hashes():
    gc = gspread.authorize(CREDS)
    sh = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws = sh.worksheet("Email")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="Email", rows="1000", cols="20")
        ws.append_row(HEADERS)
        return set()

    data = ws.get_all_records()
    return set(row.get("Hash") for row in data if "Hash" in row)

def append_to_sheet(row_dict):
    gc = gspread.authorize(CREDS)
    sh = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws = sh.worksheet("Email")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="Email", rows="1000", cols="20")
        ws.append_row(HEADERS)

    existing = ws.get_all_values()
    if not existing or existing[0] != HEADERS:
        ws.clear()
        ws.append_row(HEADERS)

    row = [row_dict.get(col, "") for col in HEADERS]
    ws.append_row(row)

# =================== ОБРОБКА ЛИСТІВ ======================

def process_email_batch(limit=5):
    known_hashes = get_existing_hashes()

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select(IMAP_FOLDER)

    result, data = mail.search(None, "ALL")
    email_ids = data[0].split()

    processed = 0

    for eid in email_ids:
        if processed >= limit:
            break

        res, msg_data = mail.fetch(eid, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")
        subject = clean(subject)

        from_ = clean(msg.get("From"))
        sender_email = extract_email_address(from_)

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")
        body = clean(body)

        hash_ = generate_hash(sender_email, subject, body)
        if hash_ in known_hashes:
            continue

        gpt_result = analyze_with_gpt(body)

        row = {
            "Email": sender_email,
            "Сайт": extract_url(body),
            "Телефон": extract_phone(body),
            "Бренд": gpt_result.get("бренд", ""),
            "Продукт": gpt_result.get("продукт", ""),
            "Кількість": gpt_result.get("кількість", ""),
            "Хто звернувся": gpt_result.get("ініціатор", ""),
            "Повний текст": body,
            "Hash": hash_
        }

        append_to_sheet(row)
        processed += 1

    mail.logout()
    print(f"✅ Оброблено {processed} нових листів.")

# =================== ЗАПУСК ======================

if __name__ == "__main__":
    process_email_batch(limit=5)
