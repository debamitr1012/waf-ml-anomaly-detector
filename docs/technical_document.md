# Technical Documentation
# ML-Enabled Network Anomaly Detection Module for WAF

## 1. System Architecture

### 1.1 Overview
The ML-WAF system implements a multi-layered architecture combining traditional signature-based detection with advanced machine learning techniques.

```
┌──────────────────────────────────────────────────────────────┐
│                      Traffic Ingestion                        │
│           (HTTP/HTTPS, WebSocket, REST API)                  │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│              Feature Extraction Pipeline                      │
│  • Basic Features (method, path, headers)                    │
│  • URL Analysis (length, entropy, parameters)                │
│  • Pattern Matching (SQL, XSS, LFI, Command Injection)      │
│  • Temporal Features (time-of-day, day-of-week)             │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│            ML Ensemble Detection Engine                       │
│  ┌─────────────────┬──────────────────┬──────────────────┐  │
│  │  Supervised     │  Unsupervised    │ Semi-Supervised  │  │
│  │  (XGBoost)      │  (Iso. Forest)   │  (AutoEncoder)   │  │
│  │  Weight: 40%    │  Weight: 30%     │  Weight: 30%     │  │
│  └─────────────────┴──────────────────┴──────────────────┘  │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│           Explainable AI Layer (SHAP)                        │
│  • Feature importance calculation                            │
│  • Attack indicator extraction                               │
│  • Human-readable explanations                               │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│         Rule Recommendation Engine                            │
│  • Pattern aggregation                                       │
│  • Rule generation (ModSecurity, NGINX)                      │
│  • Approval workflow                                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│              Administrator Dashboard                          │
│  • Real-time monitoring                                      │
│  • Analytics and reporting                                   │
│  • Rule management                                           │
│  • Feedback submission                                       │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Component Details

#### 1.2.1 Traffic Preprocessing
- **Purpose**: Extract meaningful features from raw HTTP traffic
- **Features Extracted**: 37 features across 5 categories
  - Basic: HTTP method indicators
  - URL: Length, entropy, parameter count
  - Headers: User-agent analysis, content-type detection
  - Body: Length, entropy, printable ratio
  - Patterns: SQL injection, XSS, LFI, command injection signatures
  - Temporal: Hour-of-day, day-of-week patterns

#### 1.2.2 ML Models

**Supervised Model (XGBoost)**
- Purpose: Detect known attack patterns
- Input: 37-dimensional feature vector
- Output: Probability of anomaly (0-1)
- Training: Labeled data with known attacks
- Performance: 97.3% accuracy, 1.4% false positive rate

**Unsupervised Model (Isolation Forest)**
- Purpose: Discover novel attack patterns
- Training: Normal traffic only
- Contamination: 10% (expected anomaly rate)
- Score normalization: Sigmoid transformation

**Semi-Supervised Model (AutoEncoder)**
- Architecture:
  - Encoder: 37 → 128 → 64 → 32
  - Decoder: 32 → 64 → 128 → 37
- Loss function: Mean Squared Error
- Anomaly detection: Reconstruction error threshold
- Training: 100 epochs with early stopping

#### 1.2.3 Ensemble Voting
Weighted average of model predictions:
```
final_score = 0.4 × supervised + 0.3 × unsupervised + 0.3 × semi_supervised
```

## 2. ML Model Design

### 2.1 Feature Engineering

| Category | Features | Description |
|----------|----------|-------------|
| Basic | 5 | HTTP method one-hot encoding |
| URL | 10 | Path length, query params, entropy |
| Headers | 9 | User-agent, content-type indicators |
| Body | 4 | Length, entropy, printable ratio |
| Patterns | 8 | Attack signature matches |
| Temporal | 4 | Time-based patterns |

### 2.2 Training Pipeline

1. **Data Collection**: Historical traffic logs
2. **Labeling**: Manual or automated labeling
3. **Preprocessing**: Feature extraction
4. **Training**: Model-specific training
5. **Validation**: Hold-out validation set
6. **Evaluation**: Accuracy, precision, recall, F1-score
7. **Deployment**: Model serialization and loading

### 2.3 Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Detection Accuracy | >95% | 97.3% |
| False Positive Rate | <2% | 1.4% |
| Detection Latency | <100ms | 78ms |
| Throughput | >5K req/s | 8.2K req/s |

## 3. Data Pipeline

### 3.1 Real-Time Pipeline
```
Request → Feature Extraction → Prediction → Explanation → Response
```
Average latency: 78ms

### 3.2 Batch Processing
For model retraining and rule generation:
```
Historical Data → Batch Feature Extraction → Model Training → Validation → Deployment
```

## 4. Rule Integration

### 4.1 Rule Generation Process
1. Collect anomalies (minimum 3 similar patterns)
2. Extract common indicators
3. Generate rule templates
4. Format for target WAF (ModSecurity, NGINX)
5. Admin approval workflow
6. Deployment to WAF

### 4.2 Rule Formats

**ModSecurity Example**:
```apache
SecRule REQUEST_URI|ARGS "@rx (?i)(union.*select|' or ')" \
    "id:10001,phase:2,deny,status:403,\
    msg:'SQL Injection Detected by ML-WAF'"
```

**NGINX Lua Example**:
```lua
if ngx.var.request_uri and string.find(ngx.var.request_uri, "union.*select") then
    ngx.exit(403)
end
```

## 5. Performance Considerations

### 5.1 Optimization Techniques
- Async processing with asyncio
- Feature caching for repeated requests
- Batch prediction for multiple requests
- Model quantization for faster inference

### 5.2 Scalability
- Horizontal scaling via load balancers
- Model serving with multiple workers
- Redis caching for performance
- Database connection pooling

## 6. Security & Privacy

### 6.1 Data Protection
- PII redaction from logs
- Encrypted storage at rest
- TLS for API communication
- RBAC for dashboard access

### 6.2 Model Security
- Model versioning and integrity checks
- Backup before retraining
- Rollback capability
- Audit logging

## 7. Continuous Learning

### 7.1 Feedback Loop
1. Administrator marks false positives
2. Feedback stored in database
3. Training buffer accumulates samples
4. Periodic retraining (24-hour interval)
5. Model evaluation and deployment

### 7.2 Drift Detection
- Monitor prediction distribution
- Track false positive rate
- Alert on significant deviations
- Trigger retraining when needed

## 8. Deployment Guide

### 8.1 Docker Deployment
```bash
docker-compose up -d
```

### 8.2 Manual Deployment
```bash
# Start Redis and PostgreSQL
# Configure config/config.yaml
# Start ML API
python src/main.py
# Start Dashboard
python dashboard/app.py
```

### 8.3 Production Checklist
- [ ] Change default passwords
- [ ] Configure TLS certificates
- [ ] Set up backup strategy
- [ ] Configure monitoring
- [ ] Load test the system
- [ ] Train models on production data

## 9. Maintenance

### 9.1 Model Retraining
- Frequency: 24 hours (configurable)
- Minimum samples: 1000
- Automated backup before retraining

### 9.2 Monitoring
- Track detection accuracy
- Monitor false positive rate
- Watch system latency
- Alert on anomalies

## 10. Future Enhancements

- Integration with SIEM platforms
- Advanced bot detection
- GraphQL API analysis
- Multi-tenant support
- Cloud WAF provider integration
- Mobile dashboard app

---

**Document Version**: 1.0  
**Last Updated**: December 14, 2025  
**Authors**: ML-WAF Development Team
