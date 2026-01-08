"""
FastAPI routes for ML-WAF API.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.analyzer import AnomalyAnalyzer
from src.rules.generator import RuleGenerator
from src.utils.metrics import MetricsCollector

# Create routers
api_router = APIRouter(prefix="/api/v1")
analyzer = None  # Will be injected
rule_generator = RuleGenerator()
metrics = MetricsCollector()

def set_analyzer(analyzer_instance):
    """Set the analyzer instance after initialization."""
    global analyzer
    analyzer = analyzer_instance


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request model for traffic analysis."""
    source_ip: str = Field(..., description="Source IP address")
    method: str = Field(..., description="HTTP method")
    path: str = Field(..., description="Request path")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    body: str = Field(default="", description="Request body")
    timestamp: Optional[str] = Field(default=None, description="Request timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "source_ip": "192.168.1.100",
                "method": "GET",
                "path": "/api/users?id=1' OR '1'='1",
                "headers": {
                    "User-Agent": "Mozilla/5.0",
                    "Content-Type": "application/json"
                },
                "body": "",
                "timestamp": "2025-12-14T10:30:00Z"
            }
        }


class AnalyzeResponse(BaseModel):
    """Response model for analysis results."""
    is_anomaly: bool
    anomaly_score: float
    confidence: float
    threat_level: str
    explanation: Optional[Dict[str, Any]]
    recommended_action: str
    latency_ms: float
    timestamp: str


class BatchAnalyzeRequest(BaseModel):
    """Request model for batch analysis."""
    requests: List[AnalyzeRequest]


class RuleGenerationRequest(BaseModel):
    """Request model for rule generation."""
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_rules: int = Field(default=10, ge=1, le=100)


# Routes
@api_router.post("/analyze", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_traffic(request: AnalyzeRequest):
    """
    Analyze a single HTTP request for anomalies.
    
    This endpoint performs real-time ML-based anomaly detection on incoming traffic.
    """
    try:
        if analyzer is None:
            raise HTTPException(status_code=503, detail="Analyzer not initialized yet")
        
        # Convert request to dict
        request_data = request.dict()
        
        # Set timestamp if not provided
        if not request_data['timestamp']:
            request_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Analyze
        result = await analyzer.analyze_request(request_data)
        
        # Add request info to result for metrics
        result['_request_info'] = {
            'source_ip': request_data['source_ip'],
            'method': request_data['method'],
            'path': request_data['path'],
            'body': request_data.get('body', ''),
            'user_agent': request_data.get('headers', {}).get('User-Agent', '')
        }
        
        # Record metrics
        metrics.record_analysis(result)
        
        return AnalyzeResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@api_router.post("/analyze/batch", tags=["Analysis"])
async def analyze_traffic_batch(request: BatchAnalyzeRequest):
    """
    Analyze multiple HTTP requests in batch for improved performance.
    """
    try:
        # Convert requests to dicts
        requests_data = [req.dict() for req in request.requests]
        
        # Set timestamps
        for req_data in requests_data:
            if not req_data['timestamp']:
                req_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Batch analyze
        results = await analyzer.batch_analyze(requests_data)
        
        # Record metrics
        for result in results:
            metrics.record_analysis(result)
        
        return {"results": results, "count": len(results)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@api_router.get("/statistics", tags=["Monitoring"])
async def get_statistics():
    """Get analyzer statistics and performance metrics."""
    try:
        if analyzer is None:
            raise HTTPException(status_code=503, detail="Analyzer not initialized yet")
        
        analyzer_stats = analyzer.get_statistics()
        metrics_stats = metrics.get_statistics()
        
        # Format to match frontend expectations
        return {
            "analyzer": {
                "total_analyzed": metrics_stats.get('total_requests', 0),
                "anomalies_detected": metrics_stats.get('total_anomalies', 0),
                "avg_latency_ms": metrics_stats.get('avg_latency_ms', 0.0)
            },
            "metrics": {
                "requests_per_minute": metrics_stats.get('requests_per_minute', 0.0),
                "detection_rate_percent": metrics_stats.get('detection_rate_percent', 0.0),
                "false_positive_rate_percent": metrics_stats.get('false_positive_rate_percent', 0.0),
                "uptime_seconds": metrics_stats.get('uptime_seconds', 0),
                "attack_types": metrics_stats.get('attack_types', {})
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@api_router.get("/health", tags=["Monitoring"])
async def health_check():
    """Health check endpoint."""
    models_loaded = False
    if analyzer and hasattr(analyzer, 'supervised_model'):
        models_loaded = analyzer.supervised_model.is_trained if analyzer.supervised_model else False
    
    return {
        "status": "healthy" if analyzer else "initializing",
        "timestamp": datetime.utcnow().isoformat(),
        "models_loaded": models_loaded
    }


@api_router.get("/alerts/recent", tags=["Monitoring"])
async def get_recent_alerts(limit: int = 50):
    """Get recent anomaly alerts for dashboard."""
    try:
        if analyzer is None:
            raise HTTPException(status_code=503, detail="Analyzer not initialized yet")
        
        anomalies = metrics.get_recent_anomalies(limit=limit)
        
        # Format alerts for frontend
        formatted_alerts = []
        for i, alert in enumerate(anomalies):
            # Get request info to determine attack type
            request_info = alert.get('_request_info', {})
            path = request_info.get('path', '').lower()
            body = request_info.get('body', '').lower() if '_request_info' in alert else ''
            
            # Extract attack type from request content
            attack_type = 'Suspicious Activity'
            if 'union' in path or 'select' in path or '--' in path or "'" in path:
                attack_type = 'SQL Injection'
            elif '<script>' in body or 'alert(' in body or '<script>' in path:
                attack_type = 'XSS'
            elif '../' in path or 'etc/passwd' in path or 'file://' in path:
                attack_type = 'LFI'
            elif 'system(' in body or 'exec(' in body or '<?php' in body or 'cmd=' in path:
                attack_type = 'Command Injection'
            elif 'bot' in request_info.get('user_agent', '').lower():
                attack_type = 'Bot Traffic'
            
            # Fallback to indicators if available
            if attack_type == 'Suspicious Activity':
                attack_indicators = alert.get('explanation', {}).get('attack_indicators', [])
                if attack_indicators:
                    indicator = attack_indicators[0].lower()
                    if 'sql' in indicator:
                        attack_type = 'SQL Injection'
                    elif 'xss' in indicator or 'script' in indicator:
                        attack_type = 'XSS'
                    elif 'lfi' in indicator or 'file' in indicator:
                        attack_type = 'LFI'
                    elif 'command' in indicator:
                        attack_type = 'Command Injection'
            
            # Get severity from threat_level
            severity = alert.get('threat_level', 'medium').title()
            
            # Format explanation
            explanation_data = alert.get('explanation', {})
            
            # Get request info
            request_info = alert.get('_request_info', {})
            
            formatted_alerts.append({
                "request_id": f"req_{int(datetime.utcnow().timestamp())}_{i}",
                "is_anomaly": alert.get('is_anomaly', False),
                "anomaly_score": alert.get('anomaly_score', 0.0),
                "confidence": alert.get('confidence', 0.0),
                "attack_type": attack_type,
                "severity": severity,
                "timestamp": alert.get('timestamp', datetime.utcnow().isoformat()),
                "latency_ms": alert.get('latency_ms', 0.0),
                "explanation": {
                    "summary": explanation_data.get('summary', 'Anomaly detected'),
                    "top_features": []
                },
                "request_data": {
                    "method": request_info.get('method', 'GET'),
                    "url": request_info.get('path', '/'),
                    "client_ip": request_info.get('source_ip', 'unknown')
                }
            })
        
        return {
            "alerts": formatted_alerts,
            "count": len(formatted_alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@api_router.post("/rules/generate", tags=["Rules"])
async def generate_rules(request: RuleGenerationRequest, background_tasks: BackgroundTasks):
    """
    Generate security rules from recent anomalies.
    
    This endpoint analyzes detected anomalies and generates human-readable
    security rules that can be deployed to WAF.
    """
    try:
        # Get recent anomalies from metrics
        recent_anomalies = metrics.get_recent_anomalies(limit=100)
        
        # Generate rules
        rules = await rule_generator.generate_rules(
            recent_anomalies,
            confidence_threshold=request.confidence_threshold
        )
        
        # Limit number of rules
        rules = rules[:request.max_rules]
        
        return {
            "rules": rules,
            "count": len(rules),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rule generation failed: {str(e)}")


@api_router.get("/rules", tags=["Rules"])
async def get_all_rules():
    """Get all generated security rules."""
    try:
        rules = rule_generator.get_all_rules()
        return {"rules": rules, "count": len(rules)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rules: {str(e)}")


@api_router.get("/rules/export/{format}", tags=["Rules"])
async def export_rules(format: str):
    """
    Export rules in specified format.
    
    Supported formats: json, modsecurity, nginx
    """
    try:
        if format not in ['json', 'modsecurity', 'nginx']:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        exported = rule_generator.export_rules(format=format)
        
        return {
            "format": format,
            "content": exported,
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@api_router.post("/feedback", tags=["Learning"])
async def submit_feedback(
    request_id: str,
    is_false_positive: bool,
    comments: Optional[str] = None
):
    """
    Submit feedback for continuous learning.
    
    Administrators can mark detections as false positives to improve model accuracy.
    """
    try:
        # Store feedback for continuous learning
        feedback = {
            "request_id": request_id,
            "is_false_positive": is_false_positive,
            "comments": comments,
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        metrics.record_feedback(feedback)
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")


def setup_routes(app):
    """Setup all API routes."""
    # Include router
    app.include_router(api_router)
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "WAF ML Anomaly Detection API",
            "version": "1.0.0",
            "docs": "/api/docs",
            "health": "/api/v1/health"
        }
