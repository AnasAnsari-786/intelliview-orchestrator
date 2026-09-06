import numpy as np
import pytest

from retrieval.embeddings import (
    _DEFAULT_CHUNK_OVERLAP,
    _DEFAULT_CHUNK_SIZE,
    chunk_text,
    embed_query,
    embed_texts,
    get_model,
)


def test_embed_query_returns_384_dimensional_normalized_vector():
    embedding = embed_query("How do I reset my password?")

    assert len(embedding) == 384
    assert np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-5)


def test_embed_texts_returns_one_embedding_per_text():
    texts = [
        "How do I reset my password?",
        "Machine learning uses data to learn patterns.",
    ]

    embeddings = embed_texts(texts)

    assert len(embeddings) == len(texts)
    assert all(len(embedding) == 384 for embedding in embeddings)

    for embedding in embeddings:
        assert np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-5)


def test_related_texts_are_more_similar_than_unrelated_texts():
    query = embed_query("How do I reset my password?")
    related = embed_query("Where can I change my account password?")
    unrelated = embed_query("What is the weather forecast for tomorrow?")

    related_similarity = np.dot(query, related)
    unrelated_similarity = np.dot(query, unrelated)

    assert related_similarity > unrelated_similarity


def test_chunk_text_uses_default_size_and_overlap():
    assert _DEFAULT_CHUNK_SIZE == 300
    assert _DEFAULT_CHUNK_OVERLAP == 50

    text = "This is a sentence used for testing token based chunking. " * 200

    chunks = chunk_text(text)

    assert len(chunks) >= 2

    assert all(chunk.strip() for chunk in chunks)

    first_chunk = chunks[0]
    second_chunk = chunks[1]

    assert first_chunk[-100:] in second_chunk


def test_chunk_text_validates_chunk_parameters():
    with pytest.raises(ValueError, match="chunk_size"):
        chunk_text("some text", chunk_size=0)

    with pytest.raises(ValueError, match="chunk_overlap"):
        chunk_text("some text", chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError, match="chunk_overlap"):
        chunk_text("some text", chunk_size=100, chunk_overlap=-1)


def test_model_is_singleton():
    first_model = get_model()
    second_model = get_model()

    assert first_model is second_model
