"""Chunk paginated documents (PDFs) semantically, within page boundaries.

The PDFs in this corpus are textbook pages: continuous prose broken by
headers, tips and figure captions, averaging ~1900 characters per page. Two
properties follow from that shape.

Chunks should not straddle pages. Chunking the concatenated document text
lets a chunk begin mid-topic on one page and end mid-topic on the next,
splicing a figure caption onto unrelated prose. Grouping within a page keeps
each chunk to one continuous passage.

The page is the natural parent. A semantic child is precise enough to match
against but often too narrow to answer from, while the page it came from is
close to the size a reader would consult -- so children carry their page as
``parent_text`` for the generation stage to expand into (see
src.context_expansion).
"""

from __future__ import annotations

from src.chunking.semantic import _group_by_similarity_shift, _split_sentences
from src.config import ChunkingConfig
from src.embedding_cache import get_embedding_model
from src.schemas import Chunk, Document


def page_aware_chunk(document: Document, config: ChunkingConfig) -> list[Chunk]:
    """Split a paginated Document into semantic chunks that respect page bounds.

    Falls back to treating the whole document as one page when the extractor
    produced no ``pages`` metadata, so this stays safe for any Document.

    Args:
        document: The source Document, ideally with ``metadata["pages"]`` as
            produced by src.ingestion.extract_pdf.
        config: Chunking parameters (chunk_size cap, similarity threshold,
            embedding model).

    Returns:
        Chunks in page order, each carrying its page's full text as
        ``parent_text`` and its page number in metadata.
    """
    pages = document.metadata.get("pages")
    if not pages:
        pages = [{"page_number": 1, "text": document.text}]

    model = get_embedding_model(config.semantic_embedding_model_name)
    source_type = document.metadata.get("source_type")

    chunks: list[Chunk] = []
    cursor = 0

    for page in pages:
        page_text = (page.get("text") or "").strip()
        if not page_text:
            continue

        page_number = page.get("page_number")
        parent_id = f"{document.doc_id}__page{page_number}"

        sentences = _split_sentences(page_text)
        if len(sentences) <= 1:
            groups = [sentences or [page_text]]
        else:
            embeddings = model.encode(sentences)
            groups = _group_by_similarity_shift(
                sentences, embeddings, config.semantic_similarity_threshold, config.chunk_size
            )

        for group in groups:
            text = " ".join(group).strip()
            if not text:
                continue
            chunks.append(
                Chunk(
                    chunk_id=f"{document.doc_id}__chunk{len(chunks)}",
                    doc_id=document.doc_id,
                    text=text,
                    start_index=cursor,
                    end_index=cursor + len(text),
                    metadata={
                        "source_type": source_type,
                        "strategy": "page_aware",
                        "page_number": page_number,
                        "parent_id": parent_id,
                        "parent_text": page_text,
                    },
                )
            )
            cursor += len(text) + 1

    return chunks


# Public interface name matching src.schemas.ChunkerFn.
chunk = page_aware_chunk
