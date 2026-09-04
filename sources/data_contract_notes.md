# Data Contract Notes (for README integration later)

This project's `sources/citation_log.csv` functions as a data contract, in
the same spirit as the data-contract practice Target's own engineering team
has described publicly (tech.target.com, "Kelsa" pipeline architecture):
a documented agreement on where each figure comes from, who's accountable
for it, and how it was validated before use.

Four principles this project follows, matching Target's own stated
governance pillars:

- **Accessible** — every figure is public, cited, and reachable via a URL
  logged in citation_log.csv.
- **Reliable** — every number is hand-verified at least twice (see
  bridge_analysis.py's built-in check against hand-calculated constants)
  before being used in any chart.
- **Available** — the citation log and every script that reads it live in
  this repo, reproducible by anyone who clones it.
- **Discoverable** — one central log (citation_log.csv), not scattered
  across notebooks or hardcoded into charts.

Note on sourcing: this framing is corroborated by Target's own tech blog,
not by internal knowledge of Target's actual team practices. State it that
way in the README and in outreach — as an intentional design choice inspired
by public information, not as claimed insider knowledge.
