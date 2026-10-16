"""Versioned, ordered identity permutations. Never infer identities from jumps."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
import numpy as np

SCHEMA = 'beetle-identity-corrections-v1'
VERSION = '0.3.0'

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def load_bundle(bundle):
    bundle=Path(bundle);m=json.loads((bundle/'manifest.json').read_text())
    state=bundle/'canonical_states.npz'
    if sha256(state)!=m.get('output_sha256',{}).get(state.name):
        raise ValueError('Source state hash does not match manifest')
    with np.load(state,allow_pickle=False) as z:raw=z['raw'].copy()
    if raw.ndim!=3 or raw.shape[2]!=2 or raw.shape[1]<2:raise ValueError('Invalid raw shape')
    start=int(m['settings']['start'])
    identity=dict(schema=SCHEMA,analysis_manifest_sha256=sha256(bundle/'manifest.json'),
                  canonical_sha256=sha256(state),frame_start=start,
                  frame_end_inclusive=start+len(raw)-1,animal_count=raw.shape[1])
    return m,raw,identity

def replay(raw, identity, log):
    for k,v in identity.items():
        if log.get(k)!=v:raise ValueError('Correction log does not match source: '+k)
    if not isinstance(log.get('decisions'),list):raise ValueError('Decisions must be a list')
    result=raw.copy();mapping=np.tile(np.arange(raw.shape[1]),(len(raw),1))
    seen=set()
    for d in log['decisions']:
        if not isinstance(d,dict):raise ValueError('Invalid correction')
        for k in ['id','reviewer','reason','created_utc']:
            if not isinstance(d.get(k),str) or not d[k].strip():raise ValueError('Missing '+k)
        if d['id'] in seen:raise ValueError('Duplicate correction ID')
        seen.add(d['id'])
        if d.get('kind') not in {'swap','pscp'}:raise ValueError('Unsupported correction kind')
        a,b,lo,hi,anchor=[d.get(k) for k in ['animal_a','animal_b','start_frame','end_frame_inclusive','anchor_frame']]
        if any(type(n) is not int for n in [a,b,lo,hi,anchor]):raise ValueError('IDs and frames must be integers')
        if not 0<=a<raw.shape[1] or not 0<=b<raw.shape[1] or a==b:raise ValueError('Invalid swap identities')
        if not identity['frame_start']<=lo<=anchor<=hi<=identity['frame_end_inclusive']:raise ValueError('Invalid inclusive interval or anchor')
        if d['kind']=='pscp':
            if d.get('mode') not in {'partner','unresolved'}:raise ValueError('Invalid PSC mode')
            continue
        lo-=identity['frame_start'];hi=hi-identity['frame_start']+1
        # Swap BOTH channels, including NaNs. Do not duplicate a detection or fill a gap.
        result[lo:hi,[a,b]]=result[lo:hi,[b,a]].copy()
        mapping[lo:hi,[a,b]]=mapping[lo:hi,[b,a]].copy()
    # Human PSC is a separate inferred layer, evaluated after all ID swaps.
    psc_layer(result,identity,log)
    return result,mapping

def psc_layer(corrected,identity,log):
    positions=corrected.copy();source=np.where(np.isfinite(corrected).all(2),'ASSIGNED','MISSING').astype('<U24')
    for d in log['decisions']:
        if d['kind']!='pscp':continue
        a,b=d['animal_a'],d['animal_b'];lo=d['start_frame']-identity['frame_start'];hi=d['end_frame_inclusive']-identity['frame_start']+1
        if np.isfinite(corrected[lo:hi,a]).all(1).any():raise ValueError('PSC requires a missing ID throughout the interval; preserve detected identities')
        if d['mode']=='partner':
            if not np.isfinite(corrected[lo:hi,b]).all():raise ValueError('PSC partner must be detected throughout the interval')
            positions[lo:hi,a]=corrected[lo:hi,b];source[lo:hi,a]='HUMAN_PSCP'
        else:
            positions[lo:hi,a]=np.nan;source[lo:hi,a]='HUMAN_UNRESOLVED'
    return positions,source

def bind_psc_review(correction_output,new_bundle):
    """Bind PSC decisions only after the corrected raw input was reprocessed."""
    root=Path(correction_output);receipt=json.loads((root/'IDENTITY_CORRECTION_RECEIPT.json').read_text())
    for name in ['identity_corrected_window.npz','identity_corrections.json']:
        if sha256(root/name)!=receipt['output_sha256'][name]:raise ValueError('Correction output changed')
    log=json.loads((root/'identity_corrections.json').read_text())
    _,raw,identity=load_bundle(new_bundle)
    with np.load(root/'identity_corrected_window.npz') as z:expected=z['corrected']
    if identity['frame_start']!=log['frame_start'] or raw.shape!=expected.shape or not np.array_equal(raw,expected,equal_nan=True):raise ValueError('Reprocessed bundle does not contain this corrected trajectory window')
    psc_layer(raw,identity,log)
    decisions=[dict(created_utc=d['created_utc'],reviewer=d['reviewer'],reason=d['reason'],kind='pscp',
                    value='yes' if d['mode']=='partner' else 'unresolved',animal_id=d['animal_a'],partner_id=d['animal_b'],
                    start_frame=d['start_frame'],end_frame_inclusive=d['end_frame_inclusive']) for d in log['decisions'] if d['kind']=='pscp']
    return dict(schema='beetle-review-v1',analysis_manifest_sha256=identity['analysis_manifest_sha256'],
                canonical_sha256=identity['canonical_sha256'],frame_start=identity['frame_start'],frame_end_inclusive=identity['frame_end_inclusive'],decisions=decisions)

def jump_events(raw,start,threshold=100.):
    if not np.isfinite(threshold) or threshold<=0:raise ValueError('Invalid threshold')
    delta=np.linalg.norm(np.diff(raw,axis=0),axis=2)
    return [dict(kind='adjacent_jump',frame=int(i+start+1),animal=int(a),
                 previous_frame=int(i+start),distance_px=float(delta[i,a]))
            for i,a in np.argwhere(delta>threshold)]

def apply(bundle,log,output,trajectory=None):
    """Write a new correction layer; optionally a full-length pipeline input.

    Full NPY contains coordinates only: ID-indexed confidence metadata from the
    original is deliberately not copied with stale identity ordering.
    """
    m,raw,identity=load_bundle(bundle);corrected,mapping=replay(raw,identity,log)
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing existing output')
    full=None
    if trajectory:
        from processor import load_trajectories
        trajectory=Path(trajectory)
        expected=m.get('input_sha256',{}).get(m.get('trajectory_file'))
        if not expected or sha256(trajectory)!=expected:raise ValueError('Full source trajectory hash mismatch')
        full=load_trajectories(trajectory).copy();lo=identity['frame_start'];hi=identity['frame_end_inclusive']+1
        if full[lo:hi].shape!=raw.shape or not np.array_equal(full[lo:hi],raw,equal_nan=True):raise ValueError('Window is not identical to original input')
        full[lo:hi]=corrected
    output.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.identity-correction-',dir=output.parent))
    try:
        human_psc,human_source=psc_layer(corrected,identity,log)
        np.savez_compressed(staging/'identity_corrected_window.npz',original_raw=raw,
                            corrected=corrected,human_psc_positions=human_psc,human_psc_source=human_source,
                            original_identity=mapping,global_frames=np.arange(identity['frame_start'],identity['frame_end_inclusive']+1))
        (staging/'identity_corrections.json').write_text(json.dumps(log,indent=2)+'\n')
        with (staging/'identity_mapping.csv').open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['global_frame','corrected_id','original_id','original_x','original_y','corrected_x','corrected_y'])
            for t in range(len(raw)):
                for a in range(raw.shape[1]):
                    if mapping[t,a]!=a:w.writerow([t+identity['frame_start'],a,int(mapping[t,a]),*raw[t,a],*corrected[t,a]])
        if full is not None:np.save(staging/'human_corrected_trajectories.npy',full,allow_pickle=False)
        receipt=dict(schema=SCHEMA,corrector_version=VERSION,status='HUMAN_CORRECTED_NEEDS_REPROCESSING',
                     source_bundle=str(Path(bundle).resolve()),source_identity=identity,decision_count=len(log['decisions']),
                     original_trajectory=m.get('trajectory_file'),original_trajectory_sha256=m.get('input_sha256',{}).get(m.get('trajectory_file')),
                     corrected_full_trajectory=full is not None,
                     identity_swap_count=sum(d['kind']=='swap' for d in log['decisions']),
                     human_psc_count=sum(d['kind']=='pscp' for d in log['decisions']),
                     operation='Identity swaps first; human PSC kept separate and rebound after reprocessing. No interpolation or identity training.',
                     output_sha256={p.name:sha256(p) for p in staging.iterdir()})
        (staging/'IDENTITY_CORRECTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
        os.rename(staging,output)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True);p.add_argument('--log');p.add_argument('--output',required=True);p.add_argument('--trajectory',help='Original full trajectory, verified by hash; writes full corrected input for reprocessing')
    p.add_argument('--bind-psc-from',help='After reprocessing: correction output folder to bind to --bundle; --output is a new PSC review JSON')
    a=p.parse_args()
    if a.bind_psc_from:
        if a.log or a.trajectory:p.error('Binding PSC does not accept --log or --trajectory')
        review=bind_psc_review(a.bind_psc_from,a.bundle)
        with Path(a.output).open('x') as f:f.write(json.dumps(review,indent=2)+'\n')
        print(a.output)
    else:
        if not a.log:p.error('--log is required when applying corrections')
        print(apply(a.bundle,json.loads(Path(a.log).read_text()),a.output,a.trajectory))
