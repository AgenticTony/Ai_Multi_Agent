"""
Daily Feedback Pipeline - Scheduled execution for call analysis and prompt improvements
"""
import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vertex_feedback_service import run_daily_feedback_pipeline, feedback_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_feedback_pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DailyFeedbackPipeline:
    """Daily feedback pipeline orchestrator"""
    
    def __init__(self):
        self.pipeline_name = "VoiceHive Daily Feedback Pipeline"
        self.version = "1.0.0"
    
    async def run_pipeline(self, target_date: Optional[str] = None) -> bool:
        """
        Run the complete daily feedback pipeline
        
        Args:
            target_date: Optional date string (YYYY-MM-DD), defaults to yesterday
            
        Returns:
            Success status
        """
        try:
            start_time = datetime.now()
            
            if not target_date:
                yesterday = datetime.now() - timedelta(days=1)
                target_date = yesterday.strftime('%Y-%m-%d')
            
            logger.info(f"Starting {self.pipeline_name} v{self.version}")
            logger.info(f"Target date: {target_date}")
            logger.info(f"Pipeline start time: {start_time}")
            
            # Step 1: Validate environment
            if not await self._validate_environment():
                logger.error("Environment validation failed")
                return False
            
            # Step 2: Run feedback analysis
            logger.info("Step 2: Running feedback analysis...")
            success = await run_daily_feedback_pipeline(target_date)
            
            if not success:
                logger.error("Feedback analysis failed")
                return False
            
            # Step 3: Generate summary report
            logger.info("Step 3: Generating summary report...")
            await self._generate_summary_report(target_date)
            
            # Step 4: Cleanup and finalization
            logger.info("Step 4: Pipeline cleanup...")
            await self._cleanup_pipeline()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info(f"Pipeline completed successfully!")
            logger.info(f"Total duration: {duration}")
            logger.info(f"End time: {end_time}")
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            return False
    
    async def _validate_environment(self) -> bool:
        """Validate pipeline environment and dependencies"""
        try:
            logger.info("Validating environment...")
            
            # Check required environment variables
            required_vars = ['OPENAI_API_KEY']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                logger.error(f"Missing required environment variables: {missing_vars}")
                return False
            
            # Check file system access
            improvements_dir = "../improvements"
            if not os.path.exists(improvements_dir):
                logger.error(f"Improvements directory not found: {improvements_dir}")
                return False
            
            # Test memory system connection
            try:
                from memory.mem0 import memory_system
                logger.info("Memory system connection validated")
            except Exception as e:
                logger.warning(f"Memory system validation warning: {str(e)}")
            
            # Test feedback service initialization
            if not feedback_service:
                logger.error("Feedback service not initialized")
                return False
            
            logger.info("Environment validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Environment validation error: {str(e)}")
            return False
    
    async def _generate_summary_report(self, target_date: str) -> None:
        """Generate and save summary report"""
        try:
            logger.info("Generating summary report...")
            
            # Load the latest feedback data
            improvements_file = "../improvements/prompt_updates.json"
            
            if not os.path.exists(improvements_file):
                logger.warning("No improvements file found for report generation")
                return
            
            import json
            with open(improvements_file, 'r') as f:
                improvements_data = json.load(f)
            
            feedback_analysis = improvements_data.get("feedback_analysis", {})
            
            # Create summary report
            report = {
                "pipeline_execution": {
                    "date": target_date,
                    "execution_time": datetime.now().isoformat(),
                    "pipeline_version": self.version,
                    "status": "completed"
                },
                "analysis_summary": {
                    "total_calls_analyzed": feedback_analysis.get("total_calls_analyzed", 0),
                    "performance_metrics": feedback_analysis.get("performance_metrics", {}),
                    "common_issues_count": len(feedback_analysis.get("common_issues", [])),
                    "improvement_suggestions_count": len(feedback_analysis.get("improvement_suggestions", [])),
                },
                "recommendations": {
                    "pending_count": len(improvements_data.get("pending_improvements", [])),
                    "current_prompt_version": improvements_data.get("current_prompt_version", "unknown")
                }
            }
            
            # Save report
            report_file = f"../improvements/reports/daily_report_{target_date}.json"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Summary report saved: {report_file}")
            
            # Log key metrics
            logger.info(f"Calls analyzed: {report['analysis_summary']['total_calls_analyzed']}")
            logger.info(f"Issues identified: {report['analysis_summary']['common_issues_count']}")
            logger.info(f"Pending recommendations: {report['recommendations']['pending_count']}")
            
        except Exception as e:
            logger.error(f"Error generating summary report: {str(e)}")
    
    async def _cleanup_pipeline(self) -> None:
        """Cleanup pipeline resources and temporary files"""
        try:
            logger.info("Performing pipeline cleanup...")
            
            # Clean up old log files (keep last 30 days)
            log_retention_days = 30
            cutoff_date = datetime.now() - timedelta(days=log_retention_days)
            
            log_dir = "."
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(log_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_date:
                        try:
                            os.remove(file_path)
                            logger.info(f"Removed old log file: {filename}")
                        except Exception as e:
                            logger.warning(f"Failed to remove log file {filename}: {str(e)}")
            
            # Clean up old reports (keep last 90 days)
            report_retention_days = 90
            cutoff_date = datetime.now() - timedelta(days=report_retention_days)
            
            reports_dir = "../improvements/reports"
            if os.path.exists(reports_dir):
                for filename in os.listdir(reports_dir):
                    if filename.startswith('daily_report_') and filename.endswith('.json'):
                        file_path = os.path.join(reports_dir, filename)
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if file_time < cutoff_date:
                            try:
                                os.remove(file_path)
                                logger.info(f"Removed old report: {filename}")
                            except Exception as e:
                                logger.warning(f"Failed to remove report {filename}: {str(e)}")
            
            logger.info("Pipeline cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during pipeline cleanup: {str(e)}")


async def main():
    """Main pipeline execution function"""
    try:
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description='VoiceHive Daily Feedback Pipeline')
        parser.add_argument('--date', type=str, help='Target date (YYYY-MM-DD), defaults to yesterday')
        parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
        
        args = parser.parse_args()
        
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Initialize and run pipeline
        pipeline = DailyFeedbackPipeline()
        success = await pipeline.run_pipeline(args.date)
        
        if success:
            logger.info("Pipeline execution completed successfully")
            sys.exit(0)
        else:
            logger.error("Pipeline execution failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Pipeline execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        sys.exit(1)


def run_pipeline_sync(target_date: Optional[str] = None) -> bool:
    """Synchronous wrapper for pipeline execution"""
    try:
        return asyncio.run(DailyFeedbackPipeline().run_pipeline(target_date))
    except Exception as e:
        logger.error(f"Error running pipeline sync: {str(e)}")
        return False


if __name__ == "__main__":
    asyncio.run(main())
