# Fishing Exam Alert

A simple project to notify users about upcoming exam for the Bavarian Fishing Exams.

## Setup

1. Create a GMX account
2. Create a spreadsheet with the following headers:

- `Zeitstempel` -> Values of the form: `DD.MM.YYYY HH:MM:SS`
- `E-Mail-Adresse`
- `An- oder Abmeldung?` -> Valid values: `Anmeldung / Aktualisierung`, `Abmeldung`
- `Nur bestimmte Regierungsbezirke?(Standard: Alle)`
- `Prüfungszeitraum ab? (Standard: Heute)` -> Values of the form: `DD.MM.YYYY HH:MM:SS`
- `Wie oft soll ich dich benachrichtigen, wenn Termine frei sind? (Standard: 1 Stunde)`-> only integer values

## Usage

1. Expose the following env variables:
   - `GSHEET_SPREADSHEET_ID`: The ID of the Google Sheet (can be extracted from the spreadsheet’s url), e.g. `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`
   - `NOTIFY_MAIL_FROM`: The mail address for the GMX account, e.g. test@gmx.de
   - `NOTIFY_MAIL_PASSWORD`: The password for the GMX account
2. Run the script with `python fishing_exam_alert/main.py`

Note: You can check that all your credentials are working by running the script with `GSHEET_SPREADSHEET_ID=<your-gsheet-spreadsheet-id> NOTIFY_MAIL_FROM=<your-email-address> NOTIFY_MAIL_PASSWORD=<your-email-password> python fishing_exam_alert/check.py`.

## How it works

1. In each run it gets all entries from a Google Spreadsheet and checks if the record is valid for notifications.

2. If there are any valid records, it scraps and parses the fishing [exam website](https://fischerpruefung-online.bayern.de/fprApp/verwaltung/Pruefungssuche).

3. Iterate over each valid record and apply the filters. If there are any matched exams, it sends a notification to the user.

## FAQ

#### I get an `smtplib.SMTPAuthenticationError` when trying to send the email!

Activate `POP3 & IMAP` in GMX. Instructions are [here](https://hilfe.gmx.net/pop-imap/einschalten.html).
