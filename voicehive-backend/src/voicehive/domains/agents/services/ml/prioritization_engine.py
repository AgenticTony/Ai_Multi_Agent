"""
ML-Based Prioritization Engine - Hybrid Vertex AI + OpenAI approach
Implements intelligent improvement prioritization using machine learning
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import json
import numpy as np

# Google Cloud Vertex AI imports
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    from vertexai.language_models import TextEmbeddingModel
    from google.cloud import aiplatform
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logging.warning("Vertex AI not available - using fallback implementation")

from voicehive.services.ai.openai_service import OpenAIService
from voicehive.utils.exceptions import VoiceHiveError, ErrorHandler
from voicehive.core.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ImprovementPriority(Enum):
    """Priority levels for improvements"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DEFERRED = "deferred"


class ImprovementCategory(Enum):
    """Categories of improvements"""
    PERFORMANCE = "performance"
    SAFETY = "safety"
    USER_EXPERIENCE = "user_experience"
    COST_OPTIMIZATION = "cost_optimization"
    FEATURE_ENHANCEMENT = "feature_enhancement"


@dataclass
class ImprovementCandidate:
    """Improvement candidate with metadata"""
    id: str
    title: str
    description: str
    category: ImprovementCategory
    estimated_impact: float  # 0.0 to 1.0
    estimated_effort: float  # 0.0 to 1.0 (higher = more effort)
    risk_level: float  # 0.0 to 1.0
    performance_data: Dict[str, float]
    timestamp: datetime
    source_agent: str
    priority: Optional[ImprovementPriority] = None
    ml_score: Optional[float] = None
    reasoning: Optional[str] = None


@dataclass
class PrioritizationResult:
    """Result of prioritization analysis"""
    candidate: ImprovementCandidate
    final_priority: ImprovementPriority
    ml_score: float
    reasoning_score: float
    combined_score: float
    reasoning: str
    confidence: float
    recommended_timeline: str


