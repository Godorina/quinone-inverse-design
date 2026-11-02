"""Make the XLSX-to-corpus status ledger without openpyxl or any classification."""
import argparse, csv, json, re, urllib.request, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

Q=Path(__file__).resolve().parents[1]; NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
OUT=Path(__file__).with_name('xlsx_status.csv'); ABS=Q/'data/abstracts_4b'
def norm(x): return re.sub(r'^https?://(?:dx\.)?doi\.org/','',x.strip().lower()).rstrip(' .;,')
def xrows(path=Q.parent.parent/'quinone'/'quinone_CO2_simulation_papers_2020-2026.xlsx'):
    # ponytail: XLSX is ZIP/XML here; avoid an extra spreadsheet dependency.
    with zipfile.ZipFile(path) as z:
        root=ET.fromstring(z.read('xl/worksheets/sheet1.xml')); rows=[]
        for row in root.findall('.//m:sheetData/m:row',NS):
            d={}
            for c in row.findall('m:c',NS):
                col=re.match('[A-Z]+',c.attrib['r']).group(0); d[col]=''.join(t.text or '' for t in c.findall('.//m:t',NS)) or c.findtext('m:v',default='',namespaces=NS)
            if d.get('H') and d.get('H') != 'DOI': rows.append(d)
    return rows
def fetch(doi):
    ABS.mkdir(exist_ok=True); p=ABS/(doi.replace('/','_')+'.json')
    if p.exists(): return p
    for url in (f'https://api.crossref.org/works/{doi}', f'https://api.openalex.org/works/https://doi.org/{doi}'):
        try:
            with urllib.request.urlopen(url,timeout=20) as r: p.write_bytes(r.read()); return p
        except Exception as error:
            last_error = f'{type(error).__name__}: {error}'
    return None, last_error
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('xlsx', nargs='?', type=Path, default=Q.parent.parent/'quinone'/'quinone_CO2_simulation_papers_2020-2026.xlsx'); args=parser.parse_args()
    master={norm(x['doi']) for x in json.loads((Q/'phase_3_corpus/master.json').read_text()) if x.get('doi')}
    labels={norm(x['doi']):x for x in json.loads((Q/'data/labeled_all.json').read_text()) if x.get('doi')}
    out=[]
    for x in xrows(args.xlsx):
        doi=norm(x['H']); tier=x.get('B','').split()[0]
        if doi in master: status,source,quote,page='matched','phase_3_corpus/master.json','',''
        elif doi in labels:
            v=labels[doi]; status={'on_topic':'added_on_topic','borderline':'borderline','off_topic':'out_of_scope','off_topic_auto':'out_of_scope'}.get(v.get('label'),'needs_judgment'); source=f"data/labeled_all.json: {v.get('reason','')}"; quote=v.get('abstract',''); page='Abstract'
        else:
            got=fetch(doi); p=got if isinstance(got,Path) else got[0]; error='' if isinstance(got,Path) else got[1]
            status='needs_judgment'; source=str(p.relative_to(Q)) if p else f'abstract_fetch_failed: {error}'; quote=''; page=''
        out.append({'doi':doi,'xlsx_tier':tier,'title':x.get('D',''),'status':status,'source':source,'quote':quote,'page_or_locator':page})
    assert len(out)==38 and len({x['doi'] for x in out})==38
    with OUT.open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=out[0]);w.writeheader();w.writerows(out)
if __name__=='__main__': main()
