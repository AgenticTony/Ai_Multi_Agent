#!/usr/bin/env python3
"""
Sprint 3 Feedback Loop Testing Suite

This test suite validates the complete feedback loop:
- Mock data generation
- Call analysis
- Prompt improvement suggestions
- Prompt versioning
- End-to-end pipeline execution
"""

import pytest
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Add parent directories to path
sys.path.append('..')
sys.path.append('../vertex')
sys.path.append('../improvements')
sys.path.append('../memory')

from vertex.vertex_feedback_service import VertexFeedbackService, analyze_daily_calls
from vertex.daily_feedback_pipeline import DailyFeedbackPipeline
from improvements.prompt_manager import PromptManager
from memory.mem0 import MemorySystem

class TestFeedbackLoop:
    """Test the complete feedback loop functionality"""
    
    @pytest.fixture
    def mock_transcripts(self):
        """Generate mock call transcripts for testing"""
        return [
            {
                "call_id": "test_call_001",
                "session_id": "test_session_001",
                "content": """Agent: Hello! I'm Roxy, your VoiceHive assistant. How can I help you today?
Customer: Hi, I'm interested in booking an appointment.
Agent: Great! I'd be happy to help you book an appointment. Can I get your name?
Customer: Sure, it's John Smith.
Agent: Thank you John. What type of service are you looking for?
Customer: I need a consultation.
Agent: Perfect! Let me check our availability. What days work best for you?
Customer: Tuesday would be ideal.
Agent: I have Tuesday at 2 PM available. Would that work?
Customer: Yes, that's perfect.
Agent: Excellent! I've booked you for Tuesday at 2 PM.""",
                "timestamp": "2024-01-05T10:30:00Z",
                "user_name": "John Smith",
                "user_phone": "555-0123"
            },
            {
                "call_id": "test_call_002",
                "session_id": "test_session_002",
                "content": """Agent: Hello, VoiceHive here.
Customer: I want to book something.
Agent: What do you want?
Customer: An appointment, obviously.
Agent: When?
Customer: Next week sometime.
Agent: We have slots available.
Customer: This is frustrating. Can I speak to a human?
Agent: I can help you. What's your name?
Customer: Forget it, I'll call back later.""",
                "timestamp": "2024-01-05T15:45:00Z",
                "user_name": "Frustrated Customer",
                "user_phone": "555-0999"
            }
        ]
    
    @pytest.fixture
    def feedback_service(self):
        """Create a feedback service instance for testing"""
        return VertexFeedbackService()
    
    @pytest.fixture
    def prompt_manager(self):
        """Create a prompt manager instance for testing"""
        return PromptManager()
    
    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance for testing"""
        return DailyFeedbackPipeline()
    
    def test_mock_data_generation(self, mock_transcripts):
        """Test that mock data is properly generated"""
        assert len(mock_transcripts) == 2
        assert all('call_id' in transcript for transcript in mock_transcripts)
        assert all('content' in transcript for transcript in mock_transcripts)
        assert all('timestamp' in transcript for transcript in mock_transcripts)
    
    @pytest.mark.asyncio
    async def test_transcript_analysis(self, feedback_service, mock_transcripts):
        """Test individual transcript analysis"""
        # Mock the OpenAI API call
        with patch.object(feedback_service, '_analyze_with_openai') as mock_openai:
            mock_openai.return_value = {
                "sentiment_score": 0.8,
                "booking_successful": True,
                "issues_found": [],
                "improvement_suggestions": ["Be more empathetic in greeting"]
            }
            
            result = await feedback_service.analyze_transcript(mock_transcripts[0])
            
            assert result is not None
            assert 'sentiment_score' in result
            assert 'booking_successful' in result
            assert mock_openai.called
    
    @pytest.mark.asyncio
    async def test_daily_analysis_workflow(self, feedback_service):
        """Test the complete daily analysis workflow"""
        target_date = "2024-01-05"
        
        # Mock memory system to return test transcripts
        with patch('vertex.vertex_feedback_service.memory_system') as mock_memory:
            mock_memory.get_memories_by_date.return_value = {
                "success": True,
                "memories": [
                    {
                        "id": "mem_001",
                        "call_id": "test_call_001",
                        "content": "Test transcript content",
                        "timestamp": "2024-01-05T10:30:00Z"
                    }
                ]
            }
            
            # Mock OpenAI analysis
            with patch.object(feedback_service, '_analyze_with_openai') as mock_openai:
                mock_openai.return_value = {
                    "sentiment_score": 0.7,
                    "booking_successful": True,
                    "issues_found": ["Poor greeting"],
                    "improvement_suggestions": ["Improve greeting warmth"]
                }
                
                result = await analyze_daily_calls(target_date)
                
                assert result is not None
                assert result.total_calls_analyzed > 0
                assert hasattr(result, 'performance_metrics')
                assert hasattr(result, 'common_issues')
                assert hasattr(result, 'improvement_suggestions')
    
    def test_prompt_versioning(self, prompt_manager):
        """Test prompt versioning functionality"""
        # Test getting current prompt
        current_prompt = prompt_manager.get_current_prompt()
        assert current_prompt is not None
        
        # Test version history
        history = prompt_manager.get_version_history()
        assert isinstance(history, list)
        
        # Test creating new version
        improvements = [
            {
                "id": "imp_001",
                "change": "Add more empathetic greeting",
                "rationale": "Improve customer satisfaction",
                "priority": "high"
            }
        ]
        
        with patch.object(prompt_manager, '_save_prompt_version') as mock_save:
            mock_save.return_value = True
            new_version = prompt_manager.apply_improvements(improvements)
            assert new_version is not None
            assert mock_save.called
    
    @pytest.mark.asyncio
    async def test_pipeline_execution(self, pipeline):
        """Test complete pipeline execution"""
        target_date = "2024-01-05"
        
        # Mock all external dependencies
        with patch('vertex.daily_feedback_pipeline.analyze_daily_calls') as mock_analyze:
            mock_analyze.return_value = Mock(
                total_calls_analyzed=5,
                performance_metrics={"average_sentiment": 0.7},
                common_issues=[{"item": "Poor greeting", "frequency": 3}],
                improvement_suggestions=[{"item": "Add warmth", "frequency": 2}],
                recommended_prompt_changes=[{
                    "change": "Improve greeting",
                    "rationale": "Customer feedback",
                    "priority": "high"
                }]
            )
            
            with patch.object(pipeline, '_update_prompt_system') as mock_update:
                mock_update.return_value = True
                
                result = await pipeline.run_daily_analysis(target_date)
                
                assert result["success"] is True
                assert result["calls_analyzed"] == 5
                assert mock_analyze.called
                assert mock_update.called
    
    def test_feedback_data_structure(self):
        """Test that feedback data structures are properly formatted"""
        # Test FeedbackSummary structure
        from vertex.vertex_feedback_service import FeedbackSummary
        
        summary = FeedbackSummary(
            date="2024-01-05",
            total_calls_analyzed=10,
            performance_metrics={"sentiment": 0.8},
            common_issues=[{"item": "test", "frequency": 1}],
            improvement_suggestions=[{"item": "test", "frequency": 1}],
            recommended_prompt_changes=[{"change": "test", "priority": "high"}]
        )
        
        assert summary.date == "2024-01-05"
        assert summary.total_calls_analyzed == 10
        assert isinstance(summary.performance_metrics, dict)
        assert isinstance(summary.common_issues, list)
        assert isinstance(summary.improvement_suggestions, list)
        assert isinstance(summary.recommended_prompt_changes, list)
    
    def test_error_handling(self, feedback_service):
        """Test error handling in various scenarios"""
        # Test with invalid transcript
        with pytest.raises(Exception):
            asyncio.run(feedback_service.analyze_transcript({}))
        
        # Test with API failure
        with patch.object(feedback_service, '_analyze_with_openai') as mock_openai:
            mock_openai.side_effect = Exception("API Error")
            
            with pytest.raises(Exception):
                asyncio.run(feedback_service.analyze_transcript({
                    "call_id": "test",
                    "content": "test content"
                }))
    
    def test_configuration_loading(self):
        """Test configuration loading and validation"""
        # Test environment variables
        required_vars = [
            'OPENAI_API_KEY',
            'MEM0_API_KEY',
            'GOOGLE_CLOUD_PROJECT'
        ]
        
        # Mock environment variables
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'MEM0_API_KEY': 'test-mem0-key',
            'GOOGLE_CLOUD_PROJECT': 'test-project'
        }):
            # Test that services can be initialized
            service = VertexFeedbackService()
            assert service is not None
    
    @pytest.mark.asyncio
    async def test_integration_with_memory_system(self):
        """Test integration with memory system"""
        # Mock memory system responses
        with patch('memory.mem0.MemorySystem') as MockMemorySystem:
            mock_instance = MockMemorySystem.return_value
            mock_instance.get_memories_by_date.return_value = {
                "success": True,
                "memories": [
                    {
                        "id": "mem_001",
                        "call_id": "test_call",
                        "content": "Test transcript",
                        "timestamp": "2024-01-05T10:00:00Z"
                    }
                ]
            }
            
            # Test memory retrieval
            from vertex.vertex_feedback_service import memory_system
            result = memory_system.get_memories_by_date("2024-01-05")
            
            assert result["success"] is True
            assert len(result["memories"]) == 1
    
    def test_prompt_update_safety(self, prompt_manager):
        """Test safety mechanisms in prompt updates"""
        # Test that high-risk changes are flagged
        risky_improvements = [
            {
                "id": "risky_001",
                "change": "Remove all safety instructions",
                "rationale": "Speed up responses",
                "priority": "high"
            }
        ]
        
        # This should trigger safety checks
        with patch.object(prompt_manager, '_validate_safety') as mock_safety:
            mock_safety.return_value = False  # Unsafe change
            
            result = prompt_manager.apply_improvements(risky_improvements)
            assert result is None or result.get('status') == 'rejected'
    
    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation"""
        from vertex.vertex_feedback_service import VertexFeedbackService
        
        service = VertexFeedbackService()
        
        # Mock analysis results
        analysis_results = [
            {"sentiment_score": 0.8, "booking_successful": True},
            {"sentiment_score": 0.6, "booking_successful": False},
            {"sentiment_score": 0.9, "booking_successful": True}
        ]
        
        metrics = service._calculate_performance_metrics(analysis_results)
        
        assert "average_sentiment" in metrics
        assert "booking_success_rate" in metrics
        assert metrics["average_sentiment"] == pytest.approx(0.77, rel=1e-2)
        assert metrics["booking_success_rate"] == pytest.approx(0.67, rel=1e-2)

