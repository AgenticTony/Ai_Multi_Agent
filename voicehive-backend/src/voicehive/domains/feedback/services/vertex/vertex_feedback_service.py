"""
Vertex AI Feedback Service - Analyzes call transcripts and generates prompt improvements
"""
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Google Cloud imports
try:
    from google.cloud import aiplatform
    from google.cloud import secretmanager
    from google.oauth2 import service_account
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False
    aiplatform = None
    secretmanager = None
    service_account = None

# OpenAI fallback
from openai import OpenAI

# Local imports
import sys
sys.path.append('..')
from memory.mem0 import memory_system

logger = logging.getLogger(__name__)


@dataclass
class CallAnalysis:
    """Call analysis result structure"""
    call_id: str
    transcript: str
    issues_found: List[str]
    missed_opportunities: List[str]
    positive_patterns: List[str]
    improvement_suggestions: List[str]
    sentiment_score: float
    booking_success: bool
    transfer_required: bool
    analysis_timestamp: str


@dataclass
class FeedbackSummary:
    """Daily feedback summary structure"""
    date: str
    total_calls_analyzed: int
    common_issues: List[Dict[str, Any]]
    improvement_suggestions: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    recommended_prompt_changes: List[Dict[str, Any]]


class VertexFeedbackService:
    """Vertex AI service for analyzing call transcripts and generating feedback"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.vertex_client = None
        self.secret_client = None
        
        # Initialize Vertex AI if available
        if VERTEX_AVAILABLE and self.project_id:
            try:
                self._initialize_vertex_ai()
                logger.info("Vertex AI initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI: {str(e)}")
        else:
            logger.warning("Vertex AI not available, using OpenAI fallback")
    
    def _initialize_vertex_ai(self):
        """Initialize Vertex AI client"""
        try:
            # Initialize Vertex AI
            aiplatform.init(project=self.project_id, location=self.location)
            
            # Initialize Secret Manager
            self.secret_client = secretmanager.SecretManagerServiceClient()
            
            logger.info(f"Vertex AI initialized for project {self.project_id}")
            
        except Exception as e:
            logger.error(f"Error initializing Vertex AI: {str(e)}")
            raise
    
    async def analyze_daily_transcripts(self, date: str = None) -> FeedbackSummary:
        """
        Analyze transcripts from the last 24 hours and generate feedback
        
        Args:
            date: Optional date string (YYYY-MM-DD), defaults to yesterday
            
        Returns:
            FeedbackSummary with analysis results
        """
        try:
            if not date:
                yesterday = datetime.now() - timedelta(days=1)
                date = yesterday.strftime('%Y-%m-%d')
            
            logger.info(f"Analyzing transcripts for date: {date}")
            
            # Get transcripts from memory system
            transcripts = await self._get_transcripts_for_date(date)
            
            if not transcripts:
                logger.warning(f"No transcripts found for date {date}")
                return self._create_empty_feedback_summary(date)
            
            # Analyze each call
            call_analyses = []
            for transcript_data in transcripts:
                analysis = await self._analyze_single_call(transcript_data)
                if analysis:
                    call_analyses.append(analysis)
            
            # Generate summary feedback
            feedback_summary = await self._generate_feedback_summary(date, call_analyses)
            
            logger.info(f"Completed analysis of {len(call_analyses)} calls for {date}")
            
            return feedback_summary
            
        except Exception as e:
            logger.error(f"Error analyzing daily transcripts: {str(e)}")
            return self._create_empty_feedback_summary(date or "unknown")
    
    async def _get_transcripts_for_date(self, date: str) -> List[Dict[str, Any]]:
        """Get all transcripts for a specific date from memory system"""
        try:
            # Search for memories from the specified date
            search_query = f"date:{date}"
            search_result = memory_system.search_memories(search_query, limit=100)
            
            if not search_result["success"]:
                logger.warning(f"Failed to search memories for date {date}")
                return []
            
            transcripts = []
            for memory in search_result.get("results", []):
                metadata = memory.get("metadata", {})
                
                # Filter for conversation memories from the target date
                if (metadata.get("memory_type") == "conversation" and 
                    metadata.get("timestamp", "").startswith(date)):
                    
                    transcripts.append({
                        "call_id": metadata.get("call_id", "unknown"),
                        "session_id": metadata.get("session_id", "unknown"),
                        "content": memory.get("content", ""),
                        "timestamp": metadata.get("timestamp"),
                        "user_name": metadata.get("user_name"),
                        "user_phone": metadata.get("user_phone")
                    })
            
            logger.info(f"Found {len(transcripts)} transcripts for date {date}")
            return transcripts
            
        except Exception as e:
            logger.error(f"Error getting transcripts for date {date}: {str(e)}")
            return []
    
    async def _analyze_single_call(self, transcript_data: Dict[str, Any]) -> Optional[CallAnalysis]:
        """Analyze a single call transcript"""
        try:
            call_id = transcript_data.get("call_id", "unknown")
            transcript = transcript_data.get("content", "")
            
            if not transcript.strip():
                logger.warning(f"Empty transcript for call {call_id}")
                return None
            
            # Use OpenAI for analysis (can be switched to Vertex AI Gemini later)
            analysis_prompt = self._create_analysis_prompt(transcript)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert call analysis AI that evaluates voice assistant conversations for improvement opportunities."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse the analysis response
            analysis_text = response.choices[0].message.content
            analysis_data = self._parse_analysis_response(analysis_text)
            
            return CallAnalysis(
                call_id=call_id,
                transcript=transcript,
                issues_found=analysis_data.get("issues_found", []),
                missed_opportunities=analysis_data.get("missed_opportunities", []),
                positive_patterns=analysis_data.get("positive_patterns", []),
                improvement_suggestions=analysis_data.get("improvement_suggestions", []),
                sentiment_score=analysis_data.get("sentiment_score", 0.5),
                booking_success=analysis_data.get("booking_success", False),
                transfer_required=analysis_data.get("transfer_required", False),
                analysis_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing call {transcript_data.get('call_id')}: {str(e)}")
            return None
    
    def _create_analysis_prompt(self, transcript: str) -> str:
        """Create analysis prompt for AI evaluation"""
        return f"""
