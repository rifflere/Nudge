'''
emailer.py
- Accept list of new events
- Format readable message
- Send via SMTP
'''

import os
import smtplib
from email.message import EmailMessage


def send_email(new_events):
    notify_email = os.getenv("NOTIFY_EMAIL")
    from_email = os.getenv("FROM_EMAIL")
    password = os.getenv("EMAIL_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT"))

    msg = EmailMessage()
    msg["Subject"] = f"IKEA Renton: {len(new_events)} new event(s) posted"
    msg["From"] = from_email
    msg["To"] = notify_email

    body_lines = [
        "New IKEA Renton events were posted:\n",
    ]
    for event in new_events:
        body_lines.append(f"- {event}")

    body_lines.append("\nView all events:")
    body_lines.append("https://www.ikea.com/us/en/stores/events/ikea-renton-wa/")

    msg.set_content("\n".join(body_lines))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
