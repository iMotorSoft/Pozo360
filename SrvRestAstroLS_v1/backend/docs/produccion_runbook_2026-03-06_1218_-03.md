# Runbook de Produccion Vertice360

Fecha/Hora de creacion (local): 2026-03-06 12:18:25 -03
Fecha/Hora de creacion (UTC): 2026-03-06 15:18:26Z
Estado: borrador operativo inicial (actualizable)

## Objetivo
Dejar un procedimiento manual y repetible para pasar de entorno dev a produccion,
con foco en:
- Configuracion de variables en VM (`~/.bashrc`).
- Build frontend Astro.
- Copia de `dist` al servidor de produccion.
- Copia de backend al servidor de produccion.
- Validaciones posteriores al deploy.

## 1) Variables de entorno en VM de produccion (`~/.bashrc`)

Agregar/ajustar este bloque:

```bash
# ===== Vertice360 backend (prod) =====
export VERTICE360_ENV="prod"
export VERTICE360_HOST="0.0.0.0"
export VERTICE360_PORT="7062"
export VERTICE360_UVICORN_WORKERS="2"

# URL publica backend/demo
export VERTICE360_PUBLIC_BASE_URL_PRO="https://demo.vertice360.imotorsoft.com"

# CORS frontend permitido
export VERTICE360_FE_URL_LOCAL="https://demo.vertice360.imotorsoft.com"
export VERTICE360_FE_URL_IP="https://demo.vertice360.imotorsoft.com"

# DB principal + DB v360 (obligatoria para orquestador live)
export VERTICE360_DB_URL="postgresql+psycopg://USER:PASS@HOST:5432/vertice360"
export DB_PG_V360_URL="postgresql+psycopg://USER:PASS@HOST:5432/v360"
export ALLOW_FALLBACK_V360_DB="false"

# Seguridad
export VERTICE360_JWT_SECRET="CAMBIAR_ESTE_SECRET_EN_PROD"
export V360_ADMIN_TOKEN="TOKEN_ADMIN_LARGO_Y_ALEATORIO"

# ===== Gupshup (si aplica) =====
export GUPSHUP_APP_NAME_PRO="vertice360pro"
export GUPSHUP_API_KEY_PRO="TU_API_KEY_PROD"
export GUPSHUP_SRC_NUMBER_PRO="54911XXXXXXXX"
export GUPSHUP_BASE_URL_PRO="https://api.gupshup.io"

# Alias canonico runtime
export GUPSHUP_APP_NAME="$GUPSHUP_APP_NAME_PRO"
export GUPSHUP_API_KEY="$GUPSHUP_API_KEY_PRO"
export GUPSHUP_WA_SENDER="$GUPSHUP_SRC_NUMBER_PRO"

# ===== Meta WhatsApp (si aplica) =====
export META_VERTICE360_WABA_TOKEN="..."
export META_VERTICE360_WABA_ID="..."
export META_VERTICE360_PHONE_NUMBER_ID="..."
export META_VERTICE360_VERIFY_TOKEN="..."
export META_APP_SECRET_IMOTORSOFT="..."
export META_GRAPH_VERSION="v20.0"

# ===== OpenAI (si aplica) =====
export VERTICE360_OPENAI_KEY="..."
export VERTICE360_OPENAI_MODEL="gpt-4o-mini"
```

Aplicar cambios:

```bash
source ~/.bashrc
```

## 2) Paso manual obligatorio en frontend (Astro)

Archivo:
- `astro/src/components/global.js`

Cambio manual previo a build:

```js
export const URL_REST = URL_REST_PRO;
```

Contexto:
- Hoy suele estar en `URL_REST_DEV`.
- Si no se cambia, frontend en produccion puede seguir pegando a backend local/dev.

## 3) Build de frontend (Astro)

Desde `SrvRestAstroLS_v1/astro`:

```bash
pnpm build
```

Salida esperada:
- Carpeta `astro/dist/` generada.
- Sin errores de compilacion.

Nota:
- En el deploy del 2026-04-26 se uso `pnpm`.
- Si se cambia el gestor de paquetes, respetar el lockfile vigente del frontend.

## 4) Copia de frontend `dist` al servidor de produccion

Destino productivo actual:

```bash
export PROD_HOST="imotorsoft.com"
export PROD_USER="administrator"
export PROD_FE_PATH="/home/administrator/project/iMotorSoft/ai/Pozo360/SrvRestAstroLS_v1/astro/dist"
```

### Opcion recomendada: `rsync`

```bash
rsync -avz --delete \
  /media/issajar/DEVELOP/Projects/iMotorSoft/ai/dev/Vertice360/SrvRestAstroLS_v1/astro/dist/ \
  ${PROD_USER}@${PROD_HOST}:${PROD_FE_PATH}/
```

### Opcion simple: `scp`

```bash
scp -r \
  /media/issajar/DEVELOP/Projects/iMotorSoft/ai/dev/Vertice360/SrvRestAstroLS_v1/astro/dist/* \
  ${PROD_USER}@${PROD_HOST}:${PROD_FE_PATH}/
```

## 5) Copia de backend al servidor de produccion

Destino productivo actual:

```bash
export PROD_HOST="imotorsoft.com"
export PROD_USER="administrator"
export PROD_BE_PATH="/home/administrator/project/iMotorSoft/ai/Pozo360/SrvRestAstroLS_v1/backend"
```

