# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class IndustryReportSpiderItem(scrapy.Item):
    industry_large_category = scrapy.Field()
    industry_mid_category = scrapy.Field()
    industry_small_chs_name = scrapy.Field()
    industry_small_en_name = scrapy.Field()

    report_name = scrapy.Field()
    report_type = scrapy.Field()
    report_link = scrapy.Field()
    report_content = scrapy.Field()
    report_revision_time = scrapy.Field()
    report_revision_time_standard = scrapy.Field()
    report_page_count = scrapy.Field()
    report_graph_count = scrapy.Field()
    price_free = scrapy.Field()
    source_domain = scrapy.Field()
    source_name = scrapy.Field()

    pdf_Link = scrapy.Field()
    content_Link = scrapy.Field()

