"""
Cross-System Learning Engine for VoiceHive Phase 3

This module implements federated learning patterns for multi-deployment insights,
knowledge transfer between VoiceHive instances, and global pattern recognition.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from voicehive.services.ai.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class LearningType(Enum):
    """Types of cross-system learning"""
    PERFORMANCE_PATTERNS = "performance_patterns"
    ERROR_PATTERNS = "error_patterns"
    OPTIMIZATION_STRATEGIES = "optimization_strategies"
    USER_BEHAVIOR = "user_behavior"
    SYSTEM_CONFIGURATIONS = "system_configurations"
    ANOMALY_DETECTION = "anomaly_detection"


class DataSensitivity(Enum):
    """Data sensitivity levels for privacy protection"""
    PUBLIC = "public"
    AGGREGATED = "aggregated"
    ANONYMIZED = "anonymized"
    CONFIDENTIAL = "confidential"


class LearningStatus(Enum):
    """Status of learning processes"""
    COLLECTING = "collecting"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    SHARING = "sharing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class LearningData:
    """Represents learning data from a system"""
    id: str
    system_id: str
    learning_type: LearningType
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    sensitivity: DataSensitivity
    timestamp: datetime = field(default_factory=datetime.now)
    anonymized: bool = False
    hash_signature: str = ""


@dataclass
class LearningInsight:
    """Represents an insight derived from cross-system learning"""
    id: str
    insight_type: LearningType
    description: str
    confidence: float
    supporting_systems: List[str]
    applicable_contexts: List[str]
    recommendations: List[str]
    evidence: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class KnowledgeTransfer:
    """Represents knowledge transfer between systems"""
    id: str
    source_system: str
    target_systems: List[str]
    knowledge_type: LearningType
    transfer_data: Dict[str, Any]
    success_metrics: Dict[str, float]
    status: LearningStatus = LearningStatus.COLLECTING
    created_at: datetime = field(default_factory=datetime.now)


class CrossSystemLearning:
    """
    Advanced cross-system learning engine for VoiceHive deployments.
    
    Implements federated learning patterns, privacy-preserving knowledge sharing,
    and global optimization insights across multiple VoiceHive instances.
    """
    
    def __init__(self, system_id: str, openai_service: Optional[OpenAIService] = None):
        self.system_id = system_id
        self.openai_service = openai_service or OpenAIService()
        
        # Learning data storage
        self.local_data: Dict[str, LearningData] = {}
        self.shared_insights: Dict[str, LearningInsight] = {}
        self.knowledge_transfers: Dict[str, KnowledgeTransfer] = {}
        
        # Connected systems for federated learning
        self.connected_systems: Set[str] = set()
        self.trust_scores: Dict[str, float] = {}  # Trust scores for other systems
        
        # Privacy and security settings
        self.privacy_settings = {
            "allow_data_sharing": True,
            "anonymization_required": True,
            "min_trust_score": 0.7,
            "max_sharing_frequency": timedelta(hours=1)
        }
        
        # Learning configuration
        self.learning_config = {
            "min_samples_for_insight": 5,
            "confidence_threshold": 0.75,
            "max_insight_age_days": 30,
            "enable_real_time_learning": True
        }
        
        # Performance metrics
        self.metrics = {
            "total_data_points": 0,
            "insights_generated": 0,
            "successful_transfers": 0,
            "failed_transfers": 0,
            "average_insight_confidence": 0.0,
            "systems_connected": 0
        }
        
        logger.info(f"Cross-system learning initialized for system: {system_id}")
    
    def add_learning_data(
        self,
        learning_type: LearningType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        sensitivity: DataSensitivity = DataSensitivity.AGGREGATED
    ) -> str:
        """Add learning data to the system"""
        data_id = f"data_{len(self.local_data) + 1}_{int(datetime.now().timestamp())}"
        
        # Anonymize data if required
        processed_data = data.copy()
        anonymized = False
        
        if self.privacy_settings["anonymization_required"] and sensitivity != DataSensitivity.PUBLIC:
            processed_data = self._anonymize_data(processed_data, learning_type)
            anonymized = True
        
        # Generate hash signature for integrity
        hash_signature = self._generate_data_hash(processed_data)
        
        learning_data = LearningData(
            id=data_id,
            system_id=self.system_id,
            learning_type=learning_type,
            data=processed_data,
            metadata=metadata or {},
            sensitivity=sensitivity,
            anonymized=anonymized,
            hash_signature=hash_signature
        )
        
        self.local_data[data_id] = learning_data
        self.metrics["total_data_points"] += 1
        
        logger.info(f"Added learning data: {learning_type.value} (ID: {data_id})")
        
        # Trigger real-time learning if enabled
        if self.learning_config["enable_real_time_learning"]:
            asyncio.create_task(self._process_new_data(learning_data))
        
        return data_id
    
    def _anonymize_data(self, data: Dict[str, Any], learning_type: LearningType) -> Dict[str, Any]:
        """Anonymize sensitive data while preserving learning value"""
        anonymized = data.copy()
        
        # Remove or hash personally identifiable information
        sensitive_fields = ["user_id", "phone", "email", "name", "address"]
        
        for field in sensitive_fields:
            if field in anonymized:
                if isinstance(anonymized[field], str):
                    # Replace with hash
                    anonymized[field] = hashlib.sha256(anonymized[field].encode()).hexdigest()[:8]
                else:
                    # Remove non-string sensitive data
                    del anonymized[field]
        
        # Add noise to numerical values for differential privacy
        for key, value in anonymized.items():
            if isinstance(value, (int, float)) and key not in ["timestamp", "duration"]:
                # Add small amount of noise (1% of value)
                noise = np.random.normal(0, abs(value) * 0.01)
                anonymized[key] = value + noise
        
        return anonymized
    
    def _generate_data_hash(self, data: Dict[str, Any]) -> str:
        """Generate hash signature for data integrity"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def _process_new_data(self, learning_data: LearningData):
        """Process new learning data for immediate insights"""
        try:
            # Check if we have enough similar data for pattern recognition
            similar_data = [
                ld for ld in self.local_data.values()
                if ld.learning_type == learning_data.learning_type
                and ld.id != learning_data.id
            ]
            
            if len(similar_data) >= self.learning_config["min_samples_for_insight"]:
                await self._generate_local_insights(learning_data.learning_type)
                
        except Exception as e:
            logger.error(f"Failed to process new data: {str(e)}")
    
    async def generate_insights(self, learning_type: Optional[LearningType] = None) -> List[LearningInsight]:
        """Generate insights from collected learning data"""
        logger.info("Generating cross-system learning insights")
        
        insights = []
        learning_types = [learning_type] if learning_type else list(LearningType)
        
        for lt in learning_types:
            try:
                type_insights = await self._generate_local_insights(lt)
                insights.extend(type_insights)
            except Exception as e:
                logger.error(f"Failed to generate insights for {lt.value}: {str(e)}")
        
        # Update metrics
        self.metrics["insights_generated"] += len(insights)
        if insights:
            avg_confidence = sum(i.confidence for i in insights) / len(insights)
            self.metrics["average_insight_confidence"] = avg_confidence
        
        logger.info(f"Generated {len(insights)} insights")
        return insights
    
    async def _generate_local_insights(self, learning_type: LearningType) -> List[LearningInsight]:
        """Generate insights for a specific learning type"""
        # Get relevant data
        relevant_data = [
            ld for ld in self.local_data.values()
            if ld.learning_type == learning_type
        ]
        
        if len(relevant_data) < self.learning_config["min_samples_for_insight"]:
            return []
        
        # Use AI to analyze patterns and generate insights
        insights = await self._ai_pattern_analysis(learning_type, relevant_data)
        
        # Store insights
        for insight in insights:
            self.shared_insights[insight.id] = insight
        
        return insights
    
    async def _ai_pattern_analysis(
        self, 
        learning_type: LearningType, 
        data: List[LearningData]
    ) -> List[LearningInsight]:
        """Use AI to analyze patterns in learning data"""
        try:
            # Prepare data for AI analysis
            data_summary = []
            for ld in data:
                summary = {
                    "system_id": ld.system_id,
                    "timestamp": ld.timestamp.isoformat(),
                    "data_keys": list(ld.data.keys()),
                    "metadata": ld.metadata
                }
                # Include non-sensitive data values
                if ld.sensitivity in [DataSensitivity.PUBLIC, DataSensitivity.AGGREGATED]:
                    summary["sample_data"] = {k: v for k, v in list(ld.data.items())[:5]}
                data_summary.append(summary)
            
            prompt = f"""
            Analyze this cross-system learning data and identify patterns and insights:
            
            Learning Type: {learning_type.value}
            Data Points: {len(data)}
            Data Summary: {json.dumps(data_summary, indent=2)}
            
            Identify:
            1. Common patterns across systems
            2. Performance optimization opportunities
            3. Anomalies or concerning trends
            4. Best practices that could be shared
            5. Actionable recommendations
            
            For each insight, provide:
            - Description of the pattern/insight
            - Confidence level (0-1)
            - Applicable contexts
            - Specific recommendations
            
            Format as JSON array:
            [
                {{
                    "description": "insight description",
                    "confidence": 0.85,
                    "applicable_contexts": ["context1", "context2"],
                    "recommendations": ["rec1", "rec2"],
                    "evidence": {{"key": "value"}}
                }}
            ]
            """
            
            response = await self.openai_service.generate_response(
                prompt=prompt,
                max_tokens=800,
                temperature=0.3
            )
            
            try:
                ai_insights = json.loads(response)
                insights = []
                
                for ai_insight in ai_insights:
                    if ai_insight.get("confidence", 0) >= self.learning_config["confidence_threshold"]:
                        insight_id = f"insight_{len(self.shared_insights) + 1}_{int(datetime.now().timestamp())}"
                        
                        insight = LearningInsight(
                            id=insight_id,
                            insight_type=learning_type,
                            description=ai_insight.get("description", ""),
                            confidence=float(ai_insight.get("confidence", 0)),
                            supporting_systems=[self.system_id],
                            applicable_contexts=ai_insight.get("applicable_contexts", []),
                            recommendations=ai_insight.get("recommendations", []),
                            evidence=ai_insight.get("evidence", {})
                        )
                        insights.append(insight)
                
                return insights
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI insights")
                return []
                
        except Exception as e:
            logger.error(f"AI pattern analysis failed: {str(e)}")
            return []
    
    async def share_insights_with_systems(
        self, 
        target_systems: List[str], 
        insight_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Share insights with other VoiceHive systems"""
        if not self.privacy_settings["allow_data_sharing"]:
            return {"success": False, "error": "Data sharing disabled"}
        
        # Get insights to share
        if insight_ids:
            insights_to_share = [
                self.shared_insights[iid] for iid in insight_ids 
                if iid in self.shared_insights
            ]
        else:
            # Share recent high-confidence insights
            cutoff_date = datetime.now() - timedelta(days=self.learning_config["max_insight_age_days"])
            insights_to_share = [
                insight for insight in self.shared_insights.values()
                if insight.created_at > cutoff_date and 
                insight.confidence >= self.learning_config["confidence_threshold"]
            ]
        
        if not insights_to_share:
            return {"success": False, "error": "No insights available for sharing"}
        
        # Filter target systems by trust score
        trusted_systems = [
            sys for sys in target_systems
            if self.trust_scores.get(sys, 0) >= self.privacy_settings["min_trust_score"]
        ]
        
        if not trusted_systems:
            return {"success": False, "error": "No trusted target systems"}
        
        # Create knowledge transfer record
        transfer_id = f"transfer_{len(self.knowledge_transfers) + 1}_{int(datetime.now().timestamp())}"
        
        transfer = KnowledgeTransfer(
            id=transfer_id,
            source_system=self.system_id,
            target_systems=trusted_systems,
            knowledge_type=insights_to_share[0].insight_type,  # Assume same type for simplicity
            transfer_data={
                "insights": [insight.__dict__ for insight in insights_to_share],
                "metadata": {
                    "transfer_timestamp": datetime.now().isoformat(),
                    "source_system_metrics": self.metrics
                }
            },
            success_metrics={}
        )
        
        self.knowledge_transfers[transfer_id] = transfer
        
        # Simulate sharing process (in practice, this would use secure communication)
        logger.info(f"Sharing {len(insights_to_share)} insights with {len(trusted_systems)} systems")
        
        # Update metrics
        self.metrics["successful_transfers"] += 1
        
        return {
            "success": True,
            "transfer_id": transfer_id,
            "insights_shared": len(insights_to_share),
            "target_systems": len(trusted_systems)
        }

    async def receive_shared_insights(
        self,
        source_system: str,
        insights_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Receive and process insights shared from another system"""
        try:
            # Verify source system trust
            if self.trust_scores.get(source_system, 0) < self.privacy_settings["min_trust_score"]:
                return {"success": False, "error": "Source system not trusted"}

            # Process received insights
            received_insights = insights_data.get("insights", [])
            processed_count = 0

            for insight_data in received_insights:
                # Create insight object
                insight = LearningInsight(
                    id=f"shared_{insight_data.get('id', 'unknown')}",
                    insight_type=LearningType(insight_data.get("insight_type", "performance_patterns")),
                    description=insight_data.get("description", ""),
                    confidence=float(insight_data.get("confidence", 0)),
                    supporting_systems=insight_data.get("supporting_systems", []),
                    applicable_contexts=insight_data.get("applicable_contexts", []),
                    recommendations=insight_data.get("recommendations", []),
                    evidence=insight_data.get("evidence", {})
                )

                # Validate insight quality
                if await self._validate_shared_insight(insight, source_system):
                    self.shared_insights[insight.id] = insight
                    processed_count += 1

            logger.info(f"Received {processed_count} insights from {source_system}")

            return {
                "success": True,
                "insights_received": len(received_insights),
                "insights_processed": processed_count,
                "source_system": source_system
            }

        except Exception as e:
            logger.error(f"Failed to receive shared insights: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _validate_shared_insight(self, insight: LearningInsight, source_system: str) -> bool:
        """Validate quality and relevance of shared insight"""
        # Check confidence threshold
        if insight.confidence < self.learning_config["confidence_threshold"]:
            return False

        # Check if insight is applicable to this system
        if not insight.applicable_contexts:
            return True  # Generic insights are always applicable

        # In practice, you'd check against system configuration/context
        # For now, accept all insights from trusted sources
        return True

    def connect_to_system(self, system_id: str, trust_score: float = 0.8):
        """Connect to another VoiceHive system for federated learning"""
        self.connected_systems.add(system_id)
        self.trust_scores[system_id] = trust_score
        self.metrics["systems_connected"] = len(self.connected_systems)

        logger.info(f"Connected to system {system_id} with trust score {trust_score}")

    def disconnect_from_system(self, system_id: str):
        """Disconnect from a VoiceHive system"""
        self.connected_systems.discard(system_id)
        if system_id in self.trust_scores:
            del self.trust_scores[system_id]
        self.metrics["systems_connected"] = len(self.connected_systems)

        logger.info(f"Disconnected from system {system_id}")

    async def federated_learning_round(self) -> Dict[str, Any]:
        """Perform a round of federated learning with connected systems"""
        if not self.connected_systems:
            return {"success": False, "error": "No connected systems"}

        logger.info(f"Starting federated learning round with {len(self.connected_systems)} systems")

        try:
            # Generate local insights
            local_insights = await self.generate_insights()

            # Share insights with connected systems
            sharing_results = []
            for system_id in self.connected_systems:
                result = await self.share_insights_with_systems([system_id])
                sharing_results.append(result)

            # Aggregate results
            successful_shares = sum(1 for r in sharing_results if r.get("success", False))
            total_insights_shared = sum(r.get("insights_shared", 0) for r in sharing_results)

            # Generate federated insights summary
            federated_summary = await self._generate_federated_summary()

            return {
                "success": True,
                "local_insights_generated": len(local_insights),
                "systems_contacted": len(self.connected_systems),
                "successful_shares": successful_shares,
                "total_insights_shared": total_insights_shared,
                "federated_summary": federated_summary
            }

        except Exception as e:
            logger.error(f"Federated learning round failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _generate_federated_summary(self) -> Dict[str, Any]:
        """Generate summary of federated learning insights"""
        try:
            # Analyze insights from multiple systems
            all_insights = list(self.shared_insights.values())

            if not all_insights:
                return {"message": "No insights available"}

            # Group insights by type
            insights_by_type = {}
            for insight in all_insights:
                insight_type = insight.insight_type.value
                if insight_type not in insights_by_type:
                    insights_by_type[insight_type] = []
                insights_by_type[insight_type].append(insight)

            # Generate AI-powered federated analysis
            prompt = f"""
            Analyze these federated learning insights from multiple VoiceHive systems:

            Connected Systems: {len(self.connected_systems)}
            Total Insights: {len(all_insights)}
            Insights by Type: {json.dumps({k: len(v) for k, v in insights_by_type.items()}, indent=2)}

            Sample Insights:
            {json.dumps([{
                "type": i.insight_type.value,
                "description": i.description,
                "confidence": i.confidence,
                "supporting_systems": len(i.supporting_systems)
            } for i in all_insights[:5]], indent=2)}

            Provide:
            1. Key patterns across all systems
            2. Most valuable insights for optimization
            3. Recommendations for system improvements
            4. Areas needing more data collection

            Format as JSON:
            {{
                "key_patterns": ["pattern1", "pattern2"],
                "top_insights": ["insight1", "insight2"],
                "recommendations": ["rec1", "rec2"],
                "data_gaps": ["gap1", "gap2"]
            }}
            """

            response = await self.openai_service.generate_response(
                prompt=prompt,
                max_tokens=500,
                temperature=0.3
            )

            try:
                summary = json.loads(response)
                return summary
            except json.JSONDecodeError:
                return {"message": "Failed to parse federated analysis"}

        except Exception as e:
            logger.error(f"Failed to generate federated summary: {str(e)}")
            return {"error": "Summary generation failed"}

    def get_learning_dashboard(self) -> Dict[str, Any]:
        """Get cross-system learning dashboard data"""
        # Calculate insight distribution by type
        insight_distribution = {}
        for insight_type in LearningType:
            count = sum(1 for i in self.shared_insights.values() if i.insight_type == insight_type)
            insight_distribution[insight_type.value] = count

        # Get recent high-confidence insights
        recent_insights = []
        cutoff_date = datetime.now() - timedelta(days=7)
        for insight in self.shared_insights.values():
            if insight.created_at > cutoff_date and insight.confidence >= 0.8:
                recent_insights.append({
                    "id": insight.id,
                    "type": insight.insight_type.value,
                    "description": insight.description[:100] + "..." if len(insight.description) > 100 else insight.description,
                    "confidence": insight.confidence,
                    "supporting_systems": len(insight.supporting_systems)
                })

        # Sort by confidence
        recent_insights.sort(key=lambda x: x["confidence"], reverse=True)

        # Calculate trust score distribution
        trust_distribution = {
            "high_trust": sum(1 for score in self.trust_scores.values() if score >= 0.8),
            "medium_trust": sum(1 for score in self.trust_scores.values() if 0.6 <= score < 0.8),
            "low_trust": sum(1 for score in self.trust_scores.values() if score < 0.6)
        }

        return {
            "system_id": self.system_id,
            "summary": {
                "total_data_points": self.metrics["total_data_points"],
                "insights_generated": self.metrics["insights_generated"],
                "connected_systems": len(self.connected_systems),
                "successful_transfers": self.metrics["successful_transfers"]
            },
            "insight_distribution": insight_distribution,
            "recent_high_confidence_insights": recent_insights[:10],
            "trust_distribution": trust_distribution,
            "learning_config": self.learning_config,
            "privacy_settings": self.privacy_settings,
            "performance_metrics": {
                "average_insight_confidence": self.metrics["average_insight_confidence"],
                "transfer_success_rate": (
                    self.metrics["successful_transfers"] /
                    max(self.metrics["successful_transfers"] + self.metrics["failed_transfers"], 1)
                )
            }
        }
