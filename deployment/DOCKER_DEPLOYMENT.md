# PoliSim Docker Deployment Guide
# Phase 5.3: Production Deployment Infrastructure

## Table of Contents
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### Development Setup (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/GalacticOrgOfDev/polisim.git
cd polisim

# 2. Copy environment variables
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Wait for services to be healthy (30-60 seconds)
docker-compose ps

# 5. Access services
# API: http://localhost:5000
# Dashboard: http://localhost:8501
# PostgreSQL: localhost:5432
# Redis: localhost:6379
```

### Verify Installation

```bash
# Check API health
curl http://localhost:5000/api/health

# Expected response:
# {"status": "healthy", "version": "1.0.0", "timestamp": "2025-12-26T10:30:00"}

# Check dashboard
curl http://localhost:8501/_stcore/health

# Expected response: HTTP 200
```

---

## Development Setup

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis

# View logs
docker-compose logs -f api
docker-compose logs -f dashboard

# Stop services
docker-compose down

# Stop and remove volumes (DELETES DATA)
docker-compose down -v
```

### Hot Reloading (Development Mode)

The docker-compose.yml includes volume mounts for hot reloading:

```yaml
volumes:
  - ./core:/app/core  # Code changes auto-reload
  - ./api:/app/api
  - ./ui:/app/ui
```

Changes to Python files will automatically reload the services.

### Database Migrations

```bash
# Enter API container
docker-compose exec api bash

# Run migrations (if using Alembic)
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new table"
```

### Running Tests

```bash
# Run all tests in Docker
docker-compose exec api pytest tests/ -v

# Run specific test file
docker-compose exec api pytest tests/test_cbo_integration.py -v

# Run with coverage
docker-compose exec api pytest tests/ --cov=core --cov-report=html
```

---

## Production Deployment

### 1. Environment Configuration

**Edit `.env` file with production values:**

```bash
# Generate secure secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env
POLISIM_ENV=production
FLASK_ENV=production
JWT_SECRET_KEY=<generated_secret>
POSTGRES_PASSWORD=<strong_password>
REDIS_PASSWORD=<strong_password>
CORS_ORIGINS=https://yourdomain.com
```

### 2. SSL/TLS Certificates

**Option A: Let's Encrypt (Recommended)**

```bash
# Install Certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d polisim.example.com

# Copy certificates
sudo cp /etc/letsencrypt/live/polisim.example.com/fullchain.pem deployment/ssl/cert.pem
sudo cp /etc/letsencrypt/live/polisim.example.com/privkey.pem deployment/ssl/key.pem
```

**Option B: Self-Signed (Development/Testing)**

```bash
# Generate self-signed certificate
mkdir -p deployment/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deployment/ssl/key.pem \
  -out deployment/ssl/cert.pem \
  -subj "/CN=polisim.local"
```

### 3. Start Production Stack

```bash
# Build images
docker-compose build --no-cache

# Start with Nginx reverse proxy
docker-compose --profile production up -d

# Verify all services healthy
docker-compose ps
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec api python -c "from api.database import init_database; init_database()"

# Create admin user
docker-compose exec api python scripts/create_admin_user.py \
  --email admin@yourdomain.com \
  --username admin \
  --password <secure_password>
```

### 5. Configure Firewall

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block direct access to services
sudo ufw deny 5000/tcp
sudo ufw deny 8501/tcp
sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp
```

---

## Configuration

### Docker Compose Profiles

**Development Profile (default):**
- API server (exposed port 5000)
- Dashboard (exposed port 8501)
- PostgreSQL (exposed port 5432)
- Redis (exposed port 6379)

**Production Profile:**
```bash
docker-compose --profile production up -d
```
- All dev services
- Nginx reverse proxy (ports 80, 443)
- No direct port exposure

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://polisim:...` | Yes |
| `REDIS_URL` | Redis connection string | `redis://:...@redis:6379/0` | Yes |
| `JWT_SECRET_KEY` | JWT signing secret | `dev_secret_...` | Yes |
| `JWT_EXPIRATION_HOURS` | JWT token lifetime | `24` | No |
| `API_RATE_LIMIT` | Requests per hour | `1000` | No |
| `CORS_ORIGINS` | Allowed origins | `http://localhost:8501` | Yes |
| `POLISIM_ENV` | Environment | `development` | No |

### Health Checks

All services include health checks:

