# Strict BA jump gate

Vince authorized stricter handling of unresolved jumps on 13 October 2026.
The new separate BA gate marks both endpoints of every remaining step >=100
original-image pixels unknown. It never interpolates across a gap. Existing
image-supported recovery proposals are its input; this change does not rerun
recovery or claim that failed candidates now have better evidence.

There is no reliable independent anchor evidence for episode boundaries in
these sidecars. Therefore all movement steps in each affected run are unavailable,
with BLOCKED_UNRESOLVED_JUMPS status, pending a human inclusion/exclusion decision.
Endpoint masking is a minimum uncertainty mask, not a claim that the rest of the
run is correct. No beetles are automatically excluded and no posture is inferred.

Across the delivered 100 runs, nine are blocked for 230 remaining discontinuities.
NEW_016 has seven; NEW_015 has 192. All 100 strict arrays were checked for no finite
adjacent steps >=100, and every blocked movement array is entirely NaN. Three
focused algorithm tests and the existing six UI and ten export checks passed.
Browser inspection confirmed the strict default and visible movement-block warning.

The live human QC viewer on port 8798 defaults to this separate strict track.
Original and delivered proposal comparisons remain optional. Video trails do not
join >=100-pixel steps. Blocked runs cannot receive a new Looks usable decision.
Existing human decisions and dataset identity remain unchanged; new decisions
record the gate version and movement status. Earlier decisions are historical,
not approvals of the new analysis gate.

Reproduce with build_ba_strict_jump_qc.py. Artifacts and receipt are in
outputs/ba_human_qc_20261013/strict_v1/. Consumers must use its analysis and
movement_step_px arrays and respect movement_status. Previously generated
scientific reports and production pipeline outputs have not been regenerated or
silently altered. This is a BA review/analysis gate, not a production release.
