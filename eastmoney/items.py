# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class PostItem(Item):
    stock_id        = Field()
    url             = Field()
    title           = Field()
    username        = Field()
    content         = Field()
    created_time    = Field()
    updated_time    = Field()
    read_count      = Field()
    comment_count   = Field()
    thumbup_count   = Field()
    forward_count   = Field()
    share_count     = Field()
    favourite_count = Field()
