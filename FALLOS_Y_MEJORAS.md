# Fallos conocidos y propuestas

Estado a 21-nov-2026, tras el primer `scan` completo de la etiqueta `ofertas` (68 correos, ~250 ofertas).
Orden: de mayor a menor impacto.

## 1. Ofertas duplicadas con empresa errónea (alto)
**Qué pasa.** El modelo barato mezcla empresas y enlaces cuando una alerta trae varias ofertas. Resultado: la misma
oferta aparece dos veces con empresas distintas y el mismo enlace. Con borrador generado hay 8 grupos:
Santander/PrimeIT (4492162702), Plexus ×2, GRUPO NS/Hays, TECDATA/Hays (×2), SOLUZIO/Sopra Steria, METRICA/Revolut,
Mirakl ×2. Una de las dos empresas es falsa y **su carta menciona la empresa equivocada**.
**Causa.** Se le pide a Haiku extraer muchas ofertas de un HTML aplanado a texto; pierde la asociación empresa↔enlace.
**Propuesta.** Extraer en Python la "tarjeta" de cada oferta (texto entre un enlace de oferta y el siguiente: título,
empresa, ubicación) y pasarle al modelo una oferta por tarjeta, o validar su empresa contra el texto de la tarjeta.
Para lo ya guardado: conservar el borrador cuya empresa aparece en la tarjeta del enlace y marcar el otro como
duplicado erróneo (y borrar su carta).
**Limpieza hecha (21-nov).** Se quitaron 9 duplicados comparando la empresa con el texto de la tarjeta del correo
(quedan 49 borradores). Pendiente: Mirakl, dos entradas casi iguales. **Sigue sin prevención**: el próximo `scan` puede
volver a generarlos hasta que se implemente la extracción por tarjeta.
**Hecho ya.** `resolve_url()` corrige el enlace por título para ofertas nuevas, pero con títulos idénticos no distingue
empresa. Los datos antiguos no se corrigieron.

## 2. Descripciones truncadas → puntuaciones y cartas poco fiables (alto)
**Qué pasa.** LinkedIn manda el correo con título, empresa y ubicación, sin requisitos. `fetch_page` no puede leer
LinkedIn. Casi todas las cartas se basan solo en el título ("la oferta no incluye requisitos", dicen los avisos) y son
genéricas. Puntuaciones como 85 no significan encaje real.
**Propuesta.**
- Marcar cada oferta con `info: baja|alta` según haya o no requisitos, y mostrarlo en `ofertas.html` y `review`.
- **No generar carta con Sonnet cuando la info es baja**: guardar solo la oferta y generar la carta cuando el usuario
  pegue la descripción con `add` (ahorra dinero y evita cartas vacías).
- Añadir `py jobbot.py add --id <pendiente>` que reutilice el borrador y reciba la descripción pegada.
- Valorar leer InfoJobs/Indeed (más abiertos) o recibir las alertas en otro formato.

## 3. Sin bloqueo de archivos: los procesos se pisan (medio-alto)
**Qué pasa.** `scan` carga `pendientes.json` al empezar cada correo y lo guarda al terminar. Una limpieza manual hecha
mientras corría el `scan` fue deshecha: los borradores borrados volvieron, con la carpeta ya eliminada (rutas rotas).
**Propuesta.** Archivo de bloqueo (`.lock`) al empezar `scan`/`review`/`add` y salir con aviso si ya existe; o mover los
datos a SQLite (`sqlite3` ya viene con Python), que además da consultas y transacciones.

## 4. Fragilidad del JSON del modelo (medio)
**Qué pasa.** `claude_json()` extrae el JSON con la regex `\{.*\}`. Con `max_tokens` bajo se cortaba a medias (el primer
`scan` falló en ~50 de 68 correos); aún quedan fallos puntuales (`Expecting ':' delimiter`). No hay reintentos.
**Propuesta.** Usar salida estructurada / tool use con esquema JSON, reintentar una vez ante error de parseo, y procesar
de una en una las ofertas de correos largos. Subir `max_tokens` según el nº de enlaces del correo.

## 5. El filtro de nivel depende del modelo (medio)
**Qué pasa.**
- `anios_requeridos` lo rellena el modelo; si lo deja vacío, una oferta de 3+ años solo se frena por la puntuación.
  Se quitó la regex de respaldo porque daba falsos positivos ("50+ años" de antigüedad de la empresa).
- La regex del título incluye `staff`, `lead`, `principal`: descartó "STAFF 40H TEMPORAL BAJA" (dependiente) por error.
  Sin importancia aquí, pero fallaría con "Staff" = personal o "Lead generation".
