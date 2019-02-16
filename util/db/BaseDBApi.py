#!python
# coding: gbk
#----------------------------------------
# BaseDBApi.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------


class BaseDBApi:
    def __init__(self):
        self.vConn = None
        self.vCurs = None

    def connect(self): pass

    def close(self):
        try:
            self.vCurs.close()
            self.vConn.close()
        except: pass


    def execute(self, vCommand, *vQuery): self.vCurs.execute(vCommand, vQuery)
    def names(self): return [ f[0] for f in self.vCurs.description ]
    def rowcount(self): return self.vCurs.rowcount
    def fetchone(self): return self.vCurs.fetchone()
    def fetchall(self): return self.vCurs.fetchall()
    def commit(self): self.vConn.commit()
    def rollback(self): self.vConn.rollback()

