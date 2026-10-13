import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from ba_combined_layers import layers
class LayersTests(unittest.TestCase):
 def fixture(self,p,jump=False):
  n=7200;a=np.full((n,2),50.);baseline=a.copy();baseline[7]=np.nan;a[4]=np.nan;baseline[4]=np.nan
  if jump:a[30]=250;baseline[30]=250
  method=np.full(n,'existing',dtype='<U30');method[7]='interpolated';method[4]='human_exclusion';protected=np.arange(n)==4
  np.savez_compressed(p/'COORDINATES.npz',raw=baseline,baseline=baseline,analysis=a,method=method,protected=protected,start=100,end=7299)
  (p/'QC.json').write_text('{}');(p/'data.js').write_text('window.loadRun({});');(p/'MANIFEST.json').write_text('{}')
 def test_interpolation_not_used_as_posture(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p)
   seen=[]
   def features(x):seen.append(x.copy());return np.zeros((7200,1))
   with patch('ba_combined_layers.window_features',features),patch('ba_combined_layers.gate_passes',return_value=np.ones((7200,1),bool)),patch('ba_combined_layers.mask_from_windows',return_value=np.ones(7200,bool)),patch('ba_combined_layers.experiment',return_value={'episode_mask':np.ones(7200,bool)}),patch('ba_combined_layers.gate_candidates',return_value={'candidate_mask':np.ones(7200,bool),'eligible_mask':np.ones(7200,bool)}),patch('ba_combined_layers.refine',return_value={'candidate_mask':np.ones(7200,bool)}),patch('ba_combined_layers.refine_boundaries',return_value={'candidate_mask':np.ones(7200,bool)}):layers(p)
   self.assertTrue(np.isnan(seen[0][7]).all());t=json.loads((p/'TURTLING_SCREENING.json').read_text());self.assertFalse(t['candidate_mask'][7]);self.assertEqual(t['state'][7],'not_assessed_interpolated');self.assertFalse(t['candidate_mask'][4]);self.assertEqual(t['state'][4],'not_assessed_excluded')
 def test_remaining_jump_blocks_movement_and_posture(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p,True)
   with patch('ba_combined_layers.window_features',side_effect=AssertionError('Blocked run must not be classified')):layers(p)
   s=np.load(p/'STRICT_ANALYSIS.npz');self.assertTrue(np.isnan(s['movement_step_px']).all());self.assertTrue(np.isnan(s['analysis'][29:32]).all());t=json.loads((p/'TURTLING_SCREENING.json').read_text());self.assertFalse(any(t['candidate_mask']))
if __name__=='__main__':unittest.main()
