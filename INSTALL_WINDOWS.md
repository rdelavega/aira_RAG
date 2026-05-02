# Checklist de instalación AIRA — Windows (sin WSL)

## Pre-requisitos (instalar antes de empezar)

- [ ] **Docker Desktop** — https://www.docker.com/products/docker-desktop
  - Instalar y abrir Docker Desktop
  - Esperar a que el ícono de la ballena en la barra de tareas esté verde
- [ ] **Ollama para Windows** — https://ollama.com/download/windows
  - Instalar y abrir Ollama
  - Verificar que el ícono de la llama aparece en la barra de tareas
- [ ] **Obsidian** — https://obsidian.md
  - Instalar y crear un vault nuevo (o usar uno existente)
  - Anotar la ruta completa del vault (ej: C:\Users\Cliente\Documents\MiVault)

---

## 1. Descargar modelos de Ollama

Abre **PowerShell** y ejecuta:

```powershell
ollama pull bge-m3
ollama pull llama3.2:3b
```

Esto puede tardar varios minutos dependiendo de la conexión.

---

## 2. Copiar el proyecto

- Recibe la carpeta `aira_RAG` del desarrollador (por USB, Drive, etc.)
- Cópiala a una ubicación fácil de recordar, por ejemplo:
  ```
  C:\Users\Cliente\Documents\aira_RAG
  ```

---

## 3. Configurar el archivo .env

- Dentro de la carpeta `aira_RAG`, encuentra el archivo `.env.example`
- Cópialo y renómbralo a `.env`
- Ábrelo con el Bloc de notas y rellena los valores:

```
ANTHROPIC_API_KEY=sk-ant-TU_KEY_AQUI
VAULT_PATH=C:/Users/Cliente/Documents/MiVault
TELEGRAM_CHAT_ID=TU_CHAT_ID
OLLAMA_HOST=http://host.docker.internal:11434
```

> ⚠️ Importante: La ruta del vault usa barras `/` no `\`

---

## 4. Configurar el bot de Telegram

- Abre Telegram y busca el bot `@MyAiraV1_bot`
- Escríbele `/start`
- Para obtener tu Chat ID: escríbele a `@userinfobot` en Telegram

---

## 5. Primera instalación

- Haz clic derecho en `setup-autostart.bat` → **Ejecutar como administrador**
- Esto configura AIRA para que arranque automáticamente con Windows

---

## 6. Iniciar AIRA

- Doble clic en `start-aira.bat`
- Espera a que aparezca el mensaje de confirmación
- ¡Listo! Ya puedes usar el bot en Telegram

---

## Uso diario

- **AIRA arranca solo** cuando enciendes la computadora
- Si necesitas apagarlo: doble clic en `stop-aira.bat`
- Si necesitas reiniciarlo: doble clic en `start-aira.bat`

---

## Cómo usar AIRA en Telegram

### Subir un PDF

1. En el chat con el bot, toca el ícono de adjuntar 📎
2. Selecciona **Archivo** (no Foto)
3. Elige tu PDF
4. Escribe `/ingesta` y envía

### Hacer preguntas

- Sobre tus notas: _"¿Qué dice mi nota sobre diseño?"_
- Sobre tus libros: _"Resume el libro que subí sobre marketing"_
- Buscar en internet: _"Busca las últimas noticias sobre IA"_

### Aprobar borradores

- Los análisis generados se guardan en `00_INBOX/Borradores_IA/`
- Cuando los revises y apruebes, dile a AIRA: _"Aprueba el borrador de [nombre]"_

---

## Solución de problemas

| Problema                | Solución                                                              |
| ----------------------- | --------------------------------------------------------------------- |
| Docker no arranca       | Abre Docker Desktop manualmente y espera a que el ícono esté verde    |
| Ollama no conecta       | Abre Ollama desde el menú de inicio                                   |
| El bot no responde      | Verifica que Docker Desktop esté corriendo y ejecuta `start-aira.bat` |
| Error de ruta del vault | Verifica que la ruta en `.env` usa `/` no `\`                         |
