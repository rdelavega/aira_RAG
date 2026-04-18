---
name: ingesta
description: Ingesta un PDF al sistema de investigación de AIRA.
user-invocable: true
always-on: true
---

## Regla crítica

Cuando el usuario mande un archivo PDF, NUNCA lo leas directamente.
SIEMPRE ejecuta este pipeline:

## Pasos

1. Encuentra el PDF recién recibido:

```bash
find /root/.openclaw/media/inbound -name "*.pdf" -mmin -10 2>/dev/null | head -3
```

2. Mándalo a procesar y guarda el `job_id` (sin pedirle nada al usuario):

```bash
export PDF="RUTA_DEL_PDF"
export RESP="$(curl -sS -X POST http://fastapi:8000/upload -F "files=@${PDF}")"
export JOB_ID="$(python3 - <<'PY'
import json, os
resp = os.environ.get("RESP", "")
try:
    data = json.loads(resp)
    jobs = data.get("jobs") or []
    print(jobs[0]["job_id"] if jobs else "")
except Exception:
    print("")
PY
)"
```

3. Espera a que termine el job (polling automático, máximo ~30 min):

```bash
python3 - <<'PY'
import json, os, time, urllib.request

job_id = os.environ.get("JOB_ID", "").strip()
if not job_id:
    raise SystemExit("No pude obtener job_id del upload")

deadline = time.time() + 30 * 60
last = None

while time.time() < deadline:
    url = f"http://fastapi:8000/jobs/{job_id}"
    with urllib.request.urlopen(url, timeout=10) as r:
        job = json.loads(r.read().decode("utf-8"))

    status = job.get("status")
    stage = job.get("stage")
    if (status, stage) != last:
        print(f"Estado: {status} · etapa: {stage}")
        last = (status, stage)

    if status in ("done", "error"):
        print(json.dumps(job, ensure_ascii=True))
        break

    time.sleep(3)
else:
    raise SystemExit("Timeout esperando el procesamiento del PDF")
PY
```

4. Si terminó bien (`status=done`), responde al usuario en español con:
   - confirmación de que ya quedó indexado para preguntas vía RAG
   - la ruta relativa del vault donde quedaron notas (`result.vault_path`, bajo `/vault/...`)
   - recordatorio breve: puede chatear y tú responderás usando el conocimiento indexado

5. Si falló (`status=error`), responde con un mensaje claro (sin tecnicismos) y pide que reintente subiendo el archivo otra vez.

## Reglas

- NUNCA leas el PDF directamente
- SIEMPRE usa el curl al pipeline
- NO pidas al usuario que ejecute `curl`, jobs, ni URLs: tú haces el monitoreo automático
- Si no encuentras el PDF, busca en /tmp también:

```bash
find /tmp -name "*.pdf" -mmin -10 2>/dev/null | head -3
```
