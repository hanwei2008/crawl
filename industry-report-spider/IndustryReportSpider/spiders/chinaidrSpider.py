# -*- coding: utf-8 -*-

# Filename: IndustryReportSpiders

# Copyright (c) 2015 Chengdu Lanjing Data&Information Co., Ltd

import re
from urlparse import urljoin
from scrapy import FormRequest
from scrapy_tools.misc import clean_text, parse_date
from scrapy.contrib.spiders import CrawlSpider
from IndustryReportSpider.items import IndustryReportSpiderItem
from IndustryReportSpider.Utils import parseIndustryName


class IndustryReportSpiderIDR(CrawlSpider):
    name = "industry-idr"
    allowed_domains = ["chinaidr.com"]
    base_url = "http://www.chinaidr.com"
    start_urls = ["http://www.chinaidr.com/trade/electricity"]
    pattern = re.compile(ur"[\W]*[a-zA-Z0-9\u4e00-\u9fa5][\W]*")

    def __init__(self, *a, **kw):
        super(IndustryReportSpiderIDR, self).__init__(*a, **kw)

    def parse(self, response):
        large_categories = response.xpath("//*[@class='tabContent bluelink']//*[contains(@style, 'padding')]/a")
        for large_category in large_categories:
            large_category_name = clean_text(large_category.xpath(".//text()").extract()[0].strip())
            mid_categorys = large_category.xpath("./parent::*/following-sibling::*[1]/a")
            for mid_category in mid_categorys:
                mid_category_name = clean_text(mid_category.xpath("./text()").extract()[0])
                mid_category_url = urljoin(self.base_url, mid_category.xpath("./@href").extract()[0])
                request = FormRequest(mid_category_url, callback=self.parse_middle_category, dont_filter=True)
                request.meta["large_category_name"] = large_category_name
                request.meta["mid_category_name"] = mid_category_name
                yield request

    def parse_middle_category(self, response):
        report_types = response.xpath(u"//li[contains(text(),'报告')]")
        for report_type in report_types:
            mid_category_url = urljoin(self.base_url, report_type.xpath(u"./preceding-sibling::span[1]/a/@href").extract()[0])
            request = FormRequest(mid_category_url, callback=self.parse_page, dont_filter=True)
            request.meta["large_category_name"] = response.meta["large_category_name"]
            request.meta["mid_category_name"] = response.meta["mid_category_name"]
            request.meta["report_type"] = clean_text(report_type.xpath("./text()").extract()[0].strip())
            request.meta["page_base_url"] = mid_category_url
            yield request

    def parse_page(self, response):
        request_list = self._parse_list(response)
        for r in request_list:
            yield r
        next_page = response.xpath(u"//*[@id='AspNetPager1']/a[text()=\"下一页\"]/@href")
        if len(next_page) > 0:
            next_page_url = urljoin(self.base_url, next_page.extract()[0])
            if not next_page_url.startswith(response.meta["page_base_url"]):
                if next_page_url.endswith("html"):
                    next_page_url = response.meta["page_base_url"] + next_page_url[next_page_url.rindex("/") + 1:len(next_page_url)]
            request = FormRequest(next_page_url, callback=self.parse_page, dont_filter=True)
            request.meta["large_category_name"] = response.meta["large_category_name"]
            request.meta["mid_category_name"] = response.meta["mid_category_name"]
            request.meta["report_type"] = response.meta["report_type"]
            request.meta["page_base_url"] = response.meta["page_base_url"]
            yield request

    def _parse_list(self, response):
        report_list = response.xpath("//div[@class=\"reportlist bluelink\"]/ul//a/@href")
        for report_url in report_list:
            request = FormRequest(urljoin(self.base_url, report_url.extract()), callback=self.parse_item, dont_filter=False)
            request.meta["large_category_name"] = response.meta["large_category_name"]
            request.meta["mid_category_name"] = response.meta["mid_category_name"]
            request.meta["report_type"] = response.meta["report_type"]
            yield request

    def parse_item(self, response):
        item = IndustryReportSpiderItem()
        item["industry_large_category"] = response.meta["large_category_name"]
        item["industry_mid_category"] = response.meta["mid_category_name"]
        item["report_name"] = clean_text(response.xpath("//h1/text()").extract()[0].strip())
        item["report_type"] = response.meta["report_type"]
        item["industry_small_chs_name"] = parseIndustryName(item["report_name"])
        item["price_free"] = self._parse_price(response)
        item["report_link"] = response.url
        item["source_domain"] = self.base_url
        item["source_name"] = u"中国产业发展研究网"
        yield item


# 提取收费标准
    def _parse_price(self, response):
        price = response.xpath(ur"//p[contains(text(),'报告名称')][1]//text()")
        if price:
            price = price.extract()
            if re.search(ur"(?:[0-9]+RMB)|(?:协商定价)", "".join(price)):
                return False
            else:
                return True
        else:
            return True
