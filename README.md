# 🤖 Anonymous Telegram Chat Bot

A sophisticated Telegram bot for anonymous chatting with intelligent user matching, premium features, and comprehensive admin tools.

## ✨ Key Features

### 🔐 Anonymous Chatting
- Complete anonymity between users
- No personal information sharing
- Secure message forwarding
- End-to-end chat sessions

### 🎯 Smart Matching System
- Gender-based filtering (Premium feature)
- Age group filtering (Premium feature)
- Intelligent two-way matching algorithm
- Real-time partner search
- Queue management system

### ⭐ Rating & Reputation
- Post-chat rating system (1-5 stars)
- Average user rating calculation
- Rating-based user reputation
- Anti-spam rating protection

### 🚀 Friends System
- Add friends after chats
- Friend requests management
- Friends list with profiles
- Friendship statistics

### 💎 Premium Features
- Advanced search filters
- Priority matching
- No mandatory channel subscriptions
- Enhanced user experience
- Telegram Stars payment integration

### 🛡️ Security & Moderation
- Rate limiting protection
- Input validation and sanitization
- User reporting system
- Admin ban management
- Session security

### 👑 Admin Panel
- User management and statistics
- Broadcast messaging
- Channel management
- Reports handling
- Premium subscription management
- Advanced analytics

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Step 1: Clone & Setup Environment
```bash
# Clone the repository
git clone <your-repo-url>
cd singleAnonim

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Create a `.env` file in the root directory:

```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
BOT_USERNAME=your_bot_username
SUPER_ADMIN_ID=your_telegram_user_id

# Database
DATABASE_URL=sqlite:///chat_bot.db
```

### Step 3: Initial Setup
```bash
# Run the bot for the first time
python bot.py
```

### Step 4: Admin Setup
1. Send `/start` to your bot
2. Use `/admin` command to access admin panel
3. Configure mandatory channels (optional)
4. Set up subscription plans (optional)

## 🖥️ Usage

### For Windows Users
Simply run `start_bot.bat` to start the bot with automatic dependency checking.

### For Linux/macOS Users
```bash
python bot.py
```

### Admin Commands
- `/admin` - Access admin panel
- `/start` - Restart/register user

### User Flow
1. **Registration**: Gender and age group selection
2. **Matching**: Find chat partners with optional filters
3. **Chatting**: Anonymous conversations with media support
4. **Rating**: Rate partners after chat sessions
5. **Friends**: Add interesting people as friends

## Fayl tuzilishi

```
singleAnonim/
├── bot.py              # Asosiy bot fayli
├── config.py           # Konfiguratsiya sozlamalari
├── database.py         # Ma'lumotlar bazasi boshqaruvi
├── keyboards.py        # Inline tugmalar layoutlari
├── requirements.txt    # Python kutubxonalari
├── README.md          # Loyiha haqida ma'lumot
└── chat_bot.db        # SQLite ma'lumotlar bazasi (avtomatik yaratiladi)
```

## Bot funksiyalari

### 1. Foydalanuvchi ro'yxatdan o'tishi
- `/start` buyrug'i
- Majburiy kanallar tekshiruvi
- Jins tanlash (Erkak/Ayol/Boshqa)
- Yosh guruhi tanlash (18-24/25-34/35+/Boshqa)

### 2. Suhbatdosh qidirish
- Gender filtri (Erkak/Ayol/Farqi yo'q)
- Yosh filtri (18-24/25-34/35+/Farqi yo'q)
- Smart matching algoritmi
- Real-time qidiruv

### 3. Suhbat boshqaruvi
- Real-time xabar almashish
- Rasm, video, audio, sticker yuborish
- Next tugmasi - yangi suhbatdosh qidirish
- Leave tugmasi - suhbatni tugatish
- Report tugmasi - foydalanuvchini shikoyat qilish

### 4. Reyting tizimi
- Suhbat tugagach 1-5 yulduz rating
- Foydalanuvchi reytingi hisoblanishi
- Rating ma'lumotlarini ko'rsatish

### 5. Sozlamalar
- Profil ma'lumotlarini yangilash
- Botdan chiqish

## Ma'lumotlar bazasi tuzilishi

Bot SQLite ma'lumotlar bazasini ishlatadi va quyidagi jadvallarni yaratadi:

- `users` - Foydalanuvchi ma'lumotlari
- `chat_sessions` - Suhbat sessiyalari
- `ratings` - Foydalanuvchi reytinglari
- `waiting_queue` - Kutish navbati
- `reports` - Shikoyatlar

## Xatoliklarni bartaraf etish

1. **Bot token xatosi**: `config.py` da to'g'ri token kiritilganligini tekshiring
2. **Ma'lumotlar bazasi xatosi**: Bot fayli bilan bir xil papkada yozish huquqi borligini tekshiring
3. **Kanal xatosi**: Bot kanalga admin sifatida qo'shilganligini tekshiring

## Xavfsizlik

- Bot hech qanday shaxsiy ma'lumotlarni saqlamaydi
- Barcha suhbatlar anonim
- Foydalanuvchi ID'lari maxfiy
- Ma'lumotlar mahalliy SQLite bazasida saqlanadi

## Qo'llab-quvvatlash

Loyiha haqida savollariz bo'lsa, issue ochishingiz mumkin.

## Litsenziya

Bu loyiha MIT litsenziyasi ostida tarqatiladi.
