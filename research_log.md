# Research Log — Agentic Customer 360 (Proactive Intervention Desk)

 Prepathon 2026, Inter IIT Tech Meet 15.0 — Natural Language Processing PS
**Status:** Preliminary (mid-term). This log is a living document — every entry below records what I read, what I pulled from it, and the specific architectural decision it informed. Entries will be extended, and occasionally revised, as I build.

The organizing question for this log is not "what exists in this space" but "what did we change my design because of." Anything read but not load-bearing is noted as background rather than a decision driver.

Wanna share a huge thanks to scispace and notebookLMthese weere the tools which help me breakdown complex words heavy reserach aper in simple langusge and undersatnd their crux .  I also got to know everything comes at cost every thingf you gain amkes you lsoe something sometimes yuou lose performance for latency while other times you do vice versa.

First thing i got to know after studying PS is that using predifined frameworks which i currently know only one that is alnggraph will not help that much. The reason beging we need ambient agents while langgraph works on invoking with prompt. So we need to look for some other approach.

---

## 1. Memory & State Architecture

### 1.1 MemGPT — *Towards LLMs as Operating Systems* (Packer, Wooders, Lin, Fang, Patil, Stoica, Gonzalez; arXiv:2310.08560, 2023)
**What it argues:** LLM context windows are the equivalent of physical RAM — small and fast. MemGPT borrows the OS notion of virtual memory: an explicit "kernel" pages information between a small main context (what the model currently sees) and a much larger external context (a database/store), deciding what to promote or evict rather than letting old information silently fall off the edge of the window.

**What  I took from it:** The core distinction between *main context* (small, always in-scope) and *external context* (large, retrieved on demand) maps almost directly onto my working-memory vs. episodic-memory split. The important nuance we borrowed is that paging should be an **explicit, function-call-driven decision**, not an implicit side effect of the window filling up — which is why my Synthesis/Correlation Agent writes structured summaries to the state board rather than dumping raw event history into every downstream prompt.

**Decision informed:** The working-memory tier is capped and gets explicitly compressed/archived into episodic memory once a case closes (Section 4.1.1 of the architecture doc), instead of being allowed to grow unbounded per customer.

### 1.2 Generative Agents — *Interactive Simulacra of Human Behavior* (Park, O'Brien, Cai, Morris, Liang, Bernstein; UIST 2023, arXiv:2304.03442)
**What it argues:** Believable long-horizon agent behavior comes from three components — a memory stream of timestamped natural-language observations, a periodic *reflection* step that synthesizes higher-level conclusions from recent memories, and a planning step that consults both. Retrieval from the stream is scored on a weighted combination of recency, importance, and relevance rather than plain similarity search.

**What I took from it:** The recency/importance/relevance retrieval score is a much better fit for a customer-state store than pure cosine similarity, because a churn signal from three weeks ago matters differently than one from eighteen months ago even if they're semantically similar. The "reflection" concept is effectively my Life-Event Inference Agent — a periodic synthesis over the memory stream, written back into the stream, rather than a one-off classification.

**Decision informed:** Episodic memory entries are stored with recency, importance, and relevance metadata and retrieved with a weighted score (not top-k similarity alone); life-event inferences are themselves persisted as first-class memory entries other agents read, not recomputed each time — directly answering the PS's "standing goal" requirement in Section 3.

---

## 2. Multi-Agent Coordination & Topology

### 2.1 Anthropic — *Building Effective Agents* (Schluntz & Zhang, Anthropic Engineering, Dec 2024)
**What it argues:** Draws a hard line between *workflows* (LLMs and tools composed through predefined code paths — prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer) and *agents* (LLMs that dynamically direct their own tool use and stopping condition). Its central recommendation is to compose the simplest workflow pattern that solves each sub-problem rather than reaching for a single generalized "agent" abstraction everywhere.

**What I took from it:** This is the direct source of my decision to use *different* coordination patterns at different pipeline stages instead of one topology system-wide. Their "parallelization" pattern is my swarm stage; "orchestrator-workers" maps to Synthesis/Correlation Agent dispatching to Offer/Retention agents; "evaluator-optimizer" is exactly my critique-refiner pass before HITL.

**Decision informed:** Section 4.2 of the architecture explicitly justifies pattern choice per stage (swarm → handoff → debate-on-disagreement → round robin → critique-refiner) instead of defaulting to one topology, and cites this piece as the reason I treat topology as a per-stage engineering decision rather than a framework choice.

