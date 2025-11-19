"""
Multi-Agent Invoice Processing with CrewAI
Integrates Extract Thinker with intelligent validation and analysis agents
"""

from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import json
import asyncio
from datetime import datetime


# =================== TOOLS ===================

class InvoiceValidatorInput(BaseModel):
    """Input schema for Invoice Validator tool"""
    invoice_data: str = Field(..., description="JSON string with extracted invoice data")

class InvoiceValidatorTool(BaseTool):
    name: str = "Invoice Data Validator"
    description: str = "Validate extracted invoice data for completeness and accuracy. Checks for required fields, data types, and business logic."
    args_schema: type[BaseModel] = InvoiceValidatorInput
    
    def _run(self, invoice_data: str) -> str:
        """Execute the validation"""
        try:
            data = json.loads(invoice_data)
            issues = []
            warnings = []
            
            # Required fields check
            required_fields = ['invoice_number', 'total_amount', 'vendor_name']
            for field in required_fields:
                if not data.get(field):
                    issues.append(f"Missing required field: {field}")
            
            # Amount validation
            if data.get('total_amount'):
                try:
                    amount = float(str(data['total_amount']).replace(',', '').replace('$', ''))
                    if amount <= 0:
                        issues.append("Total amount must be positive")
                    if amount > 1000000:
                        warnings.append("Unusually high amount - please verify")
                except (ValueError, TypeError):
                    issues.append("Invalid total_amount format")
            
            # Date validation
            if data.get('invoice_date'):
                try:
                    invoice_date = datetime.fromisoformat(str(data['invoice_date']))
                    if invoice_date > datetime.now():
                        issues.append("Invoice date is in the future")
                except (ValueError, TypeError):
                    warnings.append("Could not parse invoice_date")
            
            # Line items validation
            if data.get('line_items'):
                if not isinstance(data['line_items'], list):
                    issues.append("line_items must be a list")
                elif len(data['line_items']) == 0:
                    warnings.append("No line items found")
            
            # Tax validation
            if data.get('tax_amount') and data.get('total_amount'):
                try:
                    tax = float(str(data['tax_amount']).replace(',', '').replace('$', ''))
                    total = float(str(data['total_amount']).replace(',', '').replace('$', ''))
                    if tax > total * 0.5:
                        warnings.append("Tax amount seems unusually high")
                except (ValueError, TypeError):
                    pass
            
            result = {
                "status": "valid" if len(issues) == 0 else "invalid",
                "issues": issues,
                "warnings": warnings,
                "fields_checked": len(data.keys()),
                "timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(result, indent=2)
            
        except json.JSONDecodeError:
            return json.dumps({
                "status": "error",
                "issues": ["Invalid JSON format"],
                "warnings": [],
                "fields_checked": 0
            })


class AnomalyDetectorInput(BaseModel):
    """Input schema for Anomaly Detector tool"""
    invoice_data: str = Field(..., description="JSON string with extracted invoice data")

class AnomalyDetectorTool(BaseTool):
    name: str = "Financial Anomaly Detector"
    description: str = "Analyze invoice data for anomalies, unusual patterns, or potential fraud indicators."
    args_schema: type[BaseModel] = AnomalyDetectorInput
    
    def _run(self, invoice_data: str) -> str:
        """Execute the anomaly detection"""
        try:
            data = json.loads(invoice_data)
            anomalies = []
            risk_score = 0
            
            # Check for duplicate invoice numbers (would need database in real scenario)
            if data.get('invoice_number'):
                # Placeholder - in production, check against database
                pass
            
            # Unusual amount patterns
            if data.get('total_amount'):
                try:
                    amount = float(str(data['total_amount']).replace(',', '').replace('$', ''))
                    
                    # Round number detection (potential fraud indicator)
                    if amount == round(amount, -2) and amount > 1000:
                        anomalies.append({
                            "type": "round_number",
                            "severity": "low",
                            "description": f"Amount is a round number: ${amount:,.2f}",
                            "recommendation": "Verify if this is legitimate"
                        })
                        risk_score += 1
                    
                    # Unusually high amount
                    if amount > 100000:
                        anomalies.append({
                            "type": "high_amount",
                            "severity": "medium",
                            "description": f"Unusually high amount: ${amount:,.2f}",
                            "recommendation": "Requires additional approval"
                        })
                        risk_score += 2
                    
                except (ValueError, TypeError):
                    pass
            
            # Missing critical information
            critical_fields = ['vendor_name', 'invoice_date', 'payment_terms']
            missing_critical = [f for f in critical_fields if not data.get(f)]
            if missing_critical:
                anomalies.append({
                    "type": "missing_data",
                    "severity": "medium",
                    "description": f"Missing critical fields: {', '.join(missing_critical)}",
                    "recommendation": "Request complete invoice from vendor"
                })
                risk_score += len(missing_critical)
            
            # Vendor name analysis
            if data.get('vendor_name'):
                vendor = str(data['vendor_name']).lower()
                suspicious_keywords = ['test', 'temp', 'dummy', 'sample']
                if any(keyword in vendor for keyword in suspicious_keywords):
                    anomalies.append({
                        "type": "suspicious_vendor",
                        "severity": "high",
                        "description": f"Vendor name contains suspicious keyword: {data['vendor_name']}",
                        "recommendation": "Verify vendor legitimacy"
                    })
                    risk_score += 5
            
            # Tax calculation verification
            if data.get('tax_amount') and data.get('subtotal'):
                try:
                    tax = float(str(data['tax_amount']).replace(',', '').replace('$', ''))
                    subtotal = float(str(data['subtotal']).replace(',', '').replace('$', ''))
                    
                    if subtotal > 0:
                        tax_rate = (tax / subtotal) * 100
                        # Typical tax rates are 5-15%
                        if tax_rate < 3 or tax_rate > 20:
                            anomalies.append({
                                "type": "unusual_tax_rate",
                                "severity": "low",
                                "description": f"Unusual tax rate: {tax_rate:.2f}%",
                                "recommendation": "Verify tax calculation"
                            })
                            risk_score += 1
                except (ValueError, TypeError, ZeroDivisionError):
                    pass
            
            # Risk assessment
            if risk_score == 0:
                risk_level = "low"
                recommendation = "Invoice appears normal - proceed with standard approval"
            elif risk_score <= 3:
                risk_level = "medium"
                recommendation = "Minor concerns detected - review before approval"
            else:
                risk_level = "high"
                recommendation = "Multiple red flags detected - requires thorough investigation"
            
            result = {
                "risk_level": risk_level,
                "risk_score": risk_score,
                "anomalies_found": len(anomalies),
                "anomalies": anomalies,
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(result, indent=2)
            
        except json.JSONDecodeError:
            return json.dumps({
                "risk_level": "unknown",
                "risk_score": 0,
                "anomalies_found": 0,
                "anomalies": [],
                "error": "Invalid JSON format"
            })


# =================== AGENTS ===================

def create_validator_agent() -> Agent:
    """Create data validation agent"""
    return Agent(
        role="Invoice Data Validator",
        goal="Ensure extracted invoice data is complete, accurate, and follows business rules",
        backstory="""You are an experienced financial auditor with 15 years of experience 
        in invoice processing and data validation. You have a keen eye for missing information, 
        data inconsistencies, and format errors. Your expertise helps prevent payment errors 
        and ensures compliance with company policies.""",
        tools=[InvoiceValidatorTool()],
        verbose=True,
        allow_delegation=False
    )


def create_analyst_agent() -> Agent:
    """Create financial analysis agent"""
    return Agent(
        role="Financial Fraud Analyst",
        goal="Detect anomalies, unusual patterns, and potential fraud indicators in invoice data",
        backstory="""You are a certified fraud examiner with expertise in financial forensics. 
        You've investigated hundreds of fraud cases and can spot red flags that others miss. 
        Your analytical skills help protect the company from fraudulent invoices, duplicate 
        payments, and vendor scams. You use statistical analysis and pattern recognition 
        to assess risk levels.""",
        tools=[AnomalyDetectorTool()],
        verbose=True,
        allow_delegation=False
    )


def create_reporter_agent() -> Agent:
    """Create reporting agent"""
    return Agent(
        role="Invoice Processing Reporter",
        goal="Create comprehensive, actionable reports summarizing validation and analysis results",
        backstory="""You are a business analyst specializing in financial reporting. 
        You excel at synthesizing complex information into clear, actionable insights. 
        Your reports help decision-makers quickly understand invoice status, risks, 
        and required actions. You prioritize clarity and actionability.""",
        verbose=True,
        allow_delegation=False
    )


# =================== CREW WORKFLOW ===================

async def process_invoice_with_crew(
    extracted_data: Dict[str, Any],
    confidence_scores: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Process extracted invoice data through multi-agent workflow
    
    Args:
        extracted_data: Data extracted by Extract Thinker
        confidence_scores: Confidence scores from extraction
    
    Returns:
        Comprehensive analysis with validation, anomaly detection, and recommendations
    """
    
    # Convert to JSON string for tools
    invoice_json = json.dumps(extracted_data, indent=2)
    
    # Create agents
    validator = create_validator_agent()
    analyst = create_analyst_agent()
    reporter = create_reporter_agent()
    
    # Define tasks
    validation_task = Task(
        description=f"""
        Validate the following extracted invoice data for completeness and accuracy:
        
        {invoice_json}
        
        Check for:
        1. Required fields (invoice_number, total_amount, vendor_name, invoice_date)
        2. Data type correctness
        3. Business logic (positive amounts, valid dates, etc.)
        4. Format consistency
        
        Provide a detailed validation report with any issues or warnings found.
        """,
        agent=validator,
        expected_output="Detailed validation report in JSON format with status, issues, and warnings"
    )
    
    analysis_task = Task(
        description=f"""
        Analyze the following invoice data for anomalies and fraud indicators:
        
        {invoice_json}
        
        Look for:
        1. Unusual amount patterns (round numbers, extremely high values)
        2. Suspicious vendor information
        3. Missing critical data
        4. Tax calculation irregularities
        5. Any red flags that warrant further investigation
        
        Provide a risk assessment with specific anomalies found and recommendations.
        """,
        agent=analyst,
        expected_output="Risk assessment report in JSON format with anomalies and risk level"
    )
    
    reporting_task = Task(
        description="""
        Based on the validation report and risk analysis, create a comprehensive summary report.
        
        Include:
        1. Overall status (APPROVED / NEEDS_REVIEW / REJECTED)
        2. Key findings from validation
        3. Risk assessment summary
        4. Specific action items required
        5. Priority level (LOW / MEDIUM / HIGH / CRITICAL)
        
        Make the report clear, concise, and actionable for decision-makers.
        """,
        agent=reporter,
        expected_output="Executive summary with clear status and action items",
        context=[validation_task, analysis_task]
    )
    
    # Create crew with sequential process
    crew = Crew(
        agents=[validator, analyst, reporter],
        tasks=[validation_task, analysis_task, reporting_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Execute workflow (run sync crew.kickoff in thread pool)
    result = await asyncio.to_thread(crew.kickoff)
    
    # Parse results from CrewAI 1.2.1 format
    # Get validation output
    try:
        validation_output = str(validation_task.output.raw) if hasattr(validation_task.output, 'raw') else str(validation_task.output)
        validation_result = json.loads(validation_output)
    except (json.JSONDecodeError, AttributeError):
        validation_result = {
            "status": "completed",
            "raw_output": validation_output if 'validation_output' in locals() else "Validation completed"
        }
    
    # Get analysis output
    try:
        analysis_output = str(analysis_task.output.raw) if hasattr(analysis_task.output, 'raw') else str(analysis_task.output)
        analysis_result = json.loads(analysis_output)
    except (json.JSONDecodeError, AttributeError):
        analysis_result = {
            "risk_level": "completed",
            "raw_output": analysis_output if 'analysis_output' in locals() else "Analysis completed"
        }
    
    # Get summary output
    try:
        summary_output = str(reporting_task.output.raw) if hasattr(reporting_task.output, 'raw') else str(reporting_task.output)
    except AttributeError:
        summary_output = str(result)
    
    # Combine results
    return {
        "validation": validation_result,
        "risk_analysis": analysis_result,
        "summary": summary_output,
        "confidence_scores": confidence_scores or {},
        "processed_at": datetime.now().isoformat(),
        "crew_execution_time": getattr(result, 'execution_time', None)
    }
