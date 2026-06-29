"""
email_parser.py
---------------
Turns a raw email (RFC822 headers, loose "Subject:/From:" text, or a bare body)
into structured fields: subject, from_name, from_email, to, date, body.

This is the piece that fixes "Subject/From/To/Date are buried in body text".
It is also the seam for a future real-Outlook swap: Microsoft Graph already
returns these fields structured, so a Graph-backed connector would populate the
same dict and the Email Agent downstream wouldn't change at all.
"""

import re
from email.parser import Parser
from email.utils import parseaddr


def parse_email(raw: str) -> dict:
    msg = Parser().parsestr(raw)

    subject = msg.get("Subject")
    sender = msg.get("From")
    to = msg.get("To")
    date = msg.get("Date") or msg.get("Sent")
    body = msg.get_payload() if msg.get_payload() else ""

    # Fallback regex for loose "Header: value" lines the RFC parser missed
    def grab(field):
        m = re.search(rf"^{field}\s*:\s*(.+)$", raw, re.IGNORECASE | re.MULTILINE)
        return m.group(1).strip() if m else None

    subject = subject or grab("Subject")
    sender = sender or grab("From")
    to = to or grab("To")
    date = date or grab("Date") or grab("Sent")

    # No headers at all -> whole thing is the body
    if not any([subject, sender, to, date]):
        body = raw

    name, addr = parseaddr(sender) if sender else ("", "")

    return {
        "subject": (subject or "(no subject)").strip(),
        "from_name": name.strip(),
        "from_email": (addr or sender or "(unknown)").strip(),
        "to": (to or "(unknown)").strip(),
        "date": (date or "(unknown)").strip(),
        "body": body.strip(),
    }


def to_indexable_text(parsed: dict) -> str:
    """
    Render parsed fields into one text block for embedding/indexing, with the
    structured fields written explicitly so the model can answer about sender,
    subject, date, etc. (not just body content).
    """
    return (
        f"EMAIL\n"
        f"Subject: {parsed['subject']}\n"
        f"From: {parsed['from_name']} <{parsed['from_email']}>\n"
        f"To: {parsed['to']}\n"
        f"Date: {parsed['date']}\n\n"
        f"{parsed['body']}"
    )
