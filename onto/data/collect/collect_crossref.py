import html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else "crossref"
CAP = 100
queries = ["quinone CO2 capture", "quinone carbon dioxide electrochemical", "quinone electro-swing carbon capture",
           "anthraquinone CO2 capture electrochemical", "redox-active quinone carbon dioxide binding"]
quinone = re.compile(r"quinon", re.I)
co2 = re.compile(r"CO2|CO\u2082|CO 2|carbon dioxide|carbon capture", re.I)
electro = re.compile(r"electrochem|redox|electrode|electro-swing", re.I)
capture = re.compile(r"captur|sorption|binding|adduct|separation", re.I)


def fetch(url):
    for wait in (2, 5, 15, 30, 60):
        try:
            return json.load(urllib.request.urlopen(url, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(wait)
    return json.load(urllib.request.urlopen(url, timeout=60))


def clean(abstract):
    return html.unescape(re.sub(r"<[^>]+>", " ", abstract or "")).strip()


def collect_year(year):
    merged = {}
    for q in queries:
        params = {"query": q, "filter": "from-pub-date:%d-01-01,until-pub-date:%d-12-31,type:journal-article" % (year, year),
                  "rows": 1000, "select": "DOI,title,abstract,container-title,author,issued,is-referenced-by-count",
                  "mailto": "research@example.com"}
        data = fetch("https://api.crossref.org/works?" + urllib.parse.urlencode(params))
        for w in data["message"]["items"]:
            title = " ".join(w.get("title") or [])
            abstract = clean(w.get("abstract"))
            text = title + " " + abstract
            doi = w["DOI"].lower()
            if not (quinone.search(text) and co2.search(text)):
                continue
            row = merged.setdefault(doi, {"title": title, "year": year, "doi": doi,
                                          "venue": " ".join(w.get("container-title") or []),
                                          "authors": [(a.get("given", "") + " " + a.get("family", "")).strip()
                                                      for a in w.get("author", [])][:8],
                                          "cited_by": w.get("is-referenced-by-count"),
                                          "has_abstract": bool(abstract),
                                          "electro_in_text": bool(electro.search(text)),
                                          "capture_in_text": bool(capture.search(text)),
                                          "matched_queries": [], "abstract": abstract})
            row["matched_queries"].append(q)
        time.sleep(1)
    return sorted(merged.values(), key=lambda r: (-(r["electro_in_text"] + r["capture_in_text"]), -(r["cited_by"] or 0)))


os.makedirs(OUT, exist_ok=True)
for year in range(2020, 2027):
    try:
        rows = collect_year(year)
    except urllib.error.URLError as e:
        print(year, "FAILED", e)
        continue
    json.dump(rows[:CAP], open(os.path.join(OUT, "crossref_%d.json" % year), "w"), ensure_ascii=False, indent=1)
    print(year, len(rows), min(len(rows), CAP), "abstract", sum(r["has_abstract"] for r in rows),
          "electro+capture", sum(r["electro_in_text"] and r["capture_in_text"] for r in rows))
