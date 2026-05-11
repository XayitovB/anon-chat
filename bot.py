import logging
import asyncio
from datetime import datetime
from telegram import Update, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler
from telegram.error import TelegramError, BadRequest, TimedOut, NetworkError

from config import BOT_TOKEN, SUPER_ADMIN_ID, BOT_USERNAME
from database import Database
from keyboards import Keyboards
from handlers.admin import AdminHandlers
from security import SecurityManager, InputValidator

# Configure color-coded logging for better visibility
try:
    import colorlog
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'white',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    ))
    
    # Configure root logger with color support
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler]
    )
except ImportError:
    # Fallback to standard logging if colorlog is not available
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),  # Console output
        ]
    )

logger = logging.getLogger(__name__)

# Set detailed logging for all modules
logging.getLogger('telegram').setLevel(logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)  # Reduce HTTP noise
logging.getLogger('urllib3').setLevel(logging.WARNING)  # Reduce HTTP noise

# Custom error logging function with red color emphasis
def log_error(message, exc_info=None):
    """Log error messages in red for better visibility"""
    logger.error(f"🔴 {message}", exc_info=exc_info)

class ChatBot:
    def __init__(self):
        self.db = Database()
        self.active_chats = {}  # {user_id: {partner_id, session_id}}
        self.user_states = {}   # {user_id: state}
        self.search_filters = {}  # {user_id: {gender_filter, age_filter}}
        self.admin_handlers = AdminHandlers(self.db, self)
        self.security = SecurityManager()
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user_id = update.effective_user.id
        
        # Handle referral links
        referrer_id = None
        if context.args and len(context.args) > 0:
            start_param = context.args[0]
            # Check if it's a referral link (format: u123456789)
            if start_param.startswith('u') and start_param[1:].isdigit():
                referrer_id = int(start_param[1:])
                logger.info(f"User {user_id} started via referral from {referrer_id}")
        
        # Cancel any ongoing search if user restarts
        if user_id in self.search_filters:
            del self.search_filters[user_id]
        
        # Remove from queue if exists
        self.db.remove_from_queue(user_id)
        
        # Remove any running search jobs if job_queue is available
        if context.job_queue:
            current_jobs = context.job_queue.get_jobs_by_name(f"search_{user_id}")
            for job in current_jobs:
                job.schedule_removal()
        
        # Check mandatory channels only for non-premium users
        if not self.db.is_user_premium(user_id):
            mandatory_channels = self.db.get_mandatory_channels()
            if mandatory_channels:
                subscribed = await self.check_user_subscription(context, user_id, mandatory_channels)
                if not subscribed:
                    await self.show_subscription_required(update, context, mandatory_channels)
                    return
        
        user = self.db.get_user(user_id)
        
        if user:
            # User already registered, show main menu
            await self.show_main_menu(update, context)
        else:
            # New user, start registration process
            # Store referrer_id in user_states for later use after registration
            if referrer_id:
                if user_id not in self.user_states:
                    self.user_states[user_id] = {}
                self.user_states[user_id]['referrer_id'] = referrer_id
            await self.start_registration(update, context)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /admin command"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ У вас нет прав администратора!")
            return
        
        # Show admin panel
        text = """
👑 Панель администратора

Выберите один из разделов:
        """
        await update.message.reply_text(text, reply_markup=Keyboards.admin_main_menu())
    
    async def check_mandatory_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Check if user subscribed to mandatory channels"""
        mandatory_channels = self.db.get_mandatory_channels()
        if not mandatory_channels:
            # No mandatory channels, proceed to registration
            await self.start_registration(update, context)
            return
        
        user_id = update.effective_user.id
        not_subscribed = []
        
        for channel in mandatory_channels:
            try:
                member = await context.bot.get_chat_member(channel, user_id)
                if member.status in ['left', 'kicked']:
                    not_subscribed.append(channel)
            except Exception as e:
                logger.error(f"Error checking channel {channel}: {e}")
                not_subscribed.append(channel)
        
        if not_subscribed:
            text = """
📍 Для использования бота, вы должны быть подписаны на наш канал:
            """
            # Create inline keyboard with channel buttons
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard_buttons = []
            
            # Add channel buttons
            for channel in not_subscribed:
                # Remove @ symbol if present for clean display
                channel_name = channel.replace('@', '')
                keyboard_buttons.append([InlineKeyboardButton(f"📺 {channel_name}", url=f"https://t.me/{channel_name}")])
            
            # Add subscription check button
            keyboard_buttons.append([InlineKeyboardButton("👍 Я подписался", callback_data="check_channels")])
            
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
            
            # 🔴 FIX: Check if message content/markup is different to avoid Telegram error
            try:
                if update.callback_query:
                    current_text = update.callback_query.message.text
                    current_markup = update.callback_query.message.reply_markup
                    
                    # Only edit if content is different
                    if current_text != text or str(current_markup) != str(keyboard):
                        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
                    else:
                        # Just answer the callback query to avoid timeout
                        await update.callback_query.answer("Пожалуйста, подпишитесь на каналы для продолжения.")
                else:
                    await update.message.reply_text(text, reply_markup=keyboard)
            except Exception as e:
                logger.error(f"🔴 Error in check_mandatory_channels message edit: {e}")
                # Fallback: send new message
                try:
                    if update.callback_query:
                        await update.callback_query.answer("Проверка подписки...")
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=text,
                            reply_markup=keyboard
                        )
                    else:
                        await update.message.reply_text(text, reply_markup=keyboard)
                except Exception as fallback_e:
                    logger.error(f"🔴 CRITICAL: Fallback also failed: {fallback_e}")
        else:
            await self.show_welcome_message(update, context)
    
    async def show_welcome_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show welcome message with image after successful subscription"""
        welcome_text = """
👋 Добро пожаловать в лучший бот для знакомств!
        """
        
        # Path to the local image file
        photo_path = "picture/1.jpg"
        
        try:
            # Send photo with caption and button
            with open(photo_path, 'rb') as photo:
                if update.callback_query:
                    # Delete the old message first
                    await update.callback_query.delete_message()
                    # Send new photo message
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=welcome_text,
                        reply_markup=Keyboards.continue_button()
                    )
                else:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=welcome_text,
                        reply_markup=Keyboards.continue_button()
                    )
        except FileNotFoundError:
            logger.error(f"Image file {photo_path} not found")
            # Fallback to text only
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    welcome_text,
                    reply_markup=Keyboards.continue_button()
                )
            else:
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=Keyboards.continue_button()
                )
        except Exception as e:
            logger.error(f"Error sending welcome message with photo: {e}")
            # Fallback to text only
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    welcome_text,
                    reply_markup=Keyboards.continue_button()
                )
            else:
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=Keyboards.continue_button()
                )
    
    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Start user registration process"""
        text = """
🎉 Добро пожаловать в бот анонимного общения!

Для продолжения выберите ваш пол:
        """
        if update.callback_query:
            # Check if the message has photo (from welcome message)
            if update.callback_query.message.photo:
                # Delete the photo message and send new text message
                await update.callback_query.delete_message()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=Keyboards.gender_selection()
                )
            else:
                # Regular text message, edit it
                await update.callback_query.edit_message_text(text, reply_markup=Keyboards.gender_selection())
        else:
            await update.message.reply_text(text, reply_markup=Keyboards.gender_selection())
    
    async def handle_gender_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, gender: str) -> None:
        """Handle gender selection"""
        user_id = update.effective_user.id
        self.user_states[user_id] = {'gender': gender}
        
        gender_text = {"erkak": "👨 Мужчина", "ayol": "👩 Женщина", "boshqa": "🚻 Другое"}[gender]
        
        text = f"""
✅ Ваш пол: {gender_text}

