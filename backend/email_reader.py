import imaplib
import email
from email.header import decode_header
import re

IMAP_SERVER = "mail.dhosting.pl"
EMAIL_ACCOUNT = "sales@xraymedem.com"
EMAIL_PASSWORD = "B8^Mz57y2#fG9OXWCySQXaQN"  # краще зберігати в .env

def clean(text):
    return re.sub(r'\s+', ' ', text).strip()

def get_latest_emails(limit=10):
    # Підключення
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)

    # Вибираємо папку INBOX
    mail.select("inbox")

    # Шукаємо всі листи (можна додати фільтр за темою/міткою)
    result, data = mail.search(None, "ALL")
    email_ids = data[0].split()
    latest_ids = email_ids[-limit:]

    emails = []

    for eid in latest_ids:
        res, msg_data = mail.fetch(eid, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")

        from_ = msg.get("From")
        body = ""

        # Витягуємо тіло
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        emails.append({
            "from": clean(from_),
            "subject": clean(subject),
            "body": clean(body[:2000])  # обрізаємо, щоб не було надто довго
        })

    mail.logout()
    return emails
