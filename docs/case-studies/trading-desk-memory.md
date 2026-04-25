# Case Study: TradeMind / ChartHustle Memory Stack (Dogfooding Remembra)

**Goal:** Make a trading system that *remembers* (setups, rules, mistakes, regimes) without bloating prompts, and can justify decisions after the fact.

This case study is based on how a live trading desk workflow naturally produces “event-boundary” data:

- `setup_detected`
- `trade_opened`
- `trade_closed`
- `veto` / “no trade”
- `regime_shift`
- end-of-day review

Remembra fits best when you treat each event as an append-only memory with **strong metadata**, then use recall + filters to fetch only what matters for the next decision.

---

## The Challenge

Trading is a high-frequency decision environment where:

- *Short-term state* changes constantly (open position, current session plan)
- *Long-term lessons* matter (what patterns win/lose in a given regime)
- *Rules are non-negotiable* (max daily loss, max consecutive losses)
- Post-trade review needs **provenance** (why we took or skipped it)

A durable memory layer has to support:

1. Fast “similar setups” recall pre-trade
2. Durable post-trade journaling + learning loops
3. Filter-only “show me last 20 of X” retrieval
4. Shared context across agents (research, execution, risk, journal)
5. Security: scoped spaces/projects; minimal cross-contamination

---

## The Pattern: Dual-Store Memory

For a production trading desk, a practical pattern is:

- **Structured journal DB (SQLite/Postgres)** for deterministic analytics (P&L, win-rate, distribution, rule violations)
- **Remembra** for semantic/graph/temporal memory (setups, reasons, regime context, lessons, constraints, provenance)

The structured journal answers: “what happened?”

Remembra answers: “what’s *similar*, what did we *learn*, and what should we do *next*?”

---

## Recommended Trade Memory Schema (Metadata)

Use a small set of consistent keys so recall can be tight and reliable:

```json
{
  "domain": "trading",
  "memory_type": "trade_episode",
  "symbol": "NQ",
  "strategy": "orb",
  "direction": "long",
  "session": "RTH",
  "regime": "high_vol",
  "setup_name": "ORB_breakout",
  "setup_score": 82,
  "rvol_zone": "high",
  "entry": 19850.25,
  "stop": 19820.25,
  "targets": [19880.25, 19910.25],
  "decision": "taken",
  "outcome": "win",
  "pnl_pts": 42.0,
  "rule_violation": false,
  "event_boundary": "trade_closed",
  "trade_date": "2026-04-25",
  "trace_id": "trc_...",
  "parent_trace_id": "trc_..."
}
```

Notes:

- Use `event_boundary` to make “decision provenance” replayable.
- Use `trace_id`/`parent_trace_id` (or a similar linkage scheme) to tie:
  `setup_detected → trade_opened → trade_closed → post_mortem`.
- Keep numeric fields numeric; keep enums low-cardinality.

---

## Pre-Trade Recall: “Show me similar setups”

Pre-trade, run a semantic query + strict filters (symbol/strategy/regime):

```python
from remembra import Memory

memory = Memory(user_id="desk", project="trademind", api_key="...", base_url="http://localhost:8787")

result = memory.recall(
    "ORB breakout after tight overnight range — what usually happens?",
    filters={"domain": "trading", "symbol": "NQ", "strategy": "orb"},
    limit=8,
)
print(result.context)
```

This is where Remembra’s graph + temporal logic helps: it can surface *who/what/when* patterns rather than only nearest-neighbor snippets.

---

## Post-Trade Memory: Store outcome + lessons

Immediately after close, store:

1) the outcome (facts + metrics)
2) the reason (what we saw)
3) the lesson (what to repeat/avoid)

```typescript
import { Remembra } from "remembra";

const memory = new Remembra({ url: "http://localhost:8787", apiKey: "...", userId: "desk", project: "trademind" });

await memory.store("ORB long worked because VWAP held and breadth stayed positive; scaled at TP1.", {
  metadata: {
    domain: "trading",
    memory_type: "trade_episode",
    symbol: "NQ",
    strategy: "orb",
    event_boundary: "trade_closed",
    outcome: "win",
    pnl_pts: 42.0,
    rule_violation: false,
  },
});
```

---

## Filter-Only Recall: “Last N episodes for a pattern”

Use filter-only recall to grab the last N matching memories (no semantic query needed):

- `filters={"domain":"trading","memory_type":"trade_episode","strategy":"orb"}`
- `limit=25`

This is useful for:

- rolling “pattern memory” used in confidence scoring
- rapid audits (“show me all rule violations this week”)
- regime shifts (“show me last 10 high-vol sessions”)

---

## Risk-Rule Recall (Non-Negotiables)

Store risk rules as first-class memories:

- `memory_type: risk_rule`
- `scope: desk` / `account` / `strategy`

Then require a “risk recall” tool call at session start.

---

## What We’d Build Next (High-Leverage)

1. **Decision provenance as a first-class pattern**: trace-linked event memories that can be replayed and audited.
2. **Setup library**: a canonical “setup card” per strategy + regime + invalidation rules.
3. **Learning loop**: post-trade feedback that supersedes outdated beliefs (e.g., “ORB under 80pt range stopped working in high-vol weeks”).
4. **Regime memory**: store regime shift events and link them to performance deltas.

