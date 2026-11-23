"""CV base (cv_base.json) y reglas anti-invención sobre las competencias."""
import json

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
