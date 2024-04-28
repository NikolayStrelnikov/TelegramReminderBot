from logging import getLogger, handlers

# ЛОГИРОВАНИЕ
logger = getLogger(__name__)
handler = handlers.RotatingFileHandler('log/bot.log', maxBytes=10 * 1024 * 1024, backupCount=5)
logger.addHandler(handler)
logger.setLevel('INFO')
