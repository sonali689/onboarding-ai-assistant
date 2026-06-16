"""
Phase 1 validation — run this BEFORE full ingestion.
Confirms Qwen2 handles cross-lingual generation correctly:
  - Japanese question + English context  → Japanese answer
  - English question  + Japanese context → English answer
All 4 tests must pass before proceeding to Phase 2.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ollama
from config import QWEN2_MODEL, OLLAMA_BASE_URL


def has_japanese(text: str) -> bool:
    """Check if text contains Japanese characters."""
    return any(
        ("\u3040" <= c <= "\u309f")   # hiragana
        or ("\u30a0" <= c <= "\u30ff") # katakana
        or ("\u4e00" <= c <= "\u9fff") # kanji
        for c in text
    )


def has_english(text: str) -> bool:
    """Check if text contains Latin alphabet characters."""
    return any(c.isalpha() and ord(c) < 128 for c in text)


def run_test(
    test_num: int,
    context: str,
    question: str,
    expect_japanese: bool,
) -> bool:
    expected_lang = "Japanese" if expect_japanese else "English"
    print(f"\n── Test {test_num} (expect {expected_lang} answer) ──")
    print(f"  Question : {question}")

    try:
        response = ollama.chat(
            model=QWEN2_MODEL,
            messages=[{
                "role": "user",
                "content": (
                    f"Context: {context}\n\n"
                    f"Question: {question}\n\n"
                    "Answer in the same language as the question:"
                ),
            }],
        )
        answer = response["message"]["content"]
        print(f"  Answer   : {answer[:250]}")

        if expect_japanese:
            passed = has_japanese(answer)
        else:
            # English answer should have Latin chars and minimal Japanese
            passed = has_english(answer) and not has_japanese(answer)

        print(f"  Result   : {' PASS' if passed else ' FAIL'}")
        return passed

    except Exception as e:
        print(f"   ERROR  : {e}")
        print(f"     Check  : Is Ollama running? Run: ollama serve")
        print(f"     Check  : Is {QWEN2_MODEL} pulled? Run: ollama list")
        return False


def main():
    print("=" * 60)
    print("Bilingual Validation Test — Qwen2 via Ollama")
    print(f"Model : {QWEN2_MODEL}")
    print(f"Server: {OLLAMA_BASE_URL}")
    print("=" * 60)

    test_cases = [
        # (context, question, expect_japanese)
        (
            "Annual leave entitlement is 25 working days per year."
            " [HR_Manual.pptx, Slide 14]",
            "何日間の年次有給休暇がありますか？",
            True,   # Japanese question → expect Japanese answer
        ),
        (
            "年次有給休暇は年間25労働日です。[HR_Manual_JP.pptx, スライド14]",
            "How many days of annual leave do I receive?",
            False,  # English question → expect English answer
        ),
        (
            "The airbag deploys within 30 milliseconds of impact detection."
            " Safety systems are tested to FMVSS 208 standards.",
            "What is the airbag deployment time?",
            False,  # English question → expect English answer
        ),
        (
            "エアバッグは衝撃検知から30ミリ秒以内に展開します。"
            "安全システムはFMVSS 208規格に基づいてテストされています。",
            "エアバッグはどのように作動しますか？",
            True,   # Japanese question → expect Japanese answer
        ),
    ]

    results = []
    for i, (context, question, expect_jp) in enumerate(test_cases, start=1):
        passed = run_test(i, context, question, expect_jp)
        results.append(passed)

    passed_count = sum(results)
    total = len(results)

    print("\n" + "=" * 60)
    print(f"Result: {passed_count}/{total} tests passed")
    print("=" * 60)

    if passed_count == total:
        print("  All tests passed.")
        print("   Safe to proceed to Phase 2 — run ingestion pipeline.")
        print("   Command: python ingestion/embedder.py")
    else:
        failed = [i + 1 for i, r in enumerate(results) if not r]
        print(f"  Tests {failed} failed.")
        print("   Action: Strengthen BILINGUAL_PROMPT in")
        print("           query/prompt_templates.py")
        print("   Do NOT proceed to ingestion until all 4 pass.")
    print("=" * 60)


if __name__ == "__main__":
    main()
