import unittest,tempfile,json,hashlib
from pathlib import Path
from ba_tracking_exclusions import subtract_intervals,review_ranges,prepare
class ExclusionTests(unittest.TestCase):
 def test_only_requested_frames_removed(self):
  intervals=[[100,150]];excluded=[[100,100],[110,112],[111,115],[149,149]]
  out=subtract_intervals(intervals,excluded);self.assertEqual(out,[[101,110],[116,149]])
  actual={f for a,b in out for f in range(a,b)};expected=set(range(100,150))-{f for a,b in excluded for f in range(a,b+1)};self.assertEqual(actual,expected)
 def test_multiple_intervals_and_outside_requests(self):
  self.assertEqual(subtract_intervals([[10,20],[30,40]],[[15,32],[0,2],[50,60]]),[[10,15],[33,40]])
 def test_bad_ranges(self):
  for bad in [[[True,10]],[[3.2,5]],[[-1,5]],[[7,6]]]:
   with self.assertRaises(ValueError):subtract_intervals([[0,20]],bad)
 def test_prepare_preserves_window_and_original(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp).resolve();src=r/'source.toml';original='number_of_animals=1\nvideo_paths=["/video.mp4"]\nroi_list=[[[0,0],[100,0],[100,100]]]\ntracking_intervals=[[100,9000]]\narea_ths=[5.0,inf]\n';src.write_text(original)
   c=dict(id='a',run_id='run',source_toml=str(src),video='/video.mp4',start=90,end=400,analysis_start=100,analysis_end=7299);cases=r/'CASES.json';cases.write_text(json.dumps([c]));h=hashlib.sha256(cases.read_bytes()).hexdigest()
   d=dict(case_id='a',run_id='run',reviewer='VAF',decision='request_exclusion',scope=dict(start=90,end_inclusive=400),exclusion_scope='selected_cell',excluded_ranges_inclusive=[[105,106],[200,209]])
   review=dict(schema='ba-visual-pattern-review-v2',set_hash=h,decisions=[d]);p=r/'scores.json';p.write_text(json.dumps(review));out=prepare(src,p,cases,r/'new');self.assertEqual(src.read_text(),original);self.assertEqual(out['retained_intervals'],[[100,105],[107,200],[210,9000]]);self.assertEqual(out['original_analysis_window_inclusive'],[100,7299]);self.assertEqual(out['eligible_window_frames'],7188)
   with self.assertRaises(FileExistsError):prepare(src,p,cases,r/'new')
   d['excluded_ranges_inclusive']=[[95,99]]
   with self.assertRaisesRegex(ValueError,'outside'):review_ranges(review,[c],str(src),'/video.mp4',h)
   d['excluded_ranges_inclusive']=[[105,106]];d['decision']='flag_problem';self.assertEqual(review_ranges(review,[c],str(src),'/video.mp4',h)[0],[])
   d['decision']='request_exclusion';d['exclusion_scope']='recording';self.assertEqual(review_ranges(review,[c],'/another_cell.toml','/video.mp4',h)[0],[[105,106]])
   self.assertEqual(review_ranges(review,[c],'/another_cell.toml','/different_video.mp4',h)[0],[])
   with self.assertRaises(ValueError):review_ranges(review,[c],str(src),'/video.mp4','wrong')
if __name__=='__main__':unittest.main()
