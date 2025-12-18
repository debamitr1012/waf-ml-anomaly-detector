"""
Main entry point for the ML-Enabled WAF Anomaly Detection System.
Initializes all components and starts the API server.
"""

import os
import sys
import asyncio
import signal
import logging
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core.analyzer import AnomalyAnalyzer
from core.baseline import BaselineManager
from api.routes import setup_routes
from utils.logger import setup_logger
from utils.metrics import MetricsCollector
from database.models import init_database
from ml.continuous_learning import ContinuousLearningEngine

# Initialize logger
logger = setup_logger(__name__)

# Global components
analyzer: Optional[AnomalyAnalyzer] = None
baseline_manager: Optional[BaselineManager] = None
learning_engine: Optional[ContinuousLearningEngine] = None
metrics_collector: Optional[MetricsCollector] = None


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="WAF ML Anomaly Detection API",
        description="Machine Learning-powered network anomaly detection for WAF",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup routes
    setup_routes(app)
    
    return app


async def initialize_components():
    """Initialize all system components."""
    global analyzer, baseline_manager, learning_engine, metrics_collector
    
    try:
        logger.info("Initializing database...")
        await init_database()
        
        logger.info("Initializing metrics collector...")
        metrics_collector = MetricsCollector()
        
        logger.info("Loading ML models...")
        analyzer = AnomalyAnalyzer()
        await analyzer.load_models()
        
        logger.info("Initializing baseline manager...")
        baseline_manager = BaselineManager()
        await baseline_manager.load_baselines()
        
        logger.info("Starting continuous learning engine...")
        learning_engine = ContinuousLearningEngine(analyzer)
        await learning_engine.start()
        
        logger.info("All components initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}", exc_info=True)
        raise


async def shutdown_components():
    """Gracefully shutdown all components."""
    global analyzer, baseline_manager, learning_engine
    
    logger.info("Shutting down components...")
    
    if learning_engine:
        await learning_engine.stop()
    
    if baseline_manager:
        await baseline_manager.save_baselines()
    
    if analyzer:
        await analyzer.save_models()
    
    logger.info("Shutdown complete!")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    asyncio.create_task(shutdown_components())
    sys.exit(0)


def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create app
    app = create_app()
    
    # Add startup event
    @app.on_event("startup")
    async def startup_event():
        await initialize_components()
        # Inject analyzer into routes
        from api.routes import set_analyzer
        set_analyzer(analyzer)
    
    # Add shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        await shutdown_components()
    
    # Get configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "4"))
    
    # Start server
    logger.info(f"Starting API server on {host}:{port}")
    logger.info(f"API documentation available at http://{host}:{port}/api/docs")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
