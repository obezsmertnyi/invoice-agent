# 📚 Invoice Agent Documentation

Complete technical documentation for the Invoice Processing Agent.

> **Quick Start**: See [Main README](../README.md) for installation and basic usage.

## 📖 Documentation Overview

This directory contains in-depth technical documentation organized by topic:

### 🏗️ Architecture & Design

**High-Level Design (HLD)**
- **[System Overview](architecture/HLD-system-overview.md)** ⭐ **START HERE**
  - Complete system architecture with diagrams
  - Component descriptions and interactions
  - Data flow for all processing modes
  - Technology stack and deployment options
  - Scalability and monitoring strategies

**Architecture Decision Records (ADR)**

Why we made key technical decisions:
- **[ADR-001: Dual Processing Architecture](adr/ADR-001-dual-processing-architecture.md)**
  - Fast mode (Extract Thinker) vs Deep mode (CrewAI)
  - Performance vs quality trade-offs
  - Use cases and cost analysis

- **[ADR-002: Multi-Model LLM Strategy](adr/ADR-002-multi-model-llm-strategy.md)**
  - Supporting 9+ LLM models
  - Automatic fallback mechanism
  - Cost optimization and model selection

- **[ADR-003: PostgreSQL Database Choice](adr/ADR-003-postgresql-database-choice.md)**
  - Why PostgreSQL over alternatives
  - Full database schema with indexes
  - Query patterns and performance

- **[ADR-004: CrewAI Multi-Agent System](adr/ADR-004-crewai-multi-agent-system.md)**
  - 3 specialized agents architecture
  - Validator → Analyst → Reporter workflow
  - Quality improvements and metrics

- **[ADR-005: Natural Language Analytics](adr/ADR-005-natural-language-analytics.md)**
  - AI-powered SQL generation
  - Natural language queries (Ukrainian/English)
  - Security and performance considerations

### 📊 API Documentation

**Available Endpoints:**
- `/extract` - Fast extraction (~5-7 sec)
- `/extract_and_analyze` - Deep analysis (~45-55 sec)
- `/batch_analyze` - Batch processing with optional full analysis
- `/analytics/chat` - Natural language queries
- `/analytics/stats` - Overall statistics
- `/analytics/vendor/{name}` - Vendor-specific data
- `/health` - Service health check

**Interactive Documentation:**
- [Swagger UI](http://localhost:8000/docs) - Try API endpoints live
- [ReDoc](http://localhost:8000/redoc) - Alternative API docs

**Detailed API Reference:** See [Main README - API Endpoints](../README.md#-api-endpoints)

### 🚀 Deployment & Operations

**Docker Deployment:**
- See [HLD - Deployment Architecture](architecture/HLD-system-overview.md#deployment-architecture)
- Docker Compose setup with PostgreSQL
- Production deployment considerations

**Configuration:**
- Environment variables and `.env` setup
- Model selection and API keys
- Database connection strings

**Monitoring:**
- Performance metrics to track
- Logging and alerting setup
- Cost monitoring per invoice

### 🔧 Development

**Getting Started:**
1. Clone repository
2. Create virtual environment: `python3 -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Configure `.env` file
5. Run: `./run.sh`

**Testing:**
```bash
pytest tests/
```

**Code Structure:**
```
invoice_service.py      # Main FastAPI app
├── ExtractorManager    # Multi-model LLM orchestration
├── CrewAI Agents       # Validator, Analyst, Reporter
├── database.py         # PostgreSQL integration
└── analytics_agent.py  # Natural language analytics
```

## 🔗 Quick Navigation

| Topic | Link | Description |
|-------|------|-------------|
| **Quick Start** | [Main README](../README.md) | Installation and basic usage |
| **System Architecture** | [HLD Overview](architecture/HLD-system-overview.md) | Complete system design |
| **API Reference** | [API Endpoints](../README.md#-api-endpoints) | All API endpoints with examples |
| **Architecture Decisions** | [ADR Index](adr/) | Why we made key decisions |
| **Docker Setup** | [Main README - Docker](../README.md#-docker-support) | Docker Compose and deployment |
| **Troubleshooting** | [Main README](../README.md#-troubleshooting) | Common issues and solutions |

## 📝 Contributing to Documentation

When adding or updating documentation:

✅ **Do:**
- Use clear, concise language
- Include code examples and diagrams
- Add cross-references to related docs
- Update "Last Updated" dates
- Test all code examples

❌ **Don't:**
- Duplicate content from other docs (link instead)
- Add outdated information
- Use vague descriptions
- Forget to update related documents

## 🎯 Documentation Roadmap

### ✅ Completed
- [x] System architecture (HLD)
- [x] Architecture decision records (ADR)
- [x] API endpoint documentation
- [x] Quick start guide
- [x] Docker setup guide

### 🚧 In Progress
- [ ] Detailed API reference with all parameters
- [ ] Production deployment guide
- [ ] Monitoring and alerting setup
- [ ] Performance tuning guide

### 📋 Planned
- [ ] Video tutorials
- [ ] Integration examples (n8n, Zapier)
- [ ] Advanced configuration guide
- [ ] Troubleshooting flowcharts

---

**Last Updated**: 2025-11-19  
**Maintainer**: DevOps Team  
**Questions?** Open an issue on [GitHub](https://github.com/obezsmertnyi/invoice-agent/issues)
