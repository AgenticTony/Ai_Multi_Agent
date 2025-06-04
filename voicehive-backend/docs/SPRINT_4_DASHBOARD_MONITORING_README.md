# Sprint 4: Dashboard & Monitoring System - Implementation Guide

## Overview

Sprint 4 delivers a comprehensive monitoring and dashboard solution for VoiceHive, providing real-time visibility into system performance, call analytics, and operational health. This implementation includes a modern React dashboard, robust monitoring infrastructure, and intelligent alerting systems.

## 🎯 Sprint 4 Objectives

### Primary Goals
- **Real-time Dashboard**: Modern web interface for monitoring VoiceHive operations
- **Comprehensive Monitoring**: Full observability with metrics, traces, and logs
- **Intelligent Alerting**: Proactive notification system for issues and anomalies
- **Performance Analytics**: Deep insights into call performance and system health

### Key Deliverables
1. Next.js Dashboard Application
2. OpenTelemetry Instrumentation
3. Prometheus Metrics Collection
4. Grafana Dashboards
5. Alertmanager Configuration
6. Comprehensive Test Suite

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   Monitoring    │    │   Alerting      │
│   (Next.js)     │    │   (Prometheus)  │    │ (Alertmanager)  │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ React UI    │ │    │ │ Metrics     │ │    │ │ Rules       │ │
│ │ Components  │ │    │ │ Collection  │ │    │ │ Engine      │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ API Client  │ │    │ │ Time Series │ │    │ │ Notification│ │
│ │ (REST/WS)   │ │    │ │ Database    │ │    │ │ Channels    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │              VoiceHive Backend                  │
         │                                                 │
         │ ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
         │ │OpenTelemetry│  │ Dashboard   │  │ Health    │ │
         │ │Instrumentation│  │ API        │  │ Endpoints │ │
         │ └─────────────┘  └─────────────┘  └───────────┘ │
         └─────────────────────────────────────────────────┘
```

## 📊 Dashboard Features

### Main Dashboard
- **Real-time Metrics**: Live call volume, success rates, and system health
- **Interactive Charts**: Call duration trends, API response times
- **System Health**: Memory, CPU, and resource utilization
- **Recent Activity**: Live feed of system events and alerts

### Key Metrics Displayed
- Total calls processed
- Active calls count
- Success rate percentage
- Average call duration
- API response times
- System resource usage
- Alert status and count

### Dashboard Components

#### 1. Navbar Component
```typescript
// Navigation with real-time notifications
<Navbar />
```

#### 2. Dashboard Cards
```typescript
// Metric display cards with trend indicators
<DashboardCard
  title="Total Calls"
  value="1,247"
  icon={Phone}
  trend="+12%"
  trendDirection="up"
/>
```

#### 3. Interactive Charts
```typescript
// Real-time data visualization
<DashboardChart />
```

## 🔧 Monitoring Infrastructure

### OpenTelemetry Instrumentation

The monitoring system uses OpenTelemetry for comprehensive observability:

```python
from monitoring.instrumentation import get_instrumentation

# Initialize instrumentation
instrumentation = get_instrumentation()

# Record call metrics
instrumentation.record_call_metrics(
    duration=4.2,
    status="success",
    agent="roxy"
)

# Create trace spans
with instrumentation.create_span("call_processing") as span:
    span.set_attribute("call_id", call_id)
    # Process call...
```

### Metrics Collection

#### Call Metrics
- `voicehive_calls_total`: Total number of calls processed
- `voicehive_call_duration_seconds`: Call duration histogram
- `voicehive_active_calls`: Current active calls gauge

#### API Metrics
- `voicehive_api_requests_total`: Total API requests
- `voicehive_api_response_time_seconds`: API response time histogram

#### System Metrics
- `voicehive_system_memory_usage_percent`: Memory usage percentage
- `voicehive_system_cpu_usage_percent`: CPU usage percentage

### Distributed Tracing

Traces are collected using Jaeger for end-to-end request tracking:

```python
# Automatic instrumentation for FastAPI
from monitoring.instrumentation import setup_instrumentation

app = FastAPI()
setup_instrumentation(app)
```

## 🚨 Alerting System

### Alert Rules

The system includes comprehensive alert rules for:

#### Critical Alerts
- High error rate (>5%)
- Service downtime
- Critical memory usage (>90%)
- Database connection issues

#### Warning Alerts
- Low success rate (<90%)
- High API response time (>2s)
- High memory usage (>80%)
- Long call duration (>10 minutes)

### Alert Configuration

```yaml
# prometheus-rules.yml
- alert: HighErrorRate
  expr: rate(voicehive_calls_total{status="error"}[5m]) / rate(voicehive_calls_total[5m]) * 100 > 5
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }}% which is above the 5% threshold"
```

### Notification Channels

Alerts are sent through multiple channels:
- **Slack**: Real-time notifications to team channels
- **Email**: Critical alerts to administrators
- **Webhook**: Integration with external systems

## 🚀 Installation & Setup

### Prerequisites
- Node.js 18+ (for dashboard)
- Python 3.9+ (for backend)
- Docker & Docker Compose (for monitoring stack)

### Dashboard Setup

1. **Install Dependencies**
```bash
cd voicehive-backend/dashboard
npm install
```

2. **Configure Environment**
```bash
# Create .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

