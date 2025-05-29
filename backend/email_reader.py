import imaplib
import email
from email.header import decode_header
import re
import hashlib

IMAP_SERVER = "mail.dhosting.pl"
EMAIL_ACCOUNT = "sales@xraymedem.com"
EMAIL_PASSWORD = "..."  # бажано з .env

def clean(text):
    return re.sub(r'\s+', ' ', text).strip()

def generate_hash(from_, subject, body):
    text = f"{from_}|{subject}|{body[:500]}"
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_next_emails_batch(limit=5, known_hashes=None):
    if known_hashes is None:
        known_hashes = set()

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("inbox")

    result, data = mail.search(None, "ALL")
    email_ids = data[0].split()

    results = []

    for eid in email_ids:
        if len(results) >= limit:
            break

        res, msg_data = mail.fetch(eid, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")

        from_ = msg.get("From")
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        from_ = clean(from_)
        subject = clean(subject)
        body = clean(body)

        h = generate_hash(from_, subject, body)

        if h in known_hashes:
            continue

        results.append({
            "from": from_,
            "subject": subject,
            "body": body,
            "hash": h
        })

    mail.logout()
    return results
