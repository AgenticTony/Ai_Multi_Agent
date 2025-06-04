<div align="center">
  <h1>🚀 AI Voice Multi Agent</h1>
  <h3>Enterprise-Grade Multi-Agent Voice Platform</h3>
  <p>Revolutionize your call center with intelligent, self-learning voice agents that never sleep.</p>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
  [![Next.js](https://img.shields.io/badge/Next.js-14.0+-black.svg)](https://nextjs.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-009688.svg)](https://fastapi.tiangolo.com/)
  
  [![Watch Demo](https://img.shields.io/badge/📺-Watch%20Demo-red)](https://youtube.com/)
  [![Try Demo](https://img.shields.io/badge/🚀-Try%20Demo%20Free-blue)](https://example.com)
</div>

## 🌟 Features

### 🤖 Intelligent Call Handling
- **24/7 AI Agents** - Never miss a call with our always-available voice agents
- **Natural Conversations** - Powered by OpenAI's latest models for human-like interactions
- **Multi-language Support** - Serve customers in their preferred language

### 📊 Real-time Analytics Dashboard
- **Call Monitoring** - Live view of all active calls and agent performance
- **Sentiment Analysis** - Track customer satisfaction in real-time
- **Custom Reporting** - Generate insights with our comprehensive analytics suite

### 🛠 Enterprise Ready
- **Scalable Architecture** - Built to handle thousands of concurrent calls
- **Self-learning** - Agents improve over time using feedback loops
- **GDPR Compliant** - Enterprise-grade security and data protection

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL (or SQLite for development)
- OpenAI API Key
- VAPI.ai Account
- Twilio Account (for telephony)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/voicehive-ai.git
   cd ai-voice-multi-agent
   ```

2. **Set up the backend**
   ```bash
   cd voicehive-backend
   cp env.template .env
   # Edit .env with your API keys
   pip install -r requirements.txt
   ```

3. **Set up the dashboard**
   ```bash
   cd dashboard
   npm install
   cp .env.local.example .env.local
   # Edit .env.local with your backend URL
   ```

4. **Run the application**
   ```bash
   # Terminal 1: Start backend
   cd voicehive-backend
   uvicorn app.main:app --reload
   
   # Terminal 2: Start dashboard
   cd voicehive-backend/dashboard
   npm run dev
   ```

5. **Access the dashboard**
   - Frontend: http://localhost:3001
   - API Docs: http://localhost:8000/docs

## 🏗 Project Structure

```
ai-voice-multi-agent/
├── voicehive-backend/           # 🚀 FastAPI Backend
│   ├── app/                     # Application code
│   │   ├── api/                 # API endpoints
│   │   ├── core/                # Core functionality
│   │   ├── models/              # Database models
│   │   └── services/            # Business logic
│   ├── tests/                   # Test suite
│   └── dashboard/               # 📊 Next.js Dashboard
│       ├── src/
│       │   ├── app/            # App router
│       │   ├── components/      # Reusable components
│       │   └── lib/             # Utility functions
│       └── public/              # Static assets
└── docs/                        # 📚 Documentation
    ├── ARCHITECTURE.md         # System design
    ├── API_REFERENCE.md        # API documentation
    └── DEPLOYMENT_GUIDE.md     # Deployment instructions
```

## 📚 Documentation

Explore our comprehensive documentation:

- [Business Overview](./docs/BUSINESS_OVERVIEW.md) - Project vision and goals
- [Architecture Guide](./docs/ARCHITECTURE.md) - System design and components
- [API Reference](./docs/API_REFERENCE.md) - Detailed API documentation
- [Deployment Guide](./docs/DEPLOYMENT_GUIDE.md) - Production deployment instructions

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) to get started.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Built with ❤️ by the AI Voice Multi Agent Team**
- **Powered by** [OpenAI](https://openai.com/), [VAPI.ai](https://www.vapi.ai/), and [Twilio](https://www.twilio.com/)
- **Special thanks** to all our beta testers and contributors

## Development

The main application is in the `ai-voice-multi-agent-backend/` directory with its own comprehensive development workflow and documentation.

## License

MIT License - see documentation for details.
