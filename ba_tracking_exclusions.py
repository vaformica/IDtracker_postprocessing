"""Prepare attributed IDtracker interval exclusions; never submit or overwrite runs.

Human ranges are inclusive. IDtracker intervals are half-open. Original temporal
windows remain fixed; no frames are concatenated, filled, or replaced by later data.
The current production BA processor still rejects split intervals: this module
creates tracking plans only, not a postprocessing release.
"""
from pathlib import Path
import argparse,copy,hashlib,json,math
try:
 import tomllib
except ImportError:
 import tomli as tomllib
VERSION='0.1.0-development'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def checked_ranges(ranges,inclusive=False):
 out=[]
 for pair in ranges:
  if not isinstance(pair,(list,tuple)) or len(pair)!=2 or any(type(x) is not int for x in pair):raise ValueError('Frame boundaries must be integer pairs')
  lo,hi=pair
  if lo<0 or hi<lo or (not inclusive and hi==lo):raise ValueError('Invalid frame interval')
  out.append([lo,hi+1 if inclusive else hi])
 out.sort();merged=[]
 for lo,hi in out:
  if merged and lo<=merged[-1][1]:merged[-1][1]=max(hi,merged[-1][1])
  else:merged.append([lo,hi])
 return merged

def subtract_intervals(tracking_intervals,excluded_inclusive):
 """Return retained half-open intervals, removing only requested intersections."""
 kept=checked_ranges(tracking_intervals);excluded=checked_ranges(excluded_inclusive,True)
 for lo,hi in excluded:
  next_kept=[]
  for a,b in kept:
   if hi<=a or lo>=b:next_kept.append([a,b]);continue
   if a<lo:next_kept.append([a,lo])
   if hi<b:next_kept.append([hi,b])
  kept=next_kept
 return kept

def review_ranges(review,cases,source_toml,source_video,cases_hash):
 if review.get('schema')!='ba-visual-pattern-review-v2' or review.get('set_hash')!=cases_hash:raise ValueError('Review does not match the frozen case set')
 byid={c['id']:c for c in cases};seen=set();ranges=[];attributions=[]
 for d in review.get('decisions',[]):
  id=d.get('case_id')
  if id in seen:raise ValueError('Duplicate decision')
  seen.add(id)
  if id not in byid:raise ValueError('Unknown case')
  if d.get('decision')!='request_exclusion':continue
  c=byid[id];scope=d.get('scope',{})
  if scope.get('start')!=c['start'] or scope.get('end_inclusive')!=c['end'] or d.get('run_id')!=c['run_id']:raise ValueError('Changed review coverage')
  if not str(d.get('reviewer','')).strip():raise ValueError('Exclusions require an attributed reviewer')
  if d.get('exclusion_scope') not in ['selected_cell','recording']:raise ValueError('Unknown exclusion scope')
  marked=d.get('excluded_ranges_inclusive',[])
  if not marked:raise ValueError('No explicit exclusion frames')
  checked_ranges(marked,True)
  for lo,hi in marked:
   if lo<max(c['start'],c['analysis_start']) or hi>min(c['end'],c['analysis_end']):raise ValueError('Exclusion outside displayed analyzed footage')
  matches=(c['source_toml']==str(source_toml)) if d['exclusion_scope']=='selected_cell' else c['video']==str(source_video)
  if matches:ranges.extend(marked);attributions.append(copy.deepcopy(d))
 return [[a,b-1] for a,b in checked_ranges(ranges,True)],attributions

def prepare(source_toml,review_path,cases_path,output,frame_count=7200):
 import toml  # Serialization dependency, used only when writing a plan.
 source=Path(source_toml).resolve();output=Path(output)
 if output.exists():raise FileExistsError(output)
 config=tomllib.loads(source.read_text());cases=json.loads(Path(cases_path).read_text());review=json.loads(Path(review_path).read_text());intervals=config.get('tracking_intervals')
 if config.get('number_of_animals')!=1 or len(config.get('roi_list',[]))!=1 or len(config.get('video_paths',[]))!=1:raise ValueError('Expected one-animal, one-video, one-ROI BA source')
 original=checked_ranges(intervals)
 if len(original)!=1 or original!=intervals:raise ValueError('First exclusion plan requires an unambiguous original interval; do not apply cumulatively to a revised TOML')
 start,stop=original[0]
 if type(frame_count) is not int or frame_count<2 or start+frame_count>stop:raise ValueError('Original analysis window does not fit')
 ranges,attributions=review_ranges(review,cases,str(source),config['video_paths'][0],sha(cases_path))
 if not ranges:raise ValueError('No attributed exclusion request applies to this TOML')
 retained=subtract_intervals(original,ranges)
 if not retained:raise ValueError('Refusing to exclude all source tracking')
 before=sum(b-a for a,b in original);after=sum(b-a for a,b in retained)
 if before==after:raise ValueError('Requested exclusions do not overlap this TOML')
 revised=copy.deepcopy(config);revised['tracking_intervals']=retained
 encoded=toml.dumps(revised);parsed=tomllib.loads(encoded)
 # Semantic preservation includes infinities used by area thresholds.
 if repr(parsed)!=repr(revised):
  def canonical(x):return json.dumps(x,sort_keys=True,allow_nan=True)
  if canonical(parsed)!=canonical(revised):raise ValueError('TOML serialization changed other settings')
 observed=sum(max(0,min(b,start+frame_count)-max(a,start)) for a,b in retained)
 receipt=dict(schema='ba-tracking-exclusion-plan-v1',version=VERSION,status='PREPARED_NOT_SUBMITTED_POSTPROCESSING_SUPPORT_REQUIRED',source_toml=str(source),source_sha256=sha(source),review_sha256=sha(review_path),case_set_sha256=sha(cases_path),original_intervals=original,retained_intervals=retained,requested_exclusions_inclusive=ranges,excluded_source_frames=before-after,original_analysis_window_inclusive=[start,start+frame_count-1],original_window_frames=frame_count,eligible_window_frames=observed,excluded_window_frames=frame_count-observed,attributions=attributions,policy='Keep original global frame axis and window. Excluded frames are unknown; never interpolate or measure steps/posture continuity across exclusions. Production BA pipeline not yet adapted; do not bypass its interval validation.')
 output.mkdir(parents=True);(output/'source.toml').write_bytes(source.read_bytes());(output/'tracking.toml').write_text('# Derived BA tracking configuration: only attributed bad frames removed. Original preserved in source.toml.\n'+encoded);receipt['tracking_toml_sha256']=sha(output/'tracking.toml');(output/'EXCLUSION_PLAN.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['source-toml','review','cases','output']:p.add_argument('--'+name,required=True)
 a=p.parse_args();print(json.dumps(prepare(a.source_toml,a.review,a.cases,a.output),indent=2))
if __name__=='__main__':main()
