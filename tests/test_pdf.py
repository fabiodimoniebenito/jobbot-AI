from jobbot.domain.cv import CV
from jobbot.infra.pdf import MAX_PERFIL, render_cv


def test_render_cv_genera_pdf(tmp_path):
    out = tmp_path / "cv.pdf"
    render_cv(out, "x" * (MAX_PERFIL + 1), ["Docker"], [])  # perfil demasiado largo -> perfil_base
    assert out.read_bytes().startswith(b"%PDF")
