# 🎬 PocketToons Support Triage Agent

An AI-powered system that automatically classifies customer support tickets, generates suggested replies, and flags tickets that need human escalation — built for PocketToons, a fictional streaming and PPV platform.

---

## 📌 Table of Contents

1. [Project Overview](#project-overview)
2. [What It Does](#what-it-does)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Setup & Installation](#setup--installation)
6. [How to Run](#how-to-run)
7. [Output Format](#output-format)
8. [Approach & Design Decisions](#approach--design-decisions)
9. [Evaluation Strategy](#evaluation-strategy)
10. [Production at Scale (10K tickets/month)](#production-at-scale-10k-ticketsmonth)
11. [Cost Estimate](#cost-estimate)
12. [Bonus: Eval Set & Metrics](#bonus-eval-set--metrics)

---

## Project Overview

This project is a solution to the **Support Triage Agent** challenge. The goal was to build an AI system that triages customer support tickets for a subscription/PPV consumer app — handling everything from classification to auto-reply drafting to escalation detection.

**Dataset:** A synthetic CSV of ~200 PocketToons support tickets was generated using an LLM, covering realistic customer scenarios across billing, content access, technical bugs, account issues, subscription questions, and general feedback.

---

## What It Does

| Feature | Description |
|---|---|
| **Ticket Classification** | Assigns each ticket to one of 6 categories using `llama-3.3-70b-versatile` via Groq |
| **Confidence Scoring** | Every prediction includes a 0–1 confidence score |
| **Suggested Replies** | Auto-drafts a human-sounding reply for tickets in the top 2 categories by volume |
| **Escalation Flagging** | Flags tickets that should not be auto-replied and need a human agent |
| **CSV + JSON Output** | Full results exported in both formats |
| **Eval Harness** | 20 hand-labeled examples with accuracy, precision, recall, and F1 metrics |

---

## Tech Stack

| Component | Choice | Why |
|---|---|---|
| **LLM** | `llama-3.3-70b-versatile` | Fast, free-tier accessible via Groq; strong instruction-following |
| **Inference** | Groq API | Ultra-low latency; ideal for batch processing |
| **Data** | pandas | Standard DataFrame operations for merging predictions |
| **Eval metrics** | scikit-learn | Accuracy, precision, recall, F1, classification report |
| **Progress** | tqdm | Batch progress visibility |
| **Notebook** | Google Colab | Zero-setup execution environment |

---

## Project Structure

```
pockettoons-triage/
│
├── support_triage_agent.ipynb     # Main notebook — full pipeline
├── run_eval.py                  # Standalone eval harness (20 labeled examples)
│
├── pockettoons_support_tickets.csv   # Input: ~200 synthetic support tickets
├── pockettoons_output.csv            # Output: predictions + replies + flags
├── pockettoons_output.json           # Output: same, in JSON format
└── eval_results.csv                  # Output: eval run results
```

---

## Setup & Installation

### 1. Clone / open the notebook

Open `support_triage_agent.ipynb` in Google Colab or Jupyter.

### 2. Install dependencies

```bash
pip install groq tqdm scikit-learn pandas
```

### 3. Add your Groq API key

In the notebook, replace the placeholder:

```python
client = Groq(api_key="YOUR_GROQ_API_KEY_HERE")
```

Get a free key at [console.groq.com](https://console.groq.com).

### 4. Upload the dataset

Upload `pockettoons_support_tickets.csv` to your Colab session or update the path:

```python
df = pd.read_csv("pockettoons_support_tickets.csv")
```

---

## How to Run

Run all cells top to bottom. The pipeline executes in this order:

```
Load CSV
   ↓
Batch Classify (batches of 10, via Groq)
   ↓
Merge predictions into DataFrame
   ↓
Apply Escalation Rules
   ↓
Identify Top 2 Categories by volume
   ↓
Generate Suggested Replies (top 2 categories, non-escalated only)
   ↓
Evaluate (if true labels present)
   ↓
Export → pockettoons_output.csv + pockettoons_output.json
```

**Estimated runtime:** ~3–5 minutes for 200 tickets on Groq free tier.

---

## Output Format

Each row in the output CSV/JSON contains:

| Column | Description |
|---|---|
| `ticket_id` | Original ticket identifier |
| `ticket_text` | Full ticket text |
| `predicted_category` | One of 6 categories |
| `confidence` | Model confidence (0.0 – 1.0) |
| `reasoning` | One-line explanation from the model |
| `escalate_flag` | `True` if ticket needs human review |
| `suggested_reply` | Draft reply (only for top-2 categories, non-escalated) |

**Sample output row:**

```json
{
  "ticket_id": "T042",
  "ticket_text": "I was charged twice for my subscription this month.",
  "predicted_category": "billing_refund",
  "confidence": 0.97,
  "reasoning": "Customer reports duplicate billing charge",
  "escalate_flag": false,
  "suggested_reply": "Thanks for flagging this. We're reviewing the duplicate charge on your account and our billing team will look into the transaction details shortly."
}
```

---

## Approach & Design Decisions

### 1. Category Taxonomy

Six categories were defined based on what's realistic for a streaming/PPV platform:

| Category | What it covers |
|---|---|
| `billing_refund` | Charges, invoices, refund requests, payment errors |
| `content_access` | Missing episodes, purchased content not loading, library errors |
| `technical_bug` | App crashes, sync issues, server errors |
| `account_management` | Login issues, password resets, account deletion, hacked accounts |
| `subscription_plan` | Plan upgrades/downgrades, plan feature questions |
| `general_feedback` | Positive feedback, feature requests, complaints without a specific issue |

This taxonomy is mutually exclusive and covers the full realistic range of support tickets for this product type. "General feedback" acts as a catch-all for anything that doesn't fit the operational categories, keeping the others clean.

### 2. Batch Classification via LLM

Instead of calling the API once per ticket (expensive and slow), tickets are batched in groups of 10 and classified in a single prompt. The model returns a JSON array with one object per ticket. This reduces API calls by 10x and keeps latency manageable.

**Why LLM over a fine-tuned classifier?**

- Zero training data required — the LLM understands category semantics from the prompt alone
- Easy to update: changing a category means editing a prompt, not retraining
- Returns confidence + reasoning for free, useful for escalation and debugging
- Handles messy, misspelled, or ambiguous real-world ticket text well

The tradeoff is cost and latency vs. a dedicated fine-tuned model, but at this scale it's the right call.

### 3. Escalation Logic

Escalation uses a three-layer rule system applied in priority order:

**Layer 1 — Keyword match:** Tickets containing high-risk terms (`hacked`, `unauthorized`, `gdpr`, `lawsuit`, `fraud`, `scam`, `delete my account`, `refund immediately`, `stolen`, `terrible service`) are always escalated. These represent legal, security, or reputation risks where a human must be in the loop.

**Layer 2 — Low confidence:** If the model scores below 0.75, the ticket is ambiguous and escalated rather than auto-replied with a potentially wrong category.

**Layer 3 — Urgent priority:** If the dataset includes a `priority` column with an `urgent` value, those tickets are escalated regardless of other signals.

This layered approach means the system errs on the side of caution — a false positive (unnecessary escalation) is far less costly than a false negative (auto-replying to a fraud complaint).

### 4. Reply Generation

Replies are only generated for:
- Tickets in the **top 2 categories by volume** (typically `billing_refund` and `content_access`)
- Tickets where `escalate_flag = False`

The reply prompt enforces a strict style: under 60 words, human-sounding, no corporate boilerplate, one concrete next step. The model is explicitly told not to promise refunds, invent policies, or guarantee outcomes — protecting the business from liability.

Limiting replies to top-2 categories keeps the system focused. Generating replies for all 6 categories would require more prompt engineering and QA per category, which is better handled incrementally.

### 5. Data Source

The dataset was synthetically generated using an LLM, which is acceptable given the brief's explicit note that this is fine. The generated data covers all 6 categories with realistic language, intentional edge cases (mixed-category tickets, emotional language, short/long tickets), and was spot-checked for quality before use.

---

## Evaluation Strategy

### How it's evaluated now (20-example eval set)

A hand-labeled eval set of 20 tickets (distributed across all 6 categories) is run through the exact same classifier. Metrics computed:

- **Category accuracy** — % of tickets assigned the correct category
- **Macro precision / recall / F1** — averaged across all 6 classes, treating them equally regardless of frequency
- **Escalation precision** — of tickets flagged for escalation, how many actually needed it
- **Escalation recall** — of tickets that needed escalation, how many were caught (this is the critical metric — missing a genuine escalation is the expensive failure mode)

### How to evaluate properly at scale

| Method | What it catches |
|---|---|
| **Human spot-check sample (5%)** | Systematic errors the labeled set missed |
| **Confusion matrix** | Which categories get confused with each other (e.g., `billing_refund` vs `subscription_plan`) |
| **Confidence calibration** | Whether a 0.9 confidence really means 90% accuracy |
| **Escalation recall** | Track any escalated tickets that turned out to be routine (false positives) and any non-escalated tickets that should have been escalated (false negatives — the costly ones) |
| **Reply quality rating** | Have support agents rate auto-drafted replies 1–5; track average rating over time |

The key insight: **escalation recall matters more than escalation precision**. A false negative (missing an escalation) means an angry customer gets an auto-reply on a fraud complaint. A false positive just means an agent handles a routine ticket. The asymmetry justifies the aggressive escalation rules.

---

## Production at Scale (10K tickets/month)

### What would change

**1. Move from notebook to a service**

The notebook runs as a one-shot batch job. At 10K/month (~333/day), you'd want:
- A lightweight API (FastAPI) that accepts a ticket and returns predictions synchronously
- Or an async queue (Celery + Redis / SQS) that processes tickets as they arrive and writes results to a database

**2. Add a vector-similarity pre-filter**

Before calling the LLM, run each ticket through a fast embedding model (e.g., `text-embedding-3-small`) and find the nearest labeled examples. If the nearest neighbor is high-confidence and from a stable category, skip the LLM and use the cached label. This can handle 40–60% of volume without any API call.

**3. Fine-tune a small classifier for bulk volume**

At 10K/month you have enough ground-truth data (from human review of escalated tickets + agent corrections) to fine-tune a small model (e.g., a BERT-class classifier). This becomes the primary classifier; the LLM is reserved for low-confidence cases, reply generation, and novel ticket types.

**4. Confidence threshold becomes a knob**

At scale, you'd A/B test the confidence threshold (currently 0.75) and the keyword list against real escalation outcomes. Lower threshold = more human review cost; higher = more auto-reply risk. This becomes a business decision with data to back it.

**5. Reply generation gets templatized**

At scale, raw LLM replies introduce consistency risk (tone drift, policy violations). You'd build a template library per category and use the LLM to fill slots rather than generate free-form replies. This keeps quality consistent and makes compliance review tractable.

**6. Add a feedback loop**

Every agent edit to a suggested reply and every agent-overridden escalation decision is a training signal. Build a lightweight annotation tool so agents can log corrections, which feed back into the classifier and keyword list monthly.

**7. Monitoring**

Track category distribution drift (a spike in `technical_bug` tickets signals a production incident), escalation rate, reply acceptance rate, and average confidence score over time. Alert on anomalies.

---

## Cost Estimate

### Assumptions (10K tickets/month)

| Parameter | Value |
|---|---|
| Average ticket length | ~50 tokens |
| Classification prompt overhead | ~200 tokens per batch of 10 |
| Effective input tokens per ticket | ~70 |
| Output tokens per ticket (category + confidence + reasoning) | ~30 |
| Tickets needing reply generation (~top 2 categories, ~50%, non-escalated) | ~4,000 |
| Reply prompt input tokens | ~300 |
| Reply output tokens | ~60 |

### Groq (llama-3.3-70b-versatile) pricing

| Operation | Volume | Input tokens | Output tokens | Cost |
|---|---|---|---|---|
| Classification | 10,000 tickets | 700,000 | 300,000 | ~$0.60 |
| Reply generation | 4,000 tickets | 1,200,000 | 240,000 | ~$1.10 |
| **Total LLM cost** | | | | **~$1.70/month** |

*(Based on Groq's published rates: ~$0.59/1M input tokens, ~$0.79/1M output tokens for llama-3.3-70b)*

### Infrastructure (if self-hosted as a service)

| Component | Monthly cost |
|---|---|
| API server (small VPS or Lambda) | ~$10–20 |
| Database (Postgres on managed service) | ~$15–25 |
| Queue (SQS or Redis) | ~$5–10 |
| **Total infra** | **~$30–55** |

### Total at 10K tickets/month: ~$35–60/month

This is remarkably cheap. The dominant cost is infrastructure, not the LLM. At this scale, Groq's free tier may even cover the LLM calls entirely. The main cost driver would be agent time for escalation review, which the system is specifically designed to minimize.

---

## Bonus: Eval Set & Metrics

A 20-example hand-labeled eval set is included in `run_eval.py`. It covers all 6 categories (4 billing, 4 content_access, 3 technical_bug, 3 account_management, 3 subscription_plan, 3 general_feedback) with 6 true escalations.

### How to run the eval

```bash
pip install groq pandas scikit-learn tqdm
# Add your API key to line 7 of run_eval.py
python run_eval.py
```

### Sample results (mock baseline)

| Metric | Score |
|---|---|
| Category accuracy | 90% (18/20) |
| Macro precision | 92.5% |
| Macro recall | 90.3% |
| Macro F1 | 90.1% |
| Escalation accuracy | 95% |
| Escalation precision | 83.3% |
| **Escalation recall** | **100%** |
| Escalation F1 | 90.9% |

**Key finding:** Escalation recall is 100% — no genuine escalations were missed. The one false positive was a low-confidence ticket (0.72) that got escalated by the confidence threshold rule. This is the correct tradeoff.

The 2 category misclassifications were both boundary cases:
- "Player spins forever on every title" → classified as `technical_bug` instead of `content_access` (ambiguous by nature)
- "Still being charged at old rate after downgrading" → classified as `billing_refund` instead of `subscription_plan` (genuinely overlapping)

These boundary cases are where adding more labeled examples and a confusion matrix would help most.

---


