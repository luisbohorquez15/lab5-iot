#!/usr/bin/env bash
# Evidencia de la TSDB: últimos puntos y conteo de la toma.
set -a; source .env; set +a
echo "== Últimos 5 puntos de temperatura =="
docker exec lab5-influxdb influx query --org "$INFLUX_ORG" --token "$INFLUX_TOKEN" \
 'from(bucket:"lab5") |> range(start:-10m) |> filter(fn:(r)=>r._field=="temperature") |> tail(n:5) |> keep(columns:["_time","_field","_value","device"])'
echo "== Puntos por variable desde el inicio de la toma (últimos 5 días) =="
docker exec lab5-influxdb influx query --org "$INFLUX_ORG" --token "$INFLUX_TOKEN" \
 'from(bucket:"lab5") |> range(start:-5d) |> filter(fn:(r)=>r._measurement=="environment") |> count() |> keep(columns:["_field","_value"])'
echo "== Primer punto (inicio de la toma) =="
docker exec lab5-influxdb influx query --org "$INFLUX_ORG" --token "$INFLUX_TOKEN" \
 'from(bucket:"lab5") |> range(start:-30d) |> filter(fn:(r)=>r._field=="temperature") |> first() |> keep(columns:["_time"])'
