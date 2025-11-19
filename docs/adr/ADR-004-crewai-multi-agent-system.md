# ADR-004: CrewAI Multi-Agent System

**Status**: Accepted  
**Date**: 2025-11-19  
**Decision Makers**: DevOps Team  
**Tags**: ai-agents, crewai, validation, fraud-detection

## Context

Deep invoice analysis requires multiple specialized tasks:
- **Data Validation**: Check completeness, consistency, format
- **Fraud Detection**: Identify anomalies, suspicious patterns
- **Risk Assessment**: Calculate risk levels based on multiple factors
- **Comprehensive Reporting**: Generate detailed analysis reports

Single-agent approach limitations:
- One prompt tries to do everything
- Difficult to maintain complex logic
- Hard to improve individual components
- No separation of concerns

## Decision

Implement **CrewAI multi-agent system** with three specialized agents for deep analysis mode.

### Agent Architecture

**1. Validator Agent**
- **Role**: Data Quality Specialist
- **Goal**: Ensure invoice data completeness and accuracy
- **Responsibilities**:
  - Verify all required fields present
  - Check data format consistency
  - Validate calculations (subtotal + tax = total)
  - Cross-reference vendor information
  - Flag missing or suspicious data

**2. Analyst Agent**
- **Role**: Fraud Detection Specialist
- **Goal**: Identify anomalies and fraud indicators
- **Responsibilities**:
  - Detect unusual amounts
  - Identify duplicate invoices
  - Check vendor legitimacy
  - Analyze payment terms
  - Calculate risk scores
  - Flag suspicious patterns

**3. Reporter Agent**
- **Role**: Reporting Specialist
- **Goal**: Generate comprehensive analysis reports
- **Responsibilities**:
  - Synthesize validation results
  - Summarize fraud analysis
  - Provide actionable recommendations
  - Generate markdown reports
  - Assign final risk levels

### Agent Workflow

```
Extract Thinker Extraction
         ↓
   Validator Agent
   (Data Quality Check)
         ↓
   Analyst Agent
   (Fraud Detection)
         ↓
   Reporter Agent
   (Comprehensive Report)
         ↓
   Database Storage
```

## Consequences

### Positive
✅ **Separation of Concerns**: Each agent has clear responsibility  
✅ **Maintainability**: Easy to improve individual agents  
✅ **Quality**: Specialized agents perform better than generalist  
✅ **Flexibility**: Can add/remove agents as needed  
✅ **Transparency**: Clear audit trail of analysis steps  
✅ **Scalability**: Agents can run in parallel (future)  

### Negative
❌ **Performance**: Sequential processing takes longer (~45-55 sec)  
❌ **Cost**: Multiple LLM calls increase API costs  
❌ **Complexity**: More moving parts to maintain  
❌ **Dependencies**: CrewAI framework dependency  

### Mitigation
- Use fast mode for bulk processing
- Reserve deep mode for high-value invoices
- Cache agent results where possible
- Monitor and optimize agent prompts
- Consider parallel execution (future)

## Implementation

### Agent Configuration (agents.yaml)

```yaml
validator_agent:
  role: "Invoice Data Validator"
  goal: "Ensure invoice data is complete, accurate, and properly formatted"
  backstory: >
    You are an expert in invoice data validation with years of experience
    in financial document processing. You have a keen eye for detail and
    can quickly identify missing or inconsistent information.

analyst_agent:
  role: "Fraud Detection Analyst"
  goal: "Identify anomalies, suspicious patterns, and potential fraud"
  backstory: >
    You are a seasoned fraud analyst with expertise in detecting financial
    irregularities. You understand common fraud patterns and can assess
    risk levels based on multiple indicators.

reporter_agent:
  role: "Analysis Reporter"
  goal: "Generate comprehensive, actionable analysis reports"
  backstory: >
    You are a skilled technical writer who excels at synthesizing complex
    analysis into clear, actionable reports. You provide recommendations
    that help decision-makers take appropriate action.
```

