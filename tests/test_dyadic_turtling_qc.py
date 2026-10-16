import json,tempfile,unittest
from pathlib import Path
import dyadic_turtling_qc as qc
class CandidateQC(unittest.TestCase):
 def test_near_and_unknown_partner_retained(self):
  for partner,context in [([20,0],'NEAR_PARTNER'),([None,None],'PARTNER_UNKNOWN')]:
   raw=[[[0,0],partner] for _ in range(120)]
   r=qc.summarize(raw,700,30);e=r['events'][0]
   self.assertEqual(e['first_global_frame'],700);self.assertEqual(e['last_global_frame_inclusive'],819)
   self.assertEqual(e['context_frames'],{context:120})
 def test_missing_is_unknown_and_never_candidate(self):
  r=qc.summarize([[[None,None],[None,None]]]*120,0,30)
  self.assertFalse(r['events']);self.assertEqual(r['per_id'][0]['tracking_unknown_frames'],120)
 def test_unsupported_fps_explicit(self):
  self.assertEqual(qc.summarize([[[0,0],[100,0]]]*120,0,60)['status'],'NOT_ASSESSED')
 def test_no_mutation_report_and_bounds(self):
  raw=[[[0,0],[100,0]] for _ in range(120)];old=json.dumps(raw)
  r=qc.summarize(raw,5,30);self.assertEqual(json.dumps(raw),old)
  with tempfile.TemporaryDirectory() as d:
   qc.write_report(d,r,raw,'../review.html')
   h=(Path(d)/'dyadic_turtling_qc.html').read_text()
   self.assertIn('../review.html#frame=5',h);self.assertIn('ID 0',h);self.assertIn('ID 1',h)
   with self.assertRaises(FileExistsError):qc.write_report(d,r,raw)
 def test_non_dyad_rejected(self):
  with self.assertRaises(ValueError):qc.summarize([[[0,0]]],0,30)
if __name__=='__main__':unittest.main()
