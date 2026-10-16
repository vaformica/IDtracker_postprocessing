# Dyadic fight processing handoff and proposed data dictionary

## Decision and scope

15 October 2026 | Proposed schema 0.1 | AI-written synthesis by Codex for Vince, Hannah and Savannah.
Vince reports that the group reviewed a handful of dyadic aggression videos and found the results good enough to advance to broader processing and quality review. Remaining centroid offsets were typically judged small, around half a body width, with some early or late proximity boundaries differing by a few frames. This is an attributed practical acceptance judgment, not a measured population error rate. It does not automatically approve every run or every metric.
The next batch belongs in the IDtracker operations chat: inventory and process all eligible fight TOMLs, then quality-check the resulting runs. No batch was launched or tracking changed for this handoff. Do not assume the historical 99-case inventory is still the complete eligible set.
Six-beetle work remains ON HOLD. The October 14 Zoom summary explicitly distinguishes problematic multi-beetle identity swaps and piles from the more usable dyadic results. BA work continues separately. This document proposes a dyadic data contract that could later be reused, not a restart of six-beetle work.

## October 14 discussion: evidence and remaining questions

The Zoom AI summary, emailed October 14 at 16:43 EDT, names Vincent Formica, Hannah Donald and Savannah Vonesh. It reports confidence in dyadic proximity, fungus occupancy, wall occupancy and distance measurements, with occasional centroid lag or misplacement. The group distinguished inferred PSC from actual touching and discussed comparing output with manual scoring. The AI summary is a secondary record; Vince's October 15 account is the authoritative current direction.
Other meeting priorities: standardize fungus/bracket outlines in TOMLs; Hannah and Savannah establish the behavior-scoring protocol and test it; consider Kieran for TOML preparation, including later BA rounds and gridded arenas; process Savannah's dBlock BAs on normal and plaster/fungus arenas before next summer. These are recorded meeting action items, not actions completed in this task. Zoom's informal 75-80% discussion is not an audited dyadic accuracy estimate and is not adopted here.
The October 14 VAF JSON contains 49 cards from 48 comments across 10 video/cell names: 28 OK, 6 ignore/no action, 8 investigate, 2 unsure and 5 without saved decisions. The earlier Slack message reported 11 videos reviewed. These denominators are different; 34/44 decided cards accepted/no-action is not a frame-level accuracy rate. Today's broader acceptance does not silently rewrite those stored decisions.
Outstanding examples: Camera 2 July 1 16:50 A1 frames 1476, 3590 and 4694 (missing-ID/PSC), 4548 (centroid jump); Camera 1 June 30 16:33 WRONG A2 frame 3058 (identity swap; Vince noted rerun); Camera 1 July 2 15:35 C2 (late start); Camera 2 June 30 16:34 WRONG C1 (unclear paint); Camera 1 July 1 13:32 C1 (localization during long PSC). Track disposition individually before using affected measurements.

## What the existing code already provides

Verified local code: persistent_groups.py PSC model 1.6.0; six_beetle_processor.py shared group processor 0.8.2-group; processor.py legacy/base 0.8.1. Dyads and six-beetle calls share the social engine. Raw/PSC viewer v4 has later display-only label controls; version alone is insufficient, so retain code hashes. IDtracker.ai version and tracking timestamps must be read per session; this task does not establish them.
Existing group outputs include animals.csv (latency and baseline), windows.csv and estimated_windows.csv (movement and coverage), regions.csv and estimated_regions.csv (region occupancy and midpoint-allocated distance), pairs.csv (joint visibility, proximity and bouts), events.csv, frame_data.csv, paired comparison tables and manifest.json. Older DATA_DICTIONARY.md mixes historical standalone columns with newer addenda; use exact code and each run's manifest when mapping fields.
Available historical features worth retaining: full and post-movement windows, accepted versus excluded steps, missingness, distance per valid step, open-arena and fungus-edge/interior measures, per-fungus summaries, pairwise event durations and first proximity latency. Turtling, touching, mounting, aggression, initiator/leaver and head-tail direction are not accepted dyadic outputs merely because exploratory code exists.
Proposed names below are a normalized analysis schema, not a claim that all fields already exist. E = existing measurement or source field to map; D = derived from existing evidence; N = new recording/export/definition needed. Every field still needs an explicit adapter and validation before release.

