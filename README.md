# Siemens Logo Modbus – Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=white)](https://github.com/hacs/integration)
[![Default](https://img.shields.io/badge/Default-Integration-blue.svg?style=for-the-badge&logo=homeassistant&logoColor=white)](https://www.home-assistant.io)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Andries%20Muylaert-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/AndriesMuylaert)

> **This integration was fully generated with [Claude](https://claude.ai) by Anthropic.**

A HACS custom integration for **Siemens Logo! 8.4** PLCs using Modbus TCP.

## Features

| Address Type | HA Platform | Direction | Unit | Description |
|---|---|---|---|---|
| **I** – Digital Inputs | `binary_sensor` | R | bit | Physical inputs (I1–I*n*, default 20) |
| **Q** – Digital Outputs | `switch` | R/W | bit | Physical outputs (Q1–Q*n*, default 16) |
| **M** – Memory Coils | `switch` | R/W | bit | Internal memory bits (M1–M64, default 16) |
| **V** – Flag Bits | `switch` | R/W | bit | Variable memory bits (V0.0–V850.7, default off) |
| **AI** – Analog Inputs | `sensor` | R | word | Analog input values (AI1–AI8, default off) |
| **AQ** – Analog Outputs | `number` | R/W | word | Analog outputs (AQ1–AQ8, default off) |
| **VW** – Analog Memory | `number` | R/W | word | Variable word registers (VW1–VW425, default off) |
| **AM** – Analog Memory 2 | `number` | R/W | word | Analog memory registers (AM1–AM64, default off) |

### Special Features

#### NQ Virtual Outputs (NQ1–NQ16)
When enabled, AQ1 and AQ2 are treated as byte values where each bit represents a virtual digital output:
- **AQ1** (8 bits) → **NQ1–NQ8**
- **AQ2** (8 bits) → **NQ9–NQ16**

Each NQ entity is exposed as a `switch` in Home Assistant. Writing to an NQ switch performs a read-modify-write on the underlying AQ register. Requires **AQ count ≥ 2**.

#### M10–M14 Decimal Selector
When enabled, a single `number` entity (range 0–31) is exposed. Setting a value writes bits M10–M14 as individual Modbus coils — useful for sending a 5-bit command to a slave Logo in the background.

The value **automatically resets to 0 after 1 second**, making it a one-shot trigger.

**Bit order: M10 is the most significant bit (MSB), M14 is the least significant bit (LSB).**

| Decimal | M10 | M11 | M12 | M13 | M14 |
|---------|:---:|:---:|:---:|:---:|:---:|
| 0  | 0 | 0 | 0 | 0 | 0 |
| 1  | 0 | 0 | 0 | 0 | 1 |
| 2  | 0 | 0 | 0 | 1 | 0 |
| 3  | 0 | 0 | 0 | 1 | 1 |
| 16 | 1 | 0 | 0 | 0 | 0 |
| 19 | 1 | 0 | 0 | 1 | 1 |
| 31 | 1 | 1 | 1 | 1 | 1 |

Example: decimal **19** = binary **10011** → M10=**1**, M11=**0**, M12=**0**, M13=**1**, M14=**1**

## Requirements

- Home Assistant **Core 2026.3+**
- Siemens Logo! **8.4** with Modbus TCP enabled
- Python package: `pymodbus>=3.6.9` (installed automatically)

## Installation via HACS

1. Open HACS → **Integrations** → ⋮ menu → *Custom repositories*
2. Add `https://github.com/AndriesMuylaert/siemens-logo-modbus` as **Integration**
3. Search for *Siemens Logo Modbus* and install
4. Restart Home Assistant

## Configuration

Go to **Settings → Devices & Services → Add Integration** and search for *Siemens Logo Modbus*.

| Setting | Default | Range | Description |
|---|---|---|---|
| Modbus IP Address | *(empty)* | any IPv4 | IP of the Logo |
| Modbus Port | `510` | 1–65535 | TCP port (Logo default: 510) |
| Refresh Interval | `2` s | 1–10 s | Poll frequency |
| Digital Inputs – I | `20` | 1–24 | Number of wired inputs |
| Digital Outputs – Q | `16` | 1–20 | Number of wired outputs |
| Memory Coils – M | `16` | 0–64 | Internal memory coils (0 = off) |
| Flag Bits – V | `0` (off) | 0–6808 | Variable flag bits |
| Analog Inputs – AI | `0` (off) | 0–8 | Analog inputs |
| Analog Outputs – AQ | `0` (off) | 0–8 | Analog outputs |
| Analog Memory – VW | `0` (off) | 0–425 | Analog memory words |
| Analog Memory 2 – AM | `0` (off) | 0–64 | Analog memory 2 |
| Enable NQ outputs | off | on/off | AQ1/AQ2 bit-to-switch mapping |
| Enable M10–M14 selector | off | on/off | 5-bit one-shot command trigger |

All settings can be changed later via **Configure** in the integration card.

## Modbus Address Space Reference

| Type | Range | Modbus Address | Direction | Unit |
|---|---|---|---|---|
| I | 1–24 | Discrete Input (DI) 1–24 | R | bit |
| Q | 1–20 | Coil 8193–8212 | R/W | bit |
| M | 1–64 | Coil 8257–8320 | R/W | bit |
| V | 0.0–850.7 | Coil 1–6808 | R/W | bit |
| AI | 1–8 | Input Register (IR) 1–8 | R | word |
| AQ | 1–8 | Holding Register (HR) 513–520 | R/W | word |
| VW | 0–850 | Holding Register (HR) 1–425 | R/W | word |
| AM | 1–64 | Holding Register (HR) 529–592 | R/W | word |

## Logo! Modbus Setup

1. In Logo!Soft Comfort or the web interface: **Ethernet → Connections → Server** – enable Modbus TCP
2. Note the IP address and port (default **510**)
3. Slave/Unit ID is fixed at **1**

## HACS Icon Note

The icon displayed in HACS is fetched directly from GitHub. It will appear once the repository is pushed to GitHub — local installations will show "icon not available" in HACS until then.

## Credits

**Author:** [Andries Muylaert](https://github.com/AndriesMuylaert)

**Generated with:** [Claude](https://claude.ai) by [Anthropic](https://www.anthropic.com)

---

*© Andries Muylaert – MIT License*
