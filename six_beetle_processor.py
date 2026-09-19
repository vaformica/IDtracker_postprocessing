"""Six-beetle analysis; see SIX_BEETLE_METHODS.html for scientific definitions.

Uses the tested v0.8.1 primitives without changing the two-animal processor.
Outputs are review candidates, never automatically approved statistical data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import tempfile

import numpy as np
import processor as legacy

SCRIPT_VERSION = '0.4.1-six-beetle'

FRAME_STATE_NAMES = ('OBSERVED_ID_ASSIGNED', 'MISSING', 'PRESUMED_SOCIAL_DISAPPEARANCE')
FRAME_STATE_COLORS = ('#0072B2', '#D55E00', '#E6AB02')


def presumed_groups(xy, threshold):
    """Causal visible-anchor inference; raw coordinates are never changed.

    A missing group transfers to a unique nearby currently visible anchor using
    positions in the immediately preceding frame. Multiple possible anchors or
    loss of every visible member leaves coordinates unresolved. Reappearing IDs
    always use their measured position and leave their former presumed group.
    """
    xy = np.asarray(xy, dtype=float)
    valid = np.isfinite(xy).all(axis=2)
    estimated = xy.copy()
    anchors = np.full(valid.shape, -1, dtype=int)
    ambiguous = np.zeros(valid.shape, dtype=bool)
    for t in range(len(xy)):
        visible = np.flatnonzero(valid[t])
        anchors[t, visible] = visible
        if t == 0:
            continue
        previous = anchors[t-1]
        for anchor in sorted(set(previous) - {-1}):
            members = np.flatnonzero(previous == anchor)
            missing = members[~valid[t, members]]
            if not len(missing):
                continue
            # Keep the established visible anchor; returning members detach.
            if valid[t, anchor]:
                target = anchor
            else:
                # A newly visible former member can carry the group if unique.
                candidates = set(members[valid[t, members]].tolist())
                old_position = estimated[t-1, anchor]
                for other in visible:
                    if not valid[t-1, other]:
                        continue
                    if np.linalg.norm(xy[t-1, other] - old_position) <= threshold:
                        candidates.add(int(other))
                if len(candidates) != 1:
                    ambiguous[t, missing] = len(candidates) > 1
                    continue
                target = candidates.pop()
            anchors[t, missing] = target
            estimated[t, missing] = xy[t, target]
    masks = {(a,b): (anchors[:,a] >= 0) & (anchors[:,a] == anchors[:,b])
             for a,b in itertools.combinations(range(xy.shape[1]),2)}
    return dict(xy=estimated, anchors=anchors, inferred=~valid & (anchors>=0),
                ambiguous=ambiguous, masks=masks)


def pair_contact_masks(pair_masks, events, start):
    """Keep disappearance inference attached to its exact candidate pair.

    Individual contact masks cannot establish a pair: two beetles may each
    interact with different partners. Only pair-specific events are used.
    """
    inferred = {pair: np.zeros_like(mask, dtype=bool) for pair, mask in pair_masks.items()}
    ambiguous = {pair: np.zeros_like(mask, dtype=bool) for pair, mask in pair_masks.items()}
    for event in events:
        if event['kind'] not in ('DISAPPEARANCE_CANDIDATE', 'PRESUMED_GROUP_CONTACT') or event.get('window', 'full') != 'full':
            continue
        pair = (event['animal_a'], event['animal_b'])
        lo = event['start_global_frame'] - start
        stop = event['end_global_frame_inclusive'] - start + 1
        inferred[pair][lo:stop] = True
        if event['candidate_partner_count'] > 1:
            ambiguous[pair][lo:stop] = True
    return inferred, ambiguous


def frame_states(xy, start, pair_masks, events):
    """Three display states plus separate observation and inference evidence.

    Presumed contact takes display priority over observed/missing. It includes
    observed proximity and both members of a bounded disappearance candidate.
    This never changes coordinates or the existing movement/missing summaries.
    """
    valid = np.isfinite(xy).all(axis=2)
    partner_count = np.zeros(valid.shape, dtype=np.int16)
    disappearance = np.zeros(valid.shape, dtype=bool)
    ambiguous = np.zeros(valid.shape, dtype=bool)
    for (a, b), mask in pair_masks.items():
        partner_count[:, a] += mask
        partner_count[:, b] += mask
    for event in events:
        if event['kind'] not in ('DISAPPEARANCE_CANDIDATE', 'PRESUMED_GROUP_CONTACT') or event.get('window', 'full') != 'full':
            continue
        lo = event['start_global_frame'] - start
        stop = event['end_global_frame_inclusive'] - start + 1
        for animal in (event['animal_a'], event['animal_b']):
            disappearance[lo:stop, animal] = True
            if event['candidate_partner_count'] > 1:
                ambiguous[lo:stop, animal] = True
    states = np.where(valid, 0, 1).astype(np.uint8)
    states[(partner_count > 0) | disappearance] = 2
    return dict(states=states, coordinate_present=valid,
                proximity_partner_count=partner_count,
                disappearance_candidate=disappearance,
                ambiguous_disappearance=ambiguous)


def regions(xy, rois, wall_buffer, fungus_buffer):
    """Centroid or midpoint membership; NaNs belong to no region."""
    valid = np.isfinite(xy).all(axis=1)
    def inside(poly):
        mask = np.zeros(len(xy), dtype=bool)
        mask[valid] = legacy.points_inside_polygon(xy[valid], poly)
        return mask
    def edge(poly, width):
        mask = np.zeros(len(xy), dtype=bool)
        mask[valid] = legacy.distance_to_polygon_boundary(xy[valid], poly) <= width
        return mask
    arena = inside(rois[0])
    fungi = [inside(poly) for poly in rois[1:]]
    union = np.logical_or.reduce(fungi)
    wall = arena & edge(rois[0], wall_buffer)
    result = {'arena': arena, 'outside_arena': valid & ~arena,
              'wall': wall, 'non_wall': valid & ~wall,
              'any_fungus': union, 'off_fungus': valid & ~union,
              'open_arena': arena & ~wall & ~union}
    for i, (poly, mask) in enumerate(zip(rois[1:], fungi), 1):
        border = mask & edge(poly, fungus_buffer)
        result[f'fungus_{i}'] = mask
        result[f'fungus_{i}_edge'] = border
        result[f'fungus_{i}_interior'] = mask & ~border
    return result


def social_network(xy, start, threshold):
    """Evaluate all 15 pairs independently, retaining multi-partner ambiguity."""
    pair_rows, events, masks = [], [], {}
    for a, b in itertools.combinations(range(6), 2):
        result = legacy.compute_social_candidates(xy[:, [a, b]], threshold)
        masks[a, b] = result['within_mask']
        both = np.isfinite(xy[:, [a, b]]).all(axis=(1, 2))
        pair_rows.append(dict(animal_a=a, animal_b=b,
            jointly_visible_frames=int(both.sum()),
            proximity_frames=int(result['within_mask'].sum()),
            proximity_proportion_jointly_visible=(float(result['within_mask'].sum()/both.sum()) if both.any() else ''),
            proximity_bouts=len(legacy._events_from_mask(result['within_mask'])),
            visible_return_events=result['return_events'],
            disappearance_candidate_events=len(result['disappearance_events'])))
        for event in legacy._events_from_mask(result['within_mask']):
            events.append(dict(kind='PROXIMITY', animal_a=a, animal_b=b,
                missing_animal='', start_global_frame=start+event['start_offset'],
                end_global_frame_inclusive=start+event['end_offset'],
                frames=event['frames'], candidate_partner_count='', attribution='OBSERVED_PROXIMITY'))
        for event in result['disappearance_events']:
            missing = (a, b)[event['missing_animal']]
            previous = xy[event['start_offset']-1]
            distances = np.linalg.norm(previous - previous[missing], axis=1)
            count = int(((distances <= threshold) & (np.arange(6) != missing)).sum())
            events.append(dict(kind='DISAPPEARANCE_CANDIDATE', animal_a=a, animal_b=b,
                missing_animal=missing, start_global_frame=start+event['start_offset'],
                end_global_frame_inclusive=start+event['end_offset'],
                frames=event['end_offset']-event['start_offset']+1,
                candidate_partner_count=count,
                attribution='AMBIGUOUS_MULTIPLE_PARTNERS' if count > 1 else 'SINGLE_CANDIDATE_NOT_CONFIRMED'))
    return pair_rows, events, masks


def summarize_window(xy, animal, lo, hi, label, start, rois, settings, turtling, masks):
    """Inclusive coordinates, adjacent-step sums, explicit matching denominators."""
    track = xy[lo:hi+1, animal]
    valid = np.isfinite(track).all(axis=1)
    lengths = np.linalg.norm(np.diff(track, axis=0), axis=1)
    possible = valid[:-1] & valid[1:]
    accepted = possible & (lengths <= settings['jump_threshold_px'])
    rejected = possible & ~accepted
    distance = float(lengths[accepted].sum()) if accepted.any() else ''
    rframes = regions(track, rois, settings['wall_buffer_px'], settings['fungus_buffer_px'])
    rsteps = regions((track[:-1]+track[1:])/2, rois, settings['wall_buffer_px'], settings['fungus_buffer_px'])
    near = np.zeros(len(track), dtype=bool)
    partners = np.zeros(len(track), dtype=int)
    for pair, mask in masks.items():
        if animal in pair:
            near |= mask[lo:hi+1]
            partners += mask[lo:hi+1]
    social_steps = accepted & near[:-1] & near[1:]
    row = dict(animal_id=animal, window=label, status='CALCULATED',
        start_global_frame=start+lo, end_global_frame_inclusive=start+hi,
        frame_observations=len(track), available_steps=max(0, len(track)-1),
        valid_coordinate_frames=int(valid.sum()), missing_coordinate_frames=int((~valid).sum()),
        missing_coordinate_proportion=float((~valid).mean()),
        accepted_steps=int(accepted.sum()), missing_endpoint_steps=int((~possible).sum()),
        rejected_jump_steps=int(rejected.sum()), distance_px=distance,
        distance_px_per_valid_step=(distance/int(accepted.sum()) if accepted.any() else ''),
        distance_px_per_available_step=(distance/(len(track)-1) if accepted.any() and len(track)>1 else ''),
        social_any_partner_frames=int(near.sum()),
        social_multiple_partner_frames=int((partners > 1).sum()),
        social_distance_px=(float(lengths[social_steps].sum()) if accepted.any() else ''),
        turtling_candidate_frames=int(turtling[lo:hi+1].sum()),
        turtling_candidate_events=len(legacy._events_from_mask(turtling[lo:hi+1])))
    region_rows = []
    for name, mask in rframes.items():
        steps = accepted & rsteps[name]
        region_rows.append(dict(animal_id=animal, window=label, region=name,
            status='CALCULATED', start_global_frame=start+lo, end_global_frame_inclusive=start+hi,
            coordinate_frames=int(mask.sum()), accepted_steps=int(steps.sum()),
            distance_px=float(lengths[steps].sum()) if accepted.any() else ''))
    return row, region_rows


def analyze_six(trajectory, session, start, window=7200, threshold=30.,
                wall_buffer_px=30., fungus_buffer_px=30., social_distance_threshold_px=60.,
                jump_threshold_px=200.):
    numeric = [threshold, social_distance_threshold_px, jump_threshold_px]
    if start <= 0 or window <= 0 or not all(np.isfinite(v) and v > 0 for v in numeric):
        raise ValueError('Positive start, window, and finite positive thresholds are required')
    if not all(np.isfinite(v) and v >= 0 for v in [wall_buffer_px, fungus_buffer_px]):
        raise ValueError('Buffer widths must be finite and nonnegative')
    trajectory, session = Path(trajectory), Path(session)
    source_kind = legacy.validate_trajectory_source(trajectory)
    data = legacy.load_trajectories(trajectory)
    if data.shape[1] != 6:
        raise ValueError(f'Expected exactly six animals; found {data.shape[1]}')
    rois = legacy.load_rois(session)
    if len(rois) != 4:
        raise ValueError(f'Expected four ROIs: arena then three fungi; found {len(rois)}')
    for poly in rois:
        area = abs(np.sum(poly[:,0]*np.roll(poly[:,1], -1)-poly[:,1]*np.roll(poly[:,0], -1)))/2
        if area <= 0:
            raise ValueError('ROI polygon must have positive area')
    if start + window >= len(data):
        raise ValueError('Inclusive global window is outside the trajectory array')
    xy = data[start:start+window+1].copy()
    settings = dict(start=start, window=window, threshold=threshold, wall_buffer_px=wall_buffer_px,
        fungus_buffer_px=fungus_buffer_px, social_distance_threshold_px=social_distance_threshold_px,
        jump_threshold_px=jump_threshold_px)
    pairs, events, masks = social_network(xy, start, social_distance_threshold_px)
    wakes = [legacy.compute_wake_threshold_result(xy[:,i], analysis_start_global_frame=start,
        movement_threshold_px=threshold, one_frame_jump_threshold_px=jump_threshold_px) for i in range(6)]
    shared = max(int(w['latency']) for w in wakes) if all(w['latency'] != '' for w in wakes) else None
    animals, windows, region_rows, turtling_masks = [], [], [], []
    for animal, wake in enumerate(wakes):
        turtle = legacy.compute_turtling_candidates(xy[:,animal])
        on_fungus = regions(xy[:,animal], rois, wall_buffer_px, fungus_buffer_px)['any_fungus']
        turtle_mask = turtle['mask'] & ~on_fungus
        turtling_masks.append(turtle_mask)
        animals.append(dict(animal_id=animal, baseline_x=wake['baseline_x'], baseline_y=wake['baseline_y'],
            threshold_crossing_global_frame=wake['crossing'], latency_to_threshold_frames=wake['latency'],
            wake_status=wake['status'], warning=wake['warning']))
        specs = [('full', 0, window, ''),
                 ('post_wake', wake['latency'], window, 'NO_RELIABLE_WAKE'),
                 ('post_wake_3600', shared, None if shared is None else shared+3600, 'NO_RELIABLE_WAKE_FOR_ALL_SIX')]
        for label, lo, hi, reason in specs:
            if lo in ('', None) or hi > window:
                windows.append(dict(animal_id=animal, window=label,
                    status=reason if lo in ('', None) else 'COMPLETE_3600_INTERVAL_WINDOW_DOES_NOT_FIT'))
                continue
            row, rr = summarize_window(xy, animal, int(lo), int(hi), label, start, rois, settings, turtle_mask, masks)
            windows.append(row)
            region_rows.extend(rr)
    pair_windows = []
    if shared is not None and shared+3600 <= window:
        fixed_pairs, fixed_events, _ = social_network(xy[shared:shared+3601], start+shared, social_distance_threshold_px)
        pair_windows = [dict(window='post_wake_3600', **row) for row in fixed_pairs]
        events += [dict(window='post_wake_3600', **e) for e in fixed_events]
    pairs = [dict(window='full', **row) for row in pairs] + pair_windows
    for event in events:
        event.setdefault('window', 'full')
    # Initialize group membership before the selected window, then slice it.
    history = presumed_groups(data[:start+window+1], social_distance_threshold_px)
    group = {key: value[start:] for key,value in history.items() if key != 'masks'}
    group['masks'] = {pair: mask[start:] for pair,mask in history['masks'].items()}
    # Legacy bounded disappearance candidates do not implement Vince's rule.
    legacy_events = events
    events = [e for e in events if e['kind'] != 'DISAPPEARANCE_CANDIDATE']
    for (a,b),mask in group['masks'].items():
        for event in legacy._events_from_mask(mask):
            events.append(dict(kind='PRESUMED_GROUP_CONTACT',window='full',animal_a=a,animal_b=b,
                start_global_frame=start+event['start_offset'],end_global_frame_inclusive=start+event['end_offset'],
                frames=event['frames'],candidate_partner_count=1,attribution='UNIQUE_VISIBLE_ANCHOR'))
    for row in pairs:
        mask=group['masks'][row['animal_a'],row['animal_b']]
        if row['window'] != 'full': mask=mask[shared:shared+3601]
        row['legacy_disappearance_candidate_events']=row.pop('disappearance_candidate_events')
        row['presumed_social_disappearance_events']=len(legacy._events_from_mask(mask))
        row['presumed_group_frames']=int(mask.sum())
    timeline = frame_states(xy, start, masks, events)
    timeline['ambiguous_disappearance'] |= group['ambiguous']
    timeline['states'] = np.where(np.isfinite(xy).all(axis=2),0,1).astype(np.uint8)
    timeline['states'][timeline['disappearance_candidate']] = 2
    estimated_windows, estimated_regions = [], []
    adjusted_masks={pair: mask | group['masks'][pair] for pair,mask in masks.items()}
    for row in windows:
        if row['status'] != 'CALCULATED':
            estimated_windows.append(row.copy());continue
        animal=row['animal_id']
        wr,rr=summarize_window(group['xy'],animal,row['start_global_frame']-start,
            row['end_global_frame_inclusive']-start,row['window'],start,rois,settings,
            turtling_masks[animal],adjusted_masks)
        estimated_windows.append(wr);estimated_regions.extend(rr)

    metadata = dict(script_version=SCRIPT_VERSION, base_processor_version=legacy.SCRIPT_VERSION,
        trajectory_file=str(trajectory.resolve()), session_folder=str(session.resolve()),
        trajectory_source_kind=source_kind, settings=settings, roi_order=['arena','fungus_1','fungus_2','fungus_3'],
        fungus_numbering_convention='Left to right; fungus 1 is the leftmost or bottommost bracket, as specified by Vince. Input order is preserved, not automatically sorted.',
        frame_state_definition='Presumed social disappearance takes precedence: membership in a causal visible-anchor group. Observed proximity alone does not change the individual display state. Otherwise coordinate present = observed/ID assigned; no coordinate = missing. Ambiguous disappearance remains flagged separately. Observed refers to the selected trajectory source, which may already contain IDtracker gap filling.',
        rois=[p.tolist() for p in rois], fixed_anchor_rule='ALL_SIX_WAKE_LATEST_CROSSING',
        qc_status='UNREVIEWED', coordinate_substitution=True, raw_coordinates_preserved=True,
        presumed_group_rule='Unique nearby visible anchor in immediately prior frame; missing members follow anchor, groups merge when anchor disappears near another visible beetle; returning IDs detach; no visible anchor or multiple candidates leaves position unresolved.',
        interpretation='Proximity/disappearance candidates do not establish attack or posture.',
        turtling_settings=dict(window_frames=120,min_path_px=120.,max_radius90_px=35.,min_turn_rotations=3.,max_straightness=.25,max_step_px=20.))
    return dict(animals=animals, windows=windows, regions=region_rows, pairs=pairs, events=events,
                metadata=metadata, xy=xy, turtling_masks=turtling_masks, masks=masks,
                frame_timeline=timeline, group=group, estimated_windows=estimated_windows,
                estimated_regions=estimated_regions, legacy_events=legacy_events)


def disappearance_offsets(track):
    """Last observed coordinates immediately before a missing run; no imputation."""
    valid = np.isfinite(track).all(axis=1)
    return np.flatnonzero(valid[:-1] & ~valid[1:])


def fungus_summary(result):
    fps = result['metadata'].get('frames_per_second')
    rows = []
    for animal in range(6):
        row = {'animal_id': animal}
        for fungus in range(1, 4):
            region = next(r for r in result['regions'] if r['animal_id'] == animal
                          and r['window'] == 'full' and r['region'] == f'fungus_{fungus}')
            count = region['coordinate_frames']
            row.update({f'fungus_{fungus}_frames': count,
                        f'fungus_{fungus}_seconds': count / fps if fps else '',
                        f'fungus_{fungus}_distance_px': region['distance_px']})
        rows.append(row)
    return rows


def write_pdf(result, destination, video, cell):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.collections import LineCollection
    from textwrap import fill
    meta = result['metadata']; settings = meta['settings']; xy = result['xy']
    rois = [np.asarray(p) for p in meta['rois']]
    colors = plt.get_cmap('tab10').colors
    def footer(fig, page):
        fig.text(.06,.025,f'{SCRIPT_VERSION}  |  UNREVIEWED  |  {page}',fontsize=8,color='#555555')
        fig.text(.06,.048,fill(f'{video} | Cell {cell}',135),fontsize=7,color='#555555')
    def geometry(ax):
        for i, poly in enumerate(rois):
            p = np.vstack([poly,poly[0]])
            ax.plot(p[:,0],p[:,1],color='#333333' if i==0 else '#54956b',lw=1.3)
            if i: ax.text(*poly.mean(axis=0),f'F{i}',ha='center',fontsize=10,color='#285d3b')
        ax.set_aspect('equal'); ax.invert_yaxis(); ax.set_xlabel('x (pixels)'); ax.set_ylabel('y (pixels)')
        ax.grid(alpha=.15)
    with PdfPages(destination) as pdf:
        fig=plt.figure(figsize=(11.7,8.3))
        fig.text(.06,.92,'Six beetles / three fungus ROIs',fontsize=23,weight='bold')
        fig.text(.06,.845,fill(f'{video} | Cell {cell}',105),fontsize=11)
        fig.text(.06,.78,f"Global frames {settings['start']}–{settings['start']+settings['window']} inclusive | {settings['window']+1} observations",fontsize=11)
        ax=fig.add_axes([.06,.37,.88,.34]); ax.axis('off')
        full=[r for r in result['windows'] if r['window']=='full']
        rows=[[r['animal_id'],r['missing_coordinate_frames'],f"{100*r['missing_coordinate_proportion']:.1f}%",r['rejected_jump_steps'],f"{r['distance_px']:.1f}" if r['distance_px']!='' else 'NA',result['animals'][r['animal_id']]['threshold_crossing_global_frame'] or 'NA'] for r in full]
        table=ax.table(cellText=rows,colLabels=['Beetle ID','Missing frames','Missing %','Rejected steps','Distance (px)','Wake frame'],loc='center',cellLoc='center')
        table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1,1.8)
        fig.text(.06,.29,fill('Review required: proximity and disappearance are candidate social contact, not proof of attack. Raw coordinates remain unchanged. Missing members of an unambiguous presumed group follow its visible anchor in separately labeled estimates.',120),fontsize=11)
        fig.text(.06,.20,fill(f"Source: {meta['trajectory_source_kind']}. Social radius: {settings['social_distance_threshold_px']:g} px. Jump cutoff: {settings['jump_threshold_px']:g} px. Fixed comparison: 3600 intervals after the latest reliable wake of all six animals.",120),fontsize=10)
        footer(fig,1); pdf.savefig(fig); plt.close(fig)
        for page, ids in enumerate([range(6)]+[[i] for i in range(6)],2):
            overview=page==2
            fig, axes=plt.subplots(1,1,figsize=(11.7,8.3),squeeze=False)
            fig.suptitle('All six trajectories' if overview else f'Beetle {ids[0]}: trajectory and disappearances',fontsize=17)
            for idx,animal in enumerate(ids):
                ax=axes[0,0] if overview else axes[0,idx]
                if not overview or idx==0: geometry(ax)
                track=xy[:,animal]
                segments=legacy.continuous_path_segments(track,settings['jump_threshold_px'])
                ax.add_collection(LineCollection([s[1] for s in segments],colors=[colors[animal]],linewidths=1.1 if not overview else .7,alpha=.85))
                good=np.isfinite(track).all(axis=1)
                if good.any():
                    ax.scatter(track[good,0][0],track[good,1][0],color=colors[animal],marker='o',s=25,label=f'Beetle {animal}')
                if not overview:
                    mask=result['turtling_masks'][animal]
                    ax.scatter(track[mask,0],track[mask,1],s=8,color='darkred',label='Candidate turtling')
                    est=result['group']['xy'][:,animal]
                    is_inferred=result['group']['inferred'][:,animal]
                    edges=np.stack([est[:-1],est[1:]],axis=1)
                    accepted=np.isfinite(edges).all(axis=(1,2)) & (np.linalg.norm(est[1:]-est[:-1],axis=1)<=settings['jump_threshold_px'])
                    inferred_edges=accepted & (is_inferred[:-1] | is_inferred[1:])
                    ax.add_collection(LineCollection(edges[inferred_edges],colors=[colors[animal]],linewidths=1.5,linestyles='dashed',alpha=.8))
                    ax.plot([],[],color=colors[animal],ls='--',label='Presumed social disappearance')
                    gone=disappearance_offsets(track)
                    ax.scatter(track[gone,0],track[gone,1],s=65,marker='x',color='#D55E00',linewidths=1.7,
                               label='Last raw coordinate before disappearance',zorder=5)
                    fig.text(.08,.085,'Solid: raw assigned coordinates. Dashed: presumed anchor-following position. X: last raw coordinate before a gap.',fontsize=10)
                ax.autoscale_view(); ax.legend(loc='upper right',fontsize=8)
            fig.tight_layout(rect=[.03,.10,.97,.94]); footer(fig,page); pdf.savefig(fig); plt.close(fig)
        fig,ax=plt.subplots(figsize=(11.7,8.3))
        from matplotlib.patches import Patch
        inferred, ambiguous = pair_contact_masks(result['masks'], result['events'], settings['start'])
        for row,(pair,mask) in enumerate(result['masks'].items()):
            for state_mask, color in [(mask, '#277d8e'), (inferred[pair], FRAME_STATE_COLORS[2])]:
                ax.broken_barh([(settings['start']+e['start_offset']-.5,e['frames']) for e in legacy._events_from_mask(state_mask)],(row-.32,.64),facecolors=color)
            ax.broken_barh([(settings['start']+e['start_offset']-.5,e['frames']) for e in legacy._events_from_mask(ambiguous[pair])],
                          (row-.32,.64),facecolors='none',edgecolors='#333333',linewidth=0,hatch='////')
        ax.set_yticks(range(15),[f'{a} – {b}' for a,b in result['masks']]); ax.set_xlabel('Global frame'); ax.set_ylabel('Beetle pair')
        ax.set_xlim(settings['start']-.5,settings['start']+settings['window']+.5)
        fig.suptitle('Proximity and presumed social disappearance for all 15 pairs',fontsize=17,y=.96)
        ax.grid(axis='x',alpha=.2)
        fig.legend(handles=[Patch(facecolor='#277d8e',label='Observed proximity'),
                            Patch(facecolor=FRAME_STATE_COLORS[2],label='Presumed social disappearance'),
                            Patch(facecolor='white',edgecolor='#333333',hatch='////',label='Ambiguous partner attribution')],
                   loc='upper center',bbox_to_anchor=(.5,.92),ncol=1,frameon=False,fontsize=10)
        fig.text(.08,.11,fill('Gold marks members of the same presumed social disappearance group, including chains of three or more beetles. Ambiguous anchor choices are not assigned a location. Blank means no proximity or disappearance evidence, not confirmed absence of contact. Events remain available at exact global frames in events.csv.',125),fontsize=9)
        fig.subplots_adjust(left=.10,right=.97,bottom=.21,top=.78)
        footer(fig,9); pdf.savefig(fig); plt.close(fig)
        # Preserve the pairwise plot above; this additional page shows one row
        # per tracked identity and uses nearest-neighbor cells (no smoothing).
        from matplotlib.colors import ListedColormap, BoundaryNorm
        from matplotlib.patches import Patch
        timeline = result['frame_timeline']
        fig, ax = plt.subplots(figsize=(11.7, 8.3))
        begin = settings['start']
        end = begin + settings['window']
        ax.imshow(timeline['states'].T, aspect='auto', interpolation='nearest',
                  cmap=ListedColormap(FRAME_STATE_COLORS),
                  norm=BoundaryNorm([-.5, .5, 1.5, 2.5], 3),
                  extent=(begin-.5, end+.5, 5.5, -.5))
        for animal in range(6):
            for event in legacy._events_from_mask(timeline['ambiguous_disappearance'][:, animal]):
                ax.broken_barh([(begin+event['start_offset']-.5, event['frames'])],
                              (animal-.5, 1), facecolors='none',
                              edgecolors='#333333', linewidth=0, hatch='////')
        ax.set_yticks(range(6), [f'Beetle {i}' for i in range(6)])
        ax.set_xlabel('Global frame (inclusive observations)')
        fig.suptitle('Per-frame identity and presumed social disappearance', fontsize=17, y=.95)
        for boundary in np.arange(.5, 5.5):
            ax.axhline(boundary, color='white', linewidth=.7, alpha=.7)
        handles = [Patch(facecolor=color, label=label) for color, label in zip(
            FRAME_STATE_COLORS, ['Observed / ID assigned', 'Missing / unresolved', 'Presumed social disappearance'])]
        handles.append(Patch(facecolor='white', edgecolor='#333333', hatch='////',
                             label='Ambiguous disappearance'))
        fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5,.89),
                   ncol=2, frameon=False, fontsize=10)
        fig.text(.08,.155,fill('Gold marks presumed social disappearance: group members sharing one visible anchor. Proximity alone does not turn this panel gold. Hatching marks uncertain partner attribution. This is not proof of attack; inferred coordinates are stored separately from the original missing values.',125),fontsize=10)
        fig.text(.08,.10,fill('Observed means a coordinate assigned to this ID in the selected trajectory file; IDtracker may already have filled gaps. Very brief states may be hard to see at page scale; frame_states.csv preserves every frame and its evidence.',125),fontsize=9)
        fig.subplots_adjust(left=.10,right=.96,bottom=.28,top=.78)
        footer(fig,10); pdf.savefig(fig); plt.close(fig)
        fps=meta.get('frames_per_second')
        fig=plt.figure(figsize=(11.7,8.3)); ax=fig.add_subplot(111,projection='3d')
        from mpl_toolkits.mplot3d.art3d import Line3DCollection
        for animal in range(6):
            est=result['group']['xy'][:,animal]
            inferred=result['group']['inferred'][:,animal]
            z=np.arange(len(est))/fps if fps else np.arange(len(est))+settings['start']
            positions=np.column_stack([est,z]);edges=np.stack([positions[:-1],positions[1:]],axis=1)
            accepted=np.isfinite(edges).all(axis=(1,2)) & (np.linalg.norm(est[1:]-est[:-1],axis=1)<=settings['jump_threshold_px'])
            presumed=inferred[:-1] | inferred[1:]
            for mask,style in [(accepted & ~presumed,'solid'),(accepted & presumed,'dashed')]:
                if mask.any(): ax.add_collection3d(Line3DCollection(edges[mask],colors=[colors[animal]],linewidths=1,linestyles=style))
            ax.plot([],[],[],color=colors[animal],label=f'Beetle {animal}')
            gone=disappearance_offsets(xy[:,animal])
            ax.scatter(xy[gone,animal,0],xy[gone,animal,1],gone/fps if fps else gone+settings['start'],marker='x',color='#D55E00',s=20)
        finite=result['group']['xy'][np.isfinite(result['group']['xy']).all(axis=2)]
        ax.set_xlim(finite[:,0].min(),finite[:,0].max());ax.set_ylim(finite[:,1].min(),finite[:,1].max())
        ax.set_zlim(0 if fps else settings['start'],settings['window']/fps if fps else settings['start']+settings['window'])
        for i,poly in enumerate(rois):
            poly=np.vstack([poly,poly[0]])
            ax.plot(poly[:,0],poly[:,1],np.full(len(poly),0 if fps else settings['start']),
                    color='#333333' if i==0 else '#54956b',alpha=.65)
        ax.invert_yaxis(); ax.set_xlabel('x (pixels)');ax.set_ylabel('y (pixels)')
        ax.set_zlabel('Seconds from analysis start' if fps else 'Global frame')
        ax.view_init(elev=26,azim=-60);ax.legend(loc='upper left',fontsize=9)
        fig.suptitle('3D trajectories including presumed social disappearance positions',fontsize=17)
        fig.text(.08,.085,'Solid: raw positions. Dashed: presumed social disappearance. Orange X: last raw position before disappearance. Unresolved gaps omitted.',fontsize=10)
        fig.subplots_adjust(bottom=.14,top=.92);footer(fig,11);pdf.savefig(fig);plt.close(fig)
        fig=plt.figure(figsize=(11.7,8.3));fig.suptitle('Observed time and distance on each fungus',fontsize=20,y=.94)
        ax=fig.add_axes([.05,.33,.90,.44]);ax.axis('off')
        rows=[]
        for row in fungus_summary(result):
            values=[row['animal_id']]
            for i in range(1,4):
                time=row[f'fungus_{i}_seconds'] if fps else row[f'fungus_{i}_frames']
                distance=row[f'fungus_{i}_distance_px']
                values += [f'{time:.2f}',f'{distance:.1f}' if distance!='' else 'NA']
            rows.append(values)
        cols=['Beetle ID']
        for i in range(1,4):cols += [f'F{i} time ('+('s)' if fps else 'frames)'),f'F{i} distance (px)']
        table=ax.table(cellText=rows,colLabels=cols,loc='center',cellLoc='center')
        table.auto_set_font_size(False);table.set_fontsize(11);table.scale(1,2.2)
        note='Full analysis window. Occupancy counts assigned-coordinate frames inside each fungus polygon'
        note += f', divided by {fps:g} frames/s.' if fps else '; frame rate unavailable, so time is reported in frames.'
        note += ' Distance sums accepted adjacent steps whose midpoint lies inside the polygon. Missing coordinates add neither time nor distance. Fungus numbering follows input order, left to right.'
        fig.text(.07,.20,fill(note,125),fontsize=11)
        footer(fig,12);pdf.savefig(fig);plt.close(fig)
        fig=plt.figure(figsize=(11.7,8.3));fig.suptitle('Fungus occupancy including presumed social disappearance positions',fontsize=19,y=.94)
        ax=fig.add_axes([.05,.33,.90,.44]);ax.axis('off');rows=[]
        adjusted=dict(result,regions=result['estimated_regions'])
        for row in fungus_summary(adjusted):
            values=[row['animal_id']]
            for i in range(1,4):
                time=row[f'fungus_{i}_seconds'] if fps else row[f'fungus_{i}_frames']
                distance=row[f'fungus_{i}_distance_px']
                values += [f'{time:.2f}',f'{distance:.1f}' if distance!='' else 'NA']
            rows.append(values)
        table=ax.table(cellText=rows,colLabels=cols,loc='center',cellLoc='center')
        table.auto_set_font_size(False);table.set_fontsize(11);table.scale(1,2.2)
        fig.text(.07,.20,fill('Estimated totals: raw positions plus missing beetles assigned to a unique visible group anchor. All members follow that anchor until they reappear or its location becomes unresolved. A group can grow beyond two beetles. Distances and occupancy during inferred periods are assumptions, not observations. Original-coordinate totals are on the preceding page.',125),fontsize=11)
        footer(fig,13);pdf.savefig(fig);plt.close(fig)




def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): digest.update(chunk)
    return digest.hexdigest()


def write_bundle(result, output, video, cell, pdf_name=None):
    """Publish a complete new directory, never overwrite previous research output."""
    output=Path(output)
    if output.exists(): raise FileExistsError(f'Refusing existing output: {output}')
    output.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.six-beetle-',dir=output.parent))
    try:
        meta=result['metadata']; meta.update(video=video,cell_label=cell)
        result['fungus_summary'] = fungus_summary(result)
        result['estimated_fungus_summary'] = fungus_summary(dict(result,regions=result['estimated_regions']))
        for name in ['estimated_fungus_summary','estimated_windows','estimated_regions','legacy_events','fungus_summary','animals','windows','regions','pairs','events']:
            rows=result[name]
            fields=list(dict.fromkeys(key for row in rows for key in row))
            if not fields: fields=['window','kind','animal_a','animal_b','missing_animal','start_global_frame','end_global_frame_inclusive','frames','candidate_partner_count','attribution']
            with (staging/f'{name}.csv').open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader();writer.writerows(rows)
        timeline = result['frame_timeline']
        fields = ['global_frame', 'animal_id', 'state', 'coordinate_present',
                  'proximity_partner_count', 'disappearance_candidate',
                  'ambiguous_disappearance']
        with (staging/'frame_states.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for offset in range(len(result['xy'])):
                for animal in range(6):
                    row = dict(global_frame=meta['settings']['start']+offset,
                               animal_id=animal,
                               state=FRAME_STATE_NAMES[timeline['states'][offset, animal]])
                    row.update({key: int(timeline[key][offset, animal]) for key in fields[3:]})
                    writer.writerow(row)
        pdf_name = pdf_name or f'{Path(video).stem}_{cell}.pdf'
        if Path(pdf_name).name != pdf_name or not pdf_name.endswith('.pdf'): raise ValueError('PDF name must be a plain .pdf filename')
        meta['pdf_filename'] = pdf_name
        with (staging/'presumed_positions.csv').open('w',newline='') as stream:
            fields=['global_frame','animal_id','raw_x','raw_y','estimated_x','estimated_y','inferred','visible_anchor_id','ambiguous']
            writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
            for t in range(len(result['xy'])):
                for a in range(6):
                    raw=result['xy'][t,a];est=result['group']['xy'][t,a]
                    values=[meta['settings']['start']+t,a,*raw,*est,int(result['group']['inferred'][t,a]),
                            int(result['group']['anchors'][t,a]),int(result['group']['ambiguous'][t,a])]
                    writer.writerow(dict(zip(fields,[v if not isinstance(v,(float,np.floating)) or np.isfinite(v) else '' for v in values])))
        write_pdf(result,staging/pdf_name,video,cell)
        meta['output_sha256']={p.name:sha256(p) for p in staging.iterdir()}
        (staging/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
        if output.exists(): raise FileExistsError(output)
        os.rename(staging,output)
    finally:
        if staging.exists(): shutil.rmtree(staging)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['trajectory','session','output','video','cell-label']: parser.add_argument('--'+name,required=True)
    parser.add_argument('--start',type=int,required=True)
    parser.add_argument('--pdf-name',help='TOML stem plus .pdf')
    parser.add_argument('--fps',type=float,help='Verified recording frame rate for seconds')
    parser.add_argument('--window',type=int,default=7200)
    for name,value in [('threshold',30.),('wall-buffer-px',30.),('fungus-buffer-px',30.),('social-distance-threshold-px',60.),('jump-threshold-px',200.)]:
        parser.add_argument('--'+name,type=float,default=value)
    args=vars(parser.parse_args())
    fps=args.pop('fps'); pdf_name=args.pop('pdf_name')
    if fps is not None and (not np.isfinite(fps) or fps<=0): parser.error('fps must be finite and positive')
    output=args.pop('output'); video=args.pop('video'); cell=args.pop('cell_label')
    if not video.strip() or not cell.strip(): parser.error('Video and cell labels must be nonblank')
    # Hash before and after calculation to detect changing input files.
    source=Path(args['trajectory']); session=Path(args['session'])
    session_json=session/'session.json'
    if not session_json.is_file():
        matches=list(session.rglob('session.json'))
        if len(matches)!=1: parser.error('Expected exactly one session.json')
        session_json=matches[0]
    before={str(p.resolve()):sha256(p) for p in [source,session_json]}
    result=analyze_six(**args)
    if any(sha256(p)!=value for p,value in before.items()): raise RuntimeError('Input changed during analysis')
    result['metadata']['frames_per_second']=fps
    result['metadata']['input_sha256']=before
    result['metadata']['code_sha256']={p.name:sha256(p) for p in [Path(__file__),Path(legacy.__file__)]}
    write_bundle(result,output,video,cell,pdf_name)
    print(f'Wrote UNREVIEWED six-beetle output: {output}')


if __name__=='__main__': main()
