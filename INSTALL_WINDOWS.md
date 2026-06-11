# Instalación AIRA — Windows

## Pre-requisitos

Instala estas tres cosas antes de empezar:

| Programa | Descarga | Para qué sirve |
|---|---|---|
| **Docker Desktop** | https://www.docker.com/products/docker-desktop | Ejecuta los servicios de AIRA |
| **Ollama** | https://ollama.com/download/windows | Modelos de IA locales (embeddings) |
| **Obsidian** | https://obsidian.md | Tu vault de notas |

Después de instalar cada uno, ábrelos y espera a que estén corriendo:
- Docker Desktop: el ícono de la ballena en la barra de tareas debe estar verde
- Ollama: el ícono de la llama debe aparecer en la barra de tareas

---

## 1. Descargar el modelo de embeddings

Abre **PowerShell** y ejecuta:

```powershell
ollama pull bge-m3
```

Esto puede tardar varios minutos. Solo necesitas hacerlo una vez.

---

## 2. Configurar el archivo .env

Dentro de la carpeta `aira_RAG` que recibiste:

1. Busca el archivo `.env.example`
2. Cópialo y renómbralo a `.env`
3. Ábrelo con el Bloc de notas y rellena:

```
ANTHROPIC_API_KEY=sk-ant-TU_KEY_AQUI
VAULT_PATH=C:/Users/TuNombre/Documents/MiVault
TELEGRAM_BOT_TOKEN=tu_bot_token_aqui
ALLOWED_USER_IDS=123456789
```

> **Importante:** La ruta del vault usa barras `/` no `\`  
> Ejemplo correcto: `C:/Users/Cliente/Documents/ObsidianVault`

Para obtener tu ID de Telegram: escríbele a **@userinfobot** en Telegram, te responde con tu ID numérico.

---

## 3. Iniciar AIRA

Doble clic en **`start-aira.bat`**

El script verifica automáticamente que todo esté en orden y arranca los servicios.
Si algo falta, te indica exactamente qué hacer.

---

## 4. (Opcional) Autoarranque con Windows

Para que AIRA arranque solo cuando enciendes la computadora:

1. Clic derecho en **`setup-autostart.bat`**
2. Selecciona **Ejecutar como administrador**

Para desactivarlo más adelante:
```
schtasks /delete /tn "AIRA Autostart" /f
```

---

## Uso diario

- **Iniciar:** doble clic en `start-aira.bat`
- **Detener:** doble clic en `stop-aira.bat`
- Con autoarranque activado, no necesitas hacer nada — AIRA arranca solo

---

## Cómo usar AIRA en Telegram

### Subir un PDF

1. En el chat con el bot, toca el ícono de adjuntar 📎
2. Selecciona **Archivo** (no Foto)
3. Elige tu PDF — el bot lo procesa automáticamente

### Hacer preguntas

- Sobre tus notas: *"¿Qué dice mi nota sobre diseño?"*
- Sobre tus libros: *"Resume el libro que subí sobre marketing"*
- Buscar en internet: *"Busca las últimas noticias sobre IA"*

### Reiniciar contexto

Si el bot parece confundido o quieres empezar de cero:

```
/reset
```

---

## Solución de problemas

| Problema | Solución |
|---|---|
| Docker no arranca | Abre Docker Desktop y espera a que el ícono esté verde |
| Ollama no conecta | Abre Ollama desde el menú de inicio |
| El bot no responde | Verifica Docker Desktop y ejecuta `start-aira.bat` |
| Error de ruta del vault | La ruta en `.env` debe usar `/` en vez de `\` |
| Primera vez tarda mucho | Es normal — está descargando el modelo de embeddings |
