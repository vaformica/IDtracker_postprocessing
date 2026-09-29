"""Apply explicit human review annotations without changing source coordinates."""
import numpy as np

def apply_reviewed_contacts(display, annotations, accepted):
    output=np.array(display,copy=True)
    reviewed=np.zeros(accepted.shape,dtype=bool)
    partners=np.full(accepted.shape,-1,dtype=int)
    for note in annotations:
        a,b=note['animal_id'],note['anchor_id']
        lo,hi=note['start_frame'],note['end_frame_inclusive']+1
        if a==b or lo<0 or hi>len(output):raise ValueError('Invalid reviewed contact')
        reviewed[lo:hi,a]=True;partners[lo:hi,a]=b
        # An annotation establishes a relation, not an unobserved anchor location.
        for t in range(lo,hi):
            output[t,a]=output[t,b] if accepted[t,b] else np.nan
    return output,reviewed,partners


def follow_detected_pile(screened, blobs, members, start, end, seed, max_step=100., reacquire_radius=60.):
    """Track a user-reviewed group using unique real blob detections.

    Blob identity labels are evidence only: spatial continuity can follow a blob
    with changed labels, but this is an explicit user-reviewed group hypothesis.
    An unseen frame never receives a held or interpolated location. After an
    unseen frame, reacquisition is restricted to a fixed radius, not elapsed time.
    Multiple plausible blobs are ambiguous and do not resolve the group.
    """
    positions=np.full((end-start+1,len(members),2),np.nan)
    states=np.full((end-start+1,len(members)), 'MISSING',dtype='<U24')
    evidence=[];last=np.asarray(seed,dtype=float);last_frame=start-1
    for t in range(start,end+1):
        row=t-start
        visible=[a for a in members if np.isfinite(screened[t,a]).all()]
        if len(visible)==len(members) and np.linalg.norm(screened[t,members[0]]-screened[t,members[1]])>60:
            # Resolved separate detections should not be forced into a pile.
            positions[row]=screened[t,list(members)];states[row]='SCREENED_ASSIGNED'
            last=np.mean(positions[row],axis=0);last_frame=t
            evidence.append(dict(frame=t,source='SEPARATE_ASSIGNED',candidate_count=0));continue
        radius=max_step if t==last_frame+1 else reacquire_radius
        candidates=[b for b in blobs.get(str(t),[]) if np.linalg.norm(np.array(b['centroid'])-last)<=radius]
        if len(candidates)==1:
            b=candidates[0];last=np.asarray(b['centroid']);last_frame=t
            positions[row]=last;states[row]='PSCP_DETECTED_BLOB'
            evidence.append(dict(frame=t,source='DETECTED_BLOB',candidate_count=1,centroid=b['centroid'],original_blob_ids_1based=b['identities']))
        elif len(visible)==1 and np.linalg.norm(screened[t,visible[0]]-last)<=radius:
            last=screened[t,visible[0]];last_frame=t
            positions[row]=last;states[row]='PSCP_VISIBLE_PARTNER'
            evidence.append(dict(frame=t,source='VISIBLE_PARTNER',candidate_count=len(candidates),anchor=visible[0]))
        else:
            evidence.append(dict(frame=t,source='MISSING_OR_AMBIGUOUS',candidate_count=len(candidates)))
    return positions,states,evidence
