import re
from collections import Counter

def analyze_report(report):
    pages = report.get("pages", [])
    text = " ".join(p.get("text", "") for p in pages)
    words = re.findall(r"[A-Za-z][A-Za-z'-]{3,}", text.lower())
    common = [w for w, _ in Counter(words).most_common(12)
              if w not in {"this","that","with","from","your","have","will","more","about","their","there","which","what"}][:8]
    summaries = []
    for p in pages[:5]:
        sentences = re.split(r"(?<=[.!?])\s+", p.get("text",""))
        summaries.append({"page": p["url"], "summary": " ".join(sentences[:2])[:450] or "Not Found"})
    return {
        "summary": (report.get("description") or (pages[0].get("text","")[:500] if pages else "") or "Not Found"),
        "purpose": "Likely related to " + report.get("category", "website") + " based on publicly visible page content.",
        "keywords": common or ["Not Found"],
        "page_summaries": summaries,
        "faq": [
            {"question": "What is this website about?", "answer": report.get("description") or "Not Found"},
            {"question": "How can visitors contact the website?", "answer": ", ".join(report["contacts"]["emails"]) or "Not Found"}
        ],
        "limitations": ["AI-generated interpretation is heuristic in this starter edition.",
                        "Business model, target audience, and pricing are reported only when clearly present in extracted content."]
    }
