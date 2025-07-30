#!/usr/bin/with-contenv bashio


export MQTT_HOST=$(bashio::config 'mqtt_host' $(bashio::services mqtt "host" " "))
export MQTT_PORT=$(bashio::config 'mqtt_port' $(bashio::services mqtt "port" " "))
export MQTT_USER=$(bashio::config 'mqtt_username' $(bashio::services mqtt "username" " "))
export MQTT_PASSWORD=$(bashio::config 'mqtt_password' $(bashio::services mqtt "password" " "))
export MQTT_TOPIC=$(bashio::config 'mqtt_topic')

export PVS_HOST=$(bashio::config 'pvs_host')
export PVS_WS_PORT=$(bashio::config 'pvs_ws_port')
export PVS_WS_SECURE=$(bashio::config 'pvs_ws_secure')

if [ "$PVS_WS_SECURE" == "true" ]; then
  uv run pvs_recorder.py --pvs-ws-secure
else
  uv run pvs_recorder.py
fi
