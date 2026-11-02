import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request


def fetch(url):
    for wait in (2, 5, 15, 30, 60):
        try:
            return json.load(urllib.request.urlopen(url, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(wait)
    return json.load(urllib.request.urlopen(url, timeout=60))


OUT = sys.argv[1] if len(sys.argv) > 1 else "europepmc"
CAP = 100
Q = '(TITLE:quinone* OR ABSTRACT:quinone*)'
C = ('(TITLE:"CO2" OR ABSTRACT:"CO2" OR TITLE:"carbon dioxide" OR ABSTRACT:"carbon dioxide" OR '
     'TITLE:"carbon capture" OR ABSTRACT:"carbon capture")')
E = ('(TITLE:electrochem* OR ABSTRACT:electrochem* OR TITLE:redox OR ABSTRACT:redox OR '
     'TITLE:electrode* OR ABSTRACT:electrode* OR TITLE:electro-swing OR ABSTRACT:electro-swing)')
conditions = {
    "A_tiabs_quinone_co2_electro": "%s AND %s AND %s" % (Q, C, E),
    "B_tiabs_quinone_co2": "%s AND %s" % (Q, C),
    "C_tiabs_quinone_capture_co2": '%s AND (TITLE:capture OR ABSTRACT:capture) AND %s' % (Q, C),
    "D_fulltext_quinone_capture_electro":
        'quinone AND ("CO2 capture" OR "carbon dioxide capture" OR "carbon capture") AND electrochemical',
}
quinone = re.compile(r"quinon", re.I)
co2 = re.compile(r"CO2|CO\u2082|CO 2|carbon dioxide|carbon capture", re.I)
os.makedirs(OUT, exist_ok=True)
def collect_year(year):
    merged = {}
    for name, query in conditions.items():
        params = {"query": "%s AND PUB_YEAR:%d" % (query, year), "format": "json", "resultType": "core",
                  "pageSize": 100, "cursorMark": "*"}
        while True:
            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(params)
            data = fetch(url)
            results = data.get("resultList", {}).get("result", [])
            for r in results:
                key = (r.get("doi") or r.get("id") or "").lower()
                text = (r.get("title") or "") + " " + (r.get("abstractText") or "")
                if key not in merged:
                    merged[key] = {"title": r.get("title"), "year": int(r["pubYear"]), "doi": r.get("doi"),
                                   "pmid": r.get("pmid"), "pmcid": r.get("pmcid"), "source": r.get("source"),
                                   "venue": r.get("journalTitle"), "authors": r.get("authorString"),
                                   "open_access": r.get("isOpenAccess") == "Y",
                                   "quinone_in_title_abstract": bool(quinone.search(text)),
                                   "co2_in_title_abstract": bool(co2.search(text)),
                                   "matched": [], "abstract": r.get("abstractText")}
                merged[key]["matched"].append(name)
            nxt = data.get("nextCursorMark")
            if not results or not nxt or nxt == params["cursorMark"]:
                break
            params["cursorMark"] = nxt
            time.sleep(0.4)
    return sorted(merged.values(), key=lambda r: (-len(r["matched"]), r["title"] or ""))


for year in range(2020, 2027):
    try:
        rows = collect_year(year)
    except urllib.error.URLError as e:
        print(year, "FAILED", e)
        continue
    json.dump(rows[:CAP], open(os.path.join(OUT, "epmc_%d.json" % year), "w"), ensure_ascii=False, indent=1)
    print(year, len(rows), min(len(rows), CAP),
          "tiabs", sum(r["quinone_in_title_abstract"] and r["co2_in_title_abstract"] for r in rows))
