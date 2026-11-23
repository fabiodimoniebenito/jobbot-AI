from jobbot.infra import storage


def _setup(monkeypatch, tmp_path):
    out = tmp_path / "salidas"
    monkeypatch.setattr(storage, "OUT_DIR", out)
    monkeypatch.setattr(storage, "OFFERS_FILE", tmp_path / "ofertas.json")
    monkeypatch.setattr(storage, "OFFERS_HTML", tmp_path / "ofertas.html")
    return out


def _oferta(**kw):
    return {"empresa": "Acme", "puesto": "Backend", "url": "https://x.test/1", "puntuacion": 80, **kw}


def test_html_incluye_cv_y_carta(monkeypatch, tmp_path):
    out = _setup(monkeypatch, tmp_path)
    d = out / "20260101_acme_backend"
    d.mkdir(parents=True)
    (d / "CV_Fabio_Dimonie.pdf").write_bytes(b"%PDF-1.4")
    (d / "carta.txt").write_text("Hola <script>alert(1)</script>", encoding="utf-8")
    storage.record_offer("pendiente", _oferta(pdf=str(d / "CV_Fabio_Dimonie.pdf")))
    html = (tmp_path / "ofertas.html").read_text(encoding="utf-8")
    assert "salidas/20260101_acme_backend/CV_Fabio_Dimonie.pdf" in html
    assert "salidas/20260101_acme_backend/carta.txt" in html
    assert "&lt;script&gt;" in html and "<script>" not in html


def test_sin_borrador_no_hay_enlaces(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path)
    storage.record_offer("descartada", _oferta())
    html = (tmp_path / "ofertas.html").read_text(encoding="utf-8")
    assert "CV (PDF)" not in html and "Ver carta" not in html


def test_carpeta_se_conserva_al_cambiar_estado(monkeypatch, tmp_path):
    out = _setup(monkeypatch, tmp_path)
    storage.record_offer("pendiente", _oferta(pdf=str(out / "20260101_acme_backend" / "CV.pdf")))
    storage.record_offer("enviada", _oferta())
    assert storage.load_json(tmp_path / "ofertas.json", [])[0]["carpeta"] == "20260101_acme_backend"
