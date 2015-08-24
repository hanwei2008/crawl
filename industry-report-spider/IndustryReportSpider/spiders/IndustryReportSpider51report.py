#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author : yuantaocai
# Date:   15-5-15
# Email:  yuantaocai@163.com
# Filename: IndustryReportSpiderOlxoz
# Copyright (c) 2015 Chengdu Lanjing Data&Information Co., Ltd

import re
import pytz
from scrapy import FormRequest
from scrapy.contrib.spiders import CrawlSpider
import time
from scrapy_tools.misc import clean_text,parse_date
from IndustryReportSpider.items import IndustryReportSpiderItem
from IndustryReportSpider.Utils import parseIndustryName

class IndustryReportSpider51report(CrawlSpider):
    name = "industry_51report"
    allowed_domains = ["51report.com"]
    base_url = "http://www.51report.com/"
    start_urls = ["http://www.51report.com/research/",
                  "http://www.51report.com/free/"]
    pattern = re.compile(ur"[\W]*[a-zA-Z0-9\u4e00-\u9fa5][\W]*")
    pattern_page = re.compile(ur"(\d+).*(\d+)页")

    def __init__(self, *a, **kw):
        super(IndustryReportSpider51report, self).__init__(*a, **kw)
        self.prePauseTime = time.time()

    def parse(self, response):
        url  = response.url
        if "research" in url:
            categories = response.xpath(".//*[@class='catec']")
            for i in xrange(len(categories)-1):
                large_categories = categories[i].xpath(".//*[@class='fl']")
                large_category_name = clean_text(large_categories.xpath(".//text()").extract()[0].strip())
                mid_categories = categories[i].xpath(".//span")
                for mid_category in mid_categories:
                    mid_category_name = clean_text(mid_category.xpath(".//text()").extract()[0].strip())
                    page_url = mid_category.xpath(".//@href").extract()[0]
                    request = FormRequest(page_url, callback=self._parse_page_research, dont_filter=True)
                    request.meta["large_category"] = large_category_name
                    request.meta["mid_category"] = mid_category_name
                    request.meta["first_url"] = page_url
                    yield request
        elif "free" in url:
            large_categories = response.xpath(".//*[@class='tul2']//h2//a")
            for i in xrange(len(large_categories)):
                large_category_name = clean_text(large_categories[i].xpath(".//text()").extract()[0].strip())
                page_url = large_categories[i].xpath("./@href").extract()[0]
                request = FormRequest(page_url, callback=self._parse_page_free, dont_filter=True)
                request.meta["large_category"] = large_category_name
                request.meta["first_url"] = page_url
                yield request

    def _parse_page_research(self, response):
        total_pages = int(clean_text(response.xpath(".//*[@class='pages']//a//text()").extract()[-2].strip()))
        first_url = response.meta["first_url"]
        request = FormRequest(first_url, callback=self._parse_research, dont_filter=True)
        request.meta["large_category"] = response.meta["large_category"]
        request.meta["mid_category"] = response.meta["mid_category"]
        yield request
        if total_pages>1:
            for i in xrange(1,total_pages):
                next_page = first_url[:-5] + '-p' + str(i+1) + '.html'
                request = FormRequest(next_page, callback=self._parse_research, dont_filter=True)
                request.meta["large_category"] = response.meta["large_category"]
                request.meta["mid_category"] = response.meta["mid_category"]
                yield request


    def _parse_page_free(self, response):
        total_pages = int(clean_text(response.xpath(".//*[@class='pages']//a//text()").extract()[-2].strip()))
        first_url = response.meta["first_url"]
        request = FormRequest(first_url, callback=self._parse_free, dont_filter=True)
        request.meta["large_category"] = response.meta["large_category"]
        yield request
        if total_pages>1:
            for i in xrange(1,total_pages):
                next_page = first_url[:-5] + '-p' + str(i+1) + '.html'
                request = FormRequest(next_page, callback=self._parse_free, dont_filter=True)
                request.meta["large_category"] = response.meta["large_category"]
                yield request


    def _parse_free(self, response):
        reports = response.xpath(".//*[@class='tul3']//li")
        if len(reports)>0:
            for report in reports:
                item = IndustryReportSpiderItem()
                item["industry_large_category"] = response.meta["large_category"]
                item["report_name"] = clean_text(report.xpath(".//a//text()").extract()[0].strip())
                industry_small_chs_name = parseIndustryName(item["report_name"])
                if industry_small_chs_name != None:
                    item["industry_small_chs_name"] = industry_small_chs_name
                page_url = report.xpath(".//@href").extract()[0]
                item["report_link"] = page_url
                report_content = self.parseTimeContent(page_url)
                if report_content != None:
                    item["report_content"] = report_content
                report_time = clean_text(report.xpath(".//span//text()").extract()[0].strip())
                if (len(report_time) > 0):
                    item["report_revision_time"] = report_time
                    date, date_precision = parse_date(item["report_revision_time"])
                    try:
                        item["report_revision_time_standard"] = date.replace(tzinfo=pytz.timezone('Asia/Shanghai'))
                    except:
                        pass
                item["source_domain"] = self.allowed_domains[0]
                item["source_name"] = u"中国产业洞察网"
                item["price_free"] = True
                yield item


    def _parse_research(self, response):
        reports = response.xpath(".//*[@id='ulNewsList']//li")
        if len(reports)>0:
            for report in reports:
                item = IndustryReportSpiderItem()
                item["industry_large_category"] = response.meta["large_category"]
                item["industry_mid_category"] = response.meta["mid_category"]
                item["report_name"] = clean_text(report.xpath(".//dt//text()").extract()[0].strip())
                industry_small_chs_name = parseIndustryName(item["report_name"])
                if industry_small_chs_name != None:
                    item["industry_small_chs_name"] = industry_small_chs_name
                page_url = report.xpath(".//@href").extract()[0]
                item["report_link"] = page_url
                report_time = clean_text(report.xpath(".//*[@class='time']").extract()[0].strip())
                if len(report_time) >0:
                    item["report_revision_time"] = report_time.split(u"：")[1]
                    date, date_precision = parse_date(item["report_revision_time"])
                    try:
                        item["report_revision_time_standard"] = date.replace(tzinfo=pytz.timezone('Asia/Shanghai'))
                    except:
                        pass
                item["source_domain"] = self.allowed_domains[0]
                item["source_name"] = u"中国产业洞察网"
                item["price_free"] = False
                yield item


    @staticmethod
    def parseTimeContent(url):
        import urllib2
        from BeautifulSoup import BeautifulSoup
        report_content = []
        try:
            page = urllib2.urlopen(url)
            html_page = page.read()
            soup = BeautifulSoup(html_page.decode('utf-8','ignore'))
            content = soup.find(attrs={"class": "cont_wed"})
            report_content.append(content.text)
            return report_content
        except:
            return []