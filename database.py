"""
Invoice Database - SQLite with easy PostgreSQL migration
Stores processed invoices with extraction and analysis results
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class InvoiceDatabase:
    """Simple SQLite database for invoice storage and analytics"""
    
    def __init__(self, db_path: str = "invoices.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main invoices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT NOT NULL,
                invoice_date TEXT,
                vendor_name TEXT NOT NULL,
                vendor_tax_id TEXT,
                customer_name TEXT,
                customer_tax_id TEXT,
                subtotal REAL,
                tax_amount REAL,
                total_amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                document_type TEXT,
                model_used TEXT,
                
                -- Analysis results
                validation_status TEXT,
                risk_level TEXT,
                risk_score INTEGER,
                
                -- Full data as JSON
                extracted_data TEXT,  -- Full invoice data
                validation_results TEXT,  -- Validation details
                risk_analysis TEXT,  -- Risk analysis details
                summary TEXT,  -- Executive summary
                
                -- Metadata
                extraction_time_seconds REAL,
                analysis_time_seconds REAL,
                processed_at TEXT NOT NULL,
                
                -- Indexes for fast queries
                UNIQUE(invoice_number, vendor_name, invoice_date)
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vendor_name 
            ON invoices(vendor_name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_invoice_date 
            ON invoices(invoice_date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_risk_level 
            ON invoices(risk_level)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_processed_at 
            ON invoices(processed_at)
        """)
        
        conn.commit()
        conn.close()
    
    def save_invoice(self, 
                    extracted_data: Dict[str, Any],
                    validation: Dict[str, Any],
                    risk_analysis: Dict[str, Any],
                    summary: str,
                    model_used: str,
                    extraction_time: float,
                    analysis_time: float) -> int:
        """
        Save processed invoice to database
        
        Returns:
            invoice_id: ID of saved invoice
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO invoices (
                    invoice_number, invoice_date, vendor_name, vendor_tax_id,
                    customer_name, customer_tax_id, subtotal, tax_amount,
                    total_amount, currency, document_type, model_used,
                    validation_status, risk_level, risk_score,
                    extracted_data, validation_results, risk_analysis, summary,
                    extraction_time_seconds, analysis_time_seconds, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                extracted_data.get('invoice_number'),
                extracted_data.get('invoice_date'),
                extracted_data.get('vendor_name'),
                extracted_data.get('vendor_tax_id'),
                extracted_data.get('customer_name'),
                extracted_data.get('customer_tax_id'),
                extracted_data.get('subtotal'),
                extracted_data.get('tax_amount'),
                extracted_data.get('total_amount'),
                extracted_data.get('currency', 'USD'),
                'invoice',  # document_type
                model_used,
                validation.get('status', 'unknown'),
                risk_analysis.get('risk_level', 'unknown'),
                risk_analysis.get('risk_score', 0),
                json.dumps(extracted_data),
                json.dumps(validation),
                json.dumps(risk_analysis),
                summary,
                extraction_time,
                analysis_time,
                datetime.now().isoformat()
            ))
            
            invoice_id = cursor.lastrowid
            conn.commit()
            return invoice_id
            
        except sqlite3.IntegrityError:
            # Duplicate invoice - update instead
            cursor.execute("""
                UPDATE invoices SET
                    vendor_tax_id = ?, customer_name = ?, customer_tax_id = ?,
                    subtotal = ?, tax_amount = ?, total_amount = ?, currency = ?,
                    model_used = ?, validation_status = ?, risk_level = ?, risk_score = ?,
                    extracted_data = ?, validation_results = ?, risk_analysis = ?, summary = ?,
                    extraction_time_seconds = ?, analysis_time_seconds = ?, processed_at = ?
                WHERE invoice_number = ? AND vendor_name = ? AND invoice_date = ?
            """, (
                extracted_data.get('vendor_tax_id'),
                extracted_data.get('customer_name'),
                extracted_data.get('customer_tax_id'),
                extracted_data.get('subtotal'),
                extracted_data.get('tax_amount'),
                extracted_data.get('total_amount'),
                extracted_data.get('currency', 'USD'),
                model_used,
                validation.get('status', 'unknown'),
                risk_analysis.get('risk_level', 'unknown'),
                risk_analysis.get('risk_score', 0),
                json.dumps(extracted_data),
                json.dumps(validation),
                json.dumps(risk_analysis),
                summary,
                extraction_time,
                analysis_time,
                datetime.now().isoformat(),
                extracted_data.get('invoice_number'),
                extracted_data.get('vendor_name'),
                extracted_data.get('invoice_date')
            ))
            
            # Get the updated invoice ID
            cursor.execute("""
                SELECT id FROM invoices 
                WHERE invoice_number = ? AND vendor_name = ? AND invoice_date = ?
            """, (
                extracted_data.get('invoice_number'),
                extracted_data.get('vendor_name'),
                extracted_data.get('invoice_date')
            ))
            invoice_id = cursor.fetchone()[0]
            conn.commit()
            return invoice_id
            
        finally:
            conn.close()
    
    def get_by_vendor(self, vendor_name: str, 
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> List[Dict]:
        """Get all invoices from a specific vendor"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM invoices WHERE vendor_name LIKE ?"
        params = [f"%{vendor_name}%"]
        
        if start_date:
            query += " AND invoice_date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND invoice_date <= ?"
            params.append(end_date)
        
        query += " ORDER BY invoice_date DESC"
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def aggregate_by_vendor(self, vendor_name: str, 
                           year: Optional[int] = None) -> Dict[str, Any]:
        """Get aggregate statistics for a vendor"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                COUNT(*) as invoice_count,
                SUM(total_amount) as total_sum,
                AVG(total_amount) as average_amount,
                MIN(total_amount) as min_amount,
                MAX(total_amount) as max_amount,
                currency,
                MIN(invoice_date) as first_invoice,
                MAX(invoice_date) as last_invoice
            FROM invoices 
            WHERE vendor_name LIKE ?
        """
        params = [f"%{vendor_name}%"]
        
        if year:
            query += " AND strftime('%Y', invoice_date) = ?"
            params.append(str(year))
        
        query += " GROUP BY currency"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return {"error": f"No invoices found for vendor: {vendor_name}"}
        
        # Format results
        aggregates = []
        for row in results:
            aggregates.append({
                "currency": row[5] or "USD",
                "invoice_count": row[0],
                "total_sum": round(row[1], 2) if row[1] else 0,
                "average_amount": round(row[2], 2) if row[2] else 0,
                "min_amount": round(row[3], 2) if row[3] else 0,
                "max_amount": round(row[4], 2) if row[4] else 0,
                "first_invoice": row[6],
                "last_invoice": row[7]
            })
        
        return {
            "vendor_name": vendor_name,
            "year": year,
            "aggregates": aggregates
        }
    
    def get_high_risk_invoices(self, limit: int = 10) -> List[Dict]:
        """Get invoices with high risk"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM invoices 
            WHERE risk_level IN ('high', 'medium')
            ORDER BY risk_score DESC, processed_at DESC
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_invoices,
                COUNT(DISTINCT vendor_name) as unique_vendors,
                SUM(total_amount) as total_amount_all,
                AVG(total_amount) as avg_amount,
                COUNT(CASE WHEN risk_level = 'high' THEN 1 END) as high_risk_count,
                COUNT(CASE WHEN risk_level = 'medium' THEN 1 END) as medium_risk_count,
                COUNT(CASE WHEN risk_level = 'low' THEN 1 END) as low_risk_count
            FROM invoices
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "total_invoices": row[0],
            "unique_vendors": row[1],
            "total_amount": round(row[2], 2) if row[2] else 0,
            "average_amount": round(row[3], 2) if row[3] else 0,
            "risk_distribution": {
                "high": row[4],
                "medium": row[5],
                "low": row[6]
            }
        }


# Global database instance
db = InvoiceDatabase()