Теперь выберите вашу возрастную группу:
        """
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.age_selection())
    
    async def handle_age_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, age_group: str) -> None:
        """Handle age group selection"""
        user_id = update.effective_user.id
        user = update.effective_user
        
        if user_id not in self.user_states:
            await update.callback_query.answer("Ошибка! Попробуйте сначала.", show_alert=True)
            return
        
        gender = self.user_states[user_id]['gender']
        
        # Check if user already exists (for profile updates)
        existing_user = self.db.get_user(user_id)
        
        if existing_user:
            # Update existing user profile
            success = self.db.update_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                gender=gender,
                age_group=age_group
            )
        else:
            # Register new user in database
            success = self.db.register_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                gender=gender,
                age_group=age_group
            )
        
        if success:
            age_text = {
                "9_14": "9-14",
                "15_18": "15-18",
                "18_24": "18-24", 
                "25_34": "25-34", 
                "35_plus": "35+", 
                "boshqa": "Другое"
            }[age_group]
            
            gender_text_map = {"erkak": "👨 Мужчина", "ayol": "👩 Женщина", "boshqa": "🚻 Другое"}
            
            # Check if user came via referral
            referral_bonus = ""
            if user_id in self.user_states and 'referrer_id' in self.user_states[user_id]:
                referrer_id = self.user_states[user_id]['referrer_id']
                # Check if referrer exists and is different from current user
                if referrer_id != user_id and self.db.get_user(referrer_id):
                    # Add referral to database
                    success_referral = self.db.add_referral(referrer_id, user_id)
                    if success_referral:
                        referral_bonus = "\n🎉 Вы присоединились по реферальной ссылке! Вашему другу начислен бонус!"
                        logger.info(f"Referral processed: {referrer_id} -> {user_id}")
                        
                        # Send notification to referrer
                        try:
                            referrer_count = self.db.get_referral_count(referrer_id)
                            await context.bot.send_message(
                                chat_id=referrer_id,
                                text=f"🎉 По вашей ссылке присоединился новый пользователь!\n\n" +
                                     f"👥 Всего приглашений: {referrer_count}\n" +
                                     f"💎 За каждые 3 приглашения вы получите +1 день VIP!"
                            )
                        except Exception as e:
                            logger.error(f"Failed to send referral notification to {referrer_id}: {e}")
            
            text = f"""
🎉 Регистрация успешно завершена!

📊 Ваши данные:
• Пол: {gender_text_map[gender]}
• Возрастная группа: {age_text}{referral_bonus}

Теперь вы можете пользоваться ботом!
            """
            
            # Show completion message briefly, then show main menu with photo
            await update.callback_query.edit_message_text(text)
            
            # Wait a moment for user to read the completion message
            await asyncio.sleep(2)
            
            # Clean up user state
            del self.user_states[user_id]
            
            # Show main menu with photo
            await self.show_main_menu(update, context)
        else:
            await update.callback_query.answer("Произошла ошибка! Попробуйте снова.", show_alert=True)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show main menu"""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user:
            await self.start(update, context)
            return
        
        # Check premium status
        is_premium = self.db.is_user_premium(user_id)
        premium_info = self.db.get_premium_info(user_id) if is_premium else None
        
        # Format rating
        rating_text = f"⭐ {user[5]:.1f}/5" if user[6] > 0 else "⭐ Новый пользователь"
        
        # Format gender with emojis
        gender_display = {
            "erkak": "👨 Мужчина", 
            "ayol": "👩 Женщина", 
            "boshqa": "🚻 Другое"
        }.get(user[3], "👤 Не указано")
        
        # Format age group
        age_display = {
            "9_14": "📅 9-14 лет",
            "15_18": "📅 15-18 лет",
            "18_24": "📅 18-24 года",
            "25_34": "📅 25-34 года", 
            "35_plus": "📅 35+ лет",
            "boshqa": "📅 Другое"
        }.get(user[4], "📅 Не указано")
        
        # Premium status display
        if is_premium and premium_info and 'days_left' in premium_info:
            premium_status = f"💎 VIP статус (осталось {premium_info['days_left']} дн.)"
            premium_emoji = "💎"
        else:
            premium_status = "⚡ Обычный пользователь"
            premium_emoji = "⚡"
        
        # Beautiful main menu text
        text = f"""
🏠 *Главное меню* {premium_emoji}

═══════════════════════
👤 *Ваш профиль:*

{gender_display}
{age_display}
{rating_text}
{premium_status}
═══════════════════════

✨ Выберите действие:
        """
        
        # Check if user is admin and add admin button
        if self.is_admin(user_id):
            # Create keyboard with admin button
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard_buttons = [
                [InlineKeyboardButton("🔍 Поиск собеседника", callback_data="find_chat")],
                [
                    InlineKeyboardButton("💎 PREMIUM", callback_data="premium"),
                    InlineKeyboardButton("⚙️ Настроить поиск", callback_data="settings")
                ],
                [
                    InlineKeyboardButton("📊 Анкета", callback_data="profile"),
                    InlineKeyboardButton("🏆 ТОП", callback_data="top_users")
                ],
                [
                    InlineKeyboardButton("💬 Добавить в чат", callback_data="add_to_chat"),
                    InlineKeyboardButton("🚀 Друзья", callback_data="friends")
                ],
                [InlineKeyboardButton("👑 Админ-панель", callback_data="admin_menu")],
                [InlineKeyboardButton("❌ Выход", callback_data="exit")]
            ]
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
        else:
            keyboard = Keyboards.main_menu()
        
        # Path to the main menu image file
        photo_path = "picture/2.jpg"
        
        try:
            # Always send a fresh message for the main menu to ensure proper button display
            with open(photo_path, 'rb') as photo:
                if update.callback_query:
                    # For callback queries, delete old message and send new one
                    try:
                        await update.callback_query.delete_message()
                    except Exception as e:
                        logger.warning(f"Could not delete old message: {e}")
                    
                    # Send new photo message
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=text,
                        parse_mode='Markdown',
                        reply_markup=keyboard
                    )
                elif update.message:
                    # For regular messages (like /start command), just send new photo
                    await update.message.reply_photo(
                        photo=photo,
                        caption=text,
                        parse_mode='Markdown',
                        reply_markup=keyboard
                    )
                else:
                    # Fallback - send directly via context
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=text,
                        parse_mode='Markdown',
                        reply_markup=keyboard
                    )
        except FileNotFoundError:
            logger.error(f"Image file {photo_path} not found")
            # Fallback to text only
            if update.callback_query:
                try:
                    await update.callback_query.delete_message()
                except Exception:
                    pass
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=keyboard
                )
            elif update.message:
                await update.message.reply_text(text, reply_markup=keyboard)
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"Error sending main menu with photo: {e}")
            # Fallback to text only
            if update.callback_query:
                try:
                    await update.callback_query.delete_message()
                except Exception:
                    pass
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=keyboard
                )
            elif update.message:
                await update.message.reply_text(text, reply_markup=keyboard)
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=keyboard
                )
    
    async def start_partner_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Start partner search process"""
        user_id = update.effective_user.id
        
        # Check if user is already in chat
        if user_id in self.active_chats:
            await update.callback_query.answer("У вас уже есть активный чат!", show_alert=True)
            return
        
        # Check if user is premium
        is_premium = self.db.is_user_premium(user_id)
        
        if is_premium:
            # Premium users can select filters
            text = """
🔍 Поиск собеседника

Выберите пол искомого собеседника:
            """
            # Check if the message has photo (from main menu)
            if update.callback_query.message.photo:
                # Delete the photo message and send new text message
                await update.callback_query.delete_message()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=Keyboards.filter_gender()
                )
            else:
                await update.callback_query.edit_message_text(text, reply_markup=Keyboards.filter_gender())
        else:
            # Non-premium users get random search without filters
            text = """
🔍 Поиск собеседника

⚡ Поиск случайного собеседника...
            """
            
            # Check if the message has photo (from main menu)
            if update.callback_query.message.photo:
                # Delete the photo message and send new text message
                await update.callback_query.delete_message()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text
                )
            else:
                await update.callback_query.edit_message_text(text)
            
            # Set default filters for random search (no specific gender/age preference)
            if user_id not in self.search_filters:
                self.search_filters[user_id] = {}
            
            self.search_filters[user_id]['gender_filter'] = 'farqi_yoq'  # No gender preference
            self.search_filters[user_id]['age_filter'] = 'farqi_yoq'     # No age preference
            
            # Start searching immediately
            await self.search_partner(update, context)
    
    async def handle_gender_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE, gender_filter: str) -> None:
        """Handle gender filter selection"""
        user_id = update.effective_user.id
        
        if user_id not in self.search_filters:
            self.search_filters[user_id] = {}
        
        self.search_filters[user_id]['gender_filter'] = gender_filter
        
        filter_text = {
            "erkak": "👨 Мужчина", 
            "ayol": "👩 Женщина", 
            "farqi_yoq": "⚖ Не важно"
        }[gender_filter]
        
        text = f"""
✅ Фильтр по полу: {filter_text}

