#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author : yuantaocai
# Date:   15-5-15
# Email:  yuantaocai@163.com
# Filename: IndustryReportSpiderDrcnet
# Copyright (c) 2015 Chengdu Lanjing Data&Information Co., Ltd

import re
from urlparse import urljoin
import pytz
from selenium import webdriver
from IndustryReportSpider.Utils import parseIndustryName, login
from scrapy.contrib.spiders import CrawlSpider
from scrapy import FormRequest
import time
from scrapy_tools.misc import clean_text,parse_date
from IndustryReportSpider.items import IndustryReportSpiderItem


class IndustryReportSpiderDrcnet(CrawlSpider):
    name = "industry_drcnet"
    allowed_domains = ["drcnet.com.cn"]
    start_urls = ["http://www.drcnet.com.cn/eDRCnet.common.web/login/login.aspx?gourl=../DocView.aspx~~chnid=3805^"]
    base_url = "http://www.drcnet.com.cn/www/report/"

    UserAccount = "wyzsj"
    UserPassword = "123456789"
    reports_page = ["http://www.drcnet.com.cn/www/report/channel.aspx?uid=7802&version=dReport",
                    "http://www.drcnet.com.cn/www/report/channel.aspx?uid=7803&version=dReport",
                    "http://www.drcnet.com.cn/www/report/channel.aspx?uid=7804&version=dReport"]
    pattern = re.compile(ur"[\W]*[a-zA-Z0-9\u4e00-\u9fa5][\W]*")
    pattern_page = re.compile(ur"(\d+).*(\d+)页")

    def __init__(self, *args, **kwargs):
        CrawlSpider.__init__(self, *args, **kwargs)
        self.browser = webdriver.PhantomJS()
        self.prePauseTime = time.time()

    def __del__(self, *args, **kwargs):
        self.browser.close()


    def parse(self, response):
        login(self.browser,
              url=response.url,
              Account=self.UserAccount,
              AccountXpath=".//*[@id='loginId']",
              Password=self.UserPassword,
              PasswordXpath=".//*[@id='pass']",
              Login=".//*[@tabindex='3']",
              waitEle=".//*[@align='center']//*[@type='image']")
        for url in self.reports_page:
            yield FormRequest(url, callback=self.parse_home_page, dont_filter=True)


    def parse_home_page(self, response):
        url  = response.url
        if "uid=7802" in url:
            large_category_name = u"宏观经济"
            large_categories = response.xpath(".//*[@class='yahei f14 rgt mr20']")
            for large_category in large_categories:
                page_url = large_category.xpath("./@href").extract()[0]
                url_link  = urljoin(self.base_url, page_url)
                request = FormRequest(url_link, callback=self._parse_hg_mid, dont_filter=True)
                request.meta["large_category"] = large_category_name
                yield request
        elif "uid=78030&" in url:
            large_category_name = u"金融"
            large_categories = response.xpath(".//*[@class='yahei f14 rgt mr20']")
            for large_category in large_categories:
                page_url = large_category.xpath("./@href").extract()[0]
                url_link  = urljoin(self.base_url, page_url)
                if "uid=780301&" in url_link:
                    request = FormRequest(url_link, callback=self._parse_first, dont_filter=True)
                else:
                    request = FormRequest(url_link, callback=self._parse_hg_mid, dont_filter=True)
                request.meta["large_category"] = large_category_name
                request.meta["callback"] = self._parse_hg
                yield request
        elif "uid=7804" in url:
            large_categories = response.xpath(".//*[@class='yahei f14 rgt mr20']")
            for large_category in large_categories:
                page_url = large_category.xpath("./@href").extract()[0]
                url  = urljoin(self.base_url, page_url)
                request = FormRequest(url, callback=self._parse_hy_large, dont_filter=True)
                yield request


    def _parse_hy_large(self, response):
        large_categories = response.xpath(".//*[@class='yahei f16 fB']")
        for large_category in large_categories:
            large_category_name = clean_text(large_category.xpath(".//text()").extract()[0].strip())
            if u"区域重点行业中小企业季报" not in large_category_name:
                page_url = large_category.xpath(".//@href").extract()[0]
                url = urljoin(self.base_url, page_url)
                request = FormRequest(url, callback=self._parse_hg_mid, dont_filter=True)
                request.meta["large_category"] = parseIndustryName(large_category_name)
                yield request


    def _parse_hg_mid(self, response):
        mid_categories = response.xpath(".//*[@class='yahei f14 rgt mr20']")
        for mid_category in mid_categories:
                page_url = mid_category.xpath("./@href").extract()[0]
                url  = urljoin(self.base_url, page_url)
                request = FormRequest(url, callback=self._parse_first, dont_filter=True)
                request.meta["large_category"] = response.meta["large_category"]
                request.meta["callback"] = self._parse_hg
                yield request


    def _parse_first(self, response):
        total_pages = clean_text(response.xpath(".//*[@id='Content_WebPageDocumentsByUId1_span_totalpage']//text()").extract()[0].strip())
        if total_pages >= 1:
            for i in xrange(0,int(total_pages)):
                next_page = response.url + '&curpage=' + str(i+1)
                request = FormRequest(next_page, callback=response.meta["callback"], dont_filter=True)
                request.meta["large_category"] = response.meta["large_category"]
                yield request


    def _parse_hg(self, response):
        reports = response.xpath(".//*[@class='yahei f14']")
        if len(reports)>0:
            for report in reports:
                item = IndustryReportSpiderItem()
                item["industry_large_category"] = response.meta["large_category"]
                item["report_name"] = clean_text(report.xpath(".//a/text()").extract()[0].strip())
                page_url = report.xpath(".//a//@href").extract()[0]
                item["report_link"] = page_url
                report_time = clean_text(report.xpath(".//*[@name='deliveddate']/text()").extract()[0].strip())
                if report_time != None:
                    item["report_revision_time"] = report_time
                item["source_domain"] = self.allowed_domains[0]
                item["source_name"] = u"国研网"
                date, date_precision = parse_date(item["report_revision_time"])
                item["report_revision_time_standard"] = date.replace(tzinfo=pytz.timezone('Asia/Shanghai'))

                dict = self.parseContent(page_url)
                if dict["free"] == False:
                    item["price_free"] = False
                else:
                    item["price_free"] = True
                    if(dict["url"][0]=="pdf"):item["pdf_Link"] = dict["url"][1]
                    else:item["content_Link"] = dict["url"][1]
                yield item


    @staticmethod
    def parseContent(url):
        import urllib2
        from BeautifulSoup import BeautifulSoup
        pattern_html = re.compile(ur".*(http.*)['].*")
        result ={"free":True, "url":None}
        page = urllib2.urlopen(url)
        html_page = page.read()
        soup = BeautifulSoup(html_page.decode('utf-8','ignore'))
        if soup.find(attrs={"href": "mailto:service@drcnet.com.cn"}) != None:
            result["free"]=False
        elif soup.find(id="AttachmentDownload") != None:
            temp  = soup.find(id="AttachmentDownload").get('onclick')
            result["url"] = ["pdf", pattern_html.findall(temp)[0]]
        else:
            result["url"] = ["content", url]
        return result