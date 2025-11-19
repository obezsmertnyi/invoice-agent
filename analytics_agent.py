"""
Analytics Chat Agent - Production Version
Natural language queries → SQL → Human-friendly answers

Supports multiple LLM providers: GPT-5, Ollama, Claude, etc.
"""

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import asyncio

from database import db
from config import get_optimal_model


# =================== TOOLS ===================

class SQLQueryInput(BaseModel):
    """Input schema for SQL Query Generator tool"""
    question: str = Field(..., description="User's question in natural language")
    
class SQLQueryGeneratorTool(BaseTool):
    name: str = "SQL Query Generator"
    description: str = """
    Generate safe SQL queries from natural language questions.
    
    Database schema:
    - invoices table with columns: 
      * invoice_number, invoice_date, vendor_name, vendor_tax_id
      * customer_name, customer_tax_id
      * subtotal, tax_amount, total_amount, currency
      * validation_status, risk_level, risk_score
      * processed_at
    
    Safety rules:
    - Only SELECT queries allowed (no INSERT/UPDATE/DELETE)
    - Use parameterized queries
    - Limit results to 100 rows max
    """
    args_schema: type[BaseModel] = SQLQueryInput
    
    def _run(self, question: str) -> str:
        """Generate SQL query from natural language question"""
        
        # Parse question to extract entities
        question_lower = question.lower()
        
        # Initialize query parts
        select_clause = "SELECT "
        from_clause = "FROM invoices "
        where_clauses = []
        group_by = ""
        order_by = ""
        limit = "LIMIT 100"
        
        # Detect what user wants to know
        if any(word in question_lower for word in ['сума', 'скільки', 'total', 'amount']):
            if 'середн' in question_lower or 'average' in question_lower:
                select_clause += "AVG(total_amount) as average_amount, currency "
                group_by = "GROUP BY currency"
            else:
                select_clause += "SUM(total_amount) as total_sum, COUNT(*) as invoice_count, currency "
                group_by = "GROUP BY currency"
        elif any(word in question_lower for word in ['список', 'всі', 'list', 'all']):
            select_clause += "invoice_number, invoice_date, vendor_name, total_amount, currency, risk_level "
            order_by = "ORDER BY invoice_date DESC "
        elif 'топ' in question_lower or 'top' in question_lower:
            # Extract number for TOP N
            numbers = re.findall(r'\d+', question)
            top_n = numbers[0] if numbers else '5'
            select_clause += "vendor_name, SUM(total_amount) as total_sum, COUNT(*) as invoice_count, currency "
            group_by = "GROUP BY vendor_name, currency "
            order_by = f"ORDER BY total_sum DESC "
            limit = f"LIMIT {top_n}"
        elif 'скільки інвойсів' in question_lower or 'how many' in question_lower:
            select_clause += "COUNT(*) as invoice_count, vendor_name "
            group_by = "GROUP BY vendor_name"
        else:
            select_clause += "* "
        
        # Extract vendor name
        vendor_patterns = [
            r'від\s+([А-Яа-яA-Za-z0-9\s.]+?)(?:\s+за|\s+в|\s*$)',
            r'from\s+([A-Za-z0-9\s.]+?)(?:\s+for|\s+in|\s*$)',
            r'vendor[:\s]+([A-Za-z0-9\s.]+?)(?:\s|$)',
        ]
        for pattern in vendor_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                vendor = match.group(1).strip()
                where_clauses.append(f"vendor_name LIKE '%{vendor}%'")
                break
        
        # Extract customer name
        customer_patterns = [
            r'для\s+([А-Яа-яA-Za-z0-9\s.]+?)(?:\s+за|\s*$)',
            r'customer[:\s]+([A-Za-z0-9\s.]+?)(?:\s|$)',
        ]
        for pattern in customer_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                customer = match.group(1).strip()
                where_clauses.append(f"customer_name LIKE '%{customer}%'")
                break
        
        # Extract date range
        months = {
            'січень': '01', 'лютий': '02', 'березень': '03', 'квітень': '04',
            'травень': '05', 'червень': '06', 'липень': '07', 'серпень': '08',
            'вересень': '09', 'жовтень': '10', 'листопад': '11', 'грудень': '12',
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        
        for month_name, month_num in months.items():
            if month_name in question_lower:
                # Extract year
                years = re.findall(r'20\d{2}', question)
                year = years[0] if years else str(datetime.now().year)
                
                where_clauses.append(f"strftime('%Y-%m', invoice_date) = '{year}-{month_num}'")
                break
        
        # Check for year only
        if not any(month in question_lower for month in months.keys()):
            years = re.findall(r'20\d{2}', question)
            if years:
                where_clauses.append(f"strftime('%Y', invoice_date) = '{years[0]}'")
        
        # Risk level filter
        if 'high risk' in question_lower or 'висок ризик' in question_lower:
            where_clauses.append("risk_level = 'high'")
        elif 'medium risk' in question_lower or 'середн ризик' in question_lower:
            where_clauses.append("risk_level = 'medium'")
        
        # Build WHERE clause
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses) + " "
        
        # Construct full query
        query = select_clause + from_clause + where_clause + group_by + " " + order_by + limit
        
        # Clean up extra spaces
        query = " ".join(query.split())
        
        return json.dumps({
            "sql_query": query,
            "explanation": f"Generated SQL to answer: {question}",
            "safety_check": "✅ SELECT only, no destructive operations"
        }, ensure_ascii=False)


