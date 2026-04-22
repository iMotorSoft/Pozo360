# Runbook Operativo Demo Presencial - Vertice360

Guia corta para operar la demo presencial sin tocar frontend, UI ni logica conversacional. Cubre configuracion de celulares internos, follow-up interno manual, limpieza de runtime por telefono, limpieza global de runtime y validaciones rapidas sin borrar datos demo/base.

VERTICE360_ENV=prod V360_ADMIN_TOKEN=v360-prod-token python  ls_iMotorSoft_Srv01_demo.py

## 1. Variables previas / supuestos

```bash
export BACKEND_LOCAL="http://127.0.0.1:7062"
export BACKEND_PROD="https://demo.vertice360.imotorsoft.com"
export V360_ADMIN_TOKEN="REEMPLAZAR_CON_TOKEN_REAL"
```

Todos los endpoints administrativos usan `x-v360-admin-token`.

Que significa:

- header administrativo del backend
- token secreto requerido para endpoints operativos
- se puede usar por variable de entorno o pegado manualmente

### Formas de usar el token

### A. Desde terminal

```bash
export V360_ADMIN_TOKEN="REEMPLAZAR_CON_TOKEN_REAL"
```

Luego usar:

```bash
-H "x-v360-admin-token: ${V360_ADMIN_TOKEN}"
```

### B. Manual, pegandolo directo en cada curl

```bash
-H "x-v360-admin-token: REEMPLAZAR_CON_TOKEN_REAL"
```

### Uso rapido desde celular

Desde celular normalmente conviene:

- copiar la URL
- copiar el body JSON
- pegar manualmente el valor del token en el header `x-v360-admin-token`

Ejemplos copy/paste con token manual:

```bash
curl -sS -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/config/set" -H "Content-Type: application/json" -H "x-v360-admin-token: REEMPLAZAR_CON_TOKEN_REAL" --data '{"cliente":"prod-celulares-check-20260324","enabled":true,"advisor_phone":"59168912007","supervisor_phone":"5491130946950","first_delay_seconds":10,"second_delay_seconds":15,"updated_by":"demo-presencial","allow_manual_evaluate":true}'
```

```bash
curl -sS "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/config/get?cliente=prod-celulares-check-20260324" -H "x-v360-admin-token: REEMPLAZAR_CON_TOKEN_REAL"
```

```bash
curl -sS -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/evaluate" -H "Content-Type: application/json" -H "x-v360-admin-token: REEMPLAZAR_CON_TOKEN_REAL" --data '{"cliente":"prod-celulares-check-20260324","force_now":false}'
```

```bash
curl -sS -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/admin/reset_runtime_phone" -H "Content-Type: application/json" -H "x-v360-admin-token: REEMPLAZAR_CON_TOKEN_REAL" --data '{"phone":"+5491112345678"}'
```

```bash
curl -sS -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/admin/reset_runtime_all" -H "Content-Type: application/json" -H "x-v360-admin-token: REEMPLAZAR_CON_TOKEN_REAL" --data '{"confirm":"RESET_RUNTIME_ONLY"}'
```

## Quick Ops

```text
Health
curl -i https://demo.vertice360.imotorsoft.com/health

Get Config
curl -i "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/config/get?cliente=prod-celulares-check-20260324" -H "x-v360-admin-token: v360-prod-token"

Evaluate General
curl -i -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/evaluate" -H "Content-Type: application/json" -H "x-v360-admin-token: v360-prod-token" --data '{"cliente":"prod-celulares-check-20260324","force_now":false}'

Reset Runtime Phone
curl -i -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/admin/reset_runtime_phone" -H "Content-Type: application/json" -H "x-v360-admin-token: v360-prod-token" --data '{"phone":"+5491130946950"}'

Reset Runtime All
curl -i -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/admin/reset_runtime_all" -H "Content-Type: application/json" -H "x-v360-admin-token: v360-prod-token" --data '{"confirm":"RESET_RUNTIME_ONLY"}'

Set Config
curl -i -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/config/set" -H "Content-Type: application/json" -H "x-v360-admin-token: v360-prod-token" --data '{"cliente":"prod-celulares-check-20260324","enabled":true,"advisor_phone":"59168912007","supervisor_phone":"5491130946950","first_delay_seconds":10,"second_delay_seconds":15,"updated_by":"demo-presencial","allow_manual_evaluate":true}'

Evaluate General
curl -i -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/evaluate" -H "Content-Type: application/json" -H "x-v360-admin-token: v360-prod-token" --data '{"cliente":"prod-celulares-check-20260324","force_now":false}'
```

