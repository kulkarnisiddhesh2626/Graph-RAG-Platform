import re
from dataclasses import dataclass


@dataclass
class ExtractedEntity:
    entity_id: str
    label: str
    entity_type: str


@dataclass
class ExtractedRelation:
    source: str
    target: str
    relation: str


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "entity"


def extract_entities_and_relations(
    text: str,
) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
    """Rule-based extraction for local development without an LLM API key."""
    entities: list[ExtractedEntity] = []
    relations: list[ExtractedRelation] = []
    seen: set[str] = set()

    for match in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text):
        label = match.group(1).strip()
        if label in {"The", "This", "That"}:
            continue
        entity_id = slugify(label)
        if entity_id in seen:
            continue
        seen.add(entity_id)
        entities.append(ExtractedEntity(entity_id=entity_id, label=label, entity_type="concept"))

    relation_patterns = [
        (r"(\w[\w\s]*?)\s+works at\s+(\w[\w\s]*?)(?:\.|,|$)", "works_at"),
        (r"(\w[\w\s]*?)\s+uses\s+(\w[\w\s]*?)(?:\.|,|$)", "uses"),
        (r"(\w[\w\s]*?)\s+relates to\s+(\w[\w\s]*?)(?:\.|,|$)", "relates_to"),
    ]

    for pattern, relation in relation_patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            source_label = match.group(1).strip()
            target_label = match.group(2).strip()
            source_id = slugify(source_label)
            target_id = slugify(target_label)

            for entity_id, label in ((source_id, source_label), (target_id, target_label)):
                if entity_id not in seen:
                    seen.add(entity_id)
                    entities.append(
                        ExtractedEntity(entity_id=entity_id, label=label, entity_type="concept")
                    )

            relations.append(
                ExtractedRelation(source=source_id, target=target_id, relation=relation)
            )

    if len(entities) >= 2 and not relations:
        relations.append(
            ExtractedRelation(
                source=entities[0].entity_id,
                target=entities[1].entity_id,
                relation="mentioned_with",
            )
        )

    return entities, relations


def chunk_text(text: str, chunk_size: int = 200) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    for index in range(0, len(words), chunk_size):
        chunk = " ".join(words[index : index + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks or [text]
