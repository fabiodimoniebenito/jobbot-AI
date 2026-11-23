"""Revisión humana: nada se envía sin que lo confirmes aquí."""
import os
import sys
from pathlib import Path

from jobbot.config import PENDING_FILE
from jobbot.infra.gmail import send_mail
from jobbot.infra.storage import load_json, log, save_json


def review():
    pending = load_json(PENDING_FILE, [])
    if not pending:
        print("No hay borradores pendientes.")
        return
    rest = []
    for p in pending:
        # si retocaste carta.txt a mano, esa es la versión que cuenta
        carta_file = Path(p["pdf"]).parent / "carta.txt"
        if carta_file.exists():
            p["carta"] = carta_file.read_text(encoding="utf-8").strip()
        print("\n" + "=" * 70)
        print(f'{p["puesto"]} @ {p["empresa"]}   |   encaje: {p["puntuacion"]}/100')
        print(f'Motivo: {p["motivo"]}')
        print(f'Enlace: {p["url"] or "-"}   |   Contacto: {p["email_contacto"] or "(sin email)"}')
        if p["huecos"]:
            print("Huecos:", "; ".join(p["huecos"]))
        if p["avisos"]:
            print("AVISOS:", "; ".join(p["avisos"]))
        print(f'\n{p["carta"]}\n\nPDF: {p["pdf"]}\nCarta editable: {carta_file}')
        while True:
            c = input("\n[e] editar carta  [s] enviar  [n] descartar  [m] la envié a mano  [Enter] dejar para luego > ").strip().lower()
            if c == "e":
                if sys.platform == "win32":
                    os.startfile(carta_file)
                input("Edita y guarda carta.txt, luego pulsa Enter para recargarla...")
                p["carta"] = carta_file.read_text(encoding="utf-8").strip()
                print(f'\n{p["carta"]}')
            elif c == "s":
                if not p["email_contacto"]:
                    print("Esta oferta no tiene email: aplícala tú con el enlace y el PDF, luego pulsa [m].")
                    continue
                if input(f'Confirmar envío a {p["email_contacto"]} (escribe "si"): ').strip().lower() == "si":
                    send_mail(p)
                    log("enviada", p)
                    print("Enviada.")
                    break
            elif c == "n":
                log("descartada por mí", p)
                break
            elif c == "m":
                log("enviada a mano", p)
                break
            elif c == "":
                rest.append(p)
                break
    save_json(PENDING_FILE, rest)
