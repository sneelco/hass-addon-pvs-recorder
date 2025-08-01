#!/usr/bin/with-contenv bashio


export MQTT_HOST=$(bashio::config 'mqtt_host' $(bashio::services mqtt "host" " "))
export MQTT_PORT=$(bashio::config 'mqtt_port' $(bashio::services mqtt "port" " "))
export MQTT_USER=$(bashio::config 'mqtt_username' $(bashio::services mqtt "username" " "))
export MQTT_PASSWORD=$(bashio::config 'mqtt_password' $(bashio::services mqtt "password" " "))
export MQTT_TOPIC=$(bashio::config 'mqtt_topic')

export PVS_HOST=$(bashio::config 'pvs_host')
export PVS_WS_PORT=$(bashio::config 'pvs_ws_port')
export PVS_WS_SECURE=$(bashio::config 'pvs_ws_secure')

export ESS_HOST=$(bashio::config 'ess_host')
export ESS_PORT=$(bashio::config 'ess_port')
export ESS_PORT_503=$(bashio::config 'ess_port_503')
export ESS_DEVICES=$(bashio::config 'ess_devices')

echo "ESS_DEVICES: $ESS_DEVICES"

pwd

echo "$ESS_DEVICES" > ess_devices.json

exit 0

if [ "$PVS_WS_SECURE" == "true" ]; then
  uv run pvs_recorder.py --pvs-ws-secure
else
  uv run pvs_recorder.py
fi
