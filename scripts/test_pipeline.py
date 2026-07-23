"""End-to-end smoke test for RAGPipeline: ingest a small synthetic OS-course
corpus (as Documents, so chunking is actually exercised), then answer 3
sample queries and print the final generated answers.

Uses a synthetic corpus rather than real ingested files, since none exist
yet in data/raw/ (see DELAYED_TASKS.md).
"""

from __future__ import annotations

from src.config import PipelineConfig
from src.pipeline import RAGPipeline
from src.schemas import Document

_DOCUMENTS = [
    Document(
        doc_id="processes_and_threads",
        source_path="synthetic://processes_and_threads",
        text=(
            "A process is a program in execution, with its own address space, "
            "program counter, registers, and stack. A thread is a lightweight "
            "unit of execution within a process; threads in the same process "
            "share the same address space, which makes context switching "
            "between threads cheaper than between processes. Context switching "
            "saves the state of a running process or thread and loads the state "
            "of the next one, incurring overhead from cache and TLB flushes."
        ),
        metadata={"source_type": "text"},
    ),
    Document(
        doc_id="scheduling_and_deadlock",
        source_path="synthetic://scheduling_and_deadlock",
        text=(
            "The scheduler decides which process or thread runs next on the "
            "CPU, using policies such as round robin, priority, or multilevel "
            "feedback queues. Round robin scheduling gives each process a "
            "fixed time quantum and cycles through the ready queue, providing "
            "fairness for interactive systems. A deadlock occurs when a set of "
            "processes are each waiting for a resource held by another process "
            "in the set, so none can proceed. The four necessary conditions "
            "for deadlock are mutual exclusion, hold and wait, no preemption, "
            "and circular wait."
        ),
        metadata={"source_type": "text"},
    ),
    Document(
        doc_id="memory_and_sync",
        source_path="synthetic://memory_and_sync",
        text=(
            "Virtual memory lets a process use an address space larger than "
            "physical RAM by paging data to and from disk. A page table maps "
            "virtual addresses to physical frames; a TLB caches recent "
            "translations to speed up address translation. A semaphore is a "
            "synchronization primitive that uses an integer counter and "
            "atomic wait/signal operations to control access to shared "
            "resources. A mutex enforces mutual exclusion so that only one "
            "thread can enter a critical section at a time, preventing race "
            "conditions."
        ),
        metadata={"source_type": "text"},
    ),
]

_QUERIES = [
    "What is the difference between a process and a thread?",
    "What are the conditions required for a deadlock to occur?",
    "How does a mutex prevent race conditions?",
]


def main() -> None:
    config = PipelineConfig()
    print(f"Config: retrieval.technique={config.retrieval.technique!r}, "
          f"reranking.method={config.reranking.method!r}, "
          f"diversification.enabled={config.diversification.enabled}, "
          f"generation.backend={config.generation.backend!r} "
          f"({config.generation.model_name!r})\n")

    pipeline = RAGPipeline(config)

    print("Ingesting synthetic documents (chunk + index)...")
    pipeline.ingest(_DOCUMENTS)
    print("Ingest complete.\n")

    for query in _QUERIES:
        print(f"=== Query: {query!r} ===")
        answer = pipeline.answer(query)
        print(f"Answer: {answer}\n")


if __name__ == "__main__":
    main()
