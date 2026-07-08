from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

CONFIG_DIR = "/configs"
CONFIG_FILE = os.path.join(CONFIG_DIR, "miningcore.json")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        os.makedirs(CONFIG_DIR, exist_ok=True)

        coin = request.form.get("coin", "BCH")
        pool_type = request.form.get("pool_type", "solo")
        wallet = request.form.get("wallet", "").strip()
        pool_name = request.form.get("pool_name", f"{coin} {pool_type.title()} Pool").strip()
        stratum_port = int(request.form.get("stratum_port", "3333"))

        config = {
            "generatedBy": "Seymour MiningCore Wizard",
            "generatedAt": datetime.utcnow().isoformat() + "Z",
            "coin": coin,
            "poolType": pool_type,
            "poolName": pool_name,
            "walletAddress": wallet,
            "stratumPort": stratum_port,
            "database": {
                "host": "postgres",
                "port": 5432,
                "database": "miningcore",
                "user": "miningcore",
                "password": "miningcore"
            },
            "redis": {
                "host": "redis",
                "port": 6379
            }
        }

        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

        return redirect(url_for("success"))

    existing = None
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            existing = json.load(f)

    return render_template("index.html", existing=existing)


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/health")
def health():
    return {"status": "ok", "app": "seymour-miningcore-wizard"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