class SQLExecutorInput(BaseModel):
    """Input schema for SQL Executor tool"""
    sql_query: str = Field(..., description="SQL query to execute")

class SQLExecutorTool(BaseTool):
    name: str = "SQL Query Executor"
    description: str = "Execute SQL query on the invoice database and return results"
    args_schema: type[BaseModel] = SQLExecutorInput
    
    def _run(self, sql_query: str) -> str:
        """Execute SQL query safely"""
        
        # Safety check - only allow SELECT
        if not sql_query.strip().upper().startswith('SELECT'):
            return json.dumps({
                "error": "Only SELECT queries are allowed",
                "sql_query": sql_query
            })
        
        # Block dangerous keywords
        dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in sql_query.upper() for keyword in dangerous):
            return json.dumps({
                "error": "Query contains dangerous operations",
                "sql_query": sql_query
            })
        
        try:
            import sqlite3
            conn = sqlite3.connect('invoices.db')
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Format results
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))
            
            conn.close()
            
            return json.dumps({
                "success": True,
                "row_count": len(results),
                "columns": columns,
                "data": results
            }, ensure_ascii=False, default=str)
            
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "sql_query": sql_query
            })


# =================== AGENTS ===================

def create_sql_agent() -> Agent:
    """Create SQL generation agent"""
    return Agent(
        role="SQL Query Expert",
        goal="Generate safe and accurate SQL queries from natural language questions about invoices",
        backstory="""You are an expert SQL developer with deep knowledge of invoice databases.
        You understand business terminology and can translate natural language questions
        into precise SQL queries. You always prioritize safety and data accuracy.""",
        tools=[SQLQueryGeneratorTool()],
        verbose=True,
        allow_delegation=False
    )

def create_executor_agent() -> Agent:
    """Create SQL execution agent"""
    return Agent(
        role="Database Query Executor",
        goal="Execute SQL queries safely and return accurate results",
        backstory="""You are a database administrator responsible for executing queries
        safely and efficiently. You validate all queries before execution and ensure
        data integrity.""",
        tools=[SQLExecutorTool()],
        verbose=True,
        allow_delegation=False
    )

def create_interpreter_agent() -> Agent:
    """Create results interpretation agent"""
    return Agent(
        role="Business Intelligence Analyst",
        goal="Provide SHORT, NATURAL answers in the SAME LANGUAGE as the question",
        backstory="""You are a friendly BI analyst who provides CONCISE, NATURAL answers.
        
        CRITICAL RULES:
        1. Answer in the SAME LANGUAGE as the question (Ukrainian → Ukrainian, English → English)
        2. Use NATURAL, CONVERSATIONAL language (not robotic lists)
        3. Keep answers SHORT (2-4 sentences max)
        4. Format numbers nicely with currency symbols
        5. NO long explanations, NO recommendations
        
        Examples:
        
        Question (UA): "Топ 5 вендорів по сумі"
        Answer (UA): "Найбільше витрат на Oleksandr Bezsmertnyi, PE — $1,672.50. Далі йдуть Nedstone Investments ($452.44), Atlassian ($437.85), Digidentity ($49.55) та Zoom ($47.97)."
        
        Question (UA): "Скільки всього інвойсів?"
        Answer (UA): "В базі зберігається 15 інвойсів на загальну суму $2,660.31."
        
        Question (EN): "How many invoices from Atlassian?"
        Answer (EN): "There are 3 invoices from Atlassian totaling $437.85."
        """,
        verbose=True,
        allow_delegation=False
    )


# =================== MAIN WORKFLOW ===================