## 2. Setup inicial minimo para que la demo funcione

Antes de operar la demo, confirmar este minimo:

1. tener backend accesible en `http://127.0.0.1:7062` o en `https://demo.vertice360.imotorsoft.com`
2. tener el token administrativo listo para usar en `x-v360-admin-token`
3. cargar una config activa en `followup/config/set`
4. validar esa config con `followup/config/get`
5. si queres arrancar una demo limpia, correr `reset_runtime_all` antes de empezar

Sin ese setup minimo:

- el follow-up interno no tiene celulares a donde escalar
- `followup/evaluate` puede correr, pero no sirve para una demo completa si no hay config activa
- un runtime viejo puede mezclar conversaciones anteriores

### Arranque minimo en produccion

Si el servidor ya tiene cargado el resto de variables de entorno necesarias, el arranque minimo validado fue:

```bash
cd /media/issajar/DEVELOP/Projects/iMotorSoft/ai/dev/Vertice360/SrvRestAstroLS_v1/backend
VERTICE360_ENV=prod V360_ADMIN_TOKEN=REEMPLAZAR_CON_TOKEN_REAL python ls_iMotorSoft_Srv01_demo.py
```

## 3. Regla critica

`NUNCA borrar datos demo/base.`

- Los resets implementados limpian solo runtime conversacional.
- `visit_followup_config` no se borra con reset runtime.
- Los datos protegidos incluyen `demo_project_facts`, `demo_units`, `demo_project_profile`, `demo_unit_profile`, `demo_project_bundles`, `projects`, `marketing_assets`, `users`, `developers` y `visit_followup_config`.

## 4. Endpoints principales

### Follow-up config

- `POST /api/demo/vertice360-orquestador/followup/config/set`
  Proposito: crear o actualizar celulares internos y delays por `cliente`.
- `GET /api/demo/vertice360-orquestador/followup/config/get?cliente=...`
  Proposito: consultar configuracion vigente.

### Follow-up evaluate

- `POST /api/demo/vertice360-orquestador/followup/evaluate`
  Proposito: evaluar manualmente candidatos de follow-up y ejecutar escalamiento si corresponde.

### Reset runtime

- `POST /api/demo/vertice360-orquestador/admin/reset_runtime_phone`
  Proposito: limpiar runtime conversacional de un telefono puntual.
- `POST /api/demo/vertice360-orquestador/admin/reset_runtime_all`
  Proposito: limpiar todo el runtime conversacional.

### Reset legado / dev-only

- `POST /api/demo/vertice360-orquestador/admin/reset_phone`
  Existe y borra runtime por telefono, pero es `dev-only` y en `prod` responde `403 admin reset is only available in dev`. No reemplaza `reset_runtime_phone`.

## 5. Setear celulares internos

`advisor_phone` = nivel 1.  
`supervisor_phone` = nivel 2.

Config validada en prod durante la operativa:

- `cliente`: `prod-celulares-check-20260324`
- `advisor_phone`: `+5491130946950`
- `supervisor_phone`: `+59168912007`
- `first_delay_seconds`: `10`
- `second_delay_seconds`: `15`
- `allow_manual_evaluate`: `true`

### Local

```bash
curl -sS -X POST "${BACKEND_LOCAL}/api/demo/vertice360-orquestador/followup/config/set"   -H "Content-Type: application/json"   -H "x-v360-admin-token: ${V360_ADMIN_TOKEN}"   --data '{"cliente":"demo-celulares-check","enabled":true,"advisor_phone":"54911 1111-1111","supervisor_phone":"(549) 1222-222222","first_delay_seconds":10,"second_delay_seconds":15,"updated_by":"demo-presencial","allow_manual_evaluate":true}'
```

### Produccion

