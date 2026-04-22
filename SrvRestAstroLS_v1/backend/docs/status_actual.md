# Status Actual

- Fecha/hora local: 2026-04-15 19:48:01 -0300
- Estado: migracion de PostgreSQL local a Ubuntu `24.04` preparada a nivel operativo, sin levantar aun el contenedor.
- Docker Community instalado y reconfigurado con `data-root` en `/media/issajar/DEVELOP/docker-data`.
- Usuario `issajar` agregado al grupo `docker`.
- Red externa `dev_network` creada.
- Laboratorio PostgreSQL alineado a base `v360` en `/media/issajar/DEVELOP/Projects/iMotorSoft/ai/lab/postgres/docker-compose.yml`.
- `~/.bashrc` actualizado con `DB_PG_V360_URL` para el backend Vertice360.
- Milvus levanto con datos persistidos detectados (`JAI_document_embeddings`, `3231` rows); no parece requerir restore inmediato, pero queda pendiente validacion funcional por errores de pipeline.
- Pendiente: levantar `imotorsoft-postgres`, restaurar `v360.dump` y validar conexion real del backend.
- Detalle completo: `status_postgresql_migracion_ubuntu24_2026-04-15_19-48-01_-0300.md`

## Update 2026-04-22

- Se analizo y valido en produccion la operativa de `followup/config`, `followup/evaluate`, `reset_runtime_phone` y `reset_runtime_all` del demo `vertice360-orquestador`.
- Se confirmo que `reset_runtime_all` limpia runtime conversacional y `visit_followup_cycle`, pero no toca `visit_followup_config`.
- Config productiva validada durante la prueba:
  - `cliente=prod-celulares-check-20260324`
  - `advisor_phone=+5491130946950`
  - `supervisor_phone=+59168912007`
  - `first_delay_seconds=10`
  - `second_delay_seconds=15`
- Se detecto y corrigio en local una confusion semantica: el backend marcaba `provider_status="sent"` cuando Gupshup solo devolvia ACK. Ahora el flujo expone `provider_status="submitted"` cuando el request fue aceptado por el provider pero no hay confirmacion de entrega final.
- Se agrego tambien `target_matches_lead` en la respuesta/eventos de follow-up para distinguir cuando el destino interno coincide con el numero del lead.
- Archivo local modificado y copiado al server productivo antes de reiniciar:
  - `modules/vertice360_orquestador_demo/services.py`
- Backup remoto creado en produccion:
  - `services.py.bak-20260422-followup-status`
- Validacion end-to-end realizada en produccion post-restart:
  - ticket nuevo `7c8ec3f1-430b-4fb4-8796-382e6b48751c`
  - `level1` enviado al advisor `+5491130946950`
  - `level2` enviado al supervisor `+59168912007`
  - ambos con `provider_status="submitted"`
  - `level1` con `target_matches_lead=false`
  - `level2` con `target_matches_lead=true`
- Se actualizo el runbook:
  - `docs/demo_operativa_vertice360.md`
  - ahora refleja la config productiva real, la semantica de `submitted`, y el caso operativo con solo 2 telefonos.
- Decision de producto/operacion pendiente para retomar:
  - es factible armar una pagina/backstage browser para la demo que permita elegir `cliente`, limpiar runtime, setear `advisor/supervisor` y ejecutar `evaluate`
  - recomendacion: hacerla como pagina operativa separada de la demo publica, no embebida en el recorrido principal
  - principal riesgo operativo: exponer el `x-v360-admin-token` en frontend y facilitar resets/configuraciones equivocadas durante demos en vivo
  - recomendacion actual: avanzar con una consola de backstage con guardrails, no con un boton simple en la UI publica
