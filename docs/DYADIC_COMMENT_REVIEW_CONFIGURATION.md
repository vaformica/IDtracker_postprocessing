# Local source link for comment review

The comment-review builder no longer contains a private spreadsheet access link.
It reads the optional `DYADIC_REVIEW_SOURCE_URL` environment variable at build time.
Supply that value using your local environment or secret manager; do not save it
in repository files or shell commands retained in shared logs. With no value,
the packet has an empty source URL and hides the spreadsheet link. Existing
private input paths and processing behavior are otherwise unchanged.

If configured, the link is embedded in generated `review_data.json` and
`START_HERE.html`. Those outputs are private review artifacts, not source files
for publication. Existing packets are not rewritten by this code change.

Removing the literal from new source does not remove it from earlier public
Git history or previously distributed artifacts. The owner should assess
revoking/replacing the old Dropbox sharing link separately. This fix does not
revoke access or rewrite history.

Self-contained checks (no research inputs, media processing or network):

```sh
python3 -m unittest discover -s tests -p test_dyadic_comment_review_config.py
node tests/test_dyadic_comment_review.cjs
```

The JavaScript checks use synthetic frame arrays and comment cards. They cover
navigation, clamping, persistence, explicit decisions, invalid imports, and
optional source-link display. They do not establish browser playback or
scientific validity.
