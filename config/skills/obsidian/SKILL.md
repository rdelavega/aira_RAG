---
name: obsidian
description: Lee, analiza y escribe notas en el vault de Obsidian del usuario
always-on: true
user-invocable: true
---

## Tu rol

El vault de Obsidian está en /vault. SIEMPRE usa esta ruta sin preguntar al usuario.

## Comandos disponibles

### Listar notas

```bash
find "/vault" -name "*.md" | sort
```

### Leer una nota

```bash
cat "/vault/ruta/nota.md"
```

### Leer borradores generados por AIRA (importante)

Cuando el usuario te pase una ruta que parezca carpeta (por ejemplo `00_INBOX/Borradores_IA/...` sin `.md`), **NO intentes leerla como archivo**.

1) Verifica si es carpeta o archivo:

```bash
RUTA="/vault/00_INBOX/Borradores_IA/ALGO"
if [ -d "$RUTA" ]; then
  find "$RUTA" -maxdepth 3 -type f -name "*.md" | sort
elif [ -f "$RUTA" ]; then
  cat "$RUTA"
else
  echo "No existe esa ruta en el vault"
fi
```

2) Si es carpeta, prioriza leer primero (si existen):
- `00_Global.md`
- `00_Examen.md`
- `Capitulos/Cap01.md`

### Crear una nota

```bash
cat > "/vault/Carpeta/NombreNota.md" << 'ENDOFFILE'
---
created_by: Aira
date: FECHA
tags: [ai-generated]
---
CONTENIDO
ENDOFFILE
```

### Aprobar borrador

```bash
mv "/vault/00_INBOX/Borradores_IA/LIBRO" "/vault/10_Libros/LIBRO"
```

### Consultar RAG

```bash
curl -s -X POST http://fastapi:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "PREGUNTA", "scope": "SCOPE"}'
```

Si el usuario no es técnico, no le muestres el comando: úsalo internamente y responde con la respuesta final en español.

## Scopes disponibles

- `10_Libros` — libros indexados
- `20_DISENO` — notas de diseño
- `30_NEGOCIO` — notas de negocio
- Sin scope — busca en todo

## Reglas

1. NUNCA sobreescribas una nota sin confirmar
2. Usa frontmatter YAML en todas las notas nuevas
3. Usa sintaxis Obsidian: `[[enlaces]]`, `#tags`
