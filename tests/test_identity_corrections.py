import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from identity_corrections import SCHEMA,sha256,load_bundle,replay,apply,jump_events,psc_layer,bind_psc_review

class IdentityCorrectionTests(unittest.TestCase):
    def fixture(self,root):
        full=np.arange(60.,dtype=float).reshape(10,3,2);full[4,1]=np.nan
        traj=root/'trajectories.npy';np.save(traj,{'trajectories':full,'unrelated_confidence':'must not copy'})
        b=root/'analysis';b.mkdir();state=b/'canonical_states.npz';raw=full[2:8].copy();np.savez(state,raw=raw)
        m=dict(settings={'start':2},trajectory_file=str(traj),input_sha256={str(traj):sha256(traj)},output_sha256={state.name:sha256(state)})
        (b/'manifest.json').write_text(json.dumps(m));_,_,identity=load_bundle(b)
        d=dict(id='one',kind='swap',reviewer='Tester',reason='Visible identity swap',created_utc='2026-10-05T17:00:00Z',animal_a=0,animal_b=1,start_frame=3,end_frame_inclusive=6,anchor_frame=5)
        return b,traj,full,raw,identity,dict(identity,decisions=[d])
    def test_reciprocal_swap_backwards_inclusive_preserves_missing_and_outside(self):
        with tempfile.TemporaryDirectory() as t:
            b,traj,full,raw,identity,log=self.fixture(Path(t));before=raw.copy();out,mapping=replay(raw,identity,log)
            np.testing.assert_equal(raw,before);np.testing.assert_equal(out[1:5,0],raw[1:5,1]);np.testing.assert_equal(out[1:5,1],raw[1:5,0]);np.testing.assert_equal(out[[0,5]],raw[[0,5]]);np.testing.assert_equal(out[:,2],raw[:,2]);self.assertTrue(np.isnan(out[2,0]).all())
            log['decisions'].append(dict(log['decisions'][0],id='two',animal_a=1,animal_b=2,start_frame=4,end_frame_inclusive=5))
            out,mapping=replay(raw,identity,log)
            for i in range(len(raw)):np.testing.assert_equal(out[i],raw[i,mapping[i]])
    def test_hash_binding_duplicate_and_invalid_intervals(self):
        with tempfile.TemporaryDirectory() as t:
            b,traj,full,raw,identity,log=self.fixture(Path(t))
            for change in [dict(canonical_sha256='wrong'),dict(frame_start=1),dict(decisions=log['decisions']*2)]:
                with self.assertRaises(ValueError):replay(raw,identity,dict(log,**change))
            for change in [dict(start_frame=6),dict(end_frame_inclusive=8),dict(animal_b=0),dict(animal_a=True),dict(reviewer=''),dict(anchor_frame=7)]:
                with self.assertRaises(ValueError):replay(raw,identity,dict(log,decisions=[dict(log['decisions'][0],**change)]))
    def test_full_export_hash_guard_preservation_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);b,traj,full,raw,identity,log=self.fixture(root);original_hash=sha256(traj)
            output=apply(b,log,root/'new',traj);arr=np.load(output/'human_corrected_trajectories.npy',allow_pickle=False)
            np.testing.assert_equal(arr[:2],full[:2]);np.testing.assert_equal(arr[8:],full[8:]);np.testing.assert_equal(arr[2:8],replay(raw,identity,log)[0]);self.assertEqual(sha256(traj),original_hash)
            from processor import validate_trajectory_source
            self.assertEqual(validate_trajectory_source(output/'human_corrected_trajectories.npy'),'HUMAN_IDENTITY_CORRECTED')
            receipt=json.loads((output/'IDENTITY_CORRECTION_RECEIPT.json').read_text());self.assertEqual(receipt['status'],'HUMAN_CORRECTED_NEEDS_REPROCESSING')
            with self.assertRaises(FileExistsError):apply(b,log,output,traj)
            np.save(traj,np.zeros_like(full))
            with self.assertRaisesRegex(ValueError,'hash'):apply(b,log,root/'bad',traj)
            self.assertFalse((root/'bad').exists())
    def test_jump_warning_excludes_gaps_and_exact_threshold(self):
        raw=np.array([[[0.,0.]],[[100.,0.]],[[201.,0.]],[[np.nan,np.nan]],[[1000.,0.]]])
        events=jump_events(raw,175);self.assertEqual([(e['frame'],e['distance_px']) for e in events],[(177,101.)])

    def test_psc_preserves_raw_and_requires_missing_identity_then_binds_after_reprocessing(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);b,traj,full,raw,identity,log=self.fixture(root)
            d=dict(log['decisions'][0],kind='pscp',mode='partner',animal_a=1,animal_b=0,start_frame=4,end_frame_inclusive=4,anchor_frame=4)
            log['decisions']=[d];corrected,_=replay(raw,identity,log)
            np.testing.assert_equal(corrected,raw)
            xy,source=psc_layer(corrected,identity,log)
            np.testing.assert_equal(xy[2,1],raw[2,0]);self.assertEqual(source[2,1],'HUMAN_PSCP');self.assertTrue(np.isnan(corrected[2,1]).all())
            output=apply(b,log,root/'psc',traj)
            bound=bind_psc_review(output,b);self.assertEqual(bound['decisions'][0]['value'],'yes')
            self.assertEqual(bound['decisions'][0]['animal_id'],1)
            log['decisions']=[dict(d,mode='unresolved')];xy,source=psc_layer(raw,identity,log);self.assertTrue(np.isnan(xy[2,1]).all());self.assertEqual(source[2,1],'HUMAN_UNRESOLVED')
            for changed in [dict(d,animal_a=0,animal_b=1),dict(d,start_frame=3),dict(d,mode='invent')]:
                with self.assertRaises(ValueError):replay(raw,identity,dict(log,decisions=[changed]))
            swap=dict(d,id='swap',kind='swap',animal_a=0,animal_b=1)
            with self.assertRaisesRegex(ValueError,'missing ID'):replay(raw,identity,dict(log,decisions=[d,swap]))
            # Moving the PSC label to the newly missing channel is consistent.
            changed=dict(d,animal_a=0,animal_b=1)
            out,_=replay(raw,identity,dict(log,decisions=[swap,changed]));self.assertTrue(np.isnan(out[2,0]).all())

if __name__=='__main__':unittest.main()
