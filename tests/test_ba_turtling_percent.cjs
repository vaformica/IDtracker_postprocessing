const assert=require('assert');const Q=require('../ba_combined_qc.js');
const mask=Array(100).fill(false);mask.fill(true,0,10);
const states=Array(100).fill('no_candidate_detected');
let t=Q.turtlingSummary(100,199,[[105,114],[110,119],[199,199]],mask,states,21);
assert.equal(t.human_marked_frames,16);assert.equal(t.combined_flagged_frames,21);assert.equal(t.estimated_percent,21);assert.equal(t.cutoff_reached,false);
t=Q.turtlingSummary(100,199,[],mask,states,null);assert.equal(t.estimated_percent,10);assert.equal(t.cutoff_reached,null);
t=Q.turtlingSummary(100,199,[[100,199]],null,null,100);assert.equal(t.estimated_percent,100);assert.equal(t.automatic_candidate_percent,null);assert.equal(t.estimate_basis,'human_marks_only');
console.log('PASS: inclusive bouts, overlap union, full-window denominator, automatic/human separation, cutoff boundary, clear, unavailable predictions');
