"""Pipeline: puntuar -> filtro duro -> adaptar CV y carta -> pendientes.json."""
import datetime as dt
import hashlib
import json

from jobbot.config import MIN_SCORE, OFFERS_FILE, OUT_DIR, PENDING_FILE, SCORE_MODEL, SEEN_FILE
from jobbot.domain.cv import compose_perfil, cv_for_tailor, valid_adjacent, valid_skills
from jobbot.domain.filters import hard_reject
from jobbot.domain.links import job_id, resolve_url
from jobbot.domain.text import slug
from jobbot.infra.pdf import render_cv
from jobbot.infra.storage import load_json, log, save_json
from jobbot.infra.web import fetch_page
from jobbot.llm.client import claude_json
from jobbot.llm.prompts import SYSTEM_SCORE, SYSTEM_TAILOR


def process_text(text: str, fuente: str, links: list[dict] | None = None):
    text = text[:12000]
    ofertas = claude_json(SYSTEM_SCORE, f"<oferta_no_confiable>\n{text}\n</oferta_no_confiable>",
                          max_tokens=8000, model=SCORE_MODEL).get("ofertas", [])
    print(f"[{fuente}] {len(ofertas)} oferta(s) detectada(s)")
    seen = set(load_json(SEEN_FILE, []))
    pending = load_json(PENDING_FILE, [])
    seen_ids = {job_id(x["url"]) for x in load_json(OFFERS_FILE, []) if job_id(x["url"])}

    for o in ofertas:
        if links:  # el enlace lo decide Python con los del correo, no el modelo
            o["url"] = resolve_url(o, links)
        jid = job_id(o.get("url"))
        if jid and jid in seen_ids:
            continue
        if jid:
            seen_ids.add(jid)
        key = hashlib.sha1(f'{o.get("empresa")}|{o.get("puesto")}|{o.get("url")}'.lower().encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        score = int(o.get("puntuacion") or 0)
        motivo_rechazo = hard_reject(o)
        if motivo_rechazo:
            print(f"  - {o.get('puesto')} @ {o.get('empresa')}: descartada ({motivo_rechazo})")
            log("descartada", o, motivo_rechazo)
            continue
        if score < MIN_SCORE:
            print(f"  - {o.get('puesto')} @ {o.get('empresa')}: {score} (descartada)")
            log("descartada", o, f"puntuación < {MIN_SCORE}")
            continue

        # el email de contacto solo vale si aparece literalmente en el texto de origen
        if o.get("email_contacto") and o["email_contacto"] not in text:
            o["email_contacto"] = None

        desc = (fetch_page(o["url"]) if o.get("url") else "") or o.get("descripcion_resumen") or text[:6000]
        t = claude_json(
            SYSTEM_TAILOR,
            f"CV_JSON:\n{json.dumps(cv_for_tailor(), ensure_ascii=False)}\n\n"
            f"Empresa: {o.get('empresa')}\nPuesto: {o.get('puesto')}\n"
            f"<oferta_no_confiable>\n{desc}\n</oferta_no_confiable>",
            max_tokens=4000,
        )
        folder = OUT_DIR / f"{dt.date.today():%Y%m%d}_{slug(o.get('empresa'))}_{slug(o.get('puesto'))}"
        folder.mkdir(parents=True, exist_ok=True)
        pdf = folder / "CV_Fabio_Dimonie.pdf"
        render_cv(pdf, compose_perfil(t.get("perfil_cierre")), valid_skills(t.get("competencias_destacadas", [])),
                  valid_adjacent(t.get("competencias_adyacentes_destacadas", [])))
        (folder / "carta.txt").write_text(t["carta"], encoding="utf-8")

        pending.append({
            "id": key[:8], "empresa": o.get("empresa"), "puesto": o.get("puesto"), "url": o.get("url"),
            "email_contacto": o.get("email_contacto"), "puntuacion": score, "motivo": o.get("motivo"),
            "idioma": t.get("idioma", "es"), "carta": t["carta"], "pdf": str(pdf),
            "huecos": t.get("huecos", []), "avisos": t.get("avisos", []),
        })
        log("pendiente", o)
        print(f"  + {o.get('puesto')} @ {o.get('empresa')}: {score} -> borrador en {folder.name}")

    save_json(SEEN_FILE, sorted(seen))
    save_json(PENDING_FILE, pending)
