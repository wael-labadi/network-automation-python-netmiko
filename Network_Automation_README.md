# Network Automation Tool (Python + Netmiko + PyQt5)

A Python-based network automation tool that connects to Cisco IOS routers over SSH and automates common configuration tasks — built and tested in a GNS3 lab environment as part of the Data Computer Networks course, Faculty of Engineering and Information Technology.

**Authors:** Wael Labadi, Waseem Zalloum
**Supervised by:** Eng. Thaer Khatib

## Overview

Manually configuring network devices one by one through the CLI is slow and error-prone. This project automates that process: a Python script (later extended into a PyQt5 GUI) connects to routers via SSH using [Netmiko](https://netmiko.readthedocs.io) and lets the user apply configuration changes through simple menu choices instead of typing raw CLI commands on every device.

## Features

- **SSH connection management** to multiple routers (R1, R2), selectable at runtime
- **Change interface IP address** — updates IP/subnet on a given interface and handles the SSH session drop/reconnect that happens when the IP changes mid-session
- **Add static routes**
- **Configure OSPF** for dynamic routing between routers
- **Add user accounts** with privilege level 15 (full admin SSH access)
- **Save running configuration** to NVRAM (`write memory`) so changes survive a reboot
- **Persistent state** — saves the last-used router IPs (`router_ips.json`) and router info (`router_info.txt`) in the project folder

## Tech Stack

- **Python 3**
- **Netmiko** — SSH connection handling for network devices
- **PyQt5** — graphical interface (GUI version)
- **GNS3** — network simulation/lab environment
- **Cisco IOS** routers (simulated)

## How It Works

1. The script holds a dictionary of routers with their connection parameters (`device_type`, `host`, `username`, `password`, `secret`, timeouts, etc.)
2. The user selects which router to connect to
3. Netmiko's `ConnectHandler` opens an SSH session and enters privileged (`enable`) mode
4. A menu lets the user choose a configuration task (change IP, add route, configure OSPF, add user, save config)
5. Commands are sent via `send_config_set()`; for the IP-change case, the script gracefully handles the expected SSH disconnect, waits, and reconnects using the new IP before continuing

## Lab Environment Setup (GNS3)

The code connects to real (simulated) Cisco IOS routers, not a mock — so to run this project yourself, you need to reproduce the GNS3 lab first. This is the network the script was built and tested against.

**Topology:**
- Two Cisco IOS routers, **R1** and **R2**, connected to each other
- **R1** is also connected to the host PC through a **Cloud node** in GNS3 (not a NAT node — NAT blocks the host from initiating connections into the topology, which was one of the issues hit during development)
- Host PC ↔ R1: `FastEthernet0/0`, network `192.168.85.x`, R1 = `192.168.85.200`
- R1 ↔ R2: network `172.16.0.0/24`, R1 = `172.16.0.1`, R2 = `172.16.0.2`
- A `Loopback0` interface (`10.0.0.1`) on R1 was used for testing/verifying routing

**Setup steps:**

1. Install **VMware Workstation** and run the **GNS3 VM** inside it
2. Build the topology above in GNS3: R1 — R2, with R1 attached to a **Cloud node** linked to the host machine's network adapter
3. On each router, configure SSH access before running any Python code:
   - Set a hostname and domain name (required before generating RSA keys)
   - Generate RSA keys (1024-bit) and enable SSH version 2
   - Create a local user with privilege level 15 (full admin)
   - Set the VTY lines to local authentication, SSH-only (`transport input ssh`)
4. On the **host PC**, add a static route so it can reach R2's subnet through R1:
   ```
   route add 172.16.0.0 mask 255.255.0.0 <R1's host-facing IP>
   ```
   (R2 sits on a subnet the host has no direct route to, since it's one hop behind R1)
5. Verify router access with **Solar-PuTTY** (or any SSH client) before running the Python script, to confirm SSH is actually reachable from the host
6. Update the `routers` dictionary in the script with your router IPs/credentials, then run it

## Notable Engineering Details

- Uses `disabled_algorithms` to work around SSH key-exchange compatibility issues with older Cisco IOS SSH implementations
- Sets `use_keys=False` and `allow_agent=False` to force password-based auth and avoid conflicts with local SSH agents/keys
- Catches the session drop that occurs immediately after an interface IP change (since the SSH session becomes invalid the moment the IP changes) and reconnects automatically instead of crashing

## Challenges Solved During Development

- SSH not enabled on router by default (missing hostname/domain name required for RSA key generation)
- IP address conflicts with the GNS3 VM's own network
- NAT node vs. Cloud node in GNS3 — NAT blocked host-to-router connections; switching to a Cloud node fixed it
- Socket/session closing when changing the connected interface's own IP mid-session
- Routing from the host PC to a second router (R2) on a separate subnet, solved with a static route on the host
- PyQt5 not resolving in VS Code due to interpreter mismatch

## Future Work

- Interface status monitoring with alerts when a link goes down
- Automated, timestamped configuration backups
- Multi-device / concurrent configuration using threading or a framework like [Nornir](https://nornir.readthedocs.io)
- Non-blocking GUI (threading so the interface doesn't freeze during connections)
- Multi-vendor support via [NAPALM](https://napalm.readthedocs.io) instead of Cisco IOS only

## Security Note

Credentials are currently hardcoded for the GNS3 lab environment. In a production setting these would be pulled from environment variables or a secrets manager rather than stored in the script.

## References

- Netmiko Documentation — https://netmiko.readthedocs.io
- GNS3 Documentation — https://docs.gns3.com
- Cisco IOS SSH Configuration Guide — https://www.cisco.com
- Cisco DevNet Learning Labs — https://developer.cisco.com/learning
- PyQt5 Documentation — https://www.riverbankcomputing.com/software/pyqt
