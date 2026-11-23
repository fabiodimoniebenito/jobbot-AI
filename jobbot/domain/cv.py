"""CV base (cv_base.json) y reglas anti-invención sobre las competencias."""
import json
import re

from jobbot.config import CV_FILE

CV = json.loads(CV_FILE.read_text(encoding="utf-8"))

# -- competencias: principales (reales) y adyacentes (básicas / en aprendizaje, ya verificadas por el usuario)
_PLACEHOLDER = ("COMPLETAR", "VERIFICAR")


def adjacent_skills() -> dict[str, tuple[str, str]]:
    """{nombre_en_minusculas: (nombre, nivel)}; ignora entradas sin verificar."""
    out = {}
    for s in CV.get("competencias_adyacentes", []):
        if any(p in f'{s.get("nombre", "")} {s.get("nivel", "")}' for p in _PLACEHOLDER):
            continue
        out[s["nombre"].lower()] = (s["nombre"], s["nivel"])
    return out


def main_skills() -> list[str]:
    return [s for items in CV["competencias"].values() for s in items]


def valid_skills(destacadas: list[str]) -> list[str]:
    """Anti-invención: solo se aceptan competencias que existan en el CV."""
    allowed = {s.lower(): s for items in CV["competencias"].values() for s in items}
    return [allowed[x.lower()] for x in destacadas if x.lower() in allowed][:8]


def cv_for_tailor() -> dict:
    """CV para el LLM: solo adyacentes verificadas por el usuario."""
    cv = dict(CV)
    cv["competencias_adyacentes"] = [{"nombre": n, "nivel": lvl} for n, lvl in adjacent_skills().values()]
    return cv


def valid_adjacent(destacadas: list[str]) -> list[str]:
    """Solo adyacentes verificadas; devuelve 'Nombre (nivel)'."""
    adj = adjacent_skills()
    return [f"{adj[x.lower()][0]} ({adj[x.lower()][1]})" for x in destacadas if x.lower() in adj][:4]


MAX_CIERRE = 220  # caracteres; la frase final del maestro mide ~190


def _vocabulario() -> set[str]:
    """Palabras que ya aparecen en el CV: base para detectar tecnologías inventadas en el cierre del perfil."""
    textos = [CV.get("perfil_base", ""), *main_skills()]
    for e in CV.get("experiencia", []):
        textos += [e.get("puesto", ""), e.get("empresa", ""), *e.get("logros", [])]
    textos += [e.get("titulo", "") + " " + e.get("centro", "") for e in CV.get("educacion", [])]
    return {w.lower() for t in textos for w in re.findall(r"[\wÁÉÍÓÚÑáéíóúñ.+#]+", t)}


def compose_perfil(cierre: str | None) -> str:
    """Perfil = cuerpo del CV maestro + cierre. El cierre propuesto por el modelo solo vale si es una frase corta
    y no nombra nada (tecnología, empresa) que no esté ya en el CV; si no, se usa el cierre del maestro."""
    cuerpo = CV.get("perfil_cuerpo")
    base = CV.get("perfil_cierre", "")
    if not cuerpo:
        return CV["perfil_base"]
    c = " ".join((cierre or "").split())
    palabras = re.findall(r"[\wÁÉÍÓÚÑáéíóúñ.+#]+", c)
    vocab = _vocabulario()
    inventa = any(w[:1].isupper() and i > 0 and w.lower().strip(".") not in vocab and w.lower() not in vocab
                  for i, w in enumerate(palabras))
    if not c or len(c) > MAX_CIERRE or c.count(". ") or not c.endswith(".") or inventa:
        c = base
    return f"{cuerpo} {c}".strip()
