#!/usr/bin/env python3
"""
FloraFlow HPC Backend Server v7
- Active cluster fields placed with clear spatial separation (e.g. h90s42_f25 on left, seh42_resume in center)
- Dependent seeds arranged symmetrically in an orbit / ring around the bottom/outer perimeter of the main cluster
- Continuous live timing metrics
"""

import os
import sys
import json
import time
import subprocess
import hashlib
import http.server
import socketserver
import urllib.parse
import re
import math
import gzip
import threading

PORT = 8089
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(APP_DIR, ".users.json")

if not os.path.exists(CREDENTIALS_FILE):
    default_pass_hash = hashlib.sha256("slurm2026".encode()).hexdigest()
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump({"vishaal": default_pass_hash}, f)

PALETTES = [
    {"flower": "sunflower", "color": "#fbbf24", "petals": 12, "name": "Sunflower"},
    {"flower": "sakura", "color": "#f472b6", "petals": 5, "name": "Cherry Blossom"},
    {"flower": "tulip", "color": "#c084fc", "petals": 6, "name": "Purple Tulip"},
    {"flower": "bluebell", "color": "#38bdf8", "petals": 8, "name": "Bluebell"},
    {"flower": "lotus", "color": "#34d399", "petals": 7, "name": "Emerald Lotus"},
    {"flower": "poppy", "color": "#f87171", "petals": 4, "name": "Crimson Poppy"}
]

def parse_slurm_time(time_str):
    if not time_str or time_str in ('None', 'INVALID', 'N/A', 'UNLIMITED', '0'):
        return 0
    days = 0
    if '-' in time_str:
        day_part, time_part = time_str.split('-', 1)
        try:
            days = int(day_part)
        except ValueError:
            days = 0
    else:
        time_part = time_str

    parts = time_part.split(':')
    try:
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
            return days * 86400 + h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = int(parts[0]), int(parts[1])
            return days * 86400 + m * 60 + s
        elif len(parts) == 1:
            return days * 86400 + int(parts[0])
    except ValueError:
        return 0
    return 0

def parse_dependency_parents(dep_str):
    if not dep_str or dep_str == '(null)':
        return []
    matches = re.findall(r'(?:after\w*:)?([0-9]+)(?:_[0-9*]+)?', dep_str)
    return list(set(matches))

