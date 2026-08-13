from backend.app.extraction import chunk_text, extract_entities_and_relations


def test_extract_entities_and_relations():
    text = "Alice works at GraphCorp. GraphCorp uses Chroma."
    entities, relations = extract_entities_and_relations(text)
    labels = {entity.label for entity in entities}
    assert "Alice" in labels
    assert "GraphCorp" in labels
    assert any(relation.relation == "works_at" for relation in relations)


def test_chunk_text():
    text = " ".join(f"word{i}" for i in range(250))
    chunks = chunk_text(text, chunk_size=100)
    assert len(chunks) >= 2
