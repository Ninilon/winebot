# winebot

A Telegram bot with Yandex Music integration and utility tools.

## Features

- **Yandex Music Integration** - Show currently playing track via inline mode (@bot ym)
- **Encrypted Token Storage** - All user tokens encrypted with AES-128
- **URL Shortener** - Shorten long URLs using TinyURL
- **File Converter** - Convert images and audio files (up to 100MB)
- **QR Code Generator** - Create QR codes for any text
- **Network Tools** - WHOIS and website status checking
- **Multi-language Support** - English and Russian

## Installation

1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/winebot.git
cd winebot
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure the bot by copying `.env.example` to `.env` and filling in your bot token
4. Run the bot:
```bash
python main.py
```

## Configuration

Required environment variables:
- `BOT_TOKEN` - Your Telegram bot token from @BotFather

Optional environment variables:
- `DB_ENCRYPTION_KEY` - Encryption key for database (will be auto-generated on first run)

## Usage

### Commands
- `/yamusic <token>` - Set your Yandex Music token
- `/short <url>` - Shorten a URL
- `/convert <format>` - Convert a file (reply to file with command)
- `/qr <text>` - Generate QR code
- `/whois <target>` - Get WHOIS information
- `/status <domain>` - Check website status
- `/settings` - Bot settings
- `/help` - Show help message

### Inline Modes
- `@bot ym` - Show currently playing track on Yandex Music
- `@bot qr <text>` - Generate QR code
- `@bot st <url>` - Check website status
- `@bot sys` - System information

## License

This project is licensed under the GNU General Public License v3.0