**Propuesta.** Regex de respaldo **acotada**: años solo junto a palabras de requisito ("mínimo", "al menos",
"requerimos", "experiencia de N años"). Cambiar `staff`/`principal` por `staff engineer|principal engineer|tech lead|
team lead`. Registrar `anios_requeridos` en `ofertas.json` para auditar.

## 6. La adaptación del CV no se guarda (medio)
**Qué pasa.** `perfil_cierre` y las competencias destacadas no se persisten. Al regenerar un PDF (se hizo con 4
borradores restaurados) se pierde la adaptación y sale el perfil base.
**Propuesta.** Guardar en `pendientes.json` los campos `perfil_cierre`, `competencias_destacadas` y
`competencias_adyacentes_destacadas`, y un comando `regenerar <id>` que rehaga el PDF sin llamar al modelo.

## 7. Casi ningún borrador se puede enviar por correo (medio)
**Qué pasa.** Las ofertas de LinkedIn no traen email de contacto: solo se puede aplicar a mano con el enlace. El flujo
`review → [s]` casi no se usa.
**Propuesta.** Aceptarlo y optimizar el flujo manual: en `review`, abrir el enlace y la carpeta del PDF, copiar la
carta al portapapeles (`clip` en Windows) y pasar al siguiente. Quitar la opción de envío si no hay email.

## 8. Calibración de la puntuación (medio-bajo)
**Qué pasa.** Haiku concentra casi todo entre 50 y 60; hay 40+ borradores en 50-60 y varios descartados en 45. El
umbral (`MIN_SCORE`, 50 en el `.env` local, 65 en `.env.example`) separa casi al azar.
**Propuesta.** Puntuar por sub-criterios en el JSON (nivel, stack, ubicación, idioma) y calcular la nota en Python con
los pesos; así se puede ajustar sin tocar el prompt. Calibrar con 15-20 ofertas que el usuario puntúe a mano.

## 9. Ubicación sin criterio explícito (medio-bajo)
**Qué pasa.** Se aceptan ofertas de la UE (decisión del usuario), pero el modelo puntúa ubicación a ojo y a veces
la deja vacía. Hay ofertas en Lisboa, París o Países Bajos mezcladas con las de Madrid o remoto.
**Propuesta.** Campo `modalidad` (remoto/híbrido/presencial) y `pais` extraídos, y regla en Python: presencial/híbrido
fuera de Madrid penaliza; remoto España/UE no. Configurable en `.env`.

## 10. Coste sin visibilidad (bajo)
**Qué pasa.** No se registra cuánto gasta cada `scan`. Cada borrador usa Sonnet aunque la oferta sea de baja información.
**Propuesta.** Registrar tokens y coste estimado por ejecución (`usage` de la respuesta) y mostrarlos al final de
`scan`. Considerar Haiku también para la carta si el usuario la retoca siempre.

## 11. Ruido en los avisos (bajo)
**Qué pasa.** El modelo avisa "revisa las fechas de NOWHUB/Burger King" porque cree que son futuras (son correctas).
**Propuesta.** Indicar en el prompt la fecha de hoy (`dt.date.today()`) o filtrar ese tipo de aviso.

## 12. Competencias adyacentes sin usar (bajo)
**Qué pasa.** Todas siguen en `VERIFICAR`, así que la función de destacar tecnologías afines no tiene efecto todavía.
**Propuesta.** El usuario confirma cuáles son ciertas y pone el nivel; probar con una oferta que pida esa tecnología.

## 13. Higiene del proyecto (bajo)
- `salidas/` conserva carpetas de borradores ya borrados o duplicados (hay más carpetas que pendientes). Añadir un
  comando de limpieza que borre las que no estén en `pendientes.json`.
- ~~`.env.example` contiene un correo real~~: resuelto. Además `cv_base.json` (datos reales) pasó a `.gitignore` y hay
  un `cv_base.example.json` ficticio para publicar.
- Las claves van en texto plano en `.env`: usar el Administrador de credenciales de Windows (`keyring`) si el proyecto
  se comparte.
- `requirements.txt` sin versiones fijadas: fijarlas.
- Dependencias de formato: la carta solo sale en español o inglés según la oferta; ofertas en otros idiomas (francés,
  portugués) generan carta en español.

## Orden sugerido
1. Duplicados con empresa errónea (nº 1) y bloqueo de archivos (nº 3): afectan a la corrección de los datos.
2. Info baja → sin carta automática (nº 2) y persistencia de la adaptación (nº 6): ahorran coste y trabajo.
3. JSON estructurado con reintento (nº 4) y filtro de nivel acotado (nº 5): robustez.
4. El resto según el uso real.
