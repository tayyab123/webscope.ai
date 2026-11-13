import json, io, csv
def export_report(data, fmt):
    fmt = fmt.lower()
    if fmt == "json":
        return json.dumps(data, indent=2, ensure_ascii=False).encode(), "application/json", "webscope-report.json"
    if fmt == "txt":
        lines = [f"WebScope AI Report: {data.get('url','')}", f"Title: {data.get('title','Not Found')}",
                 f"Description: {data.get('description','Not Found')}", f"Pages: {data.get('page_count',0)}"]
        for p in data.get("pages", []):
            lines += ["", p.get("url",""), p.get("title",""), p.get("text","")]
        return "\n".join(lines).encode(), "text/plain", "webscope-report.txt"
    if fmt in ("csv","xlsx"):
        rows = [{"url":p.get("url"),"title":p.get("title"),"description":p.get("description"),"status":p.get("status"),"text":p.get("text")} for p in data.get("pages",[])]
        import pandas as pd
        df = pd.DataFrame(rows)
        buf = io.BytesIO()
        if fmt == "csv":
            df.to_csv(buf, index=False)
            return buf.getvalue(), "text/csv", "webscope-pages.csv"
        df.to_excel(buf, index=False)
        return buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "webscope-pages.xlsx"
    if fmt == "pdf":
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        buf = io.BytesIO(); doc = SimpleDocTemplate(buf, pagesize=letter)
        styles = getSampleStyleSheet(); story = [Paragraph("WebScope AI Website Report", styles["Title"]), Spacer(1,12)]
        story.append(Paragraph(str(data.get("url","")), styles["Normal"]))
        story.append(Paragraph(str(data.get("description") or "Not Found"), styles["BodyText"]))
        for p in data.get("pages", []):
            story += [Spacer(1,10), Paragraph(str(p.get("title") or p.get("url")), styles["Heading2"]),
                      Paragraph(str(p.get("text",""))[:3500].replace("&","&amp;").replace("<","&lt;"), styles["BodyText"])]
        doc.build(story)
        return buf.getvalue(), "application/pdf", "webscope-report.pdf"
    raise ValueError("Unsupported export format.")
