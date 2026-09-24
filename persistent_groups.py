"""Versioned, detection-supported contact groups; no frame-specific annotations.

Coordinates are original-image pixels. Detection identity labels are 1-based.
Positions are never held or interpolated through missing detections. Membership
survives those gaps; reacquisition has a fixed search radius. Inferred identity
is a hypothesis and raw coordinates must be retained separately.
"""
import itertools
import numpy as np

MODEL_VERSION='1.5.0'


def persistent_groups(raw, blobs, social_radius=60., max_step=100., confirmation=3,
                      gap_speed=20., gap_radius_cap=300., max_reacquire_gap=30,
                      distant_confirmation=10):
    raw=np.asarray(raw,float);nframes,nanimals,_=raw.shape
    if (not np.isfinite([social_radius,max_step,gap_speed,gap_radius_cap]).all() or
            social_radius<=0 or max_step<=0 or confirmation<1 or gap_speed<=0
            or gap_radius_cap<social_radius or max_reacquire_gap<1
            or distant_confirmation<confirmation):
        raise ValueError('Invalid model parameters')
    xy=np.full_like(raw,np.nan);group_ids=np.full((nframes,nanimals),-1,int)
    inferred=np.zeros((nframes,nanimals),bool);ambiguous=np.zeros_like(inferred)
    identity_conflict=np.zeros_like(inferred)
    anchors=np.full((nframes,nanimals),-1,int)
    source=np.full((nframes,nanimals),'MISSING',dtype='<U24')
    # An entity can split or merge, but an animal's last defensible position
    # cannot be replaced by the new entity's position. Keep this gate across
    # missing frames, pending splits, and changes of group membership.
    member_last=np.full((nanimals,2),np.nan)
    member_last_frame=np.full(nanimals,-1,int)
    independent_last=np.full((nanimals,2),np.nan)
    independent_last_frame=np.full(nanimals,-1,int)
    distant_streak=[None for _ in range(nanimals)]
    rejoin_streak=[None for _ in range(nanimals)]
    # A live entity owns one or more identities independently of its current location.
    entities=[];initialized=set();next_id=0;events=[];reacquired=[]
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
    def reachable(t,a,p):
        last=member_last[a]
        if not np.isfinite(last).all():return True
        elapsed=t-member_last_frame[a]
        return elapsed>0 and np.linalg.norm(np.asarray(p,float)-last)<=min(gap_radius_cap,max_step*elapsed)
    for t in range(nframes):
        bs=detections(t)
        # Initialize only IDs assigned a finite coordinate near a real detection.
        for a in range(nanimals):
            if a in initialized:continue
            j=raw_blob(t,a,bs)
            if j is not None:
                entities.append(dict(id=next_id,members={a},last=np.array(bs[j]['centroid'],float),last_frame=t,split_key=None,split_count=0))
                next_id+=1;initialized.add(a)
        proposals=[];candidate_by_entity={};member_entity={}
        for e in entities:
            for a in e['members']:member_entity[a]=e
            gap=t-e['last_frame']
            # Group membership persists without detections, but no position is
            # assigned during the gap. Reacquire only over a bounded plausible
            # displacement; the old fixed 60-pixel gate lost moving piles.
            if gap>max_reacquire_gap or e.get('unresolved_identity',False):
                candidates=[]
            else:
                radius=(max_step if gap<=1 or e['split_count']>0 else
                        min(gap_radius_cap, max_step*gap,
                            social_radius+gap_speed*(gap-1)))
                candidates=[j for j,b in enumerate(bs) if any(
                    np.linalg.norm(np.asarray(b['centroid'])-p)<=radius
                    for p in [e['last']]+e.get('pending_positions',[]))
                    and all(reachable(t,a,b['centroid']) for a in e['members'])]
            candidate_by_entity[e['id']]=set(candidates)
            # Identity-guided choice is allowed only inside the spatial gate.
            votes={j for a in e['members'] if (j:=raw_blob(t,a,bs)) is not None
                   and j in candidates and reachable(t,a,bs[j]['centroid'])}
            partitions={}
            for a in e['members']:
                j=raw_blob(t,a,bs)
                # A raw ID beside another beetle is not evidence that this
                # hidden member teleported out of its previous pile. Apply
                # the same spatial gate to proposed splits as to pile motion.
                if j is not None and j in candidates and reachable(t,a,bs[j]['centroid']):
                    partitions.setdefault(j,set()).add(a)
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
            # A returning subset can separate, but a hidden member with no
            # independent blob cannot be assigned to an arbitrary branch of
            # a multiway split. Its contact location becomes unresolved.
            assigned=set().union(*partitions.values()) if partitions else set()
            unknown=e['members']-assigned if len(partitions)>1 else set()
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
                if unknown:
                    child=dict(id=next_id,members=unknown,last=e['last'].copy(),
                               last_frame=e['last_frame'],split_key=None,
                               split_count=0,unresolved_identity=True,
                               former_members=set(e['members'])-unknown)
                    next_id+=1;proposals.append((child,None))
                    events.append(dict(frame=t,kind='SPLIT_IDENTITY_UNRESOLVED',
                                       members=sorted(unknown)))
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
        # A member hidden in a moving pile may eventually emerge beyond the
        # pile's one-frame gate. A raw ID at that distant blob is insufficient:
        # it must be a smooth, sustained, singly labeled track. A blob owned by
        # another entity is an explicit conflict, never a silent reassignment.
        # Its displacement from the last *independent* sighting
        # must also be physically possible over the elapsed frames. If accepted,
        # retract enough prior inferred locations to leave a real missing gap.
        claimed={j for _,j in proposals if j is not None}
        departures=[];ownership_conflicts=set()
        for a,e in member_entity.items():
            j=raw_blob(t,a,bs)
            eligible=(j is not None
                      and j not in candidate_by_entity[e['id']]
                      and bs[j].get('identities',[])==[a+1]
                      and independent_last_frame[a]>=0)
            if eligible:
                point=np.asarray(bs[j]['centroid'],float)
                elapsed=t-independent_last_frame[a]
                eligible=(elapsed>0 and
                          np.linalg.norm(point-independent_last[a])<=max_step*elapsed)
            if not eligible:
                distant_streak[a]=None;continue
            previous=distant_streak[a]
            count=(previous['count']+1 if previous is not None and
                   previous['frame']==t-1 and
                   np.linalg.norm(point-previous['point'])<=max_step else 1)
            distant_streak[a]=dict(frame=t,point=point,count=count)
            if count>=distant_confirmation:
                if j in claimed:
                    identity_conflict[t,a]=True;ambiguous[t,a]=True
                    ownership_conflicts.add(a)
                    if count==distant_confirmation:
                        events.append(dict(frame=t,kind='RAW_ID_OWNERSHIP_CONFLICT',
                                           members=[a],blob_index=j))
                else:departures.append((a,e,j,point))
        for a,e,j,point in departures:
            # A later independent sighting never justifies retaining an
            # impossible inferred jump in the preceding canonical path.
            erased=[]
            while member_last_frame[a]>=0 and np.linalg.norm(point-member_last[a])>max_step*(t-member_last_frame[a]):
                prior=member_last_frame[a]
                if source[prior,a]=='ASSIGNED':break
                erased.append(prior)
                member_last_frame[a]=-1
                for earlier in range(prior-1,-1,-1):
                    if np.isfinite(xy[earlier,a]).all():
                        member_last[a]=xy[earlier,a];member_last_frame[a]=earlier
                        break
            if (member_last_frame[a]>=0 and
                    np.linalg.norm(point-member_last[a])>max_step*(t-member_last_frame[a])):
                distant_streak[a]=None;continue
            for prior in erased:
                xy[prior,a]=np.nan;inferred[prior,a]=False;ambiguous[prior,a]=True
                anchors[prior,a]=-1;source[prior,a]='MISSING'
            e['members'].remove(a)
            e['split_key']=None;e['split_count']=0
            e.pop('pending_positions',None)
            child=dict(id=next_id,members={a},last=point.copy(),last_frame=t,
                       split_key=None,split_count=0,verified_distant=True)
            next_id+=1
            proposals=[(entity,choice) for entity,choice in proposals if entity is not e or e['members']]
            proposals.append((child,j));claimed.add(j)
            events.append(dict(frame=t,kind='DISTANT_RAW_REACQUIRED',
                               members=[a],retracted_frames=sorted(erased)))
            reacquired.append((t,a,e['id'],child['id']))
            distant_streak[a]=None
        # A multiway split can leave an unseen identity without a defensible
        # branch. Rejoin it only when its own raw label repeatedly appears on
        # the *same detected blob* as a former pile member, close to its last
        # canonical position. An arbitrary nearby or distant pile is never a
        # substitute for this identity and continuity evidence.
        owners={}
        for owner,j in proposals:
            if j is not None:owners.setdefault(j,[]).append(owner)
        for unresolved,j0 in list(proposals):
            if j0 is not None or not unresolved.get('unresolved_identity'):
                continue
            for a in list(unresolved['members']):
                j=raw_blob(t,a,bs)
                matches=owners.get(j,[]) if j is not None else []
                eligible=(len(matches)==1 and
                          bool(matches[0]['members'] & unresolved['former_members']) and
                          reachable(t,a,bs[j]['centroid']) and
                          a+1 in bs[j].get('identities',[]))
                if not eligible:
                    rejoin_streak[a]=None;continue
                owner=matches[0]
                partner=min(owner['members'] & unresolved['former_members'])
                prior=rejoin_streak[a]
                count=(prior['count']+1 if prior is not None and
                       prior['frame']==t-1 and prior['partner']==partner else 1)
                rejoin_streak[a]=dict(frame=t,partner=partner,count=count)
                if count<confirmation:continue
                unresolved['members'].remove(a)
                owner['members'].add(a)
                events.append(dict(frame=t,kind='REJOIN_FORMER_PARTNER',
                                   members=[a,partner]))
                rejoin_streak[a]=None
            if not unresolved['members']:
                proposals=[(entity,choice) for entity,choice in proposals
                           if entity is not unresolved]
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
                if a in ownership_conflicts:
                    group_ids[t,a]=e['id'];ambiguous[t,a]=True
                    source[t,a]='RAW_PSC_CONFLICT'
                    continue
                assigned=a==visible
                other=raw_blob(t,a,bs)
                if other is not None and other!=j:
                    identity_conflict[t,a]=True
                disputed=(is_pile and other is not None and other!=j and not assigned
                          and reachable(t,a,bs[other]['centroid']))
                if disputed:
                    # A conflicting raw label is not yet a trusted departure,
                    # but the pile location is no longer defensible either.
                    group_ids[t,a]=e['id'];ambiguous[t,a]=True
                    source[t,a]='SPLIT_PENDING'
                    continue
                position=p if is_pile else (raw[t,a] if assigned else p)
                long_gap_reacquired=(e.get('verified_distant',False) and
                    member_last_frame[a]>=0 and
                    np.linalg.norm(position-member_last[a])<=max_step*(t-member_last_frame[a]))
                if not reachable(t,a,position) and not long_gap_reacquired:
                    group_ids[t,a]=e['id'];ambiguous[t,a]=True
                    continue
                xy[t,a]=position
                group_ids[t,a]=e['id'];inferred[t,a]=not assigned
                anchors[t,a]=visible if visible is not None else members[0]
                source[t,a]='ASSIGNED' if assigned else 'PSCP_BLOB' if is_pile else 'BLOB_CONTINUITY'
                member_last[a]=position;member_last_frame[a]=t
                if assigned:
                    independent_last[a]=position;independent_last_frame[a]=t
            e.pop('verified_distant',None)
        for e in unseen:
            active.append(e)
            for a in e['members']:
                group_ids[t,a]=e['id'];ambiguous[t,a]=bool(bs) or e.get('unresolved_identity',False)
                if a in ownership_conflicts:
                    source[t,a]='RAW_PSC_CONFLICT'
                # No position: preserve identity membership only.
                elif e.get('unresolved_identity',False):
                    source[t,a]='UNRESOLVED_SPLIT'
        entities=active
    # A confirmed raw identity can also identify the preceding *unlabeled*
    # moving blob. Trace it backward only through a unique, smooth path on
    # detections unclaimed by any other animal. The path must return to this
    # animal's former pile within the social radius; otherwise retain the
    # missing/PSC values and report the unresolved conflict for human review.
    for end,a,former_id,child_id in reacquired:
        point=xy[end,a].copy();trail=[]
        for prior in range(end-1,-1,-1):
            options=[]
            for j,b in enumerate(detections(prior)):
                ids=b.get('identities',[])
                own=ids==[a+1]
                unlabeled=not ids or all(i is None for i in ids)
                if not (own or unlabeled):continue
                p=np.asarray(b['centroid'],float)
                distance=np.linalg.norm(point-p)
                if distance>max_step:continue
                occupied=any(k!=a and np.isfinite(xy[prior,k]).all() and
                             np.linalg.norm(xy[prior,k]-p)<=5. for k in range(nanimals))
                if occupied:continue
                options.append((distance,j,p,own))
            options.sort(key=lambda item:item[0])
            if not options or (len(options)>1 and
                               options[1][0]-options[0][0]<=social_radius/2):break
            _,j,p,own=options[0]
            if group_ids[prior,a]==former_id and source[prior,a]=='ASSIGNED':break
            trail.append((prior,p,own))
            point=p
        if not trail:continue
        first=trail[-1][0]
        preceding=first-1
        anchored=(preceding>=0 and group_ids[preceding,a]==former_id and
                  np.isfinite(xy[preceding,a]).all() and
                  np.linalg.norm(point-xy[preceding,a])<=social_radius)
        if not anchored:
            events.append(dict(frame=end,kind='REID_BACKTRACE_UNRESOLVED',
                               members=[a],earliest_candidate=first))
            identity_conflict[first:end,a]=True
            continue
        for prior,p,own in trail:
            xy[prior,a]=raw[prior,a] if own else p
            inferred[prior,a]=not own
            group_ids[prior,a]=child_id
            source[prior,a]='ASSIGNED' if own else 'RETRO_REID_BLOB'
            ambiguous[prior,a]=not own
            anchors[prior,a]=a if own else -1
        events.append(dict(frame=end,kind='RETRO_REID_BACKTRACE',members=[a],
                           first_frame=first,last_frame=end-1,
                           unlabeled_frames=sum(not own for _,_,own in trail)))
    shared={(a,b):(group_ids[:,a]>=0)&(group_ids[:,a]==group_ids[:,b])
            for a,b in itertools.combinations(range(nanimals),2)}
    masks={(a,b):joined&np.isfinite(xy[:,a]).all(axis=1)&np.isfinite(xy[:,b]).all(axis=1)&(inferred[:,a]|inferred[:,b])
           for (a,b),joined in shared.items()}
    unresolved_masks={(a,b):joined&(~np.isfinite(xy[:,a]).all(axis=1)|~np.isfinite(xy[:,b]).all(axis=1))
                      for (a,b),joined in shared.items()}
    return dict(xy=xy,group_ids=group_ids,inferred=inferred,ambiguous=ambiguous,anchors=anchors,
                identity_conflict=identity_conflict,
                masks=masks,unresolved_masks=unresolved_masks,source=source,events=events)
