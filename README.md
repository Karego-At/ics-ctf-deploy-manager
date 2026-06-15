# ICS CTF Infrastructure Manager

A Python framework for orchestrating Docker-based CTF (Capture The Flag) challenge environments. It builds and wires together Docker containers (components) on isolated Docker networks according to declarative YAML configuration files.

---

## Architecture Overview

```
infrastructure.yaml      challenge.yaml
        │                       │
        ▼                       ▼
InfrastructureConfig     ChallengeConfig
  (devices, components)    (setups, networks, peers)
        │                       │
        └──────────┬────────────┘
                   ▼
               Manager
            /          \
     BaseNetwork      BaseNetwork
      /    \            /    \
   Peer   Peer       Peer   Peer
(Container)(Container)...
```

- **`infrastructure.yaml`** defines the static inventory: physical devices and available Docker component images.
- **`challenge.yaml`** defines the runtime topology: which components to deploy, on which networks, with what settings.
- **`Manager`** reads both configs, creates Docker networks, builds and connects containers, then tears everything down on exit.

---

## Quick Start

### Native Run

```bash
pip install -r requirements.txt
python3 main.py
# Press Ctrl+C to shut down and clean up
```

### Docker

```bash
docker compose up --build
```

---

## Configuration Files

### Infrastructure Config

`config/infrastructure.yaml` — loaded once at startup. Defines physical devices and the catalogue of available Docker components.

```yaml
devices:
  - name: plc1
    type: PLC
    nw: "192.168.102.0/24"
    nic: "enx00e04c024b80"

components:
  - name: ctf-sensor
    type: simple
    path: ${components_path}/pnet-dev
    driver: pnet-driver

  - name: s7-ctf-hmi
    type: connectable
    path: ${components_path}/snap7-hmi
    port: 5000
    driver: hmi-driver
```

**Device fields:**

| Field | Description |
|-------|-------------|
| `name` | Logical name referenced in setups |
| `type` | `Device` or `PLC` |
| `nw` | Network address with prefix (e.g. `192.168.1.0/24`) |
| `nic` | Physical NIC identifier on the host machine |

**Component fields:**

| Field | Description |
|-------|-------------|
| `name` | Unique identifier referenced in peer configs |
| `type` | `simple` (no host port) or `connectable` (exposes a port) |
| `path` | Path to the directory containing the component's Dockerfile |
| `port` | *(connectable only)* Container port to expose |
| `driver` | Optional driver for post-start configuration (see Drivers) |

---

### Challenge Config

`config/challenge.yaml` — defines the runtime topology. Can contain multiple setups, each creating its own Docker network with a set of peers.

```yaml
setups:
  - network:
      name: my-network
      driver: macvlan
      options: { parent: eth0 }
      ipam: { subnet: "192.168.1.0/24" }
    peers:
      - component: ctf-sensor
        connection_options:
          ipv4_address: "192.168.1.20"
        settings:
          data: CF-4EDF1A6
```

---

### Network Config

Configures the Docker network created for each setup.

| Field | Description |
|-------|-------------|
| `name` | Network name (auto-generated if omitted) |
| `driver` | Docker network driver: `bridge`, `macvlan`, etc. |
| `options` | Driver-specific options (e.g. `{ parent: eth0 }` for macvlan) |
| `ipam` | IP address management settings, e.g. `{ subnet: "192.168.1.0/24" }` |

---

### Peer Config

Configures each container instance connected to a network.

| Field | Description |
|-------|-------------|
| `component` | Name of a component defined in `infrastructure.yaml` |
| `connection_options` | Network endpoint config: `ipv4_address`, `mac_address`, `aliases` |
| `run_options` | Container resource limits: `mem_limit`, `cpu_quota`, `log_config`, etc. |
| `settings` | Driver-specific configuration passed to the component after creation |
| `args` | Extra keyword arguments passed to container creation (e.g. `host_port`) |

**`connection_options` fields:**

| Field | Description |
|-------|-------------|
| `ipv4_address` | Static IP address within the network |
| `mac_address` | Static MAC address |
| `aliases` | List of DNS aliases within the network |

**`run_options` fields:**

| Field | Description |
|-------|-------------|
| `mem_limit` | Memory limit, e.g. `"512m"`, `"1g"` |
| `cpu_quota` | CPU quota in microseconds |
| `log_config` | Docker log driver config dict |

