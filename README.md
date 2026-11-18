# PVS Recorder

A Python application that polls a SunPower PVS (Photovoltaic System) and publishes real-time solar, battery and per-panel data to MQTT brokers. This tool enables integration of SunPower solar monitoring data into home automation systems, data logging platforms, and other IoT applications.

## Overview

PVS Recorder logs in to a SunPower PVS system's authenticated HTTPS interface and polls its `/vars` endpoint on a fixed interval. It processes the returned data and publishes key metrics to an MQTT broker, making the solar system data available for integration with platforms like Home Assistant, Grafana, or custom monitoring solutions.

**Important Network Setup**: The SunPower PVS system typically resides on a separate internal network (often using IP addresses like `172.27.153.1`). To access this system from your main network, you'll need to set up a proxy that bridges both networks. See the [Network Configuration](#network-configuration) section for details.

## Features

- **Real-time Data Collection**: Polls the authenticated PVS `/vars` endpoint (default every 10 seconds)
- **Per-device Data**: Publishes per-panel microinverter, meter, transfer switch and battery data
- **MQTT Integration**: Publishes solar power metrics to MQTT topics for easy integration
- **Automatic Re-authentication**: Logs in again automatically when the PVS session expires
- **Configurable**: Supports both command-line arguments and environment variables
- **Docker Support**: Containerized for easy deployment
- **Home Assistant Add-on**: Ready-to-use Home Assistant add-on configuration

## Data Published

All topics are relative to the configured MQTT topic prefix (default `pvs`).

### Live data (`/sys/livedata/*`)

Published to the same top-level topics the old WebSocket integration used:

- `site_load_p`: Site load power (kW)
- `net_p`: Net power (kW) - positive for consumption, negative for export
- `pv_p`: PV power generation (kW)
- `site_load_en`: Site load energy (kWh)
- `net_en`: Net energy (kWh)
- `pv_en`: PV energy generation (kWh)
- `ess_p`, `ess_en`, `soc`, `backupTimeRemaining`, `midstate`, `time`: Battery / system values when present

### Devices (`/sys/devices/<type>/<index>/<field>`)

Published to `devices/<type>/<serial>/<field>`, e.g.
`pvs/devices/inverter/E00122238011832/pMppt1Kw`. Device types include `inverter` (one per
panel), `meter`, `transfer_switch` and `ess`. The device serial number is used so topics stay
stable even if the PVS reorders devices.

### System info

`info/serialnum`, `info/model`, `info/hwrev`, `info/sw_rev`, `info/uptime`, `info/sys_type`,
`info/ram_usage`, `info/flash_usage`, `info/cpu_usage`, `ess_config/control_mode` and
`ess_config/min_customer_soc`. Other values (notably the PVS Wi-Fi SSID and WPA key) are
intentionally not published.

## Installation

### Prerequisites