3. **Start Development Server**
```bash
npm run dev
```

### Backend Integration

1. **Install Monitoring Dependencies**
```bash
pip install -r requirements.txt
```

2. **Initialize Instrumentation**
```python
from monitoring.instrumentation import setup_instrumentation
from dashboard.api.dashboard import router as dashboard_router

app = FastAPI()
app.include_router(dashboard_router)
setup_instrumentation(app)
```

3. **Configure Environment Variables**
```bash
# .env
PROMETHEUS_PORT=8001
JAEGER_HOST=localhost
JAEGER_PORT=6831
SLACK_WEBHOOK_URL=your_slack_webhook_url
```

### Monitoring Stack Deployment

1. **Docker Compose Setup**
```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/alerts/prometheus-rules.yml:/etc/prometheus/rules.yml
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - ./monitoring/dashboards:/var/lib/grafana/dashboards
  
  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alerts/alertmanager.yml:/etc/alertmanager/alertmanager.yml
```

2. **Start Monitoring Stack**
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

## 📈 Usage Examples

### Dashboard API Usage

```python
# Get real-time metrics
response = requests.get("http://localhost:8000/api/dashboard/metrics")
metrics = response.json()

# Get system health
response = requests.get("http://localhost:8000/api/dashboard/health")
health = response.json()

# Get call volume data
response = requests.get("http://localhost:8000/api/dashboard/call-volume")
volume_data = response.json()
```

### WebSocket Real-time Updates

```javascript
// Connect to real-time updates
const ws = new WebSocket('ws://localhost:8000/api/dashboard/ws/real-time');

ws.onmessage = (event) => {
  const metrics = JSON.parse(event.data);
  updateDashboard(metrics);
};
```

### Custom Metrics Recording

```python
from monitoring.instrumentation import get_instrumentation

instrumentation = get_instrumentation()

# Record custom business metrics
instrumentation.record_call_metrics(
    duration=call_duration,
    status="success" if call_successful else "error",
    agent=agent_name
)

# Update system metrics
instrumentation.update_system_metrics(
    memory_usage=psutil.virtual_memory().percent,
    cpu_usage=psutil.cpu_percent(),
    active_calls=get_active_call_count()
)
```

## 🧪 Testing

### Running Tests

```bash
# Run all Sprint 4 tests
pytest tests/test_sprint4_dashboard_monitoring.py -v

# Run specific test categories
pytest tests/test_sprint4_dashboard_monitoring.py::TestDashboardAPI -v
pytest tests/test_sprint4_dashboard_monitoring.py::TestMonitoringInstrumentation -v
pytest tests/test_sprint4_dashboard_monitoring.py::TestAlertingSystem -v
```

### Test Coverage

The test suite covers:
- Dashboard API endpoints
- Monitoring instrumentation
- Alert rule validation
- Real-time data flow
- Error handling
- Performance monitoring

### Integration Testing

```python
# End-to-end monitoring flow test
@pytest.mark.integration
async def test_complete_monitoring_flow():
    # Generate metrics
    instrumentation.record_call_metrics(4.2, "success", "roxy")
    
    # Verify dashboard API
    response = client.get("/api/dashboard/metrics")
    assert response.status_code == 200
    
    # Check real-time updates
    response = client.get("/api/dashboard/recent-activity")
    assert response.status_code == 200
```

## 🔍 Troubleshooting

### Common Issues

#### Dashboard Not Loading
```bash
# Check if backend is running
curl http://localhost:8000/api/dashboard/metrics

# Verify Node.js dependencies
cd dashboard && npm install

# Check environment variables
cat dashboard/.env.local
```

#### Metrics Not Appearing
```bash
# Verify Prometheus is scraping metrics
curl http://localhost:8001/metrics

# Check instrumentation initialization
grep "instrumentation" logs/app.log

# Validate Prometheus configuration
docker logs prometheus-container
```

#### Alerts Not Firing
```bash
# Check Prometheus rules
curl http://localhost:9090/api/v1/rules

# Verify Alertmanager configuration
curl http://localhost:9093/api/v1/status

# Test alert rules manually
curl -X POST http://localhost:9093/api/v1/alerts
```

