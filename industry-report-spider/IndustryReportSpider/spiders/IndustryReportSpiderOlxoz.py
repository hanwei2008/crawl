#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author : yuantaocai
# Date:   15-5-15
# Email:  yuantaocai@163.com
# Filename: IndustryReportSpiderOlxoz
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


class IndustryReportSpiderOlxoz(CrawlSpider):
    name = "industry_olxoz"
    allowed_domains = ["olxoz.com"]
    base_url = "http://www.olxoz.com/"
    start_urls = ["http://www.olxoz.com/shop.html"]
    pattern = re.compile(ur"[\W]*[a-zA-Z0-9\u4e00-\u9fa5][\W]*")
    pattern_page = re.compile(ur"(\d+).*(\d+)页")

    def __init__(self, *a, **kw):
        super(IndustryReportSpiderOlxoz, self).__init__(*a, **kw)
        self.prePauseTime = time.time()

    def parse(self, response):
        large_categories = response.xpath(".//*[@class='shopleft_bt']//a")
        middle_categories = response.xpath(".//*[@class='shopnav2']")
        for i in xrange(len(large_categories)):
            large_category_name = clean_text(large_categories[i].xpath("./text()").extract()[0].strip())
            middle_category_list = middle_categories[i].xpath(".//*[@class='shopleft_wt']")
            for middle_category in middle_category_list:
                middle_category_name = clean_text(middle_category.xpath(".//a/text()").extract())
                page_url = middle_category.xpath(".//a//@href").extract()[0]
                url = urljoin(self.base_url, page_url)
                request = FormRequest(url, callback=self._parse_item, dont_filter=True)
                request.meta["large_category"] = large_category_name
                request.meta["mid_category"] = middle_category_name
                yield request

    def _parse_item(self, response):
        reports = response.xpath(".//*[@class='img_des']/a")
        if len(reports)>0:
            for report in reports:
                item = IndustryReportSpiderItem()
                item["industry_large_category"] = response.meta["large_category"]
                item["industry_mid_category"] = response.meta["mid_category"]
                item["report_name"] = clean_text(report.xpath("./text()").extract()[0].strip())
                industry_small_chs_name = parseIndustryName(item["report_name"])
                if industry_small_chs_name != None:
                    item["industry_small_chs_name"] = industry_small_chs_name
                page_url = report.xpath(".//@href").extract()[0]
                url = urljoin(self.base_url, page_url)
                item["report_link"] = url
                report_time = self.parseTime(item["report_link"])
                if report_time != None:
                    item["report_revision_time"] = report_time
                item["source_domain"] = self.allowed_domains[0]
                item["source_name"] = u"欧咨网"
                date, date_precision = parse_date(item["report_revision_time"])
                item["report_revision_time_standard"] = date.replace(tzinfo=pytz.timezone('Asia/Shanghai'))
                item["price_free"] = False
                yield item

            if len(response.xpath(".//*[@class='page']//@href"))>1: #存在翻页
                page_len = clean_text(response.xpath(".//*[@class='page']//*[@class='fl_l']/text()").extract()[0].strip())
                nextPageurl = response.xpath(".//*[@class='page']//@href").extract()[-1]
                finds = self.pattern_page.findall(page_len)
                currentPage = finds[0][0]
                totlePage = finds[0][1]
                if currentPage != totlePage:
                    url = urljoin(self.base_url, nextPageurl)
                    request = FormRequest(url, callback=self._parse_item, dont_filter=True)
                    request.meta["large_category"] = response.meta["large_category"]
                    request.meta["mid_category"] = response.meta["mid_category"]
                    yield request


    @staticmethod
    def parseTime(url):
        import urllib2
        from BeautifulSoup import BeautifulSoup
        pattern_html = re.compile(ur"发布时间[:：](.*)")
        page = urllib2.urlopen(url)
        html_page = page.read()
        soup = BeautifulSoup(html_page.decode('utf-8','ignore'))
        try_time = soup.find(attrs={"class": "product_desc_rcon fl_l "})
        if(try_time != None):
            report_time = try_time
        else:
            try_time = soup.find(attrs={"class": "product_desc_rcon fl_l"})
            if (try_time != None):
                report_time = try_time
            else:
                return None
        time = report_time.find('p').text
        finds = pattern_html.findall(time)
        if len(finds)==1:
            return finds[0]