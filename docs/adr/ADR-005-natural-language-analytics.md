# ADR-005: Natural Language Analytics

**Status**: Accepted  
**Date**: 2025-11-19  
**Decision Makers**: DevOps Team  
**Tags**: analytics, nlp, sql-generation, user-experience

## Context

Users need to query invoice data for business insights:
- "What is the total amount from vendor X?"
- "How many invoices are high risk?"
- "Top 5 vendors by total amount"
- "Average invoice amount for vendor Y"

Traditional approaches:
- **Manual SQL**: Requires SQL knowledge, error-prone
- **Fixed Reports**: Limited flexibility, can't answer ad-hoc questions
- **BI Tools**: Complex setup, steep learning curve

Users want to ask questions in natural language (Ukrainian/English) and get immediate answers.

## Decision

Implement **AI-powered natural language analytics** that:
1. Accepts questions in Ukrainian or English
2. Generates SQL queries using LLM
3. Executes queries on PostgreSQL
4. Returns natural language answers

### Architecture

```
User Question (Natural Language)
         ↓
   AI SQL Generator (LLM)
         ↓
   PostgreSQL Query
         ↓
   Query Results
         ↓
   AI Answer Generator (LLM)
         ↓
   Natural Language Answer
```

## Implementation

### Analytics Agent

```python
async def process_analytics_question(question: str, db_connection):
    """
    Process natural language question about invoices
    
    Args:
        question: User question in Ukrainian or English
        db_connection: Database connection
        
    Returns:
        {
            "question": original question,
            "answer": natural language answer,
            "sql_query": generated SQL,
            "results": query results,
            "row_count": number of rows
        }
    """
    
    # Step 1: Generate SQL from natural language
    sql_query = await generate_sql(question)
    
    # Step 2: Execute SQL query
    results = await execute_query(sql_query, db_connection)
    
    # Step 3: Generate natural language answer
    answer = await generate_answer(question, results)
    
    return {
        "question": question,
        "answer": answer,
        "sql_query": sql_query,
        "results": results,
        "row_count": len(results)
    }
```

### SQL Generation Prompt

```python
SYSTEM_PROMPT = """
You are an expert SQL query generator for invoice analytics.

Database Schema:
- Table: invoices
- Columns: invoice_number, invoice_date, vendor_name, total_amount, 
           currency, risk_level, created_at, etc.

Generate PostgreSQL queries for user questions.
Use proper aggregations, filters, and sorting.
Return only the SQL query, no explanations.
"""

USER_PROMPT = f"""
Question: {question}

Generate SQL query to answer this question.
"""
```

### API Endpoint

```python
@app.post("/analytics/chat")
async def chat_analytics(request: ChatRequest):
    """
    Natural language analytics endpoint
    
    Example questions:
    - "What is the total amount of invoices from Nedstone for October 2025?"
    - "How many invoices are there from Atlassian?"
    - "Top 5 vendors by total amount"
    - "Which invoices have high risk?"
    """
    result = await process_analytics_question(
        question=request.question,
        db_connection=db.connection
    )
    
    return ChatResponse(**result)
```

## Consequences

### Positive
✅ **User-Friendly**: No SQL knowledge required  
✅ **Flexible**: Can answer any question about data  
✅ **Multilingual**: Supports Ukrainian and English  
✅ **Fast**: Answers in 2-3 seconds  
✅ **Transparent**: Shows generated SQL for verification  
✅ **Accessible**: Simple REST API endpoint  

### Negative
❌ **LLM Dependency**: Requires LLM API for SQL generation  
❌ **Query Validation**: Generated SQL might be incorrect  
❌ **Security Risk**: Potential SQL injection if not validated  
❌ **Cost**: Each question requires LLM API call  

### Mitigation
- SQL query validation before execution
- Parameterized queries to prevent injection
- Query timeout limits
- Rate limiting on analytics endpoint
- Caching for common questions
- Fallback to pre-defined queries

## Example Queries

### Question 1: Vendor Total
**Input**: "What is the total amount of invoices from Nedstone for October 2025?"

**Generated SQL**:
```sql
SELECT SUM(total_amount) as total
FROM invoices
WHERE vendor_name = 'Nedstone'
  AND EXTRACT(MONTH FROM invoice_date) = 10
  AND EXTRACT(YEAR FROM invoice_date) = 2025;
```

**Answer**: "The total amount of invoices from Nedstone for October 2025 is 452.44 EUR"

### Question 2: Invoice Count
**Input**: "How many invoices are there from Atlassian?"