## Measurement rules to freeze before extraction

Coordinates and cutoffs use original-image pixels, not resized review pixels. Preserve calibration separately; do not report millimeters without a documented px/mm calibration. Observed means present in the selected IDtracker input, which may itself be validated or gap-processed; it does not prove direct independent observation or correct identity.
Proximity: two available assigned centroids at distance <=60 px. PSC: a missing ID inferred from compatible detection and proximity evidence. Keep observed proximity, inferred PSC and unknown pair time separate. Their union can be an explicitly named supported-social-context sensitivity measure, never physical contact or aggression duration.
Latency: current exact-start rule is first displacement >=30 px from the coordinate at analysis entry, reachable through uninterrupted accepted adjacent steps. A missing starting coordinate or broken chain must not become zero latency or a later substituted baseline. It measures displacement onset, not necessarily first limb movement or righting. Record observation start relative to release/stimulus and flag already-moving starts. Current THRESHOLD_NOT_REACHED can include interrupted chains; the proposed censoring reason must distinguish true complete non-crossing from lost evidence.
Wall occupancy: centroid inside arena and within 30 px of its boundary by default. Fungus occupancy: centroid inside the source polygon. Freeze an outline protocol, author, version and boundary-inclusion convention. Suggested protocol: trace the visible physical bracket boundary consistently, define treatment of shadow/occlusion, retain an image overlay and a second-person check; final biological inclusion rule remains to be agreed.
Distance along wall means accepted 2-D path distance allocated to the wall zone by the step midpoint; it is not distance projected onto the perimeter. Fungus distance uses the same midpoint rule. No movement bridges unknown frames. Raw cutoff defaults to 200 px/step; PSC path defaults to 100 px/step. Record actual settings and do not interpret raw-versus-PSC differences as inference effects alone when cutoffs differ. A common-cutoff comparison is an additional analysis.
Let N=end-start+1. Occupancy seconds = classified frame count / fps; the timestamp span is (N-1)/fps. Accepted-step seconds = accepted steps / fps. Distance/accepted-step seconds is conditional mean speed; distance divided by all scheduled time is a different coverage-dependent quantity. Store both denominators. Unknown is never automatically off-fungus, apart or stationary.
Baseline proximity bouts are maximal consecutive positive frames with no smoothing. Unknown frames break evidence, not prove separation: mark adjacent bout boundaries censored and retain known-outside/unknown causes. Report observed segment count separately from fully bounded interaction count. Any debounce, minimum duration or bridging rule requires an agreed parameter/version and sensitivity comparison.
Full window is the primary proposed window. Dyadic reviews have used 7200 inclusive observations. Existing code's window argument counts intervals, so a 7200-observation request must map to 7199 intervals. Legacy post_wake_3600 means 3600 intervals/3601 observations anchored after the latest animal crossing; do not silently label it 3600 frames. Use explicit IDs and bounds for every window.

## Data model and joins

