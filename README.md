# sivnsh7-monitor

A root-privileged, terminal-based monitoring dashboard for Kali Linux built with [Textual](https://github.com/Textualize/textual).

It brings five views into one terminal UI:

- **Overview and system resources** — current system/resource snapshots.
- **Network traffic** — traffic and protocol counts where packet capture is available.
- **Wi-Fi scanner** — nearby Wi-Fi scan results where supported by the adapter and system tools.
- **Bluetooth scanner** — nearby Bluetooth discovery where a compatible adapter and tools are available.
- **Services and ports** — local service/port information using the available system tools.

> Root access is powerful. Review the source before running it, and only monitor devices and networks you own or are authorised to administer. Hardware-dependent views may be unavailable on machines without the relevant adapter.

## Requirements

- Kali Linux or a compatible Debian-based environment.
- Python 3 with venv support.
- System tools: iw, bluez and network-manager.
- Python packages listed in requirements.txt (textual, rich, psutil and scapy).
- Root privileges for packet capture, wireless/Bluetooth discovery and full process/connection visibility.

## Install

Use a virtual environment instead of installing Python packages into the operating system's managed Python environment.

~~~bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip iw bluez network-manager

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

## Run

From the repository root:

~~~bash
sudo .venv/bin/python sivnsh7-monitor.py
~~~

Press **q** in the terminal UI to quit. The entry point checks for root privileges before loading the monitoring application.

## Notes

- If Scapy cannot capture traffic on a given setup, bandwidth statistics may still work through psutil; protocol breakdowns can be unavailable.
- Wi-Fi scanning tries iw and then nmcli.
- Bluetooth scanning tries available tools such as hcitool and bluetoothctl.
- If no wireless or Bluetooth adapter is present, the relevant view should report that no adapter was found instead of providing scan results.
- Results depend on permissions, installed system utilities, the kernel, adapter support and local configuration.

## Project layout

~~~text
sivnsh7-monitor/
├── sivnsh7-monitor.py       # entry point and root check
├── run_sivnsh7-monitor.sh   # convenience launcher
├── app.py                   # Textual app, layout and styles
├── widgets/                 # dashboard, network, system, Wi-Fi, Bluetooth and service views
├── monitors/                # background monitoring workers
├── utils/helpers.py         # root check, interface discovery and formatters
└── requirements.txt
~~~

## Development status

This is a personal project that is under active iteration. Hardware availability and the user's Linux configuration may change which views can populate data.