**Generated SQL**:
```sql
SELECT COUNT(*) as count
FROM invoices
WHERE vendor_name = 'Atlassian';
```

**Answer**: "There are 3 invoices from Atlassian"

### Question 3: Top Vendors
**Input**: "Top 5 vendors by total amount"

**Generated SQL**:
```sql
SELECT 
    vendor_name,
    SUM(total_amount) as total,
    COUNT(*) as invoice_count
FROM invoices
GROUP BY vendor_name
ORDER BY total DESC
LIMIT 5;
```

**Answer**: "Top 5 vendors: 1) Vendor A ($10,000), 2) Vendor B ($8,500), ..."

### Question 4: Risk Analysis
**Input**: "Which invoices have high risk?"

**Generated SQL**:
```sql
SELECT 
    invoice_number,
    vendor_name,
    total_amount,
    risk_level
FROM invoices
WHERE risk_level = 'high'
ORDER BY created_at DESC;
```

**Answer**: "Found 2 high-risk invoices: INV-001 from Vendor X ($5,000), INV-002 from Vendor Y ($3,500)"

## Security Considerations

### SQL Injection Prevention

```python
def validate_sql_query(sql: str) -> bool:
    """Validate generated SQL for safety"""
    
    # Disallow dangerous operations
    forbidden = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE']
    sql_upper = sql.upper()
    
    for keyword in forbidden:
        if keyword in sql_upper:
            raise SecurityError(f"Forbidden keyword: {keyword}")
    
    # Only allow SELECT queries
    if not sql_upper.strip().startswith('SELECT'):
        raise SecurityError("Only SELECT queries allowed")
    
    return True

def execute_query_safely(sql: str, connection):
    """Execute query with timeout and validation"""
    
    # Validate SQL
    validate_sql_query(sql)
    
    # Set query timeout
    connection.execute("SET statement_timeout = '5s'")
    
    # Execute with parameterization
    return connection.execute(text(sql))
```

### Rate Limiting

```python
@app.post("/analytics/chat")
@limiter.limit("10/minute")  # Max 10 questions per minute
async def chat_analytics(request: ChatRequest):
    ...
```

## Performance Optimization

### Query Caching

```python
# Cache common questions
CACHE_TTL = 3600  # 1 hour

@lru_cache(maxsize=100)
def get_cached_answer(question: str):
    return cache.get(f"analytics:{question}")
```

### Pre-computed Aggregates

```sql
-- Materialized view for vendor statistics
CREATE MATERIALIZED VIEW vendor_stats AS
SELECT 
    vendor_name,
    COUNT(*) as invoice_count,
    SUM(total_amount) as total_amount,
    AVG(total_amount) as avg_amount
FROM invoices
GROUP BY vendor_name;

-- Refresh periodically
REFRESH MATERIALIZED VIEW vendor_stats;
```

## Alternatives Considered

### 1. Fixed Dashboard/Reports
- **Pros**: Fast, predictable
- **Cons**: Inflexible, can't answer ad-hoc questions
- **Rejected**: Users need flexibility

### 2. GraphQL API
- **Pros**: Flexible queries, typed
- **Cons**: Requires learning GraphQL syntax
- **Rejected**: Still requires technical knowledge

### 3. Traditional BI Tool (Tableau, PowerBI)
- **Pros**: Rich visualizations, powerful
- **Cons**: Complex setup, expensive, steep learning curve
- **Rejected**: Too heavy for simple queries

### 4. Elasticsearch + Kibana
- **Pros**: Fast search, good for logs
- **Cons**: Not designed for financial analytics
- **Rejected**: PostgreSQL sufficient

## Future Enhancements

1. **Query Suggestions**: Suggest common questions
2. **Visualization**: Auto-generate charts for numeric results
3. **Query History**: Save and replay previous questions
4. **Multi-Table Joins**: Support complex queries across tables
5. **Streaming Results**: Real-time results for long queries
6. **Voice Input**: Accept voice questions

## Monitoring

Track metrics:
- Questions per day
- SQL generation success rate
- Query execution time
- Error rate
- Most common questions
- User satisfaction

## Related Decisions

- [ADR-003: PostgreSQL Database Choice](ADR-003-postgresql-database-choice.md)
- [ADR-002: Multi-Model LLM Strategy](ADR-002-multi-model-llm-strategy.md)

## References

- Text-to-SQL: https://arxiv.org/abs/2204.00498
- SQL Injection Prevention: https://owasp.org/www-community/attacks/SQL_Injection
- PostgreSQL Security: https://www.postgresql.org/docs/current/sql-syntax.html

---

**Review Date**: 2026-01-19 (Quarterly review)
