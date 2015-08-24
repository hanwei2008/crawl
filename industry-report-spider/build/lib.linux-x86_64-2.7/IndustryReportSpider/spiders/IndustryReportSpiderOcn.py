#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author : yuantaocai
# Date:   15-5-15
# Email:  yuantaocai@163.com
# Filename: IndustryReportSpiderOcn
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


class IndustryReportSpiderOcn(CrawlSpider):
    name = "industry_ocn"
    allowed_domains = ["ocn.com.cn"]
    base_url = "http://www.ocn.com.cn/"
    start_urls = ["http://www.ocn.com.cn/"]
    pattern = re.compile(ur"[\W]*[a-zA-Z0-9\u4e00-\u9fa5][\W]*")
    pattern_page = re.compile(ur"第\s+(\d+)\s+页[,，]\s+共\s+(\d+)\s+页")

    def __init__(self, *a, **kw):
        super(IndustryReportSpiderOcn, self).__init__(*a, **kw)
        self.prePauseTime = time.time()

    def parse(self, response):
        large_categories = response.xpath(".//*[@class='rptmap']//strong//a")
        for large_category in large_categories:
            large_category_name = clean_text(large_category.xpath("./text()").extract()[0].strip())
            page_url = large_category.xpath("./@href").extract()[0]
            url = urljoin(self.base_url, page_url)
            request = FormRequest(url, callback=self.parse_middle_category, dont_filter=True)
            request.meta["large_category"] = large_category_name
            yield request

    def parse_middle_category(self, response):
        mid_categories = response.xpath(".//*[@class='report2']//h2//a")
        for mid_category in mid_categories:
            mid_category_name = clean_text(mid_category.xpath("./text()").extract()[0].strip())
            page_url = mid_category.xpath("./@href").extract()[0]
            url = urljoin(self.base_url, page_url)
            request = FormRequest(url, callback=self._parse_item, dont_filter=True)
            request.meta["large_category"] = response.meta["large_category"]
            request.meta["mid_category"] = mid_category_name
            request.meta["first_url"] = url
            yield request


    # def _parse_firstPage(self, response):
    #     if len(response.xpath(".//*[@class='zw']"))>0: #存在翻页
    #         total_page = response.xpath(".//*[@class='pagelist nobdbt']//li")[-2].xpath(".//a//text()").extract()[0]
    #         for i in xrange(1, int(total_page)):
    #             page_url = response.url
    #             if(page_url[-1]=='l'):
    #
    #
    #             url = urljoin(self.base_url, page_url)
    #             request = FormRequest(url, callback=self._parse_item, dont_filter=True)
    #             request.meta["large_category"] = response.meta["large_category"]
    #             request.meta["mid_category"] = response.meta["mid_category"]
    #             yield request
    #     else:
    #         request = FormRequest(response.url, callback=self._parse_item, dont_filter=True)
    #         request.meta["large_category"] = response.meta["large_category"]
    #         request.meta["mid_category"] = response.meta["mid_category"]
    #         yield request

    def _parse_item(self, response):
        reports = response.xpath(".//*[@class='info']")
        if len(reports)>0:
            for report in reports:
                item = IndustryReportSpiderItem()
                item["industry_large_category"] = response.meta["large_category"]
                item["industry_mid_category"] = response.meta["mid_category"]
                item["report_name"] = clean_text(report.xpath(".//h3//a/text()").extract()[0].strip())
                industry_small_chs_name = parseIndustryName(item["report_name"])
                if industry_small_chs_name != None:
                    item["industry_small_chs_name"] = industry_small_chs_name
                page_url = report.xpath(".//@href").extract()[0]
                url = urljoin(self.base_url, page_url)
                item["report_link"] = url
                string =clean_text(report.xpath(" //*[@class='rdate']//span/text()").extract()[0].strip())
                temp = self.parseItem(string)
                if len(temp)==1:
                    item["report_revision_time"] = temp[0][0]
                    item["report_page_count"] = temp[0][1]
                    item["report_graph_count"] = temp[0][2]
                    date, date_precision = parse_date(item["report_revision_time"])
                    item["report_revision_time_standard"] = date.replace(tzinfo=pytz.timezone('Asia/Shanghai'))

                item["source_domain"] = self.allowed_domains[0]
                item["source_name"] = u"中国投资咨询网"
                item["price_free"] = False
                yield item

            if_nextpage = response.xpath(".//*[@class='zw']")

            if len(if_nextpage)>0:
                if (if_nextpage.xpath(".//text()").extract()[-1])==u'下一页': #存在翻页
                    page_url =if_nextpage.xpath(".//@href").extract()[-1]
                    url = urljoin(self.base_url, page_url)
                    request = FormRequest(url, callback=self._parse_item, dont_filter=True)
                    request.meta["large_category"] = response.meta["large_category"]
                    request.meta["mid_category"] = response.meta["mid_category"]
                    yield request


    @staticmethod
    def parseItem(report_string):
        pattern = re.compile(ur"修订时间:(.*)\|报告页数:(\d+)页\|图表个数:(\d+)个")
        return pattern.findall(report_string)