Use UTF-8 CSV for small analysis tables, Parquet for frame data and JSON for manifests/geometry. Keep immutable source artifacts and append new processing attempts. Identifiers are opaque stable strings; filenames are descriptive attributes, not the only join keys. A new processing attempt gets a new processing_run_id. A physical arena/cell trial keeps its trial_id across reruns.
Tables: recordings (one source video); trials (one experimental cell/trial); tracking_runs (one IDtracker attempt); processing_runs (one post-processing attempt); animal_identity (one run-local identity mapping); windows (one analysis window); animal_window (one run x animal x window x trajectory layer); region_metrics (same plus region); pair_window (one unordered pair x window); bouts (one event segment); frame_observations and pair_frames (optional granular evidence); review_decisions (one attributed, versioned decision); artifacts (one file/hash). Use a separate run-selection table for the single approved attempt per trial/metric.
Primary keys must be unique. animal_a < animal_b for unordered pairs. Animal 0 in one run is not animal 0 in another run. Biological beetle IDs and paint colors need an explicit attributed mapping; uncertain mapping remains null. Two beetles in a dyad are paired observations, not independent trials. Treatments and repeat-measure identifiers come from the experimental record, never guessed from filename tokens.
Null means unmeasured/unknown/not applicable with a reason code. Zero is reserved for an observed absence or measured zero with a valid denominator. ISO-8601 UTC timestamps retain source timezone and precision when available; date-only historical information stays date-only. Never use file modification time as the tracking date. Keep named tolerances and classifications, not a single undocumented confidence score.

## Proposed data dictionary

Status: E existing source/measurement; D derived; N new definition/export needed. Compound field listings expand to separate columns.

### recordings

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| recording_id | string PK | N | Stable identity for the original source video, shared by all cells. |
| video_filename | string | E | Exact source basename including extension; retain Camera and ACT tokens. |
| video_uri | string | E | Canonical original-video location; review MP4 is a different artifact. |
| video_sha256 | string | E | Content hash, not a filename hash. |
| recorded_at | string timestamp/date nullable | N | Acquisition date/time from authoritative metadata; retain precision and source. |
| camera_id | string nullable | N | Camera serial/name from acquisition record or verified filename mapping. |
| fps | float frames/s | E | Actual source frame rate; use frame timestamps if variable-frame-rate. |
| frame_count | integer | E | Total decoded source frames, independently checked. |
| width_px,height_px | integers px | E | Original image dimensions; separate from review crop dimensions. |
| calibration_px_per_mm | float nullable | N | Measured scale with calibration artifact; null if unavailable. |

### trials

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| trial_id | string PK | N | Stable physical experimental trial/cell identifier across reruns. |
| recording_id | string FK | N | Links to recordings. |
| cell_id | string | E | Exact TOML cell label, e.g. A2; source stem retained separately. |
| source_toml_name,source_toml_uri | strings | E | Original configuration name and immutable path. |
| source_toml_sha256 | string | E | Hash of original configuration; submitted copies separately recorded. |
| assay_type | string | N | DYADIC_FIGHT for this handoff; BA and SIX_BEETLE remain separate scopes. |
| experimental_block,treatment,replicate_id | strings nullable | N | Verified design metadata; null until mapped, not inferred. |
| animal_count | integer | E | Expected identities, 2 for dyads. |
| stimulus_global_frame | integer nullable | N | Release/experimental time origin, source and reviewer; may differ from tracking start. |
| roi_definition_uri,roi_sha256 | strings | E | Original-coordinate arena and ordered fungus polygons. |
| roi_protocol_version,roi_author,roi_review_status | strings nullable | N | Boundary drawing protocol and attributed verification. |
| source_start_global_frame | integer | E | TOML start before any approved revision. |

### tracking_runs

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| tracking_run_id | string PK | N | Unique IDtracker attempt; never overwrite a prior attempt. |
| trial_id | string FK | N | Physical trial processed. |
| session_uri,trajectory_uri | strings | E | Exact session and selected trajectory file. |
| trajectory_sha256,submitted_toml_sha256 | strings | E | Hashes of actual inputs used downstream. |
| trajectory_source_kind | string enum | E | Raw, validated or gap-processed input; use exact recorded category. |
| idtracker_version | string nullable | N | Version from environment/log for this attempt, not current installed version. |
| tracking_started_at,tracking_completed_at | UTC timestamps nullable | N | From execution records; preserve unknown and timestamp provenance. |
| tracking_date_source | string | N | Log/manifest/manual attribution/unknown, with evidence URI. |
| container_digest,environment_uri | strings nullable | N | Immutable SIF/image digest and dependency capture. |
| tracking_status | string enum | N | RUNNING, COMPLETE, FAILED, COMPLETE_WITH_WARNING or UNKNOWN with log evidence. |
| tracking_log_uri,job_id | strings nullable | E | Execution evidence; scheduler success alone does not establish valid tracking. |

