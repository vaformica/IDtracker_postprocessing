from pathlib import Path
import json,hashlib,subprocess,os,grp
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan=json.loads((R/'TRACKING_PLAN.json').read_text());checks=[]
for r in plan['runs']:
 assert sha(r['savannah_source_path'])==r['savannah_source_sha256']
 assert sha(r['source_toml'])==r['toml_sha256'] and sha(r['submission_toml'])==r['submission_sha256']
 v=json.loads(subprocess.check_output(['/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,r_frame_rate,width,height','-of','json',r['video']]))['streams'][0]
 assert v['r_frame_rate']=='30/1' and int(v['nb_frames'])>r['end'];checks.append(dict(id=r['id'],video=v,source_verified=True))
gid=grp.getgrnam('vformic1-swat-lab').gr_gid
for p in [R,*R.rglob('*')]:
 os.chown(p,-1,gid);os.chmod(p,0o2770 if p.is_dir() else 0o660)
(R/'PREFLIGHT.json').write_text(json.dumps(dict(status='PASS',checks=checks),indent=2));print('PREFLIGHT PASS',len(checks))
