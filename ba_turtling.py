"""BA candidate bout accounting. Posture requires separate human review."""
import math
VERSION = '0.2.1'

def summarize(mask, detected, start, fps):
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError('fps must be positive and finite')
    if len(mask) != len(detected) or not len(mask):
        raise ValueError('aligned nonempty masks required')
    if any(bool(m) and not bool(d) for m, d in zip(mask, detected)):
        raise ValueError('missing observations cannot be candidates')
    bouts=[]; first=None
    for i, flag in enumerate(list(mask)+[False]):
        if flag and first is None: first=i
        elif not flag and first is not None:
            bouts.append(dict(start_global_frame=start+first,end_global_frame_inclusive=start+i-1,
                              frames=i-first,seconds=(i-first)/fps,
                              left_censored=first==0 or not bool(detected[first-1]),
                              right_censored=i==len(mask) or not bool(detected[i])))
            first=None
    n=sum(bool(x) for x in mask); valid=sum(bool(x) for x in detected)
    return dict(schema='ba-turtling-bouts-v1',version=VERSION,status='AUTOMATIC_CANDIDATE_UNREVIEWED',
                definition='Movement-pattern candidate; confirmed overturned time includes quiet pauses and requires video review.',
                start_global_frame=start,end_global_frame_inclusive=start+len(mask)-1,fps=fps,
                candidate_frames=n,candidate_seconds=n/fps,detected_frames=valid,
                detected_seconds=valid/fps,unknown_seconds=(len(mask)-valid)/fps,
                candidate_fraction_detected=n/valid if valid else None,
                bout_count=len(bouts),longest_bout_seconds=max((b['seconds'] for b in bouts),default=0),
                confirmed_overturned_seconds=None,bouts=bouts)

def pdf_pages(pdf, result):
    """Append paginated bout tables to the existing PDF using its PdfPages handle."""
    import matplotlib.pyplot as plt
    bouts=result['bouts']; pages=max(1,math.ceil(len(bouts)/24))
    for page in range(pages):
        fig=plt.figure(figsize=(8.5,11))
        fraction=result['candidate_fraction_detected']
        lines=['BA turtling candidates | module '+VERSION,
               'AUTOMATIC / UNREVIEWED — not confirmed overturned posture',
               f"Candidate time: {result['candidate_seconds']:.3f} s",
               'Percent of detected time: '+('NA' if fraction is None else f'{100*fraction:.2f}%'),
               f"Bouts: {result['bout_count']} | longest: {result['longest_bout_seconds']:.3f} s",
               f"Tracking unknown: {result['unknown_seconds']:.3f} s",
               'Confirmed overturned time: not assessed',
               'Quiet overturned pauses require video review.',
               'Durations count inclusive observed frames / source FPS.',
               'Missing observations split candidates; no gap filling.', '',
               'Start frame    End frame      Seconds    Boundary uncertain']
        for b in bouts[page*24:(page+1)*24]:
            lines.append(f"{b['start_global_frame']:11d} {b['end_global_frame_inclusive']:12d} {b['seconds']:12.3f}    {'yes' if b['left_censored'] or b['right_censored'] else 'no'}")
        if not bouts:lines.append('No automatic candidate bouts.')
        fig.text(.08,.94,'\n'.join(lines),va='top',fontsize=10,family='monospace',linespacing=1.6)
        fig.text(.08,.05,f'BA candidate bout report | page {page+1}/{pages}',fontsize=9)
        pdf.savefig(fig);plt.close(fig)

    if result.get('experimental') is not None:
        from ba_turtling_candidates import pdf_pages as experimental_pdf_pages
        experimental_pdf_pages(pdf, result['experimental'])

def summarize_review(notes, start, end, fps):
    """Separate attributed posture coverage; conflicting claims are rejected."""
    if end < start or fps <= 0 or not math.isfinite(fps):
        raise ValueError('invalid review window')
    posture={}; flailing={}
    for note in notes:
        decision=note.get('decision','note')
        if decision=='note': continue
        if decision not in {'confirmed_overturned','rejected_overturned','active_flailing','inactive_flailing','uncertain'}:
            raise ValueError('unknown decision')
        if not note.get('reviewer','').strip() or not note.get('reason','').strip():
            raise ValueError('reviewer and reason required')
        lo=note['first_global_frame']; hi=note['last_global_frame']
        if type(lo) is not int or type(hi) is not int or not start<=lo<=hi<=end:
            raise ValueError('invalid inclusive review range')
        for frame in range(lo,hi+1):
            if decision in {'active_flailing','inactive_flailing'}:
                if frame in flailing and flailing[frame]!=decision:raise ValueError('conflicting flailing decisions')
                flailing[frame]=decision
                continue
            if frame in posture and posture[frame]!=decision:raise ValueError('conflicting posture decisions')
            posture[frame]=decision
    positive=sum(v=='confirmed_overturned' for v in posture.values())
    negative=sum(v=='rejected_overturned' for v in posture.values())
    return dict(status='PARTIAL_HUMAN_REVIEW' if positive+negative<end-start+1 else 'FULL_WINDOW_POSTURE_REVIEW',
                confirmed_overturned_seconds=positive/fps,confirmed_upright_seconds=negative/fps,
                posture_unresolved_seconds=(end-start+1-positive-negative)/fps,
                observed_active_flailing_seconds=sum(v=='active_flailing' for v in flailing.values())/fps,
                observed_inactive_flailing_seconds=sum(v=='inactive_flailing' for v in flailing.values())/fps,
                definition='Confirmed overturned intervals include quiet pauses; no inference outside reviewed intervals.')


