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
        # 过期时间(datetime.timedelta型)
        self.vExpire = vExpire

    def __getitem__(self, vUrl): pass
    def __setitem__(self, vUrl, vHtml): pass


    def hasExpired(self, vTimestamp):
        ''' 检查该记录是否过期
        '''
        try: vTimestamp + ''
        # datetime型
        except TypeError: pass
        # string型
        else: vTimestamp = datetime.strptime(vTimestamp, '%Y-%m-%d %H:%M:%S.%f')
        return datetime.now() > (vTimestamp + self.vExpire)