### Opcion recomendada: `rsync` (sin basura local)

```bash
rsync -avz --delete \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude '.ruff_cache' \
  --exclude 'tests' \
  /media/issajar/DEVELOP/Projects/iMotorSoft/ai/dev/Vertice360/SrvRestAstroLS_v1/backend/ \
  ${PROD_USER}@${PROD_HOST}:${PROD_BE_PATH}/
```

### Opcion alternativa: `scp`

```bash
scp -r \
  /media/issajar/DEVELOP/Projects/iMotorSoft/ai/dev/Vertice360/SrvRestAstroLS_v1/backend/* \
  ${PROD_USER}@${PROD_HOST}:${PROD_BE_PATH}/
```

Nota:
- `scp` no borra archivos viejos en destino.
- `rsync --delete` mantiene destino espejo.
- No copiar `.venv` local al server.
- Si aparece `cannot delete non-empty directory` sobre un modulo eliminado, revisar si quedaron archivos excluidos como `__pycache__`. Si el `rsync` termina con codigo `0`, el deploy no necesariamente fallo.

## 6) Reinicio del backend demo en produccion (`tmux`)

El backend demo de Vertice360 se opera manualmente en `tmux`.

Sesion actual:
- nombre de sesion: `v360 api`
- path backend: `/home/administrator/project/iMotorSoft/ai/Pozo360/SrvRestAstroLS_v1/backend`

Entrar a la sesion:

```bash
ssh ${PROD_USER}@${PROD_HOST}
tmux attach -t "v360 api"
```

Arrancar/reiniciar dentro del pane correcto:

```bash
cd /home/administrator/project/iMotorSoft/ai/Pozo360/SrvRestAstroLS_v1/backend
source .venv/bin/activate
VERTICE360_ENV=prod V360_ADMIN_TOKEN=v360-prod-token python  ls_iMotorSoft_Srv01_demo.py
```

Si se lanza desde fuera de `tmux`, se puede enviar el comando al pane:

```bash
ssh ${PROD_USER}@${PROD_HOST} \
  "tmux send-keys -t 'v360 api:4' C-c; \
   sleep 2; \
   tmux send-keys -t 'v360 api:4' 'cd /home/administrator/project/iMotorSoft/ai/Pozo360/SrvRestAstroLS_v1/backend' C-m; \
   tmux send-keys -t 'v360 api:4' 'source .venv/bin/activate' C-m; \
   tmux send-keys -t 'v360 api:4' 'VERTICE360_ENV=prod V360_ADMIN_TOKEN=v360-prod-token python  ls_iMotorSoft_Srv01_demo.py' C-m"
```

Validar en el pane que aparezca:
- `env=prod`
- `host=0.0.0.0 port=7062`
- `db_v360_valid=True`
- `gupshup_enabled=True`
- `Uvicorn running on http://0.0.0.0:7062`

Nota:
- Activar siempre `.venv` antes de levantar Python.
- Si la UI muestra `HTTP 502`, revisar primero si el proceso Python quedo detenido en el pane.

## 7) Validaciones post-deploy

## 7.1 Backend

```bash
curl -fsS https://demo.vertice360.imotorsoft.com/health
curl -fsS https://demo.vertice360.imotorsoft.com/version
curl -fsS "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/bootstrap?cliente=59168912007"
curl -fsS "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/dashboard?cliente=59168912007"
```

Validar log de arranque:
- `env=prod`
- `db_v360_valid=True` o warning controlado
- `gupshup_enabled` segun configuracion

## 7.2 Frontend

Abrir en navegador:
- `https://demo.vertice360.imotorsoft.com/demo/vertice360-orquestador/?cliente=59168912007`

Confirmar:
- Carga landing.
- Con `?cliente=...` abre app live.
- SSE activa (badge Live/Reconexion y actualizacion de conversaciones).
- Se carga el numero WhatsApp demo.

## 7.3 Endpoints live orquestador

```bash
curl -fsS "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/bootstrap?cliente=59168912007"
curl -fsS "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/dashboard?cliente=59168912007"
```

## 8) Checklist corto de release

- [ ] `global.js` en `URL_REST_PRO`.
- [ ] `pnpm build` OK.
- [ ] `~/.bashrc` de VM actualizado y recargado.
- [ ] `DB_PG_V360_URL` apunta a DB `v360`.
- [ ] Backend copiado (rsync/scp).
- [ ] Frontend `dist` copiado (rsync/scp).
- [ ] Servicios reiniciados.
- [ ] Health checks OK.
- [ ] Prueba funcional orquestador OK.

## 9) Puntos importantes para futuras actualizaciones

Cada vez que se actualice este documento, registrar:
- Fecha/hora local + UTC.
- Commit/tag desplegado (frontend y backend).
- Variables cambiadas en produccion.
- Resultado de validaciones (OK/NO OK).
- Incidentes y rollback si aplica.

## 10) Registro de cambios del documento

- 2026-03-06 12:18:25 -03 (2026-03-06 15:18:26Z): creacion inicial.
- 2026-04-26 11:10 -03 aprox: se agregaron paths reales de produccion, build con `pnpm`, sync con `rsync`, reinicio manual por `tmux` + `.venv`, y validaciones de la demo live.
