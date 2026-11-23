# Manual de usuario de jobbot

Guía práctica para instalar, configurar y usar jobbot día a día. Para el detalle técnico, ver `README.md`.

## 1. Qué hace (en una frase)
Lee tus alertas de empleo de Gmail, puntúa cada oferta, descarta las que no encajan, prepara un **CV en PDF** y una
**carta** para las buenas, y te las deja revisar. **Nunca envía nada sin que tú lo confirmes** en `review`.

Flujo diario típico:

```
scan  →  (abrir data/ofertas.html y revisar)  →  review  →  enviar / aplicar a mano
```

## 2. Instalación (una sola vez)
Todos los comandos se ejecutan en PowerShell, dentro de la carpeta del proyecto. Se usa `py` (no `python`).

| Paso | Comando / acción | Para qué |
|---|---|---|
| 1 | `py -m pip install -r requirements.txt` | Instala las librerías del programa. |
| 2 | `py -m playwright install chromium` | Descarga el navegador que convierte la plantilla del CV a PDF. |
| 3 | Copiar `.env.example` a `.env` y rellenarlo | Claves y ajustes (ver sección 3). |
| 4 | Copiar `cv_base.example.json` a `cv_base.json` | Datos del CV (se rellena en el paso 5 de la sección 4). |
| 5 | En Gmail, crear la etiqueta `ofertas` y un filtro que etiquete ahí tus alertas | Es de donde lee `scan`. |
| 6 (opcional) | `py -m pip install -r requirements-dev.txt` | Solo si vas a ejecutar los tests. |

## 3. Configuración (`.env`)
No compartas nunca este archivo: contiene tu clave y tu contraseña de Gmail.

| Variable | Qué es |
|---|---|
| `GMAIL_USER` | Tu dirección de Gmail. |
| `GMAIL_APP_PASSWORD` | Contraseña de aplicación de Google (16 letras; requiere verificación en 2 pasos; IMAP activado en Gmail). No es tu contraseña normal. |
| `ALERT_LABEL` | Etiqueta de Gmail con las alertas (por defecto `ofertas`). |
| `MIN_SCORE` | Puntuación mínima (0-100) para preparar borrador. Por defecto 65. |
| `LLM_PROVIDER` | `anthropic` (por defecto, de pago) u `ollama` (local, gratis). |
| `ANTHROPIC_API_KEY` | Clave de Anthropic (solo si usas `anthropic`). |
| `SCORE_MODEL` / `CLAUDE_MODEL` | Modelo que puntúa ofertas / modelo que redacta la carta. Con Ollama son nombres de modelo de Ollama. |
| `OLLAMA_URL`, `OLLAMA_NUM_CTX` | Opcionales: dirección de Ollama (por defecto `http://localhost:11434`) y contexto (8192). |
| `MASTER_CV` | Opcional: ruta del PDF del CV maestro. |

### Usar Ollama en lugar de Anthropic
1. Instala Ollama y descarga un modelo: `ollama pull qwen2.5:7b` (ligero) y, si tu equipo aguanta, `ollama pull qwen2.5:14b`
   (mejor redacción).
2. En `.env`: `LLM_PROVIDER=ollama` y, si quieres, `SCORE_MODEL=qwen2.5:7b` y `CLAUDE_MODEL=qwen2.5:14b`.
3. Para probar solo una vez, sin tocar `.env`:
   ```powershell
   $env:LLM_PROVIDER="ollama"; $env:SCORE_MODEL="qwen2.5:7b"; $env:CLAUDE_MODEL="qwen2.5:7b"; py jobbot.py scan
   ```
   Los modelos pequeños redactan peor y se equivocan más en los años de experiencia: revisa siempre la carta.

## 4. Preparar tu CV (una vez, y cada vez que cambie)
jobbot usa tu **PDF maestro** como fuente de verdad: lo que ves en el PDF es lo que sale en cada CV generado.

1. Mantén el PDF maestro en la raíz del proyecto: `CV_Fabio_Dimonie_Junior_Backend.pdf` (o apunta a otro con `MASTER_CV`).
2. Ejecuta `py jobbot.py sync-cv` para ver qué cambiaría en `cv_base.json` (no escribe nada).
3. Si te cuadra, ejecuta `py jobbot.py sync-cv --aplicar`. Guarda antes una copia en `cv_base.json.bak`.
4. Para cambiar el CV en el futuro: edita el PDF maestro y repite los pasos 2 y 3. **No edites a mano el texto del CV
   en `cv_base.json`**: se sobrescribiría en la siguiente sincronización.
5. **Competencias adyacentes** (tecnologías que conoces a nivel básico, por ejemplo Python): se confirman a mano en
   `cv_base.json`, bloque `competencias_adyacentes`. Cambia `"nivel": "VERIFICAR"` por tu nivel real
   (`"básico"`, `"en aprendizaje"`). Las que sigan en `VERIFICAR` se ignoran. Confirma solo las que sean ciertas.

El PDF maestro debe conservar las secciones `PERFIL`, `EDUCACIÓN`, `EXPERIENCIA LABORAL`, `COMPETENCIAS TÉCNICAS`,
`IDIOMAS` e `INFORMACIÓN ADICIONAL`, y cada línea de competencias su etiqueta (`Backend:`, `Bases de datos:`, `Testing:`,
`DevOps y herramientas:`, `Frontend:`).

**Qué cambia el programa en cada CV:** solo (1) el orden de las competencias dentro de cada línea y (2) la última frase
del perfil. Todo lo demás es idéntico al maestro. Si la frase propuesta no cumple las reglas (larga, con empresa o
tecnologías que no tienes), se usa la del maestro.

## 5. Comandos

