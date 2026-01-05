"""
Entity Extractor - Extracts companies and products from medical news articles.

Uses a combination of:
1. Known medical/healthcare company database
2. Pattern matching for company indicators (Inc., Corp., Ltd., etc.)
3. Product name patterns (drug names, device names)
4. Context-aware extraction
"""

import re
import logging
from typing import List, Dict, Set, Any

logger = logging.getLogger(__name__)

# Major medical/healthcare companies database
KNOWN_COMPANIES: Set[str] = {
    # Big Pharma
    "Pfizer", "Johnson & Johnson", "J&J", "Merck", "AbbVie", "Novartis",
    "Roche", "Bristol-Myers Squibb", "BMS", "Eli Lilly", "Lilly", "AstraZeneca",
    "Sanofi", "GlaxoSmithKline", "GSK", "Gilead", "Amgen", "Regeneron",
    "Moderna", "BioNTech", "Vertex", "Biogen", "Takeda", "Bayer",
    "Boehringer Ingelheim", "Novo Nordisk", "Teva", "Allergan", "Celgene",

    # Medical Devices
    "Medtronic", "Abbott", "Abbott Laboratories", "Boston Scientific",
    "Stryker", "Becton Dickinson", "BD", "Edwards Lifesciences",
    "Intuitive Surgical", "Zimmer Biomet", "Smith & Nephew",
    "Baxter", "Dexcom", "ResMed", "Hologic", "Align Technology",
    "DePuy Synthes", "Philips", "Siemens Healthineers", "GE Healthcare",
    "Medela", "Terumo", "Olympus", "Cardinal Health", "McKesson",

    # Surgical Robotics
    "Intuitive", "da Vinci", "Mako", "ROSA", "Mazor", "Verb Surgical",
    "CMR Surgical", "Versius", "Hugo", "Senhance", "TransEnterix",
    "Auris Health", "Vicarious Surgical", "Asensus Surgical",

    # Diagnostics & Labs
    "Quest Diagnostics", "LabCorp", "Labcorp", "Exact Sciences",
    "Illumina", "Thermo Fisher", "Roche Diagnostics", "Bio-Rad",
    "Qiagen", "Cepheid", "Hologic", "Beckman Coulter", "Sysmex",

    # Digital Health / Health Tech
    "Epic", "Cerner", "Oracle Health", "Athenahealth", "Teladoc",
    "Livongo", "Omada Health", "Noom", "Fitbit", "Apple Health",
    "Google Health", "Amazon Health", "CVS Health", "Walgreens",
    "UnitedHealth", "Anthem", "Cigna", "Humana", "Aetna",

    # Diabetes Technology
    "Insulet", "Tandem Diabetes", "Tandem", "Omnipod", "Dexcom",
    "Abbott FreeStyle", "Medtronic Diabetes", "Beta Bionics",

    # Neuromodulation / Pain Management
    "Nevro", "Axonics", "Boston Scientific Neuromodulation",
    "Abbott Neuromodulation", "Medtronic Neuromodulation",

    # Orthopedics
    "Zimmer", "Biomet", "DePuy", "Synthes", "Stryker Orthopaedics",
    "Smith+Nephew", "Arthrex", "NuVasive", "Globus Medical",
    "Orthofix", "Wright Medical", "Exactech",

    # Cardiovascular
    "Edwards", "Medtronic Cardiac", "Abbott Vascular", "Boston Scientific Cardiac",
    "Biotronik", "LivaNova", "AtriCure", "Spectranetics",

    # Healthcare Systems
    "HCA Healthcare", "CommonSpirit", "Ascension", "Trinity Health",
    "Providence", "Tenet Healthcare", "Community Health Systems",
    "Universal Health Services", "Mayo Clinic", "Cleveland Clinic",
    "Johns Hopkins", "Mass General", "Kaiser Permanente",
}

# Product patterns and known products
KNOWN_PRODUCTS: Set[str] = {
    # Surgical Robots
    "da Vinci", "da Vinci Xi", "da Vinci SP", "da Vinci 5",
    "Mako", "Mako SmartRobotics", "ROSA", "ROSA Knee", "ROSA Hip",
    "Hugo RAS", "Versius", "Ion", "Monarch",

    # Diabetes Devices
    "FreeStyle Libre", "Libre 2", "Libre 3", "Dexcom G6", "Dexcom G7",
    "Dexcom Stelo", "Omnipod 5", "t:slim X2", "MiniMed 780G",
    "Control-IQ", "Loop", "iLet Bionic Pancreas",

    # Cardiac Devices
    "TAVR", "MitraClip", "Watchman", "SAPIEN", "Evolut",
    "HeartMate", "CardioMEMS", "Impella", "ECMO",

    # Neuromodulation
    "HFX", "Intellis", "Proclaim", "Spectra", "Precision",
    "Senza", "Omnia", "WaveWriter",

    # Orthopedic Implants
    "ATTUNE", "JOURNEY", "LEGION", "Triathlon", "Persona",
    "Sigma", "Genesis II", "Oxford", "MAKO TKA",

    # Cancer Drugs
    "Keytruda", "Opdivo", "Tecentriq", "Imfinzi", "Yervoy",
    "Ibrance", "Tagrisso", "Lynparza", "Darzalex", "Revlimid",

    # Other Major Drugs
    "Humira", "Eliquis", "Ozempic", "Wegovy", "Mounjaro",
    "Trulicity", "Jardiance", "Entresto", "Xarelto", "Eylea",
    "Dupixent", "Stelara", "Skyrizi", "Rinvoq", "Tremfya",
}

