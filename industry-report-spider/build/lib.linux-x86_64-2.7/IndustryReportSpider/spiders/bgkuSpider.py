# -*- coding: utf-8 -*-

# Filename: IndustryReportSpiders

# Copyright (c) 2015 Chengdu Lanjing Data&Information Co., Ltd

import re
import pytz
from urlparse import urljoin
from scrapy import FormRequest, log
from scrapy.contrib.spiders import CrawlSpider
from scrapy_tools.misc import clean_text, parse_date
from IndustryReportSpider.items import IndustryReportSpiderItem
from IndustryReportSpider.settings import Page_Limit
from scrapy.shell import inspect_response

##
 # 中经报告网
 # http:##www.bgku.cn#sitemap
 #
 ##


class IndustryReportSpiderBGKU(CrawlSpider):
    name='industry-bgku'
    allowed_domains = ["bgku.cn"]
    base_url = "http://www.bgku.cn/"
    start_urls = ["http://www.bgku.cn/sitemap_1"]
    filename =u"bgku"
    current_page = 0

   ##
    # @method parse
    #
    # 获取产业报告索引的分页总数，构建出页面的地址，交由this.parse_index_page解析
    ##

    def __init__(self, *a, **kw):
        super(IndustryReportSpiderBGKU, self).__init__(*a, **kw)
        self.f = open(self.filename, 'a')
        self.industryList = []

    def __del__(self):
        self.f.close()

    def parse(self,response):
        ## page_count_text {string}
        # @example
        #
        # if(ANP_checkInput('AspNetPager1_input',3270,'页索引超出范围！','页索引不是有效的数值！'))
        # {ANP_goToPage('AspNetPager1_input','page','http://www.bgku.cn/sitemap_1',
        # 'http://www.bgku.cn/sitemap_{page}','',3270,false);};return false;
        ##

        page_count_text= response.xpath('//*[@id="AspNetPager1_btn"]/@onclick').extract()[0]
        match= re.search(',\d{4,},',page_count_text)
        page_count= int(match.group(0).strip(','))
        for page in range(1,page_count+1):
            url= 'http://www.bgku.cn/sitemap_'+str(page)
            request = FormRequest(url, callback=self.parse_index_page, dont_filter=True)
            request.meta["page"] = page
            yield request

    def parse_index_page(self,response):
        self.current_page += 1
        industry = response.xpath('//*[@id="DataList1"]//a')
        for r in industry:
            industry_small_chs_names= clean_text(r.xpath('./text()').extract()[0].strip())
            self.industryList.append(industry_small_chs_names.encode("utf-8"))

        if self.current_page % 30 == 0:
            self.f.write("\n".join(self.industryList))
            self.f.write("\n")
            print "!" * 50, "写入文件", "!" * 50
            self.industryList = []
        print "*" * 30, response.meta["page"], "*" * 30
        print "*" * 30, "第", self.current_page, "页", "*" * 30
