from services.retrieval import load_chunks, build_context
from services.generation import generate_answer


# Load real Phoenix website content
chunks = load_chunks()

# Select the two chunks we already inspected
selected_chunks = chunks[:2]

# Prepare source excerpts for Gemini
context = build_context(selected_chunks)

# Ask a question based on the selected content
question = "מה הסכנה בטעינת סוללות של קורקינטים חשמליים בבית?"

print("QUESTION:")
print(question)

print("\nSOURCES:")
for chunk in selected_chunks:
    print(chunk["url"])

print("\nGENERATING ANSWER...\n")

answer = generate_answer(
    question=question,
    context=context
)

print("ANSWER:")
print(answer)
print("\n--- TEST 2: UNRELATED QUESTION ---")

unrelated_question = "מה מספר הטלפון של שירות הלקוחות?"

unrelated_answer = generate_answer(
    question=unrelated_question,
    context=context
)

print("QUESTION:", unrelated_question)
print("ANSWER:", unrelated_answer)