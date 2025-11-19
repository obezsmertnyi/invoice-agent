# HLD: System Overview

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Author**: DevOps Team  
**Status**: Active

## 1. Executive Summary

Invoice Processing Agent is an AI-powered system for automated invoice extraction, validation, fraud detection, and analytics. The system provides dual processing modes (fast and deep) with natural language query capabilities.

### Key Capabilities
- **Automated Extraction**: Extract structured data from PDF invoices
- **Fraud Detection**: AI-powered anomaly and fraud detection
- **Natural Language Analytics**: Query invoice data in Ukrainian/English
- **Multi-Model Support**: 9+ LLM models with automatic fallback
- **Database Storage**: PostgreSQL with full analytics capabilities

### Performance Metrics
- **Fast Mode**: ~5-7 seconds per invoice
- **Deep Mode**: ~45-55 seconds per invoice
- **Analytics Queries**: ~2-3 seconds
- **Throughput**: 1,000-10,000 invoices/day

## 2. System Architecture

### 2.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   Web    │  │   CLI    │  │   API    │  │   n8n    │       │
│  │   UI     │  │   Tool   │  │  Client  │  │ Workflow │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
        ┌─────────────▼──────────────────────────────────────────┐
        │              FastAPI Application Layer                  │
        │  ┌────────────────────────────────────────────────┐   │
        │  │           REST API Endpoints                    │   │
        │  │  /extract  /extract_and_analyze  /batch_analyze │   │
        │  │  /analytics/*  /health  /docs                   │   │
        │  └────────────────────────────────────────────────┘   │
        └─────────────┬──────────────────────────────────────────┘
                      │
        ┌─────────────▼──────────────────────────────────────────┐
        │            Processing Layer                             │
        │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
        │  │   Extract    │  │   CrewAI     │  │  Analytics   │ │
        │  │   Thinker    │  │  Multi-Agent │  │    Agent     │ │
        │  │  (Fast)      │  │  (Deep)      │  │  (NL Query)  │ │
        │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
        └─────────┼──────────────────┼──────────────────┼─────────┘
                  │                  │                  │
        ┌─────────▼──────────────────▼──────────────────▼─────────┐
        │              LLM Orchestration Layer                     │
        │  ┌────────────────────────────────────────────────────┐ │
        │  │           ExtractorManager                          │ │
        │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐          │ │
        │  │  │  OpenAI  │ │Anthropic │ │  Ollama  │          │ │
        │  │  │ GPT-5    │ │ Claude   │ │ Llama3.3 │          │ │
        │  │  └──────────┘ └──────────┘ └──────────┘          │ │
        │  └────────────────────────────────────────────────────┘ │
        └──────────────────────────┬───────────────────────────────┘
                                   │
        ┌──────────────────────────▼───────────────────────────────┐
        │              Data Layer                                   │
        │  ┌────────────────────────────────────────────────────┐  │
        │  │           PostgreSQL Database                       │  │
        │  │  - invoices table                                   │  │
        │  │  - JSONB for flexible fields                        │  │
        │  │  - Indexes for performance                          │  │
        │  │  - ACID compliance                                  │  │
        │  └────────────────────────────────────────────────────┘  │
        └───────────────────────────────────────────────────────────┘
```

### 2.2 Component Descriptions

#### 2.2.1 Client Layer
- **Web UI**: Swagger/ReDoc interactive documentation
- **CLI Tool**: Command-line interface for automation
- **API Client**: Direct REST API integration
- **n8n Workflow**: Workflow automation integration

#### 2.2.2 FastAPI Application Layer
- **REST API**: Asynchronous FastAPI endpoints
- **Request Validation**: Pydantic models
- **Error Handling**: Comprehensive exception handling
- **Authentication**: API key management (future)
- **Rate Limiting**: Request throttling (future)

#### 2.2.3 Processing Layer

**Extract Thinker (Fast Mode)**
- Single-pass extraction
- Document classification
- Data validation
- ~5-7 seconds processing

**CrewAI Multi-Agent (Deep Mode)**
- Validator Agent: Data quality check
- Analyst Agent: Fraud detection
- Reporter Agent: Comprehensive reporting
- ~45-55 seconds processing

**Analytics Agent (NL Query)**
- Natural language to SQL
- Query execution
- Natural language response
- ~2-3 seconds processing

#### 2.2.4 LLM Orchestration Layer
- **ExtractorManager**: Multi-model orchestration
- **Automatic Fallback**: Retry with backup models
- **Model Selection**: Choose optimal model for task
- **Error Handling**: Graceful degradation

#### 2.2.5 Data Layer
- **PostgreSQL 16**: Primary database
- **JSONB Storage**: Flexible schema
- **Indexes**: Optimized queries
- **Backup Strategy**: Automated backups

## 3. Data Flow

### 3.1 Fast Extraction Flow

```
1. Client uploads PDF invoice
   ↓
2. FastAPI receives request at /extract
   ↓
3. Extract Thinker processes document
   ├─ Document classification
   ├─ Data extraction (single LLM call)
   └─ Basic validation
   ↓
4. Data stored in PostgreSQL
   ↓
5. Response returned to client
   
Total Time: ~5-7 seconds
```

### 3.2 Deep Analysis Flow

```
1. Client uploads PDF invoice
   ↓
2. FastAPI receives request at /extract_and_analyze
   ↓
3. Extract Thinker extracts data
   ↓
4. CrewAI Multi-Agent processing:
   ├─ Validator Agent validates data
   ├─ Analyst Agent detects fraud
   └─ Reporter Agent generates report
   ↓
5. Results stored in PostgreSQL
   ↓
6. Comprehensive response returned
   
Total Time: ~45-55 seconds
```

### 3.3 Analytics Query Flow

```
1. Client sends natural language question
   ↓
2. FastAPI receives request at /analytics/chat
   ↓
3. Analytics Agent processes:
   ├─ Generate SQL from question (LLM)
   ├─ Validate SQL for security
   ├─ Execute query on PostgreSQL
   └─ Generate natural language answer (LLM)
   ↓
4. Response returned to client
   
Total Time: ~2-3 seconds
```

## 4. Technology Stack

### 4.1 Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Web Framework** | FastAPI | 0.115+ | REST API |
| **Extraction** | Extract Thinker | 0.1.14+ | Document processing |
| **Multi-Agent** | CrewAI | 1.5.0+ | Agent orchestration |
| **Database** | PostgreSQL | 16 | Data storage |
| **Python** | Python | 3.10+ | Runtime |
| **LLM APIs** | OpenAI, Anthropic, Cohere | Latest | AI models |
| **Local LLM** | Ollama | Latest | Local inference |

### 4.2 Key Libraries

- **pydantic**: Data validation and contracts
- **sqlalchemy**: Database ORM
- **asyncio**: Asynchronous processing
- **uvicorn**: ASGI server
- **pypdf**: PDF parsing
- **litellm**: Unified LLM interface

## 5. Deployment Architecture

### 5.1 Local Development

```
┌─────────────────────────────────────┐
│      Developer Machine              │
│  ┌────────────────────────────────┐ │
│  │  Python Virtual Environment    │ │
│  │  - FastAPI Application         │ │
│  │  - Port 8000                   │ │
│  └────────────────────────────────┘ │
│  ┌────────────────────────────────┐ │
│  │  PostgreSQL (Docker)           │ │
│  │  - Port 5432                   │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 5.2 Docker Deployment

```
┌─────────────────────────────────────┐
│      Docker Host                    │
│  ┌────────────────────────────────┐ │
│  │  invoice-agent container       │ │
│  │  - FastAPI app                 │ │
│  │  - Port 8000                   │ │
│  └────────┬───────────────────────┘ │
│           │                          │
│  ┌────────▼───────────────────────┐ │
│  │  postgres container            │ │
│  │  - PostgreSQL 16               │ │
│  │  - Port 5432                   │ │
│  │  - Volume: postgres_data       │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 5.3 Production Deployment (Future)

```
┌─────────────────────────────────────────────┐
│      Cloud Platform (GCP/AWS)               │
│  ┌────────────────────────────────────────┐ │
│  │  Load Balancer                         │ │
│  └────────┬───────────────────────────────┘ │
│           │                                  │
│  ┌────────▼───────────┐  ┌────────────────┐│
│  │  App Instance 1    │  │ App Instance 2 ││
│  │  (Container/VM)    │  │ (Container/VM) ││
│  └────────┬───────────┘  └────────┬───────┘│
│           │                       │         │
│  ┌────────▼───────────────────────▼───────┐│
│  │  Managed PostgreSQL                    ││
│  │  (Cloud SQL / RDS)                     ││
│  │  - High Availability                   ││
│  │  - Automated Backups                   ││
│  └────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

## 6. Security Considerations

### 6.1 API Security
- API key authentication (future)
- Rate limiting per client
- Request size limits
- CORS configuration

### 6.2 Data Security
- SQL injection prevention
- Input validation
- Parameterized queries
- Query timeout limits

### 6.3 LLM Security
- API key encryption
- Secure credential storage
- No sensitive data in prompts
- Response validation

### 6.4 Database Security
- Connection encryption (SSL)
- Role-based access control
- Audit logging
- Regular backups

## 7. Scalability

### 7.1 Current Capacity
- **Throughput**: 1,000-10,000 invoices/day
- **Concurrent Users**: 10-50
- **Database Size**: Up to 1M invoices
- **Response Time**: P95 < 10 seconds (fast mode)

### 7.2 Scaling Strategies

**Vertical Scaling**
- Increase CPU/RAM for app server
- Upgrade PostgreSQL instance
- Add more LLM API quota

**Horizontal Scaling**
- Multiple app instances behind load balancer
- Database read replicas for analytics
- Caching layer (Redis) for common queries

**Performance Optimization**
- Connection pooling
- Query result caching
- Async processing for batch operations
- Background job queue (Celery)

## 8. Monitoring & Observability

### 8.1 Metrics to Track
- Request rate and latency
- Error rate by endpoint
- LLM API success rate
- Database query performance
- Processing time per mode
- Cost per invoice

### 8.2 Logging
- Application logs (INFO, WARNING, ERROR)
- API access logs
- LLM API call logs
- Database query logs
- Audit trail for all operations

### 8.3 Alerting
- API downtime
- High error rate
- Database connection failures
- LLM API quota exceeded
- Slow query performance

## 9. Future Enhancements

### Phase 1 (Q1 2026)
- [ ] API authentication and authorization
- [ ] Rate limiting per user
- [ ] Webhook notifications
- [ ] Batch processing improvements

### Phase 2 (Q2 2026)
- [ ] Web UI for invoice upload
- [ ] Real-time processing status
- [ ] Advanced analytics dashboard
- [ ] Multi-tenant support

### Phase 3 (Q3 2026)
- [ ] OCR for scanned invoices
- [ ] Email integration
- [ ] Automated approval workflows
- [ ] Machine learning model training

## 10. References

- [ADR-001: Dual Processing Architecture](../adr/ADR-001-dual-processing-architecture.md)
- [ADR-002: Multi-Model LLM Strategy](../adr/ADR-002-multi-model-llm-strategy.md)
- [ADR-003: PostgreSQL Database Choice](../adr/ADR-003-postgresql-database-choice.md)
- [ADR-004: CrewAI Multi-Agent System](../adr/ADR-004-crewai-multi-agent-system.md)
- [ADR-005: Natural Language Analytics](../adr/ADR-005-natural-language-analytics.md)

---

**Document Control**
- **Version**: 1.0
- **Last Review**: 2025-11-19
- **Next Review**: 2026-01-19
- **Owner**: DevOps Team
