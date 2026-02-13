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
    
    # Configurable email content
    email_subject = os.getenv("EMAIL_SUBJECT", "Nudge: {count} new update(s)")
    email_intro = os.getenv("EMAIL_INTRO", "New updates were posted:")
    view_link_text = os.getenv("VIEW_LINK_TEXT", "View all updates:")
    view_link_url = os.getenv("VIEW_LINK_URL", os.getenv("TARGET_URL"))

    msg = EmailMessage()
    msg["Subject"] = email_subject.format(count=len(new_events))
    msg["From"] = from_email
    msg["To"] = notify_email

    body_lines = [
        email_intro + "\n",
    ]
    for event in new_events:
        body_lines.append(f"- {event}")

    body_lines.append(f"\n{view_link_text}")
    body_lines.append(view_link_url)

    msg.set_content("\n".join(body_lines))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)