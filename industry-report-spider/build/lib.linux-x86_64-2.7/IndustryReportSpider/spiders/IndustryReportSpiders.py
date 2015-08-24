# -*- coding: utf-8 -*-

# Filename: IndustryReportSpiders

# Copyright (c) 2015 Chengdu Lanjing Data&Information Co., Ltd

import re
import pytz
from urlparse import urljoin
from psycopg2._psycopg import Date
from scrapy import FormRequest, log
from scrapy.contrib.spiders import CrawlSpider
from scrapy_tools.misc import clean_text, parse_date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from IndustryReportSpider.Utils import parseIndustryName, login
from IndustryReportSpider.items import IndustryReportSpiderItem
from IndustryReportSpider.settings import Page_Limit
from selenium.webdriver.support import expected_conditions as EC


class IndustryReportSpiderIRN(CrawlSpider):
    name = "industry-irn"
    allowed_domains = ["chinairn.com"]
    base_url = "http://www.chinairn.com/yjbg/"
    start_urls = ["http://www.chinairn.com/yjbg/moref15ffff1.html"]
    pattern = re.compile(ur"[\W]*[a-zA-Z0-9\u4e00-\u9fa5][\W]*")

    def parse(self, response):
        large_categories = response.xpath("//a[contains(@id, 'xTrade')][not(contains(@id, 'All'))]")
        for large_category in large_categories:
            large_category_name = clean_text(large_category.xpath("./text()").extract()[0].strip())
            id = large_category.xpath("./@id").extract()[0]
            if id[-1] == u'l': continue
            page_url = large_category.xpath("./@href").extract()[0]
            url = urljoin(self.base_url, page_url)
            request = FormRequest(url, callback=self.parse_middle_category, dont_filter=True)
            request.meta["large_category"] = large_category_name
            yield request

    def parse_middle_category(self, response):
        mid_categories = response.xpath(".//a[contains(@id, 'sub')][not(contains(@id, 'All'))]")
        for mid_category in mid_categories:
            mid_category_name = clean_text(mid_category.xpath("./text()").extract()[0].strip())
            id = mid_category.xpath("./@id").extract()[0]
            if id[-1] == u'l': continue
            page_url = mid_category.xpath("./@href").extract()[0]
            url = urljoin(self.base_url, page_url)
            request = FormRequest(url, callback=self._parse_item, dont_filter=True)
            request.meta["large_category"] = response.meta["large_category"]
            request.meta["mid_category"] = mid_category_name
            yield request

    def _parse_item(self, response):
        domain_url = "http://www.chinairn.com/"
        reports = response.xpath("//p[@class='maintittle']")
        for report in reports:
            item = IndustryReportSpiderItem()
            item["industry_large_category"] = response.meta["large_category"]
            item["industry_mid_category"] = response.meta["mid_category"]
            item["report_name"] = clean_text(report.xpath(".//text()").extract()[0].strip())
            if parseIndustryName(item["report_name"]) != None:
                item["industry_small_chs_name"] = parseIndustryName(item["report_name"])
            page_url = report.xpath(".//@href").extract()[0]
            item["report_link"] = urljoin(domain_url, page_url)
            item["source_domain"] = self.allowed_domains[0]
            item["source_name"] = u"中国行业研究网"
            try:
                self.report_para(item, report)
            except:
                log.msg("Report revision time missed: %s"%item["report_link"], level=log.WARNING)
            item["price_free"] = False
            yield item

        Current_Page = clean_text(response.xpath(".//*[@class='hover']/text()").extract()[0])
        if Page_Limit > 0 and int(Current_Page) > Page_Limit:return

        nextPage = response.xpath("//a[contains(@class,'down')]")[0]
        lastPageurl = nextPage.xpath("./following-sibling::a[1]/@href").extract()[0]
        nextPageurl = nextPage.xpath("./@href").extract()[0]
        if lastPageurl != nextPageurl:
            url = urljoin(self.base_url, nextPageurl)
            request = FormRequest(url, callback=self._parse_item, dont_filter=True)
            request.meta["large_category"] = response.meta["large_category"]
            request.meta["mid_category"] = response.meta["mid_category"]
            yield request

    def report_para(self, item, report):
        revision_time = clean_text(report.xpath("..//*[@class='sp1']/text()").extract()[0].split(u"：")[1].strip())
        if self.pattern.match(revision_time):
            item["report_revision_time"] = revision_time
        else:
            textlst = report.xpath("../*[@class='main']/text()").extract()[0].replace(u"】 ", u"【").split(u"【")
            for text in range(len(textlst)+1):
                if textlst[text].endswith(u"日期"):
                    item["report_revision_time"] = clean_text(textlst[text+1].strip())
                    break
        try:
            date, date_precision = parse_date(item["report_revision_time"])
            dateTimezone = date.replace(tzinfo=pytz.timezone('Asia/Shanghai'))
            item["report_revision_time_standard"] = dateTimezone
        except:
            pass


