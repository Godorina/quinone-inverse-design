import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
quinone = re.compile(r"quinon", re.I)
strict = re.compile(r"CO2|CO\u2082|CO 2|carbon dioxide", re.I)
related = re.compile(r"carbon capture|carbon sequestration|carboxylat|bicarbonate|carbonate|carbamate", re.I)
flt = ("from_publication_date:2020-01-01,to_publication_date:2026-12-31,type:article,has_doi:true,"
       "title_and_abstract.search:quinone|quinones|anthraquinone|benzoquinone|naphthoquinone|quinoid,"
       'title_and_abstract.search:CO2|"carbon dioxide"|"CO 2"|"carbon capture"|carboxylate|bicarbonate|carbonate|carbamate')
params = {"filter": flt, "sort": "cited_by_count:desc", "per-page": 200, "cursor": "*",
          "mailto": "research@example.com"}
if os.environ.get("OPENALEX_API_KEY"):
    params["api_key"] = os.environ["OPENALEX_API_KEY"]


def fetch(p):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(p)
    try:
        return json.load(urllib.request.urlopen(url, timeout=60))
    except urllib.error.HTTPError as e:
        sys.exit("HTTP %d: %s" % (e.code, e.read().decode()[:300]))


papers, seen = [], set()
while True:
    data = fetch(params)
    for w in data["results"]:
        inv = w.get("abstract_inverted_index") or {}
        pos = sorted((p, t) for t, ps in inv.items() for p in ps)
        abstract = " ".join(t for _, t in pos)
        text = (w["title"] or "") + " " + abstract
        direct = bool(strict.search(text))
        if w["id"] in seen or not quinone.search(text) or not (direct or related.search(text)):
            continue
        seen.add(w["id"])
        papers.append({"title": w["title"], "year": w["publication_year"], "doi": w.get("doi"),
                       "co2_mention": "direct" if direct else "related",
                       "cited_by": w.get("cited_by_count"),
                       "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                       "authors": [a["author"]["display_name"] for a in w.get("authorships", [])][:8],
                       "abstract": abstract})
    cursor = data["meta"].get("next_cursor")
    if not data["results"] or not cursor:
        break
    params["cursor"] = cursor
    time.sleep(1)

for name, keep in (("strict", lambda r: r["co2_mention"] == "direct"), ("relaxed", lambda r: True)):
    os.makedirs(os.path.join(OUT, name), exist_ok=True)
    for year in range(2020, 2027):
        rows = [r for r in papers if r["year"] == year and keep(r)]
        json.dump(rows, open(os.path.join(OUT, name, "%s_%d.json" % (name, year)), "w"), ensure_ascii=False, indent=1)
        print(name, year, len(rows))
print("total relaxed", len(papers), "strict", sum(r["co2_mention"] == "direct" for r in papers))
