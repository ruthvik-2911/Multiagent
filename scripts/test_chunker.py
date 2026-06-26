from backend.utils.text_chunker import split_text

text = """
This is paragraph one.

This is paragraph two.

This is paragraph three.

This is paragraph four.

This is paragraph five.

""" * 100

chunks = split_text(text)

print("Total Chunks:", len(chunks))

for i, chunk in enumerate(chunks[:2]):  # Only print first two to avoid spam
    print(f"\n------ Chunk {i+1} ------")
    print(chunk[:200])