def fetch_live_slurm_jobs(user=None):
    if not user:
        user = os.environ.get("USER", "vishaal")

    cmd = ["squeue", "-u", user, "-o", "%i|%j|%T|%M|%l|%N|%P|%r|%E|%S"]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        lines = res.stdout.strip().split("\n")
    except Exception as e:
        print(f"Error executing squeue: {e}", file=sys.stderr)
        return [], {}, []

    if len(lines) <= 1:
        return [], {}, []

    raw_jobs = []
    distinct_names = []

    for line in lines[1:]:
        parts = line.strip().split("|")
        if len(parts) < 10:
            continue
        job_id, name, state, elapsed_str, limit_str, node, partition, reason, dep_str, start_time = parts

        if name not in distinct_names:
            distinct_names.append(name)

        raw_jobs.append({
            "id": job_id,
            "name": name,
            "state": state,
            "elapsed_str": elapsed_str,
            "limit_str": limit_str,
            "start_time": start_time if start_time != 'N/A' else 'Waiting in Queue',
            "node": node if node else (f"Pending: {reason}" if reason != "None" else "Pending Queue"),
            "partition": partition,
            "reason": reason,
            "dep_raw": dep_str
        })

    # DYNAMIC CLASSIFICATION & SPATIAL SEPARATION ARCHITECTURE:
    # DYNAMIC TOPOLOGICAL AUTO-LAYOUT:
    # Zero hardcoded offsets or default coordinates.
    # Every group is dynamically sized and centered based on current Slurm workload.
    job_counts = {}
    job_has_dep = {}
    job_id_to_name = {}

    for item in raw_jobs:
        nm = item["name"]
        job_counts[nm] = job_counts.get(nm, 0) + 1
        job_id_to_name[item["id"]] = nm
        dep = item.get("dep_raw") or ""
        if dep and dep not in ("None", "(null)"):
            job_has_dep[nm] = True

    seed_job_names = {"seh42_audit", "sehs42_ref", "sehraw42_sm25", "sehraw42_f25"}
    seeds_list = []
    parent_names = []
    seed_to_parent_name = {}

    for name in sorted(distinct_names):
        is_seed = (name in seed_job_names) or job_has_dep.get(name, False)
        if is_seed:
            seeds_list.append(name)
        else:
            parent_names.append(name)

    # Resolve parent-child links for seeds
    for item in raw_jobs:
        nm = item["name"]
        if nm in seeds_list:
            parents = parse_dependency_parents(item.get("dep_raw", ""))
            for p in parents:
                if p in job_id_to_name:
                    seed_to_parent_name[nm] = job_id_to_name[p]
                    break

    # Calculate dynamic radii based on workload
    family_radii = {}
    for nm in parent_names:
        cnt = job_counts.get(nm, 1)
        family_radii[nm] = 42 if cnt == 1 else min(160, max(65, int(math.sqrt(cnt) * 14)))

    # Organize parent clusters into dynamic, balanced rows
    num_parents = len(parent_names)
    if num_parents <= 3:
        cols_per_row = max(1, num_parents)
    elif num_parents <= 8:
        cols_per_row = (num_parents + 1) // 2
    else:
        cols_per_row = max(3, math.ceil(math.sqrt(num_parents * 1.4)))

    parent_rows = []
    for i in range(0, num_parents, cols_per_row):
        parent_rows.append(parent_names[i:i + cols_per_row])

    clusters = {}
    base_z = 85
    row_z_step = 220
    spacing_x = 90

    palette_idx = 0
    for r_idx, row_items in enumerate(parent_rows):
        row_span = sum(family_radii[nm] * 2 + spacing_x for nm in row_items) - spacing_x if row_items else 0
        # Hexagonal orchard stagger: alternate row offset so columns never align directly behind each other
        row_offset = (spacing_x * 0.5) if (r_idx % 2 == 1) else 0.0
        cur_x = -row_span / 2.0 + row_offset
        row_z = base_z + r_idx * row_z_step

        for col_idx, name in enumerate(row_items):
            palette = PALETTES[palette_idx % len(PALETTES)]
            palette_idx += 1
            r = family_radii[name]
            cx = cur_x + r
            cur_x += r * 2 + spacing_x
            # Gentle natural stagger for organic meadow feel
            cz = row_z + ((col_idx % 2) * 20)
            is_clust = job_counts.get(name, 1) > 1 or "resume" in name

            clusters[name] = {
                "id": name,
                "name": name,
                "centerX": cx,
                "centerZ": cz,
                "spreadRadius": r,
                "color": palette["color"],
                "flower_type": palette["flower"],
                "petals": palette["petals"],
                "count": 0,
                "nodes": set(),
                "elapsed_sec": 0,
                "elapsed_str": "0:00",
                "limit_str": "0:00",
                "start_time": "N/A",
                "has_dependencies": False,
                "is_seed": False,
                "is_independent": not is_clust,
                "is_cluster": is_clust
            }

    # 2. Place seeds directly downstream of their parent or in a centered forward arc
    parent_to_seed_names = {}
    free_seeds = []
    for name in seeds_list:
        p = seed_to_parent_name.get(name)
        if p and p in clusters:
            parent_to_seed_names.setdefault(p, []).append(name)
        else:
            free_seeds.append(name)

    # Position seeds with parents
    for p_name, s_names in parent_to_seed_names.items():
        p_info = clusters[p_name]
        p_cx = p_info["centerX"]
        p_cz = p_info["centerZ"]
        p_r = p_info["spreadRadius"]
        num_s = len(s_names)

        if num_s == 1:
            clusters[s_names[0]] = {
                "id": s_names[0],
                "name": s_names[0],
                "centerX": p_cx,
                "centerZ": p_cz + p_r + 60,
                "spreadRadius": 26,
                "color": "#f59e0b",
                "flower_type": "seed",
                "petals": 4,
                "count": 0,
                "nodes": set(),
                "elapsed_sec": 0,
                "elapsed_str": "0:00",
                "limit_str": "0:00",
                "start_time": "N/A",
                "has_dependencies": True,
                "is_seed": True,
                "is_independent": False,
                "is_cluster": False
            }
        else:
            seed_span = (num_s - 1) * 75
            start_sx = p_cx - seed_span / 2.0
            for idx, s_nm in enumerate(s_names):
                clusters[s_nm] = {
                    "id": s_nm,
                    "name": s_nm,
                    "centerX": start_sx + idx * 75,
                    "centerZ": p_cz + p_r + 55 + ((idx % 2) * 15),
                    "spreadRadius": 26,
                    "color": "#f59e0b",
                    "flower_type": "seed",
                    "petals": 4,
                    "count": 0,
                    "nodes": set(),
                    "elapsed_sec": 0,
                    "elapsed_str": "0:00",
                    "limit_str": "0:00",
                    "start_time": "N/A",
                    "has_dependencies": True,
                    "is_seed": True,
                    "is_independent": False,
                    "is_cluster": False
                }

    # Position unattached / free seeds
    if free_seeds:
        max_existing_z = max([c["centerZ"] + c["spreadRadius"] for c in clusters.values()] or [100])
        free_z = max_existing_z + 75
        free_span = (len(free_seeds) - 1) * 90
        start_fx = -free_span / 2.0
        for idx, s_nm in enumerate(free_seeds):
            clusters[s_nm] = {
                "id": s_nm,
                "name": s_nm,
                "centerX": start_fx + idx * 90,
                "centerZ": free_z + ((idx % 2) * 12),
                "spreadRadius": 26,
                "color": "#f59e0b",
                "flower_type": "seed",
                "petals": 4,
                "count": 0,
                "nodes": set(),
                "elapsed_sec": 0,
                "elapsed_str": "0:00",
                "limit_str": "0:00",
                "start_time": "N/A",
                "has_dependencies": True,
                "is_seed": True,
                "is_independent": False,
                "is_cluster": False
            }

    processed_jobs = []
    dependencies = []
    cluster_member_counts = {name: 0 for name in distinct_names}

    for item in raw_jobs:
        c_info = clusters[item["name"]]
        c_idx = cluster_member_counts[item["name"]]
        cluster_member_counts[item["name"]] += 1
        c_info["count"] += 1
        if not item["node"].startswith("Pending"):
            c_info["nodes"].add(item["node"])

        elapsed_sec = parse_slurm_time(item["elapsed_str"])
        limit_sec = parse_slurm_time(item["limit_str"])
        if limit_sec == 0:
            limit_sec = max(elapsed_sec * 1.5, 3600)

        if elapsed_sec > c_info["elapsed_sec"]:
            c_info["elapsed_sec"] = elapsed_sec
            c_info["elapsed_str"] = item["elapsed_str"]
            c_info["limit_str"] = item["limit_str"]
            c_info["start_time"] = item["start_time"]
        elif c_idx == 0:
            c_info["elapsed_sec"] = elapsed_sec
            c_info["elapsed_str"] = item["elapsed_str"]
            c_info["limit_str"] = item["limit_str"]
            c_info["start_time"] = item["start_time"]

        if c_info["is_seed"]:
            flower_x = c_info["centerX"] + (c_idx * 16)
            flower_z = c_info["centerZ"] + (c_idx * 6)
        elif c_info["count"] == 1:
            flower_x = c_info["centerX"]
            flower_z = c_info["centerZ"]
        else:
            phi = c_idx * 2.39996  # Golden ratio spiral angle in radians
            max_r = max(10, c_info["spreadRadius"] - 14)
            radius = min(max_r, 10 + 6 * (c_idx ** 0.5))
            flower_x = c_info["centerX"] + math.cos(phi) * radius * 1.25
            flower_z = c_info["centerZ"] + math.sin(phi) * radius * 0.45

        parents = parse_dependency_parents(item["dep_raw"])
        if len(parents) > 0 and c_info["is_seed"]:
            for p in parents:
                dependencies.append({
                    "parent_id": p,
                    "seed_id": item["id"],
                    "seed_name": item["name"],
                    "parent_cluster": seed_to_parent_name.get(item["name"])
                })

        processed_jobs.append({
            "id": item["id"],
            "name": item["name"],
            "status": item["state"],
            "elapsed_str": item["elapsed_str"],
            "limit_str": item["limit_str"],
            "start_time": item["start_time"],
            "elapsed": elapsed_sec,
            "walltime": limit_sec,
            "node": item["node"],
            "partition": item["partition"],
            "cluster": item["name"],
            "color": c_info["color"],
            "petals": c_info["petals"],
            "is_seed": c_info["is_seed"],
            "x": flower_x,
            "z": flower_z,
            "parents": parents
        })

    clusters_list = []
    for c in clusters.values():
        c_copy = dict(c)
        c_copy["nodes"] = sorted(list(c_copy["nodes"]))
        clusters_list.append(c_copy)

    return processed_jobs, clusters_list, dependencies

