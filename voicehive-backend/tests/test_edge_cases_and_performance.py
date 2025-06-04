#!/usr/bin/env python3
"""
Enhanced Testing Suite for Edge Cases and Performance

This test suite includes:
- Edge case testing for unusual scenarios
- Property-based testing using Hypothesis
- Performance benchmarks
- Load testing scenarios
- Error recovery testing
"""

import pytest
import asyncio
import time
import json
import random
import string
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any
import sys
import os

# Property-based testing
try:
    from hypothesis import given, strategies as st, settings, Verbosity
    from hypothesis.stateful import RuleBasedStateMachine, rule, initialize
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    print("⚠️ Hypothesis not available. Install with: pip install hypothesis")

# Add parent directories to path
sys.path.append('..')
sys.path.append('../vertex')
sys.path.append('../improvements')

from vertex.vertex_feedback_service import VertexFeedbackService, analyze_daily_calls
from vertex.daily_feedback_pipeline import DailyFeedbackPipeline
from improvements.prompt_manager import PromptManager

class TestEdgeCases:
    """Test edge cases and unusual scenarios"""
    
    @pytest.fixture
    def feedback_service(self):
        return VertexFeedbackService()
    
    @pytest.fixture
    def prompt_manager(self):
        return PromptManager()
    
    def test_empty_transcript_analysis(self, feedback_service):
        """Test analysis with empty transcript"""
        empty_transcript = {
            "call_id": "empty_001",
            "content": "",
            "timestamp": "2024-01-05T10:00:00Z"
        }
        
        with patch.object(feedback_service, '_analyze_with_openai') as mock_openai:
            mock_openai.return_value = {
                "sentiment_score": 0.0,
                "booking_successful": False,
                "issues_found": ["Empty transcript"],
                "improvement_suggestions": ["Ensure call recording is working"]
            }
            
            result = asyncio.run(feedback_service.analyze_transcript(empty_transcript))
            assert result is not None
            assert result["sentiment_score"] == 0.0
    
    def test_extremely_long_transcript(self, feedback_service):
        """Test analysis with very long transcript"""
        # Generate a very long transcript (10,000 characters)
        long_content = "Agent: " + "This is a very long conversation. " * 300
        long_transcript = {
            "call_id": "long_001",
            "content": long_content,
            "timestamp": "2024-01-05T10:00:00Z"
        }
        
        with patch.object(feedback_service, '_analyze_with_openai') as mock_openai:
            mock_openai.return_value = {
                "sentiment_score": 0.7,
                "booking_successful": True,
                "issues_found": [],
                "improvement_suggestions": []
            }
            
            start_time = time.time()
            result = asyncio.run(feedback_service.analyze_transcript(long_transcript))
            processing_time = time.time() - start_time
            
            assert result is not None
            assert processing_time < 30  # Should complete within 30 seconds
    
    def test_malformed_transcript_data(self, feedback_service):
        """Test handling of malformed transcript data"""
        malformed_transcripts = [
            {"call_id": "malformed_001"},  # Missing content
            {"content": "Some content"},   # Missing call_id
            {"call_id": None, "content": "Some content"},  # Null call_id
            {"call_id": "", "content": ""},  # Empty strings
            {"call_id": 123, "content": ["not", "a", "string"]},  # Wrong types
        ]
        
        for transcript in malformed_transcripts:
            with pytest.raises(Exception):
                asyncio.run(feedback_service.analyze_transcript(transcript))
    
    def test_unicode_and_special_characters(self, feedback_service):
        """Test handling of unicode and special characters"""
        unicode_transcript = {
            "call_id": "unicode_001",
            "content": "Agent: Hello! 🎉 Customer: Hola, ¿cómo está? Agent: 很好，谢谢！ Customer: Спасибо! 😊",
            "timestamp": "2024-01-05T10:00:00Z"
        }
        
        with patch.object(feedback_service, '_analyze_with_openai') as mock_openai:
            mock_openai.return_value = {
                "sentiment_score": 0.8,
                "booking_successful": True,
                "issues_found": [],
                "improvement_suggestions": []
            }
            
            result = asyncio.run(feedback_service.analyze_transcript(unicode_transcript))
            assert result is not None
    
    def test_concurrent_analysis_requests(self, feedback_service):
        """Test handling of concurrent analysis requests"""
        transcripts = [
            {
                "call_id": f"concurrent_{i}",
                "content": f"Agent: Hello! Customer: Hi, this is call {i}",
                "timestamp": "2024-01-05T10:00:00Z"
            }
            for i in range(10)
        ]
        
        with patch.object(feedback_service, '_analyze_with_openai') as mock_openai:
            mock_openai.return_value = {
                "sentiment_score": 0.7,
                "booking_successful": True,
                "issues_found": [],
                "improvement_suggestions": []
            }
            
            async def run_concurrent_analysis():
                tasks = [
                    feedback_service.analyze_transcript(transcript)
                    for transcript in transcripts
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return results
            
            start_time = time.time()
            results = asyncio.run(run_concurrent_analysis())
            processing_time = time.time() - start_time
            
            # All requests should complete successfully
            assert len(results) == 10
            assert all(isinstance(result, dict) for result in results)
            assert processing_time < 60  # Should complete within 60 seconds
    
    def test_api_rate_limiting(self, feedback_service):
        """Test handling of API rate limiting"""
        transcript = {
            "call_id": "rate_limit_001",
            "content": "Agent: Hello! Customer: Hi there!",
            "timestamp": "2024-01-05T10:00:00Z"
        }
        
        # Simulate rate limiting error
        with patch.object(feedback_service, '_analyze_with_openai') as mock_openai:
            mock_openai.side_effect = Exception("Rate limit exceeded")
            
            with pytest.raises(Exception, match="Rate limit exceeded"):
                asyncio.run(feedback_service.analyze_transcript(transcript))
    
    def test_network_timeout_handling(self, feedback_service):
        """Test handling of network timeouts"""
        transcript = {
            "call_id": "timeout_001",
            "content": "Agent: Hello! Customer: Hi there!",
            "timestamp": "2024-01-05T10:00:00Z"
        }
        
        with patch.object(feedback_service, '_analyze_with_openai') as mock_openai:
            mock_openai.side_effect = asyncio.TimeoutError("Request timeout")
            
            with pytest.raises(asyncio.TimeoutError):
                asyncio.run(feedback_service.analyze_transcript(transcript))
    
    def test_memory_system_unavailable(self):
        """Test handling when memory system is unavailable"""
        with patch('vertex.vertex_feedback_service.memory_system') as mock_memory:
            mock_memory.get_memories_by_date.side_effect = Exception("Memory system unavailable")
            
            with pytest.raises(Exception, match="Memory system unavailable"):
                asyncio.run(analyze_daily_calls("2024-01-05"))
    
    def test_prompt_version_conflicts(self, prompt_manager):
        """Test handling of prompt version conflicts"""
        improvements = [
            {
                "id": "conflict_001",
                "change": "Add greeting",
                "rationale": "Improve customer experience"
            }
        ]
        
        # Simulate version conflict
        with patch.object(prompt_manager, '_save_prompt_version') as mock_save:
            mock_save.side_effect = Exception("Version conflict detected")
            
            with pytest.raises(Exception, match="Version conflict"):
                prompt_manager.apply_improvements(improvements)
    
    def test_large_batch_processing(self, feedback_service):
        """Test processing of large batches of calls"""
        # Simulate 1000 calls
        large_batch = [
            {
                "id": f"batch_{i}",
                "call_id": f"call_{i:04d}",
                "content": f"Agent: Hello! Customer: Hi, this is call {i}",
                "timestamp": f"2024-01-05T{10 + (i % 14):02d}:00:00Z"
            }
            for i in range(1000)
        ]
        
        with patch('vertex.vertex_feedback_service.memory_system') as mock_memory:
            mock_memory.get_memories_by_date.return_value = {
                "success": True,
                "memories": large_batch
            }
            
            with patch.object(feedback_service, '_analyze_with_openai') as mock_openai:
                mock_openai.return_value = {
                    "sentiment_score": 0.7,
                    "booking_successful": True,
                    "issues_found": [],
                    "improvement_suggestions": []
                }
                
                start_time = time.time()
                result = asyncio.run(analyze_daily_calls("2024-01-05"))
                processing_time = time.time() - start_time
                
                assert result is not None
                assert result.total_calls_analyzed == 1000
                # Should process efficiently (less than 5 minutes for 1000 calls)
                assert processing_time < 300

@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not available")
class TestPropertyBased:
    """Property-based testing using Hypothesis"""
    
    @given(
        call_id=st.text(min_size=1, max_size=50),
        content=st.text(min_size=0, max_size=5000),
        sentiment=st.floats(min_value=0.0, max_value=1.0),
        booking_success=st.booleans()
    )
    @settings(max_examples=50, verbosity=Verbosity.verbose)
    def test_transcript_analysis_properties(self, call_id, content, sentiment, booking_success):
        """Test that transcript analysis maintains certain properties"""
        transcript = {
            "call_id": call_id,
            "content": content,
            "timestamp": "2024-01-05T10:00:00Z"
        }
        
        service = VertexFeedbackService()
        
        with patch.object(service, '_analyze_with_openai') as mock_openai:
            mock_openai.return_value = {
                "sentiment_score": sentiment,
                "booking_successful": booking_success,
                "issues_found": [],
                "improvement_suggestions": []
            }
            
            result = asyncio.run(service.analyze_transcript(transcript))
            
            # Properties that should always hold
            assert isinstance(result, dict)
            assert "sentiment_score" in result
            assert "booking_successful" in result
            assert 0.0 <= result["sentiment_score"] <= 1.0
            assert isinstance(result["booking_successful"], bool)
    
    @given(
        num_calls=st.integers(min_value=0, max_value=100),
        date_str=st.dates(min_value=datetime(2024, 1, 1), max_value=datetime(2024, 12, 31)).map(lambda d: d.strftime('%Y-%m-%d'))
    )
    @settings(max_examples=20)
    def test_daily_analysis_properties(self, num_calls, date_str):
        """Test properties of daily analysis"""
        mock_calls = [
            {
                "id": f"prop_test_{i}",
                "call_id": f"call_{i}",
                "content": f"Test call {i}",
                "timestamp": f"{date_str}T10:00:00Z"
            }
            for i in range(num_calls)
        ]
        
        with patch('vertex.vertex_feedback_service.memory_system') as mock_memory:
            mock_memory.get_memories_by_date.return_value = {
                "success": True,
                "memories": mock_calls
            }
            
            service = VertexFeedbackService()
            with patch.object(service, '_analyze_with_openai') as mock_openai:
                mock_openai.return_value = {
                    "sentiment_score": 0.7,
                    "booking_successful": True,
                    "issues_found": [],
                    "improvement_suggestions": []
                }
                
                result = asyncio.run(analyze_daily_calls(date_str))
                
                # Properties that should always hold
                if num_calls == 0:
                    assert result.total_calls_analyzed == 0
                else:
                    assert result.total_calls_analyzed == num_calls
                    assert isinstance(result.performance_metrics, dict)
                    assert isinstance(result.common_issues, list)
                    assert isinstance(result.improvement_suggestions, list)

class TestPerformanceBenchmarks:
    """Performance benchmarking tests"""
    
    def test_single_transcript_analysis_performance(self):
        """Benchmark single transcript analysis performance"""
        transcript = {
            "call_id": "perf_001",
            "content": "Agent: Hello! Customer: Hi, I need help with booking. " * 50,  # Medium-sized transcript
            "timestamp": "2024-01-05T10:00:00Z"
        }
        
        service = VertexFeedbackService()
        
        with patch.object(service, '_analyze_with_openai') as mock_openai:
            mock_openai.return_value = {
                "sentiment_score": 0.7,
                "booking_successful": True,
                "issues_found": [],
                "improvement_suggestions": []
            }
            
            # Warm up
            asyncio.run(service.analyze_transcript(transcript))
            
            # Benchmark
            times = []
            for _ in range(10):
                start_time = time.time()
                asyncio.run(service.analyze_transcript(transcript))
                times.append(time.time() - start_time)
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            print(f"\n📊 Single Transcript Analysis Performance:")
            print(f"   Average: {avg_time:.3f}s")
            print(f"   Min: {min_time:.3f}s")
            print(f"   Max: {max_time:.3f}s")
            
            # Performance assertions
            assert avg_time < 1.0  # Should average under 1 second
            assert max_time < 2.0  # Should never take more than 2 seconds
    
    def test_batch_analysis_performance(self):
        """Benchmark batch analysis performance"""
        batch_sizes = [10, 50, 100]
        
        for batch_size in batch_sizes:
            transcripts = [
                {
                    "id": f"batch_perf_{i}",
                    "call_id": f"call_{i}",
                    "content": f"Agent: Hello! Customer: This is call {i}",
                    "timestamp": "2024-01-05T10:00:00Z"
                }
                for i in range(batch_size)
            ]
            
            with patch('vertex.vertex_feedback_service.memory_system') as mock_memory:
                mock_memory.get_memories_by_date.return_value = {
                    "success": True,
                    "memories": transcripts
                }
                
                service = VertexFeedbackService()
                with patch.object(service, '_analyze_with_openai') as mock_openai:
                    mock_openai.return_value = {
                        "sentiment_score": 0.7,
                        "booking_successful": True,
                        "issues_found": [],
                        "improvement_suggestions": []
                    }
                    
                    start_time = time.time()
                    result = asyncio.run(analyze_daily_calls("2024-01-05"))
                    processing_time = time.time() - start_time
                    
                    calls_per_second = batch_size / processing_time
                    
                    print(f"\n📊 Batch Analysis Performance ({batch_size} calls):")
                    print(f"   Total time: {processing_time:.3f}s")
                    print(f"   Calls/second: {calls_per_second:.1f}")
                    
                    # Performance assertions
                    assert calls_per_second > 5  # Should process at least 5 calls per second
                    assert result.total_calls_analyzed == batch_size
    
    def test_memory_usage_analysis(self):
        """Test memory usage during analysis"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create a large dataset
        large_dataset = [
            {
                "id": f"memory_test_{i}",
                "call_id": f"call_{i}",
                "content": "Agent: " + "This is a test conversation. " * 100,  # Large content
                "timestamp": "2024-01-05T10:00:00Z"
            }
            for i in range(500)
        ]
        
        with patch('vertex.vertex_feedback_service.memory_system') as mock_memory:
            mock_memory.get_memories_by_date.return_value = {
                "success": True,
                "memories": large_dataset
            }
            
            service = VertexFeedbackService()
            with patch.object(service, '_analyze_with_openai') as mock_openai:
                mock_openai.return_value = {
                    "sentiment_score": 0.7,
                    "booking_successful": True,
                    "issues_found": [],
                    "improvement_suggestions": []
                }
                
                result = asyncio.run(analyze_daily_calls("2024-01-05"))
                
                peak_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = peak_memory - initial_memory
                
                print(f"\n📊 Memory Usage Analysis:")
                print(f"   Initial memory: {initial_memory:.1f} MB")
                print(f"   Peak memory: {peak_memory:.1f} MB")
                print(f"   Memory increase: {memory_increase:.1f} MB")
                print(f"   Memory per call: {memory_increase / 500:.3f} MB")
                
                # Memory usage assertions
                assert memory_increase < 500  # Should not use more than 500MB additional
                assert memory_increase / 500 < 1.0  # Should not use more than 1MB per call

class TestErrorRecovery:
    """Test error recovery and resilience"""
    
    def test_partial_failure_recovery(self):
        """Test recovery from partial failures in batch processing"""
        # Mix of successful and failing transcripts
        mixed_batch = [
            {"id": f"success_{i}", "call_id": f"call_{i}", "content": f"Good call {i}"}
            for i in range(5)
        ] + [
            {"id": f"fail_{i}", "call_id": f"bad_call_{i}", "content": ""}  # Empty content to cause failure
            for i in range(3)
        ]
        
        with patch('vertex.vertex_feedback_service.memory_system') as mock_memory:
            mock_memory.get_memories_by_date.return_value = {
                "success": True,
                "memories": mixed_batch
            }
            
            service = VertexFeedbackService()
            
            def mock_analysis(transcript):
                if not transcript.get("content"):
                    raise Exception("Empty content")
                return {
                    "sentiment_score": 0.7,
                    "booking_successful": True,
                    "issues_found": [],
                    "improvement_suggestions": []
                }
            
            with patch.object(service, '_analyze_with_openai', side_effect=mock_analysis):
                # Should handle partial failures gracefully
                result = asyncio.run(analyze_daily_calls("2024-01-05"))
                
                # Should process successful calls despite failures
                assert result.total_calls_analyzed >= 5  # At least the successful ones
    
    def test_retry_mechanism(self):
        """Test retry mechanism for transient failures"""
        transcript = {
            "call_id": "retry_001",
            "content": "Agent: Hello! Customer: Hi there!",
            "timestamp": "2024-01-05T10:00:00Z"
        }
        
        service = VertexFeedbackService()
        
        # Simulate transient failure followed by success
        call_count = 0
        def mock_analysis_with_retry(transcript_data):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 attempts
                raise Exception("Transient error")
            return {
                "sentiment_score": 0.7,
                "booking_successful": True,
                "issues_found": [],
                "improvement_suggestions": []
            }
        
        with patch.object(service, '_analyze_with_openai', side_effect=mock_analysis_with_retry):
            # Should eventually succeed after retries
            result = asyncio.run(service.analyze_transcript(transcript))
            assert result is not None
            assert call_count == 3  # Should have retried twice

def run_performance_suite():
    """Run the complete performance test suite"""
    print("🚀 Running Performance Test Suite")
    print("=" * 50)
    
    # Run performance tests
    test_perf = TestPerformanceBenchmarks()
    
    print("\n1. Single Transcript Analysis Performance")
    test_perf.test_single_transcript_analysis_performance()
    
    print("\n2. Batch Analysis Performance")
    test_perf.test_batch_analysis_performance()
    
    print("\n3. Memory Usage Analysis")
    test_perf.test_memory_usage_analysis()
    
    print("\n✅ Performance test suite completed!")

if __name__ == "__main__":
    # Run performance suite if executed directly
    run_performance_suite()
