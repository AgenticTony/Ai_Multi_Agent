#!/usr/bin/env python3
"""
Cloud Scheduler Trigger for VoiceHive Daily Feedback Pipeline

This script serves as the entry point for Cloud Scheduler to trigger
the daily feedback pipeline execution.
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
import functions_framework
from google.cloud import secretmanager
from google.cloud import logging as cloud_logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Google Cloud Logging
try:
    client = cloud_logging.Client()
    client.setup_logging()
except Exception as e:
    logger.warning(f"Could not setup Cloud Logging: {e}")

class CloudSchedulerTrigger:
    """Handles Cloud Scheduler triggered pipeline execution"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.secret_client = secretmanager.SecretManagerServiceClient()
        
    def get_secret(self, secret_name: str) -> str:
        """Retrieve secret from Secret Manager"""
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            raise
    
    def setup_environment(self):
        """Set up environment variables from secrets"""
        try:
            # Get OpenAI API key
            openai_key = self.get_secret("voicehive-openai-api-key")
            os.environ['OPENAI_API_KEY'] = openai_key
            
            # Get Mem0 configuration
            mem0_config = json.loads(self.get_secret("voicehive-mem0-config"))
            os.environ['MEM0_API_KEY'] = mem0_config['api_key']
            os.environ['MEM0_USER_ID'] = mem0_config['user_id']
            
            # Get Vertex configuration
            vertex_config = json.loads(self.get_secret("voicehive-vertex-config"))
            os.environ['VERTEX_SERVICE_ACCOUNT'] = vertex_config['service_account']
            os.environ['GOOGLE_CLOUD_REGION'] = vertex_config['region']
            
            logger.info("Environment setup completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup environment: {e}")
            raise
    
    async def run_daily_pipeline(self, target_date: str = None) -> Dict[str, Any]:
        """Execute the daily feedback pipeline"""
        if not target_date:
            target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"Starting daily feedback pipeline for {target_date}")
        
        try:
            # Import pipeline components
            from daily_feedback_pipeline import DailyFeedbackPipeline
            
            # Initialize and run pipeline
            pipeline = DailyFeedbackPipeline()
            result = await pipeline.run_daily_analysis(target_date)
            
            logger.info(f"Pipeline completed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            raise
    
    def send_notification(self, result: Dict[str, Any]):
        """Send notification about pipeline execution"""
        try:
            # This could be extended to send Slack/email notifications
            if result.get("success"):
                logger.info(f"✅ Daily feedback pipeline completed successfully")
                logger.info(f"📊 Calls analyzed: {result.get('calls_analyzed', 0)}")
                logger.info(f"💡 Improvements suggested: {result.get('improvements_count', 0)}")
            else:
                logger.error(f"❌ Daily feedback pipeline failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

# Global trigger instance
trigger = CloudSchedulerTrigger()

@functions_framework.http
def trigger_daily_feedback(request):
    """
    HTTP Cloud Function entry point for Cloud Scheduler
    
    This function is triggered by Cloud Scheduler daily at 6 AM UTC
    """
    try:
        # Parse request
        request_json = request.get_json(silent=True)
        target_date = None
        
        if request_json and 'target_date' in request_json:
            target_date = request_json['target_date']
        
        logger.info(f"Received trigger request for date: {target_date or 'yesterday'}")
        
        # Setup environment
        trigger.setup_environment()
        
        # Run pipeline
        result = asyncio.run(trigger.run_daily_pipeline(target_date))
        
        # Send notification
        trigger.send_notification(result)
        
        # Return success response
        return {
            "status": "success",
            "message": "Daily feedback pipeline completed",
            "result": result
        }, 200
        
    except Exception as e:
        logger.error(f"Trigger function failed: {e}")
        
        # Send error notification
        trigger.send_notification({
            "success": False,
            "error": str(e)
        })
        
        return {
            "status": "error",
            "message": str(e)
        }, 500

def manual_trigger(target_date: str = None):
    """
    Manual trigger for testing purposes
    
    Usage:
        python cloud_scheduler_trigger.py [YYYY-MM-DD]
    """
    import sys
    
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    
    print(f"🚀 Manually triggering daily feedback pipeline")
    print(f"📅 Target date: {target_date or 'yesterday'}")
    
    async def run_manual():
        try:
            # Setup environment (for local testing, use .env file)
            if os.path.exists('.env'):
                from dotenv import load_dotenv
                load_dotenv()
            
            # Run pipeline
            result = await trigger.run_daily_pipeline(target_date)
            
            print("✅ Manual trigger completed successfully")
            print(f"📊 Result: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            print(f"❌ Manual trigger failed: {e}")
            raise
    
    asyncio.run(run_manual())

if __name__ == "__main__":
    # Run manual trigger if executed directly
    manual_trigger()
