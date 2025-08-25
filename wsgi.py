#!/usr/bin/env python3
"""
WSGI entry point for Gunicorn deployment on Render.com

This file configures the Flask web dashboard to run with Gunicorn
while keeping the Discord bot running in a separate thread.
"""

import os
import sys
import threading
import logging
from pathlib import Path

# Add the src directory to Python path (same as main.py)
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from src.bot import HawkBot
from web.app import WebDashboard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('WSGI')

# Create bot instance
bot = HawkBot()

# Create Flask app instance
web_dashboard = WebDashboard()
app = web_dashboard.app

def start_discord_bot():
    """Start the Discord bot in a separate thread"""
    try:
        logger.info("Starting Discord bot...")
        bot.run(os.getenv('DISCORD_TOKEN'))
    except Exception as e:
        logger.error(f"Error starting Discord bot: {e}")

# Start Discord bot in background thread when WSGI app starts
if os.getenv('RENDER'):
    logger.info("Starting Discord bot in background thread for Render deployment")
    bot_thread = threading.Thread(target=start_discord_bot, daemon=True)
    bot_thread.start()

if __name__ == "__main__":
    # For local development
    port = int(os.getenv('PORT', 10000))
    
    # Use waitress for local development, Gunicorn handles production on Render
    try:
        from waitress import serve
        logger.info(f"Starting with Waitress on port {port}")
        serve(app, host='0.0.0.0', port=port, threads=4)
    except ImportError:
        logger.info(f"Starting with Flask dev server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)