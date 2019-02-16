#!python
# coding: gbk
#----------------------------------------
# BaseCache.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
from datetime import datetime


class BaseCache:
    def __init__(self, vExpire):
        # ����ʱ��(datetime.timedelta��)
        self.vExpire = vExpire

    def __getitem__(self, vUrl): pass
    def __setitem__(self, vUrl, vHtml): pass


    def hasExpired(self, vTimestamp):
        ''' ���ü�¼�Ƿ����
        '''
        try: vTimestamp + ''
        # datetime��
        except TypeError: pass
        # string��
        else: vTimestamp = datetime.strptime(vTimestamp, '%Y-%m-%d %H:%M:%S.%f')
        return datetime.now() > (vTimestamp + self.vExpire)
