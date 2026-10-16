"""Add a new QC dashboard over existing 25 dyadic packages without modifying them."""
from pathlib import Path
import argparse,hashlib,html,json,os
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import dyadic_turtling_qc as posture
import unified_qc

def build_one(args):
    source,out,row=args;name=row['run'];src=source/'runs'/name;dst=out/'runs'/name
    rm=json.loads((src/'review/source_manifest.json').read_text());canonical=src/'analysis/canonical_states.npz'
    digest=hashlib.sha256(canonical.read_bytes()).hexdigest()
    if digest!=rm['canonical_sha256']:raise ValueError('Canonical hash mismatch: '+name)
    with np.load(canonical) as data:raw=data['raw'].copy()
    assert raw.shape==(row['frames'],2,2)
    viewer=src/'review'/rm['html'];assert viewer.is_file()
    assert (src/'review'/rm['video']).is_file()
    link=os.path.relpath(viewer,dst)
    result=posture.summarize(raw.tolist(),row['first_global_frame'],rm['fps'])
    result['source']=dict(run=name,canonical_sha256=digest,source_toml=rm['source_toml'])
    receipt=posture.write_report(dst,result,raw.tolist(),link)
    scan=dict(status='NOT_ASSESSED',reason='Existing tracking-only QC replay; no new recording-disturbance scan performed.')
    general=unified_qc.summarize(raw,row['first_global_frame'],rm['fps'],video_scan=scan)
    general['source']=dict(video=rm['video_source'],canonical_sha256=digest)
    general['existing_review_reports']=['dyadic_turtling_qc.html',os.path.relpath(src/'START_HERE.html',dst)]
    general['dyadic_turtling_candidates']=receipt
    unified_qc.write_report(dst,general,raw,scan,link)
    return dict(row,posture_candidate_bouts=len(result['events']),posture_candidate_frames=sum(a['candidate_frames'] for a in result['per_id']),posture_status=result['status'],canonical_sha256=digest)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path('outputs/psc_review_qc_20261005'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.source=a.source.resolve();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
    rows=[r for r in json.loads((a.source/'QC_RUN_INDEX.json').read_text()) if r['collection']=='dyadic'];assert len(rows)==25
    results=[]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for row in pool.map(build_one,[(a.source,a.output,r) for r in rows]):
            results.append(row);print(row['run'],row['posture_candidate_bouts'],flush=True)
    results.sort(key=lambda r:(-r['raw_jumps_over_100'],-r['posture_candidate_bouts'],r['run']))
    body='<h1>25 dyadic runs — tracking and possible-turtling QC</h1><p>PSC 1.6.0 / processor 0.8.2-group. Original analysis unchanged. <b>Review hypotheses, not confirmed errors or posture.</b></p><p>'+posture.POLICY+'</p><p>Open General QC for tracking traces, missingness and jumps, or Turtling QC for candidate intervals and synchronized video. Recording disturbances were not rescanned. The image classifier is not used.</p><input id="search" placeholder="Filter video or cell" aria-label="Filter runs"><table><thead><tr><th>Video / TOML cell</th><th>Jumps &gt;100 px</th><th>Raw missing %</th><th>Possible-turtling bouts</th><th>Review</th></tr></thead><tbody>'
    for r in results:
        base='runs/'+r['run']+'/'
        body+='<tr><td>'+html.escape(r['run'])+'</td><td>'+str(r['raw_jumps_over_100'])+'</td><td>'+str(r['raw_missing_percent'])+'</td><td>'+str(r['posture_candidate_bouts'])+'</td><td><a href="'+base+'unified_qc.html">General QC + traces</a><br><a href="'+base+'dyadic_turtling_qc.html">Turtling QC + video</a></td></tr>'
    body+='</tbody></table><script>document.getElementById("search").oninput=function(){for(const r of document.querySelectorAll("tbody tr"))r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase())}</script>'
    (a.output/'START_HERE.html').write_text('<!doctype html><meta charset="utf-8"><title>Dyadic QC — 25 runs</title><style>body{font:16px system-ui;margin:30px;line-height:1.5;background:#f3f7f8}table{border-collapse:collapse;background:white}td,th{border:1px solid #ccd;padding:10px;text-align:left}td:first-child{max-width:540px;overflow-wrap:anywhere}input{padding:12px;font:inherit}a{color:#086078}</style>'+body)
    (a.output/'QC_RUN_INDEX.json').write_text(json.dumps(results,indent=2))
    (a.output/'RECEIPT.json').write_text(json.dumps(dict(status='COMPLETE_UNREVIEWED',runs=len(results),posture_version=posture.VERSION,screen_version=posture.SCREEN_VERSION,source=str(a.source),candidate_bouts=sum(r['posture_candidate_bouts'] for r in results),note='Local dashboard depends on unchanged sibling source packages. Not a portable download bundle.',code_sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['dyadic_turtling_qc.py','dyadic_turtling_experiment.py','unified_qc.py','build_dyadic_turtling_qc_dashboard.py']}),indent=2))
if __name__=='__main__':main()
