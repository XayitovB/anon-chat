import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import Keyboards
from admin_panel import AdminPanel
from config import SUPER_ADMIN_ID

logger = logging.getLogger(__name__)

# Custom error logging function with red color emphasis
def log_error(message, exc_info=None):
    """Log error messages in red for better visibility"""
    logger.error(f"🔴 {message}", exc_info=exc_info)

class AdminHandlers:
    def __init__(self, db, bot_instance):
        self.db = db
        self.bot = bot_instance
        self.admin_panel = AdminPanel()
    
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
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle admin callback queries"""
        query = update.callback_query
        user_id = update.effective_user.id
        
        if data == "admin_menu":
            await self.show_admin_menu(update, context)
        
        # Users management
        elif data == "admin_users":
            await self.show_users_menu(update, context)
        elif data == "admin_all_users":
            await self.show_all_users(update, context, page=1)
        elif data.startswith("admin_all_users_"):
            page = int(data.split("_")[-1])
            await self.show_all_users(update, context, page)
        elif data == "admin_active_users":
            await self.show_active_users(update, context)
        elif data == "admin_search_user":
            await self.prompt_search_user(update, context)
        elif data.startswith("admin_user_details_"):
            user_to_view = int(data.split("_")[-1])
            await self.show_user_details(update, context, user_to_view)
        
        # Broadcast
        elif data == "admin_broadcast":
            await self.show_broadcast_menu(update, context)
        elif data == "admin_broadcast_all":
            await self.prompt_broadcast_message(update, context, "all")
        elif data == "admin_broadcast_male":
            await self.prompt_broadcast_message(update, context, "male")
        elif data == "admin_broadcast_female":
            await self.prompt_broadcast_message(update, context, "female")
        
        # Channel management
        elif data == "admin_channels":
            await self.show_channels_menu(update, context)
        elif data == "admin_list_channels":
            await self.show_channels_list(update, context)
        elif data == "admin_add_channel":
            await self.prompt_add_channel(update, context)
        elif data == "admin_remove_channel":
            await self.prompt_remove_channel(update, context)
        
        # Reports only (keeping reports viewing functionality)
        elif data == "admin_reports":
            await self.show_reports(update, context)
        
        # Statistics
        elif data == "admin_stats":
            await self.show_stats_menu(update, context)
        elif data == "admin_user_stats":
            await self.show_user_statistics(update, context)
        elif data == "admin_chat_stats":
            await self.show_chat_statistics(update, context)
        elif data == "admin_rating_stats":
            await self.show_rating_statistics(update, context)
        elif data == "admin_queue_stats":
            await self.show_queue_statistics(update, context)
        elif data == "admin_full_report":
            await self.show_full_report(update, context)
        elif data == "admin_activity_analytics":
            await self.show_activity_analytics(update, context)
        
        # Premium management
        elif data == "admin_premium":
            await self.show_premium_menu(update, context)
        elif data == "admin_premium_list":
            await self.show_premium_users_list(update, context, page=1)
        elif data.startswith("admin_premium_list_"):
            page = int(data.split("_")[-1])
            await self.show_premium_users_list(update, context, page)
        elif data == "admin_add_premium":
            await self.prompt_add_premium(update, context)
        elif data == "admin_remove_premium":
            await self.prompt_remove_premium(update, context)
        elif data.startswith("admin_premium_details_"):
            premium_user_id = int(data.split("_")[-1])
            await self.show_premium_user_details(update, context, premium_user_id)
        
        # Subscription plans management
        elif data == "admin_plans":
            await self.show_plans_menu(update, context)
        elif data == "admin_plans_list":
            await self.show_plans_list(update, context)
        elif data == "admin_add_plan":
            await self.prompt_add_plan(update, context)
        elif data == "admin_edit_plan":
            await self.prompt_edit_plan(update, context)
        elif data.startswith("admin_plan_action_"):
            plan_id = int(data.split("_")[-1])
            await self.show_plan_actions(update, context, plan_id)
        elif data.startswith("admin_plan_edit_"):
            plan_id = int(data.split("_")[-1])
            await self.prompt_edit_plan_details(update, context, plan_id)
        elif data.startswith("admin_plan_delete_"):
            plan_id = int(data.split("_")[-1])
            await self.confirm_delete_plan(update, context, plan_id)
        elif data == "admin_quick_edit_plans":
            await self.show_quick_edit_plans(update, context)
        elif data == "admin_quick_delete_plans":
            await self.show_quick_delete_plans(update, context)
        elif data.startswith("admin_quick_edit_"):
            plan_id = int(data.split("_")[-1])
            await self.start_quick_edit(update, context, plan_id)
        elif data.startswith("admin_quick_delete_"):
            plan_id = int(data.split("_")[-1])
            await self.quick_delete_plan(update, context, plan_id)
        elif data.startswith("admin_confirm_delete_"):
            plan_id = int(data.split("_")[-1])
            await self.execute_quick_delete(update, context, plan_id)
        elif data == "admin_seed_plans":
            await self.seed_default_plans(update, context)
        elif data.startswith("admin_plan_toggle_"):
            plan_id = int(data.split("_")[-1])
            await self.toggle_plan_active(update, context, plan_id)
        
        # Admin management
        elif data == "admin_manage":
            if not self.is_super_admin(user_id):
                await query.answer("Только супер-админ может просматривать этот раздел!", show_alert=True)
                return
            await self.show_admin_manage_menu(update, context)
        elif data == "admin_list_admins":
            await self.show_admins_list(update, context)
        elif data == "admin_add_admin":
            await self.prompt_add_admin(update, context)
        elif data == "admin_remove_admin":
            await self.prompt_remove_admin(update, context)
    
    async def show_admin_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin main menu"""
        text = """
👑 Админ-панель

Выберите один из разделов:
        """
        # Check if the message has photo (from main menu)
        if update.callback_query.message.photo:
            # Delete the photo message and send new text message
            await update.callback_query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=Keyboards.admin_main_menu()
            )
        else:
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_main_menu())
    
    async def show_users_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show users management menu"""
        text = """
👥 Управление пользователями

Выберите одно из следующих действий:
        """
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_users_menu())
    
    async def show_all_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page=1):
        """Show paginated list of all users"""
        users_data = self.db.get_all_users(page=page, per_page=10)
        
        if not users_data or not users_data['users']:
            text = "❌ Пользователи не найдены."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        text = f"👥 Все пользователи (Страница {page}/{users_data['total_pages']})\n\n"
        
        for user in users_data['users']:
            user_id, username, first_name, gender, age_group, rating, rating_count, is_active, is_premium, premium_until, registered_at = user
            status = "✅ Активен" if is_active else "❌ Заблокирован"
            rating_text = f"⭐ {rating:.1f}" if rating_count > 0 else "Без рейтинга"
            
            # Determine premium status
            premium_status = "💎 PREMIUM" if is_premium else "⚡ SIMPLE"
            
            name = first_name or "Имя отсутствует"
            username_text = f"@{username}" if username else "Нет username"
            
            text += f"👤 {name}\n"
            text += f"📱 {username_text}\n"
            text += f"🆔 ID: {user_id}\n"
            text += f"📊 {rating_text} | {status}\n"
            text += f"💳 {premium_status}\n"
            text += f"⏰ {registered_at[:10]}\n\n"
        
        keyboard = Keyboards.admin_pagination(page, users_data['total_pages'], "admin_all_users")
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    
    async def show_active_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show currently active users"""
        active_data = self.db.get_active_users()
        
        if not active_data:
            text = "❌ Ошибка при получении данных."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        chat_users = active_data.get('chat_users', [])
        queue_users = active_data.get('queue_users', [])
        
        text = "📊 Активные пользователи\n\n"
        
        if chat_users:
            text += "💬 В чате ({}чел):\n".format(len(chat_users))
            for user in chat_users[:10]:  # Show first 10
                name = user[2] or "Имя отсутствует"
                username = f"@{user[1]}" if user[1] else "Нет username"
                text += f"• {name} ({username}) - ID: {user[0]}\n"
            if len(chat_users) > 10:
                text += f"... и еще {len(chat_users) - 10}\n"
            text += "\n"
        
        if queue_users:
            text += "🔍 В очереди ({}чел):\n".format(len(queue_users))
            for user in queue_users[:10]:  # Show first 10
                name = user[2] or "Имя отсутствует"
                username = f"@{user[1]}" if user[1] else "Нет username"
                text += f"• {name} ({username}) - ID: {user[0]}\n"
            if len(queue_users) > 10:
                text += f"... и еще {len(queue_users) - 10}\n"
        
        if not chat_users and not queue_users:
            text += "📭 Активных пользователей сейчас нет."
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def show_broadcast_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show broadcast menu"""
        text = """
