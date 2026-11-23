import requests

from jobbot.domain.text import html_to_text


def fetch_page(url: str) -> str:
    """Intenta leer la página de la oferta. LinkedIn y otros suelen bloquear: entonces devuelve ''."""
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            t = html_to_text(r.text)
            if len(t) > 500:
                return t[:8000]
    except requests.RequestException:
        pass
    return ""