# Common false positives to filter out
FALSE_POSITIVES: Set[str] = {
    'The', 'A', 'An', 'In', 'On', 'For', 'And', 'Or', 'But', 'With',
    'New', 'Study', 'Research', 'Trial', 'Results', 'Data', 'Health',
    'Medical', 'Clinical', 'Patient', 'Patients', 'Treatment', 'FDA', 'WHO', 'CDC', 'NIH',
    # Short words that match too many things
    'Ion', 'ion', 'Loop', 'loop', 'ROSA', 'Hugo', 'Mako', 'Epic'
}

# Drug name suffix patterns
DRUG_SUFFIXES = [
    'mab', 'nib', 'lib', 'tinib', 'zumab', 'ximab', 'tide', 'glutide',
    'parib', 'ciclib', 'vir', 'navir', 'previr', 'buvir', 'statin', 'pril', 'sartan', 'olol'
]


def _find_known_entities(text: str, text_lower: str, known_set: Set[str]) -> Set[str]:
    """Find known entities in text using word boundaries."""
    found: Set[str] = set()
    for entity in known_set:
        # Skip very short entities (3 chars or less) - too many false positives
        if len(entity) <= 3:
            continue
        if entity.lower() in text_lower:
            # Use word boundaries to avoid matching substrings
            pattern = re.compile(r'\b' + re.escape(entity) + r'\b', re.IGNORECASE)
            match = pattern.search(text)
            if match:
                found.add(match.group())
    return found


def _find_drug_names(text: str) -> Set[str]:
    """Find drug names based on common suffixes."""
    found: Set[str] = set()
    for suffix in DRUG_SUFFIXES:
        pattern = rf'\b([A-Z][a-z]+{suffix})\b'
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            found.add(match.title())
    return found


def _find_fda_approved(text: str) -> Set[str]:
    """Find FDA-approved products."""
    found: Set[str] = set()
    pattern = r'FDA\s+(?:approved?|cleared?|authorized?)\s+([A-Z][a-zA-Z0-9\s\-]+?)(?:\s+for|\s+to|\s+as|,|\.)'
    matches = re.findall(pattern, text)
    for match in matches:
        clean = match.strip()
        if 2 < len(clean) < 50:
            found.add(clean)
    return found


def _find_acquisitions(text: str) -> Set[str]:
    """Find companies mentioned in acquisition/partnership context."""
    found: Set[str] = set()
    pattern = r'([A-Z][a-zA-Z\s&]+?)\s+(?:acquires?|acquired|to acquire|bought|purchases?|partners? with)'
    matches = re.findall(pattern, text)
    for match in matches:
        clean = match.strip()
        if 2 < len(clean) < 40:
            found.add(clean)
    return found


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract companies and products from text.

    Args:
        text: The text to analyze (title + summary)

    Returns:
        Dict with 'companies' and 'products' lists
    """
    if not text:
        return {"companies": [], "products": []}

    text_lower = text.lower()

    # Find companies
    companies: Set[str] = set()
    companies.update(_find_known_entities(text, text_lower, KNOWN_COMPANIES))
    companies.update(_find_acquisitions(text))

    # Find products
    products: Set[str] = set()
    products.update(_find_known_entities(text, text_lower, KNOWN_PRODUCTS))
    products.update(_find_drug_names(text))
    products.update(_find_fda_approved(text))

    # Clean up results - remove false positives
    companies = {c for c in companies if c not in FALSE_POSITIVES and len(c) > 1}
    products = {p for p in products if p not in FALSE_POSITIVES and len(p) > 1}

    return {
        "companies": sorted(list(companies)),
        "products": sorted(list(products))
    }


def enrich_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich an article with extracted entities.

    Args:
        article: Article dict with 'title' and 'summary' fields

    Returns:
        Article dict with added 'companies' and 'products' fields
    """
    text = f"{article.get('title', '')} {article.get('summary', '')}"
    entities = extract_entities(text)
    article['companies'] = entities['companies']
    article['products'] = entities['products']
    return article


def enrich_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich a list of articles with extracted entities.

    Args:
        articles: List of article dicts

    Returns:
        List of enriched article dicts
    """
    return [enrich_article(article) for article in articles]