```bash
# Check all service health
docker-compose ps

# Manual health check
curl http://localhost/health  # Nginx
curl http://localhost:5000/api/health  # API
curl http://localhost:8501/_stcore/health  # Dashboard
```

---

## Monitoring

### Container Logs

```bash
# View logs for all services
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f dashboard
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 api
```

### Resource Usage

```bash
# Monitor resource usage
docker stats

# Output:
# CONTAINER          CPU %   MEM USAGE / LIMIT     MEM %   NET I/O
# polisim-api        2.5%    512MiB / 4GiB         12.8%   1.2kB / 850B
# polisim-dashboard  1.2%    256MiB / 4GiB         6.4%    800B / 500B
```

### PostgreSQL Monitoring

```bash
# Enter PostgreSQL container
docker-compose exec postgres psql -U polisim

# Check database size
SELECT pg_size_pretty(pg_database_size('polisim'));

# Active connections
SELECT count(*) FROM pg_stat_activity;

# Slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### Redis Monitoring

```bash
# Enter Redis CLI
docker-compose exec redis redis-cli -a <REDIS_PASSWORD>

# Check memory usage
INFO memory

# Monitor commands in real-time
MONITOR

# Check cache hit rate
INFO stats
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
docker-compose logs api
docker-compose logs postgres
```

**Common issues:**
- Port already in use: Change port in docker-compose.yml
- Database connection failed: Check DATABASE_URL in .env
- Permission denied: Check file permissions, run as non-root user

### Database Connection Errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres pg_isready -U polisim

# Reset database
docker-compose down -v postgres
docker-compose up -d postgres
```

### Redis Connection Errors

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli -a <PASSWORD> ping

# Expected: PONG
```

### API Returns 500 Errors

```bash
# Check API logs
docker-compose logs -f api

# Check database migrations
docker-compose exec api alembic current

# Restart API
docker-compose restart api
```

### Dashboard Won't Load

```bash
# Check dashboard logs
docker-compose logs -f dashboard

# Verify API connection
docker-compose exec dashboard curl http://api:5000/api/health

# Restart dashboard
docker-compose restart dashboard
```

### Nginx 502 Bad Gateway

```bash
# Check upstream services
docker-compose ps api dashboard

# Check Nginx logs
docker-compose logs nginx

# Test upstream connection
docker-compose exec nginx curl http://api:5000/api/health
docker-compose exec nginx curl http://dashboard:8501/_stcore/health
```

### Performance Issues

**Increase resources in docker-compose.yml:**

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

**Scale services:**

```bash
# Run multiple API workers
docker-compose up -d --scale api=3
```

---

## Backup & Restore

### PostgreSQL Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U polisim polisim > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20251226.sql | docker-compose exec -T postgres psql -U polisim polisim
```

### Redis Backup

```bash
# Backup Redis data
docker-compose exec redis redis-cli -a <PASSWORD> SAVE

# Copy RDB file
docker cp polisim-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

### Volume Backup

```bash
# Backup volumes
docker run --rm \
  -v polisim_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz -C /data .
```

---

## Scaling

### Horizontal Scaling (Multiple API Instances)

```bash
# Run 3 API instances behind Nginx load balancer
docker-compose up -d --scale api=3

# Nginx will automatically load balance requests
```

### Vertical Scaling (More Resources)

Edit `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
```

---

## Security Best Practices

1. **Change default passwords** in `.env`
2. **Use SSL/TLS** in production (Let's Encrypt)
3. **Enable firewall** to block direct service access
4. **Regular security updates**: `docker-compose pull && docker-compose up -d`
5. **Limit container privileges**: Non-root users in Dockerfiles
6. **Scan images**: `docker scan polisim-api`
7. **Monitor logs** for suspicious activity
8. **Rate limiting**: Configured in Nginx (10 req/s API, 5 req/s dashboard)

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push images
        run: |
          docker build -t polisim-api:latest .
          docker build -f Dockerfile.dashboard -t polisim-dashboard:latest .
          
      - name: Deploy to server
        run: |
          ssh user@server "cd /app/polisim && \
            docker-compose pull && \
            docker-compose up -d --no-deps api dashboard"
```

---

## Support

**Issues:** https://github.com/GalacticOrgOfDev/polisim/issues  
**Documentation:** `documentation/` directory  
**Email:** galacticorgofdev@gmail.com

---

**Last Updated:** December 26, 2025  
**Phase:** 5.3 - Deployment Infrastructure  
**Status:** ✅ Complete
