"""
Database management for North Sea Financial Bot
Handles SQLite database operations for users, transactions, and settings
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "north_sea_bot.db"):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    display_name TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings TEXT DEFAULT '{}'
                )
                """)
                
                # Transactions table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    group_id INTEGER,
                    date DATE,
                    currency TEXT,
                    amount REAL,
                    transaction_type TEXT,
                    category TEXT DEFAULT 'general',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
                """)
                
                # Exchange rates table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    date DATE,
                    currency TEXT,
                    rate REAL,
                    set_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (date, currency)
                )
                """)
                
                # Groups table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    group_id INTEGER PRIMARY KEY,
                    group_name TEXT,
                    welcome_message TEXT,
                    settings TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Fund management table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS funds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_type TEXT,
                    amount REAL,
                    currency TEXT,
                    group_id INTEGER,
                    updated_by INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                conn.commit()
                logger.info("✅ Database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection with proper locking"""
        async with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
    
    async def add_user(self, user_id: int, username: str = None, 
                       display_name: str = None, first_name: str = None, 
                       last_name: str = None) -> bool:
        """Add or update user information"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, username, display_name, first_name, last_name)
                VALUES (?, ?, ?, ?, ?)
                """, (user_id, username, display_name, first_name, last_name))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False
    
    async def add_transaction(self, user_id: int, group_id: int, 
                            transaction_date: date, currency: str, 
                            amount: float, transaction_type: str,
                            created_by: int = None, description: str = None) -> bool:
        """Add a financial transaction"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO transactions 
                (user_id, group_id, date, currency, amount, transaction_type, created_by, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, group_id, transaction_date, currency, amount, 
                      transaction_type, created_by or user_id, description))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return False
    
    async def get_user_transactions(self, user_id: int, group_id: int = None, month: int = None, 
                                  year: int = None) -> List[Dict]:
        """Get user transactions for specified period in specific group"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if month and year:
                    if group_id:
                        cursor.execute("""
                        SELECT * FROM transactions 
                        WHERE user_id = ? AND group_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
                        ORDER BY date DESC
                        """, (user_id, group_id, str(year), f"{month:02d}"))
                    else:
                        cursor.execute("""
                        SELECT * FROM transactions 
                        WHERE user_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
                        ORDER BY date DESC
                        """, (user_id, str(year), f"{month:02d}"))
                else:
                    # Current month
                    current_date = datetime.now()
                    if group_id:
                        cursor.execute("""
                        SELECT * FROM transactions 
                        WHERE user_id = ? AND group_id = ? AND strftime('%Y-%m', date) = ?
                        ORDER BY date DESC
                        """, (user_id, group_id, current_date.strftime('%Y-%m')))
                    else:
                        cursor.execute("""
                        SELECT * FROM transactions 
                        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
                        ORDER BY date DESC
                        """, (user_id, current_date.strftime('%Y-%m')))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user transactions: {e}")
            return []
    
    async def get_group_transactions(self, group_id: int, month: int = None, 
                                   year: int = None) -> List[Dict]:
        """Get group transactions for specified period"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if month and year:
                    cursor.execute("""
                    SELECT t.*, u.display_name, u.username 
                    FROM transactions t
                    LEFT JOIN users u ON t.user_id = u.user_id
                    WHERE t.group_id = ? AND strftime('%Y', t.date) = ? AND strftime('%m', t.date) = ?
                    ORDER BY t.date DESC
                    """, (group_id, str(year), f"{month:02d}"))
                else:
                    # Current month
                    current_date = datetime.now()
                    cursor.execute("""
                    SELECT t.*, u.display_name, u.username 
                    FROM transactions t
                    LEFT JOIN users u ON t.user_id = u.user_id
                    WHERE t.group_id = ? AND strftime('%Y-%m', t.date) = ?
                    ORDER BY t.date DESC
                    """, (group_id, current_date.strftime('%Y-%m')))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting group transactions: {e}")
            return []
    
    async def set_exchange_rate(self, rate_date: date, rate: float, set_by: int, currency: str = 'TW') -> bool:
        """Set exchange rate for a specific date and currency"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT OR REPLACE INTO exchange_rates (date, currency, rate, set_by)
                VALUES (?, ?, ?, ?)
                """, (rate_date, currency, rate, set_by))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting exchange rate: {e}")
            return False
    
    async def get_exchange_rate(self, rate_date: date = None, currency: str = 'TW') -> Optional[float]:
        """Get exchange rate for a specific date and currency"""
        try:
            if not rate_date:
                rate_date = date.today()
            
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT rate FROM exchange_rates 
                WHERE date <= ? AND currency = ?
                ORDER BY date DESC 
                LIMIT 1
                """, (rate_date, currency))
                
                result = cursor.fetchone()
                return result['rate'] if result else None
        except Exception as e:
            logger.error(f"Error getting exchange rate: {e}")
            return None
    
    async def delete_transaction(self, user_id: int, transaction_date: date, 
                               currency: str, amount: float) -> bool:
        """Delete a specific transaction"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                DELETE FROM transactions 
                WHERE user_id = ? AND date = ? AND currency = ? AND amount = ?
                """, (user_id, transaction_date, currency, amount))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting transaction: {e}")
            return False
    
    async def delete_monthly_transactions(self, user_id: int, month: int, 
                                        year: int, currency: str = None) -> bool:
        """Delete all transactions for a specific month"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if currency:
                    cursor.execute("""
                    DELETE FROM transactions 
                    WHERE user_id = ? AND strftime('%Y', date) = ? 
                    AND strftime('%m', date) = ? AND currency = ?
                    """, (user_id, str(year), f"{month:02d}", currency))
                else:
                    cursor.execute("""
                    DELETE FROM transactions 
                    WHERE user_id = ? AND strftime('%Y', date) = ? 
                    AND strftime('%m', date) = ?
                    """, (user_id, str(year), f"{month:02d}"))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting monthly transactions: {e}")
            return False
    
    async def update_fund(self, fund_type: str, amount: float, currency: str,
                         group_id: int, updated_by: int) -> bool:
        """Update fund amount"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT OR REPLACE INTO funds 
                (fund_type, amount, currency, group_id, updated_by)
                VALUES (?, ?, ?, ?, ?)
                """, (fund_type, amount, currency, group_id, updated_by))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating fund: {e}")
            return False
    
    async def get_fund_balance(self, fund_type: str, group_id: int) -> Dict[str, float]:
        """Get current fund balance"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT currency, amount FROM funds 
                WHERE fund_type = ? AND group_id = ?
                """, (fund_type, group_id))
                
                results = cursor.fetchall()
                return {row['currency']: row['amount'] for row in results}
        except Exception as e:
            logger.error(f"Error getting fund balance: {e}")
            return {}
    
    async def get_all_groups_transactions(self, month: int = None, year: int = None) -> List[Dict]:
        """Get transactions from all groups for fleet report"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if month and year:
                    cursor.execute("""
                    SELECT t.*, u.username, u.first_name 
                    FROM transactions t
                    LEFT JOIN users u ON t.user_id = u.user_id
                    WHERE strftime('%Y', t.date) = ? AND strftime('%m', t.date) = ?
                    ORDER BY t.date DESC, t.group_id
                    """, (str(year), f"{month:02d}"))
                else:
                    # Current month
                    current_date = datetime.now()
                    cursor.execute("""
                    SELECT t.*, u.username, u.first_name 
                    FROM transactions t
                    LEFT JOIN users u ON t.user_id = u.user_id
                    WHERE strftime('%Y-%m', t.date) = ?
                    ORDER BY t.date DESC, t.group_id
                    """, (current_date.strftime('%Y-%m'),))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all groups transactions: {e}")
            return []
    
    async def add_or_update_group(self, group_id: int, group_name: str) -> bool:
        """Add or update group information"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT OR REPLACE INTO groups 
                (group_id, group_name)
                VALUES (?, ?)
                """, (group_id, group_name))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding/updating group: {e}")
            return False
    
    async def get_group_name(self, group_id: int) -> Optional[str]:
        """Get group name by group_id"""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT group_name FROM groups WHERE group_id = ?
                """, (group_id,))
                result = cursor.fetchone()
                return result['group_name'] if result else None
        except Exception as e:
            logger.error(f"Error getting group name: {e}")
            return None
