# Batch 20B: Local DeepSeek synthesis (experimental)

The public search and deterministic evidence display remain available without login.
Optional text generation uses DeepSeek-R1-Distill-Qwen-1.5B Q4_K_M via the
**localhost-only** llama.cpp `/v1/chat/completions` service. No paid/cloud model
requests are made. A separate administrator token is mandatory for starting and
polling a generation job. **Never commit or share the token.**

Because the CPU-only model can take over 45 seconds, synthesis is an in-memory,
single-active-job queue. The UI polls for completion. The dedicated BMS FastAPI
service still uses one worker. At most eight jobs can be started per process
hour; restart resets the rate limiter. Jobs and replies expire from memory.
No clinical claims, model accuracy, or Bangla fluency are established by this demo.

To get the private administrator token from the VPS terminal, use:

    sudo sh -c "sed -n 's/^BMS_AI_ACCESS_TOKEN=//p' /etc/banglamedscanner/llm.env"

Enter the token in the web UI's password field, select local AI synthesis,
then submit a supported Bangla medical question. The token stays in the current
browser page only; do not share or paste it into chat. Never enter identifiable
patient information in a public research demo.

The model can be slow, return malformed output, or make unverified claims. When
model output is invalid, the AI job fails closed; select non-AI evidence view to
see original PubMed source links and excerpts. A valid PMID is not proof that a
model-generated claim is scientifically correct.

Disable AI without affecting research search: remove or rename the dedicated
`/etc/banglamedscanner/llm.env` file and restart ONLY `banglamedscanner.service`.
Do not change Traefik, n8n, system Nginx, or Manufacturing ERP.

The 20 evaluation candidates remain held out; they are not gold annotations.
Manual evidence-claim review, model-groundedness metrics, and Bangla translation
assessment are future research milestones.
