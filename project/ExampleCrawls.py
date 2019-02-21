#!python
# coding: gbk
#----------------------------------------
# ExampleCrawls.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
from Setting import MONGO_CONF
from util.Spider import Spider
from util.cache.MongoCache import MongoCache
from util.project.BaseProject import BaseProject


class ExampleCrawls(BaseProject):
    def __init__(self):
        super().__init__()

    # 主处理
    def main(self):
        Spider(vUrl=r'http://example.webscraping.com', \
          vMaxDepth=None, vMaxDownload=None, vCache=MongoCache(MONGO_CONF), \
          vAllowRules=[r'/view', r'/index',], \
          vDisallowRules=[r'/trap', r'/user', ] \
        ).run()

#        Spider(vUrl=r'https://requests.readthedocs.io/en/master/', \
#          vMaxDepth=None, vMaxDownload=None, vCache=mc, \
#          vDisallowRules=[r'/builds/', r'/sustainability/click/', ] \
#        ).run()
#
#        Spider(vUrl=r'https://docs.python.org/3/', \
#          vMaxDepth=3, vMaxDownload=51, vCache=mc, \
#          vDisallowRules=[r'/release', ] \
#        ).run()


# 执行
if (__name__ == '__main__'):
    ExampleCrawls().run()
