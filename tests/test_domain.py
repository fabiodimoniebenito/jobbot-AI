from jobbot.domain.cv import CV, adjacent_skills, cv_for_tailor, main_skills, valid_adjacent, valid_skills
from jobbot.domain.filters import hard_reject
from jobbot.domain.links import extract_job_links, job_id, resolve_url
from jobbot.domain.text import html_to_text, slug


def test_hard_reject_senior_por_nivel_y_por_titulo():
    assert hard_reject({"seniority": "senior"}) == "senior/lead"
    assert hard_reject({"seniority": "junior", "puesto": "Tech Lead Java"}) == "senior/lead"


def test_hard_reject_anios():
    assert hard_reject({"seniority": "junior", "anios_requeridos": 3}) == "3+ años de experiencia"
    assert hard_reject({"seniority": "junior", "anios_requeridos": 2}) is None
    assert hard_reject({"seniority": "junior", "anios_requeridos": "x"}) is None
    assert hard_reject({"puesto": "Junior Java Developer"}) is None


def test_valid_skills_solo_las_del_cv():
    assert valid_skills(["java", "COBOL", "Docker"]) == ["Java", "Docker"]
    assert len(valid_skills(main_skills() * 2)) <= 8


def test_adyacentes_sin_verificar_se_ignoran():
    assert adjacent_skills() == {}
    assert valid_adjacent(["Python"]) == []
    assert cv_for_tailor()["competencias_adyacentes"] == []
    assert all("VERIFICAR" not in str(v) for v in cv_for_tailor()["competencias_adyacentes"])
    assert CV["competencias_adyacentes"]  # el original no se muta


HTML = ('<a href="https://www.linkedin.com/comm/jobs/view/123456/?trk=x">Java Developer</a>'
        '<a href="https://www.linkedin.com/jobs/view/999/">QA Engineer</a><a href="https://otra.com">x</a>')


def test_extract_job_links_y_job_id():
    links = extract_job_links(HTML)
    assert [l["id"] for l in links] == ["123456", "999"]
    assert links[0]["url"] == "https://www.linkedin.com/jobs/view/123456/"
    assert job_id("https://x.com") is None


def test_resolve_url_por_parecido_de_titulo():
    links = extract_job_links(HTML)
    assert resolve_url({"puesto": "Java Developer"}, links).endswith("/123456/")
    assert resolve_url({"puesto": "Cocinero", "url": ""}, links) == ""


def test_html_to_text_y_slug():
    assert "Hola" in html_to_text("<script>x</script><p>Hola</p>")
    assert slug("Desarrollador/a Java!") == "desarrollador-a-java"
    assert slug(None) == "x"
