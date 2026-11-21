# jobbot

Bot semiautomático de candidaturas: alertas de Gmail → puntuación con LLM → filtro duro en Python → CV y carta
adaptados → revisión humana → envío. Un solo script (`jobbot.py`), datos en `cv_base.json`. Sin tests. No es un repo git.
Detalles de uso y funcionamiento: `README.md`. Fallos conocidos y propuestas: `FALLOS_Y_MEJORAS.md`.

## Comandos (Windows; usar `py`, `python` puede no estar en el PATH)
- `py -m pip install -r requirements.txt`
- `py jobbot.py scan [--todos]`, `add <url|.txt|texto>`, `review`, `list`
- Salida generada: `ofertas.html/json`, `pendientes.json`, `vistas.json`, `registro.csv`, `salidas/`

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

## Arquitectura (`jobbot.py`)
- **Prompts**: `SYSTEM_SCORE` (extracción y puntuación; el perfil se construye desde `cv_base.json` con
  `main_skills()` y `adjacent_skills()`) y `SYSTEM_TAILOR` (perfil, competencias y carta).
- **Modelos**: `SCORE_MODEL` (Haiku, por defecto) para puntuar; `CLAUDE_MODEL` (Sonnet) para carta y CV. Se cambian
  por variable de entorno. `claude_json()` extrae el JSON con una regex y lanza error si `stop_reason == max_tokens`.
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
- Comentarios breves, solo cuando explican un porqué. Mantener el estilo del archivo; sigue siendo un solo módulo.
- **No ejecutar dos procesos que escriban `pendientes.json`/`ofertas.json` a la vez** (un `scan` largo pisó una limpieza
  manual). No hay bloqueo de archivos. Esperar a que `scan` termine antes de editar los JSON.
- `perfil_adaptado` y las competencias elegidas por el modelo **no se guardan**: si se borra una carpeta de `salidas/`
  y se regenera el PDF, se pierde la adaptación (queda el perfil base).
- Las alertas de LinkedIn llegan truncadas; muchas ofertas se puntúan solo con el título. Las puntuaciones de esas
  ofertas son poco fiables.
- PowerShell y comillas: para scripts de Python con f-strings o comillas anidadas, escribirlos en un archivo y ejecutarlo
  en vez de usar `py -c "..."`.
- Para probar sin gastar API: `hard_reject`, `resolve_url`, `extract_job_links` y `render_cv` se pueden llamar sin red.
  Hay que importar `jobbot` desde su carpeta (carga `.env` al importar).
