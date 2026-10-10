# SPEC-03 — Caixa integration
**Priority:** P0 | **Status:** Existing integration to verify

## Source
Existing project uses `https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil` and `/{number}`. This is an external dependency; do not assert contractual stability or live contest count without an actual request.

## Normalization
Fields currently relied on: `numero` (int), `dataApuracao` (dd/mm/yyyy), `listaDezenas` (15 string digits). Convert through existing `save_contest` and full model validation. Reject incompatible/partial payloads; never fabricate missing values.

## Networking
- Explicit connect/read timeout (existing timeout 20 seconds acceptable).
- 429 and 5xx -> transient; timeouts/connection errors -> transient; 400/404, invalid JSON/schema -> permanent for the specific attempt.
- Bounded backoff/retries only on transient categories; preserve terminal cause.
- Use an acceptable request interval; no parallel flood of requests.

## Testing
`requests.get` mocked in unit tests. Test normal response, 404, 429, 503, connection timeout, malformed payload, wrong requested number. No external HTTP in tests.

## Acceptance
Import one valid contest, classify errors correctly, persist exactly one valid contest per number; failure leaves existing results intact.
