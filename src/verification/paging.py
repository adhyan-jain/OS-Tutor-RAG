"""Paging & Page Replacement deterministic simulator and verifier."""

from typing import Dict, Any, Tuple, List
from src.verification.base import BaseVerifier
from src.mechanism.schema import MechanismContract, VerificationTrace, VerificationStatus


class PagingSimulatorVerifier(BaseVerifier):
    """Simulates page replacement algorithms (FIFO, LRU, Optimal) and page fault counts."""

    @property
    def mechanism_name(self) -> str:
        return "paging_replacement"

    def execute(self, verification_input: Dict[str, Any]) -> VerificationTrace:
        algo = verification_input.get("algorithm", "FIFO").upper()
        num_frames = verification_input.get("num_frames", 3)
        ref_string = verification_input.get("ref_string", [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5])

        if algo == "FIFO":
            faults, hits, evictions = self._run_fifo(ref_string, num_frames)
        elif algo == "LRU":
            faults, hits, evictions = self._run_lru(ref_string, num_frames)
        elif algo == "OPTIMAL":
            faults, hits, evictions = self._run_optimal(ref_string, num_frames)
        else:
            faults, hits, evictions = self._run_fifo(ref_string, num_frames)

        observed = {
            "algorithm": algo,
            "num_frames": num_frames,
            "reference_string": ref_string,
            "page_faults": faults,
            "hits": hits,
            "evicted_pages": evictions
        }

        return VerificationTrace(
            verifier_name=self.mechanism_name,
            initial_state={"frames": num_frames, "ref_length": len(ref_string)},
            events_executed=[{"page": p} for p in ref_string],
            final_state={"completed": True},
            observed_values=observed,
            invariants_checked={"page_faults_non_negative": faults >= 0},
            raw_logs=[f"Paging {algo} with {num_frames} frames. Faults: {faults}, Hits: {hits}"]
        )

    def _run_fifo(self, ref_string: List[int], num_frames: int) -> Tuple[int, int, List[int]]:
        frames = []
        faults = 0
        hits = 0
        evictions = []

        for page in ref_string:
            if page in frames:
                hits += 1
            else:
                faults += 1
                if len(frames) >= num_frames:
                    evicted = frames.pop(0)
                    evictions.append(evicted)
                frames.append(page)
        return faults, hits, evictions

    def _run_lru(self, ref_string: List[int], num_frames: int) -> Tuple[int, int, List[int]]:
        frames = []
        recent_use = {}
        faults = 0
        hits = 0
        evictions = []

        for idx, page in enumerate(ref_string):
            if page in frames:
                hits += 1
            else:
                faults += 1
                if len(frames) >= num_frames:
                    lru_page = min(frames, key=lambda p: recent_use[p])
                    frames.remove(lru_page)
                    evictions.append(lru_page)
                frames.append(page)
            recent_use[page] = idx
        return faults, hits, evictions

    def _run_optimal(self, ref_string: List[int], num_frames: int) -> Tuple[int, int, List[int]]:
        frames = []
        faults = 0
        hits = 0
        evictions = []

        for idx, page in enumerate(ref_string):
            if page in frames:
                hits += 1
            else:
                faults += 1
                if len(frames) >= num_frames:
                    future_refs = ref_string[idx + 1:]
                    furthest_page = None
                    furthest_dist = -1
                    for f in frames:
                        if f not in future_refs:
                            furthest_page = f
                            break
                        dist = future_refs.index(f)
                        if dist > furthest_dist:
                            furthest_dist = dist
                            furthest_page = f
                    frames.remove(furthest_page)
                    evictions.append(furthest_page)
                frames.append(page)
        return faults, hits, evictions

    def verify(self, contract: MechanismContract) -> Tuple[VerificationStatus, str, Dict[str, Any]]:
        trace = self.execute(contract.verification_input)
        contract.verification_trace = trace

        predicted = contract.predicted_observation
        actual = trace.observed_values

        if "expected_page_faults" in predicted:
            exp_pf = predicted["expected_page_faults"]
            act_pf = actual["page_faults"]
            if exp_pf != act_pf:
                reason = f"Page fault calculation error: predicted {exp_pf} faults, but {actual['algorithm']} simulator observed {act_pf} faults."
                return VerificationStatus.FAIL, reason, actual

        if "check_belady_anomaly" in predicted and predicted["check_belady_anomaly"]:
            # Belady anomaly test comparison between frame counts
            f1 = contract.verification_input.get("frames_1", 3)
            f2 = contract.verification_input.get("frames_2", 4)
            ref = contract.verification_input.get("ref_string", [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5])
            
            t1 = self.execute({"algorithm": "FIFO", "num_frames": f1, "ref_string": ref})
            t2 = self.execute({"algorithm": "FIFO", "num_frames": f2, "ref_string": ref})
            
            pf1 = t1.observed_values["page_faults"]
            pf2 = t2.observed_values["page_faults"]
            
            is_anomaly = pf2 > pf1
            if predicted.get("asserts_always_fewer_faults_with_more_frames", False) and is_anomaly:
                reason = f"Belady's Anomaly detected: increasing frames from {f1} to {f2} increased page faults from {pf1} to {pf2}. Statement claiming 'more frames always reduce page faults' fails."
                return VerificationStatus.FAIL, reason, {"pf_frames_3": pf1, "pf_frames_4": pf2}

        return VerificationStatus.PASS, "Paging predictions verified successfully.", actual
