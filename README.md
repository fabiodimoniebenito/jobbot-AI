# jobbot: candidaturas semiautomáticas

Lee alertas de empleo de Gmail, puntúa cada oferta, descarta las que no encajan por nivel, prepara un CV (PDF) y
una carta adaptados **sin inventar nada**, y te deja revisarlo todo antes de enviar.
**Nunca envía nada sin que pulses `s` y escribas "si" en `review`.**

```
Gmail (etiqueta "ofertas")
   │  scan
   ▼
Haiku extrae y puntúa ──► filtro duro en Python (senior/lead, 3+ años) ──► puntuación ≥ MIN_SCORE
                                                                              │
                                    ofertas.html (todas, con enlace) ◄────────┤
                                                                              ▼
                                           Sonnet adapta perfil + carta ──► salidas/<fecha>_<empresa>_<puesto>/
                                                                              │   CV_Fabio_Dimonie.pdf
                                                                              │   carta.txt (editable)
                                                                              ▼
                                                              review: editar / enviar / descartar
```

## Instalación (Windows)
1. Python 3.10 o superior. En Windows se usa el lanzador `py` (o `python` si está en el PATH).
2. `py -m pip install -r requirements.txt`
3. Copia `.env.example` a `.env` y rellénalo:
   - `ANTHROPIC_API_KEY`: clave de console.anthropic.com.
   - `GMAIL_USER` y `GMAIL_APP_PASSWORD`: activa la verificación en 2 pasos de Google y crea una "contraseña de
     aplicación" (myaccount.google.com/apppasswords). IMAP debe estar activado en Gmail.
   - `ALERT_LABEL` (por defecto `ofertas`), `MIN_SCORE` (puntuación mínima), `CLAUDE_MODEL` y `SCORE_MODEL`.
4. En Gmail crea la etiqueta `ofertas` y un filtro que etiquete ahí las alertas (LinkedIn, InfoJobs, Indeed…):
   Filtrar mensajes como estos → aplicar etiqueta `ofertas`.
5. Copia `cv_base.example.json` a `cv_base.json` y rellénalo con tus datos reales: es la única fuente de datos del
   CV. `cv_base.json` está en `.gitignore` y no debe subirse.

## Uso

| Comando | Qué hace |
|---|---|
| `py jobbot.py scan` | Procesa los correos **sin leer** de la etiqueta y prepara borradores. |
| `py jobbot.py scan --todos` | Procesa también los ya leídos. Las ofertas ya vistas se saltan. |
| `py jobbot.py add "<url \| .txt \| texto>"` | Procesa una oferta suelta. Con el texto completo la carta sale mejor. |
| `py jobbot.py review` | Revisa borradores: `[e]` editar carta, `[s]` enviar, `[n]` descartar, `[m]` enviada a mano, Enter para luego. |
| `py jobbot.py list` | Pendientes y ruta de `ofertas.html`. |

`scan` marca un correo como leído **solo si se procesó bien**; si falla, se reintenta en el siguiente `scan`.

## Cómo decide

1. **Extracción y puntuación** (`SCORE_MODEL`, por defecto Haiku, barato). Devuelve por oferta: empresa, puesto,
   ubicación, enlace, `seniority`, `anios_requeridos`, puntuación 0-100 y motivo. Pesos: nivel 45 %, stack 25 %,
   ubicación/remoto 15 %, idioma 15 %.
2. **Filtro duro en Python** (`hard_reject` en `jobbot.py`): se descarta si `seniority` es senior/lead, si el
   título contiene senior/lead/principal/staff, o si `anios_requeridos` > `MAX_YEARS` (2, es decir 3+ años).
   1-2 años no descarta.
3. **Stack flexible**: una tecnología distinta pero afín solo penaliza un poco. Solo un stack totalmente ajeno
   (SAP, iOS nativo…) puntúa bajo. Se aceptan ofertas de la UE y remotas.
4. **Umbral**: puntuación < `MIN_SCORE` → descartada (pero queda registrada con su enlace y motivo).
5. **Adaptación** (`CLAUDE_MODEL`, por defecto Sonnet): reescribe el perfil, elige hasta 8 competencias del CV y
   redacta la carta (130-170 palabras, trato neutro en español: "la empresa/el equipo", sin "ustedes/vosotros").

