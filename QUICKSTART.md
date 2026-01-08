# 🚀 Quick Start Guide
# ML-Enabled WAF Anomaly Detection System

## Prerequisites
- Python 3.9+
- Redis (optional, for production)
- PostgreSQL (optional, for production)

## Installation Steps

### 1. Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Train Models with Dataset1
```powershell
python src\ml\train.py --data dataset1\Train_data.csv --output models
```

**Note:** Training uses KDD Cup 1999 network intrusion dataset (25,192 samples) for robust anomaly detection model development.

### 4. Start ML API
```powershell
# In terminal 1
python src\main.py
```

### 5. Start Dashboard (Next.js)
```powershell
# In terminal 2
cd dashboard
npm install
npm run dev
cd ..
```

### 6. Generate Test Traffic
```powershell
# In terminal 3
python scripts\generate_traffic.py --normal 100 --anomalous 10
```

### 7. Access Dashboard
Open browser to: http://localhost:3000

**Login Credentials:**
- Username: `admin`
- Password: `changeme`

## Quick Test Commands

### Test Single Request (Normal)
```powershell
$headers = @{
    "Content-Type" = "application/json"
}

$body = @{
    source_ip = "192.168.1.100"
    method = "GET"
    path = "/api/users"
    headers = @{
        "User-Agent" = "Mozilla/5.0"
    }
    body = ""
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analyze" -Method Post -Headers $headers -Body $body
```

### Test Single Request (SQL Injection)
```powershell
$body = @{
    source_ip = "10.0.0.5"
    method = "GET"
    path = "/api/users?id=1' OR '1'='1"
    headers = @{
        "User-Agent" = "curl/7.68.0"
    }
    body = ""
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/analyze" -Method Post -Headers $headers -Body $body
```

### View Statistics
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/statistics" -Method Get
```

### Generate Security Rules
```powershell
$body = @{
    confidence_threshold = 0.7
    max_rules = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/rules/generate" -Method Post -Headers @{"Content-Type"="application/json"} -Body $body
```

## Docker Quick Start

### Using Docker Compose
```powershell
docker-compose up -d
```

Access:
- API: http://localhost:8000
- Dashboard: http://localhost:5000
- API Docs: http://localhost:8000/api/docs

## Troubleshooting

### Issue: Models not loading
**Solution:** Train models first using the training script

### Issue: Connection refused
**Solution:** Check if services are running on correct ports

### Issue: Import errors
**Solution:** Ensure virtual environment is activated

### Issue: Redis connection error
**Solution:** Install and start Redis, or comment out Redis dependencies for development

## Next Steps

1. ✅ Train models with your own traffic data
2. ✅ Configure integration with your WAF
3. ✅ Customize detection thresholds
4. ✅ Set up continuous learning
5. ✅ Deploy to production environment

## Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/analyze` | POST | Analyze single request |
| `/api/v1/analyze/batch` | POST | Analyze batch requests |
| `/api/v1/statistics` | GET | Get system statistics |
| `/api/v1/rules/generate` | POST | Generate security rules |
| `/api/v1/rules` | GET | Get all rules |
| `/api/v1/health` | GET | Health check |

## Documentation

- **Full README**: [README.md](README.md)
- **Technical Docs**: [docs/technical_document.md](docs/technical_document.md)
- **API Docs**: http://localhost:8000/api/docs (when running)

## Support

For issues or questions:
- Check documentation
- Review logs in `logs/` directory
- Examine error messages
- Verify configuration in `config/config.yaml`

---

**Happy Detecting! 🛡️**