Выберите возрастную группу:
        """
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.filter_age())
    
    async def handle_age_filter(self, update: Update, context: ContextTypes.DEFAULT_TYPE, age_filter: str) -> None:
        """Handle age filter selection and start search"""
        user_id = update.effective_user.id
        
        if user_id not in self.search_filters or 'gender_filter' not in self.search_filters[user_id]:
            await update.callback_query.answer("Ошибка! Попробуйте снова.", show_alert=True)
            return
        
        self.search_filters[user_id]['age_filter'] = age_filter
        
        # Start searching for partner
        await self.search_partner(update, context)
    
    async def search_partner(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Search for a compatible partner"""
        user_id = update.effective_user.id
        user = self.db.get_user(user_id)
        
        if not user or user_id not in self.search_filters:
            await update.callback_query.answer("Произошла ошибка!", show_alert=True)
            return
        
        gender_filter = self.search_filters[user_id]['gender_filter']
        age_filter = self.search_filters[user_id]['age_filter']
        
        logger.info(f"User {user_id} searching with filters: gender={gender_filter}, age={age_filter}")
        
        # Try to find a partner
        partner_id = self.db.find_partner(
            user_id=user_id,
            user_gender=user[3],  # user's gender
            user_age=user[4],     # user's age group
            gender_filter=gender_filter,
            age_filter=age_filter
        )
        
        if partner_id:
            logger.info(f"Partner found immediately: {partner_id} for user {user_id}")
            # Partner found, start chat
            await self.start_chat(update, context, user_id, partner_id)
        else:
            logger.info(f"No partner found for user {user_id}, adding to queue")
            # No partner found, add to queue
            self.db.add_to_queue(user_id, gender_filter, age_filter)
            
            text = """
🔍 Идет поиск собеседника...

Вы будете уведомлены, когда найдется подходящий собеседник.
            """
            
            # Send a new message instead of trying to edit (which may not exist)
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=Keyboards.cancel_search()
                )
            except Exception as e:
                logger.error(f"Error sending search message: {e}")
                return
            
            # Get the message ID from the sent message for periodic updates
            # We'll use the chat ID for reference instead since we sent a new message
            
            # Start periodic check for partners if job_queue is available
            if context.job_queue:
                logger.info(f"Starting periodic search job for user {user_id}")
                context.job_queue.run_repeating(
                    callback=self.check_for_partner,
                    interval=10,
                    data={'user_id': user_id, 'chat_id': update.effective_chat.id},
                    name=f"search_{user_id}"
                )
            else:
                logger.warning(f"JobQueue not available, user {user_id} added to queue but no periodic search will run")
    
    async def check_for_partner(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Periodic check for available partners"""
        job = context.job
        user_id = job.data['user_id']
        # Handle both old and new data formats
        message_id = job.data.get('message_id')
        chat_id = job.data.get('chat_id', user_id)  # Fallback to user_id as chat_id
        
        # Check if user is still in queue
        user = self.db.get_user(user_id)
        if not user or user_id in self.active_chats:
            job.schedule_removal()
            return
        
        # Try to find a partner again
        if user_id in self.search_filters:
            gender_filter = self.search_filters[user_id]['gender_filter']
            age_filter = self.search_filters[user_id]['age_filter']
            
            partner_id = self.db.find_partner(
                user_id=user_id,
                user_gender=user[3],
                user_age=user[4],
                gender_filter=gender_filter,
                age_filter=age_filter
            )
            
            if partner_id:
                # Partner found!
                self.db.remove_from_queue(user_id)
                job.schedule_removal()
                
                # Notify user that partner was found
                try:
                    # Since we can't edit a specific message anymore, just send a new message
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="✅ Собеседник найден! Чат начинается..."
                    )
                    
                    # Start chat
                    await self.start_chat_by_ids(context, user_id, partner_id)
                    
                except Exception as e:
                    logger.error(f"Error starting chat: {e}")
    
    async def start_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user1_id: int, user2_id: int) -> None:
        """Start chat between two users"""
        await self.start_chat_by_ids(context, user1_id, user2_id)
    
    async def start_chat_by_ids(self, context: ContextTypes.DEFAULT_TYPE, user1_id: int, user2_id: int) -> None:
        """Start chat between two users by their IDs"""
        # Create chat session
        session_id = self.db.create_chat_session(user1_id, user2_id)
        if not session_id:
            return
        
        # Add to active chats
        self.active_chats[user1_id] = {'partner_id': user2_id, 'session_id': session_id}
        self.active_chats[user2_id] = {'partner_id': user1_id, 'session_id': session_id}
        
        # Get partner info for rating display
        user1 = self.db.get_user(user1_id)
        user2 = self.db.get_user(user2_id)
        
        user1_rating = f"⭐ {user1[5]:.1f}/5" if user1[6] > 0 else "Новый пользователь"
        user2_rating = f"⭐ {user2[5]:.1f}/5" if user2[6] > 0 else "Новый пользователь"
        
        # Notify both users
        text1 = f"""
✅ Собеседник найден!

📊 Рейтинг собеседника: {user2_rating}

Чат начался! Отправьте сообщение или используйте кнопки ниже.
        """
        
        text2 = f"""
✅ Собеседник найден!

📊 Рейтинг собеседника: {user1_rating}

Чат начался! Отправьте сообщение или используйте кнопки ниже.
        """
        
        try:
            await context.bot.send_message(
                chat_id=user1_id,
                text=text1,
                reply_markup=Keyboards.chat_controls()
            )
            await context.bot.send_message(
                chat_id=user2_id,
                text=text2,
                reply_markup=Keyboards.chat_controls()
            )
        except Exception as e:
            logger.error(f"Error sending chat start messages: {e}")
        
        # Clean up search filters
        if user1_id in self.search_filters:
            del self.search_filters[user1_id]
        if user2_id in self.search_filters:
            del self.search_filters[user2_id]
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle regular messages during chat with security checks"""
        user_id = update.effective_user.id
        
        # Check if admin is providing input
        if self.is_admin(user_id) and ('awaiting_input' in context.user_data or 'broadcast_target' in context.user_data):
            await self.admin_handlers.handle_admin_message_input(update, context)
            return
        
        # Check mandatory channels for non-premium users
        mandatory_channels = self.db.get_mandatory_channels()
        if mandatory_channels and not self.db.is_user_premium(user_id):
            subscribed = await self.check_user_subscription(context, user_id, mandatory_channels)
            if not subscribed:
                await self.show_subscription_required(update, context, mandatory_channels)
                return
        
        # Security checks
        if self.security.is_rate_limited(user_id, "message"):
            await update.message.reply_text(
                "Вы отправляете сообщения слишком быстро. Подождите немного."
            )
            return
        
        # Check if user is banned
        if self.db.is_user_banned(user_id):
            await update.message.reply_text(
                "Ваш аккаунт заблокирован."
            )
            return
        
        if user_id not in self.active_chats:
            # User not in active chat
            await update.message.reply_text(
                "У вас нет активного чата. Для начала чата отправьте команду /start."
            )
            return
        
        partner_id = self.active_chats[user_id]['partner_id']
        
        # Forward message to partner
        try:
            if update.message.text:
                await context.bot.send_message(chat_id=partner_id, text=update.message.text)
            elif update.message.photo:
                await context.bot.send_photo(
                    chat_id=partner_id,
                    photo=update.message.photo[-1].file_id,
                    caption=update.message.caption
                )
            elif update.message.video:
                await context.bot.send_video(
                    chat_id=partner_id,
                    video=update.message.video.file_id,
                    caption=update.message.caption
                )
            elif update.message.document:
                await context.bot.send_document(
                    chat_id=partner_id,
                    document=update.message.document.file_id,
                    caption=update.message.caption
                )
            elif update.message.voice:
                await context.bot.send_voice(
                    chat_id=partner_id,
                    voice=update.message.voice.file_id
                )
            elif update.message.sticker:
                await context.bot.send_sticker(
                    chat_id=partner_id,
                    sticker=update.message.sticker.file_id
                )
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            await update.message.reply_text("Сообщение не отправлено. Возможно, собеседник остановил бота.")
    
    async def end_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None) -> None:
        """End current chat"""
        if user_id is None:
            user_id = update.effective_user.id
        
        if user_id not in self.active_chats:
            if update and update.callback_query:
                await update.callback_query.answer("Активный чат не найден!", show_alert=True)
            return
        
        chat_info = self.active_chats[user_id]
        partner_id = chat_info['partner_id']
        session_id = chat_info['session_id']
        
        # End session in database
        self.db.end_chat_session(session_id)
        
        # Remove from active chats
        if user_id in self.active_chats:
            del self.active_chats[user_id]
        if partner_id in self.active_chats:
            del self.active_chats[partner_id]
        
        # Notify both users and ask for rating with add friend option
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="Чат завершен. Оцените вашего собеседника:",
                reply_markup=Keyboards.rating(show_add_friend=True, partner_id=partner_id)
            )
            await context.bot.send_message(
                chat_id=partner_id,
                text="Чат завершен. Оцените вашего собеседника:",
                reply_markup=Keyboards.rating(show_add_friend=True, partner_id=user_id)
            )
            
            # Store rating context
            self.user_states[user_id] = {'rating_context': {'partner_id': partner_id, 'session_id': session_id}}
            self.user_states[partner_id] = {'rating_context': {'partner_id': user_id, 'session_id': session_id}}
            
        except Exception as e:
            logger.error(f"Error ending chat: {e}")
    
    async def handle_rating(self, update: Update, context: ContextTypes.DEFAULT_TYPE, rating: int) -> None:
        """Handle rating submission with security checks"""
        user_id = update.effective_user.id
        
        # Rate limiting check
        if self.security.is_rate_limited(user_id, "action"):
            await update.callback_query.answer("Вы действуете слишком быстро. Подождите немного.", show_alert=True)
            return
        
        # Validate rating context
        if user_id not in self.user_states or 'rating_context' not in self.user_states[user_id]:
            await update.callback_query.answer("Произошла ошибка!", show_alert=True)
            return
        
        rating_context = self.user_states[user_id]['rating_context']
        partner_id = rating_context['partner_id']
        session_id = rating_context['session_id']
        
        # Security check: Prevent multiple ratings for same session
        if not self.security.can_rate_session(user_id, session_id):
            await update.callback_query.answer("Вы уже оценили эту сессию!", show_alert=True)
            return
        
        # Validate rating value
        try:
            validated_rating = InputValidator.validate_rating(str(rating))
        except ValueError:
            await update.callback_query.answer("Неправильное значение оценки!", show_alert=True)
            return
        
        # Add rating to database
        success = self.db.add_rating(user_id, partner_id, session_id, validated_rating)
        
        if success:
            text = f"""
✅ Ваша оценка принята!

⭐ Ваша оценка: {validated_rating}/5

Спасибо! Вы можете продолжить пользоваться ботом.
            """
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.main_menu())
            
            # Clean up state
            del self.user_states[user_id]
        else:
            await update.callback_query.answer("Произошла ошибка! Попробуйте еще раз.", show_alert=True)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        data = query.data
        user_id = update.effective_user.id
        
        logger.info(f"🎯 CALLBACK QUERY: User {user_id} clicked button '{data}'")
        
        # Answer the callback query first to prevent timeout errors
        try:
            await query.answer()
            logger.debug(f"✅ Callback query answered for user {user_id}")
        except Exception as e:
            # Handle "Query is too old" and other callback query errors
            logger.warning(f"⚠️ Failed to answer callback query for user {user_id}: {e}")
            # Continue processing even if answer fails
        
        # Skip channel check for admin operations and initial registration
        skip_channel_check = (
            data.startswith("admin_") or 
            data.startswith("gender_") or 
            data.startswith("age_") or 
            data == "check_channels"
        )
        
        # Check mandatory channels for non-premium users
        if not skip_channel_check:
            mandatory_channels = self.db.get_mandatory_channels()
            if mandatory_channels and not self.db.is_user_premium(user_id):
                subscribed = await self.check_user_subscription(context, user_id, mandatory_channels)
                if not subscribed:
                    await self.show_subscription_required(update, context, mandatory_channels)
                    return
        
        # Channel check
        if data == "check_channels":
            await self.check_mandatory_channels(update, context)
        
        # Continue registration after welcome message
        elif data == "continue_registration":
            await self.start_registration(update, context)
        
        # Gender selection
        elif data.startswith("gender_"):
            gender = data.replace("gender_", "")
            await self.handle_gender_selection(update, context, gender)
        
        # Age selection
        elif data.startswith("age_"):
            age_group = data.replace("age_", "")
            await self.handle_age_selection(update, context, age_group)
        
        # Main menu
        elif data == "main_menu":
            await self.show_main_menu(update, context)
        
        # Find chat
        elif data == "find_chat":
            logger.info(f"User {user_id} clicked find_chat")
            await self.start_partner_search(update, context)
        
        # Gender filter
        elif data.startswith("filter_gender_"):
            gender_filter = data.replace("filter_gender_", "")
            logger.info(f"User {user_id} selected gender filter: {gender_filter}")
            await self.handle_gender_filter(update, context, gender_filter)
        
        # Age filter
        elif data.startswith("filter_age_"):
            age_filter = data.replace("filter_age_", "")
            logger.info(f"User {user_id} selected age filter: {age_filter}")
            await self.handle_age_filter(update, context, age_filter)
        
        # Cancel search
        elif data == "cancel_search":
            self.db.remove_from_queue(user_id)
            if user_id in self.search_filters:
                del self.search_filters[user_id]
            
            # Remove job if job_queue is available
            if context.job_queue:
                current_jobs = context.job_queue.get_jobs_by_name(f"search_{user_id}")
                for job in current_jobs:
                    job.schedule_removal()
            
            await self.show_main_menu(update, context)
        
        # Chat controls
        elif data == "next_partner":
            await self.end_chat(update, context)
        
        elif data == "leave_chat":
            await self.end_chat(update, context)
        
        elif data == "report_user":
            if user_id in self.active_chats:
                chat_info = self.active_chats[user_id]
                self.db.add_report(
                    reporter_id=user_id,
                    reported_id=chat_info['partner_id'],
                    session_id=chat_info['session_id'],
                    reason="User report"
                )
                await query.edit_message_text(
                    "✅ Жалоба отправлена. Модераторы рассмотрят её.",
                    reply_markup=Keyboards.back_to_menu()
                )
        
        # Rating
        elif data.startswith("rate_"):
            rating = int(data.replace("rate_", ""))
            await self.handle_rating(update, context, rating)
        
        # Settings
        elif data == "settings":
            text = """
⚙️ Настройки

Здесь вы можете управлять своим профилем.
            """
            # Path to the settings image file
            photo_path = "picture/3.jpg"
            
            try:
                # Send photo with caption and keyboard
                with open(photo_path, 'rb') as photo:
                    # Delete the old message first
                    await query.delete_message()
                    # Send new photo message
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=text,
                        reply_markup=Keyboards.settings_menu()
                    )
            except FileNotFoundError:
                logger.error(f"Image file {photo_path} not found")
                # Fallback to text only
                # Check if the message has photo (from main menu)
                if query.message.photo:
                    # Delete the photo message and send new text message
                    await query.delete_message()
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        reply_markup=Keyboards.settings_menu()
                    )
                else:
                    await query.edit_message_text(text, reply_markup=Keyboards.settings_menu())
            except Exception as e:
                logger.error(f"Error sending settings with photo: {e}")
                # Fallback to text only
                # Check if the message has photo (from main menu)
                if query.message.photo:
                    # Delete the photo message and send new text message
                    await query.delete_message()
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        reply_markup=Keyboards.settings_menu()
                    )
                else:
                    await query.edit_message_text(text, reply_markup=Keyboards.settings_menu())
        
        elif data == "update_profile":
            text = """
🔄 Обновление данных

Для обновления профиля пройдите регистрацию заново.
            """
            # Handle photo messages that can't be edited
            try:
                if query.message.photo:
                    # Delete the photo message and send new text message
                    await query.delete_message()
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        reply_markup=Keyboards.gender_selection()
                    )
                else:
                    await query.edit_message_text(text, reply_markup=Keyboards.gender_selection())
            except Exception as e:
                logger.error(f"Error in update_profile: {e}")
                # Fallback: delete message and send new one
                try:
                    await query.delete_message()
                except Exception:
                    pass
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=Keyboards.gender_selection()
                )
        
        # Premium
        elif data == "premium":
            logger.info(f"🔥 USER {user_id} CLICKED PREMIUM BUTTON")
            
            text = """
💎 PREMIUM

Преимущества VIP 👑:

✨ Возможен поиск по полу (мужской и женский)
✨ Возможность общаться в Пошлома чате 🔞
✨ Возможность отправлять и получать от собеседника фото/видео
✨ Собеседник попадается мгновенно
✨ Отключается реклама
✨ Больше не надо подписываться на каналы

✅ VIP выдается сразу после оплаты
            """
            
            # Get dynamic subscription plans from database
            subscription_plans = self.db.get_active_subscription_plans_for_purchase()
            logger.info(f"📊 Found {len(subscription_plans)} active subscription plans for user {user_id}")
            
            # Path to the premium image file
            photo_path = "picture/premium.jpg"
            logger.info(f"🖼️ Attempting to send premium image from: {photo_path}")
            
            try:
                logger.info(f"📤 Attempting to send photo message to user {user_id}")
                # Send photo with caption and keyboard
                with open(photo_path, 'rb') as photo:
                    logger.info(f"📂 Successfully opened image file: {photo_path}")
                    
                    # Delete the old message first
                    logger.info(f"🗑️ Deleting old message for user {user_id}")
                    await query.delete_message()
                    
                    # Send new photo message with dynamic plans
                    logger.info(f"📸 Sending premium photo to user {user_id} with {len(subscription_plans)} plans")
                    message = await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=text,
                        reply_markup=Keyboards.premium_menu(subscription_plans)
                    )
                    logger.info(f"✅ Premium photo message sent successfully to user {user_id}, message_id: {message.message_id}")
                    
            except FileNotFoundError as e:
                logger.error(f"❌ Image file {photo_path} not found! Error: {e}")
                logger.error(f"📁 Full path: {os.path.abspath(photo_path)}")
                # Fallback to text only
                logger.info(f"🔄 Falling back to text-only message for user {user_id}")
                # Check if the message has photo (from main menu)
                if query.message.photo:
                    # Delete the photo message and send new text message
                    await query.delete_message()
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        reply_markup=Keyboards.premium_menu(subscription_plans)
                    )
                    logger.info(f"📝 Sent text-only premium message to user {user_id} (deleted photo)")
                else:
                    await query.edit_message_text(text, reply_markup=Keyboards.premium_menu(subscription_plans))
                    logger.info(f"📝 Edited message to text-only premium for user {user_id}")
                    
            except Exception as e:
                logger.error(f"💥 Error sending premium menu with photo to user {user_id}: {e}")
                logger.error(f"🔍 Error type: {type(e).__name__}")
                logger.error(f"📋 Error details: {str(e)}")
                
                # Fallback to text only
                logger.info(f"🔄 Attempting fallback to text-only for user {user_id}")
                try:
                    # Check if the message has photo (from main menu)
                    if query.message.photo:
                        # Delete the photo message and send new text message
                        await query.delete_message()
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=text,
                            reply_markup=Keyboards.premium_menu(subscription_plans)
                        )
                        logger.info(f"✅ Fallback: Sent text-only premium message to user {user_id} (deleted photo)")
                    else:
                        await query.edit_message_text(text, reply_markup=Keyboards.premium_menu(subscription_plans))
                        logger.info(f"✅ Fallback: Edited message to text-only premium for user {user_id}")
                except Exception as fallback_error:
                    logger.error(f"💀 CRITICAL: Fallback also failed for user {user_id}: {fallback_error}")
        
        # Top users
        elif data == "top_users":
            await self.show_top_users(update, context)
        
        # Profile
        elif data == "profile":
            user = self.db.get_user_by_id(user_id)
            if user:
                age_text = {
                    "9_14": "9-14",
                    "15_18": "15-18",
                    "18_24": "18-24",
                    "25_34": "25-34",
                    "35_plus": "35+",
                    "boshqa": "Другое"
                }.get(user[3], "Не указано")
                
                gender_text = {
                    "erkak": "👨 Мужчина",
                    "ayol": "👩 Женщина",
                    "boshqa": "🚻 Другое"
                }.get(user[2], "Не указано")
                
                rating = user[6] if user[6] else 0
                text = f"""
📊 Ваша анкета

👤 ID: {user_id}
{gender_text}
📅 Возраст: {age_text}
⭐ Рейтинг: {rating:.1f}
📈 Всего чатов: {user[7] if user[7] else 0}
📅 Дата регистрации: {user[8][:10] if user[8] else 'Не указано'}

💡 Улучшайте свой рейтинг, ведя интересные беседы!
                """
            else:
                text = "❌ Анкета не найдена"
                
            # Check if the message has photo (from main menu)
            if query.message.photo:
                # Delete the photo message and send new text message
                await query.delete_message()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=Keyboards.back_to_menu()
                )
            else:
                await query.edit_message_text(text, reply_markup=Keyboards.back_to_menu())
        
        # Add to chat
        elif data == "add_to_chat":
            text = """
💬 Добавить в чат

🤖 Добавьте этого бота в групповой чат, чтобы участники могли:
• Знакомиться друг с другом
• Играть в игры
• Участвовать в мероприятиях

📋 Инструкция:
1. Добавьте бота в групповой чат
2. Выдайте боту права администратора
3. Участники смогут использовать команду /start

✨ Функция будет доступна в ближайшее время!
            """
            # Check if the message has photo (from main menu)
            if query.message.photo:
                # Delete the photo message and send new text message
                await query.delete_message()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=Keyboards.back_to_menu()
                )
            else:
                await query.edit_message_text(text, reply_markup=Keyboards.back_to_menu())
        
        # Friends
        elif data == "friends":
            await self.show_friends_menu(update, context)
        
        # Premium purchase options
        elif data.startswith("premium_"):
            option = data.replace("premium_", "")
            
            # Get dynamic pricing options from database
            pricing_options = self.db.get_active_subscription_plans_for_purchase()
            
            # Fallback to default hardcoded options if no plans in database
            if not pricing_options:
                logger.warning("No subscription plans found in database, using fallback options")
                pricing_options = {
                    "1day": {"title": "1 день Premium ⭐", "stars": 1, "days": 1, "description": "Один день полного доступа"},
                    "1week": {"title": "7 дней Premium ⭐", "stars": 7, "days": 7, "description": "Неделя полного доступа"}, 
                    "1month": {"title": "30 дней Premium ⭐", "stars": 25, "days": 30, "description": "Месяц полного доступа", "is_special": True}
                }
            
            # Try to find the option in database plans (with both formats for compatibility)
            option_data = None
            
            # First try exact match with the extracted option
            if option in pricing_options:
                option_data = pricing_options[option]
            else:
                # Try with premium_ prefix (for database plans)
                full_key = f"premium_{option}"
                if full_key in pricing_options:
                    option_data = pricing_options[full_key]
                else:
                    # Try without premium_ prefix (for fallback plans)
                    for key, data in pricing_options.items():
                        if key.replace('premium_', '') == option:
                            option_data = data
                            break
            
            if option_data:
                await self.send_stars_invoice(update, context, option, option_data)
            else:
                logger.warning(f"Premium option not found: {option}. Available options: {list(pricing_options.keys())}")
                text = "❌ Неизвестная опция премиум-подписки."
                # Check if the message has photo (from premium menu)
                if query.message.photo:
                    # Delete the photo message and send new text message
                    await query.delete_message()
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        reply_markup=Keyboards.back_to_menu()
                    )
                else:
                    await query.edit_message_text(text, reply_markup=Keyboards.back_to_menu())
        
        # Reset rating option
        elif data == "reset_rating":
            text = """
😊 Обнуление рейтинга

Вы выбрали обнуление рейтинга за 99 ⭐

💳 Оплата будет производиться через Telegram Stars.

⚠️ Функция оплаты будет доступна в следующем обновлении!

Обнуление рейтинга позволит вам начать с чистого листа.
            """
            
            # Check if the message has photo (from premium menu)
            if query.message.photo:
                # Delete the photo message and send new text message
                await query.delete_message()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=Keyboards.back_to_menu()
                )
            else:
                await query.edit_message_text(text, reply_markup=Keyboards.back_to_menu())
        
        # Get free premium
        elif data == "get_free_premium":
            try:
                current_user_referrals = self.db.get_referral_count(user_id)
                
                # Calculate VIP days earned
                vip_days_earned = current_user_referrals // 3
                
                text = f"""
💎 Получить бесплатный PREMIUM

🔗 Ваша реферальная ссылка:
https://t.me/{BOT_USERNAME}?start=u{user_id}

📊 Статистика:
• По вашей ссылке пришло: {current_user_referrals} пользователей
• Заработано VIP дней: {vip_days_earned}
• До следующего VIP дня: {3 - (current_user_referrals % 3)} пользователей

📝 Как это работает:
1. Отправьте ссылку друзьям
2. Они должны перейти по ссылке
3. Подписаться на каналы и зарегистрироваться
4. Каждые 3 друга = +1 день PREMIUM!

✨ Привлекайте друзей и получайте бесплатный PREMIUM!
                """
                
                # Check if the message has photo (from main menu)
                if query.message.photo:
                    # Delete the photo message and send new text message
                    await query.delete_message()
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        reply_markup=Keyboards.back_to_menu()
                    )
                else:
                    await query.edit_message_text(text, reply_markup=Keyboards.back_to_menu())
                    
            except Exception as e:
                logger.error(f"Error in get_free_premium handler: {e}")
                error_text = "❌ Произошла ошибка при загрузке реферальной информации. Попробуйте позже."
                
                # Check if the message has photo (from main menu)
                if query.message.photo:
                    # Delete the photo message and send new text message
                    await query.delete_message()
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=error_text,
                        reply_markup=Keyboards.back_to_menu()
                    )
                else:
                    await query.edit_message_text(error_text, reply_markup=Keyboards.back_to_menu())
        
        # Exit
        elif data == "exit":
            # Remove from queue if exists
            self.db.remove_from_queue(user_id)
            if user_id in self.search_filters:
                del self.search_filters[user_id]
            
            # End active chat if exists
            if user_id in self.active_chats:
                await self.end_chat(update, context)
            
            text = """
👋 До свидания! Выход из бота выполнен.

Для повторного использования отправьте команду /start.
            """
            # Check if the message has photo (from main menu)
            if query.message.photo:
                # Delete the photo message and send new text message
                await query.delete_message()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text
                )
            else:
                await query.edit_message_text(text)
        
        # FRIENDS SYSTEM HANDLERS
        # Add friend from rating screen
        elif data.startswith("add_friend_"):
            friend_id = int(data.replace("add_friend_", ""))
            await self.handle_add_friend(update, context, friend_id)
        
        # Friends menu handlers
        elif data == "friends_list":
            await self.show_friends_list(update, context)
        
        elif data == "friend_requests_in":
            await self.show_incoming_requests(update, context)
        
        elif data == "friend_requests_out":
            await self.show_outgoing_requests(update, context)
        
        # Friend request actions
        elif data.startswith("accept_friend_"):
            requester_id = int(data.replace("accept_friend_", ""))
            await self.handle_friend_response(update, context, requester_id, accept=True)
        
        elif data.startswith("decline_friend_"):
            requester_id = int(data.replace("decline_friend_", ""))
            await self.handle_friend_response(update, context, requester_id, accept=False)
        
        elif data.startswith("remove_friend_"):
            friend_id = int(data.replace("remove_friend_", ""))
            await self.handle_remove_friend(update, context, friend_id)
        
        # ADMIN HANDLERS
        elif data.startswith("admin_"):
            if not self.is_admin(user_id):
                await query.answer("У вас нет прав администратора!", show_alert=True)
                return
            await self.admin_handlers.handle_admin_callback(update, context, data)
    
    def is_admin(self, user_id):
        """Check if user is admin (checks both database admins and super admin)"""
        # Check if user is super admin (from environment variable)
        if user_id == SUPER_ADMIN_ID:
            return True
        
        # Check if user is regular admin (from database)
        return self.db.is_admin(user_id)
    
    def is_super_admin(self, user_id):
        """Check if user is super admin"""
        return user_id == SUPER_ADMIN_ID
    
    # ===== FRIENDS SYSTEM METHODS =====
    
    async def show_friends_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show friends main menu"""
        user_id = update.effective_user.id
        
        # Get friends statistics
        friends_count = self.db.get_friends_count(user_id)
        incoming_requests = self.db.get_incoming_friend_requests(user_id)
        outgoing_requests = self.db.get_outgoing_friend_requests(user_id)
        
        text = f"""