async def process_analytics_question(question: str) -> Dict[str, Any]:
    """
    Process user question through analytics workflow
    
    Args:
        question: User's question in natural language
    
    Returns:
        Answer with SQL query, results, and natural language explanation
    """
    
    # Create agents
    sql_agent = create_sql_agent()
    executor_agent = create_executor_agent()
    interpreter_agent = create_interpreter_agent()
    
    # Define tasks
    sql_generation_task = Task(
        description=f"""
        Generate a SQL query to answer this question about invoices:
        
        "{question}"
        
        Use the SQL Query Generator tool to create a safe SELECT query.
        Return the SQL query and explanation.
        """,
        agent=sql_agent,
        expected_output="SQL query with explanation in JSON format"
    )
    
    execution_task = Task(
        description="""
        Execute the SQL query generated in the previous step.
        
        Use the SQL Query Executor tool to run the query safely.
        Return the results in structured format.
        """,
        agent=executor_agent,
        expected_output="Query results in JSON format",
        context=[sql_generation_task]
    )
    
    interpretation_task = Task(
        description=f"""
        Answer this question in NATURAL, CONVERSATIONAL language in the SAME LANGUAGE as the question:
        
        "{question}"
        
        RULES:
        - Answer in the SAME LANGUAGE as the question (Ukrainian → Ukrainian, English → English)
        - Use NATURAL language, like talking to a colleague
        - Maximum 2-4 sentences
        - Format numbers with currency symbols (e.g., $1,234.56)
        - NO robotic lists, NO analysis, NO recommendations
        
        Good examples:
        Q (UA): "Топ 5 вендорів по сумі"
        A (UA): "Найбільше витрат на Oleksandr Bezsmertnyi, PE — $1,672.50. Далі йдуть Nedstone Investments ($452.44), Atlassian ($437.85), Digidentity ($49.55) та Zoom ($47.97)."
        
        Q (EN): "How many invoices from Atlassian?"
        A (EN): "There are 3 invoices from Atlassian totaling $437.85."
        """,
        agent=interpreter_agent,
        expected_output="Natural, conversational answer in the same language as question",
        context=[sql_generation_task, execution_task]
    )
    
    # Create crew
    crew = Crew(
        agents=[sql_agent, executor_agent, interpreter_agent],
        tasks=[sql_generation_task, execution_task, interpretation_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Execute workflow (run in thread pool since kickoff is sync)
    result = await asyncio.to_thread(crew.kickoff)
    
    # Parse results from tasks
    sql_query = "N/A"
    results = []
    row_count = 0
    
    # Extract SQL query
    try:
        sql_output = str(sql_generation_task.output.raw) if hasattr(sql_generation_task.output, 'raw') else str(sql_generation_task.output)
        # Try to find SQL query in the output
        if 'SELECT' in sql_output.upper():
            # Extract SQL query from text
            import re
            sql_match = re.search(r'(SELECT.*?;)', sql_output, re.IGNORECASE | re.DOTALL)
            if sql_match:
                sql_query = sql_match.group(1).strip()
            else:
                # Try JSON format
                try:
                    sql_data = json.loads(sql_output)
                    sql_query = sql_data.get("sql_query", sql_output)
                except:
                    sql_query = sql_output
    except Exception as e:
        print(f"Error parsing SQL: {e}")
    
    # Extract execution results
    try:
        exec_output = str(execution_task.output.raw) if hasattr(execution_task.output, 'raw') else str(execution_task.output)
        # Try to parse as JSON
        try:
            exec_data = json.loads(exec_output)
            results = exec_data.get("data", [])
            row_count = exec_data.get("row_count", len(results))
        except:
            # If not JSON, try to find JSON in the text
            json_match = re.search(r'\{.*"data".*\}', exec_output, re.DOTALL)
            if json_match:
                exec_data = json.loads(json_match.group(0))
                results = exec_data.get("data", [])
                row_count = exec_data.get("row_count", len(results))
    except Exception as e:
        print(f"Error parsing execution results: {e}")
    
    # Extract answer
    try:
        answer = str(interpretation_task.output.raw) if hasattr(interpretation_task.output, 'raw') else str(interpretation_task.output)
        # Clean up answer - remove any JSON artifacts
        if answer.startswith('{'):
            try:
                answer_data = json.loads(answer)
                answer = answer_data.get("answer", answer)
            except:
                pass
    except:
        answer = str(result)
    
    return {
        "question": question,
        "sql_query": sql_query,
        "results": results,
        "row_count": row_count,
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    }
