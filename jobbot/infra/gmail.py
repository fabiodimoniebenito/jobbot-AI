import email
import imaplib
import os
import smtplib
import sys
from email.header import decode_header
from email.message import EmailMessage
from pathlib import Path

from jobbot.domain.cv import CV
from jobbot.domain.links import extract_job_links
from jobbot.domain.text import html_to_text


def decode(s):
    parts = decode_header(s or "")
    return "".join(p.decode(c or "utf-8", "ignore") if isinstance(p, bytes) else p for p, c in parts)


def scan_gmail(procesar, todos: bool = False):
    """`procesar(texto, fuente, links)` se llama por correo; solo se marca leído si no falla."""
    user, pw = os.environ["GMAIL_USER"], os.environ["GMAIL_APP_PASSWORD"]
    label = os.getenv("ALERT_LABEL", "ofertas")
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(user, pw)
    typ, _ = imap.select(f'"{label}"')
    if typ != "OK":
        sys.exit(f'No existe la etiqueta de Gmail "{label}". Créala y haz que tus alertas entren en ella.')
    _, data = imap.search(None, "ALL" if todos else "UNSEEN")
    ids = data[0].split()
    print(f"{len(ids)} correo(s) {'en' if todos else 'sin leer en'} '{label}'")
    for num in ids:
        _, md = imap.fetch(num, "(BODY.PEEK[])")  # PEEK: no lo marca como leído hasta que salga bien
        msg = email.message_from_bytes(md[0][1])
        body = ""
        links: list[dict] = []
        for part in msg.walk():
            ct = part.get_content_type()
            if ct in ("text/plain", "text/html") and not part.get_filename():
                raw = part.get_payload(decode=True) or b""
                txt = raw.decode(part.get_content_charset() or "utf-8", "ignore")
                if ct == "text/html":
                    links += extract_job_links(txt)
                    txt = html_to_text(txt)
                if ct == "text/html" or not body:
                    body = txt
        try:
            procesar(f"Asunto: {decode(msg['Subject'])}\n\n{body}", decode(msg["Subject"])[:50], links)
            imap.store(num, "+FLAGS", "\\Seen")
        except Exception as ex:  # un correo malo no debe parar el resto
            print(f"  ! error procesando un correo: {ex}")
    imap.logout()


def send_mail(p: dict):
    user, pw = os.environ["GMAIL_USER"], os.environ["GMAIL_APP_PASSWORD"]
    en = p.get("idioma") == "en"
    subject = (f'Application – {p["puesto"]} – ' if en else f'Candidatura {p["puesto"]} – ') + CV["datos"]["nombre"]
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = user, p["email_contacto"], subject
    msg.set_content(p["carta"] + f'\n\n{CV["datos"]["nombre"]}\n{CV["datos"]["email"]}\n{CV["datos"]["github"]}')
    msg.add_attachment(Path(p["pdf"]).read_bytes(), maintype="application", subtype="pdf",
                       filename="CV_Fabio_Dimonie.pdf")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw)
        s.send_message(msg)