def apply_posture_review(mask, detected, start, fps, notes):
    """Reviewed posture overrides a separate episode mask, never raw movement flags.

    This is not automatic gap closing. Only explicitly reviewed frame ranges change.
    Human posture may be visible even if tracking is missing; that stays explicit.
    """
    baseline=summarize(mask, detected, start, fps)
    review=summarize_review(notes, start, start+len(mask)-1, fps)
    episode=[bool(v) for v in mask]
    evidence=['automatic_candidate' if m else 'unassessed' for m in mask]
    for note in notes:
        decision=note.get('decision','note')
        if decision not in {'confirmed_overturned','rejected_overturned','uncertain'}:continue
        for frame in range(note['first_global_frame'],note['last_global_frame']+1):
            i=frame-start
            episode[i]=decision=='confirmed_overturned'
            evidence[i]={'confirmed_overturned':'human_confirmed_overturned',
                         'rejected_overturned':'human_confirmed_upright',
                         'uncertain':'human_uncertain'}[decision]
    # Visible human posture can establish time in otherwise missing tracking frames.
    available=[bool(d) or e.startswith('human_confirmed') for d,e in zip(detected,evidence)]
    counted=summarize(episode, available, start, fps)
    status=('FULL_WINDOW_POSTURE_REVIEW' if review['posture_unresolved_seconds']==0
            else 'REVIEW_ASSISTED_NOT_FULLY_CONFIRMED')
    return dict(schema='ba-reviewed-episodes-v1',version=VERSION,status=status,
                baseline=baseline,review=review,episode_mask=episode,evidence=evidence,
                episode_seconds=counted['candidate_seconds'],bouts=counted['bouts'],
                definition='Automatic candidates with explicit human posture corrections. No automatic gap bridging.',
                notes=notes)

def reviewed_pdf_pages(pdf, result):
    import matplotlib.pyplot as plt
    bouts=result['bouts']
    for page in range(max(1,math.ceil(len(bouts)/22))):
        fig=plt.figure(figsize=(8.5,11))
        lines=['BA reviewed turtling episodes | module '+VERSION,
               ('HUMAN POSTURE REVIEW - entire displayed window reviewed'
                if result['status']=='FULL_WINDOW_POSTURE_REVIEW' else
                'REVIEW-ASSISTED - includes unconfirmed automatic candidates'),
               f"Original movement-pattern candidate time: {result['baseline']['candidate_seconds']:.3f} s",
               f"Episode time after posture review: {result['episode_seconds']:.3f} s",
               f"Explicitly confirmed overturned: {result['review']['confirmed_overturned_seconds']:.3f} s",
               f"Explicitly observed flailing pause: {result['review']['observed_inactive_flailing_seconds']:.3f} s",
               'Overturned time includes quiet pauses; movement flags are unchanged.',
               'Only attributed, reviewed intervals change the episode mask.',
               'This does not validate automatic gap filling or quiet-posture detection.', '',
               'Start frame    End frame      Seconds   Clip boundary']
        for b in bouts[page*22:(page+1)*22]:
            boundary='both' if b['left_censored'] and b['right_censored'] else 'start' if b['left_censored'] else 'end' if b['right_censored'] else 'neither'
            lines.append(f"{b['start_global_frame']:11d} {b['end_global_frame_inclusive']:12d} {b['seconds']:12.3f}   {boundary}")
        lines += ['', 'Time is limited to the displayed window.',
                  'An event touching a clip boundary may extend beyond the clip.']
        fig.text(.08,.94,'\n'.join(lines),va='top',fontsize=10,family='monospace',linespacing=1.6)
        fig.text(.08,.05,'Human decisions and original evidence are retained separately.',fontsize=9)
        pdf.savefig(fig);plt.close(fig)
