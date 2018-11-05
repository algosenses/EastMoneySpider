# -*- coding: utf-8 -*-
import re
import math
import datetime
import lxml.etree
import lxml.html
import logging
from pymongo import MongoClient
from selenium import webdriver
from scrapy.spiders import Spider
from scrapy import Selector
from scrapy.http import Request
from eastmoney.items import PostItem


HOST_URL = "http://guba.eastmoney.com/"
LIST_URL = HOST_URL + "list,{stock_id},f_{page}.html"

class EastMoneySpider(Spider):
    name = 'EastMoneySpider'
    allowed_domains = ['eastmoney.com']
    start_urls = ['http://eastmoney.com/']

    def __init__(self, stock_id):
        self.stock_id = stock_id
        self._existed_urls = self._get_existed_urls()

    def start_requests(self):
        stock_id = self.stock_id
        request = Request(LIST_URL.format(stock_id=self.stock_id, page=1))
        request.meta['stock_id'] = stock_id
        request.meta['page'] = 1
        yield request

    def parse(self, response):
        selector = Selector(response)

        page = response.meta['page']
        if page == 1: # first page fetched.
            #self.total_pages = self._get_total_pages_num(response.url)
            page_data = selector.xpath('//div[@id="mainbody"]/div[@id="articlelistnew"]/div[@class="pager"]/span/@data-pager').extract()
            if page_data:
                page_data = re.findall('\|(\d+)', page_data[0])
                self.total_pages = math.ceil(int(page_data[0]) / int(page_data[1]))
            else:
                self.total_pages = 1

        logging.info("========= Parsing page %d... =========" % page)

        stock_id = re.search('\d+', response.url).group(0)

        posts = selector.xpath('//div[@class="articleh"]') + selector.xpath('//div[@class="articleh odd"]')
        for index, post in enumerate(posts):
            link = post.xpath('span[@class="l3"]/a/@href').extract()
            if link:
                if link[0].startswith('/'):
                    link = "http://guba.eastmoney.com/" + link[0][1:]
                else:
                    link = "http://guba.eastmoney.com/" + link[0]

                if link in self._existed_urls:
                    continue

            # drop set-top or ad post
            type = post.xpath('span[@class="l3"]/em/@class').extract()
            if type:
                type = type[0]
                if type == 'ad' or type == 'settop' or type == 'hinfo':
                    continue
            else:
                type = 'normal'

            read_count = post.xpath('span[@class="l1"]/text()').extract()
            comment_count = post.xpath('span[@class="l2"]/text()').extract()
            username = post.xpath('span[@class="l4"]/a/text()').extract()
            updated_time = post.xpath('span[@class="l5"]/text()').extract()
            if not read_count or not comment_count or not username or not updated_time:
                continue

            item = PostItem()
            item['stock_id'] = stock_id
            item['read_count'] = int(read_count[0])
            item['comment_count'] = int(comment_count[0])
            item['username'] = username[0].strip('\r\n').strip()
            item['updated_time'] = updated_time[0]
            item['url'] = link

            if link:
                yield Request(url=link, meta={'item': item, 'PhantomJS': True}, callback=self.parse_post)


        if page < self.total_pages:
            stock_id = self.stock_id
            request = Request(LIST_URL.format(stock_id=self.stock_id, page=page+1))
            request.meta['stock_id'] = stock_id
            request.meta['page'] = page + 1
            yield request


    def parse_post(self, response):
        item = response.meta['item']
        selector = Selector(response)
        title = selector.xpath('//div[@id="zwconttbt"]/text()').extract()
        if not title:
            return

        item['title'] = title[0].strip('\r\n').strip()

        created_time = re.search('[\d\-: ]+', selector.xpath('//div[@class="zwfbtime"]/text()').extract()[0]).group(0)
        item['updated_time'] = created_time[1:5] + '-' + item['updated_time']

        created_time = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', created_time)[0]
        item['created_time'] = datetime.datetime.strptime(created_time, "%Y-%m-%d %H:%M:%S")

        updated_time = re.findall(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', item['updated_time'])[0]
        item['updated_time'] = datetime.datetime.strptime(updated_time, "%Y-%m-%d %H:%M")

        content = lxml.html.fromstring(selector.xpath('//div[@id="zwconbody"]/div[@class="stockcodec"]').extract()[0].strip('\r\n').strip())
        content = lxml.html.tostring(content, method="text", encoding='unicode')
        content = content.strip('\r\n').strip()
        item['content'] = content

        yield item

    def _get_total_pages_num(self, url):
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('lang=zh_CN.UTF-8')
            chrome_options.add_argument('User-Agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.162 Safari/537.36"')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')

            driver = webdriver.Chrome(chrome_options=chrome_options)
            driver.get(url)
            page_data = driver.find_element_by_xpath('//div[@id="mainbody"]/div[@id="articlelistnew"]/div[@class="pager"]/span[@class="pagernums"]').get_attribute('data-pager')
            if page_data:
                page_nums = re.findall('\|(\d+)', page_data[0])
                total_pages = math.ceil(int(page_nums[0]) / int(page_nums[1]))
            driver.quit()
        except Exception as e:
            total_pages = 1

        return int(total_pages)

    def _is_existed(self, url):
        return True

    def _get_existed_urls(self):
        conn = MongoClient("localhost", 27017)
        db = conn["EastMoney"]
        collection = db["Post"]
        urls = collection.find({},  {'url':1, '_id':0})
        s = set()
        for x in urls:
            for k, v in x.items():
                s.add(v)
        return s

