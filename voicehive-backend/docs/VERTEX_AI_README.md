# VoiceHive Vertex AI Feedback System

A production-ready AI feedback system that automatically analyzes voice call transcripts and continuously improves agent prompts using Google Cloud Vertex AI.

## 🚀 Quick Start

### Prerequisites
- Google Cloud Project with billing enabled
- Python 3.9+
- gcloud CLI installed and authenticated
- OpenAI API key
- Mem0 API key (optional, for memory integration)

### 1. Environment Setup

```bash
# Clone and navigate to the project
cd voicehive-backend

# Install dependencies
pip install -r requirements.txt

# Set up GCP environment
cd vertex
python gcp_setup.py your-project-id us-central1
```

### 2. Configuration

Create environment configuration files:

```bash
# Copy example environment file
cp .env.example .env.vertex

# Edit with your actual values
vim .env.vertex
```

### 3. Deploy and Test

```bash
# Run comprehensive tests
python -m pytest tests/test_sprint3_feedback_loop.py -v

# Manual pipeline test
python vertex/cloud_scheduler_trigger.py 2024-01-05

# Deploy to production
gcloud functions deploy trigger-daily-feedback \
  --runtime python39 \
  --trigger-http \
  --entry-point trigger_daily_feedback \
  --source vertex/
```

## 📋 Environment Variables

### Required Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID | `my-voicehive-project` | ✅ |
| `GOOGLE_CLOUD_REGION` | GCP Region | `us-central1` | ✅ |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` | ✅ |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `MEM0_API_KEY` | Mem0 API Key for memory integration | None | `mem0_...` |
| `MEM0_USER_ID` | Mem0 User ID | `voicehive-system` | `my-user-id` |
| `VERTEX_SERVICE_ACCOUNT` | Service account email | Auto-generated | `feedback@project.iam.gserviceaccount.com` |
| `FEEDBACK_BUCKET` | Cloud Storage bucket | `{project}-voicehive-feedback` | `my-feedback-bucket` |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `WARNING`, `ERROR` |
| `ANALYSIS_DAYS` | Days of data to analyze | `3` | `1`, `7`, `30` |
| `MAX_CALLS_PER_DAY` | Maximum calls to process | `100` | `50`, `200`, `1000` |
| `FEEDBACK_SCHEDULE` | Cron schedule for pipeline | `0 6 * * *` | `0 8 * * *` |

### Secret Manager Variables

These are stored securely in Google Secret Manager:

| Secret Name | Description | Format |
|-------------|-------------|--------|
| `voicehive-openai-api-key` | OpenAI API Key | String |
| `voicehive-mem0-config` | Mem0 configuration | JSON |
| `voicehive-vertex-config` | Vertex AI configuration | JSON |

### Development Variables

For local development and testing:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment name | `development` |
| `DEBUG` | Enable debug mode | `False` |
| `MOCK_EXTERNAL_APIS` | Use mock APIs for testing | `False` |
| `LOCAL_STORAGE_PATH` | Local storage for development | `./data` |

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Voice Calls   │───▶│ VAPI Integration│───▶│ Call Transcripts│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Cloud Scheduler │───▶│ Daily Pipeline  │───▶│ Feedback Service│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Agent Updates   │◀───│ Prompt Manager  │◀───│ AI Analysis     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **Call Collection**: Voice calls are processed through VAPI
2. **Transcript Storage**: Call transcripts stored in Mem0/Cloud Storage
3. **Daily Analysis**: Scheduled pipeline analyzes previous day's calls
4. **AI Processing**: OpenAI analyzes transcripts for quality and issues
5. **Improvement Generation**: System generates prompt improvement suggestions
6. **Safety Validation**: Changes are validated for safety and effectiveness
7. **Prompt Updates**: Approved changes are applied to agent prompts
8. **Performance Monitoring**: System tracks improvement effectiveness

## 📊 Features

### Core Capabilities

- **Automated Analysis**: Daily analysis of call transcripts
- **AI-Powered Insights**: OpenAI-based quality assessment
- **Prompt Versioning**: Complete version control for agent prompts
- **Safety Validation**: Automated safety checks for prompt changes
- **Performance Tracking**: Comprehensive metrics and monitoring
- **Rollback Support**: Quick reversion of problematic changes

### Advanced Features

- **Interactive Notebook**: Jupyter notebook for manual analysis
- **Custom Metrics**: Configurable performance indicators
- **Alert System**: Real-time notifications for issues
- **Batch Processing**: Efficient handling of large call volumes
- **Multi-Environment**: Support for dev/staging/production

## 🔧 Configuration

### Pipeline Configuration

```python
# vertex/.env.vertex
FEEDBACK_SCHEDULE="0 6 * * *"  # Daily at 6 AM UTC
ANALYSIS_DAYS=3                # Analyze last 3 days
MAX_CALLS_PER_DAY=100         # Process up to 100 calls
```

### Analysis Configuration

```python
# Analysis parameters
SENTIMENT_THRESHOLD=0.5        # Minimum sentiment score
BOOKING_SUCCESS_TARGET=0.8     # Target booking success rate
ISSUE_FREQUENCY_THRESHOLD=3    # Minimum issue frequency to report
```

### Safety Configuration

```python
# Safety validation settings
ENABLE_SAFETY_CHECKS=True      # Enable safety validation
REQUIRE_HUMAN_APPROVAL=True    # Require human approval for changes
MAX_PROMPT_LENGTH=2000         # Maximum prompt length
FORBIDDEN_WORDS=["unsafe", "harmful"]  # Blocked words
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_sprint3_feedback_loop.py::TestFeedbackLoop -v
python -m pytest tests/test_sprint3_feedback_loop.py::TestEndToEndScenarios -v
```

### Integration Tests

```bash
# Test with mock data
python tests/test_sprint3_feedback_loop.py

