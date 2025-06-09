#!/usr/bin/env python3
"""
GCP Environment Setup for VoiceHive Vertex AI Feedback System

This script sets up the necessary GCP resources for the feedback pipeline:
- Enables required APIs
- Creates service accounts
- Sets up IAM permissions
- Configures Cloud Scheduler
- Creates storage buckets
"""

import os
import json
import subprocess
import sys
from typing import Dict, List, Optional
from datetime import datetime

class GCPSetup:
    def __init__(self, project_id: str, region: str = "us-central1"):
        self.project_id = project_id
        self.region = region
        self.service_account_name = "voicehive-vertex-feedback"
        self.service_account_email = f"{self.service_account_name}@{project_id}.iam.gserviceaccount.com"
        self.bucket_name = f"{project_id}-voicehive-feedback"
        
    def run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command and return the result"""
        print(f"🔧 Running: {' '.join(command)}")
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=check)
            if result.stdout:
                print(f"✅ Output: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e.stderr}")
            if check:
                raise
            return e
    
    def check_gcloud_auth(self) -> bool:
        """Check if gcloud is authenticated"""
        try:
            result = self.run_command(["gcloud", "auth", "list", "--format=json"], check=False)
            if result.returncode == 0:
                accounts = json.loads(result.stdout)
                active_accounts = [acc for acc in accounts if acc.get("status") == "ACTIVE"]
                if active_accounts:
                    print(f"✅ Authenticated as: {active_accounts[0]['account']}")
                    return True
            
            print("❌ No active gcloud authentication found")
            print("Please run: gcloud auth login")
            return False
        except Exception as e:
            print(f"❌ Error checking authentication: {e}")
            return False
    
    def set_project(self) -> bool:
        """Set the active GCP project"""
        try:
            self.run_command(["gcloud", "config", "set", "project", self.project_id])
            print(f"✅ Set active project to: {self.project_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to set project: {e}")
            return False
    
    def enable_apis(self) -> bool:
        """Enable required GCP APIs"""
        apis = [
            "aiplatform.googleapis.com",
            "cloudbuild.googleapis.com",
            "cloudscheduler.googleapis.com",
            "storage.googleapis.com",
            "secretmanager.googleapis.com",
            "compute.googleapis.com",
            "notebooks.googleapis.com"
        ]
        
        print("🔧 Enabling required APIs...")
        try:
            for api in apis:
                print(f"   Enabling {api}...")
                self.run_command(["gcloud", "services", "enable", api])
            
            print("✅ All APIs enabled successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to enable APIs: {e}")
            return False
    
    def create_service_account(self) -> bool:
        """Create service account for Vertex AI operations"""
        try:
            # Check if service account already exists
            result = self.run_command([
                "gcloud", "iam", "service-accounts", "describe", 
                self.service_account_email
            ], check=False)
            
            if result.returncode == 0:
                print(f"✅ Service account {self.service_account_email} already exists")
            else:
                # Create service account
                self.run_command([
                    "gcloud", "iam", "service-accounts", "create", 
                    self.service_account_name,
                    "--display-name=VoiceHive Vertex AI Feedback Service",
                    "--description=Service account for VoiceHive feedback pipeline"
                ])
                print(f"✅ Created service account: {self.service_account_email}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to create service account: {e}")
            return False
    
    def assign_iam_roles(self) -> bool:
        """Assign necessary IAM roles to the service account"""
        roles = [
            "roles/aiplatform.user",
            "roles/storage.admin",
            "roles/secretmanager.accessor",
            "roles/cloudscheduler.admin",
            "roles/logging.logWriter",
            "roles/monitoring.metricWriter"
        ]
        
        try:
            for role in roles:
                print(f"   Assigning role: {role}")
                self.run_command([
                    "gcloud", "projects", "add-iam-policy-binding", 
                    self.project_id,
                    f"--member=serviceAccount:{self.service_account_email}",
                    f"--role={role}"
                ])
            
            print("✅ All IAM roles assigned successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to assign IAM roles: {e}")
            return False
    
    def create_storage_bucket(self) -> bool:
        """Create Cloud Storage bucket for feedback data"""
        try:
            # Check if bucket already exists
            result = self.run_command([
                "gsutil", "ls", f"gs://{self.bucket_name}"
            ], check=False)
            
            if result.returncode == 0:
                print(f"✅ Bucket gs://{self.bucket_name} already exists")
            else:
                # Create bucket
                self.run_command([
                    "gsutil", "mb", "-l", self.region, f"gs://{self.bucket_name}"
                ])
                print(f"✅ Created bucket: gs://{self.bucket_name}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to create storage bucket: {e}")
            return False
    
    def create_service_account_key(self, output_path: str = None) -> bool:
        """Create and download service account key"""
        if not output_path:
            output_path = f"./credentials/{self.service_account_name}-key.json"
        
        try:
            # Create credentials directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create key
            self.run_command([
                "gcloud", "iam", "service-accounts", "keys", "create",
                output_path,
                f"--iam-account={self.service_account_email}"
            ])
            
            print(f"✅ Service account key created: {output_path}")
            print(f"⚠️  Keep this key secure and add {os.path.dirname(output_path)} to .gitignore")
            return True
        except Exception as e:
            print(f"❌ Failed to create service account key: {e}")
            return False
    
    def setup_cloud_scheduler(self) -> bool:
        """Set up Cloud Scheduler for daily pipeline execution"""
        job_name = "voicehive-daily-feedback"
        
        try:
            # Check if job already exists
            result = self.run_command([
                "gcloud", "scheduler", "jobs", "describe", job_name,
                f"--location={self.region}"
            ], check=False)
            
            if result.returncode == 0:
                print(f"✅ Scheduler job {job_name} already exists")
            else:
                # Create scheduler job
                self.run_command([
                    "gcloud", "scheduler", "jobs", "create", "http", job_name,
                    f"--location={self.region}",
                    "--schedule=0 6 * * *",  # Daily at 6 AM
                    "--time-zone=UTC",
                    "--uri=https://your-cloud-function-url/trigger-feedback-pipeline",
                    "--http-method=POST",
                    "--headers=Content-Type=application/json",
                    "--message-body={}",
                    "--description=Daily VoiceHive feedback pipeline trigger"
                ])
                print(f"✅ Created scheduler job: {job_name}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to setup Cloud Scheduler: {e}")
            return False
    
    def store_secrets(self) -> bool:
        """Store configuration secrets in Secret Manager"""
        secrets = {
            "voicehive-openai-api-key": "your-openai-api-key-here",
            "voicehive-mem0-config": json.dumps({
                "api_key": "your-mem0-api-key",
                "user_id": "voicehive-system"
            }),
            "voicehive-vertex-config": json.dumps({
                "project_id": self.project_id,
                "region": self.region,
                "service_account": self.service_account_email
            })
        }
        
        try:
            for secret_name, secret_value in secrets.items():
                # Check if secret exists
                result = self.run_command([
                    "gcloud", "secrets", "describe", secret_name
                ], check=False)
                
                if result.returncode != 0:
                    # Create secret
                    self.run_command([
                        "gcloud", "secrets", "create", secret_name,
                        "--data-file=-"
                    ], check=False)
                    
                    # Add secret version
                    process = subprocess.Popen([
                        "gcloud", "secrets", "versions", "add", secret_name,
                        "--data-file=-"
                    ], stdin=subprocess.PIPE, text=True)
                    process.communicate(input=secret_value)
                    
                    print(f"✅ Created secret: {secret_name}")
                else:
                    print(f"✅ Secret {secret_name} already exists")
            
            print("⚠️  Please update the secret values with your actual API keys")
            return True
        except Exception as e:
            print(f"❌ Failed to store secrets: {e}")
            return False
    
    def create_env_file(self) -> bool:
        """Create environment configuration file"""
        env_content = f"""# VoiceHive Vertex AI Configuration
