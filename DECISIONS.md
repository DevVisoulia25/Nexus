# Decision log

2026-11-07. Labels distinguish user constraints from provisional engineering choices. D013 sets the current priority; D001–D012 retain the history and requirements of the later translation phase.

| ID | Status | Decision and rationale | Revisit trigger |
|---|---|---|---|
| D001 | Agreed requirement | Final product is continuous live ASL-to-English with updating captions and measured delay. Offline/recorded camera work is intermediate. | Only explicit discussion with user can change objective |
| D002 | User confirmed | INR 0, local CPU machine, free notebooks for appropriate experiments; no automatic paid fallback. | User authorizes a concrete cost |
| D003 | User confirmed | No ASL reviewer currently available. Mark human semantic assessment unavailable; automatic metrics cannot certify fidelity. | Qualified reviewer becomes available |
| D004 | Provisional | How2Sign first, instructional domain; keep original and realigned annotation versions distinct. E000 shows large timing corrections. | Access/alignment cannot support valid pairs |
| D005 | Conditional | First smoke candidate: official Uni-Sign How2Sign pose-only weights. Verified artifact access and smaller visual input favor investigation. Code license, loading and provenance unresolved. | E001 incompatibility, unavailable terms, input fidelity or runtime failure |
| D006 | Provisional | WiCV I3D/Transformer fallback; RGB SSVP-SLT secondary option. Avoid several models/training recipes at once. | Uni-Sign route fails and fallback access is established |
| D007 | Agreed method | No post-hoc LLM polishing initially. Store raw outputs; run blank, shuffled and mismatched visual controls. | Controlled evidence supports faithful improvement |
| D008 | Agreed method | Preserve official splits for benchmark comparison but report overlap. Separate audited grouping/generalization analyses; no silent re-splitting to improve results. | Manifest audit reveals contamination |
| D009 | Provisional | Local UI/capture; evaluate CPU deployment before selecting remote inference. Training notebook is not hosting. | Measured throughput or reliability demands a different arrangement |
| D010 | Provisional | Prefix recomputation first for streaming, explicit buffers and revision ownership. Do not call the upstream whole-video demo streaming. | Stage 5 quality/latency measurements |
| D011 | Agreed method | Keep test content/results unopened until all decisions are frozen; metadata-only leakage audit is allowed separately. No learning preprocessing/vocabulary from dev/test. | Final evaluation freeze |
| D012 | Proposed protocol | Define numerical quality/latency targets after baseline profiling and agree before final testing. Hard requirements (causality, bounded memory, no false live claims) apply from the start. | Recorded user agreement/change with rationale |
| D013 | User-directed sequencing | Build limited-vocabulary individual-sign recognition first, prioritizing inference on the existing laptop; retain continuous live translation as a later separate research phase. Initial proposal is 10 signs, subject to data feasibility. This explicitly supersedes translation-only immediate scope in D001. | Recognition evaluation is complete and the user is ready to revisit translation feasibility |

Evidence and source links: [FEASIBILITY.md](FEASIBILITY.md). No model has been executed or selected as the production model.
