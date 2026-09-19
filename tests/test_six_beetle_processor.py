import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import six_beetle_processor as six


class SixBeetleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.rois=[[[0,0],[1000,0],[1000,1000],[0,1000]]]
        self.rois += [[[x,400],[x+60,400],[x+60,460],[x,460]] for x in [100,400,700]]
        (self.root/'session.json').write_text(json.dumps({'roi_list':self.rois}))
        self.xy=np.zeros((3805,6,2))
        for i in range(6):
            self.xy[:,i,0]=100+i*100+np.minimum(np.arange(3805)*2,80)
            self.xy[:,i,1]=100+i*100
        self.source=self.root/'trajectories.npy'
        np.save(self.source,{'trajectories':self.xy})

    def tearDown(self): self.tmp.cleanup()
    def analyze(self,**kw): return six.analyze_six(self.source,self.root,1,3700,**kw)

    def test_six_animals_fifteen_pairs_and_shared_window(self):
        r=self.analyze()
        self.assertEqual(len(r['animals']),6)
        self.assertEqual(len(r['pairs']),30)
        fixed=[x for x in r['windows'] if x['window']=='post_wake_3600']
        self.assertEqual({x['start_global_frame'] for x in fixed},{16})
        self.assertTrue(all(x['frame_observations']==3601 and x['available_steps']==3600 for x in fixed))
        self.assertEqual({x['region'] for x in r['regions'] if x['region'].startswith('fungus_')},
                         {f'fungus_{i}{suffix}' for i in range(1,4) for suffix in ['', '_edge','_interior']})

    def test_partition_additivity(self):
        r=self.analyze()
        for animal in range(6):
            regions={x['region']:x for x in r['regions'] if x['animal_id']==animal and x['window']=='full'}
            full=next(x for x in r['windows'] if x['animal_id']==animal and x['window']=='full')
            self.assertEqual(regions['any_fungus']['coordinate_frames']+regions['off_fungus']['coordinate_frames'],full['valid_coordinate_frames'])
            self.assertAlmostEqual(regions['wall']['distance_px']+regions['non_wall']['distance_px'],full['distance_px'])
            for i in range(1,4):
                self.assertAlmostEqual(regions[f'fungus_{i}_edge']['distance_px']+regions[f'fungus_{i}_interior']['distance_px'],regions[f'fungus_{i}']['distance_px'])

    def test_missing_and_jump_never_bridged(self):
        self.xy[100,0]=np.nan; self.xy[200,0]=[900,900]
        np.save(self.source,{'trajectories':self.xy})
        full=self.analyze()['windows'][0]
        self.assertEqual(full['missing_coordinate_frames'],1)
        self.assertEqual(full['missing_endpoint_steps'],2)
        self.assertEqual(full['rejected_jump_steps'],2)
        self.assertAlmostEqual(full['distance_px'],78.)

    def test_one_missing_baseline_disables_group_fixed_window(self):
        self.xy[1,5]=np.nan; np.save(self.source,{'trajectories':self.xy})
        r=self.analyze()
        self.assertTrue(all(x['status']=='NO_RELIABLE_WAKE_FOR_ALL_SIX' for x in r['windows'] if x['window']=='post_wake_3600'))
        self.assertEqual(r['animals'][5]['threshold_crossing_global_frame'],'')

    def test_multi_partner_disappearance_not_imputed(self):
        xy=np.tile(np.array([[0,0],[10,0],[20,0],[400,0],[600,0],[800,0]],float),(6,1,1))
        xy[2:4,0]=np.nan
        pairs,events,masks=six.social_network(xy,100,60)
        disappearance=[e for e in events if e['kind']=='DISAPPEARANCE_CANDIDATE']
        self.assertEqual(len(pairs),15); self.assertEqual(len(disappearance),2)
        self.assertEqual({e['candidate_partner_count'] for e in disappearance},{2})
        self.assertEqual({e['attribution'] for e in disappearance},{'AMBIGUOUS_MULTIPLE_PARTNERS'})
        self.assertTrue(np.isnan(xy[2:4,0]).all())
        self.assertEqual(disappearance[0]['start_global_frame'],102)
        self.assertEqual(disappearance[0]['end_global_frame_inclusive'],103)

    def test_missing_gap_is_not_visible_return(self):
        xy=np.tile(np.array([[0,0],[10,0],[200,0],[400,0],[600,0],[800,0]],float),(6,1,1))
        xy[2:4,0]=np.nan
        pairs,_,_=six.social_network(xy,10,60)
        self.assertEqual(pairs[0]['visible_return_events'],0)
        xy[2:4,0]=[100,0]
        pairs,_,_=six.social_network(xy,10,60)
        self.assertEqual(pairs[0]['visible_return_events'],1)

    def test_overlap_union_counts_once(self):
        rois=[np.asarray(p,float) for p in self.rois]
        rois[2]=rois[1].copy()
        masks=six.regions(np.array([[120.,420.],[np.nan,np.nan]]),rois,30,10)
        self.assertEqual(masks['any_fungus'].sum(),1)
        self.assertEqual(masks['fungus_1'].sum()+masks['fungus_2'].sum(),2)

    def test_reject_wrong_dimensions_rois_and_invalid_settings(self):
        for kw in [dict(threshold=float('nan')),dict(wall_buffer_px=float('inf'))]:
            with self.assertRaises(ValueError): self.analyze(**kw)
        np.save(self.source,{'trajectories':self.xy[:,:2]})
        with self.assertRaisesRegex(ValueError,'six'): self.analyze()
        np.save(self.source,{'trajectories':self.xy})
        (self.root/'session.json').write_text(json.dumps({'roi_list':self.rois[:2]}))
        with self.assertRaisesRegex(ValueError,'four'): self.analyze()

    def test_no_valid_steps_are_missing_not_zero(self):
        self.xy[:,0]=np.nan; np.save(self.source,{'trajectories':self.xy})
        r=self.analyze()
        self.assertEqual(r['windows'][0]['distance_px'],'')
        self.assertEqual(r['windows'][0]['valid_coordinate_frames'],0)

    def test_refuses_existing_output(self):
        with self.assertRaises(FileExistsError): six.write_bundle({},self.root,'test','test')

    def test_frame_states_preserve_observation_and_missing_evidence(self):
        xy=np.tile(np.array([[0,0],[200,0],[400,0],[600,0],[800,0],[1000,0]],float),(8,1,1))
        xy[1:5,1]=[10,0]
        xy[2:4,0]=np.nan  # Bounded social disappearance: both participants gold.
        xy[6:8,5]=np.nan  # Ordinary trailing missingness stays orange.
        _,events,masks=six.social_network(xy,100,60)
        states=six.frame_states(xy,100,masks,events)
        np.testing.assert_array_equal(states['states'][:,0],[0,2,2,2,2,0,0,0])
        self.assertTrue((states['states'][2:4,1]==2).all())
        self.assertTrue((states['states'][6:8,5]==1).all())
        self.assertFalse(states['coordinate_present'][2:4,0].any())
        self.assertTrue(states['coordinate_present'][2:4,1].all())
        self.assertFalse(states['ambiguous_disappearance'].any())
        self.assertTrue(np.isnan(xy[2:4,0]).all())

    def test_frame_states_flag_all_ambiguous_participants_without_double_counting(self):
        xy=np.tile(np.array([[0,0],[10,0],[20,0],[600,0],[800,0],[1000,0]],float),(6,1,1))
        xy[2:4,0]=np.nan
        _,events,masks=six.social_network(xy,20,60)
        states=six.frame_states(xy,20,masks,events)
        self.assertTrue(states['ambiguous_disappearance'][2:4,:3].all())
        self.assertEqual(states['proximity_partner_count'][0,0],2)
        self.assertEqual(int((states['states'][0]==2).sum()),3)
        self.assertEqual(states['states'].shape,(6,6))

    def test_frame_states_ignore_fixed_window_duplicate_events(self):
        xy=np.zeros((3,6,2)); masks={}
        event=dict(kind='DISAPPEARANCE_CANDIDATE',window='post_wake_3600',
                   start_global_frame=10,end_global_frame_inclusive=11,
                   animal_a=0,animal_b=1,candidate_partner_count=2)
        states=six.frame_states(xy,10,masks,[event])
        self.assertFalse(states['disappearance_candidate'].any())
        self.assertTrue((states['states']==0).all())

    def test_pair_contact_is_pair_specific_with_ambiguous_partners(self):
        xy=np.tile(np.array([[0,0],[10,0],[20,0],[600,0],[800,0],[1000,0]],float),(6,1,1))
        xy[2:4,0]=np.nan
        _,events,masks=six.social_network(xy,100,60)
        inferred,ambiguous=six.pair_contact_masks(masks,events,100)
        for pair in [(0,1),(0,2)]:
            np.testing.assert_array_equal(inferred[pair],[False,False,True,True,False,False])
            np.testing.assert_array_equal(ambiguous[pair],inferred[pair])
            self.assertFalse((masks[pair] & inferred[pair]).any())
        # Both visible partners can have inferred individual contact with 0;
        # that must not create a disappearance inference between 1 and 2.
        self.assertFalse(inferred[1,2].any())
        self.assertFalse(inferred[3,4].any())

    def test_pair_contact_single_partner_and_fixed_window_filter(self):
        masks={(0,1):np.zeros(5,dtype=bool)}
        event=dict(kind='DISAPPEARANCE_CANDIDATE',window='full',animal_a=0,animal_b=1,
                   start_global_frame=51,end_global_frame_inclusive=52,candidate_partner_count=1)
        inferred,ambiguous=six.pair_contact_masks(masks,[event],50)
        np.testing.assert_array_equal(inferred[0,1],[False,True,True,False,False])
        self.assertFalse(ambiguous[0,1].any())
        event['window']='post_wake_3600'
        inferred,_=six.pair_contact_masks(masks,[event],50)
        self.assertFalse(inferred[0,1].any())

