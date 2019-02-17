#!python
# coding: gbk
#----------------------------------------
# CrawlTool.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup


def getLinks(vHtml):
    ''' 取得页面中的链接
    '''
    vRegex = re.compile('<a[^>]+href=[\"\'](.*?)[\"\']', re.I)
    return vRegex.findall(vHtml)


def getImages(vHtml):
    ''' 取得页面中的图片资源
    '''
    vRegex = re.compile('<img[^>]+src=[\"\'](.*?)[\"\']', re.I)
    return vRegex.findall(vHtml)


def parseForm(vHtml):
    ''' 取得表单项目的内容
    '''
    vSoup = BeautifulSoup(vHtml, 'lxml')
    vData = {}
    for e in vSoup.select('form input'):
        vName = e.get('name')
        if (vName): vData[vName] = e.get('value')
    return vData


def normalizeLink(vUrl, vLink):
    ''' 将相对链接(Link)更新为绝对地址(URL)
    '''
    #if (not vLink.startswith('/')): vLink = '/' + vLink
    #vLink = urlparse(vLink).path
    return urljoin(vUrl, urlparse(vLink).path)


def checkContentType(vResponse, vType):
    ''' 检查Request返回的Response内容是什么类型：
      vType: text(普通页面)
      vType: image(图片)
    '''
    vContentType = vResponse.headers.get('Content-Type', '').lower()
    if (vContentType.startswith(vType)): return True
    else: return False


def saveResponse(vfSaveDest, vResponse, vChunkSize=100000):
    ''' 保存Response的内容(默认10K缓存)
    '''
    with open(vfSaveDest, 'wb') as f:
        for vChunk in vResponse.iter_content(chunk_size=vChunkSize):
            f.write(vChunk)
