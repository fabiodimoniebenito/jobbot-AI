import re


def html_to_text(html: str) -> str:
    html = re.sub(r'(?i)href="https://www\.linkedin\.com/comm/jobs/view/(\d+)/[^"]*"',
                  r'href="https://www.linkedin.com/jobs/view/\1/"', html)  # sin tracking: menos ruido
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    html = re.sub(r'(?is)<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"\2 (\1)", html)
    html = re.sub(r"(?s)<br\s*/?>|</p>|</div>|</tr>|</li>", "\n", html)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "x").lower()).strip("-")[:40] or "x"