### 2.2 Multi-agent debate — Du et al., *Improving Factuality and Reasoning in Language Models through Multiagent Debate* (arXiv:2305.14325, ICML 2024) and Liang et al., *Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate* (arXiv:2305.19118, EMNLP 2024)
**What they argue:** Du et al. show that N independent LLM instances that answer, see each other's answers, and revise over a few rounds outperform single-agent self-reflection and majority voting on reasoning and factuality benchmarks — debate works because agents genuinely change their answer in light of another agent's reasoning, not just by more sampling. Liang et al. add a diagnosis: a single confident LLM suffers from "Degeneration-of-Thought" — it cannot self-reflect its way out of an answer it is already confident about — and address this with an adversarial two-debater-plus-judge format where debaters are explicitly instructed that agreement is not the goal.

**What I took from it:** This is the direct justification for my Retention-Agent vs. Upsell-Agent debate pattern in the deliberation layer. The "explicitly instructed to disagree" detail matters: if I let the Retention and Upsell agents converge toward each other's position by default, I lose the DoT-resistance the pattern is supposed to provide, so their system prompts explicitly frame them as advocates for a position, and the Synthesis/Arbitration Agent is a separate role rather than either debater self-judging.

**Decision informed:** Debate is scoped narrowly to the one place in the pipeline where two agents can have *genuinely* opposed incentives on the same evidence (retain vs. upsell) rather than used as a general-purpose quality mechanism — see the counterpoint below for why I didn't go further.

**Counterpoint I deliberately read:** Smit, Grinsztajn, Duckworth, Barrett, Pretorius, *Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs* (ICML 2024) benchmarks several debate protocols and finds they do not reliably beat cheaper prompting strategies like self-consistency once you control for compute. 


**Decision informed:** I do not use debate as my default disagreement-resolution mechanism — it is reserved for the one arbitration point where the disagreement itself is the useful signal (Retention vs. Upsell), while every other place two agents might conflict is resolved by simpler mechanisms (arbitration rule or critique-refiner), matching the PS's "handoff into synthesis, debate only when swarm agents disagree" guidance rather than debating everywhere for its own sake.

### 2.3 Reflexion — *Language Agents with Verbal Reinforcement Learning* (Shinn, Cassano, Gopinath, Narasimhan, Yao; NeurIPS 2023, arXiv:2303.11366)
**What it argues:** Instead of updating model weights, an agent that fails a task generates a natural-language self-critique of what went wrong, stores it in an episodic buffer, and conditions on it in the next attempt — improving HumanEval pass@1 from 67% to 91% with no fine-tuning.

**What I took from it:** This is the mechanism behind my Critique/Compliance-Refiner Agent's revision loop — the Action Composer doesn't just get a pass/fail from the critique agent, it gets a natural-language explanation of *why* a draft was rejected (cost infeasible, wrong tone, missing citation), stored against that customer's episodic memory so a similar future draft doesn't repeat the mistake.

**Decision informed:** Critique-Refiner rejections are logged as structured, retrievable reflections tied to the customer/case ID, not just a boolean gate — feeding both the audit trail (PS Section 6.5) and future Action Composer prompts.

---

## 3. Streaming Ingestion, Feature Freshness & Enterprise Precedent

### 3.1 Uber Michelangelo / Palette (Hermann & Del Balso, *Introducing Michelangelo: Uber's Machine Learning Platform*, Uber Engineering Blog, 2017; and *Palette Metastore Journey*, Uber Engineering Blog)
**What it argues:** Michelangelo's feature store solves the training/serving duality problem by generating features in a streaming fashion and double-writing to both a batch data lake (for training) and an online low-latency store (for serving), so the same feature definition produces consistent values in both places.

**What I took from it:** My Usage/Engagement and Transaction/Billing agents compute the same rolling-window aggregates (e.g., 30-day login frequency, spend baseline) that they would also need for any offline evaluation of the system, so I define these once as stream transforms and materialize to both the live per-customer state board and an append-only log used for the scoring harness.

**Decision informed:** Section 6.1's "transforms applied on the live stream" requirement is implemented as shared aggregate definitions rather than duplicated logic between the real-time agent and the evaluation harness — directly addressing the PS's warning against training/serving-style inconsistency.

### 3.2 DoorDash — *Supercharging DoorDash's Marketplace Decision-Making with Real-Time Knowledge* (Kumar, careersatdoordash.com, 2020) and *Lessons Learned Building DoorDash's Clusterless ML Feature Store* (Tagliamonte, careersatdoordash.com, 2026)
**What it argues:** DoorDash's real-time feature layer computes windowed aggregates (e.g., "order count in the last 20 minutes for store X") directly off a streaming engine (Flink) rather than at query time, so a spike is visible to a model within seconds rather than at the next batch refresh; the more recent piece details the operational cost of keeping a feature store correct at scale once LLM-driven consumers are added on top.

