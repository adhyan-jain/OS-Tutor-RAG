# Formal framework (corrected 2026-10-02)

> **Corrections to AGY's version.**
> (1) Its "semantic trace equivalence" T1 ≡_sem T2 ⇔ V(P,T1) ∧ V(P,T2) is not an equivalence relation over traces: it is not reflexive on invalid traces, and it relates traces only by co-membership in V(P). It is renamed **co-validity** below.
> (2) V(P) was never defined per policy, and the implementation silently used a *preemptive* unit-step semantics for "FCFS".
> (3) "Superficial reordering" was never distinguished from substantive difference.

## 1. Problems, traces, validity

A problem P fixes a transition system (S, s0, →_P) with terminal states F. A trace T is a finite sequence of observable actions. **V(P, T) = true** iff T labels a path s0 → … → s ∈ F.

**V(P) = {T : V(P, T)}**, after normalisation n(·):
- Scheduling: merge adjacent segments of the same process, and make gaps explicit as IDLE.
- Concurrency: the identity.

## 2. The policies used (code: `research/simulator/`)

**Scheduling** (actions are Gantt segments (p, start, end)).
- **FCFS, SJF and PRIORITY are non-preemptive.** At a dispatch instant t, the enabled actions are: run some ready p (arrival ≤ t) that minimises the key (arrival; burst; priority number) for its full burst. If nothing is ready, idle until the next arrival. **Nondeterminism = ties in the key.**
- **RR(q).** The state includes the FIFO ready queue. The head runs for min(q, remaining). Nondeterminism comes from two places:
  - the order of simultaneous arrivals;
  - whether a process preempted at t is re-queued before or after the processes arriving at exactly t.

  Both are standard textbook ambiguities.

**Concurrency** (actions are (thread, op, arg)). Per-thread program order. lock(m) is enabled iff m is free; mutexes are not re-entrant. unlock(m) requires ownership. wait(s) is enabled iff s > 0, and decrements s. signal(s) increments s. write(v) is always enabled. Deadlocked paths are not in V(P).

**Two independent implementations decide V(P, T):**
- the enumerators (successor relation, memoised counting and membership);
- the validators (`validators.py`), which check the rules directly against T.

`tests/research/test_semantics.py` requires them to agree.

## 3. Relations between traces

- **Identity:** T1 = T2 after normalisation.
- **Co-validity (AGY's "≡_sem", renamed):** V(P,T1) ∧ V(P,T2). This is a property of a pair, not an equivalence.
- **Mazurkiewicz equivalence (concurrency):** T1 ~ T2 iff one can be turned into the other by swapping adjacent *independent* actions. Two actions are independent iff they are in different threads and touch different objects. Equivalently, T1 and T2 agree on the per-object projections. Traces in one class are *superficial* reorderings.
- **Outcome equivalence:** equal waiting-time vectors (scheduling) or equal last writer per variable (concurrency).

**The benchmark requires that R2 is not superficially equivalent to R1.** For scheduling, the waiting-time vectors must differ. For concurrency, the Mazurkiewicz class must differ.

## 4. Benchmark objects

For each P:
- **R1:** the canonical trace (tie-break by listed order, arrivals before the re-queued process, lowest-index enabled thread).
- **R2:** a valid trace sampled uniformly from V(P) \ {R1}, substantively different from R1.
- **R3:** a third valid trace.
- **I, I2:** invalid traces. They have:
  - the same length and per-entity totals as R2;
  - every adjacent pair occurring in some valid trace;
  - a profile matched to R2's: first divergence, last divergence and edit distance to R1.

## 5. Quantities measured

- **Generation.** Acc_ref = [T̂ = R1], Acc_sem = V(P, T̂). The gap Acc_sem − Acc_ref ≥ 0 holds by construction (R1 ∈ V(P)), so it is a descriptive quantity, not a hypothesis.
- **Judging.** J(P, T, R) ∈ {VALID, INVALID}, where R is a reference or none.
  - **Anchoring index:** AI = P[J(P,R2,R2)=VALID] − P[J(P,R2,R1)=VALID].
  - **Reference-choice flip rate:** P[J(P,R2,R1) ≠ J(P,R2,R3)], compared against the re-run noise floor.
  - **Context controls:** J(P,R2,none), J(P,R2,irrelevant), and J(P,R2,R1 reworded).
