#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author : yuantaocai
# Date:   15-5-16
# Email:  yuantaocai@163.com
# Filename: IndustryReportSpiderChinabgao
# Copyright (c) 2015 Chengdu Lanjing Data&Information Co., Ltd

import re
from urlparse import urljoin
import pytz
from scrapy import FormRequest
from scrapy.contrib.spiders import CrawlSpider
import time
from scrapy_tools.misc import clean_text,parse_date
from IndustryReportSpider.items import IndustryReportSpiderItem
from IndustryReportSpider.Utils import parseIndustryName

class IndustryReportSpiderChinabgao(CrawlSpider):
    name = "industry_chinabgao"
    allowed_domains = ["chinabgao.com"]
    base_url = "http://www.chinabgao.com/"
    start_urls = ["http://www.chinabgao.com/report/"]
    pattern = re.compile(ur"[\W]*[a-zA-Z0-9\u4e00-\u9fa5][\W]*")
    pattern_page = re.compile(ur"第\s+(\d+)\s+页[,，]\s+共\s+(\d+)\s+页")

    def __init__(self, *a, **kw):
        super(IndustryReportSpiderChinabgao, self).__init__(*a, **kw)
        self.prePauseTime = time.time()

    def parse(self, response):
        large_categories = response.xpath(".//*[@id='cateitems']//h3//a")
        for large_category in large_categories:
            large_category_name = clean_text(large_category.xpath("./text()").extract()[0].strip())
            page_url = large_category.xpath("./@href").extract()[0]
            request = FormRequest(page_url, callback=self.parse_middle_category, dont_filter=True)
            request.meta["large_category"] = large_category_name
            yield request

    def parse_middle_category(self, response):
        mid_categories = response.xpath(".//*[@id='catgory_container']//a")
        for mid_category in mid_categories:
            mid_category_name = clean_text(mid_category.xpath("./text()").extract()[0].strip())
            page_url = mid_category.xpath("./@href").extract()[0]
            if((mid_category_name!=u'不限') & ("report" in page_url)):
                url = urljoin(self.base_url, page_url)
                request = FormRequest(url, callback=self._parse_firstPage, dont_filter=True)
                request.meta["large_category"] = response.meta["large_category"]
                request.meta["mid_category"] = mid_category_name
                request.meta["first_url"] = url
                yield request


    def _parse_firstPage(self, response):
        if len(response.xpath(".//*[@class='counter']/text()"))>=1: #存在翻页
            first_url = response.meta["first_url"]
            page_len = clean_text(response.xpath(".//*[@class='counter']/text()").extract()[0].strip())
            finds = self.pattern_page.findall(page_len)
            totlePage = finds[0][1]
            for i in xrange(1,int(totlePage)):
                nextPageurl = "index_" + str(i+1) + ".html"
                url = urljoin(first_url, nextPageurl)
                request = FormRequest(url, callback=self._parse_item, dont_filter=True)
                request.meta["large_category"] = response.meta["large_category"]
                request.meta["mid_category"] = response.meta["mid_category"]
                request.meta["first_url"] = first_url
                yield request
        else:
            request = FormRequest(response.url, callback=self._parse_item, dont_filter=True)
            request.meta["large_category"] = response.meta["large_category"]
            request.meta["mid_category"] = response.meta["mid_category"]
            yield request


    def _parse_item(self, response):
        reports = response.xpath(".//*[@class='clistdl']")
        for report in reports:
            item = IndustryReportSpiderItem()
            item["industry_large_category"] = response.meta["large_category"]
            item["industry_mid_category"] = response.meta["mid_category"]
            item["report_name"] = clean_text(report.xpath(".//dt/a/text()").extract()[0].strip())
            if len(report.xpath(".//dd//*[@class='cxgrep']//@title"))>0:
                industry = clean_text(report.xpath(".//dd//*[@class='cxgrep']//@title").extract()[0].strip())
            else:
                industry = item["report_name"]
            industry_small_chs_name = parseIndustryName(industry)
            if industry_small_chs_name != None:
                    item["industry_small_chs_name"] = industry_small_chs_name
            page_url = report.xpath(".//@href").extract()[0]
            item["report_link"] = page_url
            item["report_revision_time"] = clean_text(report.xpath(".//dt/span/text()").extract()[0].strip())
            item["source_domain"] = self.allowed_domains[0]
            item["source_name"] = u"中国报告大厅"
            date, date_precision = parse_date(item["report_revision_time"])
            item["report_revision_time_standard"] = date.replace(tzinfo=pytz.timezone('Asia/Shanghai'))
            item["price_free"] = False
            yield item




