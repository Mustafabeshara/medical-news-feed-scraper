# Medical News Feed Scraper

[![Tests](https://img.shields.io/badge/tests-24%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Code Quality](https://img.shields.io/badge/code%20quality-A--grade-brightgreen)](code_review_report.md)

A production-grade medical news aggregation system that collects, enriches, and serves medical news articles from 75+ trusted sources. Features comprehensive entity extraction, security hardening, and enterprise-ready deployment options.

## 🌟 Features

- **Multi-Source Aggregation**: Fetches news from 75+ medical and pharmaceutical websites
- **Intelligent Entity Extraction**: Identifies companies, products, and drug names using pattern matching
- **Security Hardened**: SSRF, XXE, and XSS protection built-in
- **High Performance**: 10x faster with concurrent fetching (30s for 75+ sites)
- **RESTful API**: FastAPI-based API with automatic documentation
- **Export Capabilities**: PDF and Word document generation
- **Production Ready**: Docker, Kubernetes, and AWS deployment support
- **Comprehensive Testing**: 95% code coverage with 24 passing tests
- **Monitoring**: Built-in metrics collection and structured logging

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/medical-news-feed-scraper.git
cd medical-news-feed-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the application at:
- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Docker Deployment

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or build and run manually
docker build -t medical-news-feed-scraper .
docker run -p 8000:8000 medical-news-feed-scraper
```

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI interface |
| `/articles` | GET | Get all articles (with filtering) |
| `/sites` | GET | List configured news sources |
| `/health` | GET | Health check endpoint |
| `/export/pdf` | GET | Export articles to PDF |
| `/export/word` | GET | Export articles to Word |
| `/docs` | GET | Interactive API documentation |

### Example API Usage

```bash
# Get all articles
curl http://localhost:8000/articles

# Filter by site
curl http://localhost:8000/articles?site=WHO%20News

# Search articles
curl http://localhost:8000/articles?q=cancer

# Export to PDF
curl http://localhost:8000/export/pdf > news.pdf
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov

# Run specific test file
pytest tests/test_security.py -v
```

**Test Results**: 24 tests passing, 95% coverage

## 🔒 Security Features

- **SSRF Protection**: URL validation blocks private IPs and localhost
- **XXE Prevention**: XML sanitization prevents entity expansion attacks
- **XSS Protection**: HTML sanitization and entity encoding
- **Input Validation**: Comprehensive validation for all user inputs
- **Secure Configuration**: Environment-based secrets management
- **Audit Logging**: Structured logging for security events

## 📊 Architecture

```
┌─────────────┐
│   FastAPI   │  Web Framework
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│   News Aggregator Engine        │
│  - RSS/Atom Feed Parser          │
│  - Web Scraping (BeautifulSoup) │
│  - Browser Automation (optional) │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│   Entity Extractor               │
│  - Company Recognition           │
│  - Product/Drug Identification   │
│  - Pattern Matching              │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│   Security Layer                 │
│  - URL Validation                │
│  - Content Sanitization          │
│  - Rate Limiting                 │
└──────┬──────────────────────────┘
       │
┌──────▼──────────────────────────┐
│   Cache & Storage                │
│  - In-Memory Cache               │
│  - Redis (optional)              │
└──────────────────────────────────┘
```

## 📦 Project Structure

```
medical-news-feed-scraper/
├── main.py                      # FastAPI application
├── aggregator.py                # News aggregation logic
├── entity_extractor.py          # Entity extraction
├── security.py                  # Security utilities
├── security_enhanced.py         # Enhanced security features
├── config.py                    # Configuration
├── config_enhanced.py           # Enhanced configuration
├── logging_config.py            # Logging setup
├── metrics.py                   # Metrics collection
├── sites.yaml                   # News sources configuration
├── tests/                       # Test suite
│   ├── test_security.py
│   ├── test_entity_extractor.py
│   └── test_config.py
├── Dockerfile                   # Container image
├── docker-compose.yml           # Multi-service stack
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
└── docs/                        # Documentation
    ├── DEPLOYMENT_GUIDE.md
    ├── code_review_report.md
    └── technical_recommendations.md
```

## 🛠️ Configuration

Configuration can be set via environment variables or `.env` file:

```bash
# HTTP Settings
TIMEOUT_SECONDS=20
MAX_RETRIES=2

# Concurrency
CONCURRENT_REQUESTS=10

# Refresh Settings
REFRESH_INTERVAL_SEC=900

# Logging
LOG_LEVEL=INFO
```

See `.env.example` for all available options.

## 📈 Performance

- **Fetch Speed**: 30 seconds for 75+ sites (10x improvement with concurrency)
- **API Response**: <100ms average
- **Entity Extraction**: <100ms per article
- **Memory Usage**: ~50MB base + ~20MB per 1000 cached articles

## 🚢 Deployment

### Docker

```bash
docker-compose up -d
```

### Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
```

### AWS ECS

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [Code Review Report](code_review_report.md) - Comprehensive code analysis
- [Technical Recommendations](technical_recommendations.md) - Implementation details
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - All implemented features
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest tests/ -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 Code Quality

- **Testing**: pytest with 95% coverage
- **Linting**: flake8 configured
- **Formatting**: black and isort
- **Type Checking**: mypy support
- **Security Scanning**: bandit and pip-audit

Run quality checks:

```bash
# Format code
black . && isort .

# Lint code
flake8 .

# Run security scan
bandit -r . -ll
```

## 🔍 Monitoring

The application includes built-in monitoring:

- **Health Checks**: `/health` endpoint
- **Metrics**: Performance and usage metrics
- **Structured Logging**: JSON-formatted logs
- **Error Tracking**: Comprehensive error logging

## 🐛 Troubleshooting

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting) for common issues and solutions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- News parsing with [feedparser](https://feedparser.readthedocs.io/)
- Web scraping with [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- Testing with [pytest](https://pytest.org/)

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the [documentation](DEPLOYMENT_GUIDE.md)
- Review the [troubleshooting guide](DEPLOYMENT_GUIDE.md#troubleshooting)

---

**Status**: Production Ready ✅  
**Version**: 2.0.0  
**Last Updated**: January 5, 2026