# Test with real APIs (requires credentials)
ENVIRONMENT=testing python -m pytest tests/integration/ -v
```

### Performance Tests

```bash
# Benchmark analysis performance
python tests/benchmark_analysis.py

# Load testing
python tests/load_test_pipeline.py --calls 1000 --concurrent 10
```

## 📈 Monitoring

### Health Checks

The system provides several health check endpoints:

- `/health` - Basic system health
- `/health/pipeline` - Pipeline status
- `/health/dependencies` - External service status
- `/metrics` - Performance metrics

### Key Metrics

- **Analysis Metrics**: Calls processed, analysis time, error rates
- **Quality Metrics**: Sentiment scores, booking success rates
- **System Metrics**: Memory usage, API latency, storage usage
- **Business Metrics**: Improvement effectiveness, cost per analysis

### Alerting

Configure alerts for:

- Pipeline failures
- High error rates
- Performance degradation
- Unusual patterns in call data
- Security incidents

## 🔒 Security

### Authentication

- Service account-based authentication
- IAM roles with least privilege
- API key rotation policies
- Audit logging for all operations

### Data Protection

- Encryption at rest and in transit
- PII data handling compliance
- Data retention policies
- Secure credential storage

### Network Security

- VPC-native deployments
- Private service connections
- Firewall rules and security groups
- SSL/TLS termination

## 🚀 Deployment

### Development Environment

```bash
# Local development setup
export ENVIRONMENT=development
export DEBUG=True
export MOCK_EXTERNAL_APIS=True

python vertex/cloud_scheduler_trigger.py
```

### Staging Environment

```bash
# Deploy to staging
gcloud config set project my-staging-project
python vertex/gcp_setup.py my-staging-project us-central1

# Run staging tests
ENVIRONMENT=staging python -m pytest tests/integration/ -v
```

### Production Environment

```bash
# Deploy to production
gcloud config set project my-production-project
python vertex/gcp_setup.py my-production-project us-central1

# Verify deployment
curl https://your-function-url/health
```

## 📚 API Reference

### Feedback Service API

```python
from vertex.vertex_feedback_service import VertexFeedbackService

# Initialize service
service = VertexFeedbackService()

# Analyze single transcript
result = await service.analyze_transcript(transcript_data)

# Run daily analysis
summary = await service.analyze_daily_calls("2024-01-05")
```

### Prompt Manager API

```python
from improvements.prompt_manager import PromptManager

# Initialize manager
manager = PromptManager()

# Get current prompt
current = manager.get_current_prompt()

# Apply improvements
new_version = manager.apply_improvements(improvements)

# Rollback if needed
manager.rollback_to_version("1.0")
```

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   gcloud auth application-default login
   gcloud config set project your-project-id
   ```

2. **API Quota Exceeded**
   ```bash
   # Check quotas
   gcloud compute project-info describe --project=your-project-id
   ```

3. **Memory Issues**
   ```bash
   # Increase memory allocation
   export MEMORY_LIMIT=2Gi
   ```

4. **Network Connectivity**
   ```bash
   # Test connectivity
   curl -I https://api.openai.com/v1/models
   ```

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
export DEBUG=True
python vertex/cloud_scheduler_trigger.py
```

### Support

For issues and support:

1. Check the [troubleshooting guide](docs/troubleshooting.md)
2. Review system logs in Cloud Logging
3. Check health endpoints for system status
4. Contact the development team

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

- Documentation: [docs/](docs/)
- Issues: GitHub Issues
- Email: support@voicehive.com
- Slack: #voicehive-support
