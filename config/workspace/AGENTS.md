# Reglas de fuentes de información

## Vault de Obsidian

El vault del usuario está SIEMPRE en `/vault`. Esta ruta está garantizada por el sistema.
Antes de reportar que no encuentras el vault, verifica con:

```bash
ls /vault 2>&1 | head -5
```

Si el comando devuelve archivos, el vault está accesible. Úsalo directamente.
Si devuelve error de permiso o ruta no existe, informa al usuario que el vault no está montado
y que debe reiniciar los contenedores con `docker compose restart`.

## Usa el RAG (tus notas) cuando:

- El usuario pregunta sobre libros que ha leído
- El usuario pregunta sobre notas guardadas en Obsidian
- El usuario dice "en mis notas", "lo que leí", "el libro de X"

## Usa búsqueda web cuando:

- El usuario pregunta sobre eventos actuales
- El usuario necesita información que no está en sus notas
- El usuario dice "busca", "qué es", "noticias sobre"

## Prioridad

1. Primero revisa si la respuesta está en las notas (RAG)
2. Si no está, busca en internet
3. Nunca mezcles información de notas con información web sin aclararlo

## Límites de seguridad

- NUNCA ejecutes comandos que borren archivos del vault
- NUNCA compartas el token del gateway
- NUNCA accedas a rutas fuera de /vault y /root/.openclaw/workspace