📢 Рассылка сообщений

Кому вы хотите отправить сообщение?
        """
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_broadcast_menu())
    
    async def prompt_broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, target_type: str):
        """Prompt admin to enter broadcast message"""
        target_names = {
            "all": "Всем пользователям",
            "male": "Мужчинам",
            "female": "Женщинам"
        }
        
        text = f"""
📢 {target_names.get(target_type, "Отправить сообщение")}

Отправьте сообщение, которое хотите разослать.
        """
        
        # Store broadcast context
        context.user_data['broadcast_target'] = target_type
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def show_channels_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show channels management menu"""
        text = """
📌 Управление обязательными каналами

Выберите одно из следующих действий:
        """
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_channels_menu())
    
    async def show_channels_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show list of mandatory channels"""
        mandatory_channels = self.db.get_mandatory_channels()
        
        text = "📜 Список обязательных каналов:\n\n"
        
        if mandatory_channels:
            for i, channel in enumerate(mandatory_channels, 1):
                text += f"{i}. {channel}\n"
        else:
            text += "❌ Обязательные каналы отсутствуют."
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    
    async def show_reports(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user reports"""
        reports = self.db.get_all_reports()
        
        text = "⚠️ Foydalanuvchi shikoyatlari:\n\n"
        
        if reports:
            for report in reports[:20]:  # Show first 20
                report_id, reporter_id, reporter_name, reported_id, reported_name, reason, created_at = report
                reporter_display = reporter_name or "Ism yo'q"
                reported_display = reported_name or "Ism yo'q"
                text += f"📋 Shikoyat #{report_id}\n"
                text += f"👤 Shikoyatchi: {reporter_display} ({reporter_id})\n"
                text += f"🎯 Shikoyat qilingan: {reported_display} ({reported_id})\n"
                text += f"📝 Sabab: {reason}\n"
                text += f"⏰ {created_at[:16]}\n\n"
                
                if len(text) > 3500:  # Telegram message limit
                    break
        else:
            text += "📭 Shikoyatlar yo'q."
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def show_stats_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show statistics menu"""
        text = """
📊 Раздел статистики

Какую статистику вы хотите посмотреть?
        """
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_stats_menu())
    
    async def show_user_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show comprehensive user statistics"""
        stats = self.admin_panel.get_user_stats()
        
        if not stats:
            text = "❌ Ошибка при получении статистики."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        # Create comprehensive statistics text
        text = f"""
👥 Подробная статистика пользователей

📊 Общие показатели:
• Всего: {stats.get('total_users', 0)}
• Активных: {stats.get('active_users', 0)}
• Заблокированных: {stats.get('banned_users', 0)}
• Premium: {stats.get('premium_users', 0)}

📈 Новые регистрации:
• За 24ч: {stats.get('new_users_24h', 0)}
• За 7 дней: {stats.get('new_users_7d', 0)}
• За 30 дней: {stats.get('new_users_30d', 0)}

👨👩 По полу:
"""
        
        # Display gender distribution with percentages
        if 'gender_distribution' in stats and stats['gender_distribution']:
            for gender, data in stats['gender_distribution'].items():
                gender_emoji = {"erkak": "👨", "ayol": "👩", "boshqa": "⚖️"}.get(gender, "❓")
                gender_name = {"erkak": "Мужчины", "ayol": "Женщины", "boshqa": "Другое"}.get(gender, gender.title())
                if isinstance(data, dict):
                    text += f"{gender_emoji} {gender_name}: {data['count']} ({data['percentage']}%)\n"
                else:
                    text += f"{gender_emoji} {gender_name}: {data}\n"
        else:
            text += "• Данные недоступны\n"
        
        text += "\n📅 По возрасту:\n"
        if 'age_distribution' in stats and stats['age_distribution']:
            for age, data in stats['age_distribution'].items():
                if isinstance(data, dict):
                    text += f"• {age}: {data['count']} ({data['percentage']}%)\n"
                else:
                    text += f"• {age}: {data}\n"
        else:
            text += "• Данные недоступны\n"
        
        # Additional statistics
        text += f"\n🎆 Активность:\n"
        text += f"• С оценками: {stats.get('users_with_ratings', 0)}\n"
        text += f"• Никогда не общались: {stats.get('users_never_chatted', 0)}\n"
        text += f"• Ср. рейтинг: {stats.get('avg_user_rating', 0)}/5\n"
        
        # Check if message is too long and split if necessary
        if len(text) > 4000:  # Telegram message limit
            # Send first part
            await update.callback_query.edit_message_text(text[:4000] + "...", reply_markup=Keyboards.admin_back())
            return
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def show_chat_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show chat statistics"""
        stats = self.admin_panel.get_chat_stats()
        
        if not stats:
            text = "❌ Ошибка при получении статистики."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        text = f"""
💬 Статистика чатов

📊 Всего сессий: {stats.get('total_sessions', 'Недоступно')}
🟢 Активные сессии: {stats.get('active_sessions', 'Недоступно')}
📈 За 24 часа: {stats.get('recent_sessions', 'Недоступно')}
⏱ Средняя продолжительность: {stats.get('avg_duration_minutes', 'Недоступно')} мин
        """
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def show_rating_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show rating statistics"""
        stats = self.admin_panel.get_rating_stats()
        
        if not stats:
            text = "❌ Ошибка при получении статистики."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        text = f"""
⭐ Статистика рейтингов

📊 Всего оценок: {stats.get('total_ratings', 'Недоступно')}
📈 Средняя оценка: {stats.get('average_rating', 'Недоступно')}/5

🏆 Топ-пользователи:
"""
        
        if 'top_users' in stats and stats['top_users']:
            for user in stats['top_users'][:5]:
                user_id, first_name, rating, rating_count = user
                name = first_name or "Имя отсутствует"
                text += f"• {name}: ⭐{rating:.1f} ({rating_count} оценок)\n"
        else:
            text += "• Нет данных\n"
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def show_queue_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show queue statistics"""
        stats = self.admin_panel.get_queue_status()
        
        if not stats:
            text = "❌ Ошибка при получении статистики."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        text = f"""
🔍 Состояние очереди

👥 В очереди: {stats.get('total_in_queue', 'Недоступно')} пользователей

📊 По полу:
"""
        
        if 'gender_queue_distribution' in stats:
            for gender_filter, count in stats['gender_queue_distribution'].items():
                filter_name = {
                    "erkak": "Мужчины",
                    "ayol": "Женщины",
                    "farqi_yoq": "Не важно"
                }.get(gender_filter, gender_filter)
                text += f"• {filter_name}: {count}\n"
        else:
            text += "• Нет данных\n"
        
        text += "\n📅 По возрасту:\n"
        if 'age_queue_distribution' in stats:
            for age_filter, count in stats['age_queue_distribution'].items():
                text += f"• {age_filter}: {count}\n"
        else:
            text += "• Нет данных\n"
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def show_full_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show full statistics report"""
        user_stats = self.admin_panel.get_user_stats()
        chat_stats = self.admin_panel.get_chat_stats()
        rating_stats = self.admin_panel.get_rating_stats()
        queue_stats = self.admin_panel.get_queue_status()
        
        text = f"""
📊 Общий отчет

👥 ПОЛЬЗОВАТЕЛИ:
• Всего: {user_stats.get('total_users') if user_stats else 'Недоступно'}
• Активных: {user_stats.get('active_users') if user_stats else 'Недоступно'}

💬 ЧАТЫ:
• Всего: {chat_stats.get('total_sessions') if chat_stats else 'Недоступно'}
• Активных: {chat_stats.get('active_sessions') if chat_stats else 'Недоступно'}

⭐ РЕЙТИНГИ:
• Всего: {rating_stats.get('total_ratings') if rating_stats else 'Недоступно'}
• Средняя: {rating_stats.get('average_rating') if rating_stats else 'Недоступно'}/5

🔍 ОЧЕРЕДЬ:
• Сейчас: {queue_stats.get('total_in_queue') if queue_stats else 'Недоступно'}
        """
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def show_activity_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed activity analytics"""
        stats = self.admin_panel.get_user_stats()
        
        if not stats:
            text = "❌ Ошибка при получении данных аналитики."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        text = f"""