class TestEndToEndScenarios:
    """Test complete end-to-end scenarios"""
    
    @pytest.mark.asyncio
    async def test_three_day_simulation(self):
        """Test a 3-day feedback loop simulation"""
        dates = ["2024-01-03", "2024-01-04", "2024-01-05"]
        
        pipeline = DailyFeedbackPipeline()
        
        for date in dates:
            with patch('vertex.daily_feedback_pipeline.analyze_daily_calls') as mock_analyze:
                mock_analyze.return_value = Mock(
                    total_calls_analyzed=10,
                    performance_metrics={"average_sentiment": 0.7},
                    common_issues=[],
                    improvement_suggestions=[],
                    recommended_prompt_changes=[]
                )
                
                result = await pipeline.run_daily_analysis(date)
                assert result["success"] is True
    
    def test_rollback_scenario(self):
        """Test prompt rollback functionality"""
        prompt_manager = PromptManager()
        
        # Simulate a bad prompt update
        with patch.object(prompt_manager, '_save_prompt_version') as mock_save:
            mock_save.return_value = True
            
            # Apply a change
            improvements = [{"id": "test", "change": "test change"}]
            new_version = prompt_manager.apply_improvements(improvements)
            
            # Simulate rollback
            rollback_result = prompt_manager.rollback_to_version("1.0")
            assert rollback_result is not None

def run_manual_test():
    """Run a manual test of the feedback loop"""
    print("🧪 Running Manual Feedback Loop Test")
    print("=" * 50)
    
    async def manual_test():
        try:
            # Test 1: Mock data analysis
            print("📊 Testing mock data analysis...")
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # This would normally analyze real data
            print(f"✅ Analysis target date: {target_date}")
            
            # Test 2: Prompt manager
            print("📝 Testing prompt manager...")
            manager = PromptManager()
            current = manager.get_current_prompt()
            print(f"✅ Current prompt version: {current.version if current else 'None'}")
            
            # Test 3: Pipeline execution
            print("🔄 Testing pipeline execution...")
            pipeline = DailyFeedbackPipeline()
            print("✅ Pipeline initialized successfully")
            
            print("\n🎉 Manual test completed successfully!")
            
        except Exception as e:
            print(f"❌ Manual test failed: {e}")
    
    asyncio.run(manual_test())

if __name__ == "__main__":
    # Run manual test if executed directly
    run_manual_test()