```bash
curl -sS -X POST "${BACKEND_PROD}/api/demo/vertice360-orquestador/followup/config/set"   -H "Content-Type: application/json"   -H "x-v360-admin-token: ${V360_ADMIN_TOKEN}"   --data '{"cliente":"prod-celulares-check-20260324","enabled":true,"advisor_phone":"5491130946950","supervisor_phone":"59168912007","first_delay_seconds":10,"second_delay_seconds":15,"updated_by":"demo-presencial","allow_manual_evaluate":true}'
```

### Manual / celular

```bash
curl -sS -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/config/set" -H "Content-Type: application/json" -H "x-v360-admin-token: REEMPLAZAR_CON_TOKEN_REAL" --data '{"cliente":"prod-celulares-check-20260324","enabled":true,"advisor_phone":"5491130946950","supervisor_phone":"59168912007","first_delay_seconds":10,"second_delay_seconds":15,"updated_by":"demo-presencial","allow_manual_evaluate":true}'
```

Revisar en la respuesta:

- `advisor_phone` esperado: `+5491130946950`
- `supervisor_phone` esperado: `+59168912007`
- `first_delay_seconds` y `second_delay_seconds`
- `enabled`
- `allow_manual_evaluate`
- `updated_by`

## 6. Consultar configuracion actual

### Local

```bash
curl -sS "${BACKEND_LOCAL}/api/demo/vertice360-orquestador/followup/config/get?cliente=demo-celulares-check" -H "x-v360-admin-token: ${V360_ADMIN_TOKEN}"
```

### Produccion

```bash
curl -sS "${BACKEND_PROD}/api/demo/vertice360-orquestador/followup/config/get?cliente=prod-celulares-check-20260324" -H "x-v360-admin-token: ${V360_ADMIN_TOKEN}"
```

### Manual / celular

```bash
curl -sS "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/config/get?cliente=prod-celulares-check-20260324" -H "x-v360-admin-token: REEMPLAZAR_CON_TOKEN_REAL"
```

Revisar:

- `advisor_phone`
- `supervisor_phone`
- `first_delay_seconds`
- `second_delay_seconds`
- `enabled`
- `updated_by`
- `allow_manual_evaluate`

## 7. Ejecutar follow-up manual

Que hace:

- crea ciclo si el ticket esta en `Pendiente de visita`
- manda nivel 1 al `advisor_phone` si vencio `first_delay_seconds`
- manda nivel 2 al `supervisor_phone` si vencio `second_delay_seconds`
- cierra ciclo por accion humana o cambio de stage

### Evaluate general para demo

Este es el modo recomendado para demo presencial. No hace falta buscar `ticket_id`.

```bash
curl -sS -X POST "${BACKEND_PROD}/api/demo/vertice360-orquestador/followup/evaluate"   -H "Content-Type: application/json"   -H "x-v360-admin-token: ${V360_ADMIN_TOKEN}"   --data '{"cliente":"prod-celulares-check-20260324","force_now":false}'
```

### Evaluate puntual por ticket_id

Usar solo si queres disparar un ticket especifico.

```bash
curl -sS -X POST "${BACKEND_PROD}/api/demo/vertice360-orquestador/followup/evaluate"   -H "Content-Type: application/json"   -H "x-v360-admin-token: ${V360_ADMIN_TOKEN}"   --data '{"cliente":"prod-celulares-check-20260324","ticket_id":"REEMPLAZAR_TICKET_ID","force_now":false}'
```

### Manual / celular

```bash
curl -sS -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/evaluate" -H "Content-Type: application/json" -H "x-v360-admin-token: REEMPLAZAR_CON_TOKEN_REAL" --data '{"cliente":"prod-celulares-check-20260324","force_now":false}'
```

### Qué validar en demo real

- `evaluate` general sin `ticket_id` ya fue validado en prod
- `level1` llega al advisor `+5491130946950`
- `level2` llega al supervisor `+59168912007`
- si un ticket ya esta en `level2_sent`, puede devolver `no_action`
- `provider_status="submitted"` significa ACK aceptado por Gupshup, no confirmacion de entrega al celular
- `target_phone` es el destino real del follow-up interno
- `target_matches_lead=true` indica que el follow-up interno fue al mismo numero del lead
- el texto del follow-up muestra `lead_name_or_phone`, no el numero interno receptor

