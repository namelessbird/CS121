"""
1) Find every .json file under the corpus folder (same order every time).
2) Open each file, read url + content from JSON.
3) Build a list: (0, page), (1, page), ... and write doc_ids.txt.
"""
import json
import os

# Cut "#..." off the end of a URL
def strip_url_fragment(url):
    if not url:
        return ""
    if "#" in url:
        return url.split("#", 1)[0]
    return url

# List every .json file under the corpus folder
def list_all_json_paths(corpus):
    root = os.path.abspath(str(corpus))
    paths = []

    if os.path.isfile(root) and root.lower().endswith(".json"):
        return [root]

    for folder, subfolders, files in os.walk(root):
        subfolders.sort()
        for filename in sorted(files):
            if filename.endswith(".json"):
                full_path = os.path.join(folder, filename)
                paths.append(full_path)

    return paths

# Read crawl JSON files into (doc_id, page dict), skip broken or empty pages
def collect_pages(corpus, limit=None):
    all_paths = list_all_json_paths(corpus)
    results = []
    doc_id = 0

    for path in all_paths:
        # Stop after we have enough pages (for --limit 50 tests)
        if limit is not None and len(results) >= limit:
            break

        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError:
            continue

        try:
            text = raw.decode("utf-8", errors="replace")
            record = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            continue

        url = record.get("url")
        content = record.get("content")

        if not url or content is None:
            continue

        if not isinstance(content, str):
            content = str(content)

        page = {
            "url": strip_url_fragment(str(url)),
            "content": content,
        }
        results.append((doc_id, page))
        doc_id = doc_id + 1

        # Prints every 5000 good pages
        if doc_id % 5000 == 0:
            print("  ... loaded", doc_id, "pages so far")
    
    return results

# Write doc_ids.txt (each line is doc_id, tab, URL)
def write_doc_ids(out, pages):
    os.makedirs(str(out), exist_ok=True)
 
    out_path = os.path.join(str(out), "doc_ids.txt")

    fh = open(out_path, "w", encoding="utf-8")
    for doc_id, page in pages:
        line = str(doc_id) + "\t" + page["url"] + "\n"
        fh.write(line)
    fh.close()

# Read doc_ids.txt. Returns a list: urls[doc_id] is that page's URL
def read_urls(index_dir):
    path = os.path.join(str(index_dir), "doc_ids.txt")
    urls = []
    fh = open(path, encoding="utf-8")
    for line in fh:
        line = line.rstrip("\r\n")
        if line == "":
            continue
        parts = line.split("\t", 1)
        doc_id = int(parts[0])
        url = parts[1] if len(parts) > 1 else ""
        while len(urls) <= doc_id:
            urls.append("")
        urls[doc_id] = url
    fh.close()
    return urls

# URL for this doc id, or None.
def get_url(urls, doc_id):
    if doc_id < 0 or doc_id >= len(urls):
        return None
    u = urls[doc_id]
    if u == "":
        return None
    return u