class VertexAIPredictor:
    """Vertex AI integration for ML-based scoring"""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        self.project_id = project_id
        self.location = location
        self.initialized = False
        
        if VERTEX_AI_AVAILABLE:
            try:
                vertexai.init(project=project_id, location=location)
                self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-005")
                self.generative_model = GenerativeModel("gemini-2.0-flash")
                self.initialized = True
                logger.info("Vertex AI initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI: {str(e)}")
                self.initialized = False
        else:
            logger.warning("Vertex AI not available - using fallback scoring")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text analysis"""
        if not self.initialized:
            # Fallback: simple hash-based embeddings
            return [[hash(text) % 1000 / 1000.0 for _ in range(768)] for text in texts]
        
        try:
            embeddings = self.embedding_model.get_embeddings(texts)
            return [embedding.values for embedding in embeddings]
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return [[0.5] * 768 for _ in texts]  # Fallback
    
    async def predict_improvement_score(self, candidate: ImprovementCandidate) -> float:
        """Predict improvement score using ML model"""
        if not self.initialized:
            return self._fallback_scoring(candidate)
        
        try:
            # Feature engineering for ML model
            features = self._extract_features(candidate)
            
            # For now, use a simple heuristic model
            # In production, this would be a trained ML model
            score = self._heuristic_model(features)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {str(e)}")
            return self._fallback_scoring(candidate)
    
    def _extract_features(self, candidate: ImprovementCandidate) -> Dict[str, float]:
        """Extract features for ML model"""
        return {
            "impact": candidate.estimated_impact,
            "effort": candidate.estimated_effort,
            "risk": candidate.risk_level,
            "category_score": self._category_to_score(candidate.category),
            "performance_trend": self._calculate_performance_trend(candidate.performance_data),
            "urgency": self._calculate_urgency(candidate.timestamp),
            "source_reliability": self._source_reliability_score(candidate.source_agent)
        }
    
    def _heuristic_model(self, features: Dict[str, float]) -> float:
        """Heuristic model for improvement scoring"""
        # Weighted combination of features
        weights = {
            "impact": 0.3,
            "effort": -0.2,  # Lower effort is better
            "risk": -0.15,   # Lower risk is better
            "category_score": 0.1,
            "performance_trend": 0.15,
            "urgency": 0.1,
            "source_reliability": 0.1
        }
        
        score = sum(features.get(key, 0.5) * weight for key, weight in weights.items())
        return (score + 1) / 2  # Normalize to 0-1 range
    
    def _category_to_score(self, category: ImprovementCategory) -> float:
        """Convert category to numerical score"""
        category_scores = {
            ImprovementCategory.SAFETY: 1.0,
            ImprovementCategory.PERFORMANCE: 0.9,
            ImprovementCategory.USER_EXPERIENCE: 0.8,
            ImprovementCategory.COST_OPTIMIZATION: 0.7,
            ImprovementCategory.FEATURE_ENHANCEMENT: 0.6
        }
        return category_scores.get(category, 0.5)
    
    def _calculate_performance_trend(self, performance_data: Dict[str, float]) -> float:
        """Calculate performance trend score"""
        if not performance_data:
            return 0.5
        
        # Simple trend calculation based on recent performance
        values = list(performance_data.values())
        if len(values) < 2:
            return 0.5
        
        # Calculate trend (positive = improving, negative = degrading)
        trend = (values[-1] - values[0]) / len(values)
        return max(0.0, min(1.0, 0.5 - trend))  # Invert so degrading = higher priority
    
    def _calculate_urgency(self, timestamp: datetime) -> float:
        """Calculate urgency based on timestamp"""
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        # More urgent if older (up to 24 hours)
        return min(1.0, age_hours / 24.0)
    
    def _source_reliability_score(self, source_agent: str) -> float:
        """Score based on source agent reliability"""
        reliability_scores = {
            "monitoring_agent": 0.9,
            "emergency_manager": 1.0,
            "feedback_agent": 0.8,
            "user_feedback": 0.7,
            "automated_analysis": 0.6
        }
        return reliability_scores.get(source_agent, 0.5)
    
    def _fallback_scoring(self, candidate: ImprovementCandidate) -> float:
        """Fallback scoring when Vertex AI is not available"""
        # Simple heuristic based on impact, effort, and risk
        impact_score = candidate.estimated_impact
        effort_penalty = candidate.estimated_effort * 0.3
        risk_penalty = candidate.risk_level * 0.2
        
        score = impact_score - effort_penalty - risk_penalty
        return max(0.0, min(1.0, score))


class OpenAIReasoner:
    """OpenAI integration for reasoning and validation"""
    
    def __init__(self, openai_service: Optional[OpenAIService] = None):
        self.openai_service = openai_service or OpenAIService()
    
    async def analyze_improvement_reasoning(self, 
                                          candidate: ImprovementCandidate,
                                          ml_score: float,
                                          context: Dict[str, Any]) -> Tuple[float, str]:
        """Analyze improvement using OpenAI reasoning"""
        try:
            prompt = self._build_reasoning_prompt(candidate, ml_score, context)
            
            response = await self.openai_service.generate_response(
                system_prompt="You are an expert AI system analyst specializing in improvement prioritization.",
                conversation_history=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse response to extract score and reasoning
            reasoning_result = self._parse_reasoning_response(response)
            return reasoning_result["score"], reasoning_result["reasoning"]
            
        except Exception as e:
            logger.error(f"Error in OpenAI reasoning: {str(e)}")
            return 0.5, f"Fallback reasoning: {candidate.description}"
    
    def _build_reasoning_prompt(self, 
                               candidate: ImprovementCandidate,
                               ml_score: float,
                               context: Dict[str, Any]) -> str:
        """Build prompt for OpenAI reasoning"""
        return f"""
        Analyze this improvement candidate and provide a priority score (0.0-1.0) with detailed reasoning:

        **Improvement Details:**
        - Title: {candidate.title}
        - Description: {candidate.description}
        - Category: {candidate.category.value}
        - Estimated Impact: {candidate.estimated_impact}
        - Estimated Effort: {candidate.estimated_effort}
        - Risk Level: {candidate.risk_level}
        - Source: {candidate.source_agent}
        - ML Score: {ml_score}

        **System Context:**
        - Current Performance: {context.get('current_performance', 'Unknown')}
        - Recent Issues: {context.get('recent_issues', 'None')}
        - Resource Availability: {context.get('resource_availability', 'Normal')}
        - Business Priority: {context.get('business_priority', 'Standard')}

        **Analysis Requirements:**
        1. Validate the ML score against business logic
        2. Consider strategic alignment and timing
        3. Assess potential risks and dependencies
        4. Recommend priority level and timeline

        **Response Format:**
        {{
            "score": <float 0.0-1.0>,
            "priority": "<critical|high|medium|low|deferred>",
            "reasoning": "<detailed explanation>",
            "timeline": "<recommended implementation timeline>",
            "confidence": <float 0.0-1.0>
        }}
        """
    
    def _parse_reasoning_response(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI reasoning response"""
        try:
            # Try to parse as JSON
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                
                return {
                    "score": float(result.get("score", 0.5)),
                    "reasoning": result.get("reasoning", "No reasoning provided"),
                    "priority": result.get("priority", "medium"),
                    "timeline": result.get("timeline", "TBD"),
                    "confidence": float(result.get("confidence", 0.5))
                }
            else:
                # Fallback parsing
                return {
                    "score": 0.5,
                    "reasoning": response,
                    "priority": "medium",
                    "timeline": "TBD",
                    "confidence": 0.5
                }
                
        except Exception as e:
            logger.error(f"Error parsing reasoning response: {str(e)}")
            return {
                "score": 0.5,
                "reasoning": "Failed to parse reasoning",
                "priority": "medium",
                "timeline": "TBD",
                "confidence": 0.3
            }


