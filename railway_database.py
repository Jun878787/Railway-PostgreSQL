"""
Railway PostgreSQL database management for North Sea Financial Bot
Handles PostgreSQL database operations for Railway deployment
"""

import os
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class RailwayDatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', '')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not found")
        
        self._lock = asyncio.Lock()
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            self.database_url,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    display_name VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Transactions table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    group_id BIGINT,
                    date DATE,
                    currency VARCHAR(10),
                    amount DECIMAL(15,2),
                    transaction_type VARCHAR(20),
                    category VARCHAR(100) DEFAULT 'general',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by BIGINT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
                """)
                
                # Exchange rates table (multi-currency support)
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    date DATE,
                    currency VARCHAR(10),
                    rate DECIMAL(10,4),
                    set_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (date, currency)
                )
                """)
                
                # Groups table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    group_id BIGINT PRIMARY KEY,
                    group_name VARCHAR(255),
                    welcome_message TEXT,
                    settings JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Fund management table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS funds (
                    id SERIAL PRIMARY KEY,
                    fund_type VARCHAR(50),
                    amount DECIMAL(15,2),
                    currency VARCHAR(10),
                    group_id BIGINT,
                    updated_by BIGINT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                conn.commit()
                logger.info("✅ Railway PostgreSQL database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Error initializing Railway database: {e}")
            raise
    
    async def set_exchange_rate(self, rate_date: date, rate: float, set_by: int, currency: str = 'TW') -> bool:
        """Set exchange rate for a specific date and currency"""
        try:
            async with self._lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO exchange_rates (date, currency, rate, set_by)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (date, currency) 
                    DO UPDATE SET rate = EXCLUDED.rate, set_by = EXCLUDED.set_by, created_at = CURRENT_TIMESTAMP
                    """, (rate_date, currency, rate, set_by))
                    conn.commit()
                    logger.info(f"✅ Exchange rate set successfully: {rate_date} {currency} = {rate}")
                    return True
        except Exception as e:
            logger.error(f"❌ Error setting exchange rate: {e}")
            logger.error(f"Details: rate_date={rate_date}, currency={currency}, rate={rate}, set_by={set_by}")
            return False
    
    async def get_exchange_rate(self, rate_date: date = None, currency: str = 'TW') -> Optional[float]:
        """Get exchange rate for a specific date and currency"""
        try:
            if not rate_date:
                rate_date = date.today()
            
            async with self._lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    SELECT rate FROM exchange_rates 
                    WHERE date <= %s AND currency = %s
                    ORDER BY date DESC 
                    LIMIT 1
                    """, (rate_date, currency))
                    
                    result = cursor.fetchone()
                    return float(result['rate']) if result else None
        except Exception as e:
            logger.error(f"Error getting exchange rate: {e}")
            return None
    
    async def add_user(self, user_id: int, username: str = None, 
                       display_name: str = None, first_name: str = None, 
                       last_name: str = None) -> bool:
        """Add or update user information"""
        try:
            async with self._lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO users (user_id, username, display_name, first_name, last_name)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        username = EXCLUDED.username,
                        display_name = EXCLUDED.display_name,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        updated_at = CURRENT_TIMESTAMP
                    """, (user_id, username, display_name, first_name, last_name))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    async def add_transaction(self, user_id: int, group_id: int, 
                            transaction_date: date, currency: str, 
                            amount: float, transaction_type: str,
                            created_by: int = None, description: str = None) -> bool:
        """Add a financial transaction"""
        try:
            async with self._lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO transactions (user_id, group_id, date, currency, amount, transaction_type, created_by, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, group_id, transaction_date, currency, amount, transaction_type, created_by, description))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return False
    
    async def get_user_transactions(self, user_id: int, group_id: int = None, month: int = None, 
                                  year: int = None) -> List[Dict]:
        """Get user transactions for specified period in specific group"""
        try:
            async with self._lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    query = "SELECT * FROM transactions WHERE user_id = %s"
                    params = [user_id]
                    
                    if group_id:
                        query += " AND group_id = %s"
                        params.append(group_id)
                    
                    if month and year:
                        query += " AND EXTRACT(MONTH FROM date) = %s AND EXTRACT(YEAR FROM date) = %s"
                        params.extend([month, year])
                    
                    query += " ORDER BY date DESC"
                    
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"Error getting user transactions: {e}")
            return []
    
    async def get_group_transactions(self, group_id: int, month: int = None, 
                                   year: int = None) -> List[Dict]:
        """Get group transactions for specified period"""
        try:
            async with self._lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    query = "SELECT * FROM transactions WHERE group_id = %s"
                    params = [group_id]
                    
                    if month and year:
                        query += " AND EXTRACT(MONTH FROM date) = %s AND EXTRACT(YEAR FROM date) = %s"
                        params.extend([month, year])
                    
                    query += " ORDER BY date DESC"
                    
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"Error getting group transactions: {e}")
            return []
    
    async def get_all_groups_transactions(self, month: int = None, year: int = None) -> List[Dict]:
        """Get transactions from all groups for fleet report"""
        try:
            async with self._lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    query = """
                    SELECT t.*, g.group_name 
                    FROM transactions t 
                    LEFT JOIN groups g ON t.group_id = g.group_id
                    WHERE 1=1
                    """
                    params = []
                    
                    if month and year:
                        query += " AND EXTRACT(MONTH FROM t.date) = %s AND EXTRACT(YEAR FROM t.date) = %s"
                        params.extend([month, year])
                    
                    query += " ORDER BY t.date DESC"
                    
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"Error getting all groups transactions: {e}")
            return []
    
    async def add_or_update_group(self, group_id: int, group_name: str) -> bool:
        """Add or update group information"""
        try:
            async with self._lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO groups (group_id, group_name)
                    VALUES (%s, %s)
                    ON CONFLICT (group_id) 
                    DO UPDATE SET group_name = EXCLUDED.group_name
                    """, (group_id, group_name))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error adding/updating group: {e}")
            return False
    
    async def get_group_name(self, group_id: int) -> Optional[str]:
        """Get group name by group_id"""
        try:
            async with self._lock:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT group_name FROM groups WHERE group_id = %s", (group_id,))
                    result = cursor.fetchone()
                    return result['group_name'] if result else None
        except Exception as e:
            logger.error(f"Error getting group name: {e}")
            return None