### processing_runs

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| processing_run_id | string PK | N | Unique post-processing attempt; joins every derived table. |
| tracking_run_id | string FK | N | Exact upstream attempt. |
| processor_version,psc_engine_version,base_processor_version | strings | E | Current verified local values 0.8.2-group, 1.6.0, 0.8.1; record actual deployed versions per run. |
| code_revision,code_bundle_sha256 | strings | N | Git revision plus hash of actual dirty/frozen source bundle; revision alone is insufficient. |
| viewer_version,viewer_code_sha256 | strings | E | Display version and exact code hash; display changes do not change science version. |
| qc_version,schema_version,metric_definition_version | strings | N | Separate QC, table contract and scientific-definition versions. |
| processing_started_at,processing_completed_at | UTC timestamps | N | Actual processor execution times; packaging and review times are separate. |
| parameter_json,parameter_sha256 | JSON/string | E | All resolved settings including inactive legacy arguments explicitly marked. |
| social_radius_px,wall_buffer_px,fungus_buffer_px | floats px | E | Current defaults 60, 30, 30; retain resolved values. |
| raw_jump_cutoff_px,psc_jump_cutoff_px | floats px/step | E | Current defaults 200 and 100; retain inequality convention. |
| movement_threshold_px | float px | E | Current latency threshold 30 px. |
| analysis_status,review_status | strings | N | Separate successful computation from UNREVIEWED/NEEDS_REVIEW/ACCEPTED_FOR_METRIC. |
| manifest_uri,manifest_sha256 | strings | E | Exact output provenance manifest; timestamps may need new instrumentation. |

### animal_identity

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| processing_run_id,animal_id | composite PK; ID integer | E | Zero-based run-local tracking index, not biological identity. |
| biological_beetle_id | nullable string FK | N | Validated experimental individual ID; no automatic cross-run match. |
| paint_color,identity_mapping_status | strings nullable | N | Human mapping and CONFIRMED/UNCERTAIN/UNKNOWN. |
| identity_mapping_reviewer,identity_mapping_evidence | strings nullable | N | Attribution and source frames/record. |

### windows

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| processing_run_id,window_id | composite PK strings | N | Explicit named interval, e.g. full or post_both_move_3600_intervals. |
| start_global_frame,end_global_frame_inclusive | integers | E | Original global indices; never renumber scientific coordinates. |
| window_n_frames,window_n_intervals | integers | D | N and N-1; requested and actual values must match or status fails. |
| window_duration_s,timestamp_span_s | floats seconds | D | N/fps and (N-1)/fps, respectively. |
| window_anchor_rule,window_status | strings | E | Full, individual crossing or latest pair crossing; explicit unavailable/truncated status. |
| excluded_frames_uri | nullable string | N | Human-approved excluded intervals with attribution; retain as unknown. |

