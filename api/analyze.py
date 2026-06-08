import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, send_from_directory, abort

from engine import analyze_alignment
from graph import build_graph_figure


def _find_public():
    here = os.path.dirname(os.path.abspath(__file__))
    for c in [os.path.join(here, "..", "public"),
              os.path.join(os.getcwd(), "public"),
              "/var/task/public"]:
        if os.path.isdir(c):
            return os.path.abspath(c)
    return os.path.abspath(os.path.join(here, "..", "public"))


PUBLIC_DIR = _find_public()
app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.route("/<path:fname>")
def static_files(fname):
    if os.path.isfile(os.path.join(PUBLIC_DIR, fname)):
        return send_from_directory(PUBLIC_DIR, fname)
    abort(404)


def _clean_list(items):
    out = []
    for it in items or []:
        s = str(it).strip()
        if s:
            out.append(s[:120])
    return out[:12]  # cap at 12 each to keep the graph readable


@app.route("/api/analyze", methods=["POST"])
def analyze_endpoint():
    data = request.get_json(silent=True) or {}
    goals = _clean_list(data.get("goals"))
    habits = _clean_list(data.get("habits"))

    if len(goals) < 1:
        return jsonify({"detail": "Add at least one goal."}), 400
    if len(habits) < 1:
        return jsonify({"detail": "Add at least one habit."}), 400

    try:
        result = analyze_alignment(goals, habits)
        result["figure"] = build_graph_figure(result)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"detail": str(exc)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)
