import sqlite3
import logging
from datetime import datetime, timedelta
from config import DATABASE_PATH

class AdminPanel:
    def __init__(self):
        self.db_path = DATABASE_PATH
    
    def get_user_stats(self):
        """Get comprehensive user statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total users
                cursor.execute("SELECT COUNT(*) FROM users")
                total_users = cursor.fetchone()[0]
                
                # Active users (not banned)
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
                active_users = cursor.fetchone()[0]
                
                # Banned users
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 0")
                banned_users = cursor.fetchone()[0]
                
                # Premium users
                cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
                premium_users = cursor.fetchone()[0]
                
                # New users in different time periods
                now = datetime.now()
                
                # Last 24 hours
                yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("SELECT COUNT(*) FROM users WHERE registered_at > ?", (yesterday,))
                new_users_24h = cursor.fetchone()[0]
                
                # Last 7 days
                week_ago = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("SELECT COUNT(*) FROM users WHERE registered_at > ?", (week_ago,))
                new_users_7d = cursor.fetchone()[0]
                
                # Last 30 days
                month_ago = (now - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("SELECT COUNT(*) FROM users WHERE registered_at > ?", (month_ago,))
                new_users_30d = cursor.fetchone()[0]
                
                # Users by gender with percentages
                cursor.execute("SELECT gender, COUNT(*) FROM users WHERE is_active = 1 GROUP BY gender")
                gender_stats = cursor.fetchall()
                gender_distribution = {}
                for gender, count in gender_stats:
                    percentage = (count / max(active_users, 1)) * 100
                    gender_distribution[gender] = {
                        'count': count,
                        'percentage': round(percentage, 1)
                    }
                
                # Users by age group with percentages
                cursor.execute("SELECT age_group, COUNT(*) FROM users WHERE is_active = 1 GROUP BY age_group")
                age_stats = cursor.fetchall()
                age_distribution = {}
                for age, count in age_stats:
                    percentage = (count / max(active_users, 1)) * 100
                    age_distribution[age] = {
                        'count': count,
                        'percentage': round(percentage, 1)
                    }
                
                # Users with ratings
                cursor.execute("SELECT COUNT(*) FROM users WHERE rating_count > 0")
                users_with_ratings = cursor.fetchone()[0]
                
                # Average user rating
                cursor.execute("SELECT AVG(rating) FROM users WHERE rating_count > 0")
                avg_user_rating_result = cursor.fetchone()[0]
                avg_user_rating = round(avg_user_rating_result, 2) if avg_user_rating_result else 0
                
                # Most active users (by chat participation)
                cursor.execute('''
                    SELECT u.user_id, u.first_name, u.username, COUNT(cs.id) as chat_count
                    FROM users u
                    LEFT JOIN chat_sessions cs ON (u.user_id = cs.user1_id OR u.user_id = cs.user2_id)
                    WHERE u.is_active = 1
                    GROUP BY u.user_id, u.first_name, u.username
                    ORDER BY chat_count DESC
                    LIMIT 10
                ''')
                most_active_users = cursor.fetchall()
                
                # Users who never chatted
                cursor.execute('''
                    SELECT COUNT(*) FROM users u
                    WHERE u.is_active = 1
                    AND NOT EXISTS (
                        SELECT 1 FROM chat_sessions cs 
                        WHERE u.user_id = cs.user1_id OR u.user_id = cs.user2_id
                    )
                ''')
                users_never_chatted = cursor.fetchone()[0]
                
                # Registration trends (last 7 days)
                registration_trends = []
                for i in range(6, -1, -1):
                    day_start = (now - timedelta(days=i)).strftime('%Y-%m-%d')
                    day_end = (now - timedelta(days=i-1)).strftime('%Y-%m-%d')
                    cursor.execute(
                        "SELECT COUNT(*) FROM users WHERE DATE(registered_at) = ?",
                        (day_start,)
                    )
                    day_count = cursor.fetchone()[0]
                    registration_trends.append({
                        'date': day_start,
                        'registrations': day_count
                    })
                
                # Average registration time analysis
                cursor.execute(
                    "SELECT strftime('%H', registered_at) as hour, COUNT(*) as count FROM users GROUP BY hour ORDER BY count DESC LIMIT 5"
                )
                peak_registration_hours = cursor.fetchall()
                
                return {
                    'total_users': total_users,
                    'active_users': active_users,
                    'banned_users': banned_users,
                    'premium_users': premium_users,
                    'new_users_24h': new_users_24h,
                    'new_users_7d': new_users_7d,
                    'new_users_30d': new_users_30d,
                    'gender_distribution': gender_distribution,
                    'age_distribution': age_distribution,
                    'users_with_ratings': users_with_ratings,
                    'avg_user_rating': avg_user_rating,
                    'most_active_users': most_active_users,
                    'users_never_chatted': users_never_chatted,
                    'registration_trends': registration_trends,
                    'peak_registration_hours': peak_registration_hours
                }
        except Exception as e:
            logging.error(f"Error getting user stats: {e}")
            return None
    
    def get_chat_stats(self):
        """Get chat session statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total chat sessions
                cursor.execute("SELECT COUNT(*) FROM chat_sessions")
                total_sessions = cursor.fetchone()[0]
                
                # Active sessions
                cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE status = 'active'")
                active_sessions = cursor.fetchone()[0]
                
                # Sessions in last 24 hours
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE started_at > ?", (yesterday,))
                recent_sessions = cursor.fetchone()[0]
                
                # Average session duration (for ended sessions)
                cursor.execute('''
                    SELECT AVG(
                        CAST((julianday(ended_at) - julianday(started_at)) * 24 * 60 AS INTEGER)
                    ) as avg_duration_minutes
                    FROM chat_sessions 
                    WHERE status = 'ended' AND ended_at IS NOT NULL
                ''')
                avg_duration = cursor.fetchone()[0] or 0
                
                return {
                    'total_sessions': total_sessions,
                    'active_sessions': active_sessions,
                    'recent_sessions': recent_sessions,
                    'avg_duration_minutes': round(avg_duration, 2)
                }
        except Exception as e:
            logging.error(f"Error getting chat stats: {e}")
            return None
    
    def get_rating_stats(self):
        """Get rating statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total ratings given
                cursor.execute("SELECT COUNT(*) FROM ratings")
                total_ratings = cursor.fetchone()[0]
                
                # Average rating
                cursor.execute("SELECT AVG(rating) FROM ratings")
                avg_rating = cursor.fetchone()[0] or 0
                
                # Rating distribution
                cursor.execute("SELECT rating, COUNT(*) FROM ratings GROUP BY rating ORDER BY rating")
                rating_distribution = cursor.fetchall()
                
                # Top rated users (minimum 5 ratings)
                cursor.execute('''
                    SELECT user_id, first_name, rating, rating_count 
                    FROM users 
                    WHERE rating_count >= 5 
                    ORDER BY rating DESC 
                    LIMIT 10
                ''')
                top_users = cursor.fetchall()
                
                return {
                    'total_ratings': total_ratings,
                    'average_rating': round(avg_rating, 2),
                    'rating_distribution': dict(rating_distribution),
                    'top_users': top_users
                }
        except Exception as e:
            logging.error(f"Error getting rating stats: {e}")
            return None
    
    def get_report_stats(self):
        """Get report statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total reports
                cursor.execute("SELECT COUNT(*) FROM reports")
                total_reports = cursor.fetchone()[0]
                
                # Recent reports (last 7 days)
                week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("SELECT COUNT(*) FROM reports WHERE created_at > ?", (week_ago,))
                recent_reports = cursor.fetchone()[0]
                
                # Most reported users
                cursor.execute('''
                    SELECT u.user_id, u.first_name, COUNT(r.id) as report_count
                    FROM users u
                    JOIN reports r ON u.user_id = r.reported_id
                    GROUP BY u.user_id, u.first_name
                    ORDER BY report_count DESC
                    LIMIT 10
                ''')
                most_reported = cursor.fetchall()
                
                return {
                    'total_reports': total_reports,
                    'recent_reports': recent_reports,
                    'most_reported_users': most_reported
                }
        except Exception as e:
            logging.error(f"Error getting report stats: {e}")
            return None
    
    def get_queue_status(self):
        """Get current waiting queue status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total users in queue
                cursor.execute("SELECT COUNT(*) FROM waiting_queue")
                total_in_queue = cursor.fetchone()[0]
                
                # Queue by gender filter
                cursor.execute("SELECT gender_filter, COUNT(*) FROM waiting_queue GROUP BY gender_filter")
                gender_queue = cursor.fetchall()
                
                # Queue by age filter
                cursor.execute("SELECT age_filter, COUNT(*) FROM waiting_queue GROUP BY age_filter")
                age_queue = cursor.fetchall()
                
                # Users waiting longest
                cursor.execute('''
                    SELECT wq.user_id, u.first_name, wq.joined_at,
                           CAST((julianday('now') - julianday(wq.joined_at)) * 24 * 60 AS INTEGER) as wait_minutes
                    FROM waiting_queue wq
                    JOIN users u ON wq.user_id = u.user_id
                    ORDER BY wq.joined_at ASC
                    LIMIT 10
                ''')
                longest_waiting = cursor.fetchall()
                
                return {
                    'total_in_queue': total_in_queue,
                    'gender_queue_distribution': dict(gender_queue),
                    'age_queue_distribution': dict(age_queue),
                    'longest_waiting': longest_waiting
                }
        except Exception as e:
            logging.error(f"Error getting queue status: {e}")
            return None
    
    def ban_user(self, user_id):
        """Ban a user (deactivate account)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
                # Remove from queue if present
                cursor.execute("DELETE FROM waiting_queue WHERE user_id = ?", (user_id,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error banning user {user_id}: {e}")
            return False
    
    def unban_user(self, user_id):
        """Unban a user (activate account)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error unbanning user {user_id}: {e}")
            return False
    
    def get_user_details(self, user_id):
        """Get detailed information about a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # User basic info
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user_info = cursor.fetchone()
                
                if not user_info:
                    return None
                
                # User's chat sessions
                cursor.execute('''
                    SELECT COUNT(*) as total_chats,
                           AVG(CAST((julianday(ended_at) - julianday(started_at)) * 24 * 60 AS INTEGER)) as avg_duration
                    FROM chat_sessions 
                    WHERE (user1_id = ? OR user2_id = ?) AND status = 'ended'
                ''', (user_id, user_id))
                chat_stats = cursor.fetchone()
                
                # Ratings given by user
                cursor.execute("SELECT AVG(rating), COUNT(*) FROM ratings WHERE rater_id = ?", (user_id,))
                ratings_given = cursor.fetchone()
                
                # Reports made by user
                cursor.execute("SELECT COUNT(*) FROM reports WHERE reporter_id = ?", (user_id,))
                reports_made = cursor.fetchone()[0]
                
                # Reports against user
                cursor.execute("SELECT COUNT(*) FROM reports WHERE reported_id = ?", (user_id,))
                reports_received = cursor.fetchone()[0]
                
                return {
                    'user_info': user_info,
                    'total_chats': chat_stats[0] or 0,
                    'avg_session_duration': round(chat_stats[1] or 0, 2),
                    'avg_rating_given': round(ratings_given[0] or 0, 2),
                    'ratings_given_count': ratings_given[1] or 0,
                    'reports_made': reports_made,
                    'reports_received': reports_received
                }
        except Exception as e:
            logging.error(f"Error getting user details for {user_id}: {e}")
            return None
    
    def clear_old_data(self, days=30):
        """Clear old data (sessions, ratings) older than specified days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clear old ended sessions
                cursor.execute("DELETE FROM chat_sessions WHERE ended_at < ? AND status = 'ended'", (cutoff_date,))
                deleted_sessions = cursor.rowcount
                
                # Clear old ratings associated with deleted sessions
                cursor.execute("DELETE FROM ratings WHERE session_id NOT IN (SELECT id FROM chat_sessions)")
                deleted_ratings = cursor.rowcount
                
                # Clear old reports
                cursor.execute("DELETE FROM reports WHERE created_at < ?", (cutoff_date,))
                deleted_reports = cursor.rowcount
                
                conn.commit()
                
                return {
                    'deleted_sessions': deleted_sessions,
                    'deleted_ratings': deleted_ratings,
                    'deleted_reports': deleted_reports
                }
        except Exception as e:
            logging.error(f"Error clearing old data: {e}")
            return None
    
    # Note: Admin management and mandatory channels are now handled by the Database class
    # These methods have been moved to database.py for better consistency
    
    def get_mandatory_channels(self):
        """Get all active mandatory channels from database"""
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
    
    def get_mandatory_channels_details(self):
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
    
    def add_mandatory_channel(self, channel, added_by_user_id):
        """Add mandatory channel to database"""
        try:
            # Use the database method instead of .env file
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Ensure channel starts with @
                if not channel.startswith('@'):
                    channel = '@' + channel
                    
                # Check if channel already exists
                cursor.execute("SELECT id FROM mandatory_channels WHERE channel_username = ? AND is_active = 1", (channel,))
                if cursor.fetchone():
                    return False, "Channel already exists"
                
                # Add channel record
                cursor.execute('''
                    INSERT INTO mandatory_channels (channel_username, added_by)
                    VALUES (?, ?)
                ''', (channel, added_by_user_id))
                conn.commit()
                
                logging.info(f"Mandatory channel added: {channel} by {added_by_user_id}")
                return True, "Channel added successfully"
                
        except Exception as e:
            logging.error(f"Error adding mandatory channel: {e}")
            return False, f"Database error: {str(e)}"
    
    def remove_mandatory_channel(self, channel):
        """Remove mandatory channel from database"""
        try:
            # Use the database method instead of .env file
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Ensure channel starts with @
                if not channel.startswith('@'):
                    channel = '@' + channel
                    
                # Check if channel exists
                cursor.execute("SELECT id FROM mandatory_channels WHERE channel_username = ? AND is_active = 1", (channel,))
                if not cursor.fetchone():
                    return False, "Channel not found"
                
                # Deactivate channel record
                cursor.execute(
                    "UPDATE mandatory_channels SET is_active = 0 WHERE channel_username = ?",
                    (channel,)
                )
                conn.commit()
                
                logging.info(f"Mandatory channel removed: {channel}")
                return True, "Channel removed successfully"
                
        except Exception as e:
            logging.error(f"Error removing mandatory channel: {e}")
            return False, f"Database error: {str(e)}"

def print_dashboard():
    """Print admin dashboard with all statistics"""
    admin = AdminPanel()
    
    print("=" * 60)
    print("           TELEGRAM BOT ADMIN DASHBOARD")
    print("=" * 60)
    
    # User Statistics
    user_stats = admin.get_user_stats()
    if user_stats:
        print("\n📊 USER STATISTICS")
        print("-" * 30)
        print(f"Total Users: {user_stats['total_users']}")
        print(f"Active Users (30 days): {user_stats['active_users']}")
        print(f"Gender Distribution: {user_stats['gender_distribution']}")
        print(f"Age Distribution: {user_stats['age_distribution']}")
    
    # Chat Statistics
    chat_stats = admin.get_chat_stats()
    if chat_stats:
        print("\n💬 CHAT STATISTICS")
        print("-" * 30)
        print(f"Total Sessions: {chat_stats['total_sessions']}")
        print(f"Active Sessions: {chat_stats['active_sessions']}")
        print(f"Recent Sessions (24h): {chat_stats['recent_sessions']}")
        print(f"Average Duration: {chat_stats['avg_duration_minutes']} minutes")
    
    # Rating Statistics
    rating_stats = admin.get_rating_stats()
    if rating_stats:
        print("\n⭐ RATING STATISTICS")
        print("-" * 30)
        print(f"Total Ratings: {rating_stats['total_ratings']}")
        print(f"Average Rating: {rating_stats['average_rating']}/5")
        print(f"Rating Distribution: {rating_stats['rating_distribution']}")
    
    # Report Statistics
    report_stats = admin.get_report_stats()
    if report_stats:
        print("\n⚠️ REPORT STATISTICS")
        print("-" * 30)
        print(f"Total Reports: {report_stats['total_reports']}")
        print(f"Recent Reports (7 days): {report_stats['recent_reports']}")
        if report_stats['most_reported_users']:
            print("Most Reported Users:")
            for user_id, name, count in report_stats['most_reported_users'][:5]:
                print(f"  - {name} (ID: {user_id}): {count} reports")
    
    # Queue Status
    queue_status = admin.get_queue_status()
    if queue_status:
        print("\n🔍 QUEUE STATUS")
        print("-" * 30)
        print(f"Users in Queue: {queue_status['total_in_queue']}")
        print(f"Gender Filter Distribution: {queue_status['gender_queue_distribution']}")
        print(f"Age Filter Distribution: {queue_status['age_queue_distribution']}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print_dashboard()
