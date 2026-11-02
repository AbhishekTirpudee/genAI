import spacy
import random
from collections import defaultdict

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")


# ---------------------------------------------------------
# 1. SPLIT PARAGRAPH INTO SENTENCES
# ---------------------------------------------------------

def split_sentences(paragraph):
    doc = nlp(paragraph)

    sentences = [sent.text.strip() for sent in doc.sents]

    return sentences


# ---------------------------------------------------------
# 2. EXTRACT ENTITIES AND THEIR ROLES
# ---------------------------------------------------------

def extract_sentence_roles(sentence):

    doc = nlp(sentence)

    roles = {}

    for token in doc:

        # We consider nouns and proper nouns as entities
        if token.pos_ in ["NOUN", "PROPN"]:

            entity = token.text.lower()

            # Subject
            if token.dep_ in ["nsubj", "nsubjpass", "csubj"]:
                role = "S"

            # Object
            elif token.dep_ in ["dobj", "obj", "pobj", "iobj"]:
                role = "O"

            # Other occurrence
            else:
                role = "X"

            # If entity appears multiple times,
            # prioritize Subject over Object over Other
            if entity not in roles:
                roles[entity] = role

            else:
                if role == "S":
                    roles[entity] = "S"

                elif role == "O" and roles[entity] == "X":
                    roles[entity] = "O"

    return roles


# ---------------------------------------------------------
# 3. BUILD ENTITY GRID
# ---------------------------------------------------------

def build_entity_grid(sentences):

    sentence_roles = []

    all_entities = set()

    for sentence in sentences:

        roles = extract_sentence_roles(sentence)

        sentence_roles.append(roles)

        all_entities.update(roles.keys())

    # Sort entities alphabetically
    entities = sorted(all_entities)

    grid = []

    for roles in sentence_roles:

        row = []

        for entity in entities:

            if entity in roles:
                row.append(roles[entity])
            else:
                row.append("-")

        grid.append(row)

    return entities, grid


# ---------------------------------------------------------
# 4. DISPLAY ENTITY GRID
# ---------------------------------------------------------

def display_grid(sentences, entities, grid):

    print("\n" + "=" * 70)
    print("ENTITY GRID")
    print("=" * 70)

    # Header
    print(f"{'Sentence':<10}", end="")

    for entity in entities:
        print(f"{entity:<15}", end="")

    print()

    print("-" * (10 + 15 * len(entities)))

    # Rows
    for i, row in enumerate(grid):

        print(f"S{i+1:<9}", end="")

        for role in row:
            print(f"{role:<15}", end="")

        print()


# ---------------------------------------------------------
# 5. TRANSITION SCORING
# ---------------------------------------------------------

def transition_score(previous, current):

    # Entity absent in either sentence
    if previous == "-" or current == "-":
        return 0

    # Subject remains Subject
    if previous == "S" and current == "S":
        return 3

    # Subject -> Object
    if previous == "S" and current == "O":
        return 2

    # Object -> Subject
    if previous == "O" and current == "S":
        return 2

    # Object -> Object
    if previous == "O" and current == "O":
        return 2

    # Other -> Subject/Object
    if previous == "X" and current in ["S", "O"]:
        return 1

    # Subject/Object -> Other
    if previous in ["S", "O"] and current == "X":
        return 1

    # Other -> Other
    if previous == "X" and current == "X":
        return 1

    return 0


# ---------------------------------------------------------
# 6. CALCULATE COHERENCE SCORE
# ---------------------------------------------------------

def calculate_coherence_score(grid):

    if len(grid) < 2:
        return 0

    total_score = 0
    transitions = 0

    for i in range(len(grid) - 1):

        current_sentence = grid[i]
        next_sentence = grid[i + 1]

        for previous_role, current_role in zip(
            current_sentence,
            next_sentence
        ):

            # Only count transitions where entity
            # appears in both sentences
            if previous_role != "-" and current_role != "-":

                score = transition_score(
                    previous_role,
                    current_role
                )

                total_score += score

                transitions += 1

    if transitions == 0:
        return 0

    # Normalize score to 0-100
    max_possible_score = transitions * 3

    final_score = (total_score / max_possible_score) * 100

    return round(final_score, 2)


# ---------------------------------------------------------
# 7. SHUFFLE SENTENCES
# ---------------------------------------------------------

def shuffle_sentences(sentences):

    shuffled = sentences.copy()

    random.shuffle(shuffled)

    return shuffled


# ---------------------------------------------------------
# 8. MAIN PROGRAM
# ---------------------------------------------------------

def main():

    print("\n" + "=" * 70)
    print("ENTITY-GRID DISCOURSE COHERENCE SCORER")
    print("=" * 70)

    print("\nEnter your paragraph.")
    print("Press ENTER after typing the paragraph.\n")

    paragraph = input("Paragraph: ")

    # ---------------------------------------------
    # ORIGINAL PARAGRAPH
    # ---------------------------------------------

    sentences = split_sentences(paragraph)

    print("\n\nORIGINAL PARAGRAPH")
    print("-" * 70)

    for i, sentence in enumerate(sentences):
        print(f"S{i+1}: {sentence}")

    entities, grid = build_entity_grid(sentences)

    display_grid(sentences, entities, grid)

    original_score = calculate_coherence_score(grid)

    print("\nOriginal Coherence Score:",
          original_score, "/ 100")

    # ---------------------------------------------
    # SHUFFLED PARAGRAPH
    # ---------------------------------------------

    shuffled = shuffle_sentences(sentences)

    print("\n\nSHUFFLED PARAGRAPH")
    print("-" * 70)

    for i, sentence in enumerate(shuffled):
        print(f"S{i+1}: {sentence}")

    shuffled_entities, shuffled_grid = build_entity_grid(shuffled)

    display_grid(
        shuffled,
        shuffled_entities,
        shuffled_grid
    )

    shuffled_score = calculate_coherence_score(
        shuffled_grid
    )

    print("\nShuffled Coherence Score:",
          shuffled_score, "/ 100")

    # ---------------------------------------------
    # COMPARISON
    # ---------------------------------------------

    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)

    print(f"Original Paragraph : {original_score}/100")
    print(f"Shuffled Paragraph : {shuffled_score}/100")

    difference = round(
        original_score - shuffled_score,
        2
    )

    print(f"Score Difference   : {difference}")

    if difference > 0:
        print(
            "\nThe original sentence order has "
            "more repeated entity transitions "
            "according to this simplified model."
        )

    elif difference < 0:
        print(
            "\nThe shuffled sentence order has "
            "more repeated entity transitions "
            "according to this simplified model."
        )

    else:
        print(
            "\nBoth versions received the same score."
        )


# Run program
if __name__ == "__main__":
    main()