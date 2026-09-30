# 🌸 FloralFlow HPC

> **A Botanical Digital Twin & Real-Time Telemetry Dashboard for High Performance Computing (Slurm)**

[![Python 3](https://img.shields.io/badge/Python-3.7+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Slurm Workload Manager](https://img.shields.io/badge/Slurm-Workloads-00599C?style=for-the-badge)](https://slurm.schedmd.com)
[![Cloudflare Tunnel](https://img.shields.io/badge/Cloudflare-Tunnel-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)](https://cloudflare.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald?style=for-the-badge)](LICENSE)

**FloralFlow HPC** transforms complex, monochrome cluster queue data (`squeue`, `sacct`) into an interactive, high-craft 3D botanical sanctuary and real-time telemetric command center.

---

## 🌟 Key Features

* **🌸 Floral Meadow View**:
  * Real-time 3D botanical simulation rendered on Canvas.
  * Every running job grows into an organic flower with stems, petals, and dynamic breeze simulation.
  * Walltime progress is reflected directly in botanical growth.
  * Dependent job arrays flow through scenic mountain brooks connecting to parent nodes.
* **📊 Telemetric View**:
  * Glanceable cluster KPIs (Running jobs, Pending/Queue limits, Active GPU nodes, Recently finished).
  * Continuous second-by-second ticking elapsed timers.
  * Accounting table powered by Slurm `sacct` with exit codes, compute node mappings, and walltimes.
* **🌐 Zero-Root Cloudflare Tunnel**:
  * Generates an end-to-end encrypted public HTTPS URL (`https://xxxx.trycloudflare.com`).
  * Runs entirely in user-space on login nodes or compute nodes — **no `sudo`, no root, and no firewall configuration required**.
* **🔒 Seamless Authentication**:
  * Encrypted password authentication with persistent session storage.
  * Instant password setup and reset directly via command-line arguments.

---

## 🚀 Quickstart (Any HPC User)

### 1. Clone the Repository
```bash
git clone https://github.com/PG-9-9/FloralFlow_HPC.git
cd FloralFlow_HPC
```

### 2. Make the Launcher Executable
```bash
chmod +x start_online.sh
```

### 3. Launch with Your Password
```bash
./start_online.sh -p myClusterPassword
```

**That's it!** The script will:
1. Automatically download the standalone user-space `cloudflared` binary if not present.
2. Initialize your user credentials.
3. Start the lightweight backend daemon.
4. Output your secure public HTTPS URL:

```text
==========================================================
 🌸 FloralFlow HPC is LIVE Online!
==========================================================
 👤 Slurm User : your_username
 🌐 Public URL : https://your-tunnel-url.trycloudflare.com
 💡 Change pass: ./start_online.sh -p <new_password>
 🛑 To Stop    : ./start_online.sh --stop
==========================================================
```

Open the link on your phone, tablet, or laptop to view your HPC jobs in real time!

---

## ⚙️ Command-Line Options

The launcher (`start_online.sh`) and Python backend (`server.py`) accept arguments to customize your run:

| Option | Example | Description |
| :--- | :--- | :--- |
| `-p`, `--password <pass>` | `./start_online.sh -p myPass123` | Set or update your cluster login password |
| `-u`, `--user <username>` | `./start_online.sh -u other_user` | Monitor a specific HPC user's jobs (default: `$USER`) |
| `--port <port>` | `./start_online.sh --port 8090` | Set a custom local backend port (default: `8089`) |
| `--reset-password` | `./start_online.sh --reset-password` | Interactively change your password |
| `--stop` | `./start_online.sh --stop` | Stop all running FloralFlow servers & tunnels |
| `-h`, `--help` | `./start_online.sh --help` | Show command usage and options |

---

## 🛠️ Architecture & Security

* **Self-Contained Backend**: Written in standard Python 3 with zero required pip dependencies.
* **Cluster Privacy**: Your cluster credentials (`.users.json`), logs, and tunnel files are git-ignored and stored locally with SHA-256 password hashing.
* **Encrypted Gateway**: Cloudflare Quick Tunnels proxy the local HTTP server over encrypted TLS without opening any public listening ports on your HPC login node.

---

## 📄 License
Released under the [MIT License](LICENSE).
