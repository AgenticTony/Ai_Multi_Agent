"""
OpenTelemetry instrumentation for VoiceHive monitoring.
Provides distributed tracing, metrics collection, and observability.
"""

import os
import logging
from typing import Dict, Any
from opentelemetry import trace, metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceHiveInstrumentation:
    """Centralized instrumentation for VoiceHive monitoring."""
    
    def __init__(self):
        self.tracer = None
        self.meter = None
        self.metrics = {}
        self.setup_resource()
        self.setup_tracing()
        self.setup_metrics()
        self.setup_prometheus()
    
    def setup_resource(self):
        """Set up OpenTelemetry resource with service information."""
        self.resource = Resource.create({
            "service.name": "voicehive-backend",
            "service.version": "1.0.0",
            "service.environment": os.getenv("ENVIRONMENT", "development"),
            "service.instance.id": os.getenv("INSTANCE_ID", "local-instance")
        })
    
    def setup_tracing(self):
        """Configure distributed tracing with Jaeger."""
        try:
            # Set up tracer provider
            trace.set_tracer_provider(TracerProvider(resource=self.resource))
            self.tracer = trace.get_tracer(__name__)
            
            # Configure Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
                agent_port=int(os.getenv("JAEGER_PORT", "6831")),
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            
            logger.info("Distributed tracing configured with Jaeger")
            
        except Exception as e:
            logger.error(f"Failed to setup tracing: {e}")
    
    def setup_metrics(self):
        """Configure metrics collection."""
        try:
            # Set up meter provider
            metrics.set_meter_provider(MeterProvider(resource=self.resource))
            self.meter = metrics.get_meter(__name__)
            
            # Create custom metrics
            self.metrics = {
                'call_counter': self.meter.create_counter(
                    name="voicehive_calls_total",
                    description="Total number of calls processed",
                    unit="1"
                ),
                'call_duration': self.meter.create_histogram(
                    name="voicehive_call_duration_seconds",
                    description="Call duration in seconds",
                    unit="s"
                ),
                'success_rate': self.meter.create_gauge(
                    name="voicehive_success_rate",
                    description="Call success rate percentage",
                    unit="%"
                ),
                'active_calls': self.meter.create_gauge(
                    name="voicehive_active_calls",
                    description="Number of currently active calls",
                    unit="1"
                ),
                'api_requests': self.meter.create_counter(
                    name="voicehive_api_requests_total",
                    description="Total API requests",
                    unit="1"
                ),
                'api_response_time': self.meter.create_histogram(
                    name="voicehive_api_response_time_seconds",
                    description="API response time in seconds",
                    unit="s"
                )
            }
            
            logger.info("Metrics collection configured")
            
        except Exception as e:
            logger.error(f"Failed to setup metrics: {e}")
    
    def setup_prometheus(self):
        """Set up Prometheus metrics endpoint."""
        try:
            # Prometheus metrics
            self.prometheus_metrics = {
                'calls_total': Counter(
                    'voicehive_calls_total',
                    'Total number of calls processed',
                    ['status', 'agent']
                ),
                'call_duration_seconds': Histogram(
                    'voicehive_call_duration_seconds',
                    'Call duration in seconds',
                    ['agent']
                ),
                'active_calls_gauge': Gauge(
                    'voicehive_active_calls',
                    'Number of currently active calls'
                ),
                'api_requests_total': Counter(
                    'voicehive_api_requests_total',
                    'Total API requests',
                    ['method', 'endpoint', 'status']
                ),
                'api_response_time_seconds': Histogram(
                    'voicehive_api_response_time_seconds',
                    'API response time in seconds',
                    ['method', 'endpoint']
                ),
                'system_memory_usage': Gauge(
                    'voicehive_system_memory_usage_percent',
                    'System memory usage percentage'
                ),
                'system_cpu_usage': Gauge(
                    'voicehive_system_cpu_usage_percent',
                    'System CPU usage percentage'
                )
            }
            
            # Start Prometheus metrics server
            prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8001"))
            start_http_server(prometheus_port)
            logger.info(f"Prometheus metrics server started on port {prometheus_port}")
            
        except Exception as e:
            logger.error(f"Failed to setup Prometheus: {e}")
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI application."""
        try:
            FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
            logger.info("FastAPI instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}")
    
    def instrument_requests(self):
        """Instrument HTTP requests."""
        try:
            RequestsInstrumentor().instrument()
            logger.info("Requests instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to instrument requests: {e}")
    
    def instrument_logging(self):
        """Instrument logging."""
        try:
            LoggingInstrumentor().instrument()
            logger.info("Logging instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to instrument logging: {e}")
    
    def record_call_metrics(self, duration: float, status: str, agent: str = "roxy"):
        """Record call-related metrics."""
        try:
            # OpenTelemetry metrics
            self.metrics['call_counter'].add(1, {"status": status, "agent": agent})
            self.metrics['call_duration'].record(duration, {"agent": agent})
            
            # Prometheus metrics
            self.prometheus_metrics['calls_total'].labels(status=status, agent=agent).inc()
            self.prometheus_metrics['call_duration_seconds'].labels(agent=agent).observe(duration)
            
        except Exception as e:
            logger.error(f"Failed to record call metrics: {e}")
    
    def record_api_metrics(self, method: str, endpoint: str, status_code: int, response_time: float):
        """Record API-related metrics."""
        try:
            # OpenTelemetry metrics
            self.metrics['api_requests'].add(1, {
                "method": method,
                "endpoint": endpoint,
                "status": str(status_code)
            })
            self.metrics['api_response_time'].record(response_time, {
                "method": method,
                "endpoint": endpoint
            })
            
            # Prometheus metrics
            self.prometheus_metrics['api_requests_total'].labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()
            self.prometheus_metrics['api_response_time_seconds'].labels(
                method=method,
                endpoint=endpoint
            ).observe(response_time)
            
        except Exception as e:
            logger.error(f"Failed to record API metrics: {e}")
    
    def update_system_metrics(self, memory_usage: float, cpu_usage: float, active_calls: int):
        """Update system-level metrics."""
        try:
            # OpenTelemetry metrics
            self.metrics['active_calls'].set(active_calls)
            
            # Prometheus metrics
            self.prometheus_metrics['active_calls_gauge'].set(active_calls)
            self.prometheus_metrics['system_memory_usage'].set(memory_usage)
            self.prometheus_metrics['system_cpu_usage'].set(cpu_usage)
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def create_span(self, name: str, attributes: Dict[str, Any] = None):
        """Create a new trace span."""
        try:
            span = self.tracer.start_span(name)
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            return span
        except Exception as e:
            logger.error(f"Failed to create span: {e}")
            return None
    
    def get_current_span(self):
        """Get the current active span."""
        return trace.get_current_span()

# Global instrumentation instance
instrumentation = VoiceHiveInstrumentation()

def get_instrumentation() -> VoiceHiveInstrumentation:
    """Get the global instrumentation instance."""
    return instrumentation

def setup_instrumentation(app=None):
    """Set up all instrumentation components."""
    try:
        instrumentation.instrument_requests()
        instrumentation.instrument_logging()
        
        if app:
            instrumentation.instrument_fastapi(app)
        
        logger.info("All instrumentation components configured successfully")
        return instrumentation
        
    except Exception as e:
        logger.error(f"Failed to setup instrumentation: {e}")
        return None
