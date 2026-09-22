# 2024 six-beetle battles: OLD reconstruction review

The interactive video is `results/OLD_review_20260921/OLD_interaction_review.html`. Keep its sibling `OLD_source_crop.mp4` beside it. Open the HTML in a browser, or run `python3 results/serve_review.py` and visit http://127.0.0.1:8766/OLD_review_20260921/OLD_interaction_review.html.

The pair timeline, frame slider, and beetle/fungus/proximity/PSCP panel follow video frames 250–16997. Solid dots are speed-screened assignments; hollow dots are held last accepted positions; gold rings are separate PSCP hypotheses; dashed magenta marks are retrospective straight-line estimates. Red crosses can show rejected raw candidates. Hold and PSCP are alternative hypotheses, not simultaneous observed positions.

`trajectory_reconstruction.py` defaults to 100 original-image pixels per frame. Across a gap the allowed endpoint distance scales with elapsed frames. Reacquisition requires three consecutive finite candidate frames with bounded steps. This offline confirmation uses lookahead and does not prove identity; plausible swaps can still pass. Initial positions and end-of-file reacquisitions lacking sufficient confirmation are not accepted. Missing beetles stay at the last accepted position; separate linear bridge estimates are exported rather than substituted into observed measurements.

OLD results: 153 supplied-coordinate frames rejected/unconfirmed; 8299 missing-or-rejected beetle-frames have held positions. Five targeted reconstruction tests pass; 21 existing six-beetle tests pass; real OLD integration passed. Browser checks verified frame seeking, single-frame stepping, playback, PSCP partners, and fungus status. Clean source crop SHA-256: f687f8370f63908147c80787dcf1943cbe27c83c475d49a8fa7810dc8107e215.

Processor v0.5.0 adds a separately labeled reconstruction CSV and metadata with `--reconstruction-speed-px` (default100). Original-coordinate and previous PSCP metrics remain separate; older PDFs have not been regenerated under a different measurement definition. This review computes its proximity and PSCP hypotheses from speed-screened positions, not held coordinates. It labels fungus occupancy based on a held point as estimated. Fungus ON uses the same polygon-membership function as the PDF processor; held coordinates remain explicitly estimated.

Source video crop generated on Firebird in `six_beetle_review_20260921`, job897894. Source coordinates remain unmodified. Visual interpretation of individual contact/loss episodes remains a human review task.