🚀 Друзья

👥 Список друзей: {friends_count}
📥 Входящие заявки: {len(incoming_requests)}
📤 Исходящие заявки: {len(outgoing_requests)}

Выберите действие:
        """
        
        # Handle photo messages that can't be edited
        if update.callback_query and update.callback_query.message.photo:
            await update.callback_query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=Keyboards.friends_main_menu()
            )
        elif update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.friends_main_menu())
        else:
            await update.message.reply_text(text, reply_markup=Keyboards.friends_main_menu())
    
    async def handle_add_friend(self, update: Update, context: ContextTypes.DEFAULT_TYPE, friend_id: int) -> None:
        """Handle adding friend from rating screen"""
        user_id = update.effective_user.id
        
        # Check if trying to add themselves
        if user_id == friend_id:
            await update.callback_query.answer("❌ Нельзя добавить себя в друзья!", show_alert=True)
            return
        
        # Check if friend exists
        friend = self.db.get_user(friend_id)
        if not friend:
            await update.callback_query.answer("❌ Пользователь не найден!", show_alert=True)
            return
        
        # Check existing friendship status
        status = self.db.get_friendship_status(user_id, friend_id)
        
        if status == 'accepted':
            await update.callback_query.answer("👥 Вы уже друзья!", show_alert=True)
            return
        elif status == 'pending':
            await update.callback_query.answer("📤 Заявка уже отправлена!", show_alert=True)
            return
        
        # Send friend request
        if user_id in self.user_states and 'rating_context' in self.user_states[user_id]:
            rating_context = self.user_states[user_id]['rating_context']
            session_id = rating_context['session_id']
        else:
            session_id = None
        
        success = self.db.send_friend_request(user_id, friend_id, session_id)
        
        if success:
            await update.callback_query.answer("✅ Заявка в друзья отправлена!", show_alert=True)
            
            # Notify the potential friend
            try:
                user = self.db.get_user(user_id)
                sender_name = user[2] if user[2] else "Пользователь"  # first_name
                
                await context.bot.send_message(
                    chat_id=friend_id,
                    text=f"👋 {sender_name} хочет добавить вас в друзья!\n\nПроверьте входящие заявки в разделе 'Друзья'.",
                    reply_markup=Keyboards.check_friend_requests()
                )
            except Exception as e:
                logger.error(f"Failed to notify friend {friend_id} about request: {e}")
        else:
            await update.callback_query.answer("❌ Ошибка при отправке заявки!", show_alert=True)
    
    async def show_friends_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1) -> None:
        """Show user's friends list with beautiful formatting"""
        user_id = update.effective_user.id
        page_size = 8  # Reduced for better readability
        
        friends = self.db.get_user_friends(user_id)
        
        if not friends:
            text = """
👥 **Список друзей**

💭 У вас пока нет друзей.

🤝 Друзья появляются после завершения чатов, когда вы отправляете заявку в друзья и собеседник её принимает.

✨ Начните общение и найдите новых друзей!
            """
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.back_to_friends(), parse_mode='Markdown')
            return
        
        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        friends_page = friends[start_idx:end_idx]
        total_pages = (len(friends) + page_size - 1) // page_size
        
        # Beautiful header with stats
        text = f"""
👥 **Список друзей** ({len(friends)})

═══════════════════════════
"""
        
        for idx, friend in enumerate(friends_page, start=start_idx + 1):
            # Unpack all fields: user_id, username, first_name, gender, age_group, rating, rating_count, friendship_date
            friend_id, username, friend_name, gender, age_group, rating, rating_count, friendship_date = friend
            
            # Format display name
            if friend_name:
                display_name = friend_name
                if len(display_name) > 20:
                    display_name = display_name[:17] + "..."
            else:
                display_name = f"Пользователь {friend_id}"
            
            # Gender emoji
            gender_emoji = {
                "erkak": "👨",
                "ayol": "👩", 
                "boshqa": "🚻"
            }.get(gender, "👤")
            
            # Age group display
            age_display = {
                "18_24": "18-24",
                "25_34": "25-34",
                "35_plus": "35+",
                "boshqa": "🎭"
            }.get(age_group, "❓")
            
            # Rating display
            if rating_count > 0:
                rating_stars = "⭐" * min(int(rating), 5)  # Max 5 stars
                rating_display = f"{rating_stars} {rating:.1f}"
            else:
                rating_display = "🆕 Новичок"
            
            # Format friendship date
            try:
                from datetime import datetime
                date_obj = datetime.strptime(friendship_date[:10], '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d.%m.%Y')
            except:
                formatted_date = friendship_date[:10]
            
            # Username display
            username_display = ""
            if username:
                username_display = f" (@{username})"
            
            # Beautiful friend card
            text += f"""
{gender_emoji} **{display_name}**{username_display}
📅 {age_display} лет  •  {rating_display}
💝 Дружим с {formatted_date}

"""
        
        # Footer with pagination
        text += "═══════════════════════════\n"
        if total_pages > 1:
            text += f"📄 Страница {page} из {total_pages}\n\n"
        
        text += "💡 *Нажмите на кнопки ниже для управления друзьями*"
        
        await update.callback_query.edit_message_text(
            text, 
            reply_markup=Keyboards.friends_list_menu(friends_page, page, total_pages),
            parse_mode='Markdown'
        )
    
    async def show_incoming_requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show incoming friend requests"""
        user_id = update.effective_user.id
        requests = self.db.get_incoming_friend_requests(user_id)
        
        if not requests:
            text = "📥 У вас нет входящих заявок в друзья."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.back_to_friends())
            return
        
        text = f"📥 Входящие заявки ({len(requests)}): \n\n"
        
        for idx, request in enumerate(requests, 1):
            requester_id, requester_name, request_date = request[:3]
            display_name = requester_name if requester_name else f"Пользователь {requester_id}"
            if len(display_name) > 15:
                display_name = display_name[:12] + "..."
            text += f"{idx}. {display_name} ({request_date[:10]})\n"
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=Keyboards.incoming_requests_menu(requests)
        )
    
    async def show_outgoing_requests(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show outgoing friend requests"""
        user_id = update.effective_user.id
        requests = self.db.get_outgoing_friend_requests(user_id)
        
        if not requests:
            text = "📤 У вас нет исходящих заявок в друзья."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.back_to_friends())
            return
        
        text = f"📤 Исходящие заявки ({len(requests)}): \n\n"
        
        for idx, request in enumerate(requests, 1):
            friend_id, friend_name, request_date = request[:3]
            display_name = friend_name if friend_name else f"Пользователь {friend_id}"
            if len(display_name) > 15:
                display_name = display_name[:12] + "..."
            text += f"{idx}. {display_name} ({request_date[:10]})\n"
        
        text += "\n⏳ Ожидание ответа..."
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=Keyboards.back_to_friends()
        )
    
    async def handle_friend_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, requester_id: int, accept: bool) -> None:
        """Handle friend request response (accept/decline)"""
        user_id = update.effective_user.id
        
        if accept:
            success = self.db.accept_friend_request(requester_id, user_id)
            if success:
                await update.callback_query.answer("✅ Заявка принята! Теперь вы друзья!", show_alert=True)
                
                # Notify the requester
                try:
                    user = self.db.get_user(user_id)
                    accepter_name = user[2] if user[2] else "Пользователь"
                    
                    await context.bot.send_message(
                        chat_id=requester_id,
                        text=f"🎉 {accepter_name} принял(а) вашу заявку в друзья!\n\nТеперь вы можете найти их в своем списке друзей."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify requester {requester_id}: {e}")
            else:
                await update.callback_query.answer("❌ Ошибка при принятии заявки!", show_alert=True)
        else:
            success = self.db.decline_friend_request(requester_id, user_id)
            if success:
                await update.callback_query.answer("❌ Заявка отклонена!", show_alert=True)
            else:
                await update.callback_query.answer("❌ Ошибка при отклонении заявки!", show_alert=True)
        
        # Refresh the incoming requests view
        await self.show_incoming_requests(update, context)
    
    async def handle_remove_friend(self, update: Update, context: ContextTypes.DEFAULT_TYPE, friend_id: int) -> None:
        """Handle removing a friend"""
        user_id = update.effective_user.id
        
        success = self.db.remove_friend(user_id, friend_id)
        
        if success:
            await update.callback_query.answer("💔 Друг удален из списка!", show_alert=True)
            
            # Optionally notify the removed friend
            try:
                user = self.db.get_user(user_id)
                remover_name = user[2] if user[2] else "Пользователь"
                
                await context.bot.send_message(
                    chat_id=friend_id,
                    text=f"💔 {remover_name} удалил(а) вас из друзей."
                )
            except Exception as e:
                logger.error(f"Failed to notify removed friend {friend_id}: {e}")
        else:
            await update.callback_query.answer("❌ Ошибка при удалении друга!", show_alert=True)
        
        # Refresh the friends list
        await self.show_friends_list(update, context)
    
    async def check_user_subscription(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, mandatory_channels: list) -> bool:
        """Check if user is subscribed to all mandatory channels"""
        if not mandatory_channels:
            return True
        
        for channel in mandatory_channels:
            try:
                member = await context.bot.get_chat_member(channel, user_id)
                if member.status in ['left', 'kicked']:
                    return False
            except Exception as e:
                logger.error(f"Error checking channel {channel}: {e}")
                return False
        
        return True
    
    async def show_subscription_required(self, update: Update, context: ContextTypes.DEFAULT_TYPE, mandatory_channels: list):
        """Show subscription required message"""
        text = """
📍 Для использования бота, вы должны быть подписаны на наш канал:
        """
        # Create inline keyboard with channel buttons
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard_buttons = []
        
        # Add channel buttons
        for channel in mandatory_channels:
            # Remove @ symbol if present for clean display
            channel_name = channel.replace('@', '')
            keyboard_buttons.append([InlineKeyboardButton(f"📺 {channel_name}", url=f"https://t.me/{channel_name}")])
        
        # Add subscription check button
        keyboard_buttons.append([InlineKeyboardButton("👍 Я подписался", callback_data="check_channels")])
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
    
    async def show_top_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show TOP users leaderboard with real data from database"""
        try:
            # Get top users from database (based on total chat time or rating)
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT u.user_id, u.first_name, u.username, u.rating, u.rating_count, u.gender, u.age_group
                    FROM users u
                    WHERE u.rating_count >= 1 AND u.is_active = 1
                    ORDER BY u.rating DESC, u.rating_count DESC
                    LIMIT 10
                ''')
                top_users = cursor.fetchall()
            
            # Create the text matching the design from the image
            text = "Проведи в диалогах больше времени чем остальные и получи\n"
            text += "приз — подписку 💎 PREMIUM\n\n"
            
            text += "Участие принимают все автоматически, период проведения\n"
            text += "розыгрыша каждую неделю с понедельника по воскресенье\n\n"
            
            text += "Подведение итогов и раздача приза каждое воскресенье в 20:00\n"
            text += "по МСК.\n\n"
            
            text += "Призы:\n"
            text += "🥇 1 место — бесплатная подписка на 3 дня\n"
            text += "🥈 2 место — бесплатная подписка на 2 дня\n"
            text += "🥉 3 место — бесплатная подписка на 1 день\n\n"
            
            text += "Текущие лидеры:\n"
            if top_users:
                # Show only first user like in the image
                user_data = top_users[0]
                user_id_leader, first_name, username, rating, rating_count, gender, age_group = user_data
                
                # Format user name
                display_name = first_name or "Пользователь"
                if len(display_name) > 15:
                    display_name = display_name[:12] + "..."
                
                # Use rating_count as time in seconds (placeholder) 
                time_seconds = 1  # Default to 1 second as shown in image
                text += f"1. {display_name} — в диалогах {time_seconds} секунду\n"
            else:
                text += "1. Ннррп — в диалогах 1 секунду\n"
            
            text += "\n⚠️ \"Фарм\" времени запрещен, а аккаунты с подозрительно\n"
            text += "низким количеством диалогов и отправленных сообщений\n"
            text += "будут заблокированы в нашем боте и удалены из ТОПа."
            
            # Path to the TOP image file
            photo_path = "picture/top.jpg"
            
            try:
                # Send photo with caption and back button
                with open(photo_path, 'rb') as photo:
                    # Delete the old message first if it exists
                    if update.callback_query.message.photo:
                        await update.callback_query.delete_message()
                    
                    # Send new photo message
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo,
                        caption=text,
                        reply_markup=Keyboards.top_users_menu()
                    )
            except FileNotFoundError:
                logger.error(f"Image file {photo_path} not found")
                # Fallback to text only
                if update.callback_query.message.photo:
                    await update.callback_query.delete_message()
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        reply_markup=Keyboards.back_to_menu()
                    )
                else:
                    await update.callback_query.edit_message_text(text, reply_markup=Keyboards.back_to_menu())
            except Exception as e:
                logger.error(f"Error sending TOP users with photo: {e}")
                # Fallback to text only
                if update.callback_query.message.photo:
                    await update.callback_query.delete_message()
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        reply_markup=Keyboards.back_to_menu()
                    )
                else:
                    await update.callback_query.edit_message_text(text, reply_markup=Keyboards.back_to_menu())
        
        except Exception as e:
            logger.error(f"Error in show_top_users: {e}")
            # Fallback error message
            error_text = "❌ Произошла ошибка при загрузке ТОПа. Попробуйте позже."
            if update.callback_query.message.photo:
                await update.callback_query.delete_message()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=error_text,
                    reply_markup=Keyboards.back_to_menu()
                )
            else:
                await update.callback_query.edit_message_text(error_text, reply_markup=Keyboards.back_to_menu())
    
    async def send_stars_invoice(self, update: Update, context: ContextTypes.DEFAULT_TYPE, option: str, option_data: dict) -> None:
        """Send Telegram Stars invoice for premium purchase"""
        user_id = update.effective_user.id
        
        # Store payment context
        if user_id not in self.user_states:
            self.user_states[user_id] = {}
        self.user_states[user_id]['payment_context'] = {
            'option': option,
            'option_data': option_data
        }
        
        try:
            # Send invoice
            await context.bot.send_invoice(
                chat_id=user_id,
                title=f"💎 {option_data['title']}",
                description=f"Получите {option_data['title']} для вашего аккаунта! Преимум возможности: поиск по полу, Пошлома чат, обмен фото/видео и многое другое!",
                payload=f"premium_{option}_{user_id}_{option_data['stars']}",
                provider_token="",  # Empty for Telegram Stars
                currency="XTR",  # Telegram Stars currency
                prices=[
                    LabeledPrice(label=option_data['title'], amount=option_data['stars'])
                ],
                start_parameter=f"premium_{option}",
                photo_url="https://via.placeholder.com/512x512/4267B2/FFFFFF?text=VIP",
                photo_size=512,
                photo_width=512,
                photo_height=512,
                need_name=False,
                need_phone_number=False,
                need_email=False,
                need_shipping_address=False,
                send_phone_number_to_provider=False,
                send_email_to_provider=False,
                is_flexible=False
            )
            
            # Inform user about the invoice
            text = f"""
💎 Оплата PREMIUM

Вы выбрали: {option_data['title']} за {option_data['stars']} ⭐

💳 Для оплаты нажмите на кнопку \"Оплатить\" в сообщении выше.

✨ После успешной оплаты VIP будет активирован автоматически!
            """
            
            # Handle photo messages that can't be edited
            try:
                if update.callback_query.message.photo:
                    # Delete the photo message and send new text message
                    await update.callback_query.delete_message()
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        reply_markup=Keyboards.back_to_menu()
                    )
                else:
                    await update.callback_query.edit_message_text(text, reply_markup=Keyboards.back_to_menu())
            except Exception as edit_e:
                logger.error(f"Error editing invoice message: {edit_e}")
                # Fallback: delete and send new message
                try:
                    await update.callback_query.delete_message()
                except Exception:
                    pass
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=Keyboards.back_to_menu()
                )
            
        except Exception as e:
            logger.error(f"Error sending Stars invoice: {e}")
            error_text = "❌ Ошибка при создании счета для оплаты. Попробуйте позже."
            
            # Handle photo messages for error case too
            try:
                if update.callback_query.message.photo:
                    # Delete the photo message and send new text message
                    await update.callback_query.delete_message()
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=error_text,
                        reply_markup=Keyboards.back_to_menu()
                    )
                else:
                    await update.callback_query.edit_message_text(error_text, reply_markup=Keyboards.back_to_menu())
            except Exception as error_edit_e:
                logger.error(f"Error editing error message: {error_edit_e}")
                # Final fallback: delete and send new message
                try:
                    await update.callback_query.delete_message()
                except Exception:
                    pass
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=error_text,
                    reply_markup=Keyboards.back_to_menu()
                )
    
    async def handle_pre_checkout_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle pre-checkout query for Telegram Stars payments"""
        query = update.pre_checkout_query
        
        # Verify the payload
        payload_parts = query.invoice_payload.split('_')
        if len(payload_parts) >= 4 and payload_parts[0] == 'premium':
            # Answer OK to proceed with payment
            await query.answer(ok=True)
        else:
            # Answer with error
            await query.answer(
                ok=False,
                error_message="Неверные данные платежа. Попробуйте снова."
            )
    
    async def handle_successful_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle successful payment and activate premium"""
        user_id = update.effective_user.id
        payment = update.message.successful_payment
        
        logger.info(f"Payment successful for user {user_id}: {payment.invoice_payload}")
        
        # Parse payload
        payload_parts = payment.invoice_payload.split('_')
        if len(payload_parts) >= 4 and payload_parts[0] == 'premium':
            option = payload_parts[1]
            paid_user_id = int(payload_parts[2])
            stars_amount = int(payload_parts[3])
            
            # Verify user ID matches
            if user_id != paid_user_id:
                logger.error(f"User ID mismatch in payment: {user_id} vs {paid_user_id}")
                await update.message.reply_text("❌ Ошибка проверки платежа!")
                return
            
            # Get payment context
            payment_context = None
            if user_id in self.user_states and 'payment_context' in self.user_states[user_id]:
                payment_context = self.user_states[user_id]['payment_context']
                del self.user_states[user_id]['payment_context']
            
            # Determine VIP days
            vip_days = 1  # Default
            if payment_context:
                option_data = payment_context['option_data']
                if option_data['days'] == "random":
                    # Roulette - random between 1-30 days
                    vip_days = random.randint(1, 30)
                    roulette_text = f" (выпало {vip_days} дней!)"
                else:
                    vip_days = option_data['days']
                    roulette_text = ""
            else:
                roulette_text = ""
            
            # Add VIP days to user account in database
            success = self.db.add_premium_days(user_id, vip_days)
            
            if not success:
                logger.error(f"Failed to add premium days to user {user_id}")
                await update.message.reply_text("❌ Ошибка активации премиум подписки! Обратитесь к администратору.")
                return
            
            logger.info(f"User {user_id} received {vip_days} VIP days for option {option}")
            
            # Send success message
            success_text = f"""
✅ Оплата успешна!

🎉 Поздравляем! Вы получили VIP на {vip_days} дней{roulette_text}!

✨ Ваш VIP статус активирован и готов к использованию!

💎 Преимум возможности:
• Поиск по полу
• Пошлома чат 🔞
• Обмен фото/видео
• Мгновенный поиск
• Нет рекламы
• Не нужно подписываться на каналы

Приятного общения! 🚀
            """
            
            await update.message.reply_text(success_text, reply_markup=Keyboards.main_menu())
            
        else:
            logger.error(f"Invalid payment payload: {payment.invoice_payload}")
            await update.message.reply_text("❌ Ошибка обработки платежа!")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enhanced error handler with specific error type handling and color logging"""
    error = context.error
    error_type = type(error).__name__
    
    # 🔴 Handle specific Telegram API errors
    if isinstance(error, BadRequest):
        error_message = str(error)
        
        # Check for "Message is not modified" error - this is not critical
        if "Message is not modified" in error_message:
            log_error(f"⚠️ SUPPRESSED: Message not modified error for update {update.update_id if update else 'unknown'}: {error_message}")
            # Don't notify user, this is expected behavior
            return
        
        # Check for "Query is too old" error - also not critical
        elif "Query is too old" in error_message:
            log_error(f"⚠️ SUPPRESSED: Query too old error for update {update.update_id if update else 'unknown'}: {error_message}")
            # Don't notify user
            return
        
        # Check for "Message can't be edited" error
        elif "Message can't be edited" in error_message:
            log_error(f"⚠️ Message edit failed for update {update.update_id if update else 'unknown'}: {error_message}")
            # Try to send a new message instead
            try:
                if update and update.effective_chat:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="🔄 Обновляем интерфейс..."
                    )
            except Exception as fallback_error:
                log_error(f"Fallback message also failed: {fallback_error}")
            return
        
        # Other BadRequest errors are more serious
        log_error(f"TELEGRAM BAD REQUEST: {error_message}", exc_info=True)
        
    elif isinstance(error, TimedOut):
        log_error(f"TELEGRAM TIMEOUT: {error}", exc_info=True)
        # Don't notify user for timeouts, they're usually temporary
        return
        
    elif isinstance(error, NetworkError):
        log_error(f"TELEGRAM NETWORK ERROR: {error}", exc_info=True)
        # Don't notify user for network errors, they're usually temporary
        return
        
    else:
        # Log all other errors as critical with full stack trace
        log_error(f"CRITICAL ERROR ({error_type}): {error}", exc_info=True)
    
    # Try to inform the user about serious errors only
    try:
        if update and update.effective_chat:
            error_message = "⚠️ Произошла ошибка. Попробуйте позже или обратитесь к администратору."
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_message
            )
    except Exception as e:
        log_error(f"Failed to send error message to user: {e}")

