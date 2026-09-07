# Preliminary security triage

> Generated automatically from CI reports. This is a first-pass decision and does not replace human review.

| Source | Finding | Severity/Risk | Location/Target | Strategy | Rationale |
|---|---|---|---|---|---|
| DAST | Content Security Policy (CSP) Header Not Set | Medium (High) | https://preview.owasp-juice.shop/ | Fix | Medium finding affects browser/session hardening; validate context and remediate. |
| DAST | Cross-Domain Misconfiguration | Medium (Medium) | https://preview.owasp-juice.shop/assets/public/favicon_js.ico | Backlog | Baseline finding requires contextual triage before becoming a release blocker. |
| DAST | Cross-Origin-Embedder-Policy Header Missing or Invalid | Low (Medium) | https://preview.owasp-juice.shop/ | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |
| DAST | Cross-Origin-Opener-Policy Header Missing or Invalid | Low (Medium) | https://preview.owasp-juice.shop/ | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |
| DAST | Dangerous JS Functions | Low (Low) | https://preview.owasp-juice.shop/chunk-Bvta1DJp.js | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |
| DAST | Deprecated Feature Policy Header Set | Low (Medium) | https://preview.owasp-juice.shop/ | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |
| DAST | Permissions Policy Header Not Set | Low (Medium) | https://preview.owasp-juice.shop/ftp/package-lock.json.bak | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |
| DAST | Server Leaks Version Information via "Server" HTTP Response Header Field | Low (High) | https://preview.owasp-juice.shop/ftp/coupons_2013.md.bak | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |
| DAST | Strict-Transport-Security Header Not Set | Low (High) | https://preview.owasp-juice.shop/assets/public/favicon_js.ico | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |
| DAST | Timestamp Disclosure - Unix | Low (Low) | https://preview.owasp-juice.shop/assets/public/favicon_js.ico | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |
| DAST | Modern Web Application | Informational (Medium) | https://preview.owasp-juice.shop/ | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |
| DAST | Re-examine Cache-control Directives | Informational (Low) | https://preview.owasp-juice.shop/ftp | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |
| DAST | Storable and Cacheable Content | Informational (Medium) | https://preview.owasp-juice.shop/robots.txt | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |
| DAST | Storable but Non-Cacheable Content | Informational (Medium) | https://preview.owasp-juice.shop/ | Monitor | Low/informational baseline signal; keep for hardening and monitoring. |

## Strategy meanings

- **Fix** — remediate as soon as practical; blocking findings must be resolved before the gate passes.
- **Backlog** — schedule remediation after contextual validation.
- **Accept** — only by a documented, approved and time-bounded exception with compensating controls.
- **Monitor** — track vendor/runtime changes and reassess when new information appears.

The `Accept` strategy is intentionally not assigned automatically.
