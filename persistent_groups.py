"""Versioned, detection-supported contact groups; no frame-specific annotations.

Coordinates are original-image pixels. Detection identity labels are 1-based.
Positions are never held or interpolated through missing detections. Membership
survives those gaps; reacquisition has a fixed search radius. Inferred identity
is a hypothesis and raw coordinates must be retained separately.
"""
import itertools
import numpy as np

MODEL_VERSION='1.3.0'


def persistent_groups(raw, blobs, social_radius=60., max_step=100., confirmation=3,
                      gap_speed=20., gap_radius_cap=300., max_reacquire_gap=30):
    raw=np.asarray(raw,float);nframes,nanimals,_=raw.shape
    if (not np.isfinite([social_radius,max_step,gap_speed,gap_radius_cap]).all() or
            social_radius<=0 or max_step<=0 or confirmation<1 or gap_speed<=0
            or gap_radius_cap<social_radius or max_reacquire_gap<1):
        raise ValueError('Invalid model parameters')
    xy=np.full_like(raw,np.nan);group_ids=np.full((nframes,nanimals),-1,int)
    inferred=np.zeros((nframes,nanimals),bool);ambiguous=np.zeros_like(inferred)
    anchors=np.full((nframes,nanimals),-1,int)
    source=np.full((nframes,nanimals),'MISSING',dtype='<U24')
    # A live entity owns one or more identities independently of its current location.
    entities=[];initialized=set();next_id=0;events=[]
    def detections(t):return blobs.get(str(t),blobs.get(t,[]))
    def raw_blob(t,a,bs):
        p=raw[t,a]
        if not np.isfinite(p).all():return None
        matches=[i for i,b in enumerate(bs) if np.linalg.norm(np.asarray(b['centroid'])-p)<=social_radius]
        # Nearest unique blob, with ties treated as ambiguous.
        if not matches:return None
        matches.sort(key=lambda i:np.linalg.norm(np.asarray(bs[i]['centroid'])-p))
        if len(matches)>1 and abs(np.linalg.norm(np.asarray(bs[matches[0]]['centroid'])-p)-np.linalg.norm(np.asarray(bs[matches[1]]['centroid'])-p))<5:return None
        return matches[0]
    for t in range(nframes):
        bs=detections(t)
        # Initialize only IDs assigned a finite coordinate near a real detection.
        for a in range(nanimals):
            if a in initialized:continue
            j=raw_blob(t,a,bs)
            if j is not None:
                entities.append(dict(id=next_id,members={a},last=np.array(bs[j]['centroid'],float),last_frame=t,split_key=None,split_count=0))
                next_id+=1;initialized.add(a)
        proposals=[]
        for e in entities:
            gap=t-e['last_frame']
            # Group membership persists without detections, but no position is
            # assigned during the gap. Reacquire only over a bounded plausible
            # displacement; the old fixed 60-pixel gate lost moving piles.
            if gap>max_reacquire_gap:
                candidates=[]
            else:
                radius=(max_step if gap<=1 or e['split_count']>0 else
                        min(gap_radius_cap, max_step*gap,
                            social_radius+gap_speed*(gap-1)))
                candidates=[j for j,b in enumerate(bs) if any(
                    np.linalg.norm(np.asarray(b['centroid'])-p)<=radius
                    for p in [e['last']]+e.get('pending_positions',[]))]
            # Identity-guided choice is allowed only inside the spatial gate.
            votes={raw_blob(t,a,bs) for a in e['members']};votes.discard(None)
            votes&=set(candidates)
            partitions={}
            for a in e['members']:
                j=raw_blob(t,a,bs)
                # A member may emerge well away from the pile after being
                # hidden. The pile's spatial gate must not veto evidence for
                # a *split*. It still gates movement of the whole pile.
                if j is not None:partitions.setdefault(j,set()).add(a)
            # When only a departing member has a raw label, an unlabeled blob
            # continuing the pile is evidence for the other members. Without
            # this partition the distant label could drag the whole pile.
            if len(e['members'])>1 and len(partitions)==1:
                raw_j=next(iter(partitions))
                remaining=e['members']-partitions[raw_j]
                # Do not recruit an unrelated beetle's clearly labeled blob
                # as the supposed continuation of the hidden pile.
                near=[j for j in candidates if j!=raw_j and not
                      (set(bs[j].get('identities',[]))-{a+1 for a in e['members']})]
                if remaining and near:
                    near_j=min(near,key=lambda j:np.linalg.norm(np.asarray(bs[j]['centroid'])-e['last']))
                    partitions[near_j]=set(remaining)
            # A returning subset can separate without requiring every hidden member.
            assigned=set().union(*partitions.values()) if partitions else set()
            if len(partitions)>1 and assigned != e['members']:
                nearest=min(partitions,key=lambda j:np.linalg.norm(np.asarray(bs[j]['centroid'])-e['last']))
                partitions[nearest] |= e['members']-assigned
            split=len(partitions)>1
            key=tuple(sorted(tuple(sorted(v)) for v in partitions.values())) if split else None
            positions={tuple(sorted(v)):np.asarray(bs[j]['centroid'],float)
                       for j,v in partitions.items()} if split else {}
            smooth=key==e['split_key'] and all(
                members in e.get('split_positions',{}) and
                np.linalg.norm(p-e['split_positions'][members])<=max_step
                for members,p in positions.items())
            if key and smooth:e['split_count']+=1
            else:e['split_key']=key;e['split_count']=1 if key else 0
            e['split_positions']=positions
            if split and e['split_count']>=confirmation:
                events.append(dict(frame=t,kind='SPLIT_CONFIRMED',members=sorted(e['members'])))
                for j,members in partitions.items():
                    child=dict(id=next_id,members=members,last=e['last'].copy(),last_frame=e['last_frame'],split_key=None,split_count=0)
                    next_id+=1;proposals.append((child,j))
                continue
            # Unresolved splits: never assign an entire group to one of multiple blobs.
            if split:
                e['pending_positions']=[np.asarray(bs[j]['centroid'],float) for j in partitions]
                proposals.append((e,None));continue
            e.pop('pending_positions',None)
            if len(votes)==1:j=next(iter(votes))
            elif len(candidates)==1:j=candidates[0]
            elif candidates:
                ranked=sorted(candidates,key=lambda j:np.linalg.norm(np.asarray(bs[j]['centroid'])-e['last']))
                distances=[np.linalg.norm(np.asarray(bs[j]['centroid'])-e['last']) for j in ranked[:2]]
                j=ranked[0] if len(distances)==1 or distances[1]-distances[0]>social_radius/2 else None
            else:j=None
            proposals.append((e,j))
        # Many old entities converging on the same actual blob form a pile.
        by_blob={};unseen=[]
        for e,j in proposals:
            if j is None:unseen.append(e)
            else:by_blob.setdefault(j,[]).append(e)
        active=[]
        for j,es in by_blob.items():
            if len(es)>1:
                members=set().union(*(e['members'] for e in es))
                e=dict(id=next_id,members=members,last=np.asarray(bs[j]['centroid'],float),last_frame=t,split_key=None,split_count=0)
                next_id+=1;events.append(dict(frame=t,kind='MERGE',members=sorted(members)))
            else:e=es[0]
            p=np.asarray(bs[j]['centroid'],float);e['last']=p;e['last_frame']=t;active.append(e)
            members=sorted(e['members']);is_pile=len(members)>1
            # IDtracker can report several identity coordinates for one
            # segmented blob. Those coordinates are not independent sightings:
            # one blob supports at most one visible identity. Pick the closest
            # raw coordinate as its anchor, then infer the other pile members.
            matched=[a for a in members if raw_blob(t,a,bs)==j]
            visible=min(matched,key=lambda a:(np.linalg.norm(raw[t,a]-p),a)) if matched else None
            for a in members:
                assigned=a==visible
                other=raw_blob(t,a,bs)
                disputed=is_pile and other is not None and other!=j and not assigned
                if disputed:
                    # A conflicting raw label is not yet a trusted departure,
                    # but the pile location is no longer defensible either.
                    group_ids[t,a]=e['id'];ambiguous[t,a]=True
                    source[t,a]='SPLIT_PENDING'
                    continue
                xy[t,a]=p if is_pile else (raw[t,a] if assigned else p)
                group_ids[t,a]=e['id'];inferred[t,a]=not assigned
                anchors[t,a]=visible if visible is not None else members[0]
                source[t,a]='ASSIGNED' if assigned else 'PSCP_BLOB' if is_pile else 'BLOB_CONTINUITY'
        for e in unseen:
            active.append(e)
            for a in e['members']:
                group_ids[t,a]=e['id'];ambiguous[t,a]=len(bs)>0
                # No position: preserve identity membership only.
        entities=active
    shared={(a,b):(group_ids[:,a]>=0)&(group_ids[:,a]==group_ids[:,b])
            for a,b in itertools.combinations(range(nanimals),2)}
    masks={(a,b):joined&np.isfinite(xy[:,a]).all(axis=1)&np.isfinite(xy[:,b]).all(axis=1)&(inferred[:,a]|inferred[:,b])
           for (a,b),joined in shared.items()}
    unresolved_masks={(a,b):joined&(~np.isfinite(xy[:,a]).all(axis=1)|~np.isfinite(xy[:,b]).all(axis=1))
                      for (a,b),joined in shared.items()}
    return dict(xy=xy,group_ids=group_ids,inferred=inferred,ambiguous=ambiguous,anchors=anchors,
                masks=masks,unresolved_masks=unresolved_masks,source=source,events=events)
