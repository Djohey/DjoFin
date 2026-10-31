# DjoFin — security hold N1/N2 (31 Oct 2026)

Audit externe : `DjoFin_Audit_Global_Code_GitHub_2026-10-31.docx`.

## Containment applied on main
The five workflows formerly executing mutable `simulation-p0` code with write token or Gemini secret were replaced by manual-only, non-runnable security-hold jobs:
- archive-market-daily.yml
- djofin-public-news-collector.yml
- gemini-free-trial.yml
- gemini-list-models.yml
- gemini-minimal-probe.yml

Each hold declares `permissions: contents: read` and `if: false`. No scheduled collection, market archive, or Gemini API operation will run from these workflows while the hold remains.

## This is NOT full remediation
1. Audit every other workflow, including workflows on `simulation-p0`, for cross-branch checkout, `contents: write`, `persist-credentials`, and injected secrets.
2. Separate read-only collector/compute from authenticated data persistence; do not execute unreviewed code in a job with write credentials.
3. Pin Python dependencies with exact versions and hashes, and GitHub Actions to reviewed commit SHAs.
4. Protect production branch and pin trusted code revisions; avoid mutable checkout refs in privileged workflows.
5. Restore RSS and market archive schedules only after N1/N2 verification. Review missed intervals.
6. Verify external account billing independently; software policy alone is not a billing guarantee.
7. Preserve historical datasets before artifact expiry (N3).

## Operational impact
Scheduled news collection and daily market archive are temporarily stopped. This is deliberate. Manual Gemini probes are also blocked. Existing repository data is untouched. No real trades or paid API calls have been initiated.
