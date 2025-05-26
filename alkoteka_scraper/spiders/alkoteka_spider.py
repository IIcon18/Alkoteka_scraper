import scrapy
import json
import urllib.parse
import random
from scrapy.exceptions import CloseSpider
import time


class AlkotekaSpider(scrapy.Spider):
    name = "alkoteka_spider"

    city_uuid = "4a70f9e0-46ae-11e7-83ff-00155d026416"
    per_page = 20
    max_pages = None

    def __init__(self, *args, **kwargs):
        super(AlkotekaSpider, self).__init__(*args, **kwargs)
        self.proxy_stats = {}
        self.failed_proxies = set()

    def start_requests(self):
        try:
            with open('../alkoteka_scraper/urls.txt', 'r', encoding='utf-8') as file:
                for line in file:
                    url = line.strip()
                    if not url:
                        continue

                    parsed_url = urllib.parse.urlparse(url)
                    path_parts = parsed_url.path.strip('/').split('/')

                    if 'catalog' in path_parts:
                        idx = path_parts.index('catalog')
                        try:
                            root_category_slug = path_parts[idx + 1]
                        except IndexError:
                            self.logger.warning(f"Не удалось найти root_category_slug в ссылке: {url}")
                            continue
                    else:
                        self.logger.warning(f"Неверная структура URL: {url}")
                        continue

                    options = {}
                    if len(path_parts) > idx + 2 and path_parts[idx + 2].startswith('options-'):
                        raw_options = path_parts[idx + 2].replace('options-', '')
                        opt_parts = raw_options.split('_')
                        for i in range(0, len(opt_parts) - 1, 2):
                            key = opt_parts[i]
                            val = opt_parts[i + 1]
                            options.setdefault(key, []).append(val)

                    meta = {
                        'page_number': 1,
                        'root_category_slug': root_category_slug,
                        'options': options,
                        'retry_times': 0,
                        'proxy_retry_times': 0
                    }

                    yield self.create_request(meta)
        except FileNotFoundError:
            self.logger.error("Файл urls.txt не найден")
            raise CloseSpider('FileNotFound')

    def create_request(self, meta):
        page = meta['page_number']
        root_category_slug = meta['root_category_slug']
        options = meta.get('options', {})

        base_url = f'https://alkoteka.com/web-api/v1/product?city_uuid={self.city_uuid}&page={page}&per_page={self.per_page}&root_category_slug={root_category_slug}'

        for key, values in options.items():
            for val in values:
                param_name = f'options[{key}][]'
                base_url += f"&{param_name}={val}"

        current_proxy = None
        if self.settings.get('ROTATING_PROXY_LIST'):
            active_proxies = [p for p in self.settings['ROTATING_PROXY_LIST'] if p not in self.failed_proxies]
            if active_proxies:
                current_proxy = random.choice(active_proxies)
                self.proxy_stats[current_proxy] = self.proxy_stats.get(current_proxy, 0) + 1

        return scrapy.Request(
            base_url,
            callback=self.parse,
            errback=self.errback_httpbin,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://alkoteka.com/",
            },
            meta={
                **meta,
                'proxy': current_proxy,
                'download_timeout': 30
            }
        )

    def parse(self, response):
        meta = response.meta
        page_number = meta['page_number']
        root_category_slug = meta['root_category_slug']

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON from response: {response.text[:200]}")
            yield self.retry_request(meta, reason="JSONDecodeError")
            return

        products = data.get("results", [])
        self.logger.info(f"Number of products on page {page_number}: {len(products)}".replace("\n", ""))

        for product in products:
            timestamp = int(time.time())
            rpc = product.get("uuid", "")
            url = product.get("product_url", "")
            title = product.get("name", "")
            attributes = product.get("attributes", {})
            color = attributes.get("color", "")
            volume = attributes.get("volume", "")
            if color or volume:
                title = f"{title}, {color or volume}"

            marketing_tags = product.get("tags", [])
            brand = product.get("brand", {}).get("name", "")
            section = product.get("category", {}).get("breadcrumb", [])
            section = section.split(" > ") if isinstance(section, str) else section

            price_current = product.get("price", 0.0)
            price_original = product.get("original_price", price_current)
            sale_tag = f"Скидка {round((1 - price_current / price_original) * 100)}%" if price_original > price_current else None

            stock_count = product.get("quantity_total", 0)
            in_stock = stock_count > 0

            main_image = product.get("image_url", "")
            set_images = product.get("images", [])
            view360 = product.get("view360", [])
            video = product.get("video", [])

            metadata = attributes
            description = product.get("description", "")
            metadata["__description"] = description

            variants = len(product.get("variants", []))

            yield {
                "timestamp": timestamp,
                "RPC": rpc,
                "url": url,
                "title": title,
                "marketing_tags": marketing_tags,
                "brand": brand,
                "section": section,
                "price_data": {
                    "current": price_current,
                    "original": price_original,
                    "sale_tag": sale_tag
                },
                "stock": {
                    "in_stock": in_stock,
                    "count": stock_count
                },
                "assets": {
                    "main_image": main_image,
                    "set_images": set_images,
                    "view360": view360,
                    "video": video
                },
                "metadata": metadata,
                "variants": variants
            }

        current_page = data.get("meta", {}).get("current_page", page_number)
        total_pages = data.get("meta", {}).get("total", 1)
        print(f"{current_page}/{total_pages} {root_category_slug}")

        if current_page < total_pages and (self.max_pages is None or current_page < self.max_pages):
            meta['page_number'] += 1
            yield self.create_request(meta)

    def errback_httpbin(self, failure):
        meta = failure.request.meta
        proxy = meta.get('proxy')

        if proxy:
            self.failed_proxies.add(proxy)

        if meta.get('proxy_retry_times', 0) < self.settings.get('ROTATING_PROXY_PAGE_RETRY_TIMES', 3):
            meta['proxy_retry_times'] += 1
            yield self.create_request(meta)