"""CPU Scheduling deterministic simulator and verifier."""

from typing import Dict, Any, Tuple, List
from src.verification.base import BaseVerifier
from src.mechanism.schema import MechanismContract, VerificationTrace, VerificationStatus


class CPUSchedulerVerifier(BaseVerifier):
    """Simulates CPU scheduling algorithms (FCFS, SJF, Round Robin) and context switch counts."""

    @property
    def mechanism_name(self) -> str:
        return "cpu_scheduling"

    def execute(self, verification_input: Dict[str, Any]) -> VerificationTrace:
        algo = verification_input.get("algorithm", "ROUND_ROBIN").upper()
        quantum = verification_input.get("quantum", 2)
        processes = verification_input.get("processes", [])  # list of {"id": "P1", "arrival": 0, "burst": 4}

        if not processes:
            # Default workload for context switch testing
            processes = [
                {"id": "P1", "arrival": 0, "burst": 5},
                {"id": "P2", "arrival": 0, "burst": 5},
                {"id": "P3", "arrival": 0, "burst": 5}
            ]

        if algo == "ROUND_ROBIN":
            trace_events, context_switches, avg_turnaround, avg_wait = self._run_round_robin(processes, quantum)
        elif algo == "FCFS":
            trace_events, context_switches, avg_turnaround, avg_wait = self._run_fcfs(processes)
        elif algo == "SJF":
            trace_events, context_switches, avg_turnaround, avg_wait = self._run_sjf(processes)
        else:
            trace_events, context_switches, avg_turnaround, avg_wait = self._run_round_robin(processes, quantum)

        observed = {
            "algorithm": algo,
            "quantum": quantum,
            "context_switches": context_switches,
            "avg_turnaround_time": avg_turnaround,
            "avg_wait_time": avg_wait
        }

        return VerificationTrace(
            verifier_name=self.mechanism_name,
            initial_state={"quantum": quantum, "process_count": len(processes)},
            events_executed=trace_events,
            final_state={"completed": True},
            observed_values=observed,
            invariants_checked={"execution_completed": True},
            raw_logs=[f"Executed {algo} with {len(processes)} processes. Context switches: {context_switches}"]
        )

    def _run_round_robin(self, processes: List[Dict[str, Any]], quantum: int) -> Tuple[List[Dict[str, Any]], int, float, float]:
        queue = [dict(p, remaining=p["burst"]) for p in sorted(processes, key=lambda x: x["arrival"])]
        time = 0
        context_switches = 0
        events = []
        last_pid = None
        turnaround = {}
        wait = {}

        ready_queue = list(queue)

        while ready_queue:
            curr = ready_queue.pop(0)
            pid = curr["id"]

            if last_pid is not None and last_pid != pid:
                context_switches += 1

            last_pid = pid
            exec_time = min(curr["remaining"], quantum)
            time += exec_time
            curr["remaining"] -= exec_time

            events.append({"time": time, "pid": pid, "exec_time": exec_time, "remaining": curr["remaining"]})

            if curr["remaining"] > 0:
                ready_queue.append(curr)
            else:
                turnaround[pid] = time - curr["arrival"]
                wait[pid] = turnaround[pid] - curr["burst"]

        avg_tat = sum(turnaround.values()) / len(processes) if processes else 0.0
        avg_wt = sum(wait.values()) / len(processes) if processes else 0.0
        return events, context_switches, avg_tat, avg_wt

    def _run_fcfs(self, processes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, float, float]:
        time = 0
        context_switches = 0
        events = []
        turnaround = {}
        wait = {}

        for p in sorted(processes, key=lambda x: x["arrival"]):
            if time < p["arrival"]:
                time = p["arrival"]
            if events:
                context_switches += 1
            time += p["burst"]
            events.append({"time": time, "pid": p["id"], "burst": p["burst"]})
            turnaround[p["id"]] = time - p["arrival"]
            wait[p["id"]] = turnaround[p["id"]] - p["burst"]

        avg_tat = sum(turnaround.values()) / len(processes) if processes else 0.0
        avg_wt = sum(wait.values()) / len(processes) if processes else 0.0
        return events, context_switches, avg_tat, avg_wt

    def _run_sjf(self, processes: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, float, float]:
        # Non-preemptive SJF
        unprocessed = [dict(p) for p in processes]
        time = 0
        context_switches = 0
        events = []
        turnaround = {}
        wait = {}

        while unprocessed:
            available = [p for p in unprocessed if p["arrival"] <= time]
            if not available:
                time = min(p["arrival"] for p in unprocessed)
                available = [p for p in unprocessed if p["arrival"] <= time]

            shortest = min(available, key=lambda x: x["burst"])
            unprocessed.remove(shortest)

            if events:
                context_switches += 1

            time += shortest["burst"]
            events.append({"time": time, "pid": shortest["id"], "burst": shortest["burst"]})
            turnaround[shortest["id"]] = time - shortest["arrival"]
            wait[shortest["id"]] = turnaround[shortest["id"]] - shortest["burst"]

        avg_tat = sum(turnaround.values()) / len(processes) if processes else 0.0
        avg_wt = sum(wait.values()) / len(processes) if processes else 0.0
        return events, context_switches, avg_tat, avg_wt

    def verify(self, contract: MechanismContract) -> Tuple[VerificationStatus, str, Dict[str, Any]]:
        trace = self.execute(contract.verification_input)
        contract.verification_trace = trace

        predicted = contract.predicted_observation
        actual = trace.observed_values

        if "expected_context_switches" in predicted:
            exp_cs = predicted["expected_context_switches"]
            act_cs = actual["context_switches"]
            if exp_cs != act_cs:
                reason = f"Context switch count mismatch: expected {exp_cs}, observed {act_cs}."
                return VerificationStatus.FAIL, reason, actual

        if "expected_relation" in predicted:
            # Handles comparative/quantum change predictions
            rel = predicted["expected_relation"]  # e.g. "cs_q1 > cs_q2"
            q1 = contract.verification_input.get("quantum_1")
            q2 = contract.verification_input.get("quantum_2")
            if q1 and q2:
                inp1 = dict(contract.verification_input, quantum=q1)
                inp2 = dict(contract.verification_input, quantum=q2)
                t1 = self.execute(inp1)
                t2 = self.execute(inp2)
                cs1 = t1.observed_values["context_switches"]
                cs2 = t2.observed_values["context_switches"]
                
                if rel == "cs_q2 > cs_q1" and not (cs2 > cs1):
                    reason = f"Quantum reduction relationship failure: q={q2} produced {cs2} switches, q={q1} produced {cs1} switches."
                    return VerificationStatus.FAIL, reason, {"q1_switches": cs1, "q2_switches": cs2}
                elif rel == "cs_q2 < cs_q1" and not (cs2 < cs1):
                    reason = f"Quantum relation failure: expected cs(q2) < cs(q1), observed cs(q1)={cs1}, cs(q2)={cs2}."
                    return VerificationStatus.FAIL, reason, {"q1_switches": cs1, "q2_switches": cs2}

        return VerificationStatus.PASS, "CPU scheduling predictions verified.", actual