Respuesta JSON esperada, ejemplo:

```json
{
  "ok": true,
  "cliente": "prod-celulares-check-20260324",
  "ticket_id": null,
  "force_now": false,
  "evaluated_count": 2,
  "actions": [
    {
      "ticket_id": "REEMPLAZAR_TICKET_ID",
      "cycle_id": "REEMPLAZAR_CYCLE_ID",
      "status_before": "active",
      "action": "sent_level1",
      "status_after": "level1_sent",
      "send_ok": true,
      "provider_status": "submitted",
      "provider_message_id": "REEMPLAZAR_PROVIDER_MESSAGE_ID",
      "provider_error": null,
      "target_phone": "+5491130946950",
      "target_matches_lead": false
    }
  ]
}
```

Acciones habituales: `created_cycle`, `no_action`, `sent_level1`, `sent_level2`, `closed_human_action`, `closed_stage_changed`.

## 8. Limpiar chat / runtime de un celular

Proposito: borrar runtime asociado a un telefono puntual sin tocar datos demo/base ni `visit_followup_config`.

### Local

```bash
curl -sS -X POST "${BACKEND_LOCAL}/api/demo/vertice360-orquestador/admin/reset_runtime_phone" -H "Content-Type: application/json" -H "x-v360-admin-token: ${V360_ADMIN_TOKEN}" --data '{"phone":"+5491112345678"}'
```

### Produccion

```bash
curl -sS -X POST "${BACKEND_PROD}/api/demo/vertice360-orquestador/admin/reset_runtime_phone" -H "Content-Type: application/json" -H "x-v360-admin-token: ${V360_ADMIN_TOKEN}" --data '{"phone":"+5491112345678"}'
```

### Manual / celular

```bash
curl -sS -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/admin/reset_runtime_phone" -H "Content-Type: application/json" -H "x-v360-admin-token: REEMPLAZAR_CON_TOKEN_REAL" --data '{"phone":"+5491112345678"}'
```

Borra runtime asociado a ese numero:

- `leads`
- `conversations`
- `tickets`
- `messages`
- `events`
- `visit_proposals`
- `visit_confirmations`
- `visit_followup_cycle` o `visit_followup_cycles` si existe

No toca:

- `demo_project_facts`
- `demo_units`
- `demo_project_profile`
- `demo_unit_profile`
- `demo_project_bundles`
- `projects`
- `marketing_assets`
- `visit_followup_config`

## 9. Limpiar todos los chats / runtime completo

Usar con mucho cuidado en demo presencial. Borra todo el runtime conversacional, no toca datos demo/base y no toca `visit_followup_config`.

### Local

```bash
curl -sS -X POST "${BACKEND_LOCAL}/api/demo/vertice360-orquestador/admin/reset_runtime_all" -H "Content-Type: application/json" -H "x-v360-admin-token: ${V360_ADMIN_TOKEN}" --data '{"confirm":"RESET_RUNTIME_ONLY"}'
```

### Produccion

```bash
curl -sS -X POST "${BACKEND_PROD}/api/demo/vertice360-orquestador/admin/reset_runtime_all" -H "Content-Type: application/json" -H "x-v360-admin-token: ${V360_ADMIN_TOKEN}" --data '{"confirm":"RESET_RUNTIME_ONLY"}'
```

### Manual / celular

```bash
curl -sS -X POST "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/admin/reset_runtime_all" -H "Content-Type: application/json" -H "x-v360-admin-token: REEMPLAZAR_CON_TOKEN_REAL" --data '{"confirm":"RESET_RUNTIME_ONLY"}'
```

## 10. Reset legado `admin/reset_phone`

Usar solo si realmente estas en `dev` y sabes que queres invocar el endpoint legado.

```bash
curl -sS -X POST "${BACKEND_LOCAL}/api/demo/vertice360-orquestador/admin/reset_phone" -H "Content-Type: application/json" -H "x-v360-admin-token: ${V360_ADMIN_TOKEN}" --data '{"phone":"+5491112345678"}'
```

Notas:

