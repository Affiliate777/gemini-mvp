
- scripts/update-apply.sh: deploys release and always writes audit via update-audit-append.sh (EXIT trap).
- scripts/update-audit-append.sh: appends JSON lines to logs/update-audit.log
  Schema: {"version":"vX.Y.Z","release_dir":"/path/to/release","rc":0,"ts":<unix>}
- Tests:
    bash -x scripts/update-apply.sh v1.0.1
    bash -x scripts/update-apply.sh non-existent-version || true
