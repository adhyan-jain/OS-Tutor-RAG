"""Manual smoke test: builds dense/BM25/hybrid indexes over a small OS-course
chunk corpus and prints top-5 results per method for sample queries side by side.

Uses a synthetic in-memory corpus rather than real ingested/chunked documents,
since none exist yet (see DELAYED_TASKS.md) — swap in real Chunks from
scripts/test_chunking.py output once available.
"""

from __future__ import annotations

from src.config import RetrievalConfig
from src.retrieval.hybrid_rrf import HybridRRFRetriever
from src.schemas import Chunk

_CORPUS = [
    ("A process is a program in execution, with its own address space, "
     "program counter, registers, and stack."),
    ("A thread is a lightweight unit of execution within a process; threads "
     "in the same process share the same address space."),
    ("The scheduler decides which process or thread runs next on the CPU, "
     "using policies such as round robin, priority, or multilevel feedback queues."),
    ("Round robin scheduling gives each process a fixed time quantum and "
     "cycles through the ready queue, providing fairness for interactive systems."),
    ("A deadlock occurs when a set of processes are each waiting for a "
     "resource held by another process in the set, so none can proceed."),
    ("The four necessary conditions for deadlock are mutual exclusion, hold "
     "and wait, no preemption, and circular wait."),
    ("Virtual memory lets a process use an address space larger than "
     "physical RAM by paging data to and from disk."),
    ("A page table maps virtual addresses to physical frames; a TLB caches "
     "recent translations to speed up address translation."),
    ("A semaphore is a synchronization primitive that uses an integer "
     "counter and atomic wait/signal operations to control access to shared resources."),
    ("A mutex enforces mutual exclusion so that only one thread can enter a "
     "critical section at a time, preventing race conditions."),
    ("File systems organize data on disk using structures like inodes, "
     "directories, and free space bitmaps."),
    ("Context switching saves the state of a running process/thread and "
     "loads the state of the next one, incurring overhead from cache and TLB flushes."),
]

_QUERIES = [
    "What is the difference between a process and a thread?",
    "How does round robin scheduling work?",
    "What are the conditions required for a deadlock to occur?",
    "What is virtual memory used for?",
    "How does a mutex prevent race conditions?",
    "What happens during a context switch?",
    "What is a semaphore?",
    "How does a page table work?",
]


def build_corpus() -> list[Chunk]:
    return [
        Chunk(
            chunk_id=f"os_corpus__chunk{i}",
            doc_id="os_corpus",
            text=text,
            start_index=0,
            end_index=len(text),
            metadata={"source_type": "text"},
        )
        for i, text in enumerate(_CORPUS)
    ]


def main() -> None:
    config = RetrievalConfig(top_k=5)
    chunks = build_corpus()

    print("Building indexes (dense embeddings + BM25)...")
    hybrid = HybridRRFRetriever(config)
    hybrid.build_index(chunks)
    dense, bm25 = hybrid.dense, hybrid.bm25

    index_dir = config.index_dir
    hybrid.save_index(index_dir)
    print(f"Indexes saved to {index_dir}\n")

    for query in _QUERIES:
        print(f"=== Query: {query!r} ===")
        dense_results = dense.retrieve(query)
        bm25_results = bm25.retrieve(query)
        hybrid_results = hybrid.retrieve(query)

        for label, results in (("DENSE", dense_results), ("BM25", bm25_results), ("HYBRID_RRF", hybrid_results)):
            print(f"  [{label}]")
            for r in results:
                print(f"    {r.rank}. ({r.score:.4f}) {r.chunk.text[:80]!r}")
        print()


if __name__ == "__main__":
    main()