---

## Components

Each component is a Docker image built from a directory containing a `Dockerfile`. Components come in two types:

- **`simple`** — connected only to the internal network. No port is exposed to the host.
- **`connectable`** — given a dedicated bridge network so it can publish a port to the host, while also being connected to the internal network.

### ctf-sensor (`pnet-dev`)

A sensor simulator that writes a data string into the container filesystem on startup.

**Driver:** `pnet-driver`

**Settings:**

```yaml
settings:
  data: CF-4EDF1A6   # The sensor value written to /flag.txt inside the container
```

---

### HMI — `s7-ctf-hmi` (`snap7-hmi`)

A web-based Human-Machine Interface that polls a Siemens S7 PLC via the Snap7 library and displays mapped status messages. Runs on port `5000` inside the container.

**Driver:** `hmi-driver`

**Settings:**

```yaml
settings:
  output_settings:
    unreachable: "Congrats, you hacked plc!"
    default: "Looks like sensor is offline..."
  mappings:
    - input: CF-4EDF1A6
      output: "Sensor online!"
```

The `mappings` list translates raw PLC values to human-readable messages. The `output_settings` keys define fallback messages when the PLC is unreachable or the value has no mapping.

The HMI reads PLC connection settings from `challenge.yaml` under `connection_settings`:

```yaml
connection_settings:
  ip: "192.168.1.55"
  tcp_port: 102
  rack: 0
  slot: 1
  POLL_INTERVAL: 1.0
```

---

### PNET-dev (`pnet-dev`)

A simple network participant container used as a sensor node. Receives a flag string via the `pnet-driver` that is written to `/flag.txt` in the container.

---

### Participant Station (`participant-ssh`)

An SSH server container intended as the attacker/participant entry point. Exposes port `22` to the host.

**Driver:** `ssh-driver`

**Settings:**

```yaml
settings:
  users:
    - name: red-team
      password: 12345
    - name: blue-team
      password: 54321
```

User accounts are provisioned by writing a `users-setup.json` file to `/ws` inside the container before startup.

---

### Attacker-Auto (`attacker-auto`)

An automated attacker container that performs scripted network operations. Requires no driver or settings configuration.

---

### Demo SSH (`demo-ssh`)

A lightweight SSH server for demonstration purposes. Can be assigned a static MAC address for use in macvlan networks.

---

## Drivers

Drivers perform post-creation configuration by injecting files into containers via the Docker archive API before `start()` is called.

| Driver | Component | What it does |
|--------|-----------|--------------|
| `pnet-driver` | ctf-sensor | Writes `data` string to `/flag.txt` |
| `ssh-driver` | participant-ssh, demo-ssh | Writes `users-setup.json` to `/ws` |
| `hmi-driver` | s7-ctf-hmi | Writes `config.yaml` to `/app` |
| `attacker-driver` | attack-bot | No-op (reserved for future use) |

---

## Lifecycle

1. **Build** — all component Docker images are built from their directories at startup.
2. **Setup** — for each setup in `challenge.yaml`, a Docker network is created, then containers are created and configured via their drivers.
3. **Start** — all containers are started. If any container fails to start, already-started peers in that network are rolled back automatically.
4. **Shutdown** — on `SIGINT` or `SIGTERM`, all containers are stopped and removed, and all Docker networks are deleted. Press `Ctrl+C` a second time to force-quit immediately.

---

<!-- ## Project Structure

```
.
├── main.py                         # Entry point
├── config/
│   ├── infrastructure.yaml         # Devices & component catalogue
│   └── challenge.yaml              # Runtime topology
├── components/                     # Component Dockerfiles
│   ├── pnet-dev/
│   ├── snap7-hmi/
│   ├── participant-ssh/
│   ├── demo-ssh/
│   └── attacker-auto/
└── src/
    ├── config/
    │   ├── loader.py               # Pydantic config models & YAML loaders
    │   ├── components.py           # ComponentConfig models
    │   ├── devices.py              # DeviceConfig models
    │   └── options.py              # ConnectionOptions, RunOptions
    └── model/
        ├── manager.py              # Orchestrates networks and peers
        ├── networks.py             # BaseNetwork (Docker network wrapper)
        └── components/
            ├── components.py       # Component, Peer, ConnectablePeer
            └── drivers.py          # Driver implementations
``` -->
