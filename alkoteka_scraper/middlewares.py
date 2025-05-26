import random
from scrapy import signals



class AlkotekaScraperDownloaderMiddleware:
    """
    Middleware for handling proxies and cookies for the region.
    """

    def __init__(self, proxy_list):
        self.proxies = proxy_list

    @classmethod
    def from_crawler(cls, crawler):
        proxy_list = crawler.settings.get('PROXY_LIST', [])
        return cls(proxy_list)

    def process_request(self, request, spider):
        # Устанавливаем фиксированный регион Краснодар
        request.cookies = {"BITRIX_SM_CITY": "krd"}  # Краснодар

        # Подключаем случайный прокси
        if self.proxies:
            proxy = random.choice(self.proxies)
            spider.logger.info(f"Using proxy: {proxy}")
            request.meta['proxy'] = proxy

        return None

    def process_response(self, request, response, spider):
        # Обрабатываем статус-коды, если нужно
        if response.status == 403:
            spider.logger.warning(f"Blocked request: {response.url}")
        return response

    def process_exception(self, request, exception, spider):
        # Логируем исключения
        spider.logger.error(f"Exception during request {request.url}: {exception}")
        return None


class RotatedProxyMiddleware:
    def __init__(self, proxy_list):
        self.proxy_list = proxy_list

    @classmethod
    def from_crawler(cls, crawler):
        proxy_list = crawler.settings.get("ROTATING_PROXY_LIST", [])
        if not proxy_list:
            raise ValueError("No proxies found in settings!")
        return cls(proxy_list)

    def process_request(self, request, spider):
        if not request.meta.get("proxy"):
            proxy = random.choice(self.proxy_list)
            spider.logger.info(f"Using proxy: {proxy}")
            request.meta["proxy"] = f"http://{proxy}"