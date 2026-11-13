from flask import Flask, render_template, request, jsonify, send_file
from config import Config
from database.db import init_db, save_report, list_reports, get_report, delete_report
from scraper.engine import scrape_website
from exporters.exporter import export_report
from analyzers.insights import analyze_report
from urllib.parse import urlparse
import json, io

app = Flask(__name__)
app.config.from_object(Config)
init_db()

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/scrape")
def scrape():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    options = data.get("options") or {}
    try:
        report = scrape_website(url, options)
        report["insights"] = analyze_report(report)
        report_id = save_report(url, report)
        report["id"] = report_id
        return jsonify({"ok": True, "report": report})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        app.logger.exception("Scrape failed")
        return jsonify({"ok": False, "error": "Scraping failed. Check the URL and try again."}), 500

@app.get("/api/history")
def history():
    return jsonify(list_reports())

@app.get("/api/reports/<int:report_id>")
def report(report_id):
    item = get_report(report_id)
    if not item:
        return jsonify({"error": "Report not found"}), 404
    return jsonify(item)

@app.delete("/api/reports/<int:report_id>")
def remove_report(report_id):
    delete_report(report_id)
    return jsonify({"ok": True})

@app.get("/api/export/<int:report_id>/<fmt>")
def export(report_id, fmt):
    item = get_report(report_id)
    if not item:
        return jsonify({"error": "Report not found"}), 404
    try:
        content, mimetype, filename = export_report(item["data"], fmt)
        return send_file(io.BytesIO(content), mimetype=mimetype, as_attachment=True, download_name=filename)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True, port=5000)