### animal_window

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| processing_run_id,animal_id,window_id,trajectory_layer | composite PK | N | Layer RAW_INPUT or PSC_ESTIMATED; do not pool layers as replicates. |
| latency_to_threshold_frames,latency_to_threshold_s | integer/float nullable | E/D | Existing animals.csv latency; seconds=frames/fps. Exact-start continuous-chain rule. |
| threshold_crossing_global_frame | integer nullable | E | First reachable threshold crossing, not necessarily first physical movement. |
| latency_status,latency_censor_reason | strings | E/N | OBSERVED, NOT_REACHED_FULL_COVERAGE, MISSING_BASELINE, CHAIN_BROKEN, START_ALREADY_MOVING or UNRESOLVED; adapter must distinguish legacy ambiguous status. |
| valid_coordinate_frames,missing_coordinate_frames | integers | E | Located versus unknown observations within this window. |
| observed_frames,inferred_psc_frames,inferred_other_frames | integers | D | Disjoint location evidence classes; do not count inferred as observed. |
| tracking_coverage_fraction | float 0..1 | D | Valid coordinate frames/window_n_frames, separately by layer. |
| accepted_steps,missing_endpoint_steps,rejected_jump_steps | integers | E | Partition N-1 candidate steps; no incoming step from before window. |
| distance_px | float nullable px | E | Sum Euclidean adjacent steps passing this layer's cutoff; null if none evaluable. |
| accepted_step_time_s | float seconds | D | Accepted_steps/fps. |
| mean_speed_valid_px_s | float nullable px/s | D | Distance/accepted_step_time_s; null for zero denominator. |
| distance_per_scheduled_s | float nullable px/s | D | Distance/window_duration_s, explicitly coverage-dependent, not interchangeable with conditional speed. |
| max_raw_jump_px,raw_jumps_gt100 | float/integer | D | Diagnostic maximum and count of consecutive finite raw displacements >100 px, independent of movement cutoff. |
| longest_missing_gap_frames,missing_gap_count | integers | D | Contiguous unknown runs; record censoring at window edges. |
| movement_metric_usable,identity_metric_usable | booleans nullable | N | Attributed metric-specific eligibility; null before review, not inferred from no warnings. |

### region_metrics

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| processing_run_id,animal_id,window_id,trajectory_layer,region_id | composite PK | N | Long-format wall, any_fungus, fungus_1..N, open_arena, fungus edge/interior etc. |
| region_coordinate_frames | integer | E | Centroid membership from regions.csv coordinate_frames. |
| region_time_s | float seconds | D | Region frames/fps; unknown frames excluded from numerator. |
| region_fraction_located | float nullable | D | Region frames/valid_coordinate_frames for this layer/window. |
| region_fraction_scheduled | float nullable | D | Region frames/window_n_frames; accompanying coverage required. |
| region_accepted_steps | integer | E | Accepted steps whose midpoint is in region. |
| region_distance_px | float nullable px | E | Midpoint-allocated distance from regions.csv; not perimeter arc length. |
| region_mean_speed_px_s | float nullable px/s | D | Region distance/(region_accepted_steps/fps). |
| region_entry_count,first_entry_latency_s | integer/float nullable | N | Optional consecutive known outside-to-inside transitions; unknown boundaries censored. |
| region_visit_median_s,region_visit_max_s | floats nullable seconds | N | Optional fully observed visit durations; censored visits retained separately. |

### pair_window

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| processing_run_id,window_id,animal_a,animal_b | composite PK | E/N | One unordered pair; a<b. A dyad contributes one pair, not two independent observations. |
| jointly_located_frames | integer | E | Both raw-input IDs located; existing pairs.csv jointly_visible_frames. |
| observed_proximity_frames,observed_proximity_s | integer/float seconds | E/D | Both assigned centroids <=60 px; frames/fps. |
| proximity_fraction_jointly_located | float nullable | E | Observed proximity frames/jointly located frames; null if denominator zero. |
| observed_proximity_segments | integer | E | Existing proximity_bouts: contiguous positive segments, including censored ones. |
| complete_proximity_bout_count | integer | N | Segments with known outside state at both boundaries; unknown breaks cannot establish separate complete interactions. |
| psc_inferred_frames,psc_inferred_s | integer/float seconds | D | Pair-specific missing-ID PSC evidence; never called touching time. |
| pair_unknown_frames | integer | D | Neither measurable two-ID distance nor supported PSC; state mapping explicitly versioned. |
| supported_social_context_s | float seconds | N | Optional union of observed proximity and supported PSC, no double counting; separate from primary observed proximity. |
| first_proximity_latency_s | float nullable seconds | D | First observed positive relative to window start; mark starts-already-near and unknown-before-onset. |
| proximity_bout_median_s,proximity_bout_max_s | floats nullable seconds | D | Fully bounded bouts only in primary summary; censored durations listed separately. |
| median_pair_distance_px | float nullable px | D | Median center distance over jointly located frames, irrespective of proximity. |
| identity_swap_review_status | string | N | UNREVIEWED/SUSPECTED/CONFIRMED/RESOLVED with attributed evidence. |

