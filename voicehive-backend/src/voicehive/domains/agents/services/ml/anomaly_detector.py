"""
Predictive Issue Detection - Time-series analysis and anomaly detection
Implements early warning system for potential issues
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass
import json
import numpy as np
from collections import deque, defaultdict
import statistics

# Google Cloud Vertex AI imports
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    from google.cloud import aiplatform
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logging.warning("Vertex AI not available - using statistical fallback")

from voicehive.services.ai.openai_service import OpenAIService
from voicehive.utils.exceptions import VoiceHiveError, ErrorHandler
from voicehive.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RESPONSE_TIME_SPIKE = "response_time_spike"
    ERROR_RATE_INCREASE = "error_rate_increase"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    PATTERN_DEVIATION = "pattern_deviation"
    SEASONAL_ANOMALY = "seasonal_anomaly"
    TREND_REVERSAL = "trend_reversal"


class AnomalySeverity(Enum):
    """Severity levels for detected anomalies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MetricDataPoint:
    """Single metric data point with timestamp"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = None


@dataclass
class TimeSeriesData:
    """Time series data for a specific metric"""
    metric_name: str
    data_points: List[MetricDataPoint]
    unit: str = ""
    description: str = ""


@dataclass
class AnomalyDetection:
    """Detected anomaly with details"""
    id: str
    metric_name: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    timestamp: datetime
    value: float
    expected_value: float
    deviation_score: float
    confidence: float
    description: str
    prediction: Optional[str] = None
    recommended_actions: List[str] = None


@dataclass
class PredictionResult:
    """Prediction result for future values"""
    metric_name: str
    prediction_timestamp: datetime
    predicted_value: float
    confidence_interval: Tuple[float, float]
    confidence: float
    trend_direction: str  # "increasing", "decreasing", "stable"


class StatisticalAnalyzer:
    """Statistical analysis for anomaly detection"""
    
    def __init__(self, window_size: int = 100, sensitivity: float = 2.0):
        self.window_size = window_size
        self.sensitivity = sensitivity  # Standard deviations for anomaly threshold
        
        # Historical data storage
        self.metric_windows: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.baseline_stats: Dict[str, Dict[str, float]] = {}
    
    def add_data_point(self, metric_name: str, data_point: MetricDataPoint):
        """Add a new data point to the analysis window"""
        self.metric_windows[metric_name].append(data_point)
        self._update_baseline_stats(metric_name)
    
    def _update_baseline_stats(self, metric_name: str):
        """Update baseline statistics for a metric"""
        window = self.metric_windows[metric_name]
        if len(window) < 10:  # Need minimum data points
            return
        
        values = [dp.value for dp in window]
        
        self.baseline_stats[metric_name] = {
            "mean": statistics.mean(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0,
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "trend": self._calculate_trend(values[-20:])  # Recent trend
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend using simple linear regression"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x = list(range(n))
        
        # Simple linear regression
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope
    
    def detect_anomalies(self, metric_name: str, data_point: MetricDataPoint) -> Optional[AnomalyDetection]:
        """Detect anomalies in a new data point"""
        if metric_name not in self.baseline_stats:
            return None
        
        stats = self.baseline_stats[metric_name]
        value = data_point.value
        
        # Z-score based anomaly detection
        if stats["std"] == 0:
            return None
        
        z_score = abs(value - stats["mean"]) / stats["std"]
        
        if z_score > self.sensitivity:
            # Determine anomaly type and severity
            anomaly_type = self._classify_anomaly_type(metric_name, value, stats)
            severity = self._calculate_severity(z_score)
            
            return AnomalyDetection(
                id=f"anomaly_{metric_name}_{int(data_point.timestamp.timestamp())}",
                metric_name=metric_name,
                anomaly_type=anomaly_type,
                severity=severity,
                timestamp=data_point.timestamp,
                value=value,
                expected_value=stats["mean"],
                deviation_score=z_score,
                confidence=min(0.95, z_score / 5.0),  # Higher z-score = higher confidence
                description=f"{metric_name} anomaly: {value:.2f} (expected: {stats['mean']:.2f})"
            )
        
        return None
    
    def _classify_anomaly_type(self, metric_name: str, value: float, stats: Dict[str, float]) -> AnomalyType:
        """Classify the type of anomaly based on metric and value"""
        
        # Metric-specific classification
        if "response_time" in metric_name.lower():
            return AnomalyType.RESPONSE_TIME_SPIKE
        elif "error" in metric_name.lower():
            return AnomalyType.ERROR_RATE_INCREASE
        elif "memory" in metric_name.lower() or "cpu" in metric_name.lower():
            return AnomalyType.RESOURCE_EXHAUSTION
        elif value > stats["mean"]:
            # Check if it's following a trend
            if stats["trend"] > 0.1:  # Positive trend
                return AnomalyType.PERFORMANCE_DEGRADATION
            else:
                return AnomalyType.PATTERN_DEVIATION
        else:
            return AnomalyType.TREND_REVERSAL
    
    def _calculate_severity(self, z_score: float) -> AnomalySeverity:
        """Calculate severity based on z-score"""
        if z_score > 4.0:
            return AnomalySeverity.CRITICAL
        elif z_score > 3.0:
            return AnomalySeverity.HIGH
        elif z_score > 2.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def predict_future_values(self, metric_name: str, steps_ahead: int = 5) -> List[PredictionResult]:
        """Predict future values using trend analysis"""
        if metric_name not in self.baseline_stats:
            return []
        
        window = self.metric_windows[metric_name]
        if len(window) < 10:
            return []
        
        stats = self.baseline_stats[metric_name]
        recent_values = [dp.value for dp in list(window)[-20:]]
        trend = self._calculate_trend(recent_values)
        
        predictions = []
        last_timestamp = window[-1].timestamp
        
        for i in range(1, steps_ahead + 1):
            # Simple linear prediction
            predicted_value = recent_values[-1] + (trend * i)
            
            # Calculate confidence interval based on historical variance
            std = stats["std"]
            confidence_interval = (
                predicted_value - (1.96 * std),  # 95% confidence interval
                predicted_value + (1.96 * std)
            )
            
            # Determine trend direction
            if trend > 0.1:
                trend_direction = "increasing"
            elif trend < -0.1:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
            
            # Confidence decreases with prediction distance
            confidence = max(0.1, 0.9 - (i * 0.1))
            
            prediction = PredictionResult(
                metric_name=metric_name,
                prediction_timestamp=last_timestamp + timedelta(minutes=i * 5),  # 5-minute intervals
                predicted_value=predicted_value,
                confidence_interval=confidence_interval,
                confidence=confidence,
                trend_direction=trend_direction
            )
            
            predictions.append(prediction)
        
        return predictions


class VertexAIPredictor:
    """Vertex AI integration for advanced anomaly detection"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.initialized = False
        
        if VERTEX_AI_AVAILABLE:
            try:
                vertexai.init(project=project_id, location=location)
                self.generative_model = GenerativeModel("gemini-2.0-flash")
                self.initialized = True
                logger.info("Vertex AI Predictor initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI Predictor: {str(e)}")
                self.initialized = False
        else:
            logger.warning("Vertex AI not available for advanced predictions")
    
    async def analyze_anomaly_patterns(self, 
                                     anomalies: List[AnomalyDetection],
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in detected anomalies using Vertex AI"""
        if not self.initialized or not anomalies:
            return {"pattern_analysis": "Vertex AI not available or no anomalies to analyze"}
        
        try:
            # Prepare data for analysis
            anomaly_data = []
            for anomaly in anomalies:
                anomaly_data.append({
                    "metric": anomaly.metric_name,
                    "type": anomaly.anomaly_type.value,
                    "severity": anomaly.severity.value,
                    "timestamp": anomaly.timestamp.isoformat(),
                    "deviation": anomaly.deviation_score
                })
            
            prompt = f"""
            Analyze the following anomaly patterns and provide insights:
            
            Anomalies: {json.dumps(anomaly_data, indent=2)}
            
            System Context: {json.dumps(context, indent=2)}
            
            Please provide:
            1. Pattern identification (recurring patterns, correlations)
            2. Root cause analysis
            3. Predictive insights
            4. Recommended preventive actions
            
            Format as JSON with keys: patterns, root_causes, predictions, recommendations
            """
            
            response = await self._generate_content(prompt)
            return self._parse_analysis_response(response)
            
        except Exception as e:
            logger.error(f"Error in Vertex AI pattern analysis: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_content(self, prompt: str) -> str:
        """Generate content using Vertex AI"""
        try:
            response = self.generative_model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return "Error in content generation"
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse Vertex AI analysis response"""
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                return {"analysis": response}
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            return {"raw_response": response}


class AnomalyDetector:
    """
    Predictive Issue Detection System
    
    Features:
    - Time-series analysis for trend detection
    - Statistical anomaly detection
    - Pattern recognition for common failure modes
    - Early warning system for potential issues
    - Automated issue classification
    """
    
    def __init__(self, 
                 project_id: Optional[str] = None,
                 location: str = "us-central1",
                 openai_service: Optional[OpenAIService] = None,
                 sensitivity: float = 2.0):
        
        self.project_id = project_id or getattr(settings, 'google_cloud_project', 'default-project')
        self.statistical_analyzer = StatisticalAnalyzer(sensitivity=sensitivity)
        self.vertex_predictor = VertexAIPredictor(self.project_id, location)
        self.openai_service = openai_service or OpenAIService()
        
        # Detection state
        self.detected_anomalies: List[AnomalyDetection] = []
        self.prediction_cache: Dict[str, List[PredictionResult]] = {}
        self.last_analysis_time = datetime.now()
        
        # Configuration
        self.analysis_interval = timedelta(minutes=5)
        self.max_anomaly_history = 1000
        
        logger.info("Anomaly Detector initialized with predictive capabilities")
    
    async def add_metric_data(self, time_series: TimeSeriesData) -> List[AnomalyDetection]:
        """
        Add new metric data and detect anomalies
        
        Args:
            time_series: Time series data for analysis
            
        Returns:
            List of detected anomalies
        """
        detected_anomalies = []
        
        for data_point in time_series.data_points:
            # Add to statistical analyzer
            self.statistical_analyzer.add_data_point(time_series.metric_name, data_point)
            
            # Detect anomalies
            anomaly = self.statistical_analyzer.detect_anomalies(time_series.metric_name, data_point)
            
            if anomaly:
                # Enhance anomaly with predictions and recommendations
                anomaly = await self._enhance_anomaly_detection(anomaly, time_series)
                detected_anomalies.append(anomaly)
                
                # Store in history
                self.detected_anomalies.append(anomaly)
                
                # Trim history if too large
                if len(self.detected_anomalies) > self.max_anomaly_history:
                    self.detected_anomalies = self.detected_anomalies[-self.max_anomaly_history:]
                
                logger.warning(f"Anomaly detected: {anomaly.description}")
        
        return detected_anomalies
    
    async def _enhance_anomaly_detection(self, 
                                       anomaly: AnomalyDetection,
                                       time_series: TimeSeriesData) -> AnomalyDetection:
        """Enhance anomaly detection with AI-powered insights"""
        try:
            # Generate prediction using OpenAI
            prediction_prompt = f"""
            An anomaly has been detected in the {anomaly.metric_name} metric:
            
            - Current value: {anomaly.value}
            - Expected value: {anomaly.expected_value}
            - Deviation score: {anomaly.deviation_score}
            - Anomaly type: {anomaly.anomaly_type.value}
            - Severity: {anomaly.severity.value}
            
            Based on this anomaly, provide:
            1. A brief prediction of what might happen next
            2. 3-5 recommended immediate actions
            
            Keep the response concise and actionable.
            """
            
            response = await self.openai_service.generate_response(
                system_prompt="You are an expert system monitoring analyst.",
                conversation_history=[{"role": "user", "content": prediction_prompt}]
            )
            
            # Parse response to extract prediction and actions
            lines = response.split('\n')
            prediction = ""
            actions = []
            
            current_section = None
            for line in lines:
                line = line.strip()
                if "prediction" in line.lower() or "might happen" in line.lower():
                    current_section = "prediction"
                elif "action" in line.lower() or "recommend" in line.lower():
                    current_section = "actions"
                elif line and current_section == "prediction":
                    prediction = line
                elif line and current_section == "actions" and (line.startswith('-') or line.startswith('•')):
                    actions.append(line.lstrip('-•').strip())
            
            # Update anomaly with enhanced information
            anomaly.prediction = prediction or "Monitor for continued deviation"
            anomaly.recommended_actions = actions or ["Monitor metric closely", "Check system resources", "Review recent changes"]
            
        except Exception as e:
            logger.error(f"Error enhancing anomaly detection: {str(e)}")
            anomaly.prediction = "Unable to generate prediction"
            anomaly.recommended_actions = ["Monitor metric closely"]
        
        return anomaly
    
    async def predict_future_metrics(self, 
                                   metric_names: List[str],
                                   steps_ahead: int = 10) -> Dict[str, List[PredictionResult]]:
        """
        Predict future values for specified metrics
        
        Args:
            metric_names: List of metric names to predict
            steps_ahead: Number of time steps to predict ahead
            
        Returns:
            Dictionary mapping metric names to prediction results
        """
        predictions = {}
        
        for metric_name in metric_names:
            try:
                metric_predictions = self.statistical_analyzer.predict_future_values(
                    metric_name, steps_ahead
                )
                predictions[metric_name] = metric_predictions
                
                # Cache predictions
                self.prediction_cache[metric_name] = metric_predictions
                
            except Exception as e:
                logger.error(f"Error predicting {metric_name}: {str(e)}")
                predictions[metric_name] = []
        
        return predictions
    
    async def analyze_anomaly_patterns(self, 
                                     time_window: timedelta = timedelta(hours=24)) -> Dict[str, Any]:
        """
        Analyze patterns in recent anomalies
        
        Args:
            time_window: Time window for analysis
            
        Returns:
            Pattern analysis results
        """
        cutoff_time = datetime.now() - time_window
        recent_anomalies = [
            anomaly for anomaly in self.detected_anomalies
            if anomaly.timestamp >= cutoff_time
        ]
        
        if not recent_anomalies:
            return {"message": "No recent anomalies to analyze"}
        
        # Basic pattern analysis
        pattern_analysis = {
            "total_anomalies": len(recent_anomalies),
            "severity_distribution": {},
            "type_distribution": {},
            "metric_distribution": {},
            "time_distribution": {},
            "correlations": []
        }
        
        # Analyze distributions
        for anomaly in recent_anomalies:
            # Severity distribution
            severity = anomaly.severity.value
            pattern_analysis["severity_distribution"][severity] = \
                pattern_analysis["severity_distribution"].get(severity, 0) + 1
            
            # Type distribution
            anomaly_type = anomaly.anomaly_type.value
            pattern_analysis["type_distribution"][anomaly_type] = \
                pattern_analysis["type_distribution"].get(anomaly_type, 0) + 1
            
            # Metric distribution
            metric = anomaly.metric_name
            pattern_analysis["metric_distribution"][metric] = \
                pattern_analysis["metric_distribution"].get(metric, 0) + 1
            
            # Time distribution (by hour)
            hour = anomaly.timestamp.hour
            pattern_analysis["time_distribution"][hour] = \
                pattern_analysis["time_distribution"].get(hour, 0) + 1
        
        # Advanced pattern analysis using Vertex AI
        context = {
            "time_window_hours": time_window.total_seconds() / 3600,
            "system_load": "normal",  # This would come from monitoring
            "recent_deployments": []  # This would come from deployment history
        }
        
        vertex_analysis = await self.vertex_predictor.analyze_anomaly_patterns(
            recent_anomalies, context
        )
        
        pattern_analysis["advanced_analysis"] = vertex_analysis
        
        return pattern_analysis
    
    def get_early_warnings(self, 
                          threshold_hours: int = 2) -> List[Dict[str, Any]]:
        """
        Get early warnings for potential issues
        
        Args:
            threshold_hours: Hours ahead to look for warnings
            
        Returns:
            List of early warning alerts
        """
        warnings = []
        current_time = datetime.now()
        warning_threshold = current_time + timedelta(hours=threshold_hours)
        
        # Check predictions for potential issues
        for metric_name, predictions in self.prediction_cache.items():
            for prediction in predictions:
                if prediction.prediction_timestamp <= warning_threshold:
                    # Check if prediction indicates potential issue
                    if (prediction.trend_direction == "increasing" and 
                        "error" in metric_name.lower()) or \
                       (prediction.trend_direction == "increasing" and 
                        "response_time" in metric_name.lower()):
                        
                        warnings.append({
                            "type": "early_warning",
                            "metric": metric_name,
                            "predicted_time": prediction.prediction_timestamp.isoformat(),
                            "predicted_value": prediction.predicted_value,
                            "trend": prediction.trend_direction,
                            "confidence": prediction.confidence,
                            "message": f"Potential issue predicted for {metric_name}"
                        })
        
        return warnings
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get anomaly detection statistics"""
        total_anomalies = len(self.detected_anomalies)
        
        if total_anomalies == 0:
            return {"message": "No anomalies detected yet"}
        
        # Calculate statistics
        severity_counts = {}
        type_counts = {}
        recent_count = 0
        
        recent_threshold = datetime.now() - timedelta(hours=24)
        
        for anomaly in self.detected_anomalies:
            severity_counts[anomaly.severity.value] = \
                severity_counts.get(anomaly.severity.value, 0) + 1
            type_counts[anomaly.anomaly_type.value] = \
                type_counts.get(anomaly.anomaly_type.value, 0) + 1
            
            if anomaly.timestamp >= recent_threshold:
                recent_count += 1
        
        return {
            "total_anomalies": total_anomalies,
            "recent_anomalies_24h": recent_count,
            "severity_distribution": severity_counts,
            "type_distribution": type_counts,
            "vertex_ai_available": self.vertex_predictor.initialized,
            "metrics_monitored": len(self.statistical_analyzer.metric_windows),
            "prediction_cache_size": len(self.prediction_cache)
        }
