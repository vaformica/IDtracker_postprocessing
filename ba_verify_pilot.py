#!/usr/bin/env python3
"""Independently check completed BA pilot bundles and their indexes."""
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import zipfile


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def verify(root):
    receipt=json.loads((root/'RELEASE_RECEIPT.json').read_text())
    checks=[]
    for r in receipt['runs']:
        if r['status']!='COMPLETE_UNREVIEWED':continue
        folder=Path(r['output']);m=json.loads((folder/'manifest.json').read_text())
        for filename,digest in m['output_sha256'].items():
            assert sha(folder/filename)==digest,(r['label'],filename)
        with (folder/'frame_data.csv').open() as stream:frames=list(csv.DictReader(stream))
        with (folder/'summary.csv').open() as stream:summary=list(csv.DictReader(stream))
        assert len(frames)==7200 and len(summary)==1
        assert [int(x['global_frame']) for x in frames]==list(range(m['start_global_frame'],m['end_global_frame_inclusive']+1))
        assert all(x['animal_id']=='0' for x in frames)
        total=sum(float(x['step_distance_px']) for x in frames if x['step_distance_px'])
        assert math.isclose(total,float(summary[0]['total_distance_px_in_analysis_window']),rel_tol=1e-10,abs_tol=1e-8)
        assert sum(int(x['turtling_candidate']) for x in frames)==int(summary[0]['turtling_candidate_frames'])
        packet=json.loads(subprocess.check_output(['/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe','-v','error','-select_streams','v:0','-count_packets','-show_entries','stream=nb_read_packets,nb_frames','-of','json',str(folder/'review_video.mp4')]))['streams'][0]
        assert int(packet['nb_frames'])==7200 and int(packet['nb_read_packets'])==7200
        archive=Path(r['zip']);assert sha(archive)==r['zip_sha256']
        with zipfile.ZipFile(archive) as z:assert z.testzip() is None
        checks.append(dict(label=r['label'],frame_rows=7200,video_frames=7200,video_packets=7200,metrics_agree=True,hashes_match=True,zip_integrity=True))
    for name in ['index.html','TOML_INVENTORY.csv','VIDEO_INDEX.csv','QC_INDEX.csv','TURTLING_REVIEW_QUEUE.csv','turtling_review.html']:
        assert (root/name).is_file(),name
    result=dict(schema='ba-pilot-verification-v1',qc_status='UNREVIEWED',runs=checks,
                scope='Artifact and arithmetic checks, not human behavioral validation')
    (root/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':verify(Path(sys.argv[1]))
