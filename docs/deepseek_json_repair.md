# DeepSeek-R1 structured-response interoperability (Batch 26)

The first run failed at planning; Batch 26 then reached synthesis but failed Bangla/source validation.
The current patch keeps all source checks and retries synthesis once.

The original workflow initially failed on the query-planning step:
`AIWorkflowError: Model did not return a JSON object`. The first request was
limited to 190 generation tokens, used a system prompt, and requested an
unconstrained JSON object. This is consistent with a reasoning-model response
that uses its output budget before producing a final structured answer, but the
underlying raw model response was not logged and the cause is not proven.

This patch affects `ai_orchestration._chat` and `_model_synthesis`:

- Supplies all instructions in one user message (the DeepSeek-R1 guidance).
- Uses llama.cpp schema-constrained JSON decoding for each expected stage.
- Requests reduced reasoning and larger bounded generation budgets.
- Keeps the loopback-only model endpoint and existing citation checks.
- Refuses to publish the output when an object is missing/malformed.
- Does not interpret chain-of-thought as a medical explanation.

The 1.5B model is still a research prototype. Valid JSON, grounded excerpts and
allowed PMID references are not clinical validation or guarantees of Bangla
translation quality. The app's user-facing AI endpoints remain administrator-
restricted and the model retains its one-CPU, 3 GiB resource limit.

Before deployment, a private smoke test must complete one real model call for
planning, one for PICO candidates, and one for Bangla synthesis with a single
actual development-split abstract. These calls do not update the corpus or the
production app. If this smoke test fails, the script restores the development
source and does not restart any production service.

## Batch 28 — robust DeepSeek JSON completion

Due to intermittent unfinished `<think>` outputs from the DeepSeek-R1 chat
interface, each **real model stage** now tries (1) chat JSON-schema mode at
zero temperature and (2) the model's native llama.cpp `/completion` route with
schema-constrained grammar if the first result is not a complete JSON object.
The second route bypasses the chat-template reasoning prefix; it is still a
real inference request using the same localhost model, not a canned answer.
Only actual HTTP requests are counted in the trace, and each stage is bounded
at two attempts (Bangla synthesis can repeat its stage once after clinical-
content and language format checks, for at most four synthesis requests).
This changes neither the GGUF model nor any host-level service and does not
relax source or PMID validation. For production use, clinical review remains
mandatory. If the live model cannot produce valid structured content despite
the native grammar, deployment is refused and files rolled back.
