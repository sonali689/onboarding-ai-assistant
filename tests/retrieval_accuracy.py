"""
Phase 3 validation — run this AFTER full ingestion.
Tests that cross-lingual retrieval works:
  - Japanese questions find English content
  - English questions find Japanese content
Target: 85%+ accuracy. If below, increase TOP_K in config.py.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query.retriever import retrieve_chunks
from config import TOP_K

# ── Test cases ────────────────────────────────────────────────────────────────
# expected_keyword: substring expected in source filename, subfolder,
# or chunk content of at least one retrieved chunk.
# Fill in more after running ingestion and reviewing your actual content.
# ─────────────────────────────────────────────────────────────────────────────
TEST_CASES = [
    # ── English questions finding Japanese content ────────────────────────
    {
        "question":         "What is the airbag system?",
        "expected_keyword": "エアバッグ",
        "question_lang":    "en",
        "description":      "EN question → should find airbag folder content",
    },
    {
        "question":         "What does the seatbelt system do?",
        "expected_keyword": "シートベルト",
        "question_lang":    "en",
        "description":      "EN question → should find seatbelt folder content",
    },
    {
        "question":         "What is the TechCenter responsible for?",
        "expected_keyword": "TechCenter",
        "question_lang":    "en",
        "description":      "EN question → should find TechCenter intro content",
    },
    # ── Japanese questions finding English content ────────────────────────
    {
        "question":         "エアバッグの展開プロセスを説明してください",
        "expected_keyword": "airbag",
        "question_lang":    "ja",
        "description":      "JP question → should find airbag content",
    },
    {
        "question":         "シートベルトの仕組みを教えてください",
        "expected_keyword": "seatbelt",
        "question_lang":    "ja",
        "description":      "JP question → should find seatbelt content",
    },
    {
        "question":         "法規認証とは何ですか？",
        "expected_keyword": "法規",
        "question_lang":    "ja",
        "description":      "JP question → should find regulations folder",
    },
    # ── Mixed / cross-folder questions ────────────────────────────────────
    {
        "question":         "What are the safety regulations and standards?",
        "expected_keyword": "007",
        "question_lang":    "en",
        "description":      "EN question → should find folder 007 regulations",
    },
    {
        "question":         "ステアリングホイールについて教えてください",
        "expected_keyword": "ステアリング",
        "question_lang":    "ja",
        "description":      "JP question → should find steering wheel folder",
    },
    # ── Add more after reviewing your ingested content ────────────────────
    # {
    #     "question":         "FILL IN WITH REAL QUESTION",
    #     "expected_keyword": "FILL IN WITH EXPECTED KEYWORD",
    #     "question_lang":    "en",  # or "ja"
    #     "description":      "Description of what this tests",
    # },
]


def main():
    print("=" * 60)
    print("Retrieval Accuracy Test — Phase 3 Validation")
    print(f"TOP_K = {TOP_K} (chunks retrieved per query)")
    print("=" * 60)

    if not TEST_CASES:
        print("⚠️  No test cases defined. Add them to TEST_CASES list.")
        return

    results = []

    for i, tc in enumerate(TEST_CASES, start=1):
        question = tc["question"]
        keyword  = tc["expected_keyword"].lower()
        lang     = tc["question_lang"].upper()
        desc     = tc["description"]

        print(f"\n── Test {i} [{lang}] ──")
        print(f"  {desc}")
        print(f"  Question: {question}")
        print(f"  Expected keyword: '{tc['expected_keyword']}'")

        try:
            chunks = retrieve_chunks(question)
        except Exception as e:
            print(f"  ❌ ERROR during retrieval: {e}")
            results.append(False)
            continue

        retrieved_sources = []
        matched = False

        for chunk in chunks:
            source    = chunk.metadata.get("source", "").lower()
            subfolder = chunk.metadata.get("subfolder", "").lower()
            content   = chunk.page_content.lower()
            display   = chunk.metadata.get("source", "?")
            retrieved_sources.append(display)

            if keyword in source or keyword in subfolder or keyword in content:
                matched = True

        print(f"  Retrieved: {retrieved_sources}")
        print(f"  Result   : {'✅ PASS' if matched else '❌ FAIL'}")
        results.append(matched)

    # ── Summary ───────────────────────────────────────────────────────────
    passed   = sum(results)
    total    = len(results)
    accuracy = (passed / total * 100) if total > 0 else 0

    print("\n" + "=" * 60)
    print(f"Accuracy: {passed}/{total} ({accuracy:.0f}%)")
    print("=" * 60)

    if accuracy >= 85:
        print("✅ Retrieval accuracy meets the 85% target.")
        print("   Safe to proceed to Phase 4 — build the query chain and UI.")
    elif accuracy >= 60:
        print("⚠️  Below 85% target.")
        print(f"   Action: Increase TOP_K from {TOP_K} to "
              f"{TOP_K + 3} in config.py and re-run.")
    else:
        print("❌ Well below target — retrieval is not working correctly.")
        print("   Possible causes:")
        print("   1. Ingestion did not complete — re-run embedder.py")
        print("   2. Wrong embedding model — check EMBEDDING_MODEL in config.py")
        print("   3. ChromaDB collection empty — check chroma_db/ folder exists")

    print("=" * 60)


if __name__ == "__main__":
    main()