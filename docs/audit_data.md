# Audit page data (docs/data/audit_*.json)
Each file is read directly; a missing file shows "Not run yet". Figures are synthetic Mirage data (clubs Everett, Dedham and Waltham; DC Avon).

## 1. `data/audit_eval.json`: 30-question audit eval
`{run_at, runs[]}`: runs oldest first, with an optional `scoring_changed` flag. Written by `scripts/publish_eval.py`.
```json
{
  "run_at": "ISO-8601",
  "runs": [
    {
      "model": "string",
      "date": "YYYY-MM-DD",
      "scoring_changed": "boolean?",
      "summary": {
        "question_set": "mirage-q30-v1",
        "questions": 30,
        "overall_correct": 0.0,
        "numeric_accuracy": 0.0,
        "case_and_step": 0.0,
        "proposal_accuracy": 0.0,
        "unrequested_proposals": 0.0,
        "tool_choice": 0.0,
        "blocked_proposals": 0,
        "correct_refusals": 0.0,
        "false_refusals": 0.0,
        "grounded_answers": 0.0,
        "median_s": 0.0,
        "p95_s": 0.0
      }
    }
  ]
}
```
- Rates are percentages 0–100 with 1 decimal, or `null` if there were no questions of that kind. `blocked_proposals` is a count.
- `overall_correct`: every check on the question passed.
- `numeric_accuracy`: the expected values appear in the answer.
- `case_and_step`: the answer names the case and the next step.
- `proposal_accuracy`: propose questions where a proposal with the right SKU and action was written.
- `unrequested_proposals`: proposals made when none was asked for. Lower is better.
- `blocked_proposals`: proposals that `propose_action` refused, either because the action did not match the counts or because the reason cited numbers not in the tool results.
- `false_refusals` is lower-is-better.
- Only compare runs with the same `question_set`.

## 2. `data/audit_replay.json`: the recorded answers of the latest audit eval
```json
{ "recorded_at": "ISO-8601",
  "answers": [ { "id": "w01", "type": "gaps|why|position|po|wos|propose|refusal|multi", "question": "string",
                 "response": { "...": "POST /api/mirage/ask body, below" }, "correct": true } ] }
```

## 3. `data/audit_audit.json`: one full audit, recorded through the API
Written by `scripts/record_audit.py`. `steps[]` are in order:
1. `ask`: the question and the full answer.
2. `queue`: the waiting proposals.
3. `approve_without_key`: rejected with status 401.
4. `approve`: status 200.
5. `decide_again`: status 409, because a decision is final.
6. `audit_log`: the log rows for that proposal.
```json
{ "recorded_at": "ISO-8601",
  "steps": [ { "step": "ask", "request": { "method": "POST", "path": "/api/mirage/ask", "body": {} },
               "status_code": 200, "response": {} } ] }
```
`request.headers["X-API-Key"]` is always the placeholder `"<ADMIN_API_KEY>"`. `status_code` is present on the decision steps.

## 4. `data/audit_proposals.json`: the review queue and audit log (fixture for the approval screen)
```json
{ "generated_at": "ISO-8601",
  "proposals": [ { "id": 1, "created_at": "ISO-8601", "club": "Everett", "store_id": "101", "sku_id": "184220",
                   "sku_name": "Paper Towels 12pk", "action": "recount|pull_to_floor|reorder", "reason": "string",
                   "status": "waiting for approval|approved|rejected", "decided_by": "string|null", "decided_at": "ISO-8601|null" } ],
  "audit_log": [ { "id": 1, "proposal_id": 1, "decision": "approved|rejected", "decided_by": "string",
                   "decided_at": "ISO-8601", "note": "string|null" } ],
  "source": "string", "second_answer": { "question": "string", "status": "string", "answer": "string",
                                         "tool_calls": "[...]? as in /api/mirage/ask", "proposal_id": "integer?" } }
```
- `second_answer` comes from the second recorded `POST /api/mirage/ask` call. It has the same fields as that response:
  - `tool_calls[]`: `{tool, inputs, rows_returned, elapsed_s, output}`, as in `/api/mirage/ask`.
  - `as_of`: as in that response.
  - `proposal_id`: the id of the proposal that answer wrote, matching a row in `proposals[]`. It is `null` if the answer made no proposal.
- The static site cannot approve anything. Approval goes through the API below. In this file, the recorded decider is `"Demo reviewer"`.
- `status` `"waiting for approval"` is the only state that shows Approve and Reject buttons.

## How docs/audit.html shows them (docs/assets/js/audit.js, `renderMirage*`)
- `audit_eval.json` → "Eval scores": headline `overall_correct` on `questions`, the latest run's summary keys as given (rates + "%", `blocked_proposals` as a count, times via the duration formatter), history and a change column computed only against an earlier run of the same model with the same `question_set`, and never across `scoring_changed`.
- `audit_replay.json` → "Recorded answers": question, answer, and per answer every tool-output row that has `case`/`case_label` and `next_step` (Recount / Pull to floor / Reorder, plus `also` and `also_reason`); `output.summary` and `output.totals` are shown as labelled values exactly as given. Under any summary with case counts (`book_wrong_sku_count`, `backroom_sku_count`, `truly_out_sku_count`) the note "Categories can overlap" is shown, because one SKU can have a wrong record and backroom stock at once, so the counts may sum past `gap_sku_count`; `response.proposals[]` as chips; tool calls, rows and `transfers` behind toggles.
- `audit_proposals.json` → "Review queue" (read-only): proposals with `status` "waiting for approval", every proposal with its status, the `audit_log` rows, `second_answer` and `source`. When `second_answer.tool_calls` is present it is rendered with the same answer card as the replay (case and next step, tool calls and rows behind toggles) and `proposal_id` as a proposal chip; without them only the question and answer are shown.
- `audit_audit.json` → "Audit log": each step in order with method and path, `status_code`, `detail`, and the proposal and audit rows it returned. Header values are never shown, only the header name.
- Any `decided_by` equal to "Demo reviewer" carries a visible "Demo" label.
- The page has no write call and no key. Approve and reject go through the API (below) with `X-API-Key`.
- A missing file shows "Not run yet".

## API (agent/routes.py)
- `POST /api/mirage/ask` with `{question}` returns `{status, answer, tool_calls[], as_of, elapsed_s, model, prompt_version, checker}` plus `proposals[]`. Each proposal is `{proposal_id, club, sku_id, sku_name, action, status}`.
- `GET /api/mirage/proposals?status=waiting for approval` returns `{proposals: [...]}`, with rows as in 7d.
- `GET /api/mirage/audit-log?proposal_id=1` returns `{audit_log: [...]}`.
- `POST /api/proposals/{id}/approve` and `POST /api/proposals/{id}/reject`:
  - Header `X-API-Key: <ADMIN_API_KEY>`. Body `{decided_by: "name", note?: "string"}`.
  - Returns 200 `{proposal, audit: [...]}`.
  - Errors: 401 for a missing or wrong key; 422 for an empty `decided_by`; 404 for an unknown id; 409 if the proposal was already decided; 503 if `ADMIN_API_KEY` is not set on the server.
- No endpoint or tool changes a Mirage count. Approval records the decision only.