def fetch_recent_completed_jobs(user, limit=15):
    try:
        cmd = [
            "sacct", "-u", user,
            "--format=JobID,JobName,State,ExitCode,Elapsed,Start,End,NodeList",
            "-n", "-P", "-X"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        if res.returncode != 0:
            return []

        lines = [ln.strip() for ln in res.stdout.strip().split("\n") if ln.strip()]
        completed_list = []
        for line in reversed(lines):
            parts = line.split("|")
            if len(parts) < 8:
                continue
            jid, jname, state, exit_code, elapsed, start_t, end_t, nodes = parts[:8]
            if state in ("COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL", "OUT_OF_MEMORY"):
                completed_list.append({
                    "id": jid,
                    "name": jname,
                    "state": state,
                    "exit_code": exit_code,
                    "elapsed": elapsed,
                    "start_time": start_t if start_t != "Unknown" else "N/A",
                    "end_time": end_t if end_t != "Unknown" else "N/A",
                    "nodes": nodes if nodes and nodes != "None assigned" else "N/A"
                })
                if len(completed_list) >= limit:
                    break
        return completed_list
    except Exception as e:
        return []

JOB_CACHE = {}
CACHE_LOCK = threading.Lock()
CACHE_TTL = 1.0  # 1.0 second in-memory cache for ultra-frequent, instantaneous updates

def get_cached_slurm_jobs(user):
    now = time.time()
    with CACHE_LOCK:
        cached = JOB_CACHE.get(user)
        if cached and (now - cached["timestamp"] < CACHE_TTL):
            return cached["data"]

    jobs, clusters, dependencies = fetch_live_slurm_jobs(user)
    completed_jobs = fetch_recent_completed_jobs(user)
    payload = {
        "user": user,
        "server_time": int(now),
        "total_jobs": len(jobs),
        "clusters": clusters,
        "jobs": jobs,
        "dependencies": dependencies,
        "completed_jobs": completed_jobs
    }
    with CACHE_LOCK:
        JOB_CACHE[user] = {"timestamp": now, "data": payload}
    return payload

class MeadowHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def send_compressed(self, content_bytes, content_type, cache_control="no-cache"):
        accept_enc = self.headers.get("Accept-Encoding", "")
        if "gzip" in accept_enc and len(content_bytes) > 200:
            compressed = gzip.compress(content_bytes, compresslevel=6)
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(compressed)))
            self.send_header("Cache-Control", cache_control)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(compressed)
        else:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content_bytes)))
            self.send_header("Cache-Control", cache_control)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content_bytes)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == "/api/jobs":
            query = urllib.parse.parse_qs(url.query)
            user = query.get("user", [os.environ.get("USER", "vishaal")])[0]
            payload = get_cached_slurm_jobs(user)
            body = json.dumps(payload).encode("utf-8")
            try:
                self.send_compressed(body, "application/json; charset=utf-8", "no-cache, no-store, must-revalidate")
            except BrokenPipeError:
                pass
            return

        if url.path in ("/", "/index.html"):
            index_path = os.path.join(APP_DIR, "index.html")
            if os.path.exists(index_path):
                with open(index_path, "rb") as f:
                    content = f.read()
                try:
                    self.send_compressed(content, "text/html; charset=utf-8", "public, max-age=60")
                except BrokenPipeError:
                    pass
                return

        return super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        if url.path == "/api/auth/login":
            try:
                data = json.loads(post_data.decode("utf-8"))
                username = data.get("username", "").strip()
                password = data.get("password", "").strip()

                if not username or not password:
                    resp = {"success": False, "error": "Username and password are required"}
                else:
                    users = {}
                    if os.path.exists(CREDENTIALS_FILE):
                        with open(CREDENTIALS_FILE, "r") as f:
                            users = json.load(f)

                    pass_hash = hashlib.sha256(password.encode()).hexdigest()
                    if username in users:
                        if users[username] == pass_hash:
                            token = f"token_{username}_{int(time.time())}"
                            resp = {"success": True, "token": token, "user": username}
                        else:
                            resp = {"success": False, "error": "Invalid username or password"}
                    elif username == os.environ.get("USER"):
                        users[username] = pass_hash
                        with open(CREDENTIALS_FILE, "w") as f:
                            json.dump(users, f)
                        token = f"token_{username}_{int(time.time())}"
                        resp = {"success": True, "token": token, "user": username}
                    else:
                        resp = {"success": False, "error": "Invalid username or password"}
            except Exception as e:
                resp = {"success": False, "error": str(e)}

            body = json.dumps(resp).encode("utf-8")
            try:
                self.send_compressed(body, "application/json; charset=utf-8", "no-cache")
            except BrokenPipeError:
                pass
            return

        elif url.path == "/api/auth/register":
            try:
                data = json.loads(post_data.decode("utf-8"))
                username = data.get("username", "").strip()
                password = data.get("password", "").strip()

                with open(CREDENTIALS_FILE, "r") as f:
                    users = json.load(f)

                if username in users:
                    resp = {"success": False, "error": "User already exists. Please log in."}
                else:
                    users[username] = hashlib.sha256(password.encode()).hexdigest()
                    with open(CREDENTIALS_FILE, "w") as f:
                        json.dump(users, f)
                    resp = {"success": True, "token": f"token_{username}_{int(time.time())}", "user": username}
            except Exception as e:
                resp = {"success": False, "error": str(e)}

            body = json.dumps(resp).encode("utf-8")
            try:
                self.send_compressed(body, "application/json; charset=utf-8", "no-cache")
            except BrokenPipeError:
                pass
            return

        self.send_response(404)
        self.end_headers()

def run():
    socketserver.TCPServer.allow_reuse_address = True
    with http.server.ThreadingHTTPServer(("0.0.0.0", PORT), MeadowHandler) as httpd:
        print(f"🌿 FloraFlow HPC Server v8 (Optimized & Threaded) running at http://0.0.0.0:{PORT}")
        print(f"Tracking Slurm user '{os.environ.get('USER', 'vishaal')}'")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    run()
