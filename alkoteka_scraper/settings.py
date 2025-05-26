BOT_NAME = "alkoteka_scraper"
SPIDER_MODULES = ["alkoteka_scraper.spiders"]
NEWSPIDER_MODULE = "alkoteka_scraper.spiders"

# Настройки пользовательского агента и robots.txt
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
ROBOTSTXT_OBEY = False

# Региональные настройки
REGION_NAME = 'Краснодар'

# Настройки задержек и параллелизма
DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 2
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 5

# Настройки повторных попыток
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 403, 408, 429]

# Настройки прокси
ROTATING_PROXY_LIST = [
    '45.140.143.77:18080'
]

ROTATING_PROXY_PAGE_RETRY_TIMES = 3

# Настройки кэширования
HTTPCACHE_ENABLED = False

# Настройки экспорта
FEED_EXPORT_ENCODING = "utf-8"

# Middleware
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
    "scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware": 110,
}

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://alkoteka.com/",
}

# Настройки логирования
LOG_LEVEL = 'INFO'