class IndustryReportSpiderIResearch(CrawlSpider):
    name = "industry-iresearch"
    allowed_domains = ["report.iresearch.cn"]
    start_urls = ["http://center.iresearch.cn/login.shtml"]

    reports_page = "http://report.iresearch.cn/reports/"

    UserAccount = "ec_zhao@hotmail.com"
    UserPassword = "lanjing12345678"

    # def __init__(self, *args, **kwargs):
    #     CrawlSpider.__init__(self, *args, **kwargs)
    #     self.browser = webdriver.Firefox()
    #
    # def __del__(self, *args, **kwargs):
    #     self.browser.close()

    def parse(self, response):
        # login(self.browser,
        #       url=response.url,
        #       Account=self.UserAccount,
        #       AccountXpath="//*[@id='UserAccount']",
        #       Password=self.UserPassword,
        #       PasswordXpath="//*[@id='UserPassword']",
        #       Login=".//*[@id='LoginBtn']",
        #       waitEle="//*[@class='user_head']")
        return FormRequest(self.reports_page, callback=self.parse_home_page, dont_filter=True)

    def parse_home_page(self, response):
        pageNumInfo = response.xpath("//*[@class='page_tip']//text()").extract()[0]
        pageNum = re.findall(ur'共([0-9]+)', pageNumInfo)[0]
        for i in xrange(int(pageNum)):
            if Page_Limit > 0 and i >= Page_Limit: break
            url = "http://report.iresearch.cn/reports_%s/com-iResearch/"%(i + 1)
            yield FormRequest(url, callback=self.parse_page, dont_filter=True)

    def parse_page(self, response):
        report_links = response.xpath("//*[@class='tpList tpList_t']//a[@class='font_Large']/@href").extract()
        for report_link in report_links:
            yield FormRequest("http://report.iresearch.cn/" + report_link,
                              callback=self.parse_item, dont_filter=True)

    def parse_item(self, response):
        item = IndustryReportSpiderItem()
        item['report_link'] = response.url
        item['source_name'] = u"艾瑞网"
        item['source_domain'] = self.allowed_domains[0]
        item['report_name'] = clean_text(response.xpath("//*[@class='content_title']/text()").extract()[0].strip())
        price = response.xpath(u"//*[contains(text(), '价格')]/text()").extract()[0]
        item['price_free'] = True if u"免费" in price else False
        infodatas = response.xpath("//*[@class='content_titleinfoa']/span//text()").extract()
        for text in infodatas:
            try:
                if u"页数" in text:item['report_page_count'] = re.findall(ur'([0-9]+)', text)[0]
            except:pass
            try:
                if u"图表" in text:item['report_graph_count'] = re.findall(ur'([0-9]+)', text)[0]
            except:pass
            try:
                if u"-" in text:
                    item['report_revision_time'] = text
                    item['report_revision_time_standard'] = parse_date(item['report_revision_time'])
            except:pass
        item['industry_large_category'] =u"信息传输、软件和信息技术服务业"
        try:
            item['industry_mid_category'] = clean_text(response.xpath("//*[@class='content_titleinfoa']//a/text()").extract()[0].strip())
        except:
            pass
        # if item['price_free']:
            # self.browser.get(response.url)
            # self.browser.find_element_by_xpath("//*[@class='download']/a").click()
            # WebDriverWait(self.browser, 20).until(EC.presence_of_element_located((By.XPATH, ".//*[@id='ButtonBox']/input")))
            # Confirm = self.browser.find_element_by_xpath(".//*[@id='ButtonBox']/input")
            # Confirm.click()
            # WebDriverWait(self.browser, 20).until(EC.staleness_of(Confirm))
            # if ".pdf" in self.browser.current_url:item['pdf_Link'] = self.browser.current_url
        return item
