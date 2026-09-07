# CI evidence

GitLab CI writes operational evidence here:

- `gate-sast.log`
- `gate-sca.log`
- `gate-dast.log`
- `zap-baseline-log.txt`
- tool version logs
- `triage.md`
- `security-bundle.txt`

Real files are produced by pipeline jobs and uploaded with
`artifacts: when: always`.
