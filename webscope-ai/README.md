# WebScope AI

A Flask-based starter implementation of a responsible public-website intelligence dashboard.

## Features
- Responsive Bootstrap 5 SaaS dashboard with dark/light theme
- URL validation, public-IP checks, bounded page crawling and robots.txt checks
- Extracts page titles, descriptions, headings, paragraphs, links, images, contact-like text and basic technical metadata
- Heuristic website insights (clearly labeled; not a hosted LLM integration)
- SQLite report history: save, open and delete
- JSON, CSV, XLSX, TXT and PDF exports

## Quick start

Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Configuration
Set `SECRET_KEY` and optionally `WEBSCOPE_DB` as environment variables. The default database is `webscope.sqlite3` in the project directory.

## Important limitations / production checklist
This is a runnable MVP, not a hardened multi-tenant commercial deployment. It intentionally does not bypass authentication, paywalls, CAPTCHAs or bot protections. It does not crawl PDFs or run a browser engine for JavaScript-heavy websites. Selenium/Playwright are not enabled in this baseline. AI insights are heuristic and no external AI API key is required.

Before internet-facing production use:
- Run behind a production WSGI server and HTTPS; disable Flask debug mode.
- Add authentication, authorization, CSRF protection, per-user quotas and robust rate limiting.
- Add a dedicated egress proxy/firewall that blocks private/reserved IP ranges at connection time, revalidates DNS on every redirect/connection, and guards against DNS rebinding. Application-level DNS checks alone are not a complete SSRF defense.
- Add a background job queue, crawl concurrency controls, observability and retention policies.
- Review each target site's terms, robots.txt and applicable law. Respect crawl delays and stop on access-denied responses.
- Integrate a selected AI provider through environment-based secrets and send only content users are authorized to process.
- Add structured product/service extraction (JSON-LD, OpenGraph, schema.org) and optional Playwright rendering with the same network isolation controls.

## Project structure

```text
webscope-ai/
  app.py, config.py, requirements.txt
  scraper/       crawler and extraction engine
  analyzers/     website intelligence
  database/      SQLite persistence
  exporters/     JSON, CSV, Excel, TXT, PDF
  templates/     Bootstrap UI
  static/css/    styles
  static/js/     interactions
```
