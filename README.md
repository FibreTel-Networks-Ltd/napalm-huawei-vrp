[![PyPI](https://img.shields.io/pypi/v/napalm-huawei-vrp.svg)](https://pypi.python.org/pypi/napalm-huawei-vrp)
[![PyPI](https://img.shields.io/pypi/dm/napalm-huawei-vrp.svg)](https://pypi.python.org/pypi/napalm-huawei-vrp)

# NAPALM Huawei VRP — FibreTel Fork

This is a fork of the upstream [napalm-huawei-vrp](https://github.com/napalm-automation-community/napalm-huawei-vrp) driver, which has been dormant since 2022. The upstream driver has several unimplemented stubs and bugs that prevent it from working correctly on modern VRP8 hardware.

This fork focuses on making the driver functional for real-world SP deployments, specifically tested against **Huawei NE8000** running VRP8.

## Changes from upstream

- **Implemented `get_bgp_neighbors_detail()`** — was a stub (`pass`) in upstream. Now parses `display bgp peer` and `display bgp peer <ip> verbose` output. Returns all fields required by Peering Manager's `poll_bgp_sessions` job including `connection_state`, `remote_address`, prefix counts, flap count, uptime, and hold time.
- **Fixed `_save_config()`** — handles multiple Y/N prompts for master/slave MPU confirmation.

## Tested hardware

| Device | VRP Version | Status |
|--------|------------|--------|
| NE8000 | VRP8 | ✅ Tested |

## Supported APIs

### Get info
| API | Description |
|-----|-------------|
| `get_facts()` | Return general device information |
| `get_config()` | Read config |
| `get_arp_table()` | Get device ARP table |
| `get_mac_address_table()` | Get mac table of connected devices |
| `get_interfaces()` | Get interface information |
| `get_interfaces_ip()` | Get interface IP information |
| `get_interfaces_counters()` | Get interface counters |
| `get_lldp_neighbors()` | Fetch LLDP neighbor information |
| `get_bgp_neighbors()` | Get BGP neighbor summary |
| `get_bgp_neighbors_detail()` | Get detailed BGP neighbor state (global VRF) |

### Config
| API | Description |
|-----|-------------|
| `cli()` | Send any CLI commands |
| `load_merge_candidate()` | Load config |
| `compare_config()` | Diff running vs candidate config |
| `discard_config()` | Discard candidate config |
| `commit_config()` | Commit candidate config |

### Other
| API | Description |
|-----|-------------|
| `is_alive()` | Get device active status |
| `ping()` | Ping remote IP |

## Installation
```bash
pip install git+https://github.com/FibreTel-Networks-Ltd/napalm-huawei-vrp.git
```

## Quick start
```python
from napalm import get_network_driver
driver = get_network_driver('huawei_vrp')
device = driver(hostname='192.168.76.10', username='admin', password='password')
device.open()
print(device.get_bgp_neighbors_detail())
device.close()
```

## Notes

- `get_bgp_neighbors_detail()` currently only polls the global VRF. VPN-instance peers are not yet supported.
- Tested with Peering Manager 1.10.3 BGP session polling.

## Original project

https://github.com/napalm-automation-community/napalm-huawei-vrp