### bouts

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| bout_id | string PK | N | Unique event identity within processing run, pair and window. |
| processing_run_id,window_id,animal_a,animal_b | FKs | E/N | Exact run/pair context. |
| event_type,evidence_layer | strings | E/N | OBSERVED_PROXIMITY or INFERRED_PSC; human TOUCH/MOUNT/ATTACK separately sourced, never auto-substituted. |
| start_global_frame,end_global_frame_inclusive | integers | E | Event bounds in original video. |
| frame_count,duration_s | integer/float seconds | E/D | End-start+1 and count/fps. |
| left_censored,right_censored,boundary_reason | booleans/string | N | Window edge, missing evidence, exclusion or known transition. |
| rule_version,review_decision_id | strings nullable | N | Event definition version and optional linked human review. |

### frame_observations / pair_frames

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| processing_run_id,global_frame,animal_id | observation PK | E/N | Per-animal evidence; pair_frames replaces animal_id with sorted pair. |
| raw_x_px,raw_y_px,model_x_px,model_y_px | floats nullable | E | Preserve original and inferred coordinates side by side. |
| location_source,inferred,identity_conflict | enum/booleans | E | Exact processor evidence states, including missing/ambiguous; no imputation to zero. |
| region_membership,step_accepted,step_distance_px | list/boolean/float | E | Membership and adjacent-step evidence; first step is not applicable. |
| pair_distance_px,pair_state | float nullable/enum | D | Observed distance plus OBSERVED_NEAR/OBSERVED_APART/INFERRED_PSC/UNKNOWN; validate mutually exclusive mapping. |

### review_decisions / artifacts / selection

| Field | Type / unit | Status | Definition |
|---|---|---|---|
| review_decision_id,reviewer,reviewed_at | ID/string/UTC | N | Attributed decision; preserve original review export hash. |
| processing_run_id,metric_scope,coverage_intervals | FK/string/list | N | Exactly which version, metric and frames were inspected; unseen is not approved. |
| decision,reason,notes,supersedes_decision_id | strings nullable | N | Append-only decisions and revisions; never overwrite original annotations. |
| artifact_id,artifact_type,uri,sha256 | strings | E/N | Video, TOML, trajectory, CSV, PDF, HTML, review JSON, log and code bundle inventory. |
| artifact_created_at | UTC nullable | N | Creation/export time, separate from acquisition and computation dates. |
| selected_processing_run_id,selection_reviewer,selection_reason | strings | N | Exactly one selected result per trial/metric/versioned analysis release; do not silently choose newest rerun. |

## Export and validation contract

