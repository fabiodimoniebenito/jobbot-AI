"""CV en PDF a partir de plantilla/cv.html.j2 (formato fijo)."""
from pathlib import Path

from jobbot.config import TEMPLATE_DIR
from jobbot.domain.cv import CV


MAX_PERFIL = 650  # caracteres; el CV modelo ocupa una página y el perfil mide ~560
SECCIONES_COMP = [("backend", "Backend"), ("bases_de_datos", "Bases de datos"), ("testing", "Testing"),
                  ("herramientas", "DevOps y herramientas"), ("frontend", "Frontend")]


def render_cv(path: Path, perfil: str, destacadas: list[str], adyacentes: list[str] | None = None):
    """PDF a partir de plantilla/cv.html.j2 (formato fijo); el modelo solo aporta perfil y orden de competencias."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from playwright.sync_api import sync_playwright

    perfil = " ".join((perfil or "").split())
    if not perfil or len(perfil) > MAX_PERFIL:
        perfil = CV["perfil_base"]
    dest = {x.lower() for x in destacadas}
    comp = [(nombre, sorted(CV["competencias"][k], key=lambda x: 0 if x.lower() in dest else 1))  # sort estable
            for k, nombre in SECCIONES_COMP if CV["competencias"].get(k)]
    ok = lambda t: "COMPLETAR" not in t and "VERIFICAR" not in t
    exp = [{**e, "logros": [lg for lg in e.get("logros", []) if ok(lg)]} for e in CV["experiencia"]]

    tdir = TEMPLATE_DIR
    env = Environment(loader=FileSystemLoader(tdir), autoescape=select_autoescape(["j2"], default_for_string=True))
    html = env.get_template("cv.html.j2").render(
        css=(tdir / "cv.css").read_text(encoding="utf-8"), d=CV["datos"], perfil=perfil, educacion=CV["educacion"],
        experiencia=exp, competencias=comp, adyacentes=adyacentes or [], idiomas=CV["idiomas"],
        habilidades=CV["habilidades_blandas"])
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        page.pdf(path=str(path), prefer_css_page_size=True, print_background=True)
        browser.close()
