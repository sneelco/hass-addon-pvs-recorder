# PVS Recorder

A Python application that connects to SunPower PVS (Photovoltaic System) WebSocket interfaces and publishes real-time solar power data to MQTT brokers. This tool enables integration of SunPower solar monitoring data into home automation systems, data logging platforms, and other IoT applications.

## Overview

PVS Recorder establishes a WebSocket connection to a SunPower PVS system and continuously monitors power generation data. It processes the incoming data and publishes key metrics to an MQTT broker, making the solar system data available for integration with platforms like Home Assistant, Grafana, or custom monitoring solutions.

**Important Network Setup**: The SunPower PVS system typically resides on a separate internal network (often using IP addresses like `172.27.153.1`). To access this system from your main network, you'll need to set up a proxy that bridges both networks. See the [Network Configuration](#network-configuration) section for details.

## Features

- **Real-time Data Collection**: Connects to SunPower PVS WebSocket interface for live power data
- **MQTT Integration**: Publishes solar power metrics to MQTT topics for easy integration
- **Auto-reconnection**: Automatically reconnects if the WebSocket connection is lost
- **Configurable**: Supports both command-line arguments and environment variables
- **Docker Support**: Containerized for easy deployment
- **Home Assistant Add-on**: Ready-to-use Home Assistant add-on configuration

## Data Published

The application publishes the following metrics to MQTT topics:

- `site_load_p`: Site load power (kW)
- `net_p`: Net power (kW) - positive for consumption, negative for export
- `pv_p`: PV power generation (kW)
- `site_load_en`: Site load energy (kWh)
- `net_en`: Net energy (kWh)
- `pv_en`: PV energy generation (kWh)

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
   uv run pvs_recorder.py --pvs-host <pvs-ip> --mqtt-host <mqtt-broker-ip>
   ```
   
   **Note**: If your PVS is on a separate network, use the proxy's IP address instead of the direct PVS IP.

### Docker Installation

1. Build the Docker image:
   ```bash
   docker build -t pvs_recorder .
   ```

2. Run the container:
   ```bash
   docker run -e PVS_HOST=<pvs-ip> -e MQTT_HOST=<mqtt-broker-ip> pvs_recorder
   ```
   
   **Note**: If your PVS is on a separate network, use the proxy's IP address instead of the direct PVS IP.

## Configuration

### Command Line Options

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `--pvs-host` | PVS system IP address | `172.27.153.1` | `PVS_HOST` |
| `--pvs-ws-port` | PVS WebSocket port | `9002` | `PVS_WS_PORT` |
| `--pvs-ws-secure` | Use secure WebSocket (WSS) | `False` | `PVS_WS_SECURE` |
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
- Forward WebSocket connections from your LAN to the PVS system
- Handle the WebSocket upgrade protocol correctly

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
   - **WebSocket**: `http://<proxy-ip>:9002` (forwards to PVS WebSocket)
   - **HTTP**: `http://<proxy-ip>:9080` (forwards to PVS HTTP interface)
   - **Modbus**: `tcp://<proxy-ip>:9502` (forwards to PVS Modbus)

#### Proxy Configuration

The included nginx configuration (`pvs_proxy/nginx/nginx.conf`) forwards:
- Port 9002 → PVS WebSocket (172.27.153.1:9002)
- Port 9080 → PVS HTTP (172.27.153.1:80)
- Port 9502 → PVS Modbus (172.27.153.1:502)

**Important**: Update the `proxy_pass` directives in the nginx configuration to match your PVS system's actual IP address.

#### Using the Proxy

Once the proxy is running, use the proxy's IP address instead of the direct PVS IP:

```bash
uv run pvs_recorder.py --pvs-host <proxy-ip> --mqtt-host <mqtt-broker-ip>
```

### Custom Proxy Setup

If you prefer to use a different proxy solution:

1. Ensure your proxy forwards WebSocket connections correctly
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

### Using Secure WebSocket
```bash
uv run pvs_recorder.py \
  --pvs-host 192.168.1.50 \
  --pvs-ws-secure \
  --mqtt-host 192.168.1.10
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
pvs_ws_port: 9002
pvs_ws_secure: false
```

*Note: Use the proxy IP address in `pvs_host` if your PVS is on a separate network.*

## Data Format

The application processes JSON messages from the PVS WebSocket interface. Example power notification:

```json
{
  "notification": "power",
  "params": {
    "time": 1753730396,
    "site_load_p": 2.1732543945312505,
    "net_p": -4.3857470703125,
    "pv_p": 6.5590014648437509,
    "site_load_en": 39676.479999999996,
    "net_en": 6473.23,
    "pv_en": 33203.25
  }
}
```

## Architecture

The application consists of three main components:

1. **PVS WebSocket Client** (`pvs/pvs_websocket.py`): Handles connection to the SunPower PVS system
2. **MQTT Client** (`mqtt/__init__.py`): Manages MQTT broker communication
3. **Recorder** (`recorder/__init__.py`): Orchestrates data flow between PVS and MQTT

## Development

### Dependencies

- `websockets`: WebSocket client for PVS communication
- `paho-mqtt`: MQTT client for broker communication
- `httpx`: HTTP client for additional API calls
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
2. Check that the WebSocket port (default: 9002) is open
3. Ensure your network allows WebSocket connections
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