Each grouped comma-separated field name in the dictionary denotes separate columns of the stated types. Composite key rows specify join keys, not a serialized cell. Flatten parameter JSON only through a versioned adapter. All tables carry processing_run_id directly or through a documented foreign key.
Validate unique keys and foreign keys; exactly two run-local identities for dyads; no pair self-links; correct global frame ranges; source/trajectory/TOML/code hashes; correct video-to-frame mapping; 7200 inclusive observations for the standard full window; fractions in [0,1]; numerator <= denominator; no finite speed with zero accepted time. Check N-1 = accepted + rejected + missing-endpoint steps under the declared exclusion policy.
Region labels are not all disjoint. Wall and fungus can overlap; any_fungus is a union, not a sum of overlapping brackets. Only explicitly disjoint partitions may be required to sum to all located observations. Keep outside-arena separate; current non_wall includes outside-arena and is not the same as open_arena.
Freeze the source version and verify every rendered video frame count, links, exported table schema, package checksums and provenance. Software checks do not establish behavioral accuracy. Do not infer absence of behavior from an unreviewed or missing observation.
Human QC should combine a reproducible random sample across cameras, dates and cells with a separate warning-targeted sample. Inspect whole runs in part of the sample, especially for persistent identity swaps. Preserve sampling seed and inclusion probabilities; targeted examples cannot estimate an overall error rate. Double-score a subset and reconcile definitions. Report errors by metric and trial, including duration discrepancies and identity continuity, rather than only centroid offsets.
Before biological analysis, compare aggregate proximity, fungus and wall measures with attributed manual measurements on the audit sample. Set tolerances before scoring, and compare conclusions with/without flagged trials or with alternative proximity-boundary/bout rules. The group's practical acceptance is permission to advance, not a reason to conceal unresolved measurement-specific limitations.

## Operations handoff and decisions still needed

1. Inventory all fight TOMLs and map source video, cell, tracking attempt and design metadata. Reconcile exclusions, duplicates and incompatible settings; publish counts at each stage. Historical 99-case and current 25-case collections are references, not a new batch specification.
2. Agree on movement latency semantics and time origin; wall/fungus outline rules; primary full-window duration; observed proximity versus inferred PSC reporting; bout splitting/censoring; units/calibration; and metric-specific acceptance tolerances. Record parameter and metric-definition versions.
3. Implement and test the normalized export adapter, tracking/processing timestamp provenance, censored latency and event statuses. Preserve existing columns with a mapping. Do not fabricate missing historical IDtracker version or run date.
4. In the operations chat, freeze/deploy the actual code snapshot into a new versioned batch root, process eligible dyads and produce QC flags, videos, CSVs, PDFs, index and execution receipts. No six-beetle restart follows from this handoff.
5. Hannah and Savannah finalize manual behavior definitions and score test runs. Vince reviews QC dispositions, especially start times, swaps and paint mappings. Keep touching/mounting/attack scores separate from geometric proximity.
6. Select eligible processing attempts per metric, publish a frozen analysis table with linked provenance, and record unresolved exceptions. Broader runs and their biological release are separate milestones.
Suggested additional outcomes: latency to first proximity and first fungus entry; complete-bout median/maximum duration; pair distance distribution; region visits; missingness and jump burden. Defer posture/turtling, directed aggression and initiator/leaver until separately scored and validated. No contact label should be generated solely because two centroids are close.

## Sources and reproducibility

Primary direction: Vince's October 15 instruction in this chat; October 14 VAF review export Dyadic_comment_decisions_20261014.json. The earlier review source hash is 0547ed82d05a12a4454e0a84a4f219b28b57f29b0f0078559f8e7219ddc87f03.
Zoom AI summary: Meeting assets for Vince's Calendly Zoom Room are ready!, October 14, 2026, Gmail message 1a13c283afdcd5d4. https://mail.google.com/mail/u/0/#all/1a13c283afdcd5d4
Original review workbook: https://www.dropbox.com/scl/fi/pcxxuuf42itc75f7kt32o/Manual_Review_IDtracker_20261014.xlsx?rlkey=notnljveggluv23xcns53x4lo&dl=0
Code inspected locally October 15: six_beetle_processor.py (regions, social_network, summarize_window, analyze_six), processor.py (compute_wake_threshold_result), persistent_groups.py; DATA_DICTIONARY.md; output_manifest.py; README.md; SIX_BEETLE_README.md. September 28 PROJECT_HANDOFF is historical, superseded by later corrections and withdrawals.
No live Firebird census or deployed-version verification was performed for this documentation task. Local code version is not proof of a particular remote run's version. Read each run's manifest, frozen source hashes and logs before choosing it for extraction.
