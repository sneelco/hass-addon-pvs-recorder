#!/usr/bin/with-contenv bashio


export MQTT_HOST=$(bashio::config 'mqtt_host' $(bashio::services mqtt "host" " "))
export MQTT_PORT=$(bashio::config 'mqtt_port' $(bashio::services mqtt "port" " "))
export MQTT_USER=$(bashio::config 'mqtt_username' $(bashio::services mqtt "username" " "))
export MQTT_PASSWORD=$(bashio::config 'mqtt_password' $(bashio::services mqtt "password" " "))
export MQTT_TOPIC=$(bashio::config 'mqtt_topic')

export PVS_HOST=$(bashio::config 'pvs_host')
export PVS_PORT=$(bashio::config 'pvs_port')
export PVS_USER=$(bashio::config 'pvs_user')
export PVS_PASSWORD=$(bashio::config 'pvs_password')
export PVS_POLL_INTERVAL=$(bashio::config 'pvs_poll_interval')

if bashio::var.is_empty "$PVS_PASSWORD"; then
  bashio::exit.nok "pvs_password must be set in the add-on configuration"
fi

export ESS_HOST=$(bashio::config 'ess_host')
export ESS_PORT=$(bashio::config 'ess_port')
export ESS_PORT_503=$(bashio::config 'ess_port_503')
export ESS_DEVICES=$(bashio::config 'ess_devices')


# Transform newline-separated JSON objects into a JSON array and save to file
echo "[$(echo "$ESS_DEVICES" | sed '/^\s*$/d' | paste -sd, -)]" > /data/ess_devices.json

uv run pvs_recorder.py --ess-device-file /data/ess_devices.json
