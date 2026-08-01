import os
import shutil
import subprocess
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_from_directory

app = Flask(__name__)

# Paths (mounted/shared via docker-compose)
PROJECT_DIR = Path(os.environ.get("PROJECT_DIR", "/project"))  # holds docker-compose.yml
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/output"))
PROJECT_SRC_DIR = Path(os.environ.get("PROJECT_SRC_DIR", "/project_src"))  # holds fetched or uploaded project
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


@app.route("/git/pull", methods=["POST"])
def git_pull():
    data = request.json or {}
    repo_url = data.get("repo_url")
    branch = data.get("branch", "master")
    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400

    try:
        # Clean and recreate target directory
        if PROJECT_SRC_DIR.exists():
            shutil.rmtree(PROJECT_SRC_DIR)
        PROJECT_SRC_DIR.mkdir(parents=True, exist_ok=True)

        # Run git clone
        cmd = ["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(PROJECT_SRC_DIR)]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)

        if proc.returncode == 0:
            return jsonify({"ok": True, "output": proc.stdout})
        else:
            return jsonify({"error": f"Git clone failed (code {proc.returncode})", "output": proc.stdout}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload", methods=["POST"])
def upload_project():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not file.filename.endswith(".zip"):
        return jsonify({"error": "Only .zip files are allowed"}), 400

    try:
        # Save zip temporarily
        zip_path = Path("/tmp/uploaded_project.zip")
        file.save(zip_path)

        # Clean target directory
        if PROJECT_SRC_DIR.exists():
            shutil.rmtree(PROJECT_SRC_DIR)
        PROJECT_SRC_DIR.mkdir(parents=True, exist_ok=True)

        # Extract zip
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(PROJECT_SRC_DIR)

        # Clean up temporary zip file
        zip_path.unlink()

        # Flatten directory if nested in a single top-level directory
        subdirs = [x for x in PROJECT_SRC_DIR.iterdir() if x.is_dir() or x.is_file()]
        if len(subdirs) == 1 and subdirs[0].is_dir():
            wrapped_dir = subdirs[0]
            for item in wrapped_dir.iterdir():
                shutil.move(str(item), str(PROJECT_SRC_DIR))
            wrapped_dir.rmdir()

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    # Fetch port from environment, defaulting to 5050
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)