### Task Configuration (tasks.yaml)

```yaml
validate_invoice:
  description: >
    Validate the extracted invoice data for completeness and accuracy.
    Check all required fields, verify calculations, and flag any issues.
  expected_output: >
    A validation report with:
    - List of issues found
    - Data completeness score
    - Recommendations for corrections

analyze_fraud:
  description: >
    Analyze the invoice for fraud indicators and anomalies.
    Calculate risk score based on multiple factors.
  expected_output: >
    A fraud analysis report with:
    - Risk level (low/medium/high)
    - List of fraud indicators
    - Anomalies detected
    - Risk score calculation

generate_report:
  description: >
    Generate a comprehensive analysis report combining validation
    and fraud analysis results.
  expected_output: >
    A markdown report with:
    - Executive summary
    - Validation results
    - Fraud analysis
    - Final risk assessment
    - Actionable recommendations
```

### API Integration

```python
@app.post("/extract_and_analyze")
async def extract_and_analyze_invoice(file: UploadFile):
    # Step 1: Fast extraction with Extract Thinker
    extracted_data = await extract_thinker.extract(file)
    
    # Step 2: CrewAI multi-agent analysis
    crew = Crew(
        agents=[validator_agent, analyst_agent, reporter_agent],
        tasks=[validate_task, analyze_task, report_task],
        process=Process.sequential
    )
    
    result = crew.kickoff(inputs={"invoice_data": extracted_data})
    
    # Step 3: Store results
    await db.store_invoice(extracted_data, result)
    
    return {
        "extracted_data": extracted_data,
        "validation_report": result.validation,
        "analysis_report": result.analysis,
        "comprehensive_report": result.report
    }
```

## Performance Metrics

**Agent Execution Times:**
- Validator Agent: ~10-15 seconds
- Analyst Agent: ~15-20 seconds
- Reporter Agent: ~10-15 seconds
- **Total**: ~45-55 seconds

**Cost per Invoice (Deep Mode):**
- Extract Thinker: ~$0.001
- Validator Agent: ~$0.003-0.005
- Analyst Agent: ~$0.005-0.010
- Reporter Agent: ~$0.003-0.005
- **Total**: ~$0.015-0.025 per invoice

## Quality Improvements

**Fraud Detection Rate:**
- Single-agent: ~70% accuracy
- Multi-agent: ~90% accuracy
- **Improvement**: +20%

**False Positive Rate:**
- Single-agent: ~15%
- Multi-agent: ~5%
- **Improvement**: -10%

## Alternatives Considered

### 1. Single Comprehensive Agent
- **Pros**: Faster, simpler, cheaper
- **Cons**: Lower quality, hard to maintain
- **Rejected**: Quality not sufficient

### 2. LangChain Agents
- **Pros**: More flexible, tool calling
- **Cons**: More complex, less structured
- **Rejected**: CrewAI better for structured workflows

### 3. Custom Agent Framework
- **Pros**: Full control, optimized
- **Cons**: High development cost, maintenance burden
- **Rejected**: CrewAI provides sufficient functionality

## Future Enhancements

1. **Parallel Execution**: Run agents concurrently
2. **Agent Caching**: Cache agent results for similar invoices
3. **Dynamic Agent Selection**: Choose agents based on invoice type
4. **Human-in-the-Loop**: Allow manual review for high-risk cases
5. **Agent Learning**: Improve agents based on feedback

## Related Decisions

- [ADR-001: Dual Processing Architecture](ADR-001-dual-processing-architecture.md)
- [ADR-002: Multi-Model LLM Strategy](ADR-002-multi-model-llm-strategy.md)

## References

- CrewAI Documentation: https://docs.crewai.com/
- Multi-Agent Systems: https://en.wikipedia.org/wiki/Multi-agent_system
- Agent Design Patterns: https://www.patterns.dev/posts/agent-pattern

---

**Review Date**: 2026-01-19 (Quarterly review)
