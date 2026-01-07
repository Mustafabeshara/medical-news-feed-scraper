"""
Enhanced Entity Extractor v2.0 - Advanced Company & Product Extraction

Features:
1. Confidence scoring for extractions
2. Company categorization by sector
3. Stock ticker mapping
4. Sentiment analysis (basic)
5. Context extraction
6. Relationship detection (partnerships, acquisitions)
7. Trending entity tracking
"""

import re
import logging
from typing import List, Dict, Set, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class CompanySector(Enum):
    """Company sector classification"""
    BIG_PHARMA = "Big Pharma"
    BIOTECH = "Biotech"
    MEDICAL_DEVICES = "Medical Devices"
    SURGICAL_ROBOTICS = "Surgical Robotics"
    DIAGNOSTICS = "Diagnostics"
    DIGITAL_HEALTH = "Digital Health"
    HEALTHCARE_SYSTEMS = "Healthcare Systems"
    INSURANCE = "Insurance"
    UNKNOWN = "Unknown"


class Sentiment(Enum):
    """Sentiment classification"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class CompanyInfo:
    """Detailed company information"""
    name: str
    ticker: Optional[str] = None
    sector: CompanySector = CompanySector.UNKNOWN
    aliases: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "ticker": self.ticker,
            "sector": self.sector.value,
            "aliases": self.aliases
        }


@dataclass
class ExtractedEntity:
    """Extracted entity with metadata"""
    name: str
    entity_type: str  # "company" or "product"
    confidence: float  # 0.0 to 1.0
    sector: Optional[str] = None
    ticker: Optional[str] = None
    sentiment: Sentiment = Sentiment.NEUTRAL
    context: Optional[str] = None
    position: int = 0  # Position in text
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.entity_type,
            "confidence": round(self.confidence, 2),
            "sector": self.sector,
            "ticker": self.ticker,
            "sentiment": self.sentiment.value,
            "context": self.context
        }


@dataclass
class Relationship:
    """Relationship between entities"""
    entity1: str
    entity2: str
    relationship_type: str  # "acquisition", "partnership", "competition"
    confidence: float
    context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity1": self.entity1,
            "entity2": self.entity2,
            "type": self.relationship_type,
            "confidence": round(self.confidence, 2),
            "context": self.context
        }


# Comprehensive company database with metadata
COMPANY_DATABASE: Dict[str, CompanyInfo] = {
    # Big Pharma
    "Pfizer": CompanyInfo("Pfizer", "PFE", CompanySector.BIG_PHARMA, ["Pfizer Inc"]),
    "Johnson & Johnson": CompanyInfo("Johnson & Johnson", "JNJ", CompanySector.BIG_PHARMA, ["J&J", "JNJ"]),
    "Merck": CompanyInfo("Merck", "MRK", CompanySector.BIG_PHARMA, ["Merck & Co", "MSD"]),
    "AbbVie": CompanyInfo("AbbVie", "ABBV", CompanySector.BIG_PHARMA),
    "Novartis": CompanyInfo("Novartis", "NVS", CompanySector.BIG_PHARMA, ["Novartis AG"]),
    "Roche": CompanyInfo("Roche", "RHHBY", CompanySector.BIG_PHARMA, ["Roche Holding"]),
    "Bristol-Myers Squibb": CompanyInfo("Bristol-Myers Squibb", "BMY", CompanySector.BIG_PHARMA, ["BMS", "Bristol Myers"]),
    "Eli Lilly": CompanyInfo("Eli Lilly", "LLY", CompanySector.BIG_PHARMA, ["Lilly"]),
    "AstraZeneca": CompanyInfo("AstraZeneca", "AZN", CompanySector.BIG_PHARMA),
    "Sanofi": CompanyInfo("Sanofi", "SNY", CompanySector.BIG_PHARMA),
    "GlaxoSmithKline": CompanyInfo("GlaxoSmithKline", "GSK", CompanySector.BIG_PHARMA, ["GSK"]),
    "Gilead": CompanyInfo("Gilead", "GILD", CompanySector.BIG_PHARMA, ["Gilead Sciences"]),
    "Amgen": CompanyInfo("Amgen", "AMGN", CompanySector.BIG_PHARMA),
    "Regeneron": CompanyInfo("Regeneron", "REGN", CompanySector.BIG_PHARMA, ["Regeneron Pharmaceuticals"]),
    "Takeda": CompanyInfo("Takeda", "TAK", CompanySector.BIG_PHARMA, ["Takeda Pharmaceutical"]),
    "Bayer": CompanyInfo("Bayer", "BAYRY", CompanySector.BIG_PHARMA, ["Bayer AG"]),
    "Novo Nordisk": CompanyInfo("Novo Nordisk", "NVO", CompanySector.BIG_PHARMA),
    
    # Biotech
    "Moderna": CompanyInfo("Moderna", "MRNA", CompanySector.BIOTECH),
    "BioNTech": CompanyInfo("BioNTech", "BNTX", CompanySector.BIOTECH),
    "Vertex": CompanyInfo("Vertex", "VRTX", CompanySector.BIOTECH, ["Vertex Pharmaceuticals"]),
    "Biogen": CompanyInfo("Biogen", "BIIB", CompanySector.BIOTECH),
    "Illumina": CompanyInfo("Illumina", "ILMN", CompanySector.BIOTECH),
    "CRISPR Therapeutics": CompanyInfo("CRISPR Therapeutics", "CRSP", CompanySector.BIOTECH),
    "Intellia": CompanyInfo("Intellia", "NTLA", CompanySector.BIOTECH, ["Intellia Therapeutics"]),
    
    # Medical Devices
    "Medtronic": CompanyInfo("Medtronic", "MDT", CompanySector.MEDICAL_DEVICES),
    "Abbott": CompanyInfo("Abbott", "ABT", CompanySector.MEDICAL_DEVICES, ["Abbott Laboratories"]),
    "Boston Scientific": CompanyInfo("Boston Scientific", "BSX", CompanySector.MEDICAL_DEVICES),
    "Stryker": CompanyInfo("Stryker", "SYK", CompanySector.MEDICAL_DEVICES),
    "Edwards Lifesciences": CompanyInfo("Edwards Lifesciences", "EW", CompanySector.MEDICAL_DEVICES, ["Edwards"]),
    "Zimmer Biomet": CompanyInfo("Zimmer Biomet", "ZBH", CompanySector.MEDICAL_DEVICES, ["Zimmer"]),
    "Becton Dickinson": CompanyInfo("Becton Dickinson", "BDX", CompanySector.MEDICAL_DEVICES, ["BD"]),
    "Dexcom": CompanyInfo("Dexcom", "DXCM", CompanySector.MEDICAL_DEVICES),
    "ResMed": CompanyInfo("ResMed", "RMD", CompanySector.MEDICAL_DEVICES),
    "Align Technology": CompanyInfo("Align Technology", "ALGN", CompanySector.MEDICAL_DEVICES, ["Invisalign"]),
    
    # Surgical Robotics
    "Intuitive Surgical": CompanyInfo("Intuitive Surgical", "ISRG", CompanySector.SURGICAL_ROBOTICS, ["Intuitive", "da Vinci"]),
    "CMR Surgical": CompanyInfo("CMR Surgical", None, CompanySector.SURGICAL_ROBOTICS, ["Versius"]),
    "Asensus Surgical": CompanyInfo("Asensus Surgical", "ASXC", CompanySector.SURGICAL_ROBOTICS, ["Senhance"]),
    
    # Diagnostics
    "Quest Diagnostics": CompanyInfo("Quest Diagnostics", "DGX", CompanySector.DIAGNOSTICS),
    "LabCorp": CompanyInfo("LabCorp", "LH", CompanySector.DIAGNOSTICS, ["Labcorp"]),
    "Exact Sciences": CompanyInfo("Exact Sciences", "EXAS", CompanySector.DIAGNOSTICS),
    "Thermo Fisher": CompanyInfo("Thermo Fisher", "TMO", CompanySector.DIAGNOSTICS, ["Thermo Fisher Scientific"]),
    
    # Digital Health
    "Teladoc": CompanyInfo("Teladoc", "TDOC", CompanySector.DIGITAL_HEALTH, ["Teladoc Health"]),
    "Veeva Systems": CompanyInfo("Veeva Systems", "VEEV", CompanySector.DIGITAL_HEALTH, ["Veeva"]),
    "Doximity": CompanyInfo("Doximity", "DOCS", CompanySector.DIGITAL_HEALTH),
    
    # Healthcare Systems
    "UnitedHealth": CompanyInfo("UnitedHealth", "UNH", CompanySector.HEALTHCARE_SYSTEMS, ["UnitedHealthcare", "United Health"]),
    "CVS Health": CompanyInfo("CVS Health", "CVS", CompanySector.HEALTHCARE_SYSTEMS, ["CVS"]),
    "Cigna": CompanyInfo("Cigna", "CI", CompanySector.INSURANCE),
    "Humana": CompanyInfo("Humana", "HUM", CompanySector.INSURANCE),
    "Anthem": CompanyInfo("Anthem", "ELV", CompanySector.INSURANCE, ["Elevance Health"]),
}

# Product database with categories
PRODUCT_DATABASE: Dict[str, Dict[str, Any]] = {
    # Surgical Robots
    "da Vinci": {"company": "Intuitive Surgical", "category": "Surgical Robot"},
    "da Vinci Xi": {"company": "Intuitive Surgical", "category": "Surgical Robot"},
    "da Vinci SP": {"company": "Intuitive Surgical", "category": "Surgical Robot"},
    "da Vinci 5": {"company": "Intuitive Surgical", "category": "Surgical Robot"},
    "Mako": {"company": "Stryker", "category": "Surgical Robot"},
    "ROSA": {"company": "Zimmer Biomet", "category": "Surgical Robot"},
    "Hugo RAS": {"company": "Medtronic", "category": "Surgical Robot"},
    "Versius": {"company": "CMR Surgical", "category": "Surgical Robot"},
    "Ion": {"company": "Intuitive Surgical", "category": "Surgical Robot"},
    "Monarch": {"company": "Intuitive Surgical", "category": "Surgical Robot"},
    
    # Diabetes Devices
    "FreeStyle Libre": {"company": "Abbott", "category": "CGM"},
    "Dexcom G7": {"company": "Dexcom", "category": "CGM"},
    "Dexcom G6": {"company": "Dexcom", "category": "CGM"},
    "Omnipod 5": {"company": "Insulet", "category": "Insulin Pump"},
    "MiniMed 780G": {"company": "Medtronic", "category": "Insulin Pump"},
    
    # Cardiac Devices
    "TAVR": {"company": "Edwards Lifesciences", "category": "Heart Valve"},
    "SAPIEN": {"company": "Edwards Lifesciences", "category": "Heart Valve"},
    "MitraClip": {"company": "Abbott", "category": "Heart Valve"},
    "Watchman": {"company": "Boston Scientific", "category": "LAA Closure"},
    "Impella": {"company": "Abiomed", "category": "Heart Pump"},
    
    # Cancer Drugs
    "Keytruda": {"company": "Merck", "category": "Immunotherapy"},
    "Opdivo": {"company": "Bristol-Myers Squibb", "category": "Immunotherapy"},
    "Tecentriq": {"company": "Roche", "category": "Immunotherapy"},
    "Imfinzi": {"company": "AstraZeneca", "category": "Immunotherapy"},
    
    # GLP-1 Drugs
    "Ozempic": {"company": "Novo Nordisk", "category": "GLP-1"},
    "Wegovy": {"company": "Novo Nordisk", "category": "GLP-1"},
    "Mounjaro": {"company": "Eli Lilly", "category": "GLP-1"},
    "Trulicity": {"company": "Eli Lilly", "category": "GLP-1"},
    "Zepbound": {"company": "Eli Lilly", "category": "GLP-1"},
    
    # Other Major Drugs
    "Humira": {"company": "AbbVie", "category": "Immunology"},
    "Eliquis": {"company": "Bristol-Myers Squibb", "category": "Anticoagulant"},
    "Dupixent": {"company": "Sanofi", "category": "Immunology"},
    "Skyrizi": {"company": "AbbVie", "category": "Immunology"},
    "Rinvoq": {"company": "AbbVie", "category": "Immunology"},
}

# Sentiment indicators
POSITIVE_INDICATORS = {
    "approved", "approval", "breakthrough", "success", "successful", "positive",
    "effective", "efficacy", "benefit", "improvement", "advance", "innovation",
    "promising", "milestone", "achievement", "growth", "expansion", "launch",
    "partnership", "collaboration", "investment", "acquisition", "deal"
}

NEGATIVE_INDICATORS = {
    "failed", "failure", "rejected", "recall", "warning", "adverse", "side effect",
    "lawsuit", "litigation", "investigation", "decline", "loss", "setback",
    "concern", "risk", "safety issue", "death", "injury", "complication"
}

# Relationship patterns
ACQUISITION_PATTERNS = [
    r"(\w+(?:\s+\w+)?)\s+(?:acquires?|acquired|to acquire|bought|purchases?)\s+(\w+(?:\s+\w+)?)",
    r"(\w+(?:\s+\w+)?)\s+(?:acquisition of|takeover of)\s+(\w+(?:\s+\w+)?)",
    r"(\w+(?:\s+\w+)?)\s+(?:completes?|announces?)\s+(?:acquisition|merger)\s+(?:of|with)\s+(\w+(?:\s+\w+)?)",
]

PARTNERSHIP_PATTERNS = [
    r"(\w+(?:\s+\w+)?)\s+(?:partners? with|partnering with|collaboration with)\s+(\w+(?:\s+\w+)?)",
    r"(\w+(?:\s+\w+)?)\s+(?:and)\s+(\w+(?:\s+\w+)?)\s+(?:announce|enter|sign)\s+(?:partnership|collaboration|agreement)",
]


class EnhancedEntityExtractor:
    """Enhanced entity extraction with confidence scoring and categorization"""
    
    def __init__(self):
        self.company_db = COMPANY_DATABASE
        self.product_db = PRODUCT_DATABASE
        self._build_lookup_tables()
    
    def _build_lookup_tables(self):
        """Build efficient lookup tables for entity matching"""
        # Company name to info mapping (including aliases)
        self.company_lookup: Dict[str, CompanyInfo] = {}
        for name, info in self.company_db.items():
            self.company_lookup[name.lower()] = info
            for alias in info.aliases:
                self.company_lookup[alias.lower()] = info
        
        # Product name lookup
        self.product_lookup: Dict[str, Dict[str, Any]] = {}
        for name, info in self.product_db.items():
            self.product_lookup[name.lower()] = {"name": name, **info}
    
    def _get_context(self, text: str, match_start: int, match_end: int, window: int = 100) -> str:
        """Extract context around a match"""
        start = max(0, match_start - window)
        end = min(len(text), match_end + window)
        context = text[start:end].strip()
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        return context
    
    def _analyze_sentiment(self, context: str) -> Sentiment:
        """Analyze sentiment of context"""
        context_lower = context.lower()
        
        positive_count = sum(1 for word in POSITIVE_INDICATORS if word in context_lower)
        negative_count = sum(1 for word in NEGATIVE_INDICATORS if word in context_lower)
        
        if positive_count > negative_count:
            return Sentiment.POSITIVE
        elif negative_count > positive_count:
            return Sentiment.NEGATIVE
        return Sentiment.NEUTRAL
    
    def _calculate_confidence(self, match_type: str, context: str, is_known: bool) -> float:
        """Calculate confidence score for an extraction"""
        base_confidence = 0.9 if is_known else 0.6
        
        # Boost confidence if in a relevant context
        context_lower = context.lower()
        if any(word in context_lower for word in ["announced", "reported", "said", "according to"]):
            base_confidence += 0.05
        
        # Reduce confidence for very short contexts
        if len(context) < 50:
            base_confidence -= 0.1
        
        return min(1.0, max(0.0, base_confidence))
    
    def extract_companies(self, text: str) -> List[ExtractedEntity]:
        """Extract companies with metadata"""
        if not text:
            return []
        
        text_lower = text.lower()
        entities: List[ExtractedEntity] = []
        seen: Set[str] = set()
        
        # Search for known companies
        for name_lower, info in self.company_lookup.items():
            if name_lower in text_lower and info.name not in seen:
                # Find exact position
                pattern = re.compile(r'\b' + re.escape(name_lower) + r'\b', re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    context = self._get_context(text, match.start(), match.end())
                    sentiment = self._analyze_sentiment(context)
                    confidence = self._calculate_confidence("company", context, True)
                    
                    entities.append(ExtractedEntity(
                        name=info.name,
                        entity_type="company",
                        confidence=confidence,
                        sector=info.sector.value,
                        ticker=info.ticker,
                        sentiment=sentiment,
                        context=context,
                        position=match.start()
                    ))
                    seen.add(info.name)
        
        # Search for company patterns (Inc., Corp., Ltd., etc.)
        company_pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:Inc\.?|Corp\.?|Ltd\.?|LLC|Pharmaceuticals?|Therapeutics?|Medical|Healthcare)\b'
        for match in re.finditer(company_pattern, text):
            name = match.group(1).strip()
            if name not in seen and len(name) > 3:
                context = self._get_context(text, match.start(), match.end())
                sentiment = self._analyze_sentiment(context)
                confidence = self._calculate_confidence("company", context, False)
                
                entities.append(ExtractedEntity(
                    name=name,
                    entity_type="company",
                    confidence=confidence,
                    sector=None,
                    ticker=None,
                    sentiment=sentiment,
                    context=context,
                    position=match.start()
                ))
                seen.add(name)
        
        return sorted(entities, key=lambda x: x.confidence, reverse=True)
    
    def extract_products(self, text: str) -> List[ExtractedEntity]:
        """Extract products with metadata"""
        if not text:
            return []
        
        text_lower = text.lower()
        entities: List[ExtractedEntity] = []
        seen: Set[str] = set()
        
        # Search for known products
        for name_lower, info in self.product_lookup.items():
            if name_lower in text_lower and info["name"] not in seen:
                pattern = re.compile(r'\b' + re.escape(name_lower) + r'\b', re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    context = self._get_context(text, match.start(), match.end())
                    sentiment = self._analyze_sentiment(context)
                    confidence = self._calculate_confidence("product", context, True)
                    
                    entities.append(ExtractedEntity(
                        name=info["name"],
                        entity_type="product",
                        confidence=confidence,
                        sector=info.get("category"),
                        ticker=None,
                        sentiment=sentiment,
                        context=context,
                        position=match.start()
                    ))
                    seen.add(info["name"])
        
        # Search for drug name patterns
        drug_suffixes = ['mab', 'nib', 'lib', 'tinib', 'zumab', 'ximab', 'tide', 'glutide']
        for suffix in drug_suffixes:
            pattern = rf'\b([A-Z][a-z]+{suffix})\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).title()
                if name not in seen:
                    context = self._get_context(text, match.start(), match.end())
                    sentiment = self._analyze_sentiment(context)
                    confidence = self._calculate_confidence("product", context, False)
                    
                    entities.append(ExtractedEntity(
                        name=name,
                        entity_type="product",
                        confidence=confidence,
                        sector="Drug",
                        ticker=None,
                        sentiment=sentiment,
                        context=context,
                        position=match.start()
                    ))
                    seen.add(name)
        
        return sorted(entities, key=lambda x: x.confidence, reverse=True)
    
    def extract_relationships(self, text: str) -> List[Relationship]:
        """Extract relationships between entities"""
        relationships: List[Relationship] = []
        
        # Check acquisition patterns
        for pattern in ACQUISITION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity1 = match.group(1).strip()
                entity2 = match.group(2).strip()
                if len(entity1) > 2 and len(entity2) > 2:
                    context = self._get_context(text, match.start(), match.end())
                    relationships.append(Relationship(
                        entity1=entity1,
                        entity2=entity2,
                        relationship_type="acquisition",
                        confidence=0.8,
                        context=context
                    ))
        
        # Check partnership patterns
        for pattern in PARTNERSHIP_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity1 = match.group(1).strip()
                entity2 = match.group(2).strip()
                if len(entity1) > 2 and len(entity2) > 2:
                    context = self._get_context(text, match.start(), match.end())
                    relationships.append(Relationship(
                        entity1=entity1,
                        entity2=entity2,
                        relationship_type="partnership",
                        confidence=0.75,
                        context=context
                    ))
        
        return relationships
    
    def extract_all(self, text: str) -> Dict[str, Any]:
        """Extract all entities and relationships from text"""
        companies = self.extract_companies(text)
        products = self.extract_products(text)
        relationships = self.extract_relationships(text)
        
        return {
            "companies": [e.to_dict() for e in companies],
            "products": [e.to_dict() for e in products],
            "relationships": [r.to_dict() for r in relationships],
            "summary": {
                "company_count": len(companies),
                "product_count": len(products),
                "relationship_count": len(relationships),
                "sectors": list(set(e.sector for e in companies if e.sector)),
                "avg_confidence": round(
                    sum(e.confidence for e in companies + products) / max(1, len(companies) + len(products)),
                    2
                )
            }
        }


def enrich_article_v2(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich an article with enhanced entity extraction.
    
    Args:
        article: Article dict with 'title' and 'summary' fields
    
    Returns:
        Article dict with added entity information
    """
    extractor = EnhancedEntityExtractor()
    text = f"{article.get('title', '')} {article.get('summary', '')}"
    
    extraction = extractor.extract_all(text)
    
    article['entities'] = extraction
    article['companies'] = [e['name'] for e in extraction['companies']]
    article['products'] = [e['name'] for e in extraction['products']]
    
    return article


