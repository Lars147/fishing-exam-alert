import smtplib
from email.message import EmailMessage

import pandas as pd
from mailersend import emails
from sqlmodel import Session

from fishing_exam_alert import db, models
from fishing_exam_alert.settings import setting


def notify(email_to: str, exams: pd.DataFrame):
    """Notify the email address with information"""

    # construct the message body
    email_to_username = email_to.split("@")[0]  # removes for example @gmail.de
    pre_message_plain = f"""
    Hi {email_to_username},\n
    es gibt {len(exams)} Prüfungen, die deinen Filterkriterien entsprechen:\n\n
    """
    post_message_plain = f"""\n
    Du kannst dich hier für die Fischereiprüfung anmelden: {setting.EXAM_SCRAP_URL}.
    \n\n
    Du bekommst diese Mail, weil du dich für den Fischereiprüfungs Alarm angemeldet hast.\n
    Wenn du keine Benachrichtigungen mehr erhalten möchtest 
    oder du fälschlicherweise diese Mail erhalten hast, 
    kannst du dich hier abmelden: {setting.UNSUBSCRIBE_URL}.
    """
    plain_message = pre_message_plain + exams.to_string() + post_message_plain

    pre_message_html = f"""
    Hi {email_to_username},<br/>
    es gibt {len(exams)} Prüfungen, die deinen Filterkriterien entsprechen:<br/><br/>
    """
    post_message_html = f"""<br/>
    Du kannst dich hier für die Fischereiprüfung anmelden: <a href="{setting.EXAM_SCRAP_URL}">{setting.EXAM_SCRAP_URL}</a>.
    <br/><br/>
    Du bekommst diese Mail, weil du dich für den Fischereiprüfungs Alarm angemeldet hast.
    <br/>
    Wenn du keine Benachrichtigungen mehr erhalten möchtest 
    oder du fälschlicherweise diese Mail erhalten hast, 
    kannst du dich <a href="{setting.UNSUBSCRIBE_URL}">hier</a> abmelden.
    """
    html_message = pre_message_html + exams.to_html() + post_message_html

    send_mail(
        email_to, f"Fischereiprüfungen - Update - Es gibt {len(exams)} freie Termine!", plain_message, html_message
    )


def send_unsubscribe_mail(email_to: str):
    email_to_username = email_to.split("@")[0]  # removes for example @gmail.de
    message = f"""
    Hi {email_to_username},\n
    du wurdest erfolgreich abgemeldet! Du erhälst zukünftig keine Benachrichtigungen mehr.\n    
    \n\n
    Wenn du fälschlicherweise abgemeldet wurdest oder dich wieder anmelden möchtest, 
    kannst du dich hier wieder anmelden: {setting.SUBSCRIBE_URL}.
    """
    html_message = f"""
    Hi {email_to_username},<br/>
    du wurdest erfolgreich abgemeldet! Du erhälst zukünftig keine Benachrichtigungen mehr.<br/>    
    <br/><br/>
    Wenn du fälschlicherweise abgemeldet wurdest oder dich wieder anmelden möchtest, 
    kannst du dich <a href="{setting.SUBSCRIBE_URL}">hier</a> wieder anmelden.
    """
    send_mail(email_to, "Abmeldung - Fischereiprüfungs Alarm!", message, html_message)


