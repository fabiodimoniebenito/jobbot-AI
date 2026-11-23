"""Persistencia: JSON, registro CSV y ofertas.html."""
import csv
import datetime as dt
import json
from pathlib import Path
from xml.sax.saxutils import escape

from jobbot.config import LOG_FILE, OFFERS_FILE, OFFERS_HTML


def load_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def log(estado: str, o: dict, detalle: str = ""):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    new = not LOG_FILE.exists()
    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["fecha", "empresa", "puesto", "puntuacion", "url", "estado"])
        w.writerow([dt.date.today().isoformat(), o.get("empresa"), o.get("puesto"),
                    o.get("puntuacion"), o.get("url"), estado])
    record_offer(estado, o, detalle)


def record_offer(estado: str, o: dict, detalle: str = ""):
    """Guarda TODAS las ofertas vistas (también las descartadas) y regenera ofertas.html."""
    key = f'{o.get("empresa")}|{o.get("puesto")}|{o.get("url")}'.lower()
    offers = {x["key"]: x for x in load_json(OFFERS_FILE, [])}
    prev = offers.get(key, {})
    offers[key] = {
        "key": key, "fecha": prev.get("fecha") or dt.date.today().isoformat(),
        "empresa": o.get("empresa") or "", "puesto": o.get("puesto") or "",
        "ubicacion": o.get("ubicacion") or "", "url": o.get("url") or "",
        "puntuacion": int(o.get("puntuacion") or 0), "motivo": o.get("motivo") or prev.get("motivo", ""),
        "estado": estado, "detalle": detalle or prev.get("detalle", ""),
    }
    data = sorted(offers.values(), key=lambda x: (x["fecha"], x["puntuacion"]), reverse=True)
    save_json(OFFERS_FILE, data)
    render_offers_html(data)


def render_offers_html(data: list[dict]):
    from urllib.parse import quote_plus
    rows = []
    for x in data:
        url = x["url"] if x["url"].startswith(("http://", "https://")) else ""
        if url:
            link = f'<a href="{escape(url, {chr(34): "&quot;"})}" target="_blank" rel="noopener noreferrer">Abrir oferta</a>'
        else:
            q = quote_plus(f'{x["puesto"]} {x["empresa"]} oferta empleo')
            link = f'<a href="https://www.google.com/search?q={q}" target="_blank" rel="noopener noreferrer">Buscar oferta</a> <small>(sin enlace)</small>'
        descartada = x["estado"].startswith("descartada")
        extra = f' <small>({escape(x["detalle"])})</small>' if x["detalle"] else ""
        rows.append(
            f'<tr class="{"off" if descartada else ""}"><td>{escape(x["fecha"])}</td>'
            f'<td class="sc">{x["puntuacion"]}</td><td><b>{escape(x["puesto"])}</b><br>{escape(x["empresa"])}'
            f'<br><small>{escape(x["ubicacion"])}</small></td><td>{escape(x["estado"])}{extra}</td>'
            f'<td>{link}</td><td><small>{escape(x["motivo"])}</small></td></tr>')
    OFFERS_HTML.write_text(
        '<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Ofertas</title><style>'
        'body{font:14px system-ui,sans-serif;margin:20px;color:#222}table{border-collapse:collapse;width:100%}'
        'th,td{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left;vertical-align:top}'
        'th{background:#1f3a5f;color:#fff}tr.off{color:#888}td.sc{font-weight:bold;font-size:16px}'
        '</style></head><body><h1>Ofertas vistas</h1><table><tr><th>Fecha</th><th>Punt.</th><th>Oferta</th>'
        '<th>Estado</th><th>Enlace</th><th>Motivo de la puntuación</th></tr>' + "".join(rows) +
        '</table></body></html>', encoding="utf-8")