### Performance Optimization

#### Dashboard Performance
- Enable React.memo for components
- Implement virtual scrolling for large datasets
- Use WebSocket for real-time updates
- Cache API responses appropriately

#### Monitoring Overhead
- Adjust metric collection intervals
- Use sampling for high-volume traces
- Optimize Prometheus retention policies
- Configure appropriate alert thresholds

## 📚 API Reference

### Dashboard Endpoints

#### GET /api/dashboard/metrics
Returns current system metrics.

**Response:**
```json
{
  "total_calls": 1247,
  "active_calls": 8,
  "success_rate": 94.2,
  "avg_duration": 4.3,
  "system_health": "healthy",
  "alerts": 2,
  "last_updated": "2024-01-06T15:30:00Z"
}
```

#### GET /api/dashboard/health
Returns detailed system health information.

**Response:**
```json
{
  "status": "healthy",
  "api_response_time": 45.0,
  "memory_usage": 72.0,
  "cpu_usage": 35.0,
  "active_alerts": 2,
  "uptime": "5d 12h 30m"
}
```

#### GET /api/dashboard/call-volume
Returns call volume data for charting.

**Parameters:**
- `hours` (optional): Time period in hours (default: 24)

**Response:**
```json
[
  {"time": "00:00", "calls": 12},
  {"time": "02:00", "calls": 8},
  {"time": "04:00", "calls": 5}
]
```

#### WebSocket /api/dashboard/ws/real-time
Provides real-time metric updates.

**Message Format:**
```json
{
  "total_calls": 1248,
  "active_calls": 9,
  "success_rate": 94.3,
  "timestamp": "2024-01-06T15:31:00Z"
}
```

## 🔐 Security Considerations

### Authentication
- Implement JWT-based authentication for dashboard access
- Use API keys for monitoring endpoints
- Configure CORS policies appropriately

### Data Protection
- Encrypt sensitive metrics data
- Implement rate limiting on API endpoints
- Use HTTPS for all communications

### Access Control
- Role-based access to different dashboard sections
- Audit logging for administrative actions
- Secure storage of alert notification credentials

## 🚀 Deployment

### Production Deployment

1. **Build Dashboard**
```bash
cd dashboard
npm run build
npm run export
```

2. **Configure Production Environment**
```bash
# Production environment variables
ENVIRONMENT=production
PROMETHEUS_PORT=8001
GRAFANA_URL=https://grafana.yourdomain.com
ALERT_WEBHOOK_URL=https://alerts.yourdomain.com/webhook
```

3. **Deploy with Docker**
```bash
docker build -t voicehive-dashboard:latest .
docker run -d -p 3000:3000 voicehive-dashboard:latest
```

### Scaling Considerations

- Use Redis for session storage in multi-instance deployments
- Implement load balancing for dashboard instances
- Configure Prometheus federation for multi-region deployments
- Use external storage for Grafana dashboards

## 📊 Metrics & KPIs

### Business Metrics
- Call success rate
- Average call duration
- Customer satisfaction scores
- Agent performance metrics

### Technical Metrics
- API response times
- System resource utilization
- Error rates and types
- Service availability

### Operational Metrics
- Alert response times
- Mean time to resolution (MTTR)
- System uptime
- Deployment frequency

## 🔄 Continuous Improvement

### Monitoring Enhancements
- Add custom business metrics
- Implement anomaly detection
- Create predictive alerting
- Enhance dashboard visualizations

### Performance Optimization
- Optimize database queries
- Implement caching strategies
- Reduce monitoring overhead
- Improve alert accuracy

### Feature Roadmap
- Mobile dashboard application
- Advanced analytics and reporting
- Integration with external monitoring tools
- AI-powered incident prediction

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- Update dashboard dependencies
- Review and tune alert thresholds
- Clean up old metrics data
- Update Grafana dashboards

### Monitoring Health Checks
- Verify all monitoring components are running
- Check data retention policies
- Validate alert delivery
- Test disaster recovery procedures

### Documentation Updates
- Keep API documentation current
- Update deployment procedures
- Maintain troubleshooting guides
- Document configuration changes

---

## 🎉 Sprint 4 Success Criteria

✅ **Real-time Dashboard**: Functional Next.js dashboard with live metrics  
✅ **Comprehensive Monitoring**: OpenTelemetry instrumentation collecting metrics, traces, and logs  
✅ **Intelligent Alerting**: Prometheus rules with Alertmanager notifications  
✅ **Performance Analytics**: Detailed insights into system and call performance  
✅ **Production Ready**: Scalable, secure, and maintainable monitoring solution  

Sprint 4 delivers a world-class monitoring and dashboard solution that provides complete visibility into VoiceHive operations, enabling proactive issue resolution and data-driven optimization.
