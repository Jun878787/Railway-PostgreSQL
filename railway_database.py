"""
Railway PostgreSQL database management for North Sea Financial Bot
Handles PostgreSQL database operations for Railway deployment - Fixed version
"""

import os
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime, date
from typing import List, Dict, Optional
import asyncio
from decimal import Decimal

logger = logging.getLogger(__name__)

class RailwayDatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise Exception("DATABASE_URL environment variable not found")
        
        self._lock = asyncio.Lock()
        self.init_database()
        logger.info("✅ Railway PostgreSQL database initialized successfully")
    
    def get_connection(self):
        """Get database connection"""
        if not self.database_url:
            raise Exception("DATABASE_URL not available")
        
        # Parse the DATABASE_URL properly for Railway
        import urllib.parse as urlparse
        
        # Parse the URL
        url = urlparse.urlparse(self.database_url)
        
        return psycopg2.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=url.password,
            database=url.path[1:],  # Remove leading slash
            cursor_factory=psycopg2.extras.RealDictCursor,
            sslmode='require'  # Required for Railway PostgreSQL
        )
    
    def init_database(self):
        """Initialize database tables"""
        try:
            conn = self.get_connection()
            try:
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
                    user_id BIGINT NOT NULL,
                    group_id BIGINT NOT NULL,
                    date DATE NOT NULL,
                    currency VARCHAR(10) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    transaction_type VARCHAR(20) NOT NULL,
                    created_by BIGINT,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Exchange rates table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL,
                    currency VARCHAR(10) NOT NULL,
                    rate DECIMAL(10,4) NOT NULL,
                    set_by BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, currency)
                )
                """)
                
                # Fund balances table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS fund_balances (
                    id SERIAL PRIMARY KEY,
                    fund_type VARCHAR(50) NOT NULL,
                    currency VARCHAR(10) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL DEFAULT 0,
                    group_id BIGINT NOT NULL,
                    updated_by BIGINT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(fund_type, currency, group_id)
                )
                """)
                
                # Groups table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    group_id BIGINT PRIMARY KEY,
                    group_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                conn.commit()
                logger.info("✅ Railway PostgreSQL database initialized successfully")
                
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"❌ Error initializing Railway database: {e}")
            raise
    
    async def set_exchange_rate(self, rate_date: date, rate: float, set_by: int, currency: str = 'TW') -> bool:
        """Set exchange rate for a specific date and currency"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
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
                finally:
                    conn.close()
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
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                    SELECT rate FROM exchange_rates 
                    WHERE date <= %s AND currency = %s
                    ORDER BY date DESC 
                    LIMIT 1
                    """, (rate_date, currency))
                    result = cursor.fetchone()
                    return float(result['rate']) if result else None
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error getting exchange rate: {e}")
            return None
    
    async def add_user(self, user_id: int, username: str = None, 
                       display_name: str = None, first_name: str = None, 
                       last_name: str = None) -> bool:
        """Add or update user information"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
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
                finally:
                    conn.close()
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
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO transactions (user_id, group_id, date, currency, amount, transaction_type, created_by, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (user_id, group_id, transaction_date, currency, amount, transaction_type, created_by, description))
                    conn.commit()
                    return True
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            return False
    
    async def get_user_transactions(self, user_id: int, group_id: int = None, month: int = None, 
                                  year: int = None) -> List[Dict]:
        """Get user transactions for specified period in specific group"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
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
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error getting user transactions: {e}")
            return []
    
    async def get_group_transactions(self, group_id: int, month: int = None, 
                                   year: int = None) -> List[Dict]:
        """Get group transactions for specified period"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
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
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error getting group transactions: {e}")
            return []

    async def get_group_transactions_by_date(self, group_id: int, target_date: date) -> List[Dict]:
        """Get all transactions for a specific group on a specific date"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()

                    cursor.execute("""
                    SELECT t.*, u.username, u.display_name, u.first_name 
                    FROM transactions t
                    LEFT JOIN users u ON t.user_id = u.user_id
                    WHERE t.group_id = %s AND t.date = %s
                    ORDER BY t.created_at DESC
                    """, (group_id, target_date))

                    rows = cursor.fetchall()

                    return [dict(row) for row in rows]
                finally:
                    conn.close()

        except Exception as e:
            logger.error(f"Error getting group transactions by date: {e}")
            return []
    
    async def get_all_groups_transactions(self, month: int = None, year: int = None) -> List[Dict]:
        """Get transactions from all groups for fleet report"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    
                    query = "SELECT * FROM transactions"
                    params = []
                    
                    if month and year:
                        query += " WHERE EXTRACT(MONTH FROM date) = %s AND EXTRACT(YEAR FROM date) = %s"
                        params.extend([month, year])
                    
                    query += " ORDER BY date DESC"
                    
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    return [dict(row) for row in results] if results else []
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error getting all groups transactions: {e}")
            return []
    
    async def delete_transaction(self, user_id: int, transaction_date: date, 
                               currency: str, amount: float) -> bool:
        """Delete a specific transaction"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                    DELETE FROM transactions 
                    WHERE user_id = %s AND date = %s AND currency = %s AND amount = %s
                    """, (user_id, transaction_date, currency, amount))
                    conn.commit()
                    return cursor.rowcount > 0
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error deleting transaction: {e}")
            return False
    
    async def delete_monthly_transactions(self, user_id: int, month: int, 
                                        year: int, currency: str = None) -> bool:
        """Delete all transactions for a specific month"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    
                    query = """
                    DELETE FROM transactions 
                    WHERE user_id = %s AND EXTRACT(MONTH FROM date) = %s AND EXTRACT(YEAR FROM date) = %s
                    """
                    params = [user_id, month, year]
                    
                    if currency:
                        query += " AND currency = %s"
                        params.append(currency)
                    
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount > 0
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error deleting monthly transactions: {e}")
            return False
    
    async def update_fund(self, fund_type: str, amount: float, currency: str,
                         group_id: int, updated_by: int) -> bool:
        """Update fund amount"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO fund_balances (fund_type, currency, amount, group_id, updated_by)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (fund_type, currency, group_id) 
                    DO UPDATE SET 
                        amount = EXCLUDED.amount,
                        updated_by = EXCLUDED.updated_by,
                        updated_at = CURRENT_TIMESTAMP
                    """, (fund_type, currency, amount, group_id, updated_by))
                    conn.commit()
                    return True
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error updating fund: {e}")
            return False
    
    async def get_fund_balance(self, fund_type: str, group_id: int) -> Dict[str, float]:
        """Get current fund balance"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                    SELECT currency, amount FROM fund_balances 
                    WHERE fund_type = %s AND group_id = %s
                    """, (fund_type, group_id))
                    results = cursor.fetchall()
                    
                    balances = {}
                    for row in results:
                        balances[row['currency']] = float(row['amount'])
                    
                    return balances
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error getting fund balance: {e}")
            return {}
    
    async def add_or_update_group(self, group_id: int, group_name: str) -> bool:
        """Add or update group information"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO groups (group_id, group_name)
                    VALUES (%s, %s)
                    ON CONFLICT (group_id) 
                    DO UPDATE SET group_name = EXCLUDED.group_name
                    """, (group_id, group_name))
                    conn.commit()
                    return True
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error adding/updating group: {e}")
            return False
    
    async def get_group_name(self, group_id: int) -> Optional[str]:
        """Get group name by group_id"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT group_name FROM groups WHERE group_id = %s", (group_id,))
                    result = cursor.fetchone()
                    return result['group_name'] if result else None
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error getting group name: {e}")
            return None
    
    async def set_daily_exchange_rate(self, rate_date: date, currency_pair: str, rate: float, updated_by: int) -> bool:
        """Set exchange rate for a specific date and currency pair"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT INTO daily_exchange_rates (rate_date, currency_pair, rate, updated_by)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (rate_date, currency_pair) 
                    DO UPDATE SET rate = EXCLUDED.rate, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP
                    """, (rate_date, currency_pair, rate, updated_by))
                    conn.commit()
                    logger.info(f"Set {currency_pair} exchange rate for {rate_date}: {rate}")
                    return True
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error setting daily exchange rate: {e}")
            return False
    
    async def get_daily_exchange_rate(self, rate_date: date, currency_pair: str) -> Optional[float]:
        """Get exchange rate for a specific date and currency pair"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                    SELECT rate FROM daily_exchange_rates 
                    WHERE rate_date = %s AND currency_pair = %s
                    """, (rate_date, currency_pair))
                    result = cursor.fetchone()
                    return float(result['rate']) if result else None
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error getting daily exchange rate: {e}")
            return None
    
    async def get_latest_exchange_rates(self, rate_date: date = None) -> Dict[str, float]:
        """Get latest exchange rates for all currency pairs on a given date"""
        try:
            if not rate_date:
                from datetime import date as date_type
                rate_date = date_type.today()
            
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    # First try to get rates for the specific date
                    cursor.execute("""
                    SELECT currency, rate FROM exchange_rates 
                    WHERE date = %s
                    ORDER BY created_at DESC
                    """, (rate_date,))
                    results = cursor.fetchall()
                    
                    rates = {}
                    for row in results:
                        currency = row[0] if isinstance(row, (list, tuple)) else row['currency']
                        rate = float(row[1] if isinstance(row, (list, tuple)) else row['rate'])
                        # Map TW/CN to TWD/CNY for compatibility
                        if currency == 'TW':
                            rates['TWD'] = rate
                        elif currency == 'CN':
                            rates['CNY'] = rate
                        else:
                            rates[currency] = rate
                    
                    # If no rates found for specific date, get the most recent rates
                    if not rates:
                        cursor.execute("""
                        SELECT currency, rate FROM exchange_rates 
                        WHERE date <= %s
                        ORDER BY date DESC, created_at DESC
                        LIMIT 10
                        """, (rate_date,))
                        results = cursor.fetchall()
                        
                        for row in results:
                            currency = row[0] if isinstance(row, (list, tuple)) else row['currency']
                            rate = float(row[1] if isinstance(row, (list, tuple)) else row['rate'])
                            # Map TW/CN to TWD/CNY for compatibility
                            if currency == 'TW' and 'TWD' not in rates:
                                rates['TWD'] = rate
                            elif currency == 'CN' and 'CNY' not in rates:
                                rates['CNY'] = rate
                            
                    # Ensure we have both currencies with fallback to defaults
                    if 'TWD' not in rates:
                        rates['TWD'] = 30.0
                    if 'CNY' not in rates:
                        rates['CNY'] = 7.0
                    
                    return rates
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error getting latest exchange rates: {e}")
            return {'TWD': 30.0, 'CNY': 7.0}
    
    async def get_user_display_name(self, user_id: int) -> Optional[str]:
        """Get user display name by user_id"""
        try:
            async with self._lock:
                conn = self.get_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT display_name, first_name, username FROM users WHERE user_id = %s", (user_id,))
                    result = cursor.fetchone()
                    if result:
                        # Prefer display_name, fallback to first_name, then username
                        return result['display_name'] or result['first_name'] or result['username'] or f"User{user_id}"
                    return f"User{user_id}"
                finally:
                    conn.close()
        except Exception as e:
            logger.error(f"Error getting user display name: {e}")
            return f"User{user_id}"