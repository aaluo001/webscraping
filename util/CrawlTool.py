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
    ''' ȡ��ҳ���е�����
    '''
    vRegex = re.compile('<a[^>]+href=[\"\'](.*?)[\"\']', re.I)
    return vRegex.findall(vHtml)


def getImages(vHtml):
    ''' ȡ��ҳ���е�ͼƬ��Դ
    '''
    vRegex = re.compile('<img[^>]+src=[\"\'](.*?)[\"\']', re.I)
    return vRegex.findall(vHtml)


def parseForm(vHtml):
    ''' ȡ�ñ���Ŀ������
    '''
    vSoup = BeautifulSoup(vHtml, 'lxml')
    vData = {}
    for e in vSoup.select('form input'):
        vName = e.get('name')
        if (vName): vData[vName] = e.get('value')
    return vData


def normalizeLink(vUrl, vLink):
    ''' ���������(Link)����Ϊ���Ե�ַ(URL)
    '''
    #if (not vLink.startswith('/')): vLink = '/' + vLink
    #vLink = urlparse(vLink).path
    return urljoin(vUrl, urlparse(vLink).path)


def checkContentType(vResponse, vType):
    ''' ���Request���ص�Response������ʲô���ͣ�
      vType: text(��ͨҳ��)
      vType: image(ͼƬ)
    '''
    vContentType = vResponse.headers.get('Content-Type', '').lower()
    if (vContentType.startswith(vType)): return True
    else: return False


def saveResponse(vfSaveDest, vResponse, vChunkSize=100000):
    ''' ����Response������(Ĭ��10K����)
    '''
    with open(vfSaveDest, 'wb') as f:
        for vChunk in vResponse.iter_content(chunk_size=vChunkSize):
            f.write(vChunk)
