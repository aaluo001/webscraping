#!python
# coding: gbk
#----------------------------------------
# MongoCache.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
import zlib, pickle
from datetime import datetime, timedelta
from urllib.parse import urlparse

from pymongo import MongoClient
from bson.binary import Binary
from util.cache.BaseCache import BaseCache


class MongoCache(BaseCache):
    def __init__(self, vMongoConf, vExpire=timedelta(days=180)):
        super().__init__(vExpire)
        
        self.vClient = MongoClient(host=vMongoConf['host'], port=vMongoConf['port'])
        self.vDB = self.vClient[vMongoConf['db']]
        self.vCache = self.vDB['mongocache']


    def __getitem__(self, vUrl):
        vRecord = self.vCache.find_one({'_id': vUrl})
        if (vRecord):
            if (self.hasExpired(vRecord['update_ts'])):
                raise IndexError('{}: Has expired.'.format(vUrl))
            else:
                return pickle.loads(zlib.decompress(vRecord['result']))
        else:
            raise IndexError('{}: Dose not exist.'.format(vUrl))


    def __setitem__(self, vUrl, vHtml):
        vDomain = urlparse(vUrl).netloc
        vResult = Binary(zlib.compress(pickle.dumps(vHtml)))
        vRecord = { \
            'domain': vDomain, \
            'result': vResult, \
            'update_ts': datetime.now(), \
        }
        self.vCache.update_one({'_id': vUrl}, {'$set': vRecord}, upsert=True)


    def delete(self, vDomain):
        vResult = self.vCache.delete_many({'domain': vDomain})
        return vResult.deleted_count

