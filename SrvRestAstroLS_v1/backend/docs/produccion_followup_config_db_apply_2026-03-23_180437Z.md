# Aplicacion de `visit_followup_config` en produccion

Fecha UTC: 2026-03-23 18:04:37Z
Fecha local estimada: 2026-03-23 15:04:37 -03

## Objetivo
Registrar lo ejecutado para crear y validar el schema `visit_followup_config` en la base `v360` de produccion, sin tocar frontend, UI ni logica conversacional.

## Alcance
- Servidor remoto accedido por `ssh`
- PostgreSQL accedido dentro del contenedor Docker `imotorsoft-postgres`
- Base objetivo: `v360`
- SQL aplicado: `backend/db/visit_followup_config_schema.sql`

## Contexto previo
- En local ya existia `visit_followup_config` y funcionaban los endpoints demo de follow-up config.
- En produccion, antes del apply, el backend ya estaba desplegado pero inicialmente la tabla no existia en `v360`.

## Acceso remoto
Se uso acceso SSH al host:

```bash
ssh administrator@imotorsoft.com
```

Hostname remoto observado:

```text
vps-0bfd28fb
```

Docker directo como `administrator` fallo por permisos sobre el socket. Se uso `sudo docker`.

## Verificacion previa en produccion
Se valido acceso a `psql` dentro del contenedor:

```bash
sudo docker exec imotorsoft-postgres sh -lc   'psql -U administrator -d v360 -At -c "select current_database(), current_user;"'
```

Resultado:

```text
v360|administrator
```

Se verifico luego la ausencia de la tabla con una consulta directa a `public.visit_followup_config`.

Resultado observado:

```text
ERROR:  relation "public.visit_followup_config" does not exist
```

## Copia del SQL al remoto
Se copio el archivo puntual:

```bash
scp backend/db/visit_followup_config_schema.sql   administrator@imotorsoft.com:/tmp/visit_followup_config_schema.sql
```

## Apply ejecutado en produccion
Se aplico el SQL dentro del contenedor `imotorsoft-postgres` sobre DB `v360`:

```bash
sudo sh -lc   "docker exec -i imotorsoft-postgres sh -lc 'psql -U administrator -d v360 -v ON_ERROR_STOP=1 -f -' < /tmp/visit_followup_config_schema.sql"
```

Salida relevante del primer apply:

```text
CREATE TABLE
ALTER TABLE
...
DO
```

Durante el primer apply aparecieron notices de columnas ya existentes, lo que implica que la sentencia `create table if not exists` y los `alter table add column if not exists` operaron de forma segura.

## Validacion de idempotencia en produccion
Se corrio el mismo SQL una segunda vez:

```bash
sudo sh -lc   "docker exec -i imotorsoft-postgres sh -lc 'psql -U administrator -d v360 -v ON_ERROR_STOP=1 -f -' < /tmp/visit_followup_config_schema.sql"
```

Salida relevante del segundo apply:

```text
NOTICE:  relation "visit_followup_config" already exists, skipping
NOTICE:  column "cliente" of relation "visit_followup_config" already exists, skipping
...
DO
```

Conclusion:
- Apply idempotente confirmado en produccion

## Validacion final del schema en produccion
Existencia de tabla verificada por `information_schema.tables`.

Resultado:

```text
1
```

Row count:

```text
0
```

Columnas observadas:

```text
cliente|text|NO|
enabled|boolean|NO|true
advisor_phone|text|YES|
supervisor_phone|text|YES|
first_delay_seconds|integer|NO|
second_delay_seconds|integer|NO|
level1_template|text|YES|
level2_template|text|YES|
board_base_url|text|YES|
allow_manual_evaluate|boolean|NO|true
updated_at|timestamp with time zone|NO|now()
updated_by|text|YES|
```

Constraints observados:

```text
chk_visit_followup_config_first_delay_positive|c|CHECK ((first_delay_seconds > 0))
chk_visit_followup_config_second_delay_positive|c|CHECK ((second_delay_seconds > 0))
visit_followup_config_allow_manual_evaluate_not_null|n|NOT NULL allow_manual_evaluate
visit_followup_config_cliente_not_null|n|NOT NULL cliente
visit_followup_config_enabled_not_null|n|NOT NULL enabled
visit_followup_config_first_delay_seconds_not_null|n|NOT NULL first_delay_seconds
visit_followup_config_pkey|p|PRIMARY KEY (cliente)
visit_followup_config_second_delay_seconds_not_null|n|NOT NULL second_delay_seconds
visit_followup_config_updated_at_not_null|n|NOT NULL updated_at
```

Indice observado:

```text
visit_followup_config_pkey|CREATE UNIQUE INDEX visit_followup_config_pkey ON public.visit_followup_config USING btree (cliente)
```

## Verificacion del backend de produccion
Despues del update del servidor, se probo:

```bash
curl -i "https://demo.vertice360.imotorsoft.com/api/demo/vertice360-orquestador/followup/config/get?cliente=prod-followup-ssh-check"
curl -i "http://127.0.0.1:7062/api/demo/vertice360-orquestador/followup/config/get?cliente=prod-followup-ssh-check"
```

Respuesta observada en ambos casos:

```text
HTTP/1.1 403 Forbidden
{"status_code":403,"detail":"admin reset is only available in dev"}
```

## Conclusiones
- La tabla `visit_followup_config` quedo creada en produccion dentro de `v360`.
- El SQL puntual fue aplicado con exito.
- La aplicacion es idempotente.
- El backend de produccion ya expone la ruta, pero el acceso real en prod queda bloqueado por reutilizar la validacion `_validate_admin_reset_access()`, que exige `dev`.

## Estado final
- DB produccion: lista
- Schema `visit_followup_config`: aplicado
- Endpoints `followup/config/set` y `followup/config/get`: desplegados pero bloqueados en prod por guardia `dev-only`

## Pendiente recomendado
Ajustar seguridad de `followup/config/*` para:
- mantener `x-v360-admin-token`
- permitir uso en `prod`
- no depender de la restriccion `admin reset is only available in dev`

## Restricciones respetadas
- No se toco frontend
- No se toco UI
- No se toco logica conversacional
- No se hizo dump/restore completo de `v360`
- No se aplico migracion completa; solo SQL puntual