if __name__=='__main__': unittest.main()

class ReportAdditionsTests(unittest.TestCase):
    def test_disappearance_marks_last_valid_before_gap_only(self):
        track=np.array([[np.nan,np.nan],[1,2],[3,4],[np.nan,np.nan],[8,9],[np.nan,np.nan]])
        np.testing.assert_array_equal(six.disappearance_offsets(track),[2,4])

    def test_fungus_time_preserves_frames_and_pixel_distance(self):
        result={'metadata':{'frames_per_second':30},'regions':[
            dict(animal_id=a,window='full',region=f'fungus_{f}',coordinate_frames=60,
                 distance_px=12.5) for a in range(6) for f in range(1,4)]}
        rows=six.fungus_summary(result)
        self.assertEqual(len(rows),6)
        self.assertEqual(rows[5]['fungus_3_seconds'],2)
        self.assertEqual(rows[5]['fungus_3_distance_px'],12.5)
        result['metadata']['frames_per_second']=None
        self.assertEqual(six.fungus_summary(result)[0]['fungus_1_seconds'],'')

class PresumedGroupTests(unittest.TestCase):
    def test_pair_grows_to_triple_when_anchor_disappears(self):
        raw=np.array([[[0,0],[5,0],[100,0]],[[np.nan,np.nan],[10,0],[15,0]],
                      [[np.nan,np.nan],[np.nan,np.nan],[20,0]],
                      [[1,1],[np.nan,np.nan],[25,0]]],float)
        result=six.presumed_groups(raw,10)
        np.testing.assert_array_equal(result['anchors'][2],[2,2,2])
        np.testing.assert_allclose(result['xy'][2],[[20,0],[20,0],[20,0]])
        np.testing.assert_array_equal(result['anchors'][3],[0,2,2])
        self.assertTrue(np.isnan(raw[2,0]).all())
        self.assertTrue(result['masks'][0,1][2])

    def test_incoming_beetle_disappears_into_existing_group(self):
        raw=np.array([[[0,0],[5,0],[100,0]],[[np.nan,np.nan],[10,0],[15,0]],
                      [[np.nan,np.nan],[20,0],[np.nan,np.nan]]],float)
        r=six.presumed_groups(raw,10)
        np.testing.assert_array_equal(r['anchors'][2],[1,1,1])

    def test_multiple_candidates_or_no_anchor_remain_unresolved(self):
        raw=np.array([[[0,0],[5,0],[8,0]],[[np.nan,np.nan],[6,0],[9,0]],
                      [[np.nan,np.nan],[np.nan,np.nan],[np.nan,np.nan]]],float)
        r=six.presumed_groups(raw,10)
        self.assertTrue(r['ambiguous'][1,0])
        self.assertTrue(np.isnan(r['xy'][1,0]).all())
        self.assertTrue(np.isnan(r['xy'][2]).all())

    def test_no_future_return_required_and_no_proximity_no_assignment(self):
        raw=np.array([[[0,0],[5,0],[100,0]],[[np.nan,np.nan],[7,0],[np.nan,np.nan]],
                      [[np.nan,np.nan],[9,0],[np.nan,np.nan]]],float)
        r=six.presumed_groups(raw,10)
        np.testing.assert_allclose(r['xy'][-1,0],[9,0])
        self.assertEqual(r['anchors'][-1,2],-1)