Analyze this voice assistant call transcript and provide a detailed evaluation:

TRANSCRIPT:
{transcript}

Please analyze the conversation and provide a JSON response with the following structure:
{{
    "issues_found": ["list of specific issues or problems in the conversation"],
    "missed_opportunities": ["list of missed booking or sales opportunities"],
    "positive_patterns": ["list of things the assistant did well"],
    "improvement_suggestions": ["specific suggestions for improving the assistant's responses"],
    "sentiment_score": 0.0-1.0 (customer satisfaction estimate),
    "booking_success": true/false (was an appointment successfully booked),
    "transfer_required": true/false (was the call transferred to a human)
}}

Focus on:
1. Communication clarity and professionalism
2. Objection handling effectiveness
3. Information gathering completeness
4. Booking process efficiency
5. Customer satisfaction indicators
6. Missed opportunities for engagement
7. Response appropriateness and timing

Provide specific, actionable feedback that could improve future conversations.
"""
    
    def _parse_analysis_response(self, analysis_text: str) -> Dict[str, Any]:
        """Parse AI analysis response into structured data"""
        try:
            # Try to extract JSON from the response
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = analysis_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback parsing if JSON not found
                return self._fallback_parse_analysis(analysis_text)
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from analysis response, using fallback")
            return self._fallback_parse_analysis(analysis_text)
    
    def _fallback_parse_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Fallback parsing when JSON extraction fails"""
        return {
            "issues_found": ["Analysis parsing failed - manual review needed"],
            "missed_opportunities": [],
            "positive_patterns": [],
            "improvement_suggestions": ["Improve analysis response parsing"],
            "sentiment_score": 0.5,
            "booking_success": False,
            "transfer_required": False
        }
    
    async def _generate_feedback_summary(self, date: str, call_analyses: List[CallAnalysis]) -> FeedbackSummary:
        """Generate summary feedback from individual call analyses"""
        try:
            if not call_analyses:
                return self._create_empty_feedback_summary(date)
            
            # Aggregate issues and patterns
            all_issues = []
            all_opportunities = []
            all_suggestions = []
            all_positive = []
            
            total_sentiment = 0
            booking_successes = 0
            transfers = 0
            
            for analysis in call_analyses:
                all_issues.extend(analysis.issues_found)
                all_opportunities.extend(analysis.missed_opportunities)
                all_suggestions.extend(analysis.improvement_suggestions)
                all_positive.extend(analysis.positive_patterns)
                
                total_sentiment += analysis.sentiment_score
                if analysis.booking_success:
                    booking_successes += 1
                if analysis.transfer_required:
                    transfers += 1
            
            # Count frequency of issues and suggestions
            common_issues = self._count_and_rank_items(all_issues)
            improvement_suggestions = self._count_and_rank_items(all_suggestions)
            
            # Calculate performance metrics
            total_calls = len(call_analyses)
            performance_metrics = {
                "average_sentiment": total_sentiment / total_calls if total_calls > 0 else 0,
                "booking_success_rate": booking_successes / total_calls if total_calls > 0 else 0,
                "transfer_rate": transfers / total_calls if total_calls > 0 else 0,
                "total_calls": total_calls
            }
            
            # Generate prompt change recommendations
            prompt_changes = await self._generate_prompt_recommendations(
                common_issues, improvement_suggestions, performance_metrics
            )
            
            return FeedbackSummary(
                date=date,
                total_calls_analyzed=total_calls,
                common_issues=common_issues[:10],  # Top 10
                improvement_suggestions=improvement_suggestions[:10],  # Top 10
                performance_metrics=performance_metrics,
                recommended_prompt_changes=prompt_changes
            )
            
        except Exception as e:
            logger.error(f"Error generating feedback summary: {str(e)}")
            return self._create_empty_feedback_summary(date)
    
    def _count_and_rank_items(self, items: List[str]) -> List[Dict[str, Any]]:
        """Count frequency of items and rank by occurrence"""
        item_counts = {}
        for item in items:
            item_counts[item] = item_counts.get(item, 0) + 1
        
        # Sort by frequency
        sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"item": item, "frequency": count, "percentage": count / len(items) * 100}
            for item, count in sorted_items
        ]
    
    async def _generate_prompt_recommendations(self, common_issues: List[Dict], 
                                             suggestions: List[Dict], 
                                             metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate specific prompt change recommendations"""
        try:
            # Create recommendation prompt
            recommendation_prompt = f"""
Based on call analysis data, generate specific prompt improvements:

COMMON ISSUES (top 5):
{json.dumps(common_issues[:5], indent=2)}

IMPROVEMENT SUGGESTIONS (top 5):
{json.dumps(suggestions[:5], indent=2)}

PERFORMANCE METRICS:
{json.dumps(metrics, indent=2)}

Generate 3-5 specific prompt modifications that would address these issues. 
For each recommendation, provide:
1. The specific change to make
2. The rationale (which issue it addresses)
3. The expected impact
4. Priority level (high/medium/low)

Format as JSON array of recommendations.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert prompt engineer specializing in voice assistant optimization."},
                    {"role": "user", "content": recommendation_prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            recommendations_text = response.choices[0].message.content
            
            # Parse recommendations
            try:
                start_idx = recommendations_text.find('[')
                end_idx = recommendations_text.rfind(']') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = recommendations_text[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    return self._create_default_recommendations()
                    
            except json.JSONDecodeError:
                logger.warning("Failed to parse prompt recommendations")
                return self._create_default_recommendations()
                
        except Exception as e:
            logger.error(f"Error generating prompt recommendations: {str(e)}")
            return self._create_default_recommendations()
    
    def _create_default_recommendations(self) -> List[Dict[str, Any]]:
        """Create default recommendations when generation fails"""
        return [
            {
                "change": "Add more empathetic language patterns",
                "rationale": "Improve customer satisfaction scores",
                "expected_impact": "Higher sentiment scores",
                "priority": "medium"
            }
        ]
    
    def _create_empty_feedback_summary(self, date: str) -> FeedbackSummary:
        """Create empty feedback summary when no data available"""
        return FeedbackSummary(
            date=date,
            total_calls_analyzed=0,
            common_issues=[],
            improvement_suggestions=[],
            performance_metrics={
                "average_sentiment": 0.0,
                "booking_success_rate": 0.0,
                "transfer_rate": 0.0,
                "total_calls": 0
            },
            recommended_prompt_changes=[]
        )
    
    async def save_feedback_to_file(self, feedback_summary: FeedbackSummary) -> bool:
        """Save feedback summary to the improvements file"""
        try:
            # Load current improvements file
            improvements_file = "../improvements/prompt_updates.json"
            
            try:
                with open(improvements_file, 'r') as f:
                    improvements_data = json.load(f)
            except FileNotFoundError:
                improvements_data = {
                    "version": "1.0.0",
                    "last_updated": datetime.now().isoformat(),
                    "current_prompt_version": "v1.0",
                    "prompt_history": [],
                    "pending_improvements": [],
                    "feedback_analysis": {}
                }
            
            # Update with new feedback
            improvements_data["feedback_analysis"] = {
                "date": feedback_summary.date,
                "total_calls_analyzed": feedback_summary.total_calls_analyzed,
                "common_issues": feedback_summary.common_issues,
                "improvement_suggestions": feedback_summary.improvement_suggestions,
                "performance_metrics": feedback_summary.performance_metrics,
                "last_analysis_date": datetime.now().isoformat()
            }
            
            # Add pending improvements
            for recommendation in feedback_summary.recommended_prompt_changes:
                improvements_data["pending_improvements"].append({
                    "id": f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "recommendation": recommendation,
                    "status": "pending",
                    "created_date": datetime.now().isoformat()
                })
            
            improvements_data["last_updated"] = datetime.now().isoformat()
            
            # Save updated file
            with open(improvements_file, 'w') as f:
                json.dump(improvements_data, f, indent=2)
            
            logger.info(f"Feedback summary saved for date {feedback_summary.date}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving feedback to file: {str(e)}")
            return False


# Global service instance
feedback_service = VertexFeedbackService()


# Convenience functions
async def analyze_daily_calls(date: str = None) -> FeedbackSummary:
    """Analyze calls for a specific date"""
    return await feedback_service.analyze_daily_transcripts(date)


async def run_daily_feedback_pipeline(date: str = None) -> bool:
    """Run the complete daily feedback pipeline"""
    try:
        # Analyze transcripts
        feedback_summary = await feedback_service.analyze_daily_transcripts(date)
        
        # Save results
        success = await feedback_service.save_feedback_to_file(feedback_summary)
        
        if success:
            logger.info(f"Daily feedback pipeline completed successfully for {feedback_summary.date}")
            logger.info(f"Analyzed {feedback_summary.total_calls_analyzed} calls")
            logger.info(f"Generated {len(feedback_summary.recommended_prompt_changes)} recommendations")
        
        return success
        
    except Exception as e:
        logger.error(f"Error running daily feedback pipeline: {str(e)}")
        return False
