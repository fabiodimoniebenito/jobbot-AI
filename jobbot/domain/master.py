"""CV maestro: lectura del texto del PDF y fusión con cv_base.json. El PDF manda; lo que no está en él se conserva."""
import copy
import difflib
import json
import re

SECCIONES = ["PERFIL", "EDUCACIÓN", "EXPERIENCIA LABORAL", "COMPETENCIAS TÉCNICAS", "IDIOMAS", "INFORMACIÓN ADICIONAL"]
CLAVES_COMP = {"backend": "backend", "bases de datos": "bases_de_datos", "testing": "testing",
               "devops y herramientas": "herramientas", "frontend": "frontend"}
_PERIODO = re.compile(r"^(\S.*?)\s{2,}(\S.*)$")
_FECHA = r"(?:[A-Za-zñ]+\.? \d{4}|\d{4})"
_RANGO = re.compile(rf"^({_FECHA}) – ({_FECHA}|Actualidad)$")


def _split_commas(s: str) -> list[str]:
    """Separa por comas fuera de paréntesis."""
    out, depth, cur = [], 0, ""
    for ch in s:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return [x for x in out if x]


def _items(lines: list[str]) -> list[dict]:
    """Bloques 'Título   periodo' + línea de centro/empresa + viñetas."""
    items: list[dict] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        m = _PERIODO.match(s)
        if m and not ln.lstrip().startswith("•"):
            items.append({"titulo": m.group(1), "periodo": m.group(2), "centro": None, "logros": []})
        elif not items:
            raise ValueError(f"línea inesperada en el PDF maestro: {s!r}")
        elif s.startswith("•"):
            items[-1]["logros"].append(s.lstrip("• ").strip())
        elif items[-1]["centro"] is None:
            items[-1]["centro"] = s
        elif items[-1]["logros"]:  # continuación de una viñeta
            items[-1]["logros"][-1] += " " + s
        else:
            raise ValueError(f"línea inesperada en el PDF maestro: {s!r}")
    return items


def _rango(periodo: str) -> tuple[str, str] | None:
    m = _RANGO.match(periodo)
    return (m.group(1), m.group(2)) if m else None


def parse_master_text(text: str) -> dict:
    """Texto del PDF maestro (pypdf, extraction_mode='layout') -> datos estructurados."""
    lines = text.split("\n")
    idx = {}
    for i, ln in enumerate(lines):
        if ln.strip() in SECCIONES:
            idx[ln.strip()] = i
    falta = [s for s in SECCIONES if s not in idx]
    if falta:
        raise ValueError(f"al PDF maestro le faltan secciones: {', '.join(falta)}")
    orden = sorted(idx.values())
    sec = {n: lines[i + 1:next((j for j in orden if j > i), len(lines))] for n, i in idx.items()}
    head = [l.strip() for l in lines[:idx["PERFIL"]] if l.strip()]
    if len(head) < 3:
        raise ValueError("cabecera del PDF maestro incompleta")
    ubic = [x.strip() for x in head[1].split("·")]
    enlaces = [x.strip() for x in " ".join(head[2:]).split("·")]
    if len(ubic) < 3 or len(enlaces) < 2:
        raise ValueError("no pude leer los datos de contacto del PDF maestro")

    perfil = " ".join(" ".join(sec["PERFIL"]).split())
    frases = re.split(r"(?<=\.)\s+(?=[A-ZÁÉÍÓÚÑ])", perfil)

    educ = [{"titulo": i["titulo"], "centro": i["centro"], "periodo": i["periodo"]} for i in _items(sec["EDUCACIÓN"])]
    exp = [{"puesto": i["titulo"], "empresa": i["centro"], "periodo": i["periodo"], "logros": i["logros"]}
           for i in _items(sec["EXPERIENCIA LABORAL"])]

    comp: dict[str, list[str]] = {}
    cur = None
    for ln in sec["COMPETENCIAS TÉCNICAS"]:
        if not ln.strip():
            continue
        m = re.match(r"^\s*([^:]+):\s{2,}(.*)$", ln)
        if m and m.group(1).strip().lower() in CLAVES_COMP:
            cur = CLAVES_COMP[m.group(1).strip().lower()]
            comp[cur] = m.group(2).strip()
        elif cur:
            comp[cur] += " " + ln.strip()
        else:
            raise ValueError(f"competencias: línea inesperada {ln.strip()!r}")
    comp = {k: _split_commas(v.rstrip(".")) for k, v in comp.items()}
    if set(comp) != set(CLAVES_COMP.values()):
        raise ValueError(f"competencias del PDF maestro incompletas: {sorted(comp)}")

    idiomas = []
    for ln in sec["IDIOMAS"]:
        m = re.match(r"^\s*•\s*([^:]+):\s+(.*?)\.?\s*$", ln)
        if m:
            idiomas.append({"idioma": m.group(1).strip(), "nivel": m.group(2).strip()})
    habilidades, carnet = [], None
    for ln in sec["INFORMACIÓN ADICIONAL"]:
        s = ln.strip().lstrip("• ").strip()
        if s.lower().startswith("habilidades:"):
            habilidades = _split_commas(s.split(":", 1)[1].strip().rstrip("."))
        elif s:
            carnet = s.rstrip(".")
    if not (idiomas and habilidades and carnet):
        raise ValueError("idiomas o información adicional del PDF maestro incompletos")

    return {
        "nombre": head[0], "ubicacion": ubic[0], "telefono": ubic[1], "email": ubic[2],
        "linkedin": enlaces[0], "github": enlaces[1],
        "perfil_cuerpo": " ".join(frases[:-1]), "perfil_cierre": frases[-1],
        "educacion": educ, "experiencia": exp, "competencias": comp, "idiomas": idiomas,
        "habilidades_blandas": habilidades, "carnet": carnet,
    }


