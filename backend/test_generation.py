from services.generation import generate_answer


# Test 1: Information exists in the context
print("\n--- TEST 1: Information exists ---")

answer = generate_answer(
    question="מהן שעות הפעילות?",
    context="""
    שעות הפעילות של מוקד הדוגמה הן
    בימים ראשון עד חמישי, בין 08:00 ל-16:00.
    """
)

print(answer)


# Test 2: Information is missing from the context
print("\n--- TEST 2: Missing information ---")

answer = generate_answer(
    question="מה מספר הטלפון של המוקד?",
    context="""
    שעות הפעילות של מוקד הדוגמה הן
    בימים ראשון עד חמישי, בין 08:00 ל-16:00.
    """
)

print(answer)


# Test 3: Empty context
print("\n--- TEST 3: Empty context ---")

answer = generate_answer(
    question="מה מספר הטלפון של המוקד?",
    context=""
)

print(answer)