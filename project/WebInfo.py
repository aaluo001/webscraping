#!python
# coding: gbk
#----------------------------------------
# WebInfo.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import re, os
import requests, builtwith, whois
from urllib.parse import urlparse

from Setting import DIR_OUTPUT
from util.Common import msgInf
from util.Spider import Spider
from util.CrawlTool import saveResponse
from util.project.BaseProject import BaseProject


class WebInfo(BaseProject):
    def __init__(self):
        super().__init__()
        self.vUrl = None
        self.vScheme = None
        self.vDomain = None
        self.vFileHandle = None
        
        self.vRobotsUrl = None
        self.vSitemapUrl = None


    # 参数处理
    def procArgv(self):
        # Set Url
        try:
            self.vUrl = self.vSysArgv[1]
        except IndexError:
            print('Usage: {} 网站地址(URL)'.format(self.vAppName))
            return False
        else:
            vParseResult = urlparse(self.vUrl)
            self.vScheme = vParseResult.scheme
            self.vDomain = vParseResult.netloc
            return True


    def getRobots(self, vUrl, vResponse):
        ''' 下载robots.txt文件
        '''
        # Get and Write Robots Content
        vContent = vResponse.text
        self.vFileHandle.write('--- ROBOTS.TXT ---\n')
        self.vFileHandle.write(vContent)
        self.vFileHandle.write('\n\n\n')
        
        # Get Sitemap Url
        m = re.search('sitemap:(.+\.xml)', vContent, re.I)
        if (m): self.vSitemapUrl = m.group(1).strip()


    def getSitemap(self, vUrl, vResponse):
        ''' 下载sitemap.xml文件
        '''
        # Save Response
        vSitemapFN = '{}_[{}]_.xml'.format('Sitemap', self.vDomain)
        vSitemapFile = os.path.join(DIR_OUTPUT, vSitemapFN)
        saveResponse(vSitemapFile, vResponse)
        msgInf('Output: {}'.format(vSitemapFN))


    # 主处理
    def main(self):
        # 输出文件路径
        vOutputFN = '{}_[{}]_.txt'.format(self.vAppName, self.vDomain)
        vOutputFile = os.path.join(DIR_OUTPUT, vOutputFN)

        # Open Output File
        self.vFileHandle = open(vOutputFile, 'w')
        
        # Write Domain
        self.vFileHandle.write('--- DOMAIN ---\n')
        self.vFileHandle.write(self.vDomain)
        self.vFileHandle.write('\n\n\n')

        try:
            msgInf('Getting: builtwith')
            self.vFileHandle.write('--- BUILT WITH ---\n')
            self.vFileHandle.write(str(builtwith.parse(self.vUrl)))
            self.vFileHandle.write('\n\n\n')

            msgInf('Getting: whois')
            self.vFileHandle.write('--- WHOIS ---\n')
            self.vFileHandle.write(str(whois.whois(self.vDomain)))
            self.vFileHandle.write('\n\n\n')

            # Get robots.txt
            self.vRobotsUrl = '{}://{}/robots.txt'.format(self.vScheme, self.vDomain)
            Spider(vUrl=self.vRobotsUrl, mCallbackSaveSource=self.getRobots, vReset=True, vReport=False).run()
        finally:
            self.vFileHandle.close()

        msgInf('Output: {}'.format(vOutputFN))

        # Get sitemap.xml
        if (self.vSitemapUrl):
            Spider(vUrl=self.vSitemapUrl, mCallbackSaveSource=self.getSitemap, vReset=True, vReport=False).run()


# 执行
if (__name__ == '__main__'):
    WebInfo().run()
