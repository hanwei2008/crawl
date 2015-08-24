# -*- coding: utf-8 -*-
import os
import re
import urllib

from urlparse import urljoin
import datetime
from scrapy import log
from scrapy.exceptions import DropItem
import solr
import time
import sys
from solrcloudpy import SolrConnection
from IndustryReportSpider.settings import SOLR_COLLECTION_DEFAULT, SOLR_URL, SOLR_CACHE_MAX_ELEMENTS_PER_SPIDER, \
    RETRY_PDF_DOWNLOAD_TIMES, PDF_PATH, SOLR_SERVERS


class DuplicatesPipeline(object):

    def __init__(self):
        servers = SOLR_SERVERS
        self.cnn = SolrConnection(servers)[SOLR_COLLECTION_DEFAULT]
        self.cache_list = []

    def process_item(self, item, spider):
        if self.cnn.search({"q":'report_link:%s' % item['report_link'].encode('utf-8')}).result.response.numFound != 0 \
                or self.cache_duplicate(item["report_link"]):
            raise DropItem("Duplicate item found: %s" % item['report_link'])
        else:
            if "report_revision_time_standard" in item:
                delta = datetime.timedelta(hours=8)
                dateTimezone = item["report_revision_time_standard"] - delta
                item["report_revision_time_standard"] = dateTimezone.strftime('%Y-%m-%dT%H:%M:%S') + "Z"
            return item

    def cache_duplicate(self, report_link):
        if report_link in self.cache_list:
            return True
        else:
            if len(self.cache_list) > SOLR_CACHE_MAX_ELEMENTS_PER_SPIDER:
                self.cache_list = []
            else:
                self.cache_list.append(report_link)
            return False


class DownloadPipeline(object):
    def process_item(self, item, spider):
        if 'pdf_Link' in item:
            pdfName = item['report_name']+ u".pdf"
            PDFPath = os.path.join(PDF_PATH, item['source_name'])
            if not os.path.exists(PDFPath):os.makedirs(PDFPath)
            filepath = os.path.join(PDFPath, pdfName)
            try:
                content = self.downloadPDF(item['pdf_Link'], filepath)
                item["report_content"] = content
            except:
                self.jsonInfoStored(item, pdfName)
                log.msg("pdf download failure, information is serializing to json files", level=log.INFO)
        elif 'content_Link' in item:
            from goose import Goose
            from goose.text import StopWordsChinese
            try:
                g = Goose({'stopwords_class': StopWordsChinese})
                article = g.extract(url=item['content_Link'])
                content = article.cleaned_text
                del item['content_Link']
                item["report_content"] = content
            except:
                log.msg("Content extracted failure from page:%s"%item['report_link'], level=log.INFO)
        return item

    def downloadPDF(self, url, filepath):
        num = 1
        while(num <= RETRY_PDF_DOWNLOAD_TIMES):
            try:
                urllib.urlretrieve(url, filepath)
                content = self.convert_pdf_to_txt(filepath)
                if  re.match(ur"[\W]*[a-zA-Z0-9\u4e00-\u9fa5][\W]*", content) != None:
                    return content
                else:
                    log.msg("No content in PDF:%s"%url, level=log.WARNING)
                    break
            except:
                log.msg("PDF download failure, retry again %s times" %num, level=log.INFO)
                num += 1
                time.sleep(2)

        if num > RETRY_PDF_DOWNLOAD_TIMES:
            log.msg("Fail to download PDF finally", level=log.WARNING)
        raise Exception

    def jsonInfoStored(self, item, pdfName):
        import json
        Item_To_Store = {}
        for key, value in item.iteritems():
            if isinstance(value, unicode):
                Item_To_Store[key] = value.encode('utf-8')
            elif not isinstance(value, str):
                Item_To_Store[key] = str(value)
        with open("ContentTooShortErrorPDF.json", 'a') as f:
            json.dump(dict(Item_To_Store), f)
            f.write("\n")

    def convert_pdf_to_txt(self, filepath):
        currentpath = os.path.dirname(os.path.abspath(sys.argv[0]))
        os.environ['CLASSPATH'] = os.path.join(currentpath, "lib/tika-app-1.7.jar")
        try:
            from jnius import autoclass
            Tika = autoclass('org.apache.tika.Tika')
            Metadata = autoclass('org.apache.tika.metadata.Metadata')
            FileInputStream = autoclass('java.io.FileInputStream')
            tika = Tika()
            meta = Metadata()
        except:
            log.msg("JavaException: Class not found 'org/apache/tika/Tika'", level=log.ERROR)
            raise ImportError
        try:
            text = tika.parseToString(FileInputStream(filepath), meta, 50*10000)
            return text.decode("utf-8")
        except:
            log.msg("TikaException: Unexpected RuntimeException"
                    "(Caused by: java.lang.IndexOutOfBoundsException)", level=log.ERROR)
            raise RuntimeError