🔍 Аналитика активности пользователей

📈 Регистрации по дням (последние 7 дней):
"""
        
        # Registration trends
        if 'registration_trends' in stats and stats['registration_trends']:
            for trend in stats['registration_trends']:
                date_str = trend['date']
                registrations = trend['registrations']
                bar = "█" * min(registrations, 10)  # Visual bar
                text += f"{date_str}: {registrations} {bar}\n"
        else:
            text += "• Данные недоступны\n"
        
        text += f"\n⏰ Пиковые часы регистрации:\n"
        if 'peak_registration_hours' in stats and stats['peak_registration_hours']:
            for hour, count in stats['peak_registration_hours']:
                text += f"• {hour}:00 - {count} регистраций\n"
        else:
            text += "• Данные недоступны\n"
        
        # Most active users
        text += f"\n🏆 Самые активные пользователи:\n"
        if 'most_active_users' in stats and stats['most_active_users']:
            for user_data in stats['most_active_users'][:5]:
                user_id, first_name, username, chat_count = user_data
                name = first_name or "Имя скрыто"
                username_display = f"@{username}" if username else "No username"
                text += f"• {name} ({username_display}): {chat_count} чатов\n"
        else:
            text += "• Данные недоступны\n"
        
        # Engagement metrics
        total_users = stats.get('total_users', 0)
        users_with_ratings = stats.get('users_with_ratings', 0)
        users_never_chatted = stats.get('users_never_chatted', 0)
        
        if total_users > 0:
            engagement_rate = ((total_users - users_never_chatted) / total_users) * 100
            rating_participation = (users_with_ratings / total_users) * 100
            
            text += f"\n📊 Показатели вовлеченности:\n"
            text += f"• Общение: {engagement_rate:.1f}% пользователей\n"
            text += f"• Оценивание: {rating_participation:.1f}% пользователей\n"
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def show_admin_manage_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin management menu"""
        text = """
👑 Управление администраторами

Выберите одно из следующих действий:
        """
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_manage_menu())
    
    async def show_admins_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed list of admins from database"""
        from datetime import datetime
        
        text = "👑 СПИСОК АДМИНИСТРАТОРОВ\n"
        text += "═" * 30 + "\n\n"
        
        # Get admins from database
        db_admins = self.db.get_all_admins()
        
        # Count total admins (super admin + database admins)
        total_admins = 1 if SUPER_ADMIN_ID else 0  # Super admin
        total_admins += len(db_admins)  # Database admins
        
        text += f"📊 Всего администраторов: {total_admins}\n\n"
        
        # Super Admin section
        if SUPER_ADMIN_ID:
            text += "🔥 СУПЕР АДМИНИСТРАТОР:\n"
            text += "─" * 25 + "\n"
            
            # Get super admin details from database
            super_admin_info = self.db.get_user(SUPER_ADMIN_ID)
            if super_admin_info:
                user_id, username, first_name, gender, age_group, rating, rating_count, is_active, is_premium, premium_until, registered_at = super_admin_info
                name = first_name or "Имя скрыто"
                username_display = f"@{username}" if username else "Нет username"
                status = "🟢 Активен" if is_active else "🔴 Заблокирован"
                premium_status = "💎 Premium" if is_premium else "⚡ Обычный"
                rating_display = f"⭐ {rating:.1f}/5 ({rating_count})" if rating_count > 0 else "⭐ Новый"
                
                # Calculate days since registration
                try:
                    reg_date = datetime.fromisoformat(registered_at.replace('Z', '+00:00'))
                    days_ago = (datetime.now() - reg_date).days
                    reg_display = f"{registered_at[:10]} ({days_ago} дн. назад)"
                except:
                    reg_display = registered_at[:10] if registered_at else "Неизвестно"
                
                text += f"👤 {name}\n"
                text += f"📱 {username_display}\n"
                text += f"🆔 ID: {SUPER_ADMIN_ID}\n"
                text += f"📈 {status}\n"
                text += f"💎 {premium_status}\n"
                text += f"⭐ {rating_display}\n"
                text += f"📅 {reg_display}\n"
                text += f"🔑 Права: ВСЕ (Супер Админ)\n"
            else:
                text += f"👤 ID: {SUPER_ADMIN_ID}\n"
                text += f"❌ Пользователь не найден в базе данных\n"
                text += f"🔑 Права: ВСЕ (Супер Админ)\n"
            
            text += "\n"
        
        # Regular Admins section from database
        if db_admins:
            text += f"👨‍💼 АДМИНИСТРАТОРЫ ({len(db_admins)}):\n"
            text += "─" * 25 + "\n"
            
            for i, admin_data in enumerate(db_admins, 1):
                # 🔴 FIX: Unpack correct number of fields from get_all_admins query
                # Query returns: user_id, username, first_name, added_by, added_by_name, added_at
                admin_id, username_db, first_name_db, added_by, added_by_name, added_at = admin_data
                
                # Get admin details from database
                admin_info = self.db.get_user(admin_id)
                if admin_info:
                    user_id, username, first_name, gender, age_group, rating, rating_count, is_active, is_premium, premium_until, registered_at = admin_info
                    name = first_name or "Имя скрыто"
                    username_display = f"@{username}" if username else "Нет username"
                    status = "🟢 Активен" if is_active else "🔴 Заблокирован"
                    premium_status = "💎 Premium" if is_premium else "⚡ Обычный"
                    rating_display = f"⭐ {rating:.1f}/5 ({rating_count})" if rating_count > 0 else "⭐ Новый"
                    
                    # Calculate days since registration
                    try:
                        reg_date = datetime.fromisoformat(registered_at.replace('Z', '+00:00'))
                        days_ago = (datetime.now() - reg_date).days
                        reg_display = f"{registered_at[:10]} ({days_ago} дн. назад)"
                    except:
                        reg_display = registered_at[:10] if registered_at else "Неизвестно"
                    
                    # Format admin added date
                    try:
                        admin_date = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
                        admin_days_ago = (datetime.now() - admin_date).days
                        admin_display = f"{added_at[:10]} ({admin_days_ago} дн. назад)"
                    except:
                        admin_display = added_at[:10] if added_at else "Неизвестно"
                    
                    text += f"{i}. 👤 {name}\n"
                    text += f"   📱 {username_display}\n"
                    text += f"   🆔 ID: {admin_id}\n"
                    text += f"   📈 {status}\n"
                    text += f"   💎 {premium_status}\n"
                    text += f"   ⭐ {rating_display}\n"
                    text += f"   📅 Регистрация: {reg_display}\n"
                    text += f"   👑 Админ с: {admin_display}\n"
                    text += f"   ➕ Добавил: {added_by}\n"
                    text += f"   🔑 Права: Администратор\n"
                else:
                    text += f"{i}. 👤 ID: {admin_id}\n"
                    text += f"   ❌ Пользователь не найден в базе данных\n"
                    text += f"   👑 Админ с: {added_at[:10]}\n"
                    text += f"   ➕ Добавил: {added_by}\n"
                    text += f"   🔑 Права: Администратор\n"
                
                text += "\n"
        
        # Summary section
        text += "─" * 30 + "\n"
        text += "📋 ПРАВА ДОСТУПА:\n"
        text += "🔥 Супер Админ: Все функции\n"
        text += "👨‍💼 Администратор: Базовые функции\n\n"
        
        if total_admins == 0:
            text += "❌ Администраторы не найдены.\n"
        
        # Check if message is too long and truncate if necessary
        if len(text) > 4000:
            text = text[:3900] + "\n\n⚠️ Список слишком длинный, показана часть..."
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    # Prompt methods for getting user input
    async def prompt_search_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """
🔍 Foydalanuvchi qidirish

Foydalanuvchi ID, username yoki ismini yuboring.
        """
        context.user_data['awaiting_input'] = 'search_user'
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    
    async def prompt_add_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """
➕ Kanal qo'shish

Qo'shmoqchi bo'lgan kanal username ini yuboring (masalan: @mychannel).
        """
        context.user_data['awaiting_input'] = 'add_channel'
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def prompt_remove_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """
➖ Kanal o'chirish

O'chirmoqchi bo'lgan kanal username ini yuboring (masalan: @mychannel).
        """
        context.user_data['awaiting_input'] = 'remove_channel'
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def prompt_add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """
➕ Добавить администратора

Отправьте ID пользователя или username (например: @username или 123456789)
        """
        context.user_data['awaiting_input'] = 'add_admin'
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def prompt_remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """
➖ Admin o'chirish

Admin huquqini olib tashlamoqchi bo'lgan foydalanuvchi ID sini yuboring.
        """
        context.user_data['awaiting_input'] = 'remove_admin'
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_admin_message_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin message input for various operations"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            return
        
        user_input = update.message.text.strip()
        
        # Check if waiting for specific input
        if 'awaiting_input' in context.user_data:
            input_type = context.user_data['awaiting_input']
            
            if input_type == 'search_user':
                await self.handle_search_user_result(update, context, user_input)
            elif input_type == 'ban_user':
                await self.handle_ban_user_input(update, context, user_input)
            elif input_type == 'unban_user':
                await self.handle_unban_user_input(update, context, user_input)
            elif input_type == 'add_channel':
                await self.handle_add_channel_input(update, context, user_input)
            elif input_type == 'remove_channel':
                await self.handle_remove_channel_input(update, context, user_input)
            elif input_type == 'add_admin':
                await self.handle_add_admin_input(update, context, user_input)
            elif input_type == 'remove_admin':
                await self.handle_remove_admin_input(update, context, user_input)
            elif input_type == 'add_premium':
                await self.handle_add_premium_input(update, context, user_input)
            elif input_type == 'remove_premium':
                await self.handle_remove_premium_input(update, context, user_input)
            # Subscription plan management inputs
            elif input_type == 'add_plan':
                await self.handle_add_plan_input(update, context, user_input)
            elif input_type == 'edit_plan_select':
                await self.handle_edit_plan_select(update, context, user_input)
            elif input_type == 'edit_plan_details':
                await self.handle_edit_plan_details_input(update, context, user_input)
            elif input_type == 'delete_plan_select':
                await self.handle_delete_plan_select(update, context, user_input)
            elif input_type == 'delete_plan_confirm':
                await self.handle_delete_plan_confirm(update, context, user_input)
            elif input_type == 'quick_edit_plan':
                await self.handle_quick_edit_plan_input(update, context, user_input)
            
            # Clean up awaiting_input
            del context.user_data['awaiting_input']
            return
        
        # Check if waiting for broadcast message
        if 'broadcast_target' in context.user_data:
            await self.handle_broadcast_message(update, context, user_input)
    
    async def handle_search_user_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Handle user search result"""
        users = self.db.search_user(query)
        
        if not users:
            text = f"❌ '{query}' bo'yicha hech narsa topilmadi."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            return
        
        text = f"🔍 '{query}' bo'yicha qidiruv natijalari:\n\n"
        
        for user in users[:10]:  # Limit to 10 results
            # Handle both old and new database formats
            if len(user) >= 11:  # New format with premium fields
                user_id, username, first_name, gender, age_group, rating, rating_count, is_active, is_premium, premium_until, registered_at = user
                premium_status = "💎 PREMIUM" if is_premium else "⚡ SIMPLE"
            else:  # Old format without premium fields
                user_id, username, first_name, gender, age_group, rating, rating_count, is_active, registered_at = user
                premium_status = "⚡ SIMPLE"  # Default to simple for old records
            
            status = "✅ Faol" if is_active else "❌ Banlangan"
            rating_text = f"⭐ {rating:.1f}" if rating_count > 0 else "Reytingsiz"
            name = first_name or "Ism yo'q"
            username_text = f"@{username}" if username else "Username yo'q"
            
            text += f"👤 {name}\n"
            text += f"📱 {username_text}\n"
            text += f"🆔 ID: {user_id}\n"
            text += f"📊 {rating_text} | {status}\n"
            text += f"💳 {premium_status}\n"
            text += f"⏰ {registered_at[:10]}\n\n"
        
        if len(users) > 10:
            text += f"... va yana {len(users) - 10}ta natija"
        
        await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_ban_user_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle ban user input"""
        try:
            user_id_to_ban = int(user_input)
            
            if self.is_admin(user_id_to_ban):
                text = "❌ Adminni ban qilib bo'lmaydi!"
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            success = self.db.ban_user(user_id_to_ban)
            
            if success:
                text = f"✅ Foydalanuvchi {user_id_to_ban} muvaffaqiyatli banlandi."
            else:
                text = f"❌ Foydalanuvchi {user_id_to_ban} banlanmadi. Xatolik yuz berdi."
            
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
        except ValueError:
            text = "❌ Noto'g'ri ID format. Raqam kiriting."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_unban_user_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle unban user input"""
        try:
            user_id_to_unban = int(user_input)
            success = self.db.unban_user(user_id_to_unban)
            
            if success:
                text = f"✅ Foydalanuvchi {user_id_to_unban} ban olib tashlandi."
            else:
                text = f"❌ Foydalanuvchi {user_id_to_unban} ban olib tashlanmadi. Xatolik yuz berdi."
            
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
        except ValueError:
            text = "❌ Noto'g'ri ID format. Raqam kiriting."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_add_channel_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle add channel input"""
        channel = user_input.strip()
        if not channel.startswith('@'):
            channel = '@' + channel
        
        user_id = update.effective_user.id
        success, message = self.db.add_mandatory_channel(channel, user_id)
        
        if success:
            text = f"✅ {message}: {channel}"
        else:
            text = f"❌ {message}"
        
        await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_remove_channel_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle remove channel input"""
        channel = user_input.strip()
        if not channel.startswith('@'):
            channel = '@' + channel
        
        success, message = self.db.remove_mandatory_channel(channel)
        
        if success:
            text = f"✅ {message}: {channel}"
        else:
            text = f"❌ {message}"
        
        await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_add_admin_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle add admin input - supports both user ID and username"""
        if not self.is_super_admin(update.effective_user.id):
            text = "❌ Только супер-админ может добавлять администраторов."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            return
        
        user_input = user_input.strip()
        new_admin_id = None
        user_display = user_input
        
        # Check if input is a username (starts with @)
        if user_input.startswith('@'):
            username = user_input[1:]  # Remove @ symbol
            # Search for user by username in database
            user_data = self.db.get_user_by_username(username)
            if user_data:
                new_admin_id = user_data[0]  # user_id is the first field
                user_display = f"@{username} (ID: {new_admin_id})"
            else:
                text = f"❌ Пользователь с username @{username} не найден в базе данных."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
        else:
            # Try to parse as user ID
            try:
                new_admin_id = int(user_input)
                # Verify user exists in database
                user_data = self.db.get_user(new_admin_id)
                if user_data:
                    username = user_data[1]  # username is the second field
                    first_name = user_data[2]  # first_name is the third field
                    if username:
                        user_display = f"{first_name or 'Без имени'} (@{username}) - ID: {new_admin_id}"
                    else:
                        user_display = f"{first_name or 'Без имени'} - ID: {new_admin_id}"
                else:
                    text = f"❌ Пользователь с ID {new_admin_id} не найден в базе данных."
                    await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                    return
            except ValueError:
                text = "❌ Неправильный формат. Введите ID пользователя (число) или username (например: @username)."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
        
        # Check if user is already super admin
        if new_admin_id == SUPER_ADMIN_ID:
            text = f"❌ Пользователь {user_display} уже является супер-администратором."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            return
        
        # Check if user is already an admin in database
        if self.db.is_admin(new_admin_id):
            text = f"❌ Пользователь {user_display} уже является администратором."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            return
        
        # Add admin to database
        success, message = self.db.add_admin(new_admin_id, update.effective_user.id)
        
        if success:
            text = f"✅ Пользователь {user_display} успешно добавлен как администратор!\n\n{message}"
        else:
            text = f"❌ Ошибка при добавлении администратора {user_display}:\n{message}"
        
        await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_remove_admin_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle remove admin input"""
        if not self.is_super_admin(update.effective_user.id):
            text = "❌ Faqat super admin boshqa adminlarni o'chira oladi."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            return
        
        try:
            admin_id_to_remove = int(user_input)
            
            # Check if trying to remove super admin
            if admin_id_to_remove == SUPER_ADMIN_ID:
                text = f"❌ Нельзя удалить супер-администратора!"
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            # Check if user is actually an admin
            if not self.db.is_admin(admin_id_to_remove):
                text = f"❌ Пользователь {admin_id_to_remove} не является администратором."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            # Remove admin from database
            success = self.db.remove_admin(admin_id_to_remove)
            
            if success:
                text = f"✅ Администратор {admin_id_to_remove} успешно удален."
            else:
                text = f"❌ Ошибка при удалении администратора {admin_id_to_remove}."
            
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
        except ValueError:
            text = "❌ Noto'g'ri ID format. Raqam kiriting."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
        """Handle broadcast message"""
        target_type = context.user_data.get('broadcast_target')
        
        if not target_type:
            await update.message.reply_text("❌ Broadcast turi aniqlanmadi.", reply_markup=Keyboards.admin_back())
            return
        
        # Get target users based on filter
        filter_params = {}
        if target_type == 'male':
            filter_params['gender'] = 'erkak'
        elif target_type == 'female':
            filter_params['gender'] = 'ayol'
        
        target_users = self.db.broadcast_to_users(filter_params if filter_params else None)
        
        if not target_users:
            text = "❌ Xabar yuborish uchun foydalanuvchilar topilmadi."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            return
        
        # Send broadcast message
        success_count = 0
        failed_count = 0
        
        status_message = await update.message.reply_text(f"📤 Broadcast boshlanmoqda... 0/{len(target_users)}")
        
        for i, user_id in enumerate(target_users):
            try:
                await context.bot.send_message(chat_id=user_id, text=message)
                success_count += 1
            except Exception as e:
                failed_count += 1
                logging.error(f"Failed to send broadcast to {user_id}: {e}")
            
            # Update status every 10 messages
            if (i + 1) % 10 == 0 or i == len(target_users) - 1:
                try:
                    await status_message.edit_text(f"📤 Broadcast: {i + 1}/{len(target_users)}\n✅ Yuborildi: {success_count}\n❌ Xatolik: {failed_count}")
                except:
                    pass
        
        # Final result
        target_names = {
            'all': 'Barcha foydalanuvchilarga',
            'male': 'Erkaklarga',
            'female': 'Ayollarga'
        }
        
        result_text = f"""
✅ Broadcast yakunlandi!

📊 Natijalar:
• Maqsad: {target_names.get(target_type, 'Nomalum')}
• Jami: {len(target_users)}
• Muvaffaqiyatli: {success_count}
• Xatolik: {failed_count}
        """
        
        await update.message.reply_text(result_text, reply_markup=Keyboards.admin_back())
        
        # Clean up
        if 'broadcast_target' in context.user_data:
            del context.user_data['broadcast_target']
    
    # PREMIUM MANAGEMENT METHODS
    async def show_premium_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium management menu"""
        text = """
