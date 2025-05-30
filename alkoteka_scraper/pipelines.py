# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import json
from datetime import datetime


class SaveToFilePipeline:
    """
    Pipeline for saving items to a JSON file.
    """

    def process_item(self, item, spider):
        # Добавляем timestamp
        item['timestamp'] = int(datetime.now().timestamp())
        return item
