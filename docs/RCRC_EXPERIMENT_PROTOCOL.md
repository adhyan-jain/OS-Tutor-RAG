# RCR Experimental Protocol & Reproducibility Guide

## Protocol Steps

1. **Space Construction**:
   Run `python -m research.ssr_pilot.core.valid_space` to build and verify exact valid spaces \(V(x)\) for all 24 pilot tasks.

2. **Oracle Invariance Audit**:
   Execute `python -m research.ssr_pilot.core.oracle` to verify that `evaluate_oracle(world, raw_text)` yields identical verdicts for all reference choices \(R \in V(x)\).

3. **Evaluation Protocol Execution**:
   Run the main RCR protocol on the existing 1,152 generations:
   ```bash
   PYTHONPATH=. python -m research.ssr_pilot.rcrc.protocol --regime FULL_REFERENCE_ENUMERATION
   ```

4. **Artifact Generation**:
   Summary JSON artifact is saved to:
   `research/ssr_pilot/results/rcrc/rcr_summary.json`
   Report is updated at:
   `research/ssr_pilot/reports/RCRC_REPORT.md`

5. **Test Suite Verification**:
   Execute complete unit and integration test suite:
   ```bash
   PYTHONPATH=. pytest tests/ssr_pilot/
   ```
