import scrapy
import os
from scrapy.loader import ItemLoader
from alkoteka_scraper.items import AlkotekaItem


class AlkotekaSpider(scrapy.Spider):
    name = 'alkoteka_spider'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = self.load_start_urls()

    def load_start_urls(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Корень проекта
        urls_path = os.path.join(base_dir, 'alkoteka_scraper', 'urls.txt')  # Путь к файлу
        with open(urls_path, 'r') as f:
            return [line.strip() for line in f.readlines()]

    def parse(self, response):
        """
        Parse category pages to extract product links.
        """
        product_links = response.css('.product-card__link::attr(href)').getall()
        for link in product_links:
            yield response.follow(link, callback=self.parse_product)

    def parse_product(self, response):
        """
        Parse product page and extract structured data.
        """
        loader = ItemLoader(item=AlkotekaItem(), response=response)
        loader.add_value('url', response.url)
        loader.add_css('RPC', '.product-info__article::text')
        loader.add_css('title', '.product-info__title::text')
        loader.add_css('brand', '.product-info__brand::text')
        loader.add_css('section', '.breadcrumbs__list a::text')

        # Цена
        price_current = response.css('.price--current::text').get()
        price_original = response.css('.price--original::text').get()
        sale_tag = f"Скидка {self.calculate_discount(price_current, price_original)}%" if price_original else ""

        loader.add_value('price_data', {
            'current': float(price_current.replace(' ', '')) if price_current else None,
            'original': float(price_original.replace(' ', '')) if price_original else None,
            'sale_tag': sale_tag
        })

        # Наличие
        in_stock = bool(response.css('.availability--in-stock'))
        loader.add_value('stock', {'in_stock': in_stock, 'count': 0})

        # Изображения
        loader.add_value('assets', {
            'main_image': response.css('.gallery__main-image::attr(src)').get(),
            'set_images': response.css('.gallery__thumbs img::attr(src)').getall(),
            'view360': [],
            'video': []
        })

        # Метаданные
        metadata = {'__description': response.css('.product-info__description::text').get()}
        for char in response.css('.characteristics__item'):
            key = char.css('.characteristics__key::text').get()
            value = char.css('.characteristics__value::text').get()
            if key and value:
                metadata[key] = value
        loader.add_value('metadata', metadata)

        # Варианты
        loader.add_value('variants', len(response.css('.product-variants .variant')))

        yield loader.load_item()

    def calculate_discount(self, current, original):
        """
        Calculate discount percentage.
        """
        if not current or not original:
            return 0
        return round((1 - float(current) / float(original)) * 100, 2)