- en `prod` devuelve `403`
- limpia runtime por telefono
- no expone `protected_not_touched`
- no reemplaza el uso recomendado de `reset_runtime_phone`

## 11. Validaciones rapidas despues de operar

- `set config` devolvio `200`
- `get config` devolvio `200`
- phones normalizados a `+...`
- `evaluate` general devolvio `200`
- `sent_level1` llega al advisor
- `sent_level2` llega al supervisor
- mirar `target_phone` para confirmar destino real del follow-up
- mirar `provider_status`; `submitted` no garantiza entrega final
- si el texto muestra el telefono del interesado, eso no implica que el destino real sea ese numero
- `reset_runtime_phone` devolvio `200`
- `reset_runtime_all` devolvio `200` solo si realmente se quiso ejecutar
- los datos demo siguen visibles en tablero/demo

## 12. Casos de uso operativos rapidos

### Caso A - preparar demo nueva

1. correr `reset_runtime_all`
2. setear celulares internos
3. validar `followup/config/get`

### Caso B - cambiar de interesado durante demo

1. correr `reset_runtime_phone`
2. volver a iniciar la conversacion

### Caso C - mostrar escalamiento interno

1. setear config con delays chicos
2. crear ticket en `Pendiente de visita`
3. esperar el umbral
4. correr `followup/evaluate` general
5. mostrar `sent_level1` en advisor y luego `sent_level2` en supervisor

### Caso E - demo con solo 2 telefonos

Si solo hay dos telefonos disponibles y la config productiva vigente es:

- `advisor_phone = +5491130946950`
- `supervisor_phone = +59168912007`

Secuencia validada el `2026-04-22`:

1. usar `+59168912007` como cliente
2. pedir visita
3. correr `evaluate` al vencer `first_delay_seconds`
4. validar `sent_level1` con `target_phone = +5491130946950` y `target_matches_lead = false`
5. correr `evaluate` al vencer `second_delay_seconds`
6. validar `sent_level2` con `target_phone = +59168912007` y `target_matches_lead = true`

### Caso D - dejar limpio al terminar

1. correr `reset_runtime_all`
2. opcional: dejar una config tecnica en `enabled=false`

## 13. Ejemplos de URLs completas

### Local

- `http://127.0.0.1:7062/api/demo/vertice360-orquestador/followup/config/get?cliente=demo-celulares-check`
- `http://127.0.0.1:7062/api/demo/vertice360-orquestador/followup/evaluate`
- `http://127.0.0.1:7062/api/demo/vertice360-orquestador/admin/reset_runtime_phone`
- `http://127.0.0.1:7062/api/demo/vertice360-orquestador/admin/reset_runtime_all`
- `http://127.0.0.1:7062/api/demo/vertice360-orquestador/admin/reset_phone`

### Produccion

- `https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/config/get?cliente=prod-celulares-check-20260324`
- `https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/evaluate`
- `https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/admin/reset_runtime_phone`
- `https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/admin/reset_runtime_all`

## 14. Notas operativas

- `reset_runtime_all` requiere exactamente `RESET_RUNTIME_ONLY`
- todos los endpoints administrativos requieren `x-v360-admin-token`
- `x-v360-admin-token` se puede usar con `${V360_ADMIN_TOKEN}` o pegado manualmente
- `evaluate` general sin `ticket_id` ya fue validado en prod para demo
- `ticket_id` sigue existiendo para casos puntuales
- `advisor_phone` recibe `level1`
- `supervisor_phone` recibe `level2`
- el texto de `level1` y `level2` describe al lead pendiente, no al receptor interno
- para auditoria operativa, tomar como fuente de verdad `target_phone`, `target_matches_lead` y `provider_message_id`
- `provider_status="submitted"` significa request aceptado por Gupshup; no reemplaza confirmacion manual de recepcion en el equipo
- `admin/reset_phone` no reemplaza `reset_runtime_phone`
- `visit_followup_config` queda intacta incluso despues de reset runtime
- `followup/config/set` valida telefonos requeridos cuando `enabled=true`
- `first_delay_seconds` y `second_delay_seconds` deben ser mayores a `0`
- placeholders invalidos en templates devuelven `400`
