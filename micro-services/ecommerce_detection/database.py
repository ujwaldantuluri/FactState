"""
Database setup for advanced e-commerce detection.
This is a placeholder for future database integration.
"""

from typing import Optional
import sqlite3
import os

# Simple database setup for future integration
class DatabaseManager:
    def __init__(self, db_path: str = "ecommerce_analysis.db"):
        self.db_path = db_path
        # Ensure directory exists for file-based databases
        if db_path != ":memory:" and "/" in db_path:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                risk_score REAL NOT NULL,
                badge TEXT NOT NULL,
                reasons TEXT NOT NULL,
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                delivered BOOLEAN NOT NULL,
                order_hash TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_analysis(self, url: str, risk_score: float, badge: str, reasons: str):
        """Store analysis result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analysis_results (url, risk_score, badge, reasons)
            VALUES (?, ?, ?, ?)
        """, (url, risk_score, badge, reasons))
        conn.commit()
        conn.close()
    
    def store_feedback(self, url: str, delivered: bool, order_hash: Optional[str] = None):
        """Store user feedback."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feedback (url, delivered, order_hash)
            VALUES (?, ?, ?)
        """, (url, delivered, order_hash))
        conn.commit()
        conn.close()
    
    def get_feedback_summary(self, url: str) -> dict:
        """Get feedback summary for a URL."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT delivered, COUNT(*) 
            FROM feedback 
            WHERE url = ? 
            GROUP BY delivered
        """, (url,))
        
        results = cursor.fetchall()
        conn.close()
        
        delivered = sum(count for delivered, count in results if delivered)
        failed = sum(count for delivered, count in results if not delivered)
        
        return {
            "delivered": delivered,
            "failed": failed,
            "total": delivered + failed
        }

# Global database instance (can be replaced with proper DI later)
db = DatabaseManager()
