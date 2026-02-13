#!/bin/bash

# --- НАСТРОЙКИ ---
BOT_SCRIPT="main.py"
VENV_PATH="venv/bin/activate"
LOG_FILE="bot.log"
# -----------------

# Цвета для красоты
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

status_bot() {
    PID=$(pgrep -f "$BOT_SCRIPT")
    if [ -n "$PID" ]; then
        echo -e "${GREEN}● Бот запущен (PID: $PID)${NC}"
        return 0
    else
        echo -e "${RED}○ Бот остановлен${NC}"
        return 1
    fi
}

start_bot() {
    if status_bot > /dev/null; then
        echo -e "${YELLOW}⚠️ Бот уже работает!${NC}"
    else
        echo -e "${YELLOW}🚀 Запуск бота...${NC}"
        source "$VENV_PATH"
        nohup python3 "$BOT_SCRIPT" > "$LOG_FILE" 2>&1 &
        sleep 2
        status_bot
    fi
}

stop_bot() {
    PID=$(pgrep -f "$BOT_SCRIPT")
    if [ -n "$PID" ]; then
        echo -e "${YELLOW}🛑 Останавливаю бота (PID: $PID)...${NC}"
        kill "$PID"
        sleep 1
        echo -e "${GREEN}✅ Остановлено${NC}"
    else
        echo -e "${RED}⚠️ Бот не запущен${NC}"
    fi
}

show_logs() {
    echo -e "${YELLOW}📂 Вывод последних 50 строк логов (Ctrl+C для выхода):${NC}"
    tail -f -n 50 "$LOG_FILE"
}

case "$1" in
    start)   start_bot ;;
    stop)    stop_bot ;;
    restart) stop_bot; start_bot ;;
    status)  status_bot ;;
    logs)    show_logs ;;
    *)       echo -e "Использование: $0 {${GREEN}start${NC}|${RED}stop${NC}|${YELLOW}restart${NC}|status|logs}" ;;
esac