### Sin mentir
- El modelo solo puede usar hechos de `cv_base.json`. Lo que falta va a `huecos`, nunca a la carta.
- `valid_skills()` rechaza cualquier competencia destacada que no exista literalmente en el CV.
- `competencias_adyacentes` en `cv_base.json`: tecnologías afines que **sí** conoces a nivel básico. Pon el nivel
  (`"básico"`, `"en aprendizaje"`) solo en las que sean ciertas; las que estén en `"VERIFICAR"` se ignoran por
  completo. Salen en el PDF como "Conocimientos básicos / en aprendizaje", nunca como experiencia.
- Los logros con `COMPLETAR` o `VERIFICAR` se omiten del CV.

### Enlaces de LinkedIn
Python extrae los enlaces de oferta del HTML del correo (`extract_job_links`) y los empareja con cada oferta por
parecido de título (`resolve_url`), en vez de fiarse del enlace que devuelve el modelo. Las ofertas ya vistas se
reconocen por su número de oferta de LinkedIn.

## Dónde queda cada cosa

| Archivo | Contenido |
|---|---|
| `ofertas.html` / `ofertas.json` | **Todas** las ofertas vistas: puntuación, estado, enlace, motivo. Incluye descartadas. Se regenera sola. |
| `salidas/<fecha>_<empresa>_<puesto>/` | `CV_Fabio_Dimonie.pdf` y `carta.txt`. Retoca `carta.txt`: `review` lee siempre ese archivo. |
| `pendientes.json` | Borradores esperando `review`. |
| `vistas.json` | Huellas de ofertas ya procesadas (evita repetirlas). |
| `registro.csv` | Historial: fecha, empresa, puesto, puntuación, enlace, estado. |
| `cv_base.json` | Perfil y CV maestro. |

Todos los archivos generados están en `.gitignore`.

## Límites conocidos
- LinkedIn bloquea la lectura de sus páginas y sus alertas llegan truncadas: muchas ofertas se puntúan solo con el
  título. Para las que te interesen, copia la descripción completa en un `.txt` y usa `add`.
- Solo se envía por email si la oferta trae email de contacto; con LinkedIn casi nunca. Entonces aplicas tú con el
  enlace y el PDF, y pulsas `[m]`.
- No ejecutes dos comandos a la vez (p. ej. `scan` y `review`): escriben los mismos JSON y se pisan.
- Revisa SIEMPRE la carta antes de enviar.
- Automatizar el envío en LinkedIn o InfoJobs va contra sus normas; por eso no se hace.

La lista de fallos conocidos y propuestas está en [`FALLOS_Y_MEJORAS.md`](FALLOS_Y_MEJORAS.md).

## Licencia
MIT. Ver [`LICENSE`](LICENSE). Los datos personales (`cv_base.json`, `.env`, `salidas/`, `ofertas.*`…) no forman parte
del repositorio y están en `.gitignore`.

## Automatizar el `scan`
Programador de tareas de Windows: tarea diaria que ejecute `py jobbot.py scan` en esta carpeta. Luego solo haces
`review` cuando quieras.

## Formato del CV (plantilla)
El PDF se genera desde `plantilla/cv.html.j2` + `plantilla/cv.css` (Jinja2 + Playwright/Chromium), copiando el formato de
`CV_Fabio_Dimonie_Junior_Backend.pdf`. El modelo solo aporta el perfil (≤ 650 caracteres; si se pasa, se usa
`perfil_base`) y qué competencias van primero. Secciones, orden y estilo se cambian en la plantilla. Primera vez:
`py -m pip install -r requirements.txt` y `py -m playwright install chromium`.

## Ollama (modelo local)
`ollama pull qwen2.5:14b` y `ollama pull qwen2.5:7b`; en `.env`: `LLM_PROVIDER=ollama` (y, si quieres otros modelos,
`SCORE_MODEL`/`CLAUDE_MODEL` con su nombre en Ollama). `OLLAMA_URL` y `OLLAMA_NUM_CTX` son opcionales.
