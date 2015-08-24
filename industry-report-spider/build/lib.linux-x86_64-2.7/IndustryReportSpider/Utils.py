# -*- coding: utf-8 -*-
#
# Filename: Utils

# Copyright (c) 2015 Chengdu Lanjing Data&Information Co., Ltd
#
import re
from scrapy import log
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def parseIndustryName(report_name):
    pattern = re.compile(ur".*(?:(?:中国)|年)(.+?)"
                         ur"(?:(?:行业)|(?:市场)|(?:项目)|(?:产业)|(?:电商)).*")
    if len(re.findall(r'([0-9]+)', report_name)) == 0:
        pattern = re.compile(ur"(.+?)(?:(?:行业)|(?:市场)|(?:项目)|(?:产业)|(?:电商)).*")

    finds = pattern.findall(report_name)
    if len(finds) == 1:
        if finds[0].endswith(u"银"):
            return finds[0] + u"行"
        else:
            return finds[0]

def login(browser, url, Account, AccountXpath, Password, PasswordXpath, Login, waitEle):
    log.msg("Logging...", level=log.INFO)
    browser.get(url)
    input_Account = browser.find_element_by_xpath(AccountXpath)
    input_Account.clear()
    input_Account.send_keys(Account)

    input_Password = browser.find_element_by_xpath(PasswordXpath)
    input_Password.clear()
    input_Password.send_keys(Password)

    input_Login = browser.find_element_by_xpath(Login)
    input_Login.click()

    WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.XPATH, waitEle)))
    log.msg("Successfully logged in. Let's start crawling!", level=log.INFO)