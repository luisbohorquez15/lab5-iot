# Lab 5 · Plataforma propia — MQTT → Telegraf → InfluxDB → Grafana

Sensor ambiental simulado (temperature, humidity, illuminance) que publica por **MQTT 3.1.1, QoS 1**
a Mosquitto; Telegraf lo escribe en **InfluxDB 2.7**; **Grafana OSS** lee la TSDB, muestra la toma de 4 días
y dispara una alerta de umbral por webhook.

```
publisher ──MQTT QoS1──> mosquitto ──> telegraf ──HTTP──> influxdb <──Flux── grafana ──webhook──> alert-sink (log)
 lab5/sensor-01/telemetry          (suscriptor)        bucket lab5                 alerta T > 32 °C
```

## Requisitos de la VM
- Ubuntu Server 22.04/24.04, 2 vCPU, 2–4 GB RAM, 20 GB disco.
- Docker Engine + plugin Compose (`docker compose version`).
- Puertos: 1883 (MQTT), 8086 (InfluxDB), 3000 (Grafana).

## Levantar
```bash
cp .env.example .env
nano .env                      # cambia claves; INFLUX_TOKEN = salida de: openssl rand -hex 32
docker compose up -d --build
docker compose ps              # todo "running"/"healthy"
```
- Grafana: `http://<IP-VM>:3000` (usuario/clave del `.env`). Dashboard en carpeta **Lab 5**.
- InfluxDB UI: `http://<IP-VM>:8086`.

## Verificar cada eslabón
```bash
docker logs -f lab5-publisher                                     # publica cada 10 s
docker exec lab5-mosquitto mosquitto_sub -t 'lab5/#' -v -C 3      # el broker recibe
docker logs lab5-telegraf | tail                                  # sin errores de escritura
./scripts/consulta_influx.sh                                      # puntos en la TSDB
```

## Disparar la alerta
```bash
./scripts/forzar_alerta.sh 38.5 300     # 38.5 °C durante 5 min
docker logs -f lab5-alert-sink          # aparece ALERTA firing (~2-3 min)
```
Regla: promedio de temperatura en 2 min **> 32 °C**, evaluada cada 30 s, sostenida 1 min (`for: 1m`).
Acción: webhook → `alert-sink` → `/logs/alerts.log`. Al terminar el forzado llega el `resolved`.

## Evidencias (`/evidencias`)
- `consulta.txt` → `./scripts/consulta_influx.sh > evidencias/consulta.txt`
- `huecos.txt` → `./scripts/huecos.sh > evidencias/huecos.txt`
- `dashboard-4dias.png`, `alerta-firing.png` (Alerting → Alert rules), `alert-sink.log` (`docker logs lab5-alert-sink > evidencias/alert-sink.log`)

## Notas
- Versión de Grafana usada: 13.0.2 (fijada en docker-compose.yml)
- Todas las imágenes tienen variante ARM64 → mismo compose en la Raspberry Pi.
- No reiniciar con `docker compose down -v`: `-v` borra los volúmenes y **la toma de 4 días**.
- `.env` no se sube al repo (está en `.gitignore`).