- Python 3.12 or higher
- Access to a SunPower PVS system
- MQTT broker (optional, for data publishing)
- Network access to the PVS system (see [Network Configuration](#network-configuration))

### Local Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd pvs_recorder
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

3. Run the application:
   ```bash
   PVS_PASSWORD=<pvs-password> uv run pvs_recorder.py --pvs-host <pvs-ip> --mqtt-host <mqtt-broker-ip>
   ```
   
   **Note**: If your PVS is on a separate network, use the proxy's IP address instead of the direct PVS IP.

### Docker Installation

1. Build the Docker image:
   ```bash
   docker build -t pvs_recorder .
   ```

2. Run the container:
   ```bash
   docker run -e PVS_HOST=<pvs-ip> -e PVS_PASSWORD=<pvs-password> -e MQTT_HOST=<mqtt-broker-ip> pvs_recorder
   ```
   
   **Note**: If your PVS is on a separate network, use the proxy's IP address instead of the direct PVS IP.

## Configuration

### Command Line Options

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `--pvs-host` | PVS system IP address | `172.27.153.1` | `PVS_HOST` |
| `--pvs-port` | PVS HTTPS port | `443` | `PVS_PORT` |
| `--pvs-user` | PVS username | `ssm_owner` | `PVS_USER` |
| `--pvs-password` | PVS password (required; prefer the env var) | `None` | `PVS_PASSWORD` |
| `--pvs-poll-interval` | Seconds between polls of the PVS | `10` | `PVS_POLL_INTERVAL` |
| `--mqtt-host` | MQTT broker hostname | `None` | `MQTT_HOST` |
| `--mqtt-port` | MQTT broker port | `1883` | `MQTT_PORT` |
| `--mqtt-topic` | MQTT topic prefix | `pvs` | `MQTT_TOPIC` |
| `--mqtt-user` | MQTT username | `frigate` | `MQTT_USER` |
| `--mqtt-password` | MQTT password | `frigate` | `MQTT_PASSWORD` |
| `--debug` | Enable debug logging | `False` | N/A |

### Environment Variables

All configuration options can be set via environment variables. See the table above for the mapping between command-line options and environment variables.

## Network Configuration

SunPower PVS systems typically operate on a separate internal network (often using IP addresses in the `172.27.x.x` range). To access the PVS from your main network, you'll need to set up a proxy that bridges both networks.

### Proxy Requirements

The proxy must:
- Reside on both the PVS internal network and your primary LAN
- Forward HTTPS (TCP port 443) connections from your LAN to the PVS system

### Included Proxy Example

This project includes a ready-to-use nginx proxy configuration in the `pvs_proxy/` directory.

#### Setting Up the Proxy

1. Navigate to the proxy directory:
   ```bash
   cd pvs_proxy
   ```

2. Start the proxy using Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. The proxy will be available on:
   - **HTTPS**: `tcp://<proxy-ip>:5443` (forwards to PVS HTTPS, used for polling)
   - **HTTP**: `http://<proxy-ip>:9080` (forwards to PVS HTTP interface)
   - **Modbus**: `tcp://<proxy-ip>:5502` / `5503` (forwards to ESS Modbus)

#### Proxy Configuration

The included nginx configuration (`pvs_proxy/nginx/nginx.conf`) forwards:
- Port 5443 → PVS HTTPS (172.27.153.1:443)
- Port 9080 → PVS HTTP (172.27.153.1:80)
- Port 5502 → ESS Modbus (172.27.153.171:502)
- Port 5503 → ESS Modbus (172.27.153.171:503)

**Important**: Update the `proxy_pass` directives in the nginx configuration to match your PVS system's actual IP address.

#### Using the Proxy

Once the proxy is running, use the proxy's IP address instead of the direct PVS IP:

```bash
uv run pvs_recorder.py --pvs-host <proxy-ip> --pvs-port 5443 --mqtt-host <mqtt-broker-ip>
```

### Custom Proxy Setup

If you prefer to use a different proxy solution:

1. Ensure your proxy forwards HTTPS (TCP 443) connections to the PVS
2. Configure it to proxy to your PVS system's IP address
3. Use the proxy's IP address in the `--pvs-host` parameter

## Usage Examples

### Basic Usage (Direct Connection)
```bash
uv run pvs_recorder.py --pvs-host 192.168.1.100 --mqtt-host 192.168.1.10
```

### Basic Usage (Via Proxy)
```bash
uv run pvs_recorder.py --pvs-host 192.168.1.50 --mqtt-host 192.168.1.10
```
*Note: `192.168.1.50` is the proxy IP address, not the direct PVS IP*

### With Custom MQTT Configuration
```bash
uv run pvs_recorder.py \
  --pvs-host 192.168.1.50 \
  --mqtt-host 192.168.1.10 \
  --mqtt-topic solar \
  --mqtt-user myuser \
  --mqtt-password mypassword
```

### Custom Poll Interval
```bash
PVS_PASSWORD=<pvs-password> uv run pvs_recorder.py \
  --pvs-host 192.168.1.50 \
  --pvs-port 5443 \
  --pvs-poll-interval 30 \
  --mqtt-host 192.168.1.10
```

### One-off Query
`query_pvs_vars.py` logs in, fetches the vars once and prints them as JSON:
```bash
PVS_PASSWORD=<pvs-password> uv run query_pvs_vars.py --pvs-host 172.27.153.1
```

## Home Assistant Integration

This project includes Home Assistant add-on support. The add-on automatically discovers and uses the Home Assistant MQTT broker service.

### Add-on Configuration

```yaml
mqtt_host: "192.168.1.10"
mqtt_port: 1883
mqtt_username: "your_username"
mqtt_password: "your_password"
mqtt_topic: "solar"
pvs_host: "192.168.1.50"  # Proxy IP address
pvs_port: 5443            # 443 when talking to the PVS directly
pvs_user: ssm_owner
pvs_password: "your_pvs_password"
pvs_poll_interval: 10     # seconds
```

*Note: Use the proxy IP address in `pvs_host` if your PVS is on a separate network.*

## Data Format

The recorder first obtains a session by calling `https://<pvs>/auth?login` with HTTP basic
auth, then polls `https://<pvs>/vars?match=/` with the returned session cookie. The PVS uses a
self-signed certificate, so certificate verification is disabled. Example response:

```json
{
  "values": [
    { "name": "/sys/livedata/pv_p", "value": "5.560955" },
    { "name": "/sys/livedata/net_p", "value": "-0.496185" },
    { "name": "/sys/devices/inverter/0/sn", "value": "E00122238011832" },
    { "name": "/sys/devices/inverter/0/pMppt1Kw", "value": "0.293450" }
  ],
  "count": 4
}
```

## Architecture

The application consists of three main components:

1. **PVS Vars Client** (`pvs/pvs_vars.py`): Authenticates to and polls the SunPower PVS system
2. **MQTT Client** (`mqtt/__init__.py`): Manages MQTT broker communication
3. **Recorder** (`recorder/__init__.py`): Orchestrates data flow between PVS and MQTT

## Development

### Dependencies

- `paho-mqtt`: MQTT client for broker communication
- `httpx`: HTTPS client for polling the PVS
- `pydantic`: Data validation and settings management

### Code Quality

The project uses:
- **Ruff**: For linting and code formatting
- **MyPy**: For static type checking
- **UV**: For dependency management

### Running Tests

```bash
uv run ruff check .
uv run mypy .
```

## Troubleshooting

### Connection Issues

1. Verify the PVS host is accessible from your network
2. Check that the HTTPS port (default: 443, or 5443 via the included proxy) is reachable
3. If you see authentication errors, verify `pvs_user`/`pvs_password` (the same credentials work with the `curl https://<pvs>/auth?login` check)
4. If using a proxy, verify the proxy is running and accessible
5. Check that the proxy is correctly forwarding to the PVS system
6. Verify the proxy IP address is being used in the `--pvs-host` parameter

### MQTT Issues

1. Verify MQTT broker is running and accessible
2. Check username/password credentials
3. Ensure the MQTT topic is properly configured

### Debug Mode

Enable debug logging to see detailed connection and data processing information:

```bash
uv run pvs_recorder.py --debug --pvs-host <host> --mqtt-host <host>
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]
