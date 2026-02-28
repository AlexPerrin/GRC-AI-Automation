"""
Document chunker — raw text → overlapping chunks for embedding.
Stub for Day 1; fully implemented in Day 2.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    text: str
    metadata: dict = field(default_factory=dict)


class DocumentChunker:
    """
    Splits raw text into overlapping chunks using LangChain's
    RecursiveCharacterTextSplitter.

    Default: 512-token chunks with 64-token overlap.
    Each chunk carries metadata: doc_id, vendor_id, stage, chunk_index,
    and page_number where available.
    """

    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict) -> List[Chunk]:
        """Split text into overlapping chunks with metadata."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.overlap,
        )
        texts = splitter.split_text(text)
        return [
            Chunk(text=t, metadata={**metadata, "chunk_index": i})
            for i, t in enumerate(texts)
        ]