def _fechas(periodo: str, prev: dict | None) -> dict:
    r = _rango(periodo)
    if r:
        return {"inicio": r[0], "fin": r[1]}
    # periodo libre (p. ej. "Ago 2025 · Jun – Jul 2026"): se muestra tal cual
    return {"inicio": (prev or {}).get("inicio", periodo), "fin": (prev or {}).get("fin", ""), "periodo": periodo}


def merge_master(cv: dict, m: dict) -> tuple[dict, str]:
    """Aplica el maestro sobre cv_base. Devuelve (cv_nuevo, diff legible). Lo que el PDF no tiene se conserva;
    los logros que ya no están en el PDF pasan a `logros_extra` (solo para la carta, no se imprimen)."""
    new = copy.deepcopy(cv)
    d = new.setdefault("datos", {})
    if m["nombre"].lower() != d.get("nombre", "").lower():
        d["nombre"] = m["nombre"].title()
    for k in ("ubicacion", "telefono", "email", "linkedin", "github", "carnet"):
        d[k] = m[k]
    new["perfil_cuerpo"], new["perfil_cierre"] = m["perfil_cuerpo"], m["perfil_cierre"]
    new["perfil_base"] = f'{m["perfil_cuerpo"]} {m["perfil_cierre"]}'.strip()

    new["educacion"] = []
    for e in m["educacion"]:
        f = _fechas(e["periodo"], None)
        new["educacion"].append({"titulo": e["titulo"], "centro": e["centro"], "inicio": f["inicio"], "fin": f["fin"]})

    prev = {x["empresa"].casefold(): x for x in cv.get("experiencia", [])}
    new["experiencia"] = []
    for e in m["experiencia"]:
        old = prev.get(e["empresa"].casefold(), {})
        item = {k: v for k, v in old.items() if k not in ("periodo", "logros", "logros_extra")}
        item.update({"puesto": e["puesto"], "empresa": e["empresa"]})
        item.update(_fechas(e["periodo"], old))
        item["logros"] = e["logros"]
        extra = list(old.get("logros_extra", []))
        extra += [l for l in old.get("logros", []) if l not in e["logros"] and l not in extra]
        if extra:
            item["logros_extra"] = extra
        new["experiencia"].append(item)

    new["competencias"] = {**cv.get("competencias", {}), **m["competencias"]}
    new["idiomas"] = m["idiomas"]
    new["habilidades_blandas"] = m["habilidades_blandas"]

    dump = lambda c: json.dumps(c, ensure_ascii=False, indent=2).splitlines()
    diff = "\n".join(difflib.unified_diff(dump(cv), dump(new), "cv_base.json", "cv_base.json (maestro)", lineterm="", n=1))
    return new, diff