💎 Управление Premium подписками

Выберите одно из следующих действий:
        """
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_premium_menu())
    
    async def show_premium_users_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page=1):
        """Show paginated list of premium users"""
        premium_data = self.db.get_all_premium_users(page=page, per_page=10)
        
        if not premium_data or not premium_data['users']:
            text = "❌ Premium пользователи не найдены."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        text = f"💎 Premium пользователи (Страница {page}/{premium_data['total_pages']})\n\n"
        
        for user in premium_data['users']:
            user_id, username, first_name, gender, age_group, rating, rating_count, is_active, is_premium, premium_until, registered_at = user
            
            # Format premium info
            from datetime import datetime
            try:
                if premium_until:
                    end_date = datetime.fromisoformat(premium_until.replace('Z', '+00:00'))
                    now = datetime.now()
                    if end_date > now:
                        days_left = (end_date - now).days + 1
                        premium_status = f"💎 Активен ({days_left} дн.)"
                    else:
                        premium_status = "⚠️ Истек"
                else:
                    premium_status = "❌ Нет данных"
            except:
                premium_status = "❌ Ошибка"
            
            status = "✅ Активен" if is_active else "❌ Заблокирован"
            rating_text = f"⭐ {rating:.1f}" if rating_count > 0 else "Без рейтинга"
            name = first_name or "Имя отсутствует"
            username_text = f"@{username}" if username else "Нет username"
            
            text += f"👤 {name}\n"
            text += f"📱 {username_text}\n"
            text += f"🆔 ID: {user_id}\n"
            text += f"📊 {rating_text} | {status}\n"
            text += f"💎 {premium_status}\n"
            text += f"⏰ {registered_at[:10]}\n\n"
        
        keyboard = Keyboards.admin_pagination(page, premium_data['total_pages'], "admin_premium_list")
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    
    async def show_premium_user_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Show detailed premium information for a specific user"""
        user = self.db.get_user(user_id)
        premium_info = self.db.get_premium_info(user_id)
        
        if not user:
            text = "❌ Пользователь не найден."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        user_id_db, username, first_name, gender, age_group, rating, rating_count, is_active, is_premium, premium_until, registered_at = user
        
        name = first_name or "Имя отсутствует"
        username_text = f"@{username}" if username else "Нет username"
        status = "✅ Активен" if is_active else "❌ Заблокирован"
        rating_text = f"⭐ {rating:.1f}" if rating_count > 0 else "Без рейтинга"
        
        # Premium information
        if premium_info and premium_info['is_premium']:
            premium_status = f"💎 Активен ({premium_info['days_left']} дн.)"
            expires_at = premium_info['expires_at'].strftime('%Y-%m-%d %H:%M:%S') if premium_info['expires_at'] else "Неизвестно"
        else:
            premium_status = "⚡ Обычный"
            expires_at = "Не применимо"
        
        text = f"""
💎 Детали Premium пользователя

👤 {name}
📱 {username_text}
🆔 ID: {user_id}
📊 {rating_text}
📈 {status}
💎 Статус: {premium_status}
⏰ Истекает: {expires_at}
📅 Регистрация: {registered_at[:10]}
        """
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_premium_actions(user_id))
    
    async def prompt_add_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Prompt admin to add premium to a user"""
        text = """
➕ Добавить Premium подписку

Отправьте сообщение в формате:
<USER_ID> <DAYS>

