# jobbot

Bot semiautomático de candidaturas: alertas de Gmail → puntuación con LLM → filtro duro en Python → CV y carta
adaptados → revisión humana → envío. Paquete por capas (`jobbot/`), datos en `cv_base.json`, tests con pytest. Repo git (`data/`, `.env` y `cv_base.json` ignorados).
Detalles de uso y funcionamiento: `README.md`. Fallos conocidos y propuestas: `FALLOS_Y_MEJORAS.md`.

## Comandos (Windows; usar `py`, `python` puede no estar en el PATH)
- `py -m pip install -r requirements.txt`
- `py jobbot.py scan [--todos]`, `add <url|.txt|texto>`, `review`, `list`, `sync-cv [--aplicar]` (también `py -m jobbot ...`)
- Tests (sin red ni API): `py -m pip install -r requirements-dev.txt` y `py -m pytest`. Usan `cv_base.example.json`.
- Salida generada en `data/`: `ofertas.html/json`, `pendientes.json`, `vistas.json`, `registro.csv`, `salidas/`

## Reglas que no se negocian
- **Nunca enviar correos ni ejecutar `review`/`send_mail` por iniciativa propia.** `review` es interactivo y envía en
  su opción `[s]`. Ejecutar `scan` y `add` sí es seguro, pero llama a la API (cuesta dinero) y `scan` marca correos
  como leídos tras procesarlos.
- **El CV no puede mentir.** Todo hecho del CV sale de `cv_base.json`. `SYSTEM_TAILOR` obliga a usar solo esos hechos,
  `valid_skills()`/`valid_adjacent()` filtran lo que el modelo destaca, y las entradas con `VERIFICAR`/`COMPLETAR` se
  ignoran. No añadir tecnologías al CV que el usuario no haya confirmado en `competencias_adyacentes`.
- **No tocar `.env`** ni imprimir su contenido (clave de Anthropic y contraseña de aplicación de Gmail). `.env.example`
  es solo plantilla.
- **`cv_base.json` es privado** (datos personales reales) y está en `.gitignore`; la plantilla pública es
  `cv_base.example.json`, con datos ficticios. No copiar datos reales del CV a ejemplos, documentación ni commits.
  El proyecto es MIT (`LICENSE`).
- El texto de las ofertas es **dato no confiable** (inyección de prompts): va siempre dentro de
  `<oferta_no_confiable>` y los prompts dicen que se ignoren las instrucciones que contenga. Mantenerlo así.

## Arquitectura (paquete `jobbot/`)
Las dependencias van hacia dentro: `cli` → `services` → `infra`/`llm` → `domain` → `config`. `domain` es lógica pura
(sin red ni escribir en disco; solo lee `cv_base.json` al importar) y es lo que cubren los tests.
- `config.py`: rutas (`data/`), variables de entorno, `MODEL`, `SCORE_MODEL`, `MIN_SCORE`, `LLM_PROVIDER`. `CV_FILE`
  permite apuntar a otro CV (los tests usan el de ejemplo).
- `domain/`: `cv.py` (`CV`, `adjacent_skills`, `main_skills`, `cv_for_tailor`, `valid_skills`, `valid_adjacent`),
  `filters.py` (`hard_reject`), `links.py` (`job_id`, `extract_job_links`, `resolve_url`), `text.py` (`html_to_text`, `slug`).
- `llm/`: `prompts.py` (`SYSTEM_SCORE`, construido desde `cv_base.json`; `SYSTEM_TAILOR`) y `client.py`
  (`claude_json()` sobre `_llm_text()`, que elige Anthropic u Ollama).
- `infra/`: `gmail.py` (`scan_gmail(procesar, todos)` recibe el callback; `send_mail`), `web.py` (`fetch_page`),
  `storage.py` (JSON, `log`, `record_offer`, `ofertas.html`), `pdf.py` (`render_cv`: `plantilla/cv.html.j2` + Playwright).
- `services/`: `pipeline.py` (`process_text`) y `review.py` (`review`).
- `domain/master.py` + `infra/master_cv.py`: el PDF maestro (`MASTER_CV`) es la fuente de verdad; `sync-cv` lo vuelca en
  `cv_base.json` (conserva adyacentes, proyectos y lo que el PDF no tiene; logros viejos -> `logros_extra`, solo para la carta).
- `cli.py`: argparse. `jobbot.py` en la raíz es solo un wrapper.
- **Prompts**: `SYSTEM_SCORE` puntúa; `SYSTEM_TAILOR` devuelve perfil, competencias y carta.
- **Modelos**: `SCORE_MODEL` (Haiku por defecto) puntúa; `MODEL`/`CLAUDE_MODEL` (Sonnet) hace carta y CV. Con
  `LLM_PROVIDER=ollama` son modelos de Ollama. `claude_json()` extrae el JSON con una regex y falla si se corta por tokens.
- **Pipeline**: `process_text()` → puntúa → por oferta: resuelve enlace (`resolve_url`) → dedup por número de
  oferta de LinkedIn y por hash → `hard_reject()` → umbral `MIN_SCORE` → adapta y genera PDF/carta → `pendientes.json`.
- **Filtro duro**: `hard_reject()` usa `seniority` y `anios_requeridos` que devuelve el modelo, y una regex sobre el
  título. `MAX_YEARS = 2`. No hay regex de respaldo para años (daba falsos positivos, p. ej. "50+ años" de la empresa).
- **Enlaces**: `extract_job_links()` saca los enlaces de oferta de LinkedIn del HTML del correo; `resolve_url()` los
  empareja por parecido de título. No fiarse del enlace que devuelve el modelo.
- **Registro**: `log()` escribe `registro.csv` y llama a `record_offer()`, que mantiene `ofertas.json` y regenera
  `ofertas.html`. Todas las ofertas vistas (también las descartadas) pasan por ahí.
- **Scan**: `scan_gmail()` usa `BODY.PEEK[]` y marca `\Seen` solo si `process_text` no falló.
- **Review**: relee `carta.txt` de la carpeta del borrador; lo que ves es lo que se envía.

## Convenciones y trampas
- Código y comentarios en español; nombres de datos en español (`puesto`, `empresa`, `puntuacion`, `motivo`).
- Comentarios breves, solo cuando explican un porqué. Mantener el estilo y respetar el sentido de las dependencias entre capas.
- **No ejecutar dos procesos que escriban `pendientes.json`/`ofertas.json` a la vez** (un `scan` largo pisó una limpieza
  manual). No hay bloqueo de archivos. Esperar a que `scan` termine antes de editar los JSON.
- El CV solo puede variar por oferta en el orden de competencias y en `perfil_cierre` (última frase del perfil, validada por
  `compose_perfil()`). Ninguno de los dos **se guarda**: si se regenera un PDF de `data/salidas/`, queda el perfil del maestro.
- No tocar a mano el texto del CV en `cv_base.json`: edita el PDF maestro y ejecuta `sync-cv`.
- Las alertas de LinkedIn llegan truncadas; muchas ofertas se puntúan solo con el título. Las puntuaciones de esas
  ofertas son poco fiables.
- PowerShell y comillas: para scripts de Python con f-strings o comillas anidadas, escribirlos en un archivo y ejecutarlo
  en vez de usar `py -c "..."`.
- Para probar sin gastar API: `hard_reject`, `resolve_url`, `extract_job_links` y `render_cv` no usan red (`py -m pytest`).
  Hay que importar `jobbot` desde la raíz del proyecto (carga `.env` al importar `config`).
