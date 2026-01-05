# Deployment Guide - Medical News Feed Scraper

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Local Development

### Prerequisites

- Python 3.11+
- pip and virtualenv
- Git

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd news-feed-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment configuration
cp .env.example .env

# Run tests
pytest tests/ -v --cov

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points

- **Web UI:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Build and Run

```bash
# Build the Docker image
docker build -t news-feed-scraper:latest .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Docker Configuration

The `docker-compose.yml` includes:
- **App Service:** FastAPI application
- **Redis Service:** Caching layer
- **Health Checks:** Automatic health monitoring
- **Volumes:** Persistent data storage

### Environment Variables

Create a `.env` file in the project root:

```bash
LOG_LEVEL=INFO
TIMEOUT_SECONDS=20
MAX_RETRIES=2
CONCURRENT_REQUESTS=10
REFRESH_INTERVAL_SEC=900
REDIS_HOST=redis
REDIS_PORT=6379
```

---

## Production Deployment

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: news-feed-scraper
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: news-feed-scraper
  template:
    metadata:
      labels:
        app: news-feed-scraper
    spec:
      containers:
      - name: app
        image: news-feed-scraper:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: REDIS_HOST
          value: "redis-service"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: news-feed-scraper-service
spec:
  selector:
    app: news-feed-scraper
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Deploy to Kubernetes

```bash
# Apply deployment
kubectl apply -f deployment.yaml

# Check status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/news-feed-scraper

# Scale deployment
kubectl scale deployment news-feed-scraper --replicas=5
```

### AWS ECS Deployment

```bash
# Create ECR repository
aws ecr create-repository --repository-name news-feed-scraper

# Build and push image
docker build -t news-feed-scraper:latest .
docker tag news-feed-scraper:latest <aws-account-id>.dkr.ecr.<region>.amazonaws.com/news-feed-scraper:latest
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<region>.amazonaws.com
docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/news-feed-scraper:latest

# Create ECS task definition and service
# (Use AWS Console or AWS CLI)
```

### Nginx Reverse Proxy

```nginx
upstream news_feed_backend {
    server app:8000;
}

server {
    listen 80;
    server_name news-feed.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name news-feed.example.com;

    ssl_certificate /etc/ssl/certs/certificate.crt;
    ssl_certificate_key /etc/ssl/private/private.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/m;
    limit_req zone=api_limit burst=60 nodelay;

    location / {
        proxy_pass http://news_feed_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }

    location /health {
        proxy_pass http://news_feed_backend;
        access_log off;
    }
}
```

---

## Monitoring and Maintenance

### Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "last_refresh": 1735824123.45,
  "last_refresh_iso": "2026-01-02T12:35:23.450000",
  "sites_configured": 76,
  "sites_with_articles": 45,
  "total_articles": 1234,
  "version": "2.0.0",
  "refresh_interval_sec": 900
}
```

### Logging

Logs are stored in:
- **Console:** Real-time output
- **File:** `/app/logs/news-feed-scraper.log` (if configured)

View logs:

```bash
# Docker
docker-compose logs -f app

# Kubernetes
kubectl logs -f deployment/news-feed-scraper

# Local
tail -f logs/news-feed-scraper.log
```

### Metrics

Access metrics at: `http://localhost:8000/metrics` (if Prometheus enabled)

### Backup and Recovery

```bash
# Backup Redis data
docker exec redis-container redis-cli BGSAVE

# Backup configuration
cp sites.yaml sites.yaml.backup

# Restore from backup
docker cp sites.yaml.backup redis-container:/data/dump.rdb
```

### Scaling

```bash
# Docker Compose - scale services
docker-compose up -d --scale app=3

# Kubernetes - scale replicas
kubectl scale deployment news-feed-scraper --replicas=5

# Monitor resource usage
kubectl top nodes
kubectl top pods
```

### Updates and Rollbacks

```bash
# Update image
docker pull news-feed-scraper:latest
docker-compose up -d

# Rollback to previous version
docker-compose down
docker run -d news-feed-scraper:previous-version

# Kubernetes rolling update
kubectl set image deployment/news-feed-scraper \
  app=news-feed-scraper:new-version \
  --record

# Rollback Kubernetes deployment
kubectl rollout undo deployment/news-feed-scraper
```

---

## Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs app

# Verify configuration
cat .env

# Check port availability
lsof -i :8000
```

### High memory usage

```bash
# Check cache size
curl http://localhost:8000/health | grep articles

# Clear cache
# (Implement cache clearing endpoint)

# Reduce concurrent requests
# Edit .env: CONCURRENT_REQUESTS=5
```

### Slow response times

```bash
# Check refresh status
curl http://localhost:8000/health

# Monitor metrics
# (If Prometheus enabled)

# Increase timeout
# Edit .env: TIMEOUT_SECONDS=30
```

### Feed parsing errors

```bash
# Check site configuration
cat sites.yaml

# Test individual feed
curl -I https://example.com/feed.xml

# Check logs for specific site
docker-compose logs app | grep "site-name"
```

---

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Set strong environment variables
- [ ] Enable rate limiting
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Implement authentication if needed
- [ ] Use secrets management (e.g., AWS Secrets Manager)
- [ ] Regular backups
- [ ] Incident response plan

---

## Performance Optimization

### Caching

```bash
# Enable Redis caching
# (Already configured in docker-compose.yml)

# Monitor cache hit rate
# (Implement cache metrics)
```

### Database Optimization

```bash
# For PostgreSQL (if added):
# - Create indexes on frequently queried columns
# - Implement query optimization
# - Regular VACUUM and ANALYZE
```

### Load Balancing

```bash
# Use Nginx or HAProxy for load balancing
# - Round-robin distribution
# - Health check monitoring
# - Session persistence (if needed)
```

---

## Support and Documentation

- **API Documentation:** http://localhost:8000/docs
- **GitHub Issues:** [Project Repository]
- **Email Support:** support@example.com

---

**Last Updated:** January 5, 2026
