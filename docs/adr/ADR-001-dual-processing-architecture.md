# ADR-001: Dual Processing Architecture

**Status**: Accepted  
**Date**: 2025-11-19  
**Decision Makers**: DevOps Team  
**Tags**: architecture, processing, performance

## Context

Invoice processing requires different approaches depending on the use case:
- **High-volume processing**: Needs speed and cost efficiency
- **High-value invoices**: Requires deep validation and fraud detection
- **Compliance requirements**: Needs comprehensive audit trails

A single processing approach cannot efficiently serve all these needs.

## Decision

Implement a **dual processing architecture** with two distinct modes:

### 1. Fast Mode (Extract Thinker)
- **Purpose**: High-speed, cost-effective extraction
- **Technology**: Extract Thinker with single LLM call
- **Performance**: ~5-7 seconds per invoice
- **Use Cases**: 
  - Bulk invoice processing
  - Low-risk invoices
  - Quick data extraction
  - Cost-sensitive operations

### 2. Deep Mode (CrewAI Multi-Agent)
- **Purpose**: Comprehensive analysis and validation
- **Technology**: CrewAI with 3 specialized agents
- **Performance**: ~45-55 seconds per invoice
- **Use Cases**:
  - High-value invoices
  - Fraud detection required
  - Compliance and audit
  - Detailed reporting needed

## Consequences

### Positive
✅ **Flexibility**: Users choose appropriate mode for their needs  
✅ **Cost Optimization**: Fast mode reduces API costs for bulk processing  
✅ **Quality Assurance**: Deep mode provides thorough validation  
✅ **Scalability**: Fast mode handles high volumes efficiently  
✅ **Risk Management**: Deep mode catches fraud and anomalies  

### Negative
❌ **Complexity**: Two processing pipelines to maintain  
❌ **User Decision**: Users must understand which mode to use  
❌ **Code Duplication**: Some logic shared between modes  

### Mitigation
- Clear documentation on when to use each mode
- Default to fast mode for simplicity
- Shared extraction logic to reduce duplication
- Unified API interface for both modes

## Alternatives Considered

### 1. Single Fast Processing Only
- **Pros**: Simple, fast, cost-effective
- **Cons**: No deep validation, fraud detection limited
- **Rejected**: Insufficient for high-value invoices

### 2. Single Deep Processing Only
- **Pros**: Comprehensive analysis for all invoices
- **Cons**: Too slow and expensive for bulk processing
- **Rejected**: Not scalable for high volumes

### 3. Automatic Mode Selection
- **Pros**: No user decision required
- **Cons**: Complex heuristics, may choose wrong mode
- **Rejected**: User knows their requirements best

## Implementation

```python
# Fast Mode
POST /extract
- Extract Thinker extraction
- Basic validation
- Database storage
- ~5-7 seconds

# Deep Mode
POST /extract_and_analyze
- Extract Thinker extraction
- CrewAI validation agent
- CrewAI fraud detection agent
- CrewAI reporting agent
- Database storage
- ~45-55 seconds

# Batch with mode selection
POST /batch_analyze?full_analysis=false  # Fast mode
POST /batch_analyze?full_analysis=true   # Deep mode
```

## Related Decisions

- [ADR-002: Multi-Model LLM Strategy](ADR-002-multi-model-llm-strategy.md)
- [ADR-004: CrewAI Multi-Agent System](ADR-004-crewai-multi-agent-system.md)

## References

- Extract Thinker: https://github.com/enoch3712/ExtractThinker
- CrewAI: https://docs.crewai.com/
- Performance benchmarks: Internal testing results

---

**Review Date**: 2026-01-19 (Quarterly review)
