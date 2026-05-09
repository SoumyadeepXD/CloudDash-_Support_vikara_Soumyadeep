import pytest
from retrieval.retriever import Retriever
from models.state import Message

@pytest.fixture
def retriever():
    return Retriever()

def test_vector_store_results(retriever):
    # Test that vector store returns results for "alert not firing"
    chunks = retriever.retrieve("alert not firing")
    assert len(chunks) > 0
    assert any("KB-005" in chunk.article_id for chunk in chunks)

def test_score_filtering(retriever):
    # Low relevance query returns empty
    chunks = retriever.retrieve("gibberish nonsense abcd xyz 1234")
    # Our reranker/distance will produce very low scores for gibberish
    assert len(chunks) == 0

def test_query_rewriting(retriever):
    history = [Message(role="user", content="my alerts are broken")]
    # Without API keys, fallback returns original or we mock
    new_query = retriever.rewrite_query(history, "can you fix it")
    assert isinstance(new_query, str)
    assert len(new_query) > 0