Пример: 123456789 7
(даст пользователю 123456789 премиум на 7 дней)
        """
        context.user_data['awaiting_input'] = 'add_premium'
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def prompt_remove_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Prompt admin to remove premium from a user"""
        text = """
➖ Удалить Premium подписку

Отправьте ID пользователя, у которого нужно удалить Premium:
        """
        context.user_data['awaiting_input'] = 'remove_premium'
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_add_premium_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle add premium input"""
        try:
            parts = user_input.strip().split()
            if len(parts) != 2:
                text = "❌ Неправильный формат. Используйте: <USER_ID> <DAYS>\nПример: 123456789 7"
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            target_user_id = int(parts[0])
            days = int(parts[1])
            
            if days < 1 or days > 36500:  # Max ~100 years
                text = "❌ Количество дней должно быть от 1 до 36500."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            # Check if user exists
            user = self.db.get_user(target_user_id)
            if not user:
                text = f"❌ Пользователь с ID {target_user_id} не найден."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            # Add premium days
            success = self.db.add_premium_days(target_user_id, days)
            
            if success:
                user_name = user[2] or "Без имени"
                text = f"✅ Успешно добавлено {days} дн. Premium пользователю {user_name} (ID: {target_user_id})."
                
                # Notify user about premium
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f"🎉 Вам предоставлена Premium подписка на {days} дней!\n\n"
                             f"✨ Теперь вам доступны все Premium возможности:\n"
                             f"• Поиск по полу\n"
                             f"• Мгновенный поиск партнеров\n"
                             f"• Нет рекламы\n"
                             f"• Не нужна подписка на каналы"
                    )
                except Exception as e:
                    text += f"\n⚠️ Не удалось уведомить пользователя: {e}"
            else:
                text = f"❌ Ошибка при добавлении Premium пользователю {target_user_id}."
            
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            
        except ValueError:
            text = "❌ Неправильный формат. USER_ID и DAYS должны быть числами."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
        except Exception as e:
            text = f"❌ Ошибка: {str(e)}"
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    # SUBSCRIPTION PLANS MANAGEMENT METHODS
    async def show_plans_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show subscription plans management menu"""
        text = """
💰 Управление тарифными планами

Выберите одно из следующих действий:
        """
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_plans_menu())
    
    async def show_plans_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show interactive list of all subscription plans with management buttons"""
        plans = self.db.get_all_subscription_plans(include_inactive=True)
        
        if not plans:
            text = "❌ Тарифные планы не найдены.\n\n🔧 Создайте первый план через кнопку ниже."
            # Create keyboard with seed and add options
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [InlineKeyboardButton("➕ Добавить план", callback_data="admin_add_plan")],
                [InlineKeyboardButton("🌱 Создать базовые планы", callback_data="admin_seed_plans")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="admin_plans")]
            ]
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        # Sort plans by sort_order for consistent display
        sorted_plans = sorted(plans, key=lambda x: (x[8], x[0]))  # sort_order, then ID
        
        text = f"💰 Управление тарифными планами ({len(plans)}):\n\n"
        
        # Create interactive buttons for each plan
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        
        for plan in sorted_plans[:10]:  # Show max 10 plans to avoid button limit
            plan_id, plan_key, title, description, stars, days, is_active, is_special, sort_order, created_by, created_at, updated_at = plan
            
            status_emoji = "🟢" if is_active else "🔴"
            special_mark = "⭐" if is_special else ""
            
            # Truncate title if too long for button
            display_title = title if len(title) <= 25 else title[:22] + "..."
            button_text = f"{status_emoji} {display_title} ({stars}⭐→{days}d) {special_mark}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"admin_plan_action_{plan_id}")])
        
        if len(plans) > 10:
            text += f"⚠️ Показаны первые 10 планов из {len(plans)}. Используйте поиск для полного списка.\n\n"
        
        # Add management buttons
        keyboard.extend([
            [InlineKeyboardButton("➕ Добавить план", callback_data="admin_add_plan")],
            [
                InlineKeyboardButton("📊 Статистика планов", callback_data="admin_plans_stats"),
                InlineKeyboardButton("🔄 Сортировать", callback_data="admin_plans_sort")
            ],
            [
                InlineKeyboardButton("⚖️ Быстрое редактирование", callback_data="admin_quick_edit_plans"),
                InlineKeyboardButton("🗑️ Быстрое удаление", callback_data="admin_quick_delete_plans")
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_plans")]
        ])
        
        text += "💡 Нажмите на план для управления или используйте кнопки ниже."
        
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def handle_quick_edit_plan_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle quick edit plan input"""
        plan_id = context.user_data.get('editing_plan_id')
        if not plan_id:
            text = "❌ Ошибка: ID плана не найден."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            return
        
        try:
            import shlex
            parts = shlex.split(user_input.strip())
            
            if len(parts) < 3:
                text = "❌ Недостаточно параметров. Минимум: НАЗВАНИЕ ЦЕНА ДНЕЙ\n\n"
                text += "Формат: \"название\" цена_звезд количество_дней [\"описание\"]"
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            title = parts[0]
            stars = int(parts[1])
            days = int(parts[2])
            description = parts[3] if len(parts) > 3 else None
            
            # Validation
            if stars < 1 or stars > 10000:
                text = "❌ Количество звезд должно быть от 1 до 10000."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            if days < 1 or days > 36500:
                text = "❌ Количество дней должно быть от 1 до 36500."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            # Update plan
            success, message = self.db.update_subscription_plan(
                plan_id=plan_id,
                title=title,
                stars=stars,
                days=days,
                description=description
            )
            
            if success:
                text = f"✅ **ПЛАН УСПЕШНО ОБНОВЛЕН!**\n\n"
                text += f"📋 Название: {title}\n"
                text += f"⭐ Цена: {stars} звезд\n"
                text += f"📅 Длительность: {days} дней\n"
                if description:
                    text += f"📄 Описание: {description}\n"
                text += f"\n🎉 План готов к использованию!"
            else:
                text = f"❌ Ошибка при обновлении плана: {message}"
            
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [
                [InlineKeyboardButton("📜 Список планов", callback_data="admin_plans_list")],
                [InlineKeyboardButton("⚖️ Редактировать еще", callback_data="admin_quick_edit_plans")]
            ]
            
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            
            # Clean up context
            if 'editing_plan_id' in context.user_data:
                del context.user_data['editing_plan_id']
            
        except ValueError:
            text = "❌ Неправильный формат чисел. ЦЕНА и ДНИ должны быть целыми числами."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
        except Exception as e:
            text = f"❌ Ошибка при парсинге: {str(e)}\n\nПроверьте формат ввода:"
            text += "\n\"название\" цена_звезд количество_дней [\"описание\"]"
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def execute_quick_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int):
        """Execute quick delete confirmation"""
        success, message = self.db.delete_subscription_plan(plan_id)
        
        if success:
            text = f"✅ **ПЛАН УСПЕШНО УДАЛЕН!**\n\n"
            text += f"План ID {plan_id} был навсегда удален из базы данных.\n\n"
            text += f"🗂️ Все связанные данные очищены."
        else:
            text = f"❌ **ОШИБКА ПРИ УДАЛЕНИИ**\n\n{message}"
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("📜 Список планов", callback_data="admin_plans_list")],
            [InlineKeyboardButton("🗑️ Удалить еще", callback_data="admin_quick_delete_plans")]
        ]
        
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def show_plan_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int):
        """Show actions for a specific plan"""
        plan = self.db.get_subscription_plan_by_id(plan_id)
        
        if not plan:
            text = "❌ План не найден."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        plan_id_db, plan_key, title, description, stars, days, is_active, is_special, sort_order, created_by, created_at, updated_at = plan
        
        status = "🟢 Активен" if is_active else "🔴 Отключен"
        special_mark = " ⭐ ОСОБЫЙ" if is_special else ""
        
        text = f"""
💰 План: {title}{special_mark}

🔑 Ключ: {plan_key}
⭐ Цена: {stars} звезд
📅 Длительность: {days} дней
📄 Описание: {description or 'Не указано'}
📊 Статус: {status}
🔢 Порядок: {sort_order}
📋 ID: {plan_id}
⏰ Создан: {created_at[:10]}
🔄 Обновлен: {updated_at[:10]}

Выберите действие:
        """
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_plan_actions(plan_id))
    
    async def prompt_add_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Prompt admin to add a new subscription plan"""
        text = """
➕ Создать новый тарифный план

Отправьте данные в формате:
<KEY> <TITLE> <STARS> <DAYS> [DESCRIPTION]

Пример:
premium_14d "14 дней Premium" 12 14 "Две недели полного доступа"

Обязательные параметры:
• KEY - уникальный ключ (без пробелов)
• TITLE - название (в кавычках если содержит пробелы)
• STARS - количество звезд
• DAYS - количество дней

Необязательные:
• DESCRIPTION - описание (в кавычках)
        """
        context.user_data['awaiting_input'] = 'add_plan'
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def prompt_edit_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Prompt admin to select a plan to edit"""
        text = """
✏️ Редактировать план

Отправьте ID плана, который хотите отредактировать.
Для просмотра списка планов используйте кнопку "Список планов".
        """
        context.user_data['awaiting_input'] = 'edit_plan_select'
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def prompt_edit_plan_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int):
        """Prompt admin to edit plan details"""
        plan = self.db.get_subscription_plan_by_id(plan_id)
        
        if not plan:
            text = "❌ План не найден."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        plan_id_db, plan_key, title, description, stars, days, is_active, is_special, sort_order, created_by, created_at, updated_at = plan
        
        text = f"""
✏️ Редактирование плана: {title}

Отправьте новые данные в формате:
<TITLE> <STARS> <DAYS> [DESCRIPTION]

Текущие значения:
• Название: {title}
• Звезды: {stars}
• Дни: {days}
• Описание: {description or 'Не указано'}

Пример:
"Premium 30 дней" 25 30 "Месяц полного доступа"
        """
        context.user_data['awaiting_input'] = 'edit_plan_details'
        context.user_data['editing_plan_id'] = plan_id
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def prompt_delete_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Prompt admin to select a plan to delete"""
        text = """
