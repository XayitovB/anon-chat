from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class Keyboards:
    @staticmethod
    def start_check_channels():
        """Keyboard for channel subscription check"""
        keyboard = [
            [InlineKeyboardButton("👍 Я подписался", callback_data="check_channels")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def continue_button():
        """Continue button after successful subscription"""
        keyboard = [
            [InlineKeyboardButton("Продолжить ➡️", callback_data="continue_registration")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def gender_selection():
        """Keyboard for gender selection"""
        keyboard = [
            [InlineKeyboardButton("👨 Мужчина", callback_data="gender_erkak")],
            [InlineKeyboardButton("👩 Женщина", callback_data="gender_ayol")],
            [InlineKeyboardButton("🚻 Другое", callback_data="gender_boshqa")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def age_selection():
        """Keyboard for age selection"""
        keyboard = [
            [InlineKeyboardButton("9-14", callback_data="age_9_14")],
            [InlineKeyboardButton("15-18", callback_data="age_15_18")],
            [InlineKeyboardButton("18-24", callback_data="age_18_24")],
            [InlineKeyboardButton("25-34", callback_data="age_25_34")],
            [InlineKeyboardButton("35+", callback_data="age_35_plus")],
            [InlineKeyboardButton("🔄 Другое", callback_data="age_boshqa")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def main_menu():
        """Main menu keyboard"""
        keyboard = [
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
            [InlineKeyboardButton("❌ Выход", callback_data="exit")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def filter_gender():
        """Gender filter for partner search"""
        keyboard = [
            [InlineKeyboardButton("👨 Мужчина", callback_data="filter_gender_erkak")],
            [InlineKeyboardButton("👩 Женщина", callback_data="filter_gender_ayol")],
            [InlineKeyboardButton("⚖️ Не важно", callback_data="filter_gender_farqi_yoq")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def filter_age():
        """Age filter for partner search"""
        keyboard = [
            [InlineKeyboardButton("9-14", callback_data="filter_age_9_14")],
            [InlineKeyboardButton("15-18", callback_data="filter_age_15_18")],
            [InlineKeyboardButton("18-24", callback_data="filter_age_18_24")],
            [InlineKeyboardButton("25-34", callback_data="filter_age_25_34")],
            [InlineKeyboardButton("35+", callback_data="filter_age_35_plus")],
            [InlineKeyboardButton("🔄 Не важно", callback_data="filter_age_farqi_yoq")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def cancel_search():
        """Cancel search keyboard"""
        keyboard = [
            [InlineKeyboardButton("❌ Отменить поиск", callback_data="cancel_search")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def chat_controls():
        """Chat control buttons"""
        keyboard = [
            [InlineKeyboardButton("⏭ Следующий", callback_data="next_partner")],
            [InlineKeyboardButton("🚫 Покинуть", callback_data="leave_chat")],
            [InlineKeyboardButton("⚠️ Пожаловаться", callback_data="report_user")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def rating(show_add_friend=False, partner_id=None):
        """Rating keyboard with optional add to friends button"""
        keyboard = [
            [
                InlineKeyboardButton("⭐ 1", callback_data="rate_1"),
                InlineKeyboardButton("⭐ 2", callback_data="rate_2"),
                InlineKeyboardButton("⭐ 3", callback_data="rate_3"),
                InlineKeyboardButton("⭐ 4", callback_data="rate_4"),
                InlineKeyboardButton("⭐ 5", callback_data="rate_5")
            ]
        ]
        
        # Add friend request button if enabled and partner_id provided
        if show_add_friend and partner_id:
            keyboard.append([
                InlineKeyboardButton("👥 Добавить в друзья", callback_data=f"add_friend_{partner_id}")
            ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_to_menu():
        """Back to main menu"""
        keyboard = [
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def top_users_menu():
        """TOP users menu with premium button"""
        keyboard = [
            [InlineKeyboardButton("Получить бесплатный 💎 PREMIUM", callback_data="get_free_premium")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def settings_menu():
        """Settings menu"""
        keyboard = [
            [InlineKeyboardButton("🔄 Обновить данные", callback_data="update_profile")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def premium_menu(subscription_plans=None):
        """Premium menu with pricing options (dynamic or fallback)"""
        keyboard = []
        
        if subscription_plans:
            # Sort plans by sort_order and add them dynamically
            sorted_plans = sorted(
                subscription_plans.items(), 
                key=lambda x: (x[1].get('sort_order', 0), x[1].get('stars', 0))
            )
            
            for plan_key, plan_data in sorted_plans:
                title = plan_data['title']
                stars = plan_data['stars']
                is_special = plan_data.get('is_special', False)
                
                # Add special emoji for special plans
                button_text = f"💰 {title} - {stars} ⭐"
                if is_special:
                    button_text = f"🎆 {title} - {stars} ⭐ 🎆"
                
                # Remove 'premium_' prefix if it exists to avoid double prefix
                clean_plan_key = plan_key.replace('premium_', '')
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"premium_{clean_plan_key}")])
        else:
            # Fallback hardcoded options if no plans available
            keyboard = [
                [InlineKeyboardButton("💰 1 день Premium ⭐ - 1 ⭐", callback_data="premium_1day")],
                [InlineKeyboardButton("💰 7 дней Premium ⭐ - 7 ⭐", callback_data="premium_1week")],
                [InlineKeyboardButton("🎆 30 дней Premium ⭐ - 25 ⭐ 🎆", callback_data="premium_1month")],
            ]
        
        # Add additional options
        keyboard.extend([
            [InlineKeyboardButton("😊 Обнулить рейтинг - 99 ⭐", callback_data="reset_rating")],
            [InlineKeyboardButton("💰 Получить бесплатно!", callback_data="get_free_premium")],
            [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    # ADMIN KEYBOARDS
    @staticmethod
    def admin_main_menu():
        """Admin main menu"""
        keyboard = [
            [InlineKeyboardButton("📋 Список пользователей", callback_data="admin_users")],
            [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📌 Обязательные каналы", callback_data="admin_channels")],
            [InlineKeyboardButton("💎 Управление Premium", callback_data="admin_premium")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("👑 Управление админами", callback_data="admin_manage")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_users_menu():
        """Admin users management menu"""
        keyboard = [
            [InlineKeyboardButton("👥 Все пользователи", callback_data="admin_all_users")],
            [InlineKeyboardButton("🔍 Поиск пользователя", callback_data="admin_search_user")],
            [InlineKeyboardButton("📊 Активные пользователи", callback_data="admin_active_users")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_broadcast_menu():
        """Admin broadcast menu"""
        keyboard = [
            [InlineKeyboardButton("📤 Отправить всем", callback_data="admin_broadcast_all")],
            [InlineKeyboardButton("👨 Отправить мужчинам", callback_data="admin_broadcast_male")],
            [InlineKeyboardButton("👩 Отправить женщинам", callback_data="admin_broadcast_female")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_channels_menu():
        """Admin channels management menu"""
        keyboard = [
            [InlineKeyboardButton("📜 Список каналов", callback_data="admin_list_channels")],
            [InlineKeyboardButton("➕ Добавить канал", callback_data="admin_add_channel")],
            [InlineKeyboardButton("➖ Удалить канал", callback_data="admin_remove_channel")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_bans_menu():
        """Admin ban management menu"""
        keyboard = [
            [InlineKeyboardButton("🚫 Заблокированные пользователи", callback_data="admin_banned_users")],
            [InlineKeyboardButton("🔨 Заблокировать пользователя", callback_data="admin_ban_user")],
            [InlineKeyboardButton("✅ Разблокировать", callback_data="admin_unban_user")],
            [InlineKeyboardButton("⚠️ Жалобы", callback_data="admin_reports")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_stats_menu():
        """Admin statistics menu"""
        keyboard = [
            [InlineKeyboardButton("👥 Статистика пользователей", callback_data="admin_user_stats")],
            [InlineKeyboardButton("💬 Статистика чатов", callback_data="admin_chat_stats")],
            [InlineKeyboardButton("⭐ Статистика рейтингов", callback_data="admin_rating_stats")],
            [InlineKeyboardButton("🔍 Состояние очереди", callback_data="admin_queue_stats")],
            [InlineKeyboardButton("📊 Общий отчет", callback_data="admin_full_report")],
            [InlineKeyboardButton("🔍 Аналитика активности", callback_data="admin_activity_analytics")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_manage_menu():
        """Admin management menu"""
        keyboard = [
            [InlineKeyboardButton("📜 Список админов", callback_data="admin_list_admins")],
            [InlineKeyboardButton("➕ Добавить админа", callback_data="admin_add_admin")],
            [InlineKeyboardButton("➖ Удалить админа", callback_data="admin_remove_admin")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_back():
        """Back to admin menu"""
        keyboard = [
            [InlineKeyboardButton("⬅️ Возврат в админ-панель", callback_data="admin_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_confirm_action(action, target_id):
        """Confirm admin action"""
        keyboard = [
            [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_confirm_{action}_{target_id}")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_user_actions(user_id):
        """User action buttons for admin"""
        keyboard = [
            [InlineKeyboardButton("🔍 Batafsil ma'lumot", callback_data=f"admin_user_details_{user_id}")],
            [InlineKeyboardButton("🚫 Banlash", callback_data=f"admin_ban_confirm_{user_id}")],
            [InlineKeyboardButton("✅ Ban olib tashlash", callback_data=f"admin_unban_confirm_{user_id}")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_users")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_pagination(page, total_pages, callback_prefix):
        """Pagination buttons for admin"""
        keyboard = []
        nav_buttons = []
        
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"{callback_prefix}_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"))
        
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"{callback_prefix}_{page+1}"))
        
        keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_premium_menu():
        """Admin premium management menu"""
        keyboard = [
            [InlineKeyboardButton("📜 Список Premium пользователей", callback_data="admin_premium_list")],
            [InlineKeyboardButton("➕ Добавить Premium", callback_data="admin_add_premium")],
            [InlineKeyboardButton("➖ Удалить Premium", callback_data="admin_remove_premium")],
            [InlineKeyboardButton("💰 Управление тарифами", callback_data="admin_plans")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # FRIENDS SYSTEM KEYBOARDS
    @staticmethod
    def friends_menu(friends_count=0, pending_requests=0):
        """Friends main menu"""
        keyboard = [
            [InlineKeyboardButton(f"👥 Мои друзья ({friends_count})", callback_data="friends_list")],
            [InlineKeyboardButton(f"📨 Входящие запросы ({pending_requests})", callback_data="friend_requests_in")],
            [InlineKeyboardButton("📤 Исходящие запросы", callback_data="friend_requests_out")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def friend_request_actions(requester_id):
        """Accept/decline friend request buttons"""
        keyboard = [
            [InlineKeyboardButton("✅ Принять", callback_data=f"accept_friend_{requester_id}")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_friend_{requester_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="friend_requests_in")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def friend_actions(friend_id):
        """Friend management buttons"""
        keyboard = [
            [InlineKeyboardButton("💬 Написать", callback_data=f"message_friend_{friend_id}")],
            [InlineKeyboardButton("🗑 Удалить из друзей", callback_data=f"remove_friend_{friend_id}")],
            [InlineKeyboardButton("🔙 Назад к друзьям", callback_data="friends_list")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def friends_back():
        """Back to friends menu"""
        keyboard = [
            [InlineKeyboardButton("🔙 К друзьям", callback_data="friends")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def friends_pagination(page, total_pages, callback_prefix):
        """Pagination for friends lists"""
        keyboard = []
        nav_buttons = []
        
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"{callback_prefix}_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"))
        
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"{callback_prefix}_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("🔙 К друзьям", callback_data="friends")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_premium_actions(user_id):
        """Premium user action buttons for admin"""
        keyboard = [
            [InlineKeyboardButton("➕ Добавить дни", callback_data="admin_add_premium")],
            [InlineKeyboardButton("➖ Удалить Premium", callback_data="admin_remove_premium")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_premium_list")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_plans_menu():
        """Admin subscription plans management menu"""
        keyboard = [
            [InlineKeyboardButton("📜 Список тарифов", callback_data="admin_plans_list")],
            [InlineKeyboardButton("➕ Добавить тариф", callback_data="admin_add_plan")],
            [InlineKeyboardButton("⚖ Изменить тариф", callback_data="admin_edit_plan")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_premium")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_plan_actions(plan_id):
        """Individual plan action buttons for admin"""
        keyboard = [
            [InlineKeyboardButton("⚖ Изменить", callback_data=f"admin_plan_edit_{plan_id}")],
            [InlineKeyboardButton("➖ Удалить", callback_data=f"admin_plan_delete_{plan_id}")],
            [InlineKeyboardButton("❤️ Вкл/Выкл", callback_data=f"admin_plan_toggle_{plan_id}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_plans_list")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    # Additional missing friend system keyboards
    @staticmethod
    def check_friend_requests():
        """Quick access to friend requests"""
        keyboard = [
            [InlineKeyboardButton("📥 Проверить заявки", callback_data="friends")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def friends_main_menu():
        """Friends main menu (alias for friends_menu with default params)"""
        keyboard = [
            [InlineKeyboardButton("👥 Список друзей", callback_data="friends_list")],
            [InlineKeyboardButton("📥 Входящие заявки", callback_data="friend_requests_in")],
            [InlineKeyboardButton("📤 Исходящие заявки", callback_data="friend_requests_out")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_to_friends():
        """Back to friends menu (alias for friends_back)"""
        keyboard = [
            [InlineKeyboardButton("🔙 К друзьям", callback_data="friends")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def friends_list_menu(friends_page, page, total_pages):
        """Friends list with pagination"""
        keyboard = []
        
        # Add remove friend buttons for each friend
        for friend in friends_page[:3]:  # Show only first 3 for space
            friend_id = friend[0]
            friend_name = friend[2] if friend[2] else f"User {friend_id}"
            if len(friend_name) > 12:
                friend_name = friend_name[:9] + "..."
            keyboard.append([
                InlineKeyboardButton(f"❌ {friend_name}", callback_data=f"remove_friend_{friend_id}")
            ])
        
        # Pagination
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"friends_list_page_{page-1}"))
        if total_pages > 1:
            nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="ignore"))
        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"friends_list_page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🔙 К друзьям", callback_data="friends")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def incoming_requests_menu(requests):
        """Incoming friend requests menu with action buttons"""
        keyboard = []
        
        # Add accept/decline buttons for first few requests
        for request in requests[:3]:  # Show only first 3 for space
            requester_id = request[0]
            requester_name = request[2] if request[2] else f"User {requester_id}"
            if len(requester_name) > 10:
                requester_name = requester_name[:7] + "..."
            
            keyboard.append([
                InlineKeyboardButton(f"✅ {requester_name}", callback_data=f"accept_friend_{requester_id}"),
                InlineKeyboardButton(f"❌ {requester_name}", callback_data=f"decline_friend_{requester_id}")
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 К друзьям", callback_data="friends")])
        return InlineKeyboardMarkup(keyboard)
