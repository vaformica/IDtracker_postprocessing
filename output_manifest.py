#!/usr/bin/env python3
"""Write a student-facing, schema-checked manifest for a group analysis run.

Every CSV header in the actual output must have a plain-English definition.
Adding an output column therefore requires updating this dictionary before a
new complete pipeline run can be reported as documented.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

VERSION = '1.2.0'

CSV_FILES = {
    'animals.csv': 'One row per beetle: where its raw track began and when it first met the movement (wake) threshold.',
    'windows.csv': 'Per-beetle summaries calculated from original IDtracker coordinates, by analysis window.',
    'regions.csv': 'Original-coordinate time and accepted movement distance in the arena, walls, fungus ROIs, and other regions.',
    'pairs.csv': 'One row per beetle pair and window, comparing observed proximity with inferred group contact.',
    'events.csv': 'Current observed-proximity, presumed-group-contact, and unresolved-contact episodes.',
    'legacy_events.csv': 'Historical proximity and disappearance-candidate episodes retained for comparison; do not substitute these for current group-contact events.',
    'frame_states.csv': 'One row per beetle per frame with a compact observed, presumed-social, or missing display state.',
    'canonical_positions.csv': 'One row per beetle per frame with the position used by the current group model.',
    'presumed_positions.csv': 'Original and estimated positions side by side, with the inference and ambiguity flags.',
    'reconstructed_positions.csv': 'Diagnostic speed-screened, held, and straight-line bridge paths. Held and bridge paths are not used as observed positions in the main estimates.',
    'frame_data.csv': 'The main reusable per-frame table: raw and working positions, contact partners, fungus flags, and accepted movement steps.',
    'fungus_summary.csv': 'Original-coordinate frame counts and movement distance for each fungus ROI.',
    'estimated_windows.csv': 'Per-beetle window summaries using current detection-supported group positions, including presumed social positions.',
    'estimated_regions.csv': 'Region counts and accepted movement distance using current detection-supported group positions.',
    'estimated_fungus_summary.csv': 'Fungus frame counts and movement distance using current detection-supported group positions.',
    'window_comparison.csv': 'Raw and PSC-model per-beetle window statistics in the same row; prefixes identify the coordinate source.',
    'region_comparison.csv': 'Raw and PSC-model region statistics in the same row, including distance and frame counts.',
    'fungus_comparison.csv': 'Raw and PSC-model fungus occupancy and movement statistics in the same beetle row.',
}

COLUMNS = {
    'accepted_steps': 'Number of adjacent-frame movements included in distance after the jump rule.',
    'ambiguous': '1 when the group location or identity assignment remains ambiguous; otherwise 0.',
    'ambiguous_disappearance': '1 when a disappearance could involve more than one partner or the group position is uncertain.',
    'animal_a': 'First beetle ID in a pair. IDs are zero-based.',
    'animal_b': 'Second beetle ID in a pair. IDs are zero-based.',
    'animal_id': 'Beetle identity assigned by IDtracker, numbered from 0.',
    'any_fungus': '1 when the working position lies in at least one fungus ROI; otherwise 0.',
    'attribution': 'Evidence category or rule that produced this event; read with kind.',
    'available_steps': 'Number of adjacent frame pairs in the window, whether positions are known or not.',
    'baseline_x': 'Original x coordinate at the exact first analysis frame, in source-video pixels.',
    'baseline_y': 'Original y coordinate at the exact first analysis frame, in source-video pixels.',
    'bridge_x': 'X coordinate on a straight-line diagnostic bridge across a gap; not observed motion.',
    'bridge_y': 'Y coordinate on a straight-line diagnostic bridge across a gap; not observed motion.',
    'candidate_partner_count': 'Number of nearby candidate partners when the disappearance began; blank when not applicable.',
    'candidate_rejected': '1 if a raw position failed the speed or reacquisition screen; otherwise 0.',
    'coordinate_frames': 'Frames in this region with a usable position under this table’s coordinate source.',
    'coordinate_present': '1 if this beetle has a working position on this frame; otherwise 0.',
    'disappearance_candidate': 'Under PSC 1.6.0, 1 only for this missing ID with PSCP_BLOB inference; the assigned partner remains 0. Earlier models used pair-episode membership.',
    'distance_px': 'Sum of accepted adjacent-frame step lengths, in source-video pixels.',
    'distance_px_per_available_step': 'Accepted distance divided by all possible adjacent-frame steps in the window.',
    'distance_px_per_valid_step': 'Accepted distance divided by the number of accepted steps.',
    'end_global_frame_inclusive': 'Last original-video frame counted in this row; this end is inclusive.',
    'estimated_x': 'Current model’s x position, possibly shared with a detected group blob; blank when location is unresolved.',
    'estimated_y': 'Current model’s y position, possibly shared with a detected group blob; blank when location is unresolved.',
    'frame_observations': 'Number of frames included for this beetle and window.',
    'frames': 'Duration of an event in frames, including both its start and end frames.',
    'global_frame': 'Frame number in the original source video, beginning at 0; not the clip-relative frame.',
    'group_id': 'Internal persistent-group identifier for this frame; useful for linking members, not a beetle ID.',
    'group_representative_id': 'Beetle ID used as the detected position anchor for the presumed group; this is not proof of that beetle’s identity.',
    'held_x': 'Last accepted x position carried forward as a diagnostic hold; not counted as observed movement.',
    'held_y': 'Last accepted y position carried forward as a diagnostic hold; not counted as observed movement.',
    'human_intervention': '1 if a human review edit was applied to this frame; 0 means no human edit in this export.',
    'identity_conflict': '1 when the raw IDtracker identity points to a different detected blob than its current PSC entity, including disagreements later resolved by retrospective reidentification; review the raw video.',
    'in_arena': '1 when the working position is inside the arena ROI; otherwise 0.',
    'inferred': '1 when the working position is inferred from a detected social group rather than independently assigned.',
    'jointly_visible_frames': 'Frames when both members of this pair have independent accepted assignments.',
    'kind': 'Event type, such as PROXIMITY, PRESUMED_GROUP_CONTACT, or PILE_LOCATION_UNRESOLVED.',
    'latency_to_threshold_frames': 'Frames from the exact analysis start to the first reliable movement-threshold crossing; blank if unavailable.',
    'legacy_disappearance_candidate_events': 'Count from the older pairwise disappearance rule, retained only as a comparison.',
    'location_known': '1 when x and y are available in the current working path; otherwise 0.',
    'location_source': 'ASSIGNED = exact available IDtracker position under PSC 1.6.0 (independently accepted position in earlier models); PSCP_BLOB = missing-ID presumed position at a detected group blob; BLOB_CONTINUITY = inferred singleton position; RETRO_REID_BLOB = a retrospectively linked unlabeled blob after sustained raw reidentification, still inferred and ambiguous; DEPARTURE_UNCERTAIN = unknown position during the short interval before the retrospectively identified blob path begins, so no pile movement or fungus credit; RAW_PSC_CONFLICT = sustained raw ID belongs to a blob already owned by another entity, so canonical location is unknown pending review; SPLIT_PENDING = unresolved candidate separation; UNRESOLVED_SPLIT = hidden member has no defensible branch after a multiway split; MISSING = no defensible position.',
    'missing_animal': 'Beetle ID that disappeared in a legacy candidate event; blank when not applicable.',
    'missing_coordinate_frames': 'Frames with no usable position under this table’s coordinate source.',
    'missing_coordinate_proportion': 'Missing-coordinate frames divided by all frame observations in the window (0 to 1).',
    'missing_endpoint_steps': 'Adjacent frame pairs for which at least one endpoint lacks a usable position.',
    'observed_proximity_partners': 'Semicolon-separated beetle IDs independently seen nearby on this frame; blank means none.',
    'presumed_group_frames': 'Frames this pair is assigned to the same detection-supported presumed group.',
    'presumed_social_disappearance_events': 'Number of continuous presumed-group-contact episodes for this pair.',
    'proximity_bouts': 'Number of separate continuous observed-proximity episodes.',
    'proximity_frames': 'Frames this pair is independently assigned and within the proximity radius.',
    'proximity_partner_count': 'Number of independently observed nearby partners on this frame.',
    'proximity_proportion_jointly_visible': 'Observed-proximity frames divided by jointly visible frames; blank if never jointly visible.',
    'pscp_partners': 'Semicolon-separated beetle IDs sharing presumed social contact on this frame; blank means none.',
    'raw_x': 'Original IDtracker x coordinate in source-video pixels; blank if IDtracker has no coordinate.',
    'raw_y': 'Original IDtracker y coordinate in source-video pixels; blank if IDtracker has no coordinate.',
    'raw_location_known': '1 when original IDtracker x/y are both finite; 0 when the raw identity has no position.',
    'raw_in_arena': '1 when the original IDtracker coordinate lies inside the arena ROI.',
    'raw_any_fungus': '1 when the original IDtracker coordinate lies in any fungus ROI.',
    'raw_proximity_partners': 'Semicolon-separated IDs within the social radius using original IDtracker coordinates, before PSC screening.',
    'raw_step_from_previous_accepted': '1 when the adjacent original-coordinate step passes the raw jump cutoff.',
    'raw_step_distance_px': 'Original-coordinate adjacent-step distance in pixels when accepted; blank otherwise.',
    'raw_proximity_frames': 'Frames when both original IDtracker coordinates are present and within the social radius.',
    'raw_proximity_bouts': 'Continuous raw-coordinate proximity episodes.',
    'raw_jointly_present_frames': 'Frames when both original IDtracker coordinates are finite.',
    'raw_proximity_proportion_jointly_present': 'Raw-proximity frames divided by frames with both raw coordinates; blank if no joint presence.',
    'region': 'Named area being summarized; fungus indices follow the input TOML ROI order.',
    'rejected_jump_steps': 'Adjacent coordinate steps excluded because they exceed the report’s jump cutoff.',
    'screened_x': 'Raw x coordinate accepted by the speed/reacquisition diagnostic; blank when rejected or missing.',
    'screened_y': 'Raw y coordinate accepted by the speed/reacquisition diagnostic; blank when rejected or missing.',
    'social_any_partner_frames': 'Frames this beetle is independently observed within the proximity radius of at least one partner.',
    'social_distance_px': 'Accepted movement distance during steps whose endpoints are both in observed proximity.',
    'social_multiple_partner_frames': 'Frames this beetle is independently observed near two or more partners.',
    'start_global_frame': 'First original-video frame included in this row or event.',
    'step_distance_px': 'Accepted movement distance from the previous frame to this frame; blank if the step is not accepted.',
    'step_from_previous_accepted': '1 when both positions are known and their adjacent-frame movement passes the speed rule.',
    'threshold_crossing_global_frame': 'Original-video frame of the first reliable movement-threshold crossing; blank if unavailable.',
    'turtling_candidate_events': 'Number of continuous path-shape episodes meeting the provisional turtling screen; not confirmed behavior.',
    'turtling_candidate_frames': 'Frames meeting the provisional path-shape screen; not confirmed behavior.',
    'unresolved_contact_partners': 'Semicolon-separated beetle IDs still presumed grouped while no defensible shared location is available.',
    'unresolved_group_frames': 'Frames this pair remains grouped but no detected position supports a shared location.',
    'valid_coordinate_frames': 'Frames with a usable position under this table’s coordinate source.',
    'visible_return_events': 'Count of pairwise disappearances followed by a visible return under the older screening rule.',
    'wake_status': 'Whether the exact-start movement threshold was calculated; NOT_CALCULATED and THRESHOLD_NOT_REACHED explain missing latencies.',
    'warning': 'Plain-English reason a wake or related calculation was unavailable or questionable.',
    'window': 'Analysis period: full, post_wake, or post_wake_3600.',
    'x': 'Current working x coordinate in source-video pixels; may be inferred in a detected social group.',
    'y': 'Current working y coordinate in source-video pixels; may be inferred in a detected social group.',
    'status': 'Whether this window or region was calculated, or why it could not be calculated.',
    'state': 'Status code for this row; see the file-specific state note below.',
}

OVERRIDES = {
    'frame_states.csv': {
        'state': 'OBSERVED_ID_ASSIGNED = independent accepted position; PRESUMED_SOCIAL_DISAPPEARANCE = group-supported inferred position; MISSING = no defensible position.'},
    'canonical_positions.csv': {
        'state': 'ASSIGNED, PSCP_BLOB, or MISSING: how the current position was obtained.'},
    'reconstructed_positions.csv': {
        'state': 'SCREENED_ASSIGNED, HELD_LAST_POSITION, or UNLOCATED in the diagnostic reconstruction; this is not the primary scored path.'},
}

JSON_KEYS = {
    'analysis/manifest.json': {
        'script_version':'Version of the group processor that produced the analysis.',
        'base_processor_version':'Version of the earlier post-processor on which this model builds.',
        'trajectory_file':'Original IDtracker trajectory used as input.',
        'session_folder':'IDtracker session directory containing the trajectory and ROI settings.',
        'trajectory_source_kind':'Which trajectory representation was read.',
        'settings':'Frame interval and analysis thresholds; distance thresholds use source-video pixels.',
        'animal_count':'Number of tracked beetle identities.',
        'roi_order':'Order of the arena and fungus ROIs.',
        'fungus_numbering_convention':'How fungus 1, 2, and 3 were numbered.',
        'frame_state_definition':'Meaning and priority of observed, presumed-social, and missing states.',
        'rois':'Polygon coordinates for the arena and fungi in original-video pixels.',
        'fixed_anchor_rule':'Rule for choosing a comparable post-wake period.',
        'qc_status':'Review state. UNREVIEWED means no human confirmation of identity or behavior.',
        'coordinate_substitution':'Whether the estimated tables include detection-supported group positions.',
        'raw_coordinates_preserved':'Whether original IDtracker coordinates were kept alongside estimates.',
        'raw_identity_policy':'IDTRACKER_AUTHORITATIVE means every finite input identity keeps its exact coordinates and is never relabeled inferred.',
        'presumed_group_rule':'Plain-language summary of persistent contact and missing-location rules.',
        'persistent_group_settings':'Numeric settings controlling persistent groups and reacquisition.',
        'persistent_model_version':'Version of the persistent contact algorithm.',
        'blob_evidence_sha256':'Hash of the exported detection evidence used by the model.',
        'blob_evidence_file':'Path to the detection-evidence export on the original machine.',
        'interpretation':'Caution about what tracking and proximity do or do not establish.',
        'turtling_settings':'Thresholds for a provisional path-shape screen.',
        'reconstruction':'Diagnostic speed-screening and gap-handling rules.',
        'frames_per_second':'Source video frame rate; reported durations remain in frames.',
        'input_sha256':'Hashes of the trajectory and session inputs.',
        'code_sha256':'Hashes of the processor code used for the analysis.',
        'output_sha256':'Hashes of analysis files present when the analysis bundle was created.',
        'pdf_filename':'Name of this run’s PDF report.',
        'pdf_track_style_version':'Version of the PDF track-drawing convention, including outlined presumed-social paths.',
        'video':'Source video name recorded with this analysis.',
        'cell_label':'Label attached to this trial run.',
    },
    'review/source_manifest.json': {
        'schema':'Format version for the interactive review bundle.',
        'status':'Review state, usually UNREVIEWED until a person checks it.',
        'decision_count':'Number of saved human review decisions.',
        'review_code_sha256':'Hashes of the code and template used to build the review.',
        'animal_count':'Number of beetle identities shown.',
        'fungus_count':'Number of fungus ROIs shown.',
        'label':'Trial label displayed in the review.',
        'cell_id':'Cell or box identifier extracted from the source TOML filename; null if unavailable.',
        'source_toml':'Original tracking TOML path used for the review identity and filenames.',
        'analysis_bundle':'Original path to the analysis files; may be on Firebird.',
        'analysis_manifest_sha256':'Hash of the analysis provenance manifest.',
        'canonical_sha256':'Hash of the canonical position/state data behind the overlay.',
        'video_source':'Original or copied path to the review video.',
        'video_sha256':'Hash of the video used to build the review.',
        'copied_video_sha256':'Hash of the video beside the HTML file.',
        'analysis_frame_count':'Number of original-video frames represented in this synchronized review.',
        'processor_version':'Group-processor version of the analysis displayed in the review.',
        'psc_model_version':'Presumed social-contact model version displayed in the review.',
        'review_view_version':'Version of the RAW/PSC comparison controls and display.',
        'video_generation_filter':'FFmpeg trim, rotation, crop, scale, and padding applied to the review video.',
        'video_geometry':'Crop and orientation metadata; aspect_preserved confirms no stretching.',
        'crop':'Source-video crop [x, y, width, height] used for the review video.',
        'fps':'Frame rate used to synchronize the HTML slider and video.',
        'html':'Filename of the interactive review page.',
        'video':'Filename of the review MP4 beside the HTML page.',
    },
}

NPZ_ARRAYS = {
    'raw':'Original IDtracker positions, shape [frames, beetles, x/y].',
    'xy':'Current detection-supported working positions, shape [frames, beetles, x/y].',
    'inferred':'Boolean flag for group-supported presumed positions.',
    'group_ids':'Persistent group identifier for each beetle and frame.',
    'source':'ASSIGNED, PSCP_BLOB, or MISSING source code for each position.',
    'ambiguous':'Boolean ambiguity flag for each beetle and frame.',
}

TOML_KEYS = {
    'name':'Name supplied when the tracking configuration was created; check against the source filename if labels differ.',
    'video_paths':'Source video file(s) on Firebird.',
    'intensity_ths':'Pixel-intensity thresholds used to select candidate blobs; meaning depends on background subtraction.',
    'area_ths':'Minimum and maximum candidate-blob area in square pixels.',
    'tracking_intervals':'Original-video frame intervals submitted to IDtracker; the end is exclusive.',
    'number_of_animals':'Number of beetles IDtracker was asked to track.',
    'use_bkg':'Whether background subtraction was enabled.',
    'check_segmentation':'Whether IDtracker was asked to open/check segmentation before tracking.',
    'track_wo_identities':'Whether IDtracker was asked to track blobs without resolving identities.',
    'roi_list':'Arena polygon followed by fungus polygons, in the entered order.',
    'background_subtraction_stat':'Statistic (such as median) used to estimate the background image.',
    'number_of_frames_for_background':'Number of frames sampled to estimate the background.',
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def column_description(name: str, filename: str) -> str | None:
    if name in OVERRIDES.get(filename, {}):
        return OVERRIDES[filename][name]
    if name in COLUMNS:
        return COLUMNS[name]
    if (match := re.fullmatch(r'raw_fungus_(\d+)', name)):
        return f'1 when the original IDtracker coordinate lies inside fungus ROI {match.group(1)}.'
    if (match := re.fullmatch(r'raw_step_midpoint_fungus_(\d+)', name)):
        return f'1 when the accepted original-coordinate step midpoint lies inside fungus ROI {match.group(1)}.'
    if (match := re.fullmatch(r'(raw|pscp)_fungus_(\d+)_(frames|distance_px)', name)):
        source,number,measure=match.groups()
        return f'{"Original IDtracker" if source=="raw" else "PSC-model"} fungus ROI {number} {"frame count" if measure=="frames" else "accepted midpoint-allocated movement distance in pixels"}.'
    if (match := re.fullmatch(r'(raw|pscp)_(.+)', name)) and match.group(2) in COLUMNS:
        source='original IDtracker coordinates and the raw jump cutoff' if match.group(1)=='raw' else 'PSC-model coordinates and the reconstruction speed limit'
        return f'{COLUMNS[match.group(2)]} Calculated using {source}.'
    if (match := re.fullmatch(r'fungus_(\d+)', name)):
        return f'1 if this frame’s working position lies inside fungus ROI {match.group(1)}; otherwise 0.'
    if (match := re.fullmatch(r'step_midpoint_fungus_(\d+)', name)):
        return f'1 if the accepted step from the previous frame has its midpoint inside fungus ROI {match.group(1)}.'
    if (match := re.fullmatch(r'fungus_(\d+)_frames', name)):
        return f'Number of analyzed frames in fungus ROI {match.group(1)} under this table’s coordinate source.'
    if (match := re.fullmatch(r'fungus_(\d+)_distance_px', name)):
        return f'Sum of accepted movement distances whose step midpoints lie in fungus ROI {match.group(1)}, in pixels.'
    return None


def render(analysis: Path, review: Path, receipt: Path | None = None,
           source_toml: Path | None = None) -> str:
    manifest = json.loads((analysis/'manifest.json').read_text())
    review_manifest = json.loads((review/'source_manifest.json').read_text())
    csv_paths = sorted(analysis.glob('*.csv'))
    unknown_files = {p.name for p in csv_paths} - set(CSV_FILES)
    missing_files = set(CSV_FILES) - {p.name for p in csv_paths}
    if unknown_files or missing_files:
        raise ValueError(f'Update output-manifest file descriptions: unknown={sorted(unknown_files)}, missing={sorted(missing_files)}')
    headers = {}
    unknown_columns = {}
    for path in csv_paths:
        with path.open(newline='') as stream:
            columns = next(csv.reader(stream), [])
        headers[path.name] = columns
        undefined = [name for name in columns if column_description(name, path.name) is None]
        if undefined:
            unknown_columns[path.name] = undefined
    if unknown_columns:
        raise ValueError(f'Update output-manifest column definitions: {unknown_columns}')
    for name, path in [('analysis/manifest.json',analysis/'manifest.json'),
                       ('review/source_manifest.json',review/'source_manifest.json')]:
        unknown = set(json.loads(path.read_text())) - set(JSON_KEYS[name])
        if unknown:
            raise ValueError(f'Update output-manifest JSON definitions for {name}: {sorted(unknown)}')
    start = int(manifest['settings']['start'])
    end = start + int(manifest['settings']['window'])
    lines = [
        f'# Output manifest and data dictionary: {manifest["cell_label"]}',
        '',
        f'*Documentation schema {VERSION}; group processor {manifest["script_version"]}; persistent group model {manifest["persistent_model_version"]}.*',
        '',
        'This guide describes the actual files and CSV columns in this run. It is written for students and can be printed to PDF from a Markdown viewer. The outputs are **UNREVIEWED** until someone checks beetle identities and inferred contacts in the video.',
        '',
        '## Contents', '',
        '- [Run at a glance](#run-at-a-glance)',
        '- [How to read these results](#how-to-read-these-results)',
        '- [File map](#file-map)',
        '- [CSV data dictionary](#csv-data-dictionary)',
        '- [Other files and settings](#other-files-and-settings)',
        '- [Recalculating from frame data](#recalculating-from-frame-data)',
        '- [Review and provenance cautions](#review-and-provenance-cautions)',
        '',
        '## Run at a glance', '',
        f'- **Trial label:** `{manifest["cell_label"]}`',
        f'- **Original-video frames:** {start} through {end}, inclusive ({end-start+1:,} frames).',
        f'- **Beetles:** {manifest["animal_count"]}; IDs begin at 0.',
        f'- **ROIs:** one arena and {len(manifest["rois"])-1} fungus regions. Fungus numbers preserve TOML input order; they are not automatically sorted.',
        f'- **Review status:** `{manifest["qc_status"]}`.',
        f'- **Trajectory source:** `{manifest["trajectory_source_kind"]}`.',
        f'- **Source TOML:** `{source_toml.name if source_toml else "not supplied to this post-processing run"}`.',
        '',
        '## How to read these results', '',
        '- **Raw** means the selected IDtracker trajectory coordinate before this PSC model; the selected input may itself be a validated or gap-processed IDtracker array. Check `trajectory_source_kind`. **Working/canonical** means the position used by the persistent-group model. They are kept separately.',
        '- **Observed proximity** requires two independently assigned beetles near one another. **PSCP** (presumed social contact position) assigns a group member without an independent accepted position to a detected shared blob. If the whole group loses a defensible detection, its position stays missing even while contact membership may persist.',
        '- A presumed position is an inference, not a second independently seen beetle. A copied group path can count toward each member’s estimated distance and fungus occupancy; the original-coordinate summaries remain separate.',
        '- Paired `raw_` and `pscp_` summary columns use the same frame windows and ROI polygons. Their adjacent-step cutoffs differ: the raw jump cutoff is in `settings.jump_threshold_px`; the PSC-model continuity cutoff is in `reconstruction.max_speed_px_per_frame`. Wake frame is defined only from the original path.',
        '- `full` covers the entire chosen interval. `post_wake` starts when that beetle reliably crosses the movement threshold. `post_wake_3600` is the shared 3,600-step interval after the latest reliable wake; with inclusive endpoints it contains 3,601 frame observations when available.',
        '- Distances and coordinates use **pixels in the original video**, and durations use **frames**, not seconds. Blank numeric cells mean the value was unavailable or not applicable; they are not zero.',
        '',
        '## File map', '',
        '- `analysis/*.csv` — analysis tables described below. The three `*_comparison.csv` files place raw and PSC-model values side by side; the separate source-specific files remain for compatibility.',
        f'- `analysis/{manifest["pdf_filename"]}` — plots and summary tables for this trial.',
        '- `analysis/canonical_states.npz` — compact NumPy arrays for software reuse; CSV alternatives are provided for students.',
        '- `analysis/unified_qc.html` and `analysis/unified_qc.json` — shared video-disturbance and raw-tracking review evidence when generated by the current pipeline; check scan status before interpreting an absence of flags.',
        '- `analysis/manifest.json` — analysis settings, ROI geometry, code/input hashes, and scientific cautions.',
        '- `analysis/OUTPUT_MANIFEST.md` — this guide.',
        f'- `review/{review_manifest["html"]}` — interactive frame-by-frame visual review. Open after extracting the bundle.',
        f'- `review/{review_manifest["video"]}` — synchronized cropped video; keep it beside the HTML file.',
        '- `review/source_manifest.json` — video and review-code hashes, crop, frame rate, and review state.',
        '- `analysis.pipeline_receipt.json`, when supplied — command, input/output paths and hashes for the complete pipeline.',
        '- `analysis.blob_evidence.json`, when supplied — IDtracker blob centroids/identities by frame used to support persistent groups.',
        '- `source.toml` and `submitted.toml`, when supplied — original and exact tracking settings; they may differ if a run was retuned.',
        '',
        '## CSV data dictionary', '',
        'Each CSV has a header row. A row can describe one beetle, one pair, one event, or one beetle-frame; check the file description before combining tables. Column names and definitions below are read from this run’s real CSV headers.',
    ]
    for filename in CSV_FILES:
        lines += ['', f'### `analysis/{filename}`', '', CSV_FILES[filename], '']
        for name in headers[filename]:
            lines.append(f'- `{name}` — {column_description(name, filename)}')
    lines += ['', '## Other files and settings', '',
              '### `analysis/canonical_states.npz`', '',
              'This compressed NumPy file stores arrays with one time axis per original-video frame in the analyzed interval. Open it with `numpy.load` if you need the complete working arrays. Its entries are:','']
    for key, description in NPZ_ARRAYS.items():
        lines.append(f'- `{key}` — {description}')
    for filename in ('analysis/manifest.json','review/source_manifest.json'):
        lines += ['',f'### `{filename}`','',
                  'The fields below document provenance and review state. Nested `settings` values are numeric thresholds in source-video pixels or frame counts unless labeled otherwise.','']
        for key in json.loads((analysis if filename.startswith('analysis/') else review).joinpath(Path(filename).name).read_text()):
            lines.append(f'- `{key}` — {JSON_KEYS[filename][key]}')
    lines += ['', '### Input TOMLs, if included', '',
              'The source TOML is the student-entered configuration; the submitted TOML is the exact copy sent to IDtracker. The most common fields are:','']
    for key, description in TOML_KEYS.items():
        lines.append(f'- `{key}` — {description}')
    lines += ['', '### Pipeline receipt and blob evidence, if included', '',
              '- The pipeline receipt records input paths and SHA-256 hashes, analyzed frame interval, thresholds, source video, and output paths. Paths may name Firebird locations that are not valid on another computer.',
              '- Blob evidence is a JSON map keyed by original frame. Each blob has `centroid` (x/y pixels), `identities` (IDtracker IDs, sometimes missing), and `crossing` (whether IDtracker called it a crossing). `source_sha256` identifies the original IDtracker blob file.',
              '', '## Recalculating from frame data', '',
              'Use `analysis/frame_data.csv` when you want a different frame window. Filter `global_frame` to the new inclusive range and group by `animal_id`. Raw and PSC-model positions each have their own location, fungus, and accepted-step columns. Count `raw_fungus_N` versus `fungus_N` for paired occupancy; sum `raw_step_distance_px` versus `step_distance_px` only for accepted steps whose corresponding midpoint flag is 1. The first retained frame has no within-window preceding step, so exclude a step that begins before your new window. `raw_proximity_partners`, `observed_proximity_partners`, `pscp_partners`, and `unresolved_contact_partners` preserve distinct contact classes.',
              '', '## Review and provenance cautions', '',
              '- The selected IDtracker result and this post-processing output are **not verified ground truth**. Inspect unexpected jumps, missing frames, pile membership, and fungus assignment in the HTML video.',
              '- High IDtracker identity scores or a low missing percentage do not prove correct identities during fights.',
              '- Folder or session names may contain old labels. Use the source TOML, receipt, video path, ROI geometry, and selection manifest to confirm biological labels.',
              '- The analysis `output_sha256` list was recorded before this guide was added; the guide is an additional documentation file, not a change to the measured data.',
              f'- This guide was generated by `output_manifest.py` version {VERSION} (SHA-256 `{sha256(Path(__file__))}`). New output columns must be defined there before a future run can finish with a documented manifest.',
              '']
    return '\n'.join(lines)


def write_output_manifest(analysis: Path, review: Path, receipt: Path | None = None,
                          source_toml: Path | None = None, output: Path | None = None) -> Path:
    analysis = Path(analysis)
    review = Path(review)
    destination = Path(output) if output else analysis/'OUTPUT_MANIFEST.md'
    if destination.exists():
        raise FileExistsError(destination)
    content = render(analysis, review, receipt, source_toml)
    destination.write_text(content)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis', required=True, type=Path)
    parser.add_argument('--review', required=True, type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--source-toml', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    print(write_output_manifest(args.analysis, args.review, args.receipt, args.source_toml, args.output))


if __name__ == '__main__':
    main()