def enrich_articles_v2(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich a list of articles with enhanced entity extraction.
    
    Args:
        articles: List of article dicts
    
    Returns:
        List of enriched article dicts
    """
    extractor = EnhancedEntityExtractor()
    
    for article in articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}"
        extraction = extractor.extract_all(text)
        
        article['entities'] = extraction
        article['companies'] = [e['name'] for e in extraction['companies']]
        article['products'] = [e['name'] for e in extraction['products']]
    
    return articles


# Utility functions for API endpoints
def get_entity_statistics(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get aggregated entity statistics from a list of articles.
    
    Returns:
        Dict with top companies, products, sectors, and trends
    """
    company_mentions: Dict[str, int] = defaultdict(int)
    product_mentions: Dict[str, int] = defaultdict(int)
    sector_counts: Dict[str, int] = defaultdict(int)
    company_sentiments: Dict[str, List[str]] = defaultdict(list)
    
    for article in articles:
        entities = article.get('entities', {})
        
        for company in entities.get('companies', []):
            company_mentions[company['name']] += 1
            if company.get('sector'):
                sector_counts[company['sector']] += 1
            company_sentiments[company['name']].append(company.get('sentiment', 'neutral'))
        
        for product in entities.get('products', []):
            product_mentions[product['name']] += 1
    
    # Calculate sentiment averages
    def sentiment_score(sentiments: List[str]) -> float:
        scores = {'positive': 1, 'neutral': 0, 'negative': -1}
        return sum(scores.get(s, 0) for s in sentiments) / max(1, len(sentiments))
    
    top_companies = [
        {
            "name": name,
            "mentions": count,
            "sentiment_avg": round(sentiment_score(company_sentiments[name]), 2)
        }
        for name, count in sorted(company_mentions.items(), key=lambda x: x[1], reverse=True)[:20]
    ]
    
    top_products = [
        {"name": name, "mentions": count}
        for name, count in sorted(product_mentions.items(), key=lambda x: x[1], reverse=True)[:20]
    ]
    
    return {
        "top_companies": top_companies,
        "top_products": top_products,
        "sector_breakdown": dict(sector_counts),
        "total_companies": len(company_mentions),
        "total_products": len(product_mentions)
    }


# Example usage
if __name__ == "__main__":
    # Test extraction
    test_text = """
    Pfizer announced today that the FDA has approved Keytruda for a new indication. 
    The drug, developed in partnership with Merck, showed promising results in clinical trials.
    Meanwhile, Intuitive Surgical reported strong sales of its da Vinci Xi surgical robot system.
    Johnson & Johnson is acquiring a small biotech company to expand its oncology portfolio.
    """
    
    extractor = EnhancedEntityExtractor()
    results = extractor.extract_all(test_text)
    
    print("Companies found:")
    for company in results['companies']:
        print(f"  - {company['name']} ({company['sector']}) - {company['ticker']} - Confidence: {company['confidence']}")
    
    print("\nProducts found:")
    for product in results['products']:
        print(f"  - {product['name']} ({product['sector']}) - Confidence: {product['confidence']}")
    
    print("\nRelationships found:")
    for rel in results['relationships']:
        print(f"  - {rel['entity1']} -> {rel['type']} -> {rel['entity2']}")