async def security_cleanup(context):
    """Periodic security cleanup task"""
    bot = context.bot_data.get('bot_instance')
    if bot:
        bot.security.cleanup_old_data()
        # Clean inactive queue entries
        removed_count = bot.db.clear_inactive_queue(hours=2)
        if removed_count > 0:
            logger.info(f"Cleaned {removed_count} inactive queue entries")
        
        # Clean up expired premium subscriptions
        expired_count = bot.db.cleanup_expired_premium()
        if expired_count > 0:
            logger.info(f"Cleaned {expired_count} expired premium subscriptions")

def main():
    """Start the bot"""
    # Create application with job queue enabled
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create bot instance
    bot = ChatBot()
    
    # Store bot instance for cleanup tasks
    application.bot_data['bot_instance'] = bot
    
    # Add periodic cleanup task (every hour) if job_queue is available
    if application.job_queue:
        application.job_queue.run_repeating(
            callback=security_cleanup,
            interval=3600,  # 1 hour
            first=60  # Start after 1 minute
        )
    else:
        logger.warning("JobQueue not available, periodic cleanup disabled")
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("admin", bot.admin_command))
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    
    # Payment handlers
    application.add_handler(PreCheckoutQueryHandler(bot.handle_pre_checkout_query))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, bot.handle_successful_payment))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, bot.handle_message))
    application.add_handler(MessageHandler(filters.VIDEO, bot.handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, bot.handle_message))
    application.add_handler(MessageHandler(filters.VOICE, bot.handle_message))
    application.add_handler(MessageHandler(filters.Sticker.ALL, bot.handle_message))
    
    # Start the bot
    logger.info("Bot started with security features enabled!")
    application.run_polling()

if __name__ == '__main__':
    main()
