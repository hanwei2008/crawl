# -*- coding: utf-8 -*-

BOT_NAME = 'IndustryReportSpider'

SPIDER_MODULES = ['IndustryReportSpider.spiders']
NEWSPIDER_MODULE = 'IndustryReportSpider.spiders'
LOG_LEVEL = "INFO"

PDF_PATH = "DownLoad/IndustryReport"

ITEM_PIPELINES = {
    'IndustryReportSpider.pipelines.DuplicatesPipeline': 1,
    'IndustryReportSpider.pipelines.DownloadPipeline': 100,
    'scrapy_tools.SolrPipeline.SolrPipeline': 200,
}

NameJoin = u"__"
DOWNLOAD_DELAY = 2
COOKIES_ENABLES=True
RETRY_PDF_DOWNLOAD_TIMES = 20

RETRY_ENABLED = True
RETRY_TIMES = 400
Page_Limit = 0
#
# SOLR_URL = "http://192.168.1.59:8153/solr/"
# SOLR_SERVERS = ["http://192.168.1.59:8153"]
# SOLR_COLLECTION_DEFAULT = "IndustryReport"
# SOLR_CACHE_MAX_ELEMENTS_PER_SPIDER = 0

SOLR_CLOUD_MODE = True
SOLR_URL = "http://192.168.1.51:8983"
SOLR_SERVERS = ["192.168.1.51:8983",
                "192.168.1.52:8983",
                "192.168.1.54:8983",
                "192.168.1.56:8983",
                "192.168.1.57:8983"]
SOLR_COLLECTION_DEFAULT = "collection_industry_report"
SOLR_CACHE_MAX_ELEMENTS_PER_SPIDER = 100

USER_AGENT_LIST = ["Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:37.0) Gecko/20100101 Firefox/37.0",
                   "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/41.0.2272.76 Chrome/41.0.2272.76 Safari/537.36",
                   ]
# USER_AGENT = USER_AGENT_LIST[0]
#
# CONCURRENT_REQUESTS_PER_DOMAIN = 30
# CONCURRENT_REQUESTS = 30