GOOGLE_CLOUD_PROJECT={self.project_id}
GOOGLE_CLOUD_REGION={self.region}
VERTEX_SERVICE_ACCOUNT={self.service_account_email}
FEEDBACK_BUCKET={self.bucket_name}

# Secret Manager secret names
OPENAI_API_KEY_SECRET=voicehive-openai-api-key
MEM0_CONFIG_SECRET=voicehive-mem0-config
VERTEX_CONFIG_SECRET=voicehive-vertex-config

# Pipeline configuration
FEEDBACK_SCHEDULE="0 6 * * *"
ANALYSIS_DAYS=3
MAX_CALLS_PER_DAY=100

# Logging
LOG_LEVEL=INFO
"""
        
        try:
            with open("vertex/.env.vertex", "w") as f:
                f.write(env_content)
            
            print("✅ Created vertex/.env.vertex configuration file")
            return True
        except Exception as e:
            print(f"❌ Failed to create env file: {e}")
            return False
    
    def run_setup(self) -> bool:
        """Run the complete setup process"""
        print("🚀 Starting VoiceHive Vertex AI Setup")
        print("=" * 50)
        
        steps = [
            ("Checking gcloud authentication", self.check_gcloud_auth),
            ("Setting active project", self.set_project),
            ("Enabling required APIs", self.enable_apis),
            ("Creating service account", self.create_service_account),
            ("Assigning IAM roles", self.assign_iam_roles),
            ("Creating storage bucket", self.create_storage_bucket),
            ("Creating service account key", self.create_service_account_key),
            ("Setting up Cloud Scheduler", self.setup_cloud_scheduler),
            ("Storing secrets", self.store_secrets),
            ("Creating environment file", self.create_env_file)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Setup failed at: {step_name}")
                return False
        
        print("\n🎉 Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update secret values in Secret Manager with your actual API keys")
        print("2. Test the feedback pipeline manually")
        print("3. Verify Cloud Scheduler job is working")
        print("4. Monitor logs and metrics")
        
        return True

def main():
    """Main setup function"""
    if len(sys.argv) < 2:
        print("Usage: python gcp_setup.py <project-id> [region]")
        print("Example: python gcp_setup.py my-voicehive-project us-central1")
        sys.exit(1)
    
    project_id = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else "us-central1"
    
    setup = GCPSetup(project_id, region)
    success = setup.run_setup()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
