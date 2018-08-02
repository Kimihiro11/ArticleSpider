# -*- coding: utf-8 -*-
import scrapy
import re
import datetime

from scrapy.http import Request
from scrapy.loader import ItemLoader
from urllib import parse

from ArticleSpider2.items import JobBoleArticleItem
from ArticleSpider2.utils.common import get_md5

class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        post_nodes = response.xpath('//*[@id="archive"]//div[@class="post-thumb"]/a')

        for post_node in post_nodes:
            front_src = post_node.css('img::attr(src)').extract_first("")
            post_url = post_node.css('::attr(href)').extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), meta={'front_image_url': front_src}, callback=self.parseDetail)

        #
        # next_url = response.css('.next.page-numbers::attr(href)').extract_first()
        # if next_url:
        #     yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parseDetail(self, response):
        article_item = JobBoleArticleItem()

        front_image_url  =  response.meta.get('front_image_url', '')
        title = response.xpath('//div[@class="entry-header"]/h1/text()').extract()[0]
        create_date = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/text()').extract()[0].strip().replace('·','').strip()
        praise_nums = response.xpath('//span[contains(@class,"vote-post-up")]/h10/text()').extract()[0]
        fav_nums = response.xpath('//span[contains(@class, "bookmark-btn")]/text()').extract()[0]
        match_re = re.match('.*?(\d+).*',fav_nums)
        if match_re:
            fav_nums = int(match_re.group(1))
        else:
            fav_nums = 0
        comment_nums = response.xpath('//a[@href="#article-comment"]/span/text()').extract()[0]
        match_re = re.match('.*?(\d+).*',comment_nums)
        if match_re:
            comment_nums = int(match_re.group(1))
        else:
            comment_nums = 0
        # content = response.xpath('//div[@class="entry"]').extract()[0]
        tag_list = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        tag_list = [element for element in tag_list if not element.strip().endswith('评论')]
        tags = ','.join(tag_list)

        article_item["front_image_url"] = [front_image_url]
        article_item["url"] = response.url
        article_item["url_object_id"] = get_md5(response.url)
        article_item["title"] = title
        try:
            create_date = datetime.datetime.strptime(create_date, '%Y/%m/%d').date()
        except Exception as e:
            create_date = datetime.datetime.now().date()
        article_item["create_date"] = create_date
        article_item["praise_nums"] = praise_nums
        article_item["fav_nums"] = fav_nums
        article_item["comment_nums"] =comment_nums
        # article_item["content"] = content
        article_item["tags"] = tags

        #通过ItemLoader加载item
        item_loader = ItemLoader(item=JobBoleArticleItem, response=response)
        item_loader.add_xpath()

        yield article_item