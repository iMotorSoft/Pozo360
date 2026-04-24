# Status PostgreSQL Migracion Ubuntu 24.04

Fecha y hora: `2026-04-15 19:48:01 -0300`

## Objetivo

Dejar documentado el estado de la migracion operativa de PostgreSQL local sobre Ubuntu `24.04`, manteniendo el modelo de uso anterior:

- contenedor Docker local
- uso normal con `docker compose`
- volumen Docker nombrado para persistencia
- datos fuera de `home`

## Decision tomada

Para PostgreSQL se decidio:

- no usar bind mount a un directorio del proyecto
- seguir con volumen Docker nombrado
- mover el `data-root` global de Docker a la particion `DEVELOP`

Razon:

- replica el flujo anterior que ya funcionaba bien
- evita usar `home` para la persistencia
- evita mezclar archivos internos de PostgreSQL dentro del repo/lab

## Estado actual confirmado

### Sistema base

- Ubuntu: `24.04.4 LTS`
- particion `DEVELOP` montada persistentemente en:
  - `/media/issajar/DEVELOP`

### Docker instalado

Quedo instalado Docker Community oficial:

- `docker-ce 29.4.0`
- `docker-ce-cli 29.4.0`
- `containerd.io 2.2.3`
- `docker-buildx-plugin 0.33.0`
- `docker-compose-plugin 5.1.3`

### Data root de Docker

Docker quedo reconfigurado para usar:

- `/media/issajar/DEVELOP/docker-data`

Validacion realizada:

- `DockerRootDir=/media/issajar/DEVELOP/docker-data`

Implicancia:

- los volumenes Docker nombrados nuevos, incluyendo el de PostgreSQL, quedaran fisicamente en `DEVELOP`

### Acceso sin sudo

El usuario `issajar` fue agregado al grupo:

- `docker`

Nota:

- para que esto impacte en terminales ya abiertas, hace falta reingresar sesion o ejecutar `newgrp docker`

### Red externa requerida por compose

Se creo la red externa:

- `dev_network`

## Laboratorio PostgreSQL

Directorio activo identificado:

- `/media/issajar/DEVELOP/Projects/iMotorSoft/ai/lab/postgres`

Archivo compose alineado:

- `docker-compose.yml`

Estado final del compose:

- imagen: `postgres:18.1-alpine3.22`
- contenedor: `imotorsoft-postgres`
- usuario: `administrator`
- puerto publicado: `5432`
- volumen nombrado: `pgdata`
- red externa: `dev_network`

## Ajuste importante aplicado

El compose estaba creando por defecto:

- `POSTGRES_DB=imotor_ai`

Pero la configuracion real del backend y la operativa documentada usan consistentemente:

- base `v360`

Por eso se alineo el compose a:

- `POSTGRES_DB=v360`

Esto evita desfasaje entre:

- `docker-compose.yml`
- `DB_PG_V360_URL`
- `v360.dump`
- documentacion operativa del backend

## Variables de entorno restauradas

Se actualizo el `~/.bashrc` actual con un bloque minimo para PostgreSQL / Vertice360:

- `DB_PG_IP=localhost`
- `DB_PG_PORT=5432`
- `DB_PG_USER=administrator`
- `DB_PG_PASS=TodaRaba`
- `DB_PG_V360_URL=postgresql+psycopg://administrator:TodaRaba@localhost:5432/v360`

Se decidio no restaurar el `.bashrc` historico completo porque contenia arrastre y muchos secretos heredados.

## Backend Vertice360

Se confirmo que el backend usa PostgreSQL por URL TCP con `psycopg`, no via `docker exec`.

Puntos verificados:

- `globalVar.py` exige `DB_PG_V360_URL`
- la URL debe apuntar a la base `v360`
- `modules/vertice360_orquestador_demo/db.py` usa `psycopg` / `psycopg_pool`

## Backups y restauracion

Material identificado:

- dump principal:
  - `/media/issajar/DEVELOP/Projects/iMotorSoft/ai/lab/postgres/v360.dump`
- tipo confirmado:
  - `PostgreSQL custom database dump`

Observacion importante:

- en este laboratorio, la persistencia real no estaba en el directorio del proyecto sino en volumen Docker nombrado
- por eso el activo critico para restaurar contenido es `v360.dump`

## Nota adicional: Milvus

Aunque este status esta centrado en PostgreSQL, durante la misma sesion se reviso el laboratorio:

- `/media/issajar/DEVELOP/Projects/iMotorSoft/ai/lab/milvus`

Hallazgos confirmados:

- Milvus usa bind mount local, no volumen Docker nombrado
- la persistencia principal esta en:
  - `/media/issajar/DEVELOP/Projects/iMotorSoft/ai/lab/milvus/volumes/milvus`
- el directorio persistido no esta vacio:
  - `./volumes` pesa aproximadamente `579M`
- la instancia levantada reconocio al menos una coleccion existente:
  - `JAI_document_embeddings`
- metricas internas de Milvus reportaron:
  - `collection_num = 1`
  - `stored_rows_num = 3231`

Conclusion provisional sobre Milvus:

- no parece requerir restauracion inmediata por falta de datos
- los datos previos estan montados y visibles
- pero se observaron errores de pipeline / channel recovery en logs (`failed to unmarshal message header`, `InitPipelineFailed`)

Pendiente especifico de Milvus:

- validar funcionalmente la coleccion recuperada antes de decidir limpieza o restauracion
- el siguiente paso correcto es listar colecciones, describir `JAI_document_embeddings` y probar una consulta / search minima

## Pendientes

Al momento de este status todavia no se hizo:

- levantar el contenedor PostgreSQL en esta maquina nueva
- restaurar `v360.dump` dentro de la base `v360`
- validar conexion real desde el backend contra el contenedor ya corriendo

## Comando previsto para arranque

Cuando se necesite levantar PostgreSQL:

```bash
cd /media/issajar/DEVELOP/Projects/iMotorSoft/ai/lab/postgres
docker compose up -d
```

## Comando previsto para restauracion

Cuando el contenedor ya este arriba:

```bash
docker exec -i imotorsoft-postgres sh -lc 'PGPASSWORD="TodaRaba" pg_restore -U administrator -d v360 --clean --if-exists --no-owner --no-privileges' < /media/issajar/DEVELOP/Projects/iMotorSoft/ai/lab/postgres/v360.dump
```

## Criterio de cierre

La migracion local de PostgreSQL a Ubuntu `24.04` quedara efectivamente cerrada cuando:

- `docker compose up -d` levante `imotorsoft-postgres`
- `v360.dump` quede restaurado en `v360`
- el backend conecte correctamente usando `DB_PG_V360_URL`
- se confirme uso sin `sudo` desde una sesion nueva del usuario
