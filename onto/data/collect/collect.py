import json, re, sys, time, urllib.error, urllib.request, urllib.parse
N = 50


def fetch(url):
    for wait in (2, 5, 15, 30, 60):
        try:
            return json.load(urllib.request.urlopen(url, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(wait)
    return json.load(urllib.request.urlopen(url, timeout=60))

mode = sys.argv[1]
quinone = re.compile(r"quinon", re.I)
strict = re.compile(r"CO2|CO\u2082|CO 2|carbon dioxide", re.I)
relaxed = re.compile(r"carbon capture|CO2 capture|carbon sequestration|carboxylat|bicarbonate|carbonate|carbamate|\bCO\b", re.I)
co2_terms = {"strict": 'CO2|"carbon dioxide"|"CO 2"',
             "relaxed": 'CO2|"carbon dioxide"|"CO 2"|"carbon capture"|carboxylate|bicarbonate|carbonate|carbamate'}[mode]
terms = ("title_and_abstract.search:quinone|quinones|anthraquinone|benzoquinone|naphthoquinone|quinoid,"
         "title_and_abstract.search:" + co2_terms)
accept = (lambda t: strict.search(t)) if mode == "strict" else (lambda t: strict.search(t) or relaxed.search(t))
for year in map(int, sys.argv[2:]):
    kept, seen = [], set()
    for page in range(1, 4):
        q = {"filter": "publication_year:%d,type:article,has_doi:true,%s" % (year, terms),
             "sort": "cited_by_count:desc", "per-page": 200, "page": page, "mailto": "research@example.com"}
        results = fetch("https://api.openalex.org/works?" + urllib.parse.urlencode(q))["results"]
        time.sleep(1)
        for w in results:
            inv = w.get("abstract_inverted_index") or {}
            pos = sorted((p, t) for t, ps in inv.items() for p in ps)
            abstract = " ".join(t for _, t in pos)
            text = (w["title"] or "") + " " + abstract
            if w["id"] in seen or not (quinone.search(text) and accept(text)):
                continue
            seen.add(w["id"])
            kept.append({"title": w["title"], "year": w["publication_year"], "doi": w.get("doi"),
                         "co2_mention": "direct" if strict.search(text) else "related",
                         "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                         "authors": [a["author"]["display_name"] for a in w.get("authorships", [])][:8],
                         "abstract": abstract})
    json.dump(kept[:N], open("%s_%d.json" % (mode, year), "w"), ensure_ascii=False, indent=1)
    print(mode, year, len(kept), min(len(kept), N))
