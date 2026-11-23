"""Enlaces de ofertas de LinkedIn."""
import re

_LI_JOB_RE = re.compile(r"linkedin\.com/(?:comm/)?jobs/view/(\d+)")


def job_id(url: str | None) -> str | None:
    m = _LI_JOB_RE.search(url or "")
    return m.group(1) if m else None


def extract_job_links(html: str) -> list[dict]:
    """Enlaces de ofertas de LinkedIn de un correo, en orden: {id, title, url} (sin tracking)."""
    from html import unescape
    found: dict[str, dict] = {}
    for href, inner in re.findall(r'(?is)<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html):
        jid = job_id(href)
        if not jid:
            continue
        title = unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", inner))).strip()
        e = found.setdefault(jid, {"id": jid, "title": "", "url": f"https://www.linkedin.com/jobs/view/{jid}/"})
        e["title"] = e["title"] or title
    return list(found.values())


def resolve_url(o: dict, links: list[dict]) -> str:
    """Enlace real de una oferta: el que casa con su título en el correo; si no, solo uno que exista en él."""
    import difflib
    norm = lambda s: re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()
    puesto = norm(o.get("puesto"))
    best, score = None, 0.0
    for l in links:
        t = norm(l["title"])
        if not t or not puesto:
            continue
        r = difflib.SequenceMatcher(None, puesto, t).ratio()
        if t.startswith(puesto) or puesto.startswith(t):
            r = max(r, 0.9)
        if r > score:
            best, score = l, r
    if best and score >= 0.6:
        return best["url"]
    jid = job_id(o.get("url"))
    return next((l["url"] for l in links if l["id"] == jid), "") if jid else ""
