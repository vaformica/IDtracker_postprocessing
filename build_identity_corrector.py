"""Build an offline click-based identity editor from an immutable review bundle."""
from pathlib import Path
import argparse
import csv
import json
import os
import shutil
import tempfile
import numpy as np
from identity_corrections import VERSION,load_bundle,sha256,jump_events

def build(bundle,review,output,initial_frame=None):
    bundle,review,output=map(Path,(bundle,review,output))
    if output.exists():raise FileExistsError(output)
    meta,raw,identity=load_bundle(bundle)
    rm=json.loads((review/'source_manifest.json').read_text())
    if rm['analysis_manifest_sha256']!=identity['analysis_manifest_sha256'] or rm['canonical_sha256']!=identity['canonical_sha256']:raise ValueError('Video review belongs to different analysis')
    name=rm['video']
    if Path(name).name!=name:raise ValueError('Video filename must be plain')
    video=review/name
    if sha256(video)!=rm['copied_video_sha256']:raise ValueError('Video hash mismatch')
    geometry=rm['video_geometry']
    if geometry['rotation_cw'] not in [0,90,180,270] or geometry['canvas_width']!=1280 or geometry['canvas_height']!=920:raise ValueError('Unsupported geometry')
    initial_frame=identity['frame_start'] if initial_frame is None else initial_frame
    if not identity['frame_start']<=initial_frame<=identity['frame_end_inclusive']:raise ValueError('Initial frame outside window')
    label=rm['label']
    if Path(label).name!=label:raise ValueError('Label must be a plain filename stem')
    def clean(x):
        if isinstance(x,list):return [clean(v) for v in x]
        return x if np.isfinite(x) else None
    data=dict(version=VERSION,identity=identity,label=label,raw=clean(raw.tolist()),geometry=geometry,
              video=name,fps=rm['fps'],initial_frame=initial_frame)
    here=Path(__file__).parent;template=(here/'identity_corrector_template.html').read_text()
    for token,value in [('__DATA__',json.dumps(data,separators=(',',':'),allow_nan=False).replace('<','\\u003c')),
                        ('__CORE__',(here/'identity_corrector_core.js').read_text()),
                        ('__UI__',(here/'identity_corrector_ui.js').read_text())]:
        assert template.count(token)==1;template=template.replace(token,value)
    output.parent.mkdir(parents=True,exist_ok=True);staging=Path(tempfile.mkdtemp(prefix='.identity-editor-',dir=output.parent))
    try:
        filename=label+'__identity_corrector.html';(staging/filename).write_text(template)
        shutil.copy2(video,staging/name)
        jumps=jump_events(raw,identity['frame_start'])
        with (staging/(label+'__raw_jump_warnings.csv')).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['kind','frame','animal','previous_frame','distance_px']);w.writeheader();w.writerows(jumps)
        (staging/'START_HERE.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url='+filename+'"><a href="'+filename+'">Open identity corrector</a>')
        (staging/'READ_ME_FIRST.txt').write_text('Identity corrector '+VERSION+' — test version\n\nOpen START_HERE.html. The video must stay beside the editor.\nClick a beetle, choose its correct ID, set or suggest an inclusive global-frame interval, preview, then accept. Use 0–5 for this six-beetle trial. Export corrections and return the JSON to Codex for reprocessing. No identities have been corrected in this starting package.\n\nIdentity corrections only. Motion-based suggestions can follow reciprocal raw-label reversals. Saved intervals appear on the timeline and update playback immediately. Original data remain unchanged; missing detections are not filled. Pile editing is not included. Browser previews do not recompute automatic PSC or behavioral measurements. Suggestions stop at gaps, proximity, and jumps, but are not biological identity proof.\n')
        receipt=dict(version=VERSION,status='TEST_EDITOR_UNREVIEWED',source_identity=identity,source_review_sha256=sha256(review/'source_manifest.json'),
                     raw_adjacent_jump_count=len(jumps),jump_warning_px=100,html=filename,
                     code_sha256={n:sha256(here/n) for n in ['build_identity_corrector.py','identity_corrections.py','identity_corrector_core.js','identity_corrector_ui.js','identity_corrector_template.html']},
                     output_sha256={p.name:sha256(p) for p in staging.iterdir()})
        (staging/'CORRECTOR_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');os.rename(staging,output)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return output/filename

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['bundle','review','output']:p.add_argument('--'+n,required=True)
    p.add_argument('--initial-frame',type=int);print(build(**vars(p.parse_args())))
