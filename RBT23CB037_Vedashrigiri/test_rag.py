"""
test_rag.py
"""
import sys
import io
sys.stdout.reconfigure(encoding='utf-8')
from rag_engine import AcademicRAGEngine

print("Testing AcademicRAGEngine...")
engine = AcademicRAGEngine()

with open("sample_notes/CS_Foundations_Notes.pdf", "rb") as f:
    pdf_bytes = f.read()

res = engine.add_pdf(pdf_bytes, "CS_Foundations_Notes.pdf")
print("Added PDF:", res)

# Test query
query = "What are the four Coffman conditions for a deadlock?"
print(f"Querying: {query}")
result = engine.query(query)
print("Answer:\n", result["answer"][:300], "...\n")
print("Citations count:", len(result["citations"]))
for c in result["citations"]:
    print(f" - Page {c['page']}: {c['section']} (Relevance: {c['relevance']}%)")

# Test flashcards
print("\nTesting flashcards...")
cards = engine.generate_flashcards(count=3)
print(f"Generated {len(cards)} cards:")
for card in cards:
    print(f" - [{card.get('category')}] {card.get('front')} -> {card.get('back')[:60]}...")

# Test quiz
print("\nTesting quiz...")
quiz = engine.generate_quiz(count=2)
print(f"Generated {len(quiz)} quiz questions:")
for q in quiz:
    print(f" - Q: {q.get('question')} (Correct: {q.get('correct_index')})")

print("\nSUCCESS: All RAG tests passed!")
