@echo off
echo 🤖 Starting Telegram Anonymous Chat Bot...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found

REM Check if required packages are installed
python -c "import telegram" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installing required packages...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Failed to install packages
        pause
        exit /b 1
    )
    echo ✅ Packages installed
) else (
    echo ✅ Packages already installed
)

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found!
    echo Please copy .env.example to .env and configure your settings
    echo.
    echo Example:
    echo copy .env.example .env
    echo Then edit .env file with your bot token and admin ID
    pause
    exit /b 1
)

REM Check configuration
python -c "from config import BOT_TOKEN, SUPER_ADMIN_ID" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Configuration error!
    echo Please check your .env file configuration
    echo Make sure BOT_TOKEN and SUPER_ADMIN_ID are properly set
    pause
    exit /b 1
)

echo ✅ Configuration looks good
echo.
echo 🚀 Starting the bot...
echo Press Ctrl+C to stop the bot
echo.

python bot.py
