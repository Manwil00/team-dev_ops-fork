import pytest
from src.services.query_generation_service import QueryGenerationService


@pytest.fixture
def service():
    """Provides a QueryGenerationService instance for testing."""
    return QueryGenerationService()


def test_get_category_suggestions_returns_dict(service):
    """
    Tests that get_category_suggestions returns a dictionary with the expected structure.
    """
    suggestions = service.get_category_suggestions()
    assert isinstance(suggestions, dict)
    assert "Computer Science" in suggestions
    assert "Mathematics" in suggestions
    assert "Physics" in suggestions
    assert isinstance(suggestions["Computer Science"], list)


def test_build_advanced_query_with_terms(service):
    """
    Tests building an advanced query with both search terms and a category.
    """
    query = service.build_advanced_query("graph neural network", "cs.LG")
    expected = 'all:"graph neural network"+AND+cat:cs.LG'
    assert query == expected


def test_build_advanced_query_no_terms(service):
    """
    Tests building a query with only a category when search terms are empty.
    """
    query = service.build_advanced_query("  ", "cs.AI")
    assert query == "cat:cs.AI"


def test_build_advanced_query_with_stop_words(service):
    """
    Tests that common stop words are stripped from the search terms.
    """
    query = service.build_advanced_query(
        "the latest trends in computer vision", "cs.CV"
    )
    # "the", "in" are stop words and should be removed. "latest" and "trends" are not in the stopword list.
    expected = 'all:"latest trends computer vision"+AND+cat:cs.CV'
    assert query == expected


def test_build_advanced_query_long_query(service):
    """
    Tests that the search query is truncated to the first 5 meaningful words.
    """
    long_query = "a very long query with more than five meaningful search words"
    query = service.build_advanced_query(long_query, "cs.CL")
    expected = 'all:"very long query more than"+AND+cat:cs.CL'
    assert query == expected


def test_internal_build_search_query_simple_category(service):
    """
    Tests the internal query builder with a simple category string.
    """
    query = service._build_search_query("cs.AI")
    assert query == "cat:cs.AI"


def test_internal_build_search_query_advanced(service):
    """
    Tests that the internal query builder recognizes and preserves an already advanced query.
    """
    advanced_query = 'all:"transformer architecture"+AND+cat:cs.LG'
    query = service._build_search_query(advanced_query)
    assert query == advanced_query


def test_internal_build_search_query_mixed_phrase(service):
    """

    Tests that the internal query builder can extract terms and a category from a mixed phrase.
    """
    mixed_phrase = "some research about robotics in cs.RO"
    query = service._build_search_query(mixed_phrase)
    assert query == 'all:"some research about robotics"+AND+cat:cs.RO'


def test_internal_build_search_query_natural_language(service):
    """
    Tests the natural language fallback for query building.
    """
    natural_query = "I want to see papers about machine learning"
    query = service._build_search_query(natural_query)
    assert query == 'all:"want see papers about machine"+AND+cat:cs.LG'
