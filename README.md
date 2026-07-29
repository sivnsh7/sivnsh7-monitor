# KaliWatch

A root-privileged, terminal-based monitoring dashboard for Kali Linux, built with
[Textual](https://github.com/Textualize/textual). Five tabs, one dashboard overview:
Network Traffic, System Resources, WiFi Scanner, Bluetooth Scanner, Services & Ports.

## Setup

```bash
cd kalwatch
sudo apt install -y python3-pip iw bluez network-manager   # system tools used as fallbacks
sudo pip install -r requirements.txt --break-system-packages
```

## Run

```bash
sudo python3 kalwatch.py
# or
./run_kalwatch.sh
```

Press `q` to quit. Requires root for packet capture, WiFi/Bluetooth scanning, and full
process/connection visibility — the app will refuse to start otherwise.

## Notes

- If `scapy` can't sniff on your setup, bandwidth stats keep working (via `psutil`);
  only the protocol-count breakdown is disabled.
- WiFi scanning tries `iw dev <iface> scan` first, then `nmcli`.
- Bluetooth scanning tries `hcitool scan` first, then `bluetoothctl`.
- No wireless/Bluetooth adapter present → the relevant tab shows a clear
  "No adapter found" state instead of crashing.

## Project layout

```
kalwatch/
├── kalwatch.py        # entry point + root check
├── app.py             # Textual App, CSS, tab layout
├── widgets/            # per-tab UI (dashboard, net, sys, wifi, bt, svc)
├── monitors/           # background threads publishing lock-protected snapshots
└── utils/helpers.py    # root check, interface discovery, formatters
```