class PrioritizationEngine:
    """
    Hybrid ML-based prioritization engine
    
    Combines Vertex AI machine learning with OpenAI reasoning
    for intelligent improvement prioritization
    """
    
    def __init__(self, 
                 project_id: Optional[str] = None,
                 location: str = "us-central1",
                 openai_service: Optional[OpenAIService] = None):
        
        self.project_id = project_id or getattr(settings, 'google_cloud_project', 'default-project')
        self.vertex_predictor = VertexAIPredictor(self.project_id, location)
        self.openai_reasoner = OpenAIReasoner(openai_service)
        
        # Prioritization history for learning
        self.prioritization_history: List[PrioritizationResult] = []
        self.performance_feedback: Dict[str, float] = {}
        
        logger.info("Prioritization Engine initialized with hybrid ML approach")
    
    async def prioritize_improvements(self, 
                                    candidates: List[ImprovementCandidate],
                                    context: Optional[Dict[str, Any]] = None) -> List[PrioritizationResult]:
        """
        Prioritize a list of improvement candidates
        
        Args:
            candidates: List of improvement candidates
            context: Additional context for prioritization
            
        Returns:
            List of prioritization results sorted by priority
        """
        if not candidates:
            return []
        
        context = context or {}
        results = []
        
        logger.info(f"Prioritizing {len(candidates)} improvement candidates")
        
        for candidate in candidates:
            try:
                result = await self._prioritize_single_candidate(candidate, context)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error prioritizing candidate {candidate.id}: {str(e)}")
                # Create fallback result
                fallback_result = PrioritizationResult(
                    candidate=candidate,
                    final_priority=ImprovementPriority.MEDIUM,
                    ml_score=0.5,
                    reasoning_score=0.5,
                    combined_score=0.5,
                    reasoning="Error in prioritization - using fallback",
                    confidence=0.3,
                    recommended_timeline="TBD"
                )
                results.append(fallback_result)
        
        # Sort by combined score (highest first)
        results.sort(key=lambda x: x.combined_score, reverse=True)
        
        # Store in history for learning
        self.prioritization_history.extend(results)
        
        logger.info(f"Prioritization complete - {len(results)} results generated")
        return results
    
    async def _prioritize_single_candidate(self, 
                                         candidate: ImprovementCandidate,
                                         context: Dict[str, Any]) -> PrioritizationResult:
        """Prioritize a single improvement candidate"""
        
        # Step 1: Get ML-based score from Vertex AI
        ml_score = await self.vertex_predictor.predict_improvement_score(candidate)
        
        # Step 2: Get reasoning-based analysis from OpenAI
        reasoning_score, reasoning_text = await self.openai_reasoner.analyze_improvement_reasoning(
            candidate, ml_score, context
        )
        
        # Step 3: Combine scores with weighted approach
        combined_score = self._combine_scores(ml_score, reasoning_score, candidate)
        
        # Step 4: Determine final priority
        final_priority = self._score_to_priority(combined_score)
        
        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(ml_score, reasoning_score, candidate)
        
        # Step 6: Generate timeline recommendation
        timeline = self._recommend_timeline(final_priority, candidate)
        
        return PrioritizationResult(
            candidate=candidate,
            final_priority=final_priority,
            ml_score=ml_score,
            reasoning_score=reasoning_score,
            combined_score=combined_score,
            reasoning=reasoning_text,
            confidence=confidence,
            recommended_timeline=timeline
        )
    
    def _combine_scores(self, 
                       ml_score: float, 
                       reasoning_score: float, 
                       candidate: ImprovementCandidate) -> float:
        """Combine ML and reasoning scores with intelligent weighting"""
        
        # Dynamic weighting based on candidate characteristics
        if candidate.category == ImprovementCategory.SAFETY:
            # Safety improvements: trust reasoning more
            ml_weight = 0.3
            reasoning_weight = 0.7
        elif candidate.risk_level > 0.7:
            # High-risk improvements: trust reasoning more
            ml_weight = 0.4
            reasoning_weight = 0.6
        else:
            # Standard improvements: balanced approach
            ml_weight = 0.6
            reasoning_weight = 0.4
        
        combined = (ml_score * ml_weight) + (reasoning_score * reasoning_weight)
        return max(0.0, min(1.0, combined))
    
    def _score_to_priority(self, score: float) -> ImprovementPriority:
        """Convert numerical score to priority level"""
        if score >= 0.8:
            return ImprovementPriority.CRITICAL
        elif score >= 0.6:
            return ImprovementPriority.HIGH
        elif score >= 0.4:
            return ImprovementPriority.MEDIUM
        elif score >= 0.2:
            return ImprovementPriority.LOW
        else:
            return ImprovementPriority.DEFERRED
    
    def _calculate_confidence(self, 
                            ml_score: float, 
                            reasoning_score: float, 
                            candidate: ImprovementCandidate) -> float:
        """Calculate confidence in the prioritization"""
        
        # Higher confidence when ML and reasoning agree
        score_agreement = 1.0 - abs(ml_score - reasoning_score)
        
        # Higher confidence for well-defined candidates
        definition_clarity = (
            (1.0 if candidate.estimated_impact > 0 else 0.5) +
            (1.0 if candidate.estimated_effort > 0 else 0.5) +
            (1.0 if candidate.performance_data else 0.5)
        ) / 3.0
        
        # Combine factors
        confidence = (score_agreement * 0.6) + (definition_clarity * 0.4)
        return max(0.0, min(1.0, confidence))
    
    def _recommend_timeline(self, 
                          priority: ImprovementPriority, 
                          candidate: ImprovementCandidate) -> str:
        """Recommend implementation timeline based on priority and effort"""
        
        effort_multiplier = 1.0 + candidate.estimated_effort
        
        base_timelines = {
            ImprovementPriority.CRITICAL: 1,    # 1 day base
            ImprovementPriority.HIGH: 3,        # 3 days base
            ImprovementPriority.MEDIUM: 7,      # 1 week base
            ImprovementPriority.LOW: 14,        # 2 weeks base
            ImprovementPriority.DEFERRED: 30    # 1 month base
        }
        
        base_days = base_timelines.get(priority, 7)
        estimated_days = int(base_days * effort_multiplier)
        
        if estimated_days <= 1:
            return "Immediate (within 24 hours)"
        elif estimated_days <= 3:
            return f"Short-term ({estimated_days} days)"
        elif estimated_days <= 14:
            return f"Medium-term ({estimated_days} days)"
        else:
            return f"Long-term ({estimated_days} days)"
    
    def get_prioritization_statistics(self) -> Dict[str, Any]:
        """Get statistics about prioritization performance"""
        if not self.prioritization_history:
            return {"message": "No prioritization history available"}
        
        total_prioritizations = len(self.prioritization_history)
        
        # Priority distribution
        priority_counts = {}
        confidence_sum = 0
        
        for result in self.prioritization_history:
            priority = result.final_priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            confidence_sum += result.confidence
        
        avg_confidence = confidence_sum / total_prioritizations
        
        return {
            "total_prioritizations": total_prioritizations,
            "priority_distribution": priority_counts,
            "average_confidence": avg_confidence,
            "vertex_ai_available": self.vertex_predictor.initialized,
            "last_prioritization": self.prioritization_history[-1].candidate.timestamp.isoformat()
        }
