#!/usr/bin/env bash
# Lista los huecos de la toma (más de 60 s sin datos). Úsalo para el informe.
set -a; source .env; set +a
docker exec lab5-influxdb influx query --org "$INFLUX_ORG" --token "$INFLUX_TOKEN" \
 'from(bucket:"lab5") |> range(start:-30d) |> filter(fn:(r)=>r._field=="temperature")
  |> elapsed(unit:1s) |> filter(fn:(r)=>r.elapsed > 60) |> keep(columns:["_time","elapsed"])'
