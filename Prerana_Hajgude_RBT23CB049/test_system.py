"""
test_system.py - End-to-end test suite for the AI Technical Support System.
"""

import os
import sys

# Ensure UTF-8 output on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from ingest import ingest_manuals, DEFAULT_MANUALS_DIR, DEFAULT_CHROMA_DIR
from retriever import get_relevant_chunks
from agents import RouterAgent, TroubleshootingAgent


def run_tests():
    print("=" * 65)
    print("🧪 RUNNING AI TECHNICAL SUPPORT SYSTEM VERIFICATION SUITE")
    print("=" * 65)

    # 1. Ingestion Test
    print("\n[Step 1] Ingesting PDF manuals into ChromaDB...")
    ingest_result = ingest_manuals(manuals_dir=DEFAULT_MANUALS_DIR, chroma_dir=DEFAULT_CHROMA_DIR)
    assert ingest_result["pdf_count"] >= 1, "Failed: Expected at least 1 PDF indexed"
    assert ingest_result["chunk_count"] >= 1, "Failed: Expected at least 1 chunk indexed"
    print(f"✅ Ingestion Succeeded: {ingest_result['status']}")

    # 2. Retriever Test
    sample_query = "My laptop fan is very loud"
    print(f"\n[Step 2] Testing Retriever with query: '{sample_query}'...")
    chunks = get_relevant_chunks(sample_query, n_results=4)
    assert len(chunks) == 4, f"Failed: Expected 4 chunks, got {len(chunks)}"
    for idx, c in enumerate(chunks, 1):
        assert "file_name" in c, f"Missing file_name in chunk {idx}"
        assert "page_number" in c, f"Missing page_number in chunk {idx}"
        assert "text" in c, f"Missing text in chunk {idx}"
        print(f"  Chunk {idx}: [{c['file_name']}, Page {c['page_number']}] (Distance: {c['distance']:.4f})")
    assert chunks[0]["page_number"] == 3, f"Expected top chunk to be Page 3, got Page {chunks[0]['page_number']}"
    print("✅ Retriever Succeeded: Top chunk correctly matches Section 3 (Cooling Fan Noise)")

    # 3. Router Agent Test - Non-Hardware Question
    non_hw_query = "Write a haiku about chocolate ice cream"
    print(f"\n[Step 3] Testing Router Agent with non-hardware query: '{non_hw_query}'...")
    router = RouterAgent()
    is_hw_non, refusal = router.route(non_hw_query)
    assert not is_hw_non, "Failed: Non-hardware query was marked as hardware"
    assert refusal and len(refusal) > 10, "Failed: Empty refusal message"
    print(f"✅ Router Agent Succeeded (Politely Refused):\n  \"{refusal[:120]}...\"")

    # 4. Router Agent Test - Hardware Question
    print(f"\n[Step 4] Testing Router Agent with hardware query: '{sample_query}'...")
    is_hw_yes, refusal_none = router.route(sample_query)
    assert is_hw_yes, "Failed: Hardware query was marked as non-hardware"
    assert refusal_none is None, "Failed: Refusal message should be None for hardware questions"
    print("✅ Router Agent Succeeded: Classified as Hardware")

    # 5. Troubleshooting Agent Test
    print(f"\n[Step 5] Testing Troubleshooting Agent with retrieved chunks...")
    troubleshooter = TroubleshootingAgent()
    solution = troubleshooter.troubleshoot(sample_query, chunks)
    print("\n--- Diagnostic Response Output ---")
    print(solution)
    print("----------------------------------")

    # Validations
    assert "Likely Cause" in solution, "Missing 'Likely Cause' section"
    assert "Step-by-Step Fixes" in solution, "Missing 'Step-by-Step Fixes' section"
    assert "Safety Warning" in solution, "Missing 'Safety Warning' section"
    assert "Follow-up Question" in solution, "Missing 'Follow-up Question' section"
    assert "Dell_Inspiron_Hardware_Maintenance_Manual.pdf" in solution, "Missing manual citation"
    assert "Page" in solution, "Missing page citation"

    print("\n" + "=" * 65)
    print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    run_tests()

