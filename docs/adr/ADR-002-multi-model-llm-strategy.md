# ADR-002: Multi-Model LLM Strategy

**Status**: Accepted  
**Date**: 2025-11-19  
**Decision Makers**: DevOps Team  
**Tags**: llm, ai-models, cost-optimization

## Context

Different LLM providers offer various trade-offs:
- **Cost**: OpenAI GPT-4o-mini ($0.15/1M) vs GPT-5 ($1.25/1M)
- **Speed**: Claude Haiku 4.5 (fastest) vs GPT-5 (slower)
- **Privacy**: Cloud APIs vs local Ollama models
- **Capabilities**: Reasoning (o3), multilingual (Cohere), vision
- **Availability**: API rate limits, regional restrictions

Single-model dependency creates risks:
- Vendor lock-in
- API outages
- Cost unpredictability
- Limited feature access

## Decision

Implement **multi-model LLM strategy** with automatic fallback:

### Supported Providers

**1. OpenAI (Primary)**
- GPT-5, GPT-5-mini, GPT-5-nano
- GPT-4.1, GPT-4.1-mini
- GPT-4o, GPT-4o-mini
- o3, o3-mini (reasoning)

**2. Anthropic (Secondary)**
- Claude Sonnet 4.5 (flagship)
- Claude Haiku 4.5 (fastest)
- Claude Opus 4.1 (most powerful)

**3. Ollama (Local/Privacy)**
- Llama 3.3
- Qwen 2.5:14b
- Mistral
- DeepSeek-R1:7b

**4. Cohere (Multilingual)**
- Command-R-Plus
- Command-R

### Selection Strategy

```python
# Priority order with automatic fallback
PRIMARY_MODEL = "gpt-4.1-nano"  # Fast, cheap, accurate
BACKUP_MODELS = [
    "gpt-5-mini",                # Better quality
    "claude-sonnet-4-5",         # Different provider
    "gpt-4o-mini",               # Cheapest option
    "ollama/llama3.3"            # Local fallback
]
```

### Model Selection Logic

- **Default**: GPT-4.1-nano (best balance)
- **Privacy Critical**: Ollama (local, no API calls)
- **Speed Critical**: Claude Haiku 4.5
- **Cost Sensitive**: GPT-4o-mini
- **Multilingual**: Cohere Command-R-Plus
- **Reasoning**: o3-mini

## Consequences

### Positive
✅ **Resilience**: Automatic fallback on API failures  
✅ **Cost Optimization**: Choose cheapest model for task  
✅ **Performance**: Select fastest model when needed  
✅ **Privacy**: Local models for sensitive data  
✅ **Flexibility**: Easy to add new models  
✅ **Vendor Independence**: Not locked to single provider  

### Negative
❌ **Complexity**: Multiple API integrations to maintain  
❌ **Testing**: Must test all model combinations  
❌ **Consistency**: Different models may produce different results  
❌ **Configuration**: More API keys to manage  

### Mitigation
- Unified ExtractorManager interface
- Comprehensive error handling
- Model performance monitoring
- Clear documentation on model selection
- Consistent prompting across models

## Implementation

```python
class ExtractorManager:
    def __init__(self):
        self.extractors = {}
        self._initialize_extractors()
    
    def extract_with_fallback(self, file_path, contract_type):
        """Try primary model, fallback to backups on failure"""
        models = [PRIMARY_MODEL] + BACKUP_MODELS
        
        for model in models:
            try:
                return self._extract(model, file_path, contract_type)
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
                continue
        
        raise Exception("All models failed")
```

## Cost Analysis

**Per 1M tokens (input/output):**
- GPT-4o-mini: $0.15/$0.60 ✅ **Cheapest**
- GPT-4.1-nano: $0.20/$0.80
- GPT-5-mini: $0.25/$2.00 🔥 **Recommended**
- Claude Haiku 4.5: $0.25/$1.25 ⚡ **Fastest**
- GPT-5: $1.25/$10.00
- Claude Sonnet 4.5: $3.00/$15.00

**Estimated costs (per invoice):**
- Fast mode: ~$0.001-0.003 per invoice
- Deep mode: ~$0.01-0.03 per invoice

## Alternatives Considered

### 1. Single Model (OpenAI Only)
- **Pros**: Simple, consistent
- **Cons**: Vendor lock-in, no fallback
- **Rejected**: Too risky

### 2. Open Source Only (Ollama)
- **Pros**: Free, private, no API limits
- **Cons**: Lower accuracy, requires GPU
- **Rejected**: Quality not sufficient

### 3. Anthropic Only
- **Pros**: High quality, good context
- **Cons**: More expensive, limited models
- **Rejected**: Cost prohibitive

## Monitoring

Track per model:
- Success rate
- Average latency
- Cost per request
- Error types
- Quality scores

## Related Decisions

- [ADR-001: Dual Processing Architecture](ADR-001-dual-processing-architecture.md)
- [ADR-004: CrewAI Multi-Agent System](ADR-004-crewai-multi-agent-system.md)

## References

- OpenAI Pricing: https://openai.com/pricing
- Anthropic Pricing: https://www.anthropic.com/pricing
- Ollama: https://ollama.ai/
- Extract Thinker: https://github.com/enoch3712/ExtractThinker

---

**Review Date**: 2026-01-19 (Quarterly review)
