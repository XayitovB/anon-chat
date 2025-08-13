import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager
from config import DATABASE_PATH
from security import SecurityManager, InputValidator

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        gender TEXT NOT NULL,
                        age_group TEXT NOT NULL,
                        rating REAL DEFAULT 0.0,
                        rating_count INTEGER DEFAULT 0,
                        is_active BOOLEAN DEFAULT 1,
                        is_premium BOOLEAN DEFAULT 0,
                        premium_until TIMESTAMP,
                        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Add premium columns if they don't exist (for existing databases)
                try:
                    cursor.execute('ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT 0')
                    cursor.execute('ALTER TABLE users ADD COLUMN premium_until TIMESTAMP')
                except sqlite3.OperationalError:
                    # Columns already exist, ignore error
                    pass
                
                # Chat sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user1_id INTEGER,
                        user2_id INTEGER,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ended_at TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        FOREIGN KEY (user1_id) REFERENCES users (user_id),
                        FOREIGN KEY (user2_id) REFERENCES users (user_id)
                    )
                ''')
                
                # Ratings table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ratings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rater_id INTEGER,
                        rated_id INTEGER,
                        session_id INTEGER,
                        rating INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (rater_id) REFERENCES users (user_id),
                        FOREIGN KEY (rated_id) REFERENCES users (user_id),
                        FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
                    )
                ''')
                
                # Waiting queue table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS waiting_queue (
                        user_id INTEGER PRIMARY KEY,
                        gender_filter TEXT,
                        age_filter TEXT,
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')
                
                # Reports table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reporter_id INTEGER,
                        reported_id INTEGER,
                        session_id INTEGER,
                        reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (reporter_id) REFERENCES users (user_id),
                        FOREIGN KEY (reported_id) REFERENCES users (user_id),
                        FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
                    )
                ''')
                
                # Referrals table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS referrals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        referrer_id INTEGER,
                        referred_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                        FOREIGN KEY (referred_id) REFERENCES users (user_id)
                    )
                ''')
                
                # Admins table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER UNIQUE,
                        added_by INTEGER,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (added_by) REFERENCES users (user_id)
                    )
                ''')
                
                # Mandatory channels table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS mandatory_channels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_username TEXT UNIQUE NOT NULL,
                        added_by INTEGER NOT NULL,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1,
                        FOREIGN KEY (added_by) REFERENCES users (user_id)
                    )
                ''')
                
                # Subscription plans table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS subscription_plans (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_key TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        stars INTEGER NOT NULL,
                        days INTEGER NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        is_special BOOLEAN DEFAULT 0,
                        sort_order INTEGER DEFAULT 0,
                        created_by INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (created_by) REFERENCES users (user_id)
                    )
                ''')
                
                # Friends table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS friends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        friend_id INTEGER NOT NULL,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (friend_id) REFERENCES users (user_id),
                        FOREIGN KEY (session_id) REFERENCES chat_sessions (id),
                        UNIQUE(user_id, friend_id)
                    )
                ''')
                
                conn.commit()
                logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
    
    def register_user(self, user_id, username, first_name, gender, age_group):
        """Register a new user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, gender, age_group)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username, first_name, gender, age_group))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error registering user: {e}")
            return False
    
    def update_user(self, user_id, username=None, first_name=None, gender=None, age_group=None):
        """Update user information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                update_fields = []
                params = []
                
                if username is not None:
                    update_fields.append("username = ?")
                    params.append(username)
                
                if first_name is not None:
                    update_fields.append("first_name = ?")
                    params.append(first_name)
                
                if gender is not None:
                    update_fields.append("gender = ?")
                    params.append(gender)
                
                if age_group is not None:
                    update_fields.append("age_group = ?")
                    params.append(age_group)
                
                if not update_fields:
                    return False  # No fields to update
                
                params.append(user_id)  # For WHERE clause
                
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = ?"
                cursor.execute(query, params)
                conn.commit()
                
                logging.info(f"User {user_id} updated: {', '.join(update_fields)}")
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error updating user: {e}")
            return False
    
    def get_user(self, user_id):
        """Get user information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"Error getting user: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user information by ID (alias for get_user)"""
        return self.get_user(user_id)
    
    def add_to_queue(self, user_id, gender_filter, age_filter):
        """Add user to waiting queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO waiting_queue 
                    (user_id, gender_filter, age_filter)
                    VALUES (?, ?, ?)
                ''', (user_id, gender_filter, age_filter))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding to queue: {e}")
            return False
    
    def find_partner(self, user_id, user_gender, user_age, gender_filter, age_filter):
        """Find a compatible partner from the queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First, log the current queue state with detailed info
                cursor.execute('''
                    SELECT q.user_id, u.gender, u.age_group, q.gender_filter, q.age_filter
                    FROM waiting_queue q
                    JOIN users u ON q.user_id = u.user_id
                ''')
                queue_users = cursor.fetchall()
                logging.info(f"Current queue has {len(queue_users)} users:")
                for user in queue_users:
                    logging.info(f"  User {user[0]}: gender={user[1]}, age={user[2]}, wants_gender={user[3]}, wants_age={user[4]}")
                
                logging.info(f"Looking for partner for user {user_id}: gender={user_gender}, age={user_age}, wants_gender={gender_filter}, wants_age={age_filter}")
                
                # Build the query - find users who want this user AND whom this user wants
                query = '''
                    SELECT q.user_id, u.gender, u.age_group, u.rating, u.rating_count
                    FROM waiting_queue q
                    JOIN users u ON q.user_id = u.user_id
                    WHERE q.user_id != ?
                '''
                params = [user_id]
                
                # Check if this user wants the partner's gender
                if gender_filter != "farqi_yoq":
                    query += " AND u.gender = ?"
                    params.append(gender_filter)
                
                # Check if partner wants this user's gender
                query += " AND (q.gender_filter = 'farqi_yoq' OR q.gender_filter = ?)"
                params.append(user_gender)
                
                # Check if this user wants the partner's age
                if age_filter != "farqi_yoq":
                    query += " AND u.age_group = ?"
                    params.append(age_filter)
                
                # Check if partner wants this user's age
                query += " AND (q.age_filter = 'farqi_yoq' OR q.age_filter = ?)"
                params.append(user_age)
                
                query += " ORDER BY q.joined_at ASC LIMIT 1"
                
                logging.info(f"Find partner query: {query}")
                logging.info(f"Query params: {params}")
                
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                if result:
                    logging.info(f"✅ Partner found: {result[0]} (gender={result[1]}, age={result[2]}) for user {user_id}")
                    # Remove partner from queue
                    cursor.execute('DELETE FROM waiting_queue WHERE user_id = ?', (result[0],))
                    conn.commit()
                    return result[0]
                else:
                    logging.info(f"❌ No compatible partner found for user {user_id}")
                    
                return None
        except Exception as e:
            logging.error(f"Error finding partner: {e}")
            return None
    
    def remove_from_queue(self, user_id):
        """Remove user from waiting queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM waiting_queue WHERE user_id = ?', (user_id,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error removing from queue: {e}")
            return False
    
    def clear_inactive_queue(self, hours=2):
        """Remove users from queue who have been waiting too long"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM waiting_queue 
                    WHERE datetime(joined_at, '+' || ? || ' hours') < datetime('now')
                """, (hours,))
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logging.error(f"Error clearing inactive queue: {e}")
            return 0
    
    def create_chat_session(self, user1_id, user2_id):
        """Create a new chat session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO chat_sessions (user1_id, user2_id)
                    VALUES (?, ?)
                ''', (user1_id, user2_id))
                session_id = cursor.lastrowid
                conn.commit()
                return session_id
        except Exception as e:
            logging.error(f"Error creating chat session: {e}")
            return None
    
    def end_chat_session(self, session_id):
        """End a chat session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE chat_sessions 
                    SET ended_at = CURRENT_TIMESTAMP, status = 'ended'
                    WHERE id = ?
                ''', (session_id,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error ending chat session: {e}")
            return False
    
    def add_rating(self, rater_id, rated_id, session_id, rating):
        """Add a rating for a user with validation"""
        try:
            # Input validation
            rating = InputValidator.validate_rating(str(rating))
            if not InputValidator.validate_user_id(rater_id) or not InputValidator.validate_user_id(rated_id):
                return False
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if rating already exists for this session and rater
                cursor.execute(
                    "SELECT id FROM ratings WHERE rater_id = ? AND session_id = ?",
                    (rater_id, session_id)
                )
                if cursor.fetchone():
                    return False  # Already rated
                
                # Add rating record
                cursor.execute('''
                    INSERT INTO ratings (rater_id, rated_id, session_id, rating)
                    VALUES (?, ?, ?, ?)
                ''', (rater_id, rated_id, session_id, rating))
                
                # Update user's average rating
                cursor.execute('''
                    UPDATE users 
                    SET rating = (
                        SELECT AVG(rating) FROM ratings WHERE rated_id = ?
                    ),
                    rating_count = (
                        SELECT COUNT(*) FROM ratings WHERE rated_id = ?
                    )
                    WHERE user_id = ?
                ''', (rated_id, rated_id, rated_id))
                
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding rating: {e}")
            return False
    
    def add_report(self, reporter_id, reported_id, session_id, reason):
        """Add a report"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reports (reporter_id, reported_id, session_id, reason)
                    VALUES (?, ?, ?, ?)
                ''', (reporter_id, reported_id, session_id, reason))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error adding report: {e}")
            return False
    
    # ADMIN METHODS
    def get_all_users(self, page=1, per_page=10):
        """Get paginated list of all users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total count
                cursor.execute("SELECT COUNT(*) FROM users")
                total_count = cursor.fetchone()[0]
                
                # Get paginated users
                offset = (page - 1) * per_page
                cursor.execute('''
                    SELECT user_id, username, first_name, gender, age_group, 
                           rating, rating_count, is_active, is_premium, premium_until, registered_at
                    FROM users 
                    ORDER BY registered_at DESC 
                    LIMIT ? OFFSET ?
                ''', (per_page, offset))
                
                users = cursor.fetchall()
                total_pages = (total_count + per_page - 1) // per_page
                
                return {
                    'users': users,
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_count': total_count
                }
        except Exception as e:
            logging.error(f"Error getting all users: {e}")
            return None
    
    def get_active_users(self):
        """Get currently active users (in chat or queue)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users in active chats
                cursor.execute('''
                    SELECT DISTINCT u.user_id, u.username, u.first_name, 'in_chat' as status
                    FROM users u
                    JOIN chat_sessions cs ON (u.user_id = cs.user1_id OR u.user_id = cs.user2_id)
                    WHERE cs.status = 'active'
                ''')
                active_chat_users = cursor.fetchall()
                
                # Users in waiting queue
                cursor.execute('''
                    SELECT u.user_id, u.username, u.first_name, 'in_queue' as status
                    FROM users u
                    JOIN waiting_queue wq ON u.user_id = wq.user_id
                ''')
                queue_users = cursor.fetchall()
                
                return {
                    'chat_users': active_chat_users,
                    'queue_users': queue_users
                }
        except Exception as e:
            logging.error(f"Error getting active users: {e}")
            return None
    
    def search_user(self, query):
        """Search users by ID, username, or first name"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Try to search by user ID first (if query is numeric)
                if query.isdigit():
                    cursor.execute('SELECT * FROM users WHERE user_id = ?', (int(query),))
                    result = cursor.fetchone()
                    if result:
                        return [result]
                
                # Search by username or first name
                cursor.execute('''
                    SELECT * FROM users 
                    WHERE username LIKE ? OR first_name LIKE ?
                    ORDER BY registered_at DESC
                    LIMIT 20
                ''', (f'%{query}%', f'%{query}%'))
                
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error searching user: {e}")
            return []
    
    def get_banned_users(self):
        """Get list of banned users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, username, first_name, registered_at
                    FROM users 
                    WHERE is_active = 0
                    ORDER BY registered_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting banned users: {e}")
            return []
    
    def get_all_reports(self):
        """Get all reports with user details"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT r.id, r.reporter_id, u1.first_name as reporter_name,
                           r.reported_id, u2.first_name as reported_name,
                           r.reason, r.created_at
                    FROM reports r
                    LEFT JOIN users u1 ON r.reporter_id = u1.user_id
                    LEFT JOIN users u2 ON r.reported_id = u2.user_id
                    ORDER BY r.created_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting all reports: {e}")
            return []
    
    def broadcast_to_users(self, user_filter=None):
        """Get user IDs for broadcasting based on filter"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT user_id FROM users WHERE is_active = 1"
                params = []
                
                if user_filter:
                    if user_filter.get('gender'):
                        query += " AND gender = ?"
                        params.append(user_filter['gender'])
                    
                    if user_filter.get('age_group'):
                        query += " AND age_group = ?"
                        params.append(user_filter['age_group'])
                
                cursor.execute(query, params)
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting broadcast users: {e}")
            return []
    
    def ban_user(self, user_id):
        """Ban a user by setting is_active to False"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (user_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error banning user: {e}")
            return False
    
    def unban_user(self, user_id):
        """Unban a user by setting is_active to True"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET is_active = 1 WHERE user_id = ?', (user_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error unbanning user: {e}")
            return False
    
    def is_user_banned(self, user_id):
        """Check if a user is banned"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT is_active FROM users WHERE user_id = ?', (user_id,))
                result = cursor.fetchone()
                return result and result[0] == 0
        except Exception as e:
            logging.error(f"Error checking if user is banned: {e}")
            return False
    
    def get_stats(self):
        """Get bot statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total users
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]
                
                # Active users
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
                active_users = cursor.fetchone()[0]
                
                # Banned users
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 0")
                banned_users = cursor.fetchone()[0]
                
                # Total chats
                cursor.execute("SELECT COUNT(*) FROM chat_sessions")
                total_chats = cursor.fetchone()[0]
                
                # Active chats
                cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE status = 'active'")
                active_chats = cursor.fetchone()[0]
                
                # Users in queue
                cursor.execute("SELECT COUNT(*) FROM waiting_queue")
                users_in_queue = cursor.fetchone()[0]
                
                # Total reports
                cursor.execute("SELECT COUNT(*) FROM reports")
                total_reports = cursor.fetchone()[0]
                
                return {
                    'total_users': total_users,
                    'active_users': active_users,
                    'banned_users': banned_users,
                    'total_chats': total_chats,
                    'active_chats': active_chats,
                    'users_in_queue': users_in_queue,
                    'total_reports': total_reports
                }
        except Exception as e:
            logging.error(f"Error getting stats: {e}")
            return None
    
    # REFERRAL SYSTEM METHODS
    def add_referral(self, referrer_id, referred_id):
        """Add a referral record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if referral already exists
                cursor.execute(
                    "SELECT id FROM referrals WHERE referrer_id = ? AND referred_id = ?",
                    (referrer_id, referred_id)
                )
                if cursor.fetchone():
                    return False  # Referral already exists
                
                # Don't allow self-referral
                if referrer_id == referred_id:
                    return False
                
                # Add referral record
                cursor.execute('''
                    INSERT INTO referrals (referrer_id, referred_id)
                    VALUES (?, ?)
                ''', (referrer_id, referred_id))
                conn.commit()
                
                logging.info(f"Referral added: {referrer_id} referred {referred_id}")
                return True
        except Exception as e:
            logging.error(f"Error adding referral: {e}")
            return False
    
    def get_referral_count(self, user_id):
        """Get the number of active referrals for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND is_active = 1",
                    (user_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logging.error(f"Error getting referral count: {e}")
            return 0
    
    def get_referrals_by_user(self, user_id):
        """Get all referrals made by a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT r.id, r.referred_id, u.first_name, u.username, r.created_at, r.is_active
                    FROM referrals r
                    LEFT JOIN users u ON r.referred_id = u.user_id
                    WHERE r.referrer_id = ?
                    ORDER BY r.created_at DESC
                ''', (user_id,))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting referrals by user: {e}")
            return []
    
    def check_referral_exists(self, referrer_id, referred_id):
        """Check if a referral record already exists"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM referrals WHERE referrer_id = ? AND referred_id = ?",
                    (referrer_id, referred_id)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking referral exists: {e}")
            return False
    
    def get_referrer(self, referred_id):
        """Get the referrer of a user (if any)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT referrer_id FROM referrals WHERE referred_id = ? AND is_active = 1",
                    (referred_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logging.error(f"Error getting referrer: {e}")
            return None
    
    def deactivate_referral(self, referrer_id, referred_id):
        """Deactivate a referral (e.g., if referred user gets banned)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE referrals SET is_active = 0 WHERE referrer_id = ? AND referred_id = ?",
                    (referrer_id, referred_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error deactivating referral: {e}")
            return False
    
    # PREMIUM SUBSCRIPTION METHODS
    def add_premium_days(self, user_id, days):
        """Add premium days to user account"""
        try:
            from datetime import datetime, timedelta
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current premium status
                cursor.execute(
                    "SELECT premium_until FROM users WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                current_premium_until = result[0]
                now = datetime.now()
                
                # Calculate new premium end date
                if current_premium_until:
                    try:
                        current_end = datetime.fromisoformat(current_premium_until.replace('Z', '+00:00'))
                        if current_end > now:
                            # Extend existing premium
                            new_end = current_end + timedelta(days=days)
                        else:
                            # Premium expired, start from now
                            new_end = now + timedelta(days=days)
                    except (ValueError, AttributeError):
                        # Invalid date format, start from now
                        new_end = now + timedelta(days=days)
                else:
                    # No existing premium
                    new_end = now + timedelta(days=days)
                
                # Update premium status
                cursor.execute('''
                    UPDATE users 
                    SET is_premium = 1, premium_until = ?
                    WHERE user_id = ?
                ''', (new_end.isoformat(), user_id))
                
                conn.commit()
                
                logging.info(f"Added {days} premium days to user {user_id}. Premium until: {new_end}")
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error adding premium days: {e}")
            return False
    
    def is_user_premium(self, user_id):
        """Check if user has active premium subscription"""
        try:
            from datetime import datetime
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT is_premium, premium_until FROM users WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                is_premium, premium_until = result
                
                if not is_premium or not premium_until:
                    return False
                
                try:
                    end_date = datetime.fromisoformat(premium_until.replace('Z', '+00:00'))
                    now = datetime.now()
                    
                    if end_date > now:
                        return True
                    else:
                        # Premium expired, update database
                        cursor.execute(
                            "UPDATE users SET is_premium = 0 WHERE user_id = ?",
                            (user_id,)
                        )
                        conn.commit()
                        return False
                except (ValueError, AttributeError):
                    return False
                
        except Exception as e:
            logging.error(f"Error checking premium status: {e}")
            return False
    
    def get_premium_info(self, user_id):
        """Get premium subscription info for user"""
        try:
            from datetime import datetime
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT is_premium, premium_until FROM users WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                is_premium, premium_until = result
                
                if not is_premium or not premium_until:
                    return {'is_premium': False, 'days_left': 0, 'expires_at': None}
                
                try:
                    end_date = datetime.fromisoformat(premium_until.replace('Z', '+00:00'))
                    now = datetime.now()
                    
                    if end_date > now:
                        days_left = (end_date - now).days + 1
                        return {
                            'is_premium': True,
                            'days_left': days_left,
                            'expires_at': end_date
                        }
                    else:
                        # Premium expired, update database
                        cursor.execute(
                            "UPDATE users SET is_premium = 0 WHERE user_id = ?",
                            (user_id,)
                        )
                        conn.commit()
                        return {'is_premium': False, 'days_left': 0, 'expires_at': None}
                except (ValueError, AttributeError):
                    return {'is_premium': False, 'days_left': 0, 'expires_at': None}
                
        except Exception as e:
            logging.error(f"Error getting premium info: {e}")
            return None
    
    def get_user_by_username(self, username):
        """Get user information by username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,))
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"Error getting user by username: {e}")
            return None
    
    def remove_premium(self, user_id):
        """Remove premium status from user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if user exists and has premium
                cursor.execute(
                    "SELECT is_premium FROM users WHERE user_id = ?",
                    (user_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return False, "User not found"
                
                if not result[0]:
                    return False, "User doesn't have premium"
                
                # Remove premium status
                cursor.execute(
                    "UPDATE users SET is_premium = 0, premium_until = NULL WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                
                logging.info(f"Premium removed from user {user_id}")
                return True, "Premium removed successfully"
                
        except Exception as e:
            logging.error(f"Error removing premium: {e}")
            return False, f"Database error: {str(e)}"
    
    def get_all_premium_users(self, page=1, per_page=20):
        """Get all premium users with pagination"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count total premium users
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
                total_count = cursor.fetchone()[0]
                
                if total_count == 0:
                    return {
                        'users': [],
                        'total_count': 0,
                        'total_pages': 0,
                        'current_page': page
                    }
                
                # Calculate pagination
                total_pages = (total_count + per_page - 1) // per_page
                offset = (page - 1) * per_page
                
                # Get premium users
                cursor.execute('''
                    SELECT user_id, username, first_name, gender, age_group, 
                           rating, rating_count, is_active, is_premium, 
                           premium_until, registered_at
                    FROM users 
                    WHERE is_premium = 1
                    ORDER BY premium_until DESC, registered_at DESC
                    LIMIT ? OFFSET ?
                ''', (per_page, offset))
                
                users = cursor.fetchall()
                
                return {
                    'users': users,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'current_page': page
                }
                
        except Exception as e:
            logging.error(f"Error getting premium users: {e}")
            return {
                'users': [],
                'total_count': 0,
                'total_pages': 0,
                'current_page': 1
            }
    
    def cleanup_expired_premium(self):
        """Clean up expired premium subscriptions"""
        try:
            from datetime import datetime
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                now = datetime.now().isoformat()
                cursor.execute(
                    "UPDATE users SET is_premium = 0 WHERE is_premium = 1 AND premium_until < ?",
                    (now,)
                )
                
                expired_count = cursor.rowcount
                conn.commit()
                
                if expired_count > 0:
                    logging.info(f"Cleaned up {expired_count} expired premium subscriptions")
                
            return expired_count
        except Exception as e:
            logging.error(f"Error cleaning up expired premium: {e}")
            return 0
    
    # SUBSCRIPTION PLANS MANAGEMENT METHODS
    def create_subscription_plan(self, plan_key, title, description, stars, days, is_special=False, sort_order=0, created_by=None):
        """Create a new subscription plan"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if plan_key already exists
                cursor.execute("SELECT id FROM subscription_plans WHERE plan_key = ?", (plan_key,))
                if cursor.fetchone():
                    return False, "Plan key already exists"
                
                # Insert new plan
                cursor.execute('''
                    INSERT INTO subscription_plans 
                    (plan_key, title, description, stars, days, is_special, sort_order, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (plan_key, title, description, stars, days, is_special, sort_order, created_by))
                
                plan_id = cursor.lastrowid
                conn.commit()
                
                logging.info(f"Subscription plan created: {plan_key} (ID: {plan_id}) by {created_by}")
                return True, plan_id
                
        except Exception as e:
            logging.error(f"Error creating subscription plan: {e}")
            return False, f"Database error: {str(e)}"
    
    def get_all_subscription_plans(self, include_inactive=False):
        """Get all subscription plans"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, plan_key, title, description, stars, days, 
                           is_active, is_special, sort_order, created_by, created_at, updated_at
                    FROM subscription_plans
                '''
                
                if not include_inactive:
                    query += " WHERE is_active = 1"
                
                query += " ORDER BY sort_order ASC, created_at ASC"
                
                cursor.execute(query)
                return cursor.fetchall()
                
        except Exception as e:
            logging.error(f"Error getting subscription plans: {e}")
            return []
    
    def get_subscription_plan_by_id(self, plan_id):
        """Get a subscription plan by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, plan_key, title, description, stars, days, 
                           is_active, is_special, sort_order, created_by, created_at, updated_at
                    FROM subscription_plans
                    WHERE id = ?
                ''', (plan_id,))
                
                return cursor.fetchone()
                
        except Exception as e:
            logging.error(f"Error getting subscription plan by ID: {e}")
            return None
    
    def get_subscription_plan_by_key(self, plan_key):
        """Get a subscription plan by key"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, plan_key, title, description, stars, days, 
                           is_active, is_special, sort_order, created_by, created_at, updated_at
                    FROM subscription_plans
                    WHERE plan_key = ?
                ''', (plan_key,))
                
                return cursor.fetchone()
                
        except Exception as e:
            logging.error(f"Error getting subscription plan by key: {e}")
            return None
    
    def update_subscription_plan(self, plan_id, title=None, description=None, stars=None, days=None, is_special=None, sort_order=None):
        """Update a subscription plan"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                update_fields = []
                params = []
                
                if title is not None:
                    update_fields.append("title = ?")
                    params.append(title)
                
                if description is not None:
                    update_fields.append("description = ?")
                    params.append(description)
                
                if stars is not None:
                    update_fields.append("stars = ?")
                    params.append(stars)
                
                if days is not None:
                    update_fields.append("days = ?")
                    params.append(days)
                
                if is_special is not None:
                    update_fields.append("is_special = ?")
                    params.append(is_special)
                
                if sort_order is not None:
                    update_fields.append("sort_order = ?")
                    params.append(sort_order)
                
                if not update_fields:
                    return False, "No fields to update"
                
                # Add updated_at
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.append(plan_id)  # For WHERE clause
                
                query = f"UPDATE subscription_plans SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                
                if cursor.rowcount > 0:
                    logging.info(f"Subscription plan {plan_id} updated: {', '.join(update_fields)}")
                    return True, "Plan updated successfully"
                else:
                    return False, "Plan not found"
                
        except Exception as e:
            logging.error(f"Error updating subscription plan: {e}")
            return False, f"Database error: {str(e)}"
    
    def toggle_subscription_plan_active(self, plan_id):
        """Toggle active status of a subscription plan"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current active status
                cursor.execute("SELECT is_active FROM subscription_plans WHERE id = ?", (plan_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False, "Plan not found"
                
                new_status = 1 if result[0] == 0 else 0
                
                # Update active status
                cursor.execute('''
                    UPDATE subscription_plans 
                    SET is_active = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (new_status, plan_id))
                conn.commit()
                
                status_text = "activated" if new_status else "deactivated"
                logging.info(f"Subscription plan {plan_id} {status_text}")
                return True, f"Plan {status_text} successfully"
                
        except Exception as e:
            logging.error(f"Error toggling subscription plan active status: {e}")
            return False, f"Database error: {str(e)}"
    
    def delete_subscription_plan(self, plan_id):
        """Delete a subscription plan (permanent deletion)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if plan exists
                cursor.execute("SELECT plan_key FROM subscription_plans WHERE id = ?", (plan_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False, "Plan not found"
                
                plan_key = result[0]
                
                # Delete the plan
                cursor.execute("DELETE FROM subscription_plans WHERE id = ?", (plan_id,))
                conn.commit()
                
                logging.info(f"Subscription plan {plan_id} ({plan_key}) deleted permanently")
                return True, "Plan deleted successfully"
                
        except Exception as e:
            logging.error(f"Error deleting subscription plan: {e}")
            return False, f"Database error: {str(e)}"
    
    def get_active_subscription_plans_for_purchase(self):
        """Get active subscription plans formatted for purchase display"""
        try:
            plans = self.get_all_subscription_plans(include_inactive=False)
            
            # Convert to dictionary format similar to the original pricing_options
            pricing_options = {}
            for plan in plans:
                plan_id, plan_key, title, description, stars, days, is_active, is_special, sort_order, created_by, created_at, updated_at = plan
                
                pricing_options[plan_key] = {
                    'title': title,
                    'stars': stars,
                    'days': days,
                    'description': description,
                    'is_special': bool(is_special)
                }
            
            return pricing_options
            
        except Exception as e:
            logging.error(f"Error getting active subscription plans for purchase: {e}")
            return {}
    
    def seed_default_subscription_plans(self, created_by=None):
        """Seed database with default subscription plans (for initial setup)"""
        try:
            default_plans = [
                {
                    'plan_key': 'premium_1d',
                    'title': '1 kun Premium ⭐',
                    'description': 'Ҳаммасига киришга рухсат',
                    'stars': 1,
                    'days': 1,
                    'sort_order': 1
                },
                {
                    'plan_key': 'premium_7d',
                    'title': '7 kun Premium ⭐',
                    'description': '1 ҳафта давомида тўлиқ кириш',
                    'stars': 7,
                    'days': 7,
                    'sort_order': 2
                },
                {
                    'plan_key': 'premium_30d',
                    'title': '30 kun Premium ⭐',
                    'description': '1 ой давомида тўлиқ кириш',
                    'stars': 25,
                    'days': 30,
                    'sort_order': 3,
                    'is_special': True
                }
            ]
            
            created_count = 0
            for plan_data in default_plans:
                success, result = self.create_subscription_plan(
                    plan_key=plan_data['plan_key'],
                    title=plan_data['title'],
                    description=plan_data['description'],
                    stars=plan_data['stars'],
                    days=plan_data['days'],
                    is_special=plan_data.get('is_special', False),
                    sort_order=plan_data['sort_order'],
                    created_by=created_by
                )
                
                if success:
                    created_count += 1
            
            logging.info(f"Seeded {created_count}/{len(default_plans)} default subscription plans")
            return created_count
            
        except Exception as e:
            logging.error(f"Error seeding default subscription plans: {e}")
            return 0
    
    # ADMIN MANAGEMENT METHODS
    def add_admin(self, user_id, added_by):
        """Add a user as admin to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if admin already exists
                cursor.execute("SELECT id FROM admins WHERE user_id = ?", (user_id,))
                if cursor.fetchone():
                    return False, "User is already an admin"
                
                # Add admin record
                cursor.execute('''
                    INSERT INTO admins (user_id, added_by)
                    VALUES (?, ?)
                ''', (user_id, added_by))
                conn.commit()
                
                logging.info(f"Admin added: {user_id} by {added_by}")
                return True, "Admin added successfully"
                
        except Exception as e:
            logging.error(f"Error adding admin: {e}")
            return False, f"Database error: {str(e)}"
    
    def remove_admin(self, user_id):
        """Remove admin status from user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if admin exists
                cursor.execute("SELECT id FROM admins WHERE user_id = ? AND is_active = 1", (user_id,))
                if not cursor.fetchone():
                    return False, "User is not an admin"
                
                # Deactivate admin record
                cursor.execute(
                    "UPDATE admins SET is_active = 0 WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                
                logging.info(f"Admin removed: {user_id}")
                return True, "Admin removed successfully"
                
        except Exception as e:
            logging.error(f"Error removing admin: {e}")
            return False, f"Database error: {str(e)}"
    
    def is_admin(self, user_id):
        """Check if user is admin in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM admins WHERE user_id = ? AND is_active = 1",
                    (user_id,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking admin status: {e}")
            return False
    
    def get_all_admins(self):
        """Get all active admins from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT a.user_id, u.username, u.first_name, a.added_by, 
                           u2.first_name as added_by_name, a.added_at
                    FROM admins a
                    LEFT JOIN users u ON a.user_id = u.user_id
                    LEFT JOIN users u2 ON a.added_by = u2.user_id
                    WHERE a.is_active = 1
                    ORDER BY a.added_at ASC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting all admins: {e}")
            return []
    
    def get_admin_ids(self):
        """Get list of all active admin user IDs"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT user_id FROM admins WHERE is_active = 1"
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting admin IDs: {e}")
            return []
    
    # MANDATORY CHANNELS MANAGEMENT METHODS
    def add_mandatory_channel(self, channel_username, added_by):
        """Add a mandatory channel to the database"""
        try:
            # Ensure channel starts with @
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if channel already exists
                cursor.execute("SELECT id FROM mandatory_channels WHERE channel_username = ? AND is_active = 1", (channel_username,))
                if cursor.fetchone():
                    return False, "Channel already exists"
                
                # Add channel record
                cursor.execute('''
                    INSERT INTO mandatory_channels (channel_username, added_by)
                    VALUES (?, ?)
                ''', (channel_username, added_by))
                conn.commit()
                
                logging.info(f"Mandatory channel added: {channel_username} by {added_by}")
                return True, "Channel added successfully"
                
        except Exception as e:
            logging.error(f"Error adding mandatory channel: {e}")
            return False, f"Database error: {str(e)}"
    
    def remove_mandatory_channel(self, channel_username):
        """Remove a mandatory channel from the database"""
        try:
            # Ensure channel starts with @
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if channel exists
                cursor.execute("SELECT id FROM mandatory_channels WHERE channel_username = ? AND is_active = 1", (channel_username,))
                if not cursor.fetchone():
                    return False, "Channel not found"
                
                # Deactivate channel record
                cursor.execute(
                    "UPDATE mandatory_channels SET is_active = 0 WHERE channel_username = ?",
                    (channel_username,)
                )
                conn.commit()
                
                logging.info(f"Mandatory channel removed: {channel_username}")
                return True, "Channel removed successfully"
                
        except Exception as e:
            logging.error(f"Error removing mandatory channel: {e}")
            return False, f"Database error: {str(e)}"
    
    def get_mandatory_channels(self):
        """Get all active mandatory channels"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT channel_username FROM mandatory_channels WHERE is_active = 1 ORDER BY added_at ASC"
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting mandatory channels: {e}")
            return []
    
    def get_all_mandatory_channels_details(self):
        """Get all mandatory channels with details"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT mc.channel_username, u.first_name as added_by_name, mc.added_by, mc.added_at
                    FROM mandatory_channels mc
                    LEFT JOIN users u ON mc.added_by = u.user_id
                    WHERE mc.is_active = 1
                    ORDER BY mc.added_at ASC
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting mandatory channels details: {e}")
            return []
    
    # FRIENDS SYSTEM METHODS
    def send_friend_request(self, user_id, friend_id, session_id=None):
        """Send a friend request"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if users exist
                cursor.execute("SELECT user_id FROM users WHERE user_id IN (?, ?) AND is_active = 1", (user_id, friend_id))
                if len(cursor.fetchall()) != 2:
                    return False, "One or both users not found or inactive"
                
                # Don't allow self-friendship
                if user_id == friend_id:
                    return False, "Cannot add yourself as friend"
                
                # Check if friendship already exists (in any direction)
                cursor.execute(
                    "SELECT status FROM friends WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)",
                    (user_id, friend_id, friend_id, user_id)
                )
                existing = cursor.fetchone()
                
                if existing:
                    status = existing[0]
                    if status == 'accepted':
                        return False, "Already friends"
                    elif status == 'pending':
                        return False, "Friend request already pending"
                    elif status == 'declined':
                        # Update to pending again
                        cursor.execute(
                            "UPDATE friends SET status = 'pending', updated_at = CURRENT_TIMESTAMP WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)",
                            (user_id, friend_id, friend_id, user_id)
                        )
                        conn.commit()
                        return True, "Friend request sent again"
                
                # Create new friend request
                cursor.execute('''
                    INSERT INTO friends (user_id, friend_id, status, session_id)
                    VALUES (?, ?, 'pending', ?)
                ''', (user_id, friend_id, session_id))
                conn.commit()
                
                logging.info(f"Friend request sent: {user_id} -> {friend_id}")
                return True, "Friend request sent successfully"
                
        except Exception as e:
            logging.error(f"Error sending friend request: {e}")
            return False, f"Database error: {str(e)}"
    
    def respond_to_friend_request(self, user_id, requester_id, accept=True):
        """Accept or decline a friend request"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find the friend request
                cursor.execute(
                    "SELECT id FROM friends WHERE user_id = ? AND friend_id = ? AND status = 'pending'",
                    (requester_id, user_id)
                )
                request = cursor.fetchone()
                
                if not request:
                    return False, "Friend request not found"
                
                new_status = 'accepted' if accept else 'declined'
                
                # Update the request status
                cursor.execute(
                    "UPDATE friends SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_status, request[0])
                )
                
                # If accepted, create reciprocal friendship
                if accept:
                    cursor.execute('''
                        INSERT INTO friends (user_id, friend_id, status)
                        VALUES (?, ?, 'accepted')
                    ''', (user_id, requester_id))
                
                conn.commit()
                
                action = "accepted" if accept else "declined"
                logging.info(f"Friend request {action}: {requester_id} -> {user_id}")
                return True, f"Friend request {action}"
                
        except Exception as e:
            logging.error(f"Error responding to friend request: {e}")
            return False, f"Database error: {str(e)}"
    
    def remove_friend(self, user_id, friend_id):
        """Remove friendship (both directions)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove friendship in both directions
                cursor.execute(
                    "DELETE FROM friends WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)",
                    (user_id, friend_id, friend_id, user_id)
                )
                
                if cursor.rowcount == 0:
                    return False, "Friendship not found"
                
                conn.commit()
                
                logging.info(f"Friendship removed: {user_id} <-> {friend_id}")
                return True, "Friend removed successfully"
                
        except Exception as e:
            logging.error(f"Error removing friend: {e}")
            return False, f"Database error: {str(e)}"
    
    def get_friends_list(self, user_id):
        """Get list of user's friends with their info"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get accepted friends with their user info
                cursor.execute('''
                    SELECT u.user_id, u.username, u.first_name, u.gender, u.age_group, 
                           u.rating, u.rating_count, f.created_at as friendship_date
                    FROM friends f
                    JOIN users u ON f.friend_id = u.user_id
                    WHERE f.user_id = ? AND f.status = 'accepted' AND u.is_active = 1
                    ORDER BY f.created_at DESC
                ''', (user_id,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logging.error(f"Error getting friends list: {e}")
            return []
    
    def get_pending_friend_requests(self, user_id, incoming=True):
        """Get pending friend requests (incoming or outgoing)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if incoming:
                    # Incoming requests (others sent to this user)
                    cursor.execute('''
                        SELECT u.user_id, u.username, u.first_name, u.gender, u.age_group, 
                               u.rating, u.rating_count, f.created_at, f.session_id
                        FROM friends f
                        JOIN users u ON f.user_id = u.user_id
                        WHERE f.friend_id = ? AND f.status = 'pending' AND u.is_active = 1
                        ORDER BY f.created_at DESC
                    ''', (user_id,))
                else:
                    # Outgoing requests (this user sent to others)
                    cursor.execute('''
                        SELECT u.user_id, u.username, u.first_name, u.gender, u.age_group, 
                               u.rating, u.rating_count, f.created_at, f.session_id
                        FROM friends f
                        JOIN users u ON f.friend_id = u.user_id
                        WHERE f.user_id = ? AND f.status = 'pending' AND u.is_active = 1
                        ORDER BY f.created_at DESC
                    ''', (user_id,))
                
                return cursor.fetchall()
                
        except Exception as e:
            logging.error(f"Error getting pending friend requests: {e}")
            return []
    
    def get_friends_count(self, user_id):
        """Get total number of friends for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM friends f JOIN users u ON f.friend_id = u.user_id WHERE f.user_id = ? AND f.status = 'accepted' AND u.is_active = 1",
                    (user_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logging.error(f"Error getting friends count: {e}")
            return 0
    
    def are_friends(self, user_id1, user_id2):
        """Check if two users are friends"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM friends WHERE user_id = ? AND friend_id = ? AND status = 'accepted'",
                    (user_id1, user_id2)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking friendship: {e}")
            return False
    
    def get_friendship_status(self, user_id1, user_id2):
        """Get friendship status between two users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check both directions
                cursor.execute(
                    "SELECT status FROM friends WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)",
                    (user_id1, user_id2, user_id2, user_id1)
                )
                result = cursor.fetchone()
                
                return result[0] if result else None
                
        except Exception as e:
            logging.error(f"Error getting friendship status: {e}")
            return None
    
    # Additional friend methods needed by bot.py
    def get_incoming_friend_requests(self, user_id):
        """Get incoming friend requests for a user"""
        return self.get_pending_friend_requests(user_id, incoming=True)
    
    def get_outgoing_friend_requests(self, user_id):
        """Get outgoing friend requests for a user"""
        return self.get_pending_friend_requests(user_id, incoming=False)
    
    def get_user_friends(self, user_id):
        """Get user's friends list (alias for get_friends_list)"""
        return self.get_friends_list(user_id)
    
    def accept_friend_request(self, requester_id, user_id):
        """Accept a friend request"""
        success, message = self.respond_to_friend_request(user_id, requester_id, accept=True)
        return success
    
    def decline_friend_request(self, requester_id, user_id):
        """Decline a friend request"""
        success, message = self.respond_to_friend_request(user_id, requester_id, accept=False)
        return success
