import requests
# import config


class TelegramClient:
    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url

    def prepare_url(self, method: str):
        result_url = f'{self.base_url}/bot{self.token}/'
        if method is not None:
            result_url += method
        return result_url

    def post(self, method: str = None, params: dict = None, body: dict = None):
        url = self.prepare_url(method)
        resp = requests.post(url, params=params, data=body)
        return resp.json()


# if __name__ == '__main__':
#     telegram_client = TelegramClient(token=config.TOKEN, base_url=config.BASE_URL)
#     my_params = {'chat_id': config.ADMIN_CHAT_ID, 'text': 'тестовое сообщение'}
#     print(telegram_client.post(method='sendMessage', params=my_params))
