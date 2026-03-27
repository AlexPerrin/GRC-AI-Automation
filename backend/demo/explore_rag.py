#!/usr/bin/env python3
"""
RAG exploration script — inspect ChromaDB collections and run ad-hoc queries.

Run from inside the API container (has the venv + Docker network access):

  docker exec -it grc-ai-automation-api-1 python3 /app/demo/explore_rag.py
  docker exec -it grc-ai-automation-api-1 python3 /app/demo/explore_rag.py -c vendor_1_LEGAL_1
  docker exec -it grc-ai-automation-api-1 python3 /app/demo/explore_rag.py -c vendor_1_LEGAL_1 -q "GDPR data transfer"
  docker exec -it grc-ai-automation-api-1 python3 /app/demo/explore_rag.py --all-queries
"""
import argparse
import sys

# Default: internal Docker hostname. Override with --host/--port if needed.
CHROMA_HOST = "chromadb"
CHROMA_PORT = 8000
EMBEDDER_MODEL = "all-MiniLM-L6-v2"

# Preset queries used by --all-queries mode
PRESET_QUERIES = [
    "GDPR data transfer and international transfers",
    "data retention and deletion policy",
    "penetration test and vulnerability assessment",
    "incident response plan and SLA",
    "revenue growth and financial health",
    "sub-processor and third-party data sharing",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_client(host: str, port: int):
    import chromadb
    return chromadb.HttpClient(host=host, port=port)


def get_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDER_MODEL)


def list_collections(client) -> list[str]:
    return sorted(client.list_collections())


def print_header(text: str) -> None:
    width = 72
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


def print_subheader(text: str) -> None:
    print(f"\n--- {text} ---")


def dump_collection(client, name: str) -> None:
    col = client.get_collection(name)
    results = col.get(include=["documents", "metadatas"])
    ids = results["ids"]
    docs = results["documents"]
    metas = results["metadatas"]
    print_header(f"Collection: {name}  ({len(ids)} chunks)")
    for i, (chunk_id, text, meta) in enumerate(zip(ids, docs, metas), 1):
        print(f"\n[Chunk {i}]  id={chunk_id}")
        if meta:
            print(f"  metadata: {meta}")
        print(f"  text ({len(text)} chars):")
        preview = text[:400].replace("\n", " ")
        suffix = " …" if len(text) > 400 else ""
        print(f"    {preview}{suffix}")


def query_collection(client, embedder, name: str, query: str, n: int = 4) -> None:
    col = client.get_collection(name)
    embedding = embedder.encode([query]).tolist()
    results = col.query(query_embeddings=embedding, n_results=min(n, col.count()))
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]
    print_subheader(f'Query: "{query}"  →  top {len(docs)} chunks')
    for i, (text, meta, dist) in enumerate(zip(docs, metas, distances), 1):
        score = 1 - dist  # cosine similarity
        preview = text[:350].replace("\n", " ")
        suffix = " …" if len(text) > 350 else ""
        print(f"\n  [{i}] score={score:.4f}  meta={meta}")
        print(f"      {preview}{suffix}")


def run_all_queries(client, embedder) -> None:
    collections = list_collections(client)
    if not collections:
        print("No collections found. Run POST /dev/seed first.")
        return
    for name in collections:
        print_header(f"Collection: {name}")
        for q in PRESET_QUERIES:
            try:
                query_collection(client, embedder, name, q, n=2)
            except Exception as exc:
                print(f"  [error] {exc}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Explore ChromaDB RAG data")
    parser.add_argument("--collection", "-c", metavar="NAME",
                        help="Collection to inspect or query")
    parser.add_argument("--query", "-q", metavar="TEXT",
                        help="Semantic query to run against --collection")
    parser.add_argument("--top-n", "-n", type=int, default=4,
                        help="Number of results to return (default: 4)")
    parser.add_argument("--all-queries", action="store_true",
                        help="Run preset queries against every collection")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all collections and exit")
    parser.add_argument("--host", default=CHROMA_HOST,
                        help=f"ChromaDB host (default: {CHROMA_HOST})")
    parser.add_argument("--port", type=int, default=CHROMA_PORT,
                        help=f"ChromaDB port (default: {CHROMA_PORT})")
    args = parser.parse_args()

    client = get_client(args.host, args.port)
    collections = list_collections(client)

    # --list (default when no other args given)
    if args.list or (not args.collection and not args.all_queries):
        print_header(f"ChromaDB collections  ({len(collections)} total)")
        if not collections:
            print("  (none — run POST /dev/seed first)")
        for name in collections:
            try:
                count = client.get_collection(name).count()
                print(f"  {name:<55} {count:>4} chunks")
            except Exception:
                print(f"  {name}")
        return

    # --all-queries
    if args.all_queries:
        embedder = get_embedder()
        run_all_queries(client, embedder)
        return

    # --collection (required from here on)
    if args.collection not in collections:
        print(f"Collection '{args.collection}' not found.")
        print(f"Available: {collections}")
        sys.exit(1)

    if args.query:
        embedder = get_embedder()
        print_header(f"Collection: {args.collection}")
        query_collection(client, embedder, args.collection, args.query, n=args.top_n)
    else:
        dump_collection(client, args.collection)


if __name__ == "__main__":
    main()
