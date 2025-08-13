import time
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        # Rate limiting: user_id -> deque of timestamps
        self.user_actions = defaultdict(lambda: deque())
        self.message_counts = defaultdict(lambda: deque())
        
        # Flood protection settings
        self.MAX_ACTIONS_PER_MINUTE = 30  # Max actions per minute
        self.MAX_MESSAGES_PER_MINUTE = 20  # Max messages per minute
        self.ACTION_WINDOW = 60  # seconds
        
        # Rating protection: prevent multiple ratings per session
        self.rated_sessions = set()  # session_ids that have been rated by user
        
        # Command cooldowns: user_id -> last_command_time
        self.command_cooldowns = defaultdict(float)
        self.COMMAND_COOLDOWN = 1  # seconds between commands
        
    def is_rate_limited(self, user_id: int, action_type: str = "action") -> bool:
        """Check if user is rate limited"""
        current_time = time.time()
        
        if action_type == "message":
            user_deque = self.message_counts[user_id]
            max_count = self.MAX_MESSAGES_PER_MINUTE
        else:
            user_deque = self.user_actions[user_id]
            max_count = self.MAX_ACTIONS_PER_MINUTE
        
        # Remove old entries
        while user_deque and current_time - user_deque[0] > self.ACTION_WINDOW:
            user_deque.popleft()
        
        # Check if limit exceeded
        if len(user_deque) >= max_count:
            logger.warning(f"Rate limit exceeded for user {user_id}, action: {action_type}")
            return True
        
        # Add current action
        user_deque.append(current_time)
        return False
    
    def is_command_on_cooldown(self, user_id: int) -> bool:
        """Check if user is on command cooldown"""
        current_time = time.time()
        last_command = self.command_cooldowns.get(user_id, 0)
        
        if current_time - last_command < self.COMMAND_COOLDOWN:
            return True
        
        self.command_cooldowns[user_id] = current_time
        return False
    
    def can_rate_session(self, user_id: int, session_id: int) -> bool:
        """Check if user can rate this session (prevent multiple ratings)"""
        rating_key = f"{user_id}_{session_id}"
        
        if rating_key in self.rated_sessions:
            logger.warning(f"User {user_id} attempted to rate session {session_id} multiple times")
            return False
        
        self.rated_sessions.add(rating_key)
        return True
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        if not text:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "\\", "`"]
        sanitized = text
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        # Limit length
        return sanitized[:1000]  # Max 1000 characters
    
    def validate_user_id(self, user_id) -> bool:
        """Validate user ID format"""
        try:
            user_id = int(user_id)
            return 0 < user_id < 10**15  # Reasonable range for Telegram user IDs
        except (ValueError, TypeError):
            return False
    
    def is_admin_authorized(self, user_id: int, admin_ids: list, super_admin_id: int = None) -> bool:
        """Check if user is authorized admin"""
        return user_id in admin_ids or user_id == super_admin_id
    
    def cleanup_old_data(self):
        """Clean up old rate limiting data (should be called periodically)"""
        current_time = time.time()
        
        # Clean up rate limiting data older than window
        for user_id in list(self.user_actions.keys()):
            user_deque = self.user_actions[user_id]
            while user_deque and current_time - user_deque[0] > self.ACTION_WINDOW:
                user_deque.popleft()
            
            if not user_deque:
                del self.user_actions[user_id]
        
        for user_id in list(self.message_counts.keys()):
            user_deque = self.message_counts[user_id]
            while user_deque and current_time - user_deque[0] > self.ACTION_WINDOW:
                user_deque.popleft()
            
            if not user_deque:
                del self.message_counts[user_id]
        
        # Clean up old command cooldowns (older than 1 hour)
        hour_ago = current_time - 3600
        self.command_cooldowns = {
            uid: timestamp for uid, timestamp in self.command_cooldowns.items()
            if timestamp > hour_ago
        }
        
        # Clean up old rated sessions (older than 24 hours)
        # Note: This is basic cleanup. In production, you might want to use database for this
        if len(self.rated_sessions) > 10000:  # Prevent memory issues
            # Keep only recent half (simple approach)
            recent_sessions = list(self.rated_sessions)[-5000:]
            self.rated_sessions = set(recent_sessions)

class InputValidator:
    """Validate and sanitize user inputs"""
    
    @staticmethod
    def validate_rating(rating: str) -> int:
        """Validate rating input"""
        try:
            rating = int(rating)
            if 1 <= rating <= 5:
                return rating
        except (ValueError, TypeError):
            pass
        raise ValueError("Invalid rating. Must be 1-5.")
    
    @staticmethod
    def validate_user_id(user_id) -> bool:
        """Validate user ID"""
        try:
            user_id = int(user_id)
            return 0 < user_id < 10**15  # Reasonable range for Telegram user IDs
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_gender(gender: str) -> str:
        """Validate gender input"""
        valid_genders = ["erkak", "ayol", "boshqa"]
        if gender.lower() in valid_genders:
            return gender.lower()
        raise ValueError("Invalid gender selection.")
    
    @staticmethod
    def validate_age_group(age_group: str) -> str:
        """Validate age group input"""
        valid_ages = ["18_24", "25_34", "35_plus", "boshqa"]
        if age_group in valid_ages:
            return age_group
        raise ValueError("Invalid age group selection.")
    
    @staticmethod
    def validate_filter(filter_value: str, filter_type: str) -> str:
        """Validate filter values"""
        if filter_type == "gender":
            valid_filters = ["erkak", "ayol", "farqi_yoq"]
        elif filter_type == "age":
            valid_filters = ["18_24", "25_34", "35_plus", "farqi_yoq"]
        else:
            raise ValueError("Invalid filter type.")
        
        if filter_value in valid_filters:
            return filter_value
        raise ValueError(f"Invalid {filter_type} filter.")
    
    @staticmethod
    def validate_broadcast_message(message: str) -> str:
        """Validate broadcast message"""
        if not message or len(message.strip()) == 0:
            raise ValueError("Broadcast message cannot be empty.")
        
        if len(message) > 4096:  # Telegram message limit
            raise ValueError("Message too long. Maximum 4096 characters.")
        
        return message.strip()
    
    @staticmethod
    def validate_channel_username(username: str) -> str:
        """Validate channel username"""
        if not username:
            raise ValueError("Channel username cannot be empty.")
        
        # Ensure it starts with @
        if not username.startswith("@"):
            username = "@" + username
        
        # Basic validation (letters, numbers, underscores)
        import re
        if not re.match(r"@[a-zA-Z0-9_]+$", username):
            raise ValueError("Invalid channel username format.")
        
        return username
