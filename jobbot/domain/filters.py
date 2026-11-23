import re

_SENIOR_RE = re.compile(r"\b(senior|sr\.?|lead|principal|staff|team lead|tech lead)\b", re.I)
MAX_YEARS = 2  # 3 o más años pedidos = descarte duro


def hard_reject(o: dict) -> str | None:
    """Exclusiones obvias, independientes del LLM. Devuelve el motivo o None."""
    if str(o.get("seniority", "")).lower() in {"senior", "lead"} or _SENIOR_RE.search(o.get("puesto") or ""):
        return "senior/lead"
    years = o.get("anios_requeridos")
    try:
        years = int(years) if years is not None else None
    except (TypeError, ValueError):
        years = None
    if years is not None and years > MAX_YEARS:
        return f"{years}+ años de experiencia"
    return None
