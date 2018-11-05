# -*- coding: utf-8 -*-

from pymongo import MongoClient
from eastmoney.items import PostItem

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

class MongoDB(object):
    def __init__(self, host, port, database, collection):
        self.host = host
        self.port = port
        self.database = database
        self.collection = collection
        self.conn = MongoClient(self.host, self.port)
        self.db = self.conn[self.database]
        self.collection = self.db[self.collection]

    def get_one(self, query):
        return self.collection.find_one(query, projection = {"_id": False})

    def get_all(self, query):
        return self.collection.find(query)

    def add_one(self, kv_dict):
        return self.collection.insert_one(kv_dict)

    def add_many(self, kv_dict):
        return self.collection.insert_many(kv_dict)

    def delete(self, query):
        return self.collection.delete_many(query)

    def check_exist(self, query):
        ret = self.collection.find_one(query)
        return ret != None

    def update(self, query, kv_dict):
        self.collection.update_one(query, {
            '$set': kv_dict
        }, upsert=True)

class EastmoneyPipeline(object):
    def __init__(self):
        self.database = MongoDB("localhost", 27017, "EastMoney", "Post")

    def process_item(self, item, spider):
        if type(item) is PostItem:
            self.database.update({'url': item['url']}, {
                'url': item['url'],
                'username': item['username'],
                'title': item['title'],
                'content': item['content'],
                'created_time': item['created_time'],
                'updated_time': item['updated_time'],
                'read_count': item['read_count'],
                'comment_count': item['comment_count']
            })

