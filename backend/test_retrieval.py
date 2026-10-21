from services.retrieval import load_chunks, build_context

chunks = load_chunks()

print("Total chunks:", len(chunks))

# Select two chunks for formatting test
sample_chunks = chunks[:2]

context = build_context(sample_chunks)

print("\nFORMATTED CONTEXT:")
print(context[:2000])