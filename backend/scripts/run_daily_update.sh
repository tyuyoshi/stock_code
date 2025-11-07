#!/bin/bash
# Daily update script wrapper for cron execution

set -e  # Exit on any error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

# Change to app directory
cd "$APP_DIR"

# Timestamp for logging
echo "$(date '+%Y-%m-%d %H:%M:%S'): Starting daily stock price update"

# Check if it's a trading day using Python trading calendar
# The trading calendar includes Japanese holidays
echo "$(date '+%Y-%m-%d %H:%M:%S'): Checking if today is a trading day"
TRADING_DAY_CHECK=$(python -c "
import sys
sys.path.append('${APP_DIR}')
from services.trading_calendar import is_trading_day
print('yes' if is_trading_day() else 'no')
" 2>/dev/null)

if [ "$TRADING_DAY_CHECK" != "yes" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): Today is not a trading day, skipping update"
    exit 0
fi

echo "$(date '+%Y-%m-%d %H:%M:%S'): Today is a trading day, proceeding with update"

# Set environment variables
export PYTHONPATH="${APP_DIR}:${PYTHONPATH}"

# Activate virtual environment if it exists
if [ -f "${APP_DIR}/venv/bin/activate" ]; then
    source "${APP_DIR}/venv/bin/activate"
    echo "$(date '+%Y-%m-%d %H:%M:%S'): Virtual environment activated"
fi

# Run the daily update
echo "$(date '+%Y-%m-%d %H:%M:%S'): Executing daily update job"
python -m batch.daily_update

# Check exit code
if [ $? -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S'): Daily update completed successfully"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S'): Daily update failed with exit code $?"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S'): Daily update script finished"