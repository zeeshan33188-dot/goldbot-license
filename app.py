"""
LICENSE SERVER — Gold Signal Bot
Host on Render.com (Free)
"""

from flask import Flask, request, jsonify
import json
import os
import hashlib
from datetime import datetime, timedelta

app = Flask(__name__)

# ─────────────────────────────────────────────
#  MASTER PASSWORD — CHANGE THIS!
# ─────────────────────────────────────────────
MASTER_KEY = "ZeeshanGoldBot2026"  # Aapka secret key — kisi ko mat batana!

# ─────────────────────────────────────────────
#  LICENSES DATABASE (JSON file)
# ─────────────────────────────────────────────
DB_FILE = "licenses.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─────────────────────────────────────────────
#  LICENSE CHECK — Bot yeh call karta hai
# ─────────────────────────────────────────────

@app.route("/check", methods=["POST"])
def check_license():
    data      = request.json
    mt5_login = str(data.get("mt5_login", ""))
    key       = data.get("license_key", "")

    db = load_db()

    if mt5_login not in db:
        return jsonify({"valid": False, "msg": "License nahi mili"})

    license = db[mt5_login]

    # Key check
    if license["key"] != key:
        return jsonify({"valid": False, "msg": "Wrong license key"})

    # Expiry check
    expiry = datetime.strptime(license["expiry"], "%Y-%m-%d")
    if datetime.now() > expiry:
        return jsonify({"valid": False, "msg": f"License expired: {license['expiry']}"})

    # Active check
    if not license.get("active", True):
        return jsonify({"valid": False, "msg": "License band kar di gayi hai"})

    days_left = (expiry - datetime.now()).days
    return jsonify({
        "valid":     True,
        "msg":       f"License valid! {days_left} din baaki",
        "days_left": days_left,
        "name":      license.get("name", "Client")
    })

# ─────────────────────────────────────────────
#  ADMIN ROUTES — Aap yeh use karo
# ─────────────────────────────────────────────

@app.route("/admin/add", methods=["POST"])
def add_license():
    """Naya client add karo"""
    data = request.json
    if data.get("master_key") != MASTER_KEY:
        return jsonify({"success": False, "msg": "Wrong master key"})

    mt5_login = str(data["mt5_login"])
    name      = data.get("name", "Client")
    days      = data.get("days", 30)

    # License key generate karo
    key    = hashlib.md5(f"{mt5_login}{MASTER_KEY}{name}".encode()).hexdigest()[:16].upper()
    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    db = load_db()
    db[mt5_login] = {
        "name":    name,
        "key":     key,
        "expiry":  expiry,
        "active":  True,
        "added":   datetime.now().strftime("%Y-%m-%d"),
    }
    save_db(db)

    return jsonify({
        "success":    True,
        "mt5_login":  mt5_login,
        "name":       name,
        "key":        key,
        "expiry":     expiry,
        "msg":        f"License add ho gayi! Key: {key}"
    })


@app.route("/admin/extend", methods=["POST"])
def extend_license():
    """License extend karo"""
    data = request.json
    if data.get("master_key") != MASTER_KEY:
        return jsonify({"success": False, "msg": "Wrong master key"})

    mt5_login = str(data["mt5_login"])
    days      = data.get("days", 30)

    db = load_db()
    if mt5_login not in db:
        return jsonify({"success": False, "msg": "License nahi mili"})

    old_expiry = datetime.strptime(db[mt5_login]["expiry"], "%Y-%m-%d")
    new_expiry = old_expiry + timedelta(days=days)
    db[mt5_login]["expiry"] = new_expiry.strftime("%Y-%m-%d")
    save_db(db)

    return jsonify({
        "success":    True,
        "mt5_login":  mt5_login,
        "new_expiry": db[mt5_login]["expiry"],
        "msg":        f"License {days} din extend ho gayi!"
    })


@app.route("/admin/block", methods=["POST"])
def block_license():
    """License band karo"""
    data = request.json
    if data.get("master_key") != MASTER_KEY:
        return jsonify({"success": False, "msg": "Wrong master key"})

    mt5_login = str(data["mt5_login"])
    db = load_db()
    if mt5_login not in db:
        return jsonify({"success": False, "msg": "License nahi mili"})

    db[mt5_login]["active"] = False
    save_db(db)
    return jsonify({"success": True, "msg": f"{mt5_login} block ho gaya!"})


@app.route("/admin/unblock", methods=["POST"])
def unblock_license():
    """License wapas on karo"""
    data = request.json
    if data.get("master_key") != MASTER_KEY:
        return jsonify({"success": False, "msg": "Wrong master key"})

    mt5_login = str(data["mt5_login"])
    db = load_db()
    if mt5_login not in db:
        return jsonify({"success": False, "msg": "License nahi mili"})

    db[mt5_login]["active"] = True
    save_db(db)
    return jsonify({"success": True, "msg": f"{mt5_login} unblock ho gaya!"})


@app.route("/admin/list", methods=["POST"])
def list_licenses():
    """Sab licenses dekho"""
    data = request.json
    if data.get("master_key") != MASTER_KEY:
        return jsonify({"success": False, "msg": "Wrong master key"})

    db = load_db()
    result = []
    for login, info in db.items():
        expiry    = datetime.strptime(info["expiry"], "%Y-%m-%d")
        days_left = (expiry - datetime.now()).days
        result.append({
            "mt5_login": login,
            "name":      info["name"],
            "key":       info["key"],
            "expiry":    info["expiry"],
            "days_left": days_left,
            "active":    info.get("active", True),
            "status":    "✅ Active" if info.get("active", True) and days_left > 0 else "❌ Expired/Blocked"
        })
    return jsonify({"success": True, "total": len(result), "licenses": result})


@app.route("/")
def home():
    return "Gold Signal Bot License Server — Running ✅"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
