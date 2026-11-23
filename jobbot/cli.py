"""
jobbot: pipeline semiautomático de candidaturas.

  scan   -> lee alertas de empleo de Gmail (etiqueta), puntúa, adapta CV y carta, genera PDF
  add    -> lo mismo para una oferta suelta (URL, archivo de texto o texto pegado)
  review -> te enseña cada borrador y TÚ decides si se envía (nunca envía solo)
  list   -> muestra pendientes y registro

Nada se envía sin tu aprobación explícita en `review`.
"""
import argparse
import sys
from pathlib import Path

from jobbot.config import LOG_FILE, OFFERS_HTML, PENDING_FILE
from jobbot.infra.gmail import scan_gmail
from jobbot.infra.storage import load_json
from jobbot.infra.web import fetch_page
from jobbot.services.pipeline import process_text
from jobbot.services.review import review


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sc = sub.add_parser("scan")
    sc.add_argument("--todos", action="store_true", help="procesa también los correos ya leídos de la etiqueta")
    a = sub.add_parser("add")
    a.add_argument("fuente", help="URL, ruta a un .txt, o el texto de la oferta entre comillas")
    sub.add_parser("review")
    sub.add_parser("list")
    args = ap.parse_args()

    if args.cmd == "scan":
        scan_gmail(process_text, args.todos)
    elif args.cmd == "add":
        f = args.fuente
        if f.startswith("http"):
            text = fetch_page(f) or sys.exit("No pude leer esa web (suelen bloquearlo). Pega el texto de la oferta en un .txt.")
            text = f"URL: {f}\n\n{text}"
        elif Path(f).exists():
            text = Path(f).read_text(encoding="utf-8")
        else:
            text = f
        process_text(text, "add")
    elif args.cmd == "review":
        review()
    elif args.cmd == "list":
        for p in load_json(PENDING_FILE, []):
            print(f'{p["id"]}  {p["puntuacion"]:>3}  {p["puesto"]} @ {p["empresa"]}')
        print(f'\nRegistro: {LOG_FILE}\nOfertas con enlace y puntuación: {OFFERS_HTML}')