| Comando | Qué hace | Cuándo usarlo |
|---|---|---|
| `py jobbot.py scan` | Lee los correos **sin leer** de la etiqueta, puntúa las ofertas y prepara CV y carta de las que pasan el filtro. Marca el correo como leído solo si se procesó bien. | Cada día, o automatizado. |
| `py jobbot.py scan --todos` | Igual, pero incluye correos ya leídos. Las ofertas ya vistas se saltan. | Primera vez, o si quieres reprocesar. |
| `py jobbot.py add "<url>"` | Procesa una oferta desde una web. LinkedIn suele bloquear la lectura. | Ofertas de webs que sí se dejan leer. |
| `py jobbot.py add ruta\oferta.txt` | Procesa una oferta desde un archivo de texto. | Cuando copias la descripción completa (mejor resultado). |
| `py jobbot.py add "texto de la oferta"` | Procesa el texto pegado entre comillas. | Ofertas sueltas rápidas. |
| `py jobbot.py list` | Muestra los borradores pendientes y las rutas de registro y de `ofertas.html`. | Ver qué tienes pendiente. |
| `py jobbot.py review` | **Interactivo.** Te enseña cada borrador y tú decides (ver sección 6). Es el único comando que puede enviar correos. | Cuando quieras aplicar. |
| `py jobbot.py sync-cv` | Muestra qué cambiaría en `cv_base.json` al leer el PDF maestro. No escribe. | Tras editar el PDF maestro. |
| `py jobbot.py sync-cv --aplicar` | Escribe `cv_base.json` desde el PDF maestro (copia antes `cv_base.json.bak`). | Tras revisar el diff. |
| `py jobbot.py --help` | Lista los comandos. | Ayuda. |
| `py -m jobbot <comando>` | Equivale a `py jobbot.py <comando>`. | Alternativa. |
| `py -m pytest` | Ejecuta los tests (sin red ni API; usan datos ficticios). | Tras tocar el código. |

`scan` y `add` llaman al modelo: con Anthropic cuestan dinero, con Ollama no. `scan` además marca correos como leídos.

## 6. Revisar y enviar (`review`)
`review` recorre los borradores uno a uno y muestra puesto, empresa, puntuación, motivo, enlace, contacto, los
**huecos** (lo que la oferta pide y tú no tienes), los **avisos** y la carta. Opciones:

| Tecla | Acción |
|---|---|
| `e` | Edita la carta: abre `carta.txt` en el Bloc de notas; guarda, vuelve y pulsa Enter para recargarla. |
| `s` | Enviar por email (solo si la oferta trae email de contacto). Pide escribir `si` para confirmar. |
| `n` | Descartar el borrador (queda registrado). |
| `m` | Márcalo como "enviada a mano" (cuando aplicas tú desde LinkedIn u otra web). |
| Enter | Dejarlo para más tarde. |

Lo que ves es lo que se envía: `review` siempre relee `carta.txt`. Revisa la carta antes de enviar.

## 7. Dónde queda cada cosa
Todo lo generado está en `data/` (ignorado por git):

| Archivo | Contenido |
|---|---|
| `data/ofertas.html` | **Todas** las ofertas vistas, con puntuación, estado, enlace y motivo. Ábrelo en el navegador. |
| `data/salidas/<fecha>_<empresa>_<puesto>/` | `CV_Fabio_Dimonie.pdf` y `carta.txt` de cada borrador. |
| `data/pendientes.json` | Borradores esperando `review`. |
| `data/vistas.json` | Ofertas ya procesadas (para no repetirlas). |
| `data/registro.csv` | Historial (fecha, empresa, puesto, puntuación, enlace, estado). |
| `data/ofertas.json` | Los mismos datos que `ofertas.html`, en JSON. |

## 8. Cómo decide jobbot
1. El modelo extrae cada oferta y le da una puntuación 0-100 (nivel 45 %, stack 25 %, ubicación 15 %, idioma 15 %).
2. Un filtro en Python descarta las senior/lead y las que piden 3 o más años de experiencia.
3. Si la puntuación es menor que `MIN_SCORE`, se descarta (queda registrada con su motivo).
4. Si pasa, se genera el CV (formato del PDF maestro) y la carta con **solo hechos de tu CV**; lo que no tienes va a
   "huecos" y nunca aparece en la carta.

## 9. Buenas prácticas
- No ejecutes dos comandos a la vez (por ejemplo `scan` y `review`): escriben los mismos archivos y se pisan.
- Las alertas de LinkedIn llegan truncadas: muchas ofertas se puntúan solo con el título. Para las que te interesen,
  copia la descripción completa en un `.txt` y usa `add`.
- Revisa siempre la carta y los avisos antes de enviar, sobre todo con modelos locales.
- Automatizar el `scan`: Programador de tareas de Windows, tarea diaria con `py jobbot.py scan` en la carpeta del proyecto.
  `review` hazlo tú cuando quieras.

## 10. Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| `No existe la etiqueta de Gmail "ofertas"` | Crea la etiqueta en Gmail o cambia `ALERT_LABEL`. |
| Error de login en Gmail | Revisa `GMAIL_APP_PASSWORD` (contraseña de aplicación, no la normal) y que IMAP esté activado. |
| `No pude leer esa web` | La web bloquea la lectura. Pega el texto de la oferta en un `.txt` y usa `add`. |
| Error al conectar con Ollama | Comprueba que Ollama está abierto (`http://localhost:11434`) y que descargaste el modelo con `ollama pull`. |
| `al PDF maestro le faltan secciones` | El PDF no conserva las secciones o el formato esperado (ver sección 4). |
| El PDF no se genera | Ejecuta `py -m playwright install chromium`. |
| Una oferta no sale como esperabas | Mira `data/ofertas.html`: ahí está su puntuación, estado y motivo, incluso si se descartó. |
