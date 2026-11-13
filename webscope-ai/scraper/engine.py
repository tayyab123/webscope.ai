import requests, socket, ipaddress, re, time
from urllib.parse import urljoin, urlparse, urldefrag
from bs4 import BeautifulSoup
from collections import deque
from urllib.robotparser import RobotFileParser

UA = "WebScopeAI/1.0 (+responsible public website analysis)"
TIMEOUT = 12
MAX_BYTES = 2_000_000

def validate_url(url):
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ValueError("Enter a valid public http:// or https:// URL.")
    host = p.hostname.lower()
    if host in ("localhost",) or host.endswith(".local"):
        raise ValueError("Local and private network addresses are not allowed.")
    try:
        infos = socket.getaddrinfo(host, None)
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if not ip.is_global:
                raise ValueError("Private, local, and reserved IP addresses are blocked.")
    except socket.gaierror:
        raise ValueError("The domain could not be resolved.")
    return p

def safe_get(session, url):
    # Validate every destination and disable redirects so a public URL cannot redirect to an internal host.
    validate_url(url)
    r = session.get(url, timeout=TIMEOUT, allow_redirects=False, stream=True)
    if 300 <= r.status_code < 400:
        loc = r.headers.get("Location")
        r.close()
        if loc:
            target = urljoin(url, loc)
            validate_url(target)
            return session.get(target, timeout=TIMEOUT, allow_redirects=False)
    raw = r.raw.read(MAX_BYTES + 1, decode_content=True)
    r.close()
    if len(raw) > MAX_BYTES:
        raise ValueError("Page exceeds the 2 MB response limit.")
    r._content = raw
    return r

def scrape_website(start_url, options=None):
    options = options or {}
    start = validate_url(start_url)
    start_url = start.geturl()
    max_pages = max(1, min(int(options.get("max_pages", 10)), 30))
    max_depth = max(0, min(int(options.get("max_depth", 2)), 4))
    mode = options.get("mode", "multi")
    if mode == "single":
        max_pages, max_depth = 1, 0
    include = [x.strip() for x in options.get("include", "").splitlines() if x.strip()]
    exclude = [x.strip() for x in options.get("exclude", "").splitlines() if x.strip()]
    host = start.hostname.lower()
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    robots_allowed = True
    robots_url = f"{start.scheme}://{start.netloc}/robots.txt"
    try:
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rr = safe_get(session, robots_url)
        rp.parse(rr.text.splitlines())
        robots_allowed = rp.can_fetch(UA, start_url)
    except Exception:
        # If robots.txt is unavailable, proceed conservatively; the report records its availability.
        rp = None
    if not robots_allowed:
        raise ValueError("robots.txt disallows crawling this page for WebScope AI.")
    queue = deque([(start_url, 0)])
    seen, pages, all_links, images, emails, phones = set(), [], [], [], set(), set()
    robots_status = "Available" if rp else "Unavailable"
    while queue and len(pages) < max_pages:
        url, depth = queue.popleft()
        url, _ = urldefrag(url)
        if url in seen: continue
        seen.add(url)
        if any(x in url for x in exclude): continue
        if include and not any(x in url for x in include): continue
        try:
            if rp and not rp.can_fetch(UA, url): continue
            response = safe_get(session, url)
            ctype = response.headers.get("Content-Type", "")
            if response.status_code >= 400 or "text/html" not in ctype: continue
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "noscript", "svg"]): tag.decompose()
            title = soup.title.get_text(" ", strip=True) if soup.title else ""
            desc = (soup.find("meta", attrs={"name": re.compile("^description$", re.I)}) or {}).get("content", "")
            canonical = soup.find("link", rel="canonical")
            headings = {f"h{i}": [h.get_text(" ", strip=True) for h in soup.find_all(f"h{i}")] for i in range(1,7)}
            paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p") if p.get_text(" ", strip=True)]
            text = soup.get_text(" ", strip=True)
            text = re.sub(r"\s+", " ", text)[:25000]
            page_links = []
            for a in soup.find_all("a", href=True):
                target = urljoin(url, a["href"].strip())
                parsed = urlparse(target)
                if parsed.scheme not in ("http", "https"): continue
                item = {"url": target, "text": a.get_text(" ", strip=True)[:200],
                        "type": "internal" if parsed.hostname and parsed.hostname.lower() == host else "external"}
                page_links.append(item); all_links.append(item)
                if item["type"] == "internal" and depth < max_depth and len(seen)+len(queue) < max_pages*4:
                    clean, _ = urldefrag(target)
                    if clean not in seen: queue.append((clean, depth+1))
            for img in soup.find_all("img", src=True):
                images.append({"url": urljoin(url, img["src"]), "alt": img.get("alt", "")})
            emails.update(re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I))
            phones.update(re.findall(r"(?:\+?\d[\d\s().-]{7,}\d)", text))
            pages.append({
                "url": url, "status": response.status_code, "title": title, "description": desc,
                "canonical": canonical.get("href") if canonical else "",
                "language": (soup.html.get("lang") if soup.html else "") or "",
                "robots_meta": (soup.find("meta", attrs={"name": re.compile("^robots$", re.I)}) or {}).get("content", ""),
                "headings": headings, "paragraphs": paragraphs[:100], "text": text,
                "links": page_links, "images": []
            })
            pages[-1]["images"] = [x for x in images if x["url"]]
            time.sleep(0.35)
        except ValueError:
            raise
        except Exception:
            continue
    if not pages:
        raise ValueError("No accessible HTML pages were extracted. Check the URL and robots.txt.")
    first = pages[0]
    full_text = " ".join(p["text"] for p in pages)
    category = "E-commerce" if re.search(r"cart|add to cart|product", full_text, re.I) else \
               "Blog / News" if re.search(r"article|blog|published", full_text, re.I) else "General website"
    social = sorted({x["url"] for x in all_links if any(s in x["url"].lower() for s in ["facebook.com","instagram.com","linkedin.com","x.com","twitter.com","youtube.com"])})
    return {
        "url": start_url, "name": first["title"] or start.hostname, "title": first["title"],
        "description": first["description"], "category": category, "pages": pages,
        "page_count": len(pages), "links": all_links, "images": images[:500],
        "contacts": {"emails": sorted(emails), "phones": sorted(phones), "social_links": social},
        "technical": {"robots_txt": robots_status, "http_status": first["status"],
                      "language": first["language"], "canonical": first["canonical"],
                      "robots_meta": first["robots_meta"]},
        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }
