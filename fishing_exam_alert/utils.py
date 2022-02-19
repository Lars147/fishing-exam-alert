import smtplib
from email.message import EmailMessage

import pandas as pd

from fishing_exam_alert.settings import setting


def notify(email: str, exams: list):
    """Notify the email address with information"""
    # init df for exam data
    df = pd.DataFrame.from_records(exams)

    send_mail(email, f"Es gibt {len(exams)} freie Termine!", df.to_string(), df.to_html())


def send_mail(email_to: str, subject: str, message: str, html_message: str = ""):
    """Send a mail. Optional with HTML content."""
    msg = EmailMessage()
    msg.set_content(message)
    if html_message:
        msg.add_alternative(html_message, subtype="html")
    msg["Subject"] = subject
    msg["From"] = setting.NOTIFY_MAIL_FROM
    msg["To"] = email_to

    s = smtplib.SMTP("mail.gmx.net", port=587)
    s.starttls()
    s.login(setting.NOTIFY_MAIL_FROM, setting.NOTIFY_MAIL_PASSWORD)
    s.send_message(msg)
    s.quit()