🗑️ Удалить план

Отправьте ID плана, который хотите удалить.
⚠️ ВНИМАНИЕ: Это действие нельзя отменить!

Для просмотра списка планов используйте кнопку "Список планов".
        """
        context.user_data['awaiting_input'] = 'delete_plan_select'
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def confirm_delete_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int):
        """Confirm plan deletion"""
        plan = self.db.get_subscription_plan_by_id(plan_id)
        
        if not plan:
            text = "❌ План не найден."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        success, message = self.db.delete_subscription_plan(plan_id)
        
        if success:
            text = f"✅ {message}\n\nПlan ID {plan_id} был окончательно удален из базы данных."
        else:
            text = f"❌ Ошибка при удалении плана: {message}"
        
        await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
    
    async def toggle_plan_active(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int):
        """Toggle plan active status"""
        success, message = self.db.toggle_subscription_plan_active(plan_id)
        
        if success:
            text = f"✅ {message}"
        else:
            text = f"❌ Ошибка: {message}"
        
        # Refresh the plan actions view
        await update.callback_query.answer(text, show_alert=True)
        await self.show_plan_actions(update, context, plan_id)
    
    async def handle_add_plan_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle add subscription plan input"""
        try:
            # Parse input using simple split but handle quoted strings
            import shlex
            parts = shlex.split(user_input.strip())
            
            if len(parts) < 4:
                text = "❌ Недостаточно параметров. Минимум: KEY TITLE STARS DAYS"
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            plan_key = parts[0]
            title = parts[1]
            stars = int(parts[2])
            days = int(parts[3])
            description = parts[4] if len(parts) > 4 else None
            
            # Validation
            if not plan_key or ' ' in plan_key:
                text = "❌ Ключ плана не должен содержать пробелы."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            if stars < 1 or stars > 10000:
                text = "❌ Количество звезд должно быть от 1 до 10000."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            if days < 1 or days > 36500:
                text = "❌ Количество дней должно быть от 1 до 36500."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            # Create plan
            success, result = self.db.create_subscription_plan(
                plan_key=plan_key,
                title=title,
                description=description,
                stars=stars,
                days=days,
                created_by=update.effective_user.id
            )
            
            if success:
                text = f"✅ Тарифный план успешно создан!\n\n"
                text += f"🔑 Ключ: {plan_key}\n"
                text += f"📋 Название: {title}\n"
                text += f"⭐ Цена: {stars} звезд\n"
                text += f"📅 Длительность: {days} дней\n"
                if description:
                    text += f"📄 Описание: {description}\n"
                text += f"🆔 ID плана: {result}"
            else:
                text = f"❌ Ошибка при создании плана: {result}"
            
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            
        except ValueError as e:
            text = "❌ Неправильный формат чисел. STARS и DAYS должны быть целыми числами."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
        except Exception as e:
            text = f"❌ Ошибка при парсинге: {str(e)}\n\nПроверьте формат ввода."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_edit_plan_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle plan selection for editing"""
        try:
            plan_id = int(user_input.strip())
            plan = self.db.get_subscription_plan_by_id(plan_id)
            
            if not plan:
                text = f"❌ План с ID {plan_id} не найден."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            # Show plan edit form
            await self.prompt_edit_plan_details(update, context, plan_id)
            
        except ValueError:
            text = "❌ Неправильный формат. Введите числовой ID плана."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_edit_plan_details_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle plan details editing input"""
        plan_id = context.user_data.get('editing_plan_id')
        if not plan_id:
            text = "❌ Ошибка: ID плана не найден."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            return
        
        try:
            import shlex
            parts = shlex.split(user_input.strip())
            
            if len(parts) < 3:
                text = "❌ Недостаточно параметров. Минимум: TITLE STARS DAYS"
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            title = parts[0]
            stars = int(parts[1])
            days = int(parts[2])
            description = parts[3] if len(parts) > 3 else None
            
            # Validation
            if stars < 1 or stars > 10000:
                text = "❌ Количество звезд должно быть от 1 до 10000."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            if days < 1 or days > 36500:
                text = "❌ Количество дней должно быть от 1 до 36500."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            # Update plan
            success, message = self.db.update_subscription_plan(
                plan_id=plan_id,
                title=title,
                stars=stars,
                days=days,
                description=description
            )
            
            if success:
                text = f"✅ План успешно обновлен!\n\n"
                text += f"📋 Новое название: {title}\n"
                text += f"⭐ Новая цена: {stars} звезд\n"
                text += f"📅 Новая длительность: {days} дней\n"
                if description:
                    text += f"📄 Новое описание: {description}\n"
            else:
                text = f"❌ Ошибка при обновлении плана: {message}"
            
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            
            # Clean up context
            if 'editing_plan_id' in context.user_data:
                del context.user_data['editing_plan_id']
            
        except ValueError:
            text = "❌ Неправильный формат чисел. STARS и DAYS должны быть целыми числами."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
        except Exception as e:
            text = f"❌ Ошибка при парсинге: {str(e)}\n\nПроверьте формат ввода."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_delete_plan_select(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle plan selection for deletion"""
        try:
            plan_id = int(user_input.strip())
            plan = self.db.get_subscription_plan_by_id(plan_id)
            
            if not plan:
                text = f"❌ План с ID {plan_id} не найден."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            plan_id_db, plan_key, title, description, stars, days, is_active, is_special, sort_order, created_by, created_at, updated_at = plan
            
            text = f"""
⚠️ ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ

Вы действительно хотите удалить этот план?

📋 {title}
🔑 {plan_key}
⭐ {stars} звезд → {days} дней
🆔 ID: {plan_id}

❗ Это действие нельзя отменить!

Для подтверждения напишите: DELETE {plan_id}
            """
            
            context.user_data['awaiting_input'] = 'delete_plan_confirm'
            context.user_data['deleting_plan_id'] = plan_id
            
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            
        except ValueError:
            text = "❌ Неправильный формат. Введите числовой ID плана."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
    
    async def handle_delete_plan_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle plan deletion confirmation"""
        plan_id = context.user_data.get('deleting_plan_id')
        if not plan_id:
            text = "❌ Ошибка: ID плана не найден."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            return
        
        expected_confirmation = f"DELETE {plan_id}"
        if user_input.strip().upper() != expected_confirmation.upper():
            text = f"❌ Неправильное подтверждение.\n\nДля удаления напишите точно: {expected_confirmation}"
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            return
        
        # Delete the plan
        success, message = self.db.delete_subscription_plan(plan_id)
        
        if success:
            text = f"✅ {message}\n\nПлан ID {plan_id} был безвозвратно удален."
        else:
            text = f"❌ Ошибка при удалении плана: {message}"
        
        await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
        
        # Clean up context
        if 'deleting_plan_id' in context.user_data:
            del context.user_data['deleting_plan_id']
    
    # NEW QUICK EDIT AND DELETE METHODS
    async def show_quick_edit_plans(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show plans list for quick editing"""
        plans = self.db.get_all_subscription_plans(include_inactive=True)
        
        if not plans:
            text = "❌ Нет планов для редактирования."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        text = "⚖️ <b>БЫСТРОЕ РЕДАКТИРОВАНИЕ ПЛАНОВ</b>\n\n"
        text += "Выберите план для быстрого редактирования:\n\n"
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        
        # Sort plans by sort_order for consistent display
        sorted_plans = sorted(plans, key=lambda x: (x[8], x[0]))  # sort_order, then ID
        
        for plan in sorted_plans[:15]:  # Show max 15 plans
            plan_id, plan_key, title, description, stars, days, is_active, is_special, sort_order, created_by, created_at, updated_at = plan
            
            status_emoji = "🔢" if is_active else "🔴"
            special_mark = "⭐" if is_special else ""
            
            # Create shorter button text
            button_text = f"{status_emoji} {title[:20]}{'...' if len(title) > 20 else ''} ({stars}⭐/{days}d) {special_mark}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"admin_quick_edit_{plan_id}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад к списку планов", callback_data="admin_plans_list")])
        
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    async def show_quick_delete_plans(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show plans list for quick deletion"""
        plans = self.db.get_all_subscription_plans(include_inactive=True)
        
        if not plans:
            text = "❌ Нет планов для удаления."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        text = "🗑️ <b>БЫСТРОЕ УДАЛЕНИЕ ПЛАНОВ</b>\n\n"
        text += "⚠️ <b>ВНИМАНИЕ:</b> Удаление нельзя отменить!\n\n"
        text += "Выберите план для удаления:\n\n"
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        
        # Sort plans by sort_order for consistent display
        sorted_plans = sorted(plans, key=lambda x: (x[8], x[0]))  # sort_order, then ID
        
        for plan in sorted_plans[:15]:  # Show max 15 plans
            plan_id, plan_key, title, description, stars, days, is_active, is_special, sort_order, created_by, created_at, updated_at = plan
            
            status_emoji = "🔢" if is_active else "🔴"
            special_mark = "⭐" if is_special else ""
            
            # Create shorter button text with delete warning
            button_text = f"🗑️ {status_emoji} {title[:18]}{'...' if len(title) > 18 else ''} ({stars}⭐/{days}d) {special_mark}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"admin_quick_delete_{plan_id}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад к списку планов", callback_data="admin_plans_list")])
        
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    async def start_quick_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int):
        """Start quick edit process for a plan"""
        plan = self.db.get_subscription_plan_by_id(plan_id)
        
        if not plan:
            text = "❌ План не найден."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        plan_id_db, plan_key, title, description, stars, days, is_active, is_special, sort_order, created_by, created_at, updated_at = plan
        
        # Escape HTML characters to prevent parsing errors
        import html
        title_escaped = html.escape(str(title))
        description_escaped = html.escape(str(description) if description else 'Не указано')
        
        text = f"⚖️ <b>БЫСТРОЕ РЕДАКТИРОВАНИЕ</b>\n\n"
        text += f"📋 <b>Текущий план:</b> {title_escaped}\n\n"
        text += f"<b>Текущие параметры:</b>\n"
        text += f"• Название: {title_escaped}\n"
        text += f"• Цена: {stars} ⭐\n"
        text += f"• Дни: {days}\n"
        text += f"• Описание: {description_escaped}\n\n"
        text += f"<b>Отправьте новые данные в формате:</b>\n"
        text += f"<code>'название' цена_звезд количество_дней 'описание'</code>\n\n"
        text += f"<b>Пример:</b>\n"
        text += f"<code>'Premium 30 дней' 25 30 'Месяц полного доступа'</code>\n\n"
        text += f"💡 Если описание не нужно, не указывайте его."
        
        context.user_data['awaiting_input'] = 'quick_edit_plan'
        context.user_data['editing_plan_id'] = plan_id
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="admin_plans_list")]]
        
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    async def quick_delete_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: int):
        """Quick delete a plan with single confirmation"""
        plan = self.db.get_subscription_plan_by_id(plan_id)
        
        if not plan:
            text = "❌ План не найден."
            await update.callback_query.edit_message_text(text, reply_markup=Keyboards.admin_back())
            return
        
        plan_id_db, plan_key, title, description, stars, days, is_active, is_special, sort_order, created_by, created_at, updated_at = plan
        
        # Escape HTML characters to prevent parsing errors
        import html
        title_escaped = html.escape(str(title))
        plan_key_escaped = html.escape(str(plan_key))
        
        text = f"🗑️ <b>ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ</b>\n\n"
        text += f"⚠️ <b>Вы действительно хотите удалить план?</b>\n\n"
        text += f"<b>План:</b> {title_escaped}\n"
        text += f"<b>Ключ:</b> {plan_key_escaped}\n"
        text += f"<b>Цена:</b> {stars} ⭐ - {days} дней\n"
        text += f"<b>ID:</b> {plan_id}\n\n"
        text += f"❗ <b>Это действие нельзя отменить!</b>"
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton("🗑️ ДА, УДАЛИТЬ НАВСЕГДА", callback_data=f"admin_confirm_delete_{plan_id}")],
            [InlineKeyboardButton("❌ Нет, отменить", callback_data="admin_quick_delete_plans")]
        ]
        
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    async def seed_default_plans(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Seed database with default subscription plans"""
        admin_id = update.effective_user.id
        
        # Create default plans
        created_count = self.db.seed_default_subscription_plans(created_by=admin_id)
        
        if created_count > 0:
            text = f"✅ Успешно создано {created_count} базовых планов подписки!\n\n"
            text += f"Созданные планы:\n"
            text += f"• 1 день Premium (1 ⭐)\n"
            text += f"• 7 дней Premium (7 ⭐)\n"
            text += f"• 30 дней Premium (25 ⭐) - ОСОБЫЙ\n\n"
            text += f"Планы готовы к использованию!"
        else:
            text = "ℹ️ Базовые планы уже существуют или произошла ошибка при создании."
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[InlineKeyboardButton("📜 Посмотреть планы", callback_data="admin_plans_list")]]
        
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Update the handle_admin_message_input method to include new plan inputs
    async def handle_admin_message_input_extended(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Extended version of admin message input handler with plan management"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            return
        
        user_input = update.message.text.strip()
        
        # Check if waiting for specific input
        if 'awaiting_input' in context.user_data:
            input_type = context.user_data['awaiting_input']
            
            # Existing input types
            if input_type == 'search_user':
                await self.handle_search_user_result(update, context, user_input)
            elif input_type == 'ban_user':
                await self.handle_ban_user_input(update, context, user_input)
            elif input_type == 'unban_user':
                await self.handle_unban_user_input(update, context, user_input)
            elif input_type == 'add_channel':
                await self.handle_add_channel_input(update, context, user_input)
            elif input_type == 'remove_channel':
                await self.handle_remove_channel_input(update, context, user_input)
            elif input_type == 'add_admin':
                await self.handle_add_admin_input(update, context, user_input)
            elif input_type == 'remove_admin':
                await self.handle_remove_admin_input(update, context, user_input)
            elif input_type == 'add_premium':
                await self.handle_add_premium_input(update, context, user_input)
            elif input_type == 'remove_premium':
                await self.handle_remove_premium_input(update, context, user_input)
            
            # New subscription plan input types
            elif input_type == 'add_plan':
                await self.handle_add_plan_input(update, context, user_input)
            elif input_type == 'edit_plan_select':
                await self.handle_edit_plan_select(update, context, user_input)
            elif input_type == 'edit_plan_details':
                await self.handle_edit_plan_details_input(update, context, user_input)
            elif input_type == 'delete_plan_select':
                await self.handle_delete_plan_select(update, context, user_input)
            elif input_type == 'delete_plan_confirm':
                await self.handle_delete_plan_confirm(update, context, user_input)
            
            # Clean up awaiting_input
            del context.user_data['awaiting_input']
            return
        
        # Check if waiting for broadcast message
        if 'broadcast_target' in context.user_data:
            await self.handle_broadcast_message(update, context, user_input)
    
    async def handle_remove_premium_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_input: str):
        """Handle remove premium input"""
        try:
            target_user_id = int(user_input.strip())
            
            # Check if user exists
            user = self.db.get_user(target_user_id)
            if not user:
                text = f"❌ Пользователь с ID {target_user_id} не найден."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            # Check if user has premium
            if not self.db.is_user_premium(target_user_id):
                text = f"❌ Пользователь {target_user_id} не имеет Premium подписки."
                await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
                return
            
            # Remove premium
            success, message = self.db.remove_premium(target_user_id)
            
            if success:
                user_name = user[2] or "Без имени"
                text = f"✅ Premium подписка успешно удалена у пользователя {user_name} (ID: {target_user_id})."
                
                # Notify user about premium removal
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text="ℹ️ Ваша Premium подписка была деактивирована администратором.\n\n"
                             "Для получения Premium возможностей приобретите новую подписку."
                    )
                except Exception as e:
                    text += f"\n⚠️ Не удалось уведомить пользователя: {e}"
            else:
                text = f"❌ Ошибка при удалении Premium: {message}"
            
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
            
        except ValueError:
            text = "❌ Неправильный формат. Введите числовой ID пользователя."
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
        except Exception as e:
            text = f"❌ Ошибка: {str(e)}"
            await update.message.reply_text(text, reply_markup=Keyboards.admin_back())