**What I took from it:** Confirms the naming convention and freshness expectation I use for my own windowed features (e.g., `txn_volume_p1h`, `login_freq_30d_trend`) and is the direct source for treating "spike within seconds" as a testable requirement rather than an aspiration — my Transaction/Billing Agent's anomaly score is defined as a streaming window aggregation, not a nightly rollup.

**Decision informed:** The PS's late/out-of-order event-handling checklist item (6.1) is treated as a first-class test scenario, not an edge case, because both Uber's and DoorDash's write-ups flag it as the actual operational failure mode in production feature pipelines.

### 3.3 Streaming RAG freshness (RisingWave Engineering, *Streaming RAG: Real-Time Retrieval for Agents That Can't Wait* and *Streaming for RAG: How to Keep Retrieval-Augmented Generation Fresh in Real Time*, 2026)
**What it argues:** A vector index refreshed on a schedule silently serves stale context between refreshes; the fix is driving re-embedding off change events (CDC) rather than a cron job, and giving the retrieving agent an explicit "freshness window" so it knows how stale its context might be, rather than reasoning confidently over an out-of-date policy document.

**What I took from it:** This is the justification for the PS's "vector DB / index kept live" checklist item being non-optional. It also gave us the concrete failure mode I use as a test scenario: a compliance/policy document changes (e.g., an eligibility rule), and an Offer/Eligibility Agent must not keep citing the old rule until a scheduled reindex catches up. 

**Decision informed:** Policy and CRM-note retrieval for the Offer/Eligibility and Retention/Action agents is event-driven (re-embed on write) rather than batch-refreshed, and every retrieval carries a freshness timestamp that is logged as part of the decision's citation trail (PS Section 6.5).

---

## 4. Guardrails, Governance & Non-Negotiable Safety Components

### 4.1 Constitutional AI — *Harmlessness from AI Feedback* (Bai et al., Anthropic, arXiv:2212.08073, 2022)
**What it argues:** Instead of relying only on human-labeled examples of harmful outputs, a model can be steered by a small set of written principles (a "constitution") that it uses to critique and revise its own outputs, later reinforced with AI-generated preference feedback. The important structural idea for us is not the training procedure itself (out of scope for an inference-time system) but the *pattern*: explicit, inspectable principles that a critique step checks outputs against, rather than an implicit sense of "be careful" baked into a single prompt.

**What I took from it:** My Critique/Compliance-Refiner Agent is explicitly given a written rubric (cost ceilings, tone requirements, compliance clauses) it checks proposed actions against — mirroring the constitution-as-explicit-rubric pattern rather than trusting an undifferentiated "be compliant" instruction. Crucially, the hard-stop guardrails (legal threats, fraud keywords) are kept **outside** this LLM-critiqued rubric entirely and implemented as deterministic keyword/classifier matches, precisely because the paper's method is a soft, learned harmlessness signal — not a hard safety boundary, and the PS explicitly requires the latter for catastrophic cases.

**Decision informed:** Two-tier safety design: deterministic, non-LLM guardrails for hard-stop conditions (Escalation/Guardrail Agent, Section 6.4 of the PS) sit structurally outside and upstream of the LLM-based critique-refiner rubric used for softer cost/tone/compliance checks — the constitution pattern informs the latter only.

---

## 5. Reading still in progress (to extend before end-term)
- Anthropic Cookbook, *Building Effective Agents — patterns/agents* (orchestrator-workers and evaluator-optimizer reference implementations) — to validate my handoff-scoping code structure.
- Zhuge et al., *GPTSwarm: Language Agents as Optimizable Graphs* (ICML 2024) — being read for whether the swarm stage should be represented as an explicit graph for later optimization, or kept as a flat parallel fan-out for v1 simplicity.
- Multi-agent memory consistency literature (e.g., Yu et al., *Multi-Agent Memory from a Computer Architecture Perspective*, 2026 preprint) — being read to firm up my answer to the PS's open question on memory bleed-through prevention across concurrent per-customer stores.

## 6. What this reading changed my mind about
My first instinct was a single generalist agent with one shared vector store — the PS explicitly calls this out as the pattern to avoid, and the debate/critique/reflection literature above is what convinced us it would also underperform empirically, not just architecturally: single-agent self-reflection is documented to underperform structured multi-agent critique (Liang et al.; Shinn et al.), and a single shared store without recency/importance weighting would misprioritize old signals (Park et al.). The counterpoint reading (Smit et al.) also stopped us from over-applying debate everywhere it was tempting to use it. Also teh dynamic re indexing of vectors based on freshembeddings in needed. We also need ashared feature store taht is here some state parameters for swarm agents tow ork on aso that the otehr judge agent can amke decision absed on combiend decisions by all. Also we need not ignore the previos data as throen light by MemGPT research paper.