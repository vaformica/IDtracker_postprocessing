"""IDtracker-first, detection-supported inference for missing identities only.

Finite original-image coordinates are authoritative assignments, even when two
IDs share a segmentation blob. Blob continuity and social history may locate a
missing ID, but never replace, delay, or relabel an available IDtracker position.
"""
import itertools
import numpy as np

MODEL_VERSION = '1.6.0'


def persistent_groups(raw, blobs, social_radius=60., max_step=100., confirmation=3,
                      gap_speed=20., gap_radius_cap=300., max_reacquire_gap=30,
                      distant_confirmation=10):
    """Keep raw IDs; infer only missing members of spatially supported groups.

    confirmation/distant_confirmation remain accepted for historical callers,
    but do not delay raw returns. No retrospective rewriting of raw IDs occurs.
    """
    raw = np.asarray(raw, float)
    if raw.ndim != 3 or raw.shape[2] != 2:
        raise ValueError('Expected frame, animal, x/y coordinates')
    nframes, nanimals, _ = raw.shape
    if (not np.isfinite([social_radius, max_step, gap_speed, gap_radius_cap]).all()
            or social_radius <= 0 or max_step <= 0 or confirmation < 1
            or gap_speed <= 0 or gap_radius_cap < social_radius
            or max_reacquire_gap < 1 or distant_confirmation < confirmation):
        raise ValueError('Invalid model parameters')
    known = np.isfinite(raw).all(axis=2)
    xy = np.full_like(raw, np.nan)
    group_ids = np.full((nframes, nanimals), -1, int)
    inferred = np.zeros((nframes, nanimals), bool)
    ambiguous = np.zeros_like(inferred)
    identity_conflict = np.zeros_like(inferred)
    anchors = np.full((nframes, nanimals), -1, int)
    source = np.full((nframes, nanimals), 'MISSING', dtype='<U24')
    member_last = np.full((nanimals, 2), np.nan)
    member_frame = np.full(nanimals, -1, int)
    entities = []
    initialized = set()
    next_id = 0
    events = []

    def match(point, detections):
        choices = sorted((float(np.linalg.norm(np.asarray(b['centroid'])-point)), j)
                         for j, b in enumerate(detections))
        choices = [(d, j) for d, j in choices if d <= social_radius]
        if not choices or (len(choices) > 1 and choices[1][0]-choices[0][0] < 5):
            return None
        return choices[0][1]

    def reachable(t, a, point):
        elapsed = t-member_frame[a]
        return (member_frame[a] >= 0 and elapsed > 0 and
                np.linalg.norm(point-member_last[a]) <= min(gap_radius_cap, max_step*elapsed))

    def near_before_loss(t, left, right):
        # Never merge two available IDs into a presumed-contact group.
        # New missing-ID contact needs support in the immediately prior frame.
        if not t:
            return False
        return any(not (known[t, a] and known[t, b]) and
                   np.isfinite(xy[t-1, [a, b]]).all() and
                   np.linalg.norm(xy[t-1, a]-xy[t-1, b]) <= social_radius
                   for a in left['members'] for b in right['members'])

    for t in range(nframes):
        bs = blobs.get(str(t), blobs.get(t, []))
        prior_members = {e['id']: set(e['members']) for e in entities}
        # Detach returning raw IDs *before* calculating inference proposals.
        # Thus an obsolete pile cannot keep an observed animal or drag it back.
        separated = []
        for e in entities:
            present = {a for a in e['members'] if known[t, a]}
            if len(e['members']) > 1 and present:
                e['members'] -= present
                if e['members']:
                    separated.append(e)
                for a in sorted(present):
                    separated.append(dict(id=next_id, members={a}, last=raw[t, a].copy(), last_frame=t))
                    next_id += 1
            else:
                separated.append(e)
        entities = separated
        for a in np.flatnonzero(known[t]):
            if a not in initialized:
                entities.append(dict(id=next_id, members={int(a)}, last=raw[t, a].copy(), last_frame=t))
                next_id += 1
                initialized.add(int(a))
            if t and not known[t-1, a]:
                events.append(dict(frame=t, kind='RAW_ID_RETURNED', members=[int(a)]))

        proposals = []
        raw_matches = {int(a): match(raw[t, a], bs) for a in np.flatnonzero(known[t])}
        for e in entities:
            present = [a for a in e['members'] if known[t, a]]
            if present:
                a = present[0]  # all observed entities are now singletons
                e['last'] = raw[t, a].copy()
                e['last_frame'] = t
                proposals.append((e, raw_matches[a]))
                continue
            gap = t-e['last_frame']
            radius = (max_step if gap <= 1 else
                      min(gap_radius_cap, max_step*gap, social_radius+gap_speed*(gap-1)))
            candidates = [] if gap > max_reacquire_gap else [
                j for j, b in enumerate(bs)
                if np.linalg.norm(np.asarray(b['centroid'])-e['last']) <= radius
                and all(reachable(t, a, np.asarray(b['centroid'])) for a in e['members'])]
            # A missing identity must not steal an unrelated observed animal's
            # blob merely because it is reachable within the movement radius.
            candidates = [j for j in candidates if all(
                near_before_loss(t, e, dict(members={a}))
                for a, raw_j in raw_matches.items() if raw_j == j)]
            ranked = sorted((float(np.linalg.norm(np.asarray(bs[j]['centroid'])-e['last'])), j)
                            for j in candidates)
            choice = (ranked[0][1] if ranked and
                      (len(ranked) == 1 or ranked[1][0]-ranked[0][0] > social_radius/2) else None)
            proposals.append((e, choice))

        by_blob = {}
        unseen = []
        for e, j in proposals:
            if j is None:
                unseen.append(e)
            else:
                by_blob.setdefault(j, []).append(e)
        active = list(unseen)
        for j, es in by_blob.items():
            # Multiple raw IDs may share a blob: preserve them independently.
            # Missing entities may join only one proximity-connected component.
            components = []
            for e in es:
                joins = [c for c in components if any(near_before_loss(t, e, other) for other in c)]
                if joins:
                    combined = [e]
                    for c in joins:
                        combined.extend(c)
                        components.remove(c)
                    components.append(combined)
                else:
                    components.append([e])
            missing_components = [c for c in components if any(not known[t, a] for e in c for a in e['members'])]
            # Independent components cannot all claim one detection. Keep raw
            # assignments, but withhold ambiguous missing-ID attribution.
            blocked = len(components) > 1 and bool(missing_components)
            for component in components:
                members = set().union(*(e['members'] for e in component))
                if blocked:
                    for e in component:
                        active.append(e)
                        for a in e['members']:
                            if not known[t, a]:
                                ambiguous[t, a] = True
                    continue
                if len(component) > 1:
                    reuse = next((e for e in component if prior_members.get(e['id']) == members), None)
                    if reuse is None:
                        e = dict(id=next_id, members=members)
                        next_id += 1
                        events.append(dict(frame=t, kind='MERGE', members=sorted(members)))
                    else:
                        e = reuse
                        e['members'] = members
                else:
                    e = component[0]
                point = np.asarray(bs[j]['centroid'], float)
                e['last'] = point.copy()
                e['last_frame'] = t
                active.append(e)
                present = [a for a in sorted(members) if known[t, a]]
                for a in members:
                    if known[t, a]:
                        continue
                    xy[t, a] = point
                    inferred[t, a] = True
                    source[t, a] = 'PSCP_BLOB' if len(members) > 1 else 'BLOB_CONTINUITY'
                    anchors[t, a] = present[0] if present else min(members)
        entities = active
        for e in entities:
            for a in e['members']:
                group_ids[t, a] = e['id']
                if not known[t, a] and not np.isfinite(xy[t, a]).all():
                    ambiguous[t, a] |= bool(bs)
        # Authoritative raw assignments are never subject to blob or movement
        # gates. Large raw jumps remain available for separate QC/step filtering.
        xy[t, known[t]] = raw[t, known[t]]
        source[t, known[t]] = 'ASSIGNED'
        anchors[t, known[t]] = np.flatnonzero(known[t])
        located = np.isfinite(xy[t]).all(axis=1)
        member_last[located] = xy[t, located]
        member_frame[located] = t

    shared = {(a, b): (group_ids[:, a] >= 0) & (group_ids[:, a] == group_ids[:, b])
              for a, b in itertools.combinations(range(nanimals), 2)}
    masks = {(a, b): joined & np.isfinite(xy[:, a]).all(axis=1)
             & np.isfinite(xy[:, b]).all(axis=1) & (inferred[:, a] | inferred[:, b])
             for (a, b), joined in shared.items()}
    unresolved = {(a, b): joined & (~np.isfinite(xy[:, a]).all(axis=1)
                  | ~np.isfinite(xy[:, b]).all(axis=1)) for (a, b), joined in shared.items()}
    return dict(xy=xy, group_ids=group_ids, inferred=inferred, ambiguous=ambiguous,
                anchors=anchors, identity_conflict=identity_conflict, masks=masks,
                unresolved_masks=unresolved, source=source, events=events)
