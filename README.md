# 🌸 FloralFlow HPC

> **Real-time Botanical Digital Twin & Telemetric Dashboard for Slurm Clusters**

---

## 🚀 Quickstart

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
./start_online.sh -p mySecretPass123
```

> **👤 What is my username?**
> Your username is simply your **HPC username** (the username you use to SSH into your cluster, i.e. the output of `whoami`). It is automatically detected from your HPC environment (`$USER`).

The script automatically downloads `cloudflared` (no root/sudo needed), starts the backend, and gives you a secure public HTTPS URL:

```text
==========================================================
 🌸 FloralFlow HPC is LIVE Online!
==========================================================
 👤 Slurm User : vishaal
 🌐 Public URL : https://your-tunnel-url.trycloudflare.com
 💡 Change pass: ./start_online.sh -p <new_password>
 🛑 To Stop    : ./start_online.sh --stop
==========================================================
```

Open the link in any web browser (phone, tablet, or laptop) and log in using your HPC username (e.g. `vishaal`) and the password you set.

---

## ⚙️ Command-Line Options & Examples

| Option | Description | Example (using `vishaal`) |
| :--- | :--- | :--- |
| **Default Launch** | Starts with current user and existing/default credentials | `./start_online.sh` |
| `-p`, `--password <pass>` | Set or update your cluster login password | `./start_online.sh -u vishaal -p slurm2026` |
| `-u`, `--user <username>` | Specify the Slurm user to monitor (defaults to your `$USER`) | `./start_online.sh -u vishaal` |
| `--port <port>` | Run backend on a custom local port | `./start_online.sh -u vishaal --port 8090` |
| `--reset-password` | Prompt interactively to change your password | `./start_online.sh -u vishaal --reset-password` |
| `--stop` | Terminate running FloralFlow server and Cloudflare tunnel | `./start_online.sh --stop` |
| `-h`, `--help` | Display command usage and options | `./start_online.sh -h` |
