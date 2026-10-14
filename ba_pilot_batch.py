#!/usr/bin/env python3
"""Process eligible preselected pilot runs; retain blocked cases and QC index."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def run(root):
    inventory=json.loads((root/'inventory.json').read_text())
    selected={r['toml']:r for r in inventory['rows'] if r['toml'] in inventory['pilot_tomls']}
    records=[]
    for index,toml in enumerate(inventory['pilot_tomls'],1):
        row=selected[toml];label=Path(toml).stem
        record=dict(sample_index=index,label=label,toml=toml,video=row.get('video'),status='BLOCKED',flags=row['flags'],output='')
        eligible=[s for s in row.get('sessions',[]) if s['covers_window'] and not s['settings_differences']]
        if row['flags'] or len(eligible)!=1:
            record['reason']='; '.join(row['flags']) or 'No unique eligible session'
        else:
            session=eligible[0]
            try:
                for name,path,expected in [('TOML',Path(toml),row['toml_sha256']),('session',Path(session['session'])/'session.json',session['session_sha256'])]:
                    if sha(path)!=expected:raise RuntimeError(name+' changed since inventory')
                destination=root/'runs'/label
                command=[sys.executable,str(Path(__file__).with_name('run_ba_pipeline.py')),'--toml',toml,
                    '--session',session['session'],'--trajectory',session['trajectory'],'--output',str(destination),
                    '--ffmpeg','/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg',
                    '--ffprobe','/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe']
                log=root/'logs'/(label+'.log');log.parent.mkdir(exist_ok=True)
                with log.open('x') as stream:subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,check=True)
                manifest=json.loads((destination/'manifest.json').read_text())
                for name,expected in manifest['output_sha256'].items():
                    if sha(destination/name)!=expected:raise RuntimeError('Output hash mismatch: '+name)
                qc=json.loads((destination/'qc.json').read_text())
                record.update(status='COMPLETE_UNREVIEWED',flags=qc['flags'],output=str(destination),metrics=qc['metrics'])
                archive=root/'individual_run_zips'/(label+'.zip');archive.parent.mkdir(exist_ok=True)
                with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
                    for path in sorted(destination.iterdir()):z.write(path,arcname=label+'/'+path.name)
                with zipfile.ZipFile(archive) as z:
                    if z.testzip() is not None:raise RuntimeError('ZIP integrity check failed')
                record.update(zip=str(archive),zip_sha256=sha(archive))
            except Exception as exc:
                record.update(status='FAILED',reason=str(exc))
        records.append(record)
        (root/'PILOT_STATUS.json').write_text(json.dumps(records,indent=2)+'\n')
        print(record['label'],record['status'],flush=True)
    with (root/'QC_INDEX.csv').open('w',newline='') as stream:
        fields=['sample_index','label','status','flags','reason','output','video','toml','missing_fraction','longest_missing_frames','rejected_jump_fraction','outside_arena_fraction','exact_stationary_run_frames']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for r in records:
            data={**r,**r.get('metrics',{}),'flags':'; '.join(r['flags'])}
            writer.writerow({k:data.get(k,'') for k in fields})
    (root/'RELEASE_RECEIPT.json').write_text(json.dumps(dict(schema='ba-pilot-release-v1',qc_status='UNREVIEWED',created_utc=datetime.now(timezone.utc).isoformat(),seed=inventory['seed'],sampling=inventory['sampling'],selected=len(records),complete=sum(r['status']=='COMPLETE_UNREVIEWED' for r in records),blocked=sum(r['status']=='BLOCKED' for r in records),failed=sum(r['status']=='FAILED' for r in records),inventory_sha256=sha(root/'inventory.json'),runs=records),indent=2)+'\n')
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();run(a.root)
