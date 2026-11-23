import re
import unicodedata
from pathlib import Path

import pytest

from jobbot.config import MASTER_CV
from jobbot.domain.cv import CV, MAX_CIERRE, compose_perfil
from jobbot.domain.master import merge_master, parse_master_text

TEXTO = """\
                                    NOMBRE EJEMPLO APELLIDO
                       Madrid  ·  600 000 000  ·  ejemplo@example.com
                    linkedin.com/in/ejemplo  ·  github.com/ejemplo
PERFIL
Desarrollador backend junior con Java. Me centro en APIs REST. Busco un equipo
donde aprender.

EDUCACIÓN
CFGS en Desarrollo (DAM)                                              Sept 2024 – Jun 2027
Instituto Ejemplo
EXPERIENCIA LABORAL
Desarrollador — Prácticas                                             Oct 2026 – Actualidad
Empresa Uno
 •  Desarrollo de software en equipo.
Socorrista                                                       Ago 2025 · Jun – Jul 2026
Empresa Dos
COMPETENCIAS TÉCNICAS
 Backend:    Java, Spring Boot (JWT), arquitectura
 hexagonal, Maven.
 Bases de datos:     PostgreSQL, Flyway (migraciones, versionadas).
 Testing:  JUnit.
 DevOps y herramientas:        Git, Docker.
 Frontend:    Angular, HTML.
IDIOMAS
 •  Español:   Nativo.
 •  Inglés:  B2.
INFORMACIÓN ADICIONAL
 •  Habilidades:    comunicación, equipo.
 •  Carnet B y vehículo propio.
"""


def test_parse_master_text():
    m = parse_master_text(TEXTO)
    assert m["telefono"] == "600 000 000" and m["github"] == "github.com/ejemplo"
    assert m["perfil_cierre"] == "Busco un equipo donde aprender."
    assert m["perfil_cuerpo"].endswith("APIs REST.")
    assert m["competencias"]["backend"] == ["Java", "Spring Boot (JWT)", "arquitectura hexagonal", "Maven"]
    assert m["competencias"]["bases_de_datos"][1] == "Flyway (migraciones, versionadas)"
    assert m["competencias"]["herramientas"] == ["Git", "Docker"]
    assert [i["nivel"] for i in m["idiomas"]] == ["Nativo", "B2"]
    assert m["experiencia"][0]["logros"] == ["Desarrollo de software en equipo."]
    assert m["experiencia"][1]["periodo"] == "Ago 2025 · Jun – Jul 2026"


def test_parse_master_text_exige_secciones():
    with pytest.raises(ValueError):
        parse_master_text(TEXTO.replace("IDIOMAS", "OTRA COSA"))


def test_merge_conserva_lo_que_el_pdf_no_tiene_y_mueve_logros():
    cv = {"datos": {"nombre": "Nombre Ejemplo Apellido"}, "competencias_adyacentes": [{"nombre": "Go", "nivel": "básico"}],
          "proyectos": {"texto": "p"}, "competencias": {"backend": ["x"]},
          "experiencia": [{"puesto": "Dev", "empresa": "Empresa Uno", "inicio": "a", "fin": "b", "relevancia": "alta",
                           "logros": ["Logro antiguo concreto."]}]}
    new, diff = merge_master(cv, parse_master_text(TEXTO))
    assert new["competencias_adyacentes"] == cv["competencias_adyacentes"] and new["proyectos"] == cv["proyectos"]
    e = new["experiencia"][0]
    assert e["logros"] == ["Desarrollo de software en equipo."] and e["logros_extra"] == ["Logro antiguo concreto."]
    assert e["relevancia"] == "alta" and e["inicio"] == "Oct 2026"
    assert new["experiencia"][1]["periodo"] == "Ago 2025 · Jun – Jul 2026"
    assert new["datos"]["nombre"] == "Nombre Ejemplo Apellido" and diff
    assert merge_master(new, parse_master_text(TEXTO))[1] == ""  # idempotente


def test_compose_perfil_acepta_cierre_valido_y_rechaza_el_resto():
    ok = compose_perfil("Busco un puesto backend donde crecer con Java.")
    assert ok.startswith(CV["perfil_cuerpo"]) and ok.endswith("donde crecer con Java.")
    base = f'{CV["perfil_cuerpo"]} {CV["perfil_cierre"]}'
    for malo in ["", None, "x" * (MAX_CIERRE + 1) + ".", "Sin punto final", "Una. Dos frases.",
                 "Busco un equipo con Kubernetes y Kafka.", "Quiero entrar en Acme."]:
        assert compose_perfil(malo) == base


REAL_CV = Path(__file__).resolve().parent.parent / "cv_base.json"


@pytest.mark.skipif(not (Path(MASTER_CV).exists() and REAL_CV.exists()), reason="sin PDF maestro o cv_base.json real")
def test_cv_generado_coincide_con_el_pdf_maestro(tmp_path, monkeypatch):
    """Con perfil y orden base, el CV generado (datos reales) tiene el mismo texto que el PDF maestro."""
    import json

    import jobbot.infra.pdf as pdf
    from pypdf import PdfReader

    real = json.loads(REAL_CV.read_text(encoding="utf-8"))
    monkeypatch.setattr(pdf, "CV", real)
    out = tmp_path / "cv.pdf"
    pdf.render_cv(out, real["perfil_base"], [], [])
    norm = lambda p: re.sub(r"[\s•]+", "", unicodedata.normalize("NFKC", " ".join(pg.extract_text() for pg in PdfReader(str(p)).pages)))
    assert norm(out) == norm(MASTER_CV)
