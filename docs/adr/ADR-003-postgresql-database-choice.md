# ADR-003: PostgreSQL Database Choice

**Status**: Accepted  
**Date**: 2025-11-19  
**Decision Makers**: DevOps Team  
**Tags**: database, storage, analytics

## Context

Invoice processing system requires persistent storage for:
- **Extracted invoice data**: Structured financial information
- **Analytics queries**: Vendor aggregates, risk analysis
- **Audit trail**: Processing history and timestamps
- **Duplicate detection**: Prevent re-processing same invoices
- **Natural language queries**: SQL generation for analytics

Database requirements:
- ACID compliance for financial data
- JSON/JSONB support for flexible fields (line items, risk factors)
- Full-text search for vendor names
- Aggregate functions for analytics
- Strong indexing for performance
- SQL support for AI-generated queries

## Decision

Use **PostgreSQL 16** as the primary database.

### Key Features Used

**1. JSONB Storage**
```sql
line_items JSONB,          -- Flexible line item storage
risk_factors JSONB,         -- Dynamic risk factor data
```

**2. Unique Constraints**
```sql
UNIQUE(invoice_number, vendor_name)  -- Duplicate prevention
```

**3. Indexes for Performance**
```sql
CREATE INDEX idx_vendor_name ON invoices(vendor_name);
CREATE INDEX idx_invoice_date ON invoices(invoice_date);
CREATE INDEX idx_risk_level ON invoices(risk_level);
```

**4. UUID Primary Keys**
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
```

**5. Timestamp Tracking**
```sql
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

## Consequences

### Positive
✅ **ACID Compliance**: Financial data integrity guaranteed  
✅ **JSONB Support**: Flexible schema for varying invoice formats  
✅ **SQL Analytics**: Direct SQL queries for analytics agent  
✅ **Performance**: Excellent indexing and query optimization  
✅ **Mature Ecosystem**: Wide tooling and library support  
✅ **Open Source**: No licensing costs  
✅ **Scalability**: Handles millions of invoices  
✅ **Full-Text Search**: Fast vendor name searches  

### Negative
❌ **Operational Overhead**: Requires database management  
❌ **Backup Strategy**: Need automated backups  
❌ **Scaling Complexity**: Vertical scaling easier than horizontal  

### Mitigation
- Docker Compose for easy local setup
- Automated backup scripts
- Connection pooling for performance
- Read replicas for analytics queries (future)

## Schema Design

```sql
CREATE TABLE invoices (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Invoice Identifiers
    invoice_number VARCHAR(255) NOT NULL,
    invoice_date DATE,
    due_date DATE,
    
    -- Vendor Information
    vendor_name VARCHAR(255) NOT NULL,
    vendor_address TEXT,
    vendor_tax_id VARCHAR(100),
    vendor_email VARCHAR(255),
    vendor_phone VARCHAR(50),
    
    -- Customer Information
    customer_name VARCHAR(255),
    customer_address TEXT,
    customer_tax_id VARCHAR(100),
    
    -- Financial Data
    subtotal DECIMAL(15,2),
    tax_rate DECIMAL(5,2),
    tax_amount DECIMAL(15,2),
    discount_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    
    -- Payment Information
    payment_terms TEXT,
    payment_method TEXT,
    bank_account TEXT,
    
    -- Flexible Fields (JSONB)
    line_items JSONB,
    notes TEXT,
    purchase_order VARCHAR(255),
    
    -- Analysis Results
    risk_level VARCHAR(20),
    risk_factors JSONB,
    validation_status VARCHAR(50),
    analysis_report TEXT,
    
    -- Audit Trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_by VARCHAR(100),
    
    -- Constraints
    UNIQUE(invoice_number, vendor_name)
);

-- Performance Indexes
CREATE INDEX idx_vendor_name ON invoices(vendor_name);
CREATE INDEX idx_invoice_date ON invoices(invoice_date);
CREATE INDEX idx_risk_level ON invoices(risk_level);
CREATE INDEX idx_created_at ON invoices(created_at);
CREATE INDEX idx_currency ON invoices(currency);
```

## Query Patterns

### 1. Vendor Analytics
```sql
SELECT 
    vendor_name,
    currency,
    COUNT(*) as invoice_count,
    SUM(total_amount) as total_sum,
    AVG(total_amount) as average_amount,
    MIN(total_amount) as min_amount,
    MAX(total_amount) as max_amount
FROM invoices
WHERE vendor_name = 'Nedstone'
    AND EXTRACT(YEAR FROM invoice_date) = 2025
GROUP BY vendor_name, currency;
```

### 2. Risk Analysis
```sql
SELECT *
FROM invoices
WHERE risk_level IN ('high', 'medium')
ORDER BY created_at DESC
LIMIT 10;
```

### 3. Duplicate Detection
```sql
INSERT INTO invoices (...)
VALUES (...)
ON CONFLICT (invoice_number, vendor_name) 
DO UPDATE SET updated_at = CURRENT_TIMESTAMP;
```

## Alternatives Considered

### 1. MongoDB
- **Pros**: Flexible schema, JSON native
- **Cons**: No ACID guarantees, complex analytics
- **Rejected**: Financial data needs ACID

### 2. MySQL
- **Pros**: Popular, well-known
- **Cons**: Limited JSON support, weaker full-text search
- **Rejected**: PostgreSQL JSONB superior

### 3. SQLite
- **Pros**: Simple, no server needed
- **Cons**: No concurrent writes, limited scalability
- **Rejected**: Not suitable for production

### 4. Cloud Firestore
- **Pros**: Serverless, auto-scaling
- **Cons**: Complex queries expensive, vendor lock-in
- **Rejected**: SQL needed for analytics agent

## Performance Considerations

**Expected Load:**
- 1,000-10,000 invoices/day
- 100-500 analytics queries/day
- Average invoice: 2KB storage

**Optimization:**
- Connection pooling (10-20 connections)
- Prepared statements
- Index-only scans where possible
- JSONB GIN indexes for complex queries

## Backup Strategy

```bash
# Daily automated backups
pg_dump -Fc invoices > backup_$(date +%Y%m%d).dump

# Retention: 30 days
# Storage: S3/GCS with encryption
```

## Related Decisions

- [ADR-005: Natural Language Analytics](ADR-005-natural-language-analytics.md)

## References

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- JSONB Performance: https://www.postgresql.org/docs/current/datatype-json.html
- Indexing Best Practices: https://www.postgresql.org/docs/current/indexes.html

---

**Review Date**: 2026-01-19 (Quarterly review)