def send_confirmation_mail(email_to: str, filters: dict):
    """
    Send a confirmation mail to the user.

    Sends a mail with the filters that were used to get the exams, e.g.
    ```
    {
        "Teilnehmer": "Frei",
        "Regierungsbezirk": ["Oberbayern"]
    }
    ```
    """

    filters_text_plain = "\n".join(f"\t- {key}: {value}" for key, value in filters.items())
    email_to_username = email_to.split("@")[0]  # removes for example @gmail.de
    message = f"""
    Hi {email_to_username},\n
    du erhälst diese Mail, weil du dich für den Fischereiprüfungs Alarm angemeldet hast.\n
    Ab sofort wirst du über alle Termine informiert, wenn die folgenden Filter zutreffen:\n
    
    {filters_text_plain}
    
    \n\n
    Wenn du keine Benachrichtigungen mehr erhalten möchtest 
    oder du fälschlicherweise diese Mail erhalten hast, 
    kannst du dich hier abmelden: {setting.UNSUBSCRIBE_URL}.
    """

    filters_text_html = "\n".join([f"<li>{key}: {value}</li>" for key, value in filters.items()])
    html_message = f"""
    Hi {email_to_username},<br/>
    du erhälst diese Mail, weil du dich für den Fischereiprüfungs Alarm angemeldet hast.<br/>
    Ab sofort wirst du über alle Termine informiert, wenn die folgenden Filter zutreffen:<br/>
    
    <ul>
    {filters_text_html}
    </ul>
    
    <br/><br/>
    Wenn du keine Benachrichtigungen mehr erhalten möchtest 
    oder du fälschlicherweise diese Mail erhalten hast, 
    kannst du dich <a href="{setting.UNSUBSCRIBE_URL}">hier</a> abmelden.
    """
    send_mail(email_to, "Anmeldung - Fischereiprüfungs Alarm!", message, html_message)


def send_mail(email_to: str, subject: str, message: str, html_message: str = "", send_duplicate: bool = False):
    """Send a mail. Optional with HTML content."""

    if not send_duplicate:
        with Session(db.engine) as session:
            latest_mail = models.EmailLog.get_latest_mail_by_user_mail(db=session, email=email_to)

        if latest_mail and latest_mail.content == message:
            print(f"Skip sending mail to {email_to} because it was already sent.")
            return  # don't send duplicate mail content

    if setting.MAIL_SERVICE == "mailersend":
        send_mail_with_mailersend(email_to, subject, message, html_message)
    else:
        send_mail_with_gmx(email_to, subject, message, html_message)

    with Session(db.engine) as session:
        user = models.User.get_by_mail(session, email=email_to)
        if not user:
            raise Exception(f"User with mail {email_to} not found")
        user.create_email_log(session, category=models.EmailLogCategory.notification, content=message)
        session.commit()


def send_mail_with_mailersend(email_to: str, subject: str, message: str, html_message: str = ""):
    """Send a mail with mailersend. Optional with HTML content."""
    mailer = emails.NewEmail(setting.NOTIFY_MAIL_PASSWORD)

    mail_body = {}
    mail_from = {
        # "name": "Your Name",
        "email": setting.NOTIFY_MAIL_FROM,
    }
    recipients = [
        {
            # "name": "Your Client",
            "email": email_to,
        }
    ]

    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(subject, mail_body)
    mailer.set_plaintext_content(message, mail_body)
    if html_message:
        mailer.set_html_content(html_message, mail_body)

    if setting.NOTIFY_MAIL_REPLY_TO:
        reply_to = [
            {
                # "name": "Name",
                "email": setting.NOTIFY_MAIL_REPLY_TO,
            }
        ]
        mailer.set_reply_to(reply_to, mail_body)

    # using print() will also return status code and data
    mailer.send(mail_body)


def send_mail_with_gmx(email_to: str, subject: str, message: str, html_message: str = ""):
    """Send a mail with GMX. Optional with HTML content."""
    msg = EmailMessage()
    msg.set_content(message)
    if html_message:
        msg.add_alternative(html_message, subtype="html")
    msg["Subject"] = subject
    msg["From"] = setting.NOTIFY_MAIL_FROM
    msg["To"] = email_to
    # TODO: add reply_to for gmx

    with smtplib.SMTP("mail.gmx.net", port=587) as s:
        s.starttls()
        s.login(setting.NOTIFY_MAIL_FROM, setting.NOTIFY_MAIL_PASSWORD)
        s.send_message(msg)
