#!/usr/bin/env bash
# Fuerza la temperatura del publicador a 38.5 °C durante 5 minutos (dispara la alerta).
# Uso: ./scripts/forzar_alerta.sh [valor] [segundos]
VAL=${1:-38.5}; DUR=${2:-300}
docker exec lab5-publisher sh -c "echo '{\"temperature\": $VAL, \"duration_s\": $DUR}' > /state/override.json"
echo "Temperatura forzada a $VAL °C por $DUR s. Mira: docker logs -f lab5-publisher"
