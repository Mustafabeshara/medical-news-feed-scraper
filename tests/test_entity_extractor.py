"""Test entity extractor module."""

import pytest
import sys
sys.path.insert(0, '/home/ubuntu/news_feed_review')

from entity_extractor import extract_entities, enrich_article


class TestEntityExtraction:
    """Test entity extraction functionality."""
    
    def test_company_extraction(self):
        """Test company name extraction."""
        text = "Pfizer announced a partnership with Moderna"
        entities = extract_entities(text)
        assert "Pfizer" in entities["companies"]
        assert "Moderna" in entities["companies"]
    
    def test_product_extraction(self):
        """Test product name extraction."""
        text = "FDA approved Keytruda for cancer treatment"
        entities = extract_entities(text)
        assert "Keytruda" in entities["products"]
    
    def test_multiple_companies(self):
        """Test extraction of multiple companies."""
        text = "Johnson & Johnson, Merck, and AstraZeneca announced collaboration"
        entities = extract_entities(text)
        assert len(entities["companies"]) >= 2
    
    def test_empty_text(self):
        """Test handling of empty text."""
        entities = extract_entities("")
        assert entities["companies"] == []
        assert entities["products"] == []
    
    def test_none_text(self):
        """Test handling of None text."""
        entities = extract_entities(None)
        assert entities["companies"] == []
        assert entities["products"] == []
    
    def test_false_positive_filtering(self):
        """Test that false positives are filtered."""
        text = "The study shows that Epic systems are used in hospitals"
        entities = extract_entities(text)
        # "Epic" should not be in products due to false positive filtering
        assert "Epic" not in entities.get("products", [])
    
    def test_article_enrichment(self):
        """Test article enrichment with entities."""
        article = {
            "title": "Johnson & Johnson announces Eliquis approval",
            "summary": "Major pharmaceutical company news about blood thinner"
        }
        enriched = enrich_article(article)
        assert "companies" in enriched
        assert "products" in enriched
        assert "Johnson & Johnson" in enriched["companies"]
        assert "Eliquis" in enriched["products"]
    
    def test_enrichment_preserves_article_data(self):
        """Test that enrichment preserves original article data."""
        article = {
            "title": "Test Article",
            "summary": "Test summary",
            "link": "https://example.com"
        }
        enriched = enrich_article(article)
        assert enriched["title"] == article["title"]
        assert enriched["summary"] == article["summary"]
        assert enriched["link"] == article["link"]
    
    def test_drug_name_pattern_matching(self):
        """Test drug name pattern matching."""
        text = "Pembrolizumab and Nivolumab are checkpoint inhibitors"
        entities = extract_entities(text)
        # Should extract drug names based on suffix patterns
        assert len(entities["products"]) > 0
