from logging import getLogger, handlers, Formatter

# Логирование
logger = getLogger(__name__)
handler = handlers.RotatingFileHandler('log/bot.log', maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')

# Формат сообщений лога
formatter = Formatter('%(levelname)s - %(asctime)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel('DEBUG')


# DEBUG: наименее серьезный уровень. Обычно используется для диагностики
# INFO: используется для подтверждения того, что все работает как ожидалось
# WARNING: указывает на то, что произошло что-то необычное, или на возможную проблему в будущем
# ERROR: указывает на более серьезную проблему, которая не позволила программе выполнить что-то
# CRITICAL: наиболее серьезный уровень. Индицирует очень серьезную проблему


def read_last_log(filename='log/bot.log', lines=10):
    with open(filename, 'r', encoding='utf-8') as f:
        return ''.join(f.readlines()[-lines:])
