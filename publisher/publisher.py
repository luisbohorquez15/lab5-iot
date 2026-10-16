"""
Publicador MQTT del Lab 5.

Simula un sensor ambiental en Bucaramanga y publica cada INTERVAL_S segundos:
  temperature (°C), humidity (%RH), illuminance (lux)
en el tópico  lab5/<DEVICE_ID>/telemetry  con QoS 1, en JSON.

Los valores siguen un ciclo día/noche (hora local America/Bogota) + ruido,
para que el dashboard de 4 días muestre una curva realista.

Forzar la alerta: si existe OVERRIDE_FILE con, por ejemplo,
  {"temperature": 38.5, "duration_s": 300}
ese valor reemplaza al simulado durante duration_s segundos.
"""
import json
import math
import os
import random
import signal
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt

HOST = os.getenv("MQTT_HOST", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
DEVICE = os.getenv("DEVICE_ID", "sensor-01")
INTERVAL = float(os.getenv("INTERVAL_S", "10"))
OVERRIDE_FILE = os.getenv("OVERRIDE_FILE", "/state/override.json")
TOPIC = f"lab5/{DEVICE}/telemetry"

override = {}          # valores forzados activos
override_until = 0.0   # epoch hasta cuando aplican


def log(msg):
    print(f"{datetime.now().isoformat(timespec='seconds')} {msg}", flush=True)


def simulate(now):
    """Valores con ciclo diario. Pico de calor ~14:00, mínimo ~05:00."""
    lt = time.localtime(now)
    hour = lt.tm_hour + lt.tm_min / 60
    day_phase = math.sin((hour - 8) / 24 * 2 * math.pi)        # +1 a las 14h, -1 a las 02h

    temperature = 24 + 4 * day_phase + random.gauss(0, 0.3)    # ~20-28 °C
    humidity = 72 - 12 * day_phase + random.gauss(0, 1.0)      # inversa a la temperatura
    humidity = max(0, min(100, humidity))

    # luz solo entre 06:00 y 18:00, máximo al mediodía
    if 6 <= hour <= 18:
        sun = math.sin((hour - 6) / 12 * math.pi)
        illuminance = 30000 * sun * random.uniform(0.7, 1.0)    # nubes
    else:
        illuminance = random.uniform(0, 5)                     # alumbrado / ruido
    return round(temperature, 2), round(humidity, 2), round(illuminance, 1)


def check_override(now):
    global override, override_until
    if os.path.exists(OVERRIDE_FILE):
        try:
            with open(OVERRIDE_FILE) as f:
                data = json.load(f)
            duration = float(data.pop("duration_s", 300))
            override = {k: float(v) for k, v in data.items()
                        if k in ("temperature", "humidity", "illuminance")}
            override_until = now + duration
            log(f"OVERRIDE activado {override} por {duration:.0f}s")
        except Exception as e:  # archivo mal escrito: se ignora
            log(f"override inválido: {e}")
        finally:
            os.remove(OVERRIDE_FILE)
    if override and now > override_until:
        log("OVERRIDE terminado, vuelve la simulación")
        override = {}


def on_connect(client, userdata, flags, reason_code, properties):
    log(f"conectado a {HOST}:{PORT} ({reason_code})")


def on_disconnect(client, userdata, flags, reason_code, properties):
    log(f"desconectado ({reason_code}); paho reintenta solo")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"pub-{DEVICE}")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    while True:  # el broker puede tardar en arrancar
        try:
            client.connect(HOST, PORT, keepalive=60)
            break
        except OSError as e:
            log(f"broker no disponible ({e}), reintento en 3s")
            time.sleep(3)
    client.loop_start()

    def stop(*_):
        log("deteniendo publicador")
        client.loop_stop()
        client.disconnect()
        sys.exit(0)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    log(f"publicando en '{TOPIC}' cada {INTERVAL}s")
    while True:
        now = time.time()
        check_override(now)
        t, h, l = simulate(now)
        payload = {
            "device": DEVICE,
            "ts": int(now * 1000),              # marca de tiempo real (ms)
            "temperature": override.get("temperature", t),
            "humidity": override.get("humidity", h),
            "illuminance": override.get("illuminance", l),
        }
        info = client.publish(TOPIC, json.dumps(payload), qos=1)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            log(f"error publicando rc={info.rc}")
        elif override:
            log(f"[FORZADO] {payload}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
