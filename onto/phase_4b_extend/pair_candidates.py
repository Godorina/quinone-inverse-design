"""List same-paper, same-compound MeCN potential/binding candidates for human review."""
import csv,json
from pathlib import Path
Q=Path(__file__).resolve().parents[1]; REC=Q/'phase_4_extract/records_final'; OUT=Path(__file__).with_name('pair_review.csv')
POT={'ReductionPotential','HalfWavePotential'}; BIND={'Log10BindingConstant','BindingConstant','BindingEnergy'}
FIELDS='paper_id compound potential_property potential_value unit ref_electrode redox_couple potential_quote potential_page binding_property binding_value binding_unit binding_quote binding_page basis method same_condition_key co2_standard_state flags reviewer_verdict reviewer_note'.split()
def pair_rows(d):
 # ponytail: retain ambiguous condition pairs for human review instead of inventing conversion logic.
 rows=[]; cond={x['key']:x for x in d.get('conditions',[])}
 for a in d.get('measurements',[]):
  if a['property'] not in POT or cond.get(a['condition'],{}).get('solvent')!='Acetonitrile': continue
  for b in d.get('measurements',[]):
   if b['compound']==a['compound'] and b['property'] in BIND and cond.get(b['condition'],{}).get('solvent')=='Acetonitrile':
    c=cond[a['condition']]; flags=[]
    if c.get('reference_electrode')!='FcFcPlus': flags.append('ref_not_fc')
    if b['property'] in {'BindingEnergy','DeltaGBinding'} and b.get('basis')=='Experiment' and b.get('method') in {'CyclicVoltammetry','Voltammetry'}: flags.append('basis_suspect')
    if a['condition']!=b['condition']: flags.append('diff_condition_key')
    rows.append(dict(zip(FIELDS,[d['paper_id'],a['compound'],a['property'],a['value'],a['unit'],c['reference_electrode'],a.get('redox_couple') or '',a['quote'],a.get('page',''),b['property'],b['value'],b['unit'],b['quote'],b.get('page',''),b['basis'],b['method'],a['condition']==b['condition'],'',';'.join(flags),'',''])))
 return rows
def main():
 rows=[]
 for p in sorted(REC.glob('*.json')):
  d=json.loads(p.read_text()); rows += pair_rows(d)
 with OUT.open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
if __name__=='__main__':main()
