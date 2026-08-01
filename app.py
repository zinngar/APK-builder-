import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, send_from_directory

app = Flask(__name__)

# Paths (mounted into this container via docker-compose)
PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", "/project"))  # holds docker-compose.yml
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/output"))
LOG_FILE = Path("/tmp/build.log")

state = {
    "status": "idle",       # idle | running | success | failed
    "started_at": None,
    "finished_at": None,
    "build_type": None,
}
lock = threading.Lock()


def run_build(build_type: str):
    with lock:
        state["status"] = "running"
        state["started_at"] = datetime.now().isoformat(timespec="seconds")
        state["finished_at"] = None
        state["build_type"] = build_type

    LOG_FILE.write_text(f"=== Build started ({build_type}) ===\n")

    cmd = [
        "docker", "compose", "run", "--rm",
        "trafficlites-build", build_type,
    ]

    try:
        with open(LOG_FILE, "a") as log:
            proc = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_DIR),
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
            proc.wait()

        with lock:
            state["status"] = "success" if proc.returncode == 0 else "failed"
            state["finished_at"] = datetime.now().isoformat(timespec="seconds")
    except Exception as e:
        with open(LOG_FILE, "a") as log:
            log.write(f"\n!! Runner error: {e}\n")
        with lock:
            state["status"] = "failed"
            state["finished_at"] = datetime.now().isoformat(timespec="seconds")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/build/<build_type>", methods=["POST"])
def trigger_build(build_type):
    if build_type not in ("release", "debug"):
        return jsonify({"error": "build_type must be 'release' or 'debug'"}), 400

    with lock:
        if state["status"] == "running":
            return jsonify({"error": "A build is already running"}), 409

    thread = threading.Thread(target=run_build, args=(build_type,), daemon=True)
    thread.start()
    return jsonify({"ok": True})


@app.route("/status")
def status():
    with lock:
        return jsonify(dict(state))


@app.route("/logs")
def logs():
    if not LOG_FILE.exists():
        return Response("", mimetype="text/plain")
    return Response(LOG_FILE.read_text(), mimetype="text/plain")


@app.route("/logs/stream")
def logs_stream():
    def generate():
        last_size = 0
        # stream until build no longer running, then send final chunk and stop
        while True:
            if LOG_FILE.exists():
                content = LOG_FILE.read_text()
                if len(content) > last_size:
                    yield content[last_size:]
                    last_size = len(content)
            with lock:
                running = state["status"] == "running"
            if not running:
                break
            time.sleep(1)

    return Response(generate(), mimetype="text/plain")


@app.route("/apks")
def list_apks():
    if not OUTPUT_DIR.exists():
        return jsonify([])
    files = sorted(
        OUTPUT_DIR.glob("*.apk"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    return jsonify(
        [
            {
                "name": f.name,
                "size_mb": round(f.stat().st_size / 1_000_000, 1),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(
                    timespec="seconds"
                ),
            }
            for f in files
        ]
    )


@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
