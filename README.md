# Monitor de "Destino Oculto 3" — Wingo

Vigila wingo.com y noticias cada ~2-3 minutos, gratis, 24/7, y te avisa por
Telegram al celular apenas detecte señales de que lanzaron la edición 3.

## Paso 1 — Crear tu bot de Telegram (2 minutos)

1. En Telegram, busca **@BotFather** y ábrele un chat.
2. Envíale `/newbot`.
3. Ponle un nombre (ej. `Wingo Alert Bot`) y un usuario que termine en `bot`
   (ej. `wingo_destino_oculto_bot`).
4. BotFather te va a dar un **token** parecido a:
   `7912345678:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   → Guárdalo, es tu `TELEGRAM_BOT_TOKEN`.

## Paso 2 — Obtener tu chat_id

1. Busca tu bot recién creado en Telegram (por el usuario que le pusiste) y
   dale **"Iniciar" / Start**, o mándale cualquier mensaje, ej: "hola".
2. En tu navegador abre esta URL (reemplaza `<TOKEN>` por el token del paso 1):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Busca en el JSON el valor `"chat":{"id":123456789,...}` → ese número es tu
   `TELEGRAM_CHAT_ID`.

## Paso 3 — Subir este proyecto a GitHub

1. Crea una cuenta gratis en [github.com](https://github.com) si no tienes.
2. Crea un repositorio nuevo, **privado** (para que nadie más vea tu bot),
   ej. `wingo-destino-oculto`.
3. Sube todos los archivos de esta carpeta (`monitor.py`, `requirements.txt`,
   `state.json`, `.github/workflows/monitor.yml`, este `README.md`) a ese
   repositorio. La forma más fácil: en la página del repo, "Add file" →
   "Upload files", y arrastra los archivos (mantén la carpeta
   `.github/workflows/monitor.yml` en esa ruta exacta).

## Paso 4 — Configurar los secrets

1. En tu repo: **Settings → Secrets and variables → Actions → New repository secret**.
2. Crea dos secrets:
   - `TELEGRAM_BOT_TOKEN` → el token del Paso 1
   - `TELEGRAM_CHAT_ID` → el número del Paso 2

## Paso 5 — Probarlo

1. Ve a la pestaña **Actions** de tu repo.
2. Selecciona el workflow **"Monitor Destino Oculto Wingo"**.
3. Click en **"Run workflow"** (botón manual) para probarlo ya mismo.
4. Revisa los logs: debería decir "Sin novedades" (mientras no haya
   lanzamiento). Si algo falla, el error aparece ahí mismo.

A partir de ese momento, el workflow corre solo cada ~2-3 minutos, sin que
tengas que hacer nada ni tener el celular o computador prendido corriendo
código — solo recibirás la notificación de Telegram cuando detecte el
lanzamiento.

## Cómo funciona la detección

El script busca la palabra **"destino oculto"** junto con frases que indican
que ya se puede comprar (ej. "ya puedes", "compra tus tiquetes", "tercera
edición", "destino oculto 3", "cupos limitados"), en:

- La página principal de wingo.com
- Noticias recientes vía Google News (búsqueda "Destino Oculto Wingo")

Esto evita que te llegue una falsa alarma solo porque un artículo viejo
mencione "destino oculto" hablando de ediciones pasadas.

Una vez manda la alerta, se marca como `"alerted": true` en `state.json` para
no mandarte la misma alarma 500 veces seguidas. Si quieres reactivar el
monitoreo después (ej. para el próximo año), edita `state.json` en GitHub y
pon `"alerted": false` otra vez.

## Limitaciones a tener en cuenta

- **Instagram/Facebook no se monitorean directamente**: ambas plataformas
  bloquean el scraping automatizado sin iniciar sesión, así que no es
  confiable ni sostenible incluirlas aquí. La cobertura de noticias + sitio
  web debería avisarte con tiempo de sobra, ya que los medios suelen cubrir
  el lanzamiento apenas Wingo lo anuncia.
- **GitHub Actions no garantiza el minuto exacto**: en momentos de alta
  demanda en GitHub, un cron puede atrasarse un par de minutos. Es gratis y
  confiable en general, pero no es un sistema de tiempo real perfecto.
- Si wingo.com cambia su estructura (ej. exige JavaScript pesado para
  cargar contenido), puede que el `requests` simple no vea el texto — si
  notas que nunca detecta nada aun con el sitio actualizado, avísame y
  ajustamos el script para usar un navegador headless (Playwright).
