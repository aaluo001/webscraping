#!python
# coding: gbk
#----------------------------------------
# ToutiaoOutputs.py
#----------------------------------------
# Copyright 2018 Pywork by TangJianwei.
# All rights reserved. 
#----------------------------------------
from datetime import datetime

from Setting import MYSQL_CONF
from util.Common import msgInf
from util.Common import toCsv
from util.project.BaseProject import BaseProject

from util.db.MysqlDBApi import MysqlDBApi as DBApi
from util.db.MysqlDBApi import DBApiError


MSG_EMPTY = 'û����Ҫ�ҵ����ݣ�'


class ToutiaoOutputs(BaseProject):
    def __init__(self):
        super().__init__()

        # Database
        self.vDB = DBApi(MYSQL_CONF)

        # Input parameter
        self.vParam = None


    # ��������
    def procArgv(self):
        try:
            self.vParam = self.vSysArgv[1]
        except IndexError:
            self.vParam = None
        else:
            if (self.vParam == '*'): pass
            else:
                try:
                    vDate = datetime.strptime(self.vParam, '%Y-%m-%d')
                except ValueError:
                    print('Usage: {} [ * | YYYY-mm-dd ]'.format(self.vAppName))
                    print('    δָ������: ��ӡ��ÿ�����ż�¼��������')
                    print('    *: ���ȫ�������ż�¼��CSV�ļ���')
                    print('    YYYY-mm-dd: ���ָ�����ڵ����ż�¼��CSV�ļ���')
                    return False
                else:
                    self.vParam = vDate.strftime('%Y-%m-%d')
        return True


    def countRecords(self):
        ''' ��ӡ��ÿ�����ż�¼������
        '''
        vSQL = '''
        SELECT DATE(update_ts) AS date, COUNT(id) AS count 
        FROM toutiao_news 
        GROUP BY DATE(update_ts)
        '''
        self.vDB.connect()
        try:
            self.vDB.execute(vSQL)
            vNames = self.vDB.names()
            vRecordList = self.vDB.fetchall()
            if (vRecordList):
                msgInf('{:<10} {:<5}'.format(vNames[0], vNames[1]))
                msgInf('{} {}'.format('-'*10, '-'*5))
                for vRecord in vRecordList:
                    msgInf('{:<10} {:>5}'.format(str(vRecord[0]), vRecord[1]))
                msgInf('{} {}'.format('-'*10, '-'*5))
            else:
                msgInf(MSG_EMPTY)

        finally:
            self.vDB.close()


    def outputRecords(self):
        ''' �����������CSV�ļ�
        '''
        vSQL = '''
        SELECT Date(update_ts) AS date, Time(update_ts) AS time, title, kind, source, comment, uptime, url
        FROM toutiao_news 
        '''
        vQuery = []
        
        if (self.vParam == '*'):
            # ���ȫ�������ż�¼
            vSQL += 'ORDER BY DATE(update_ts) DESC, comment DESC'
        else:
            # ���ָ�����ڵ����ż�¼
            vSQL += 'WHERE DATE(update_ts)=%s ORDER BY comment DESC'
            vQuery.append(self.vParam)
        
        self.vDB.connect()
        try:
            self.vDB.execute(vSQL, *vQuery)
            vFields = self.vDB.names()
            vRecordList = self.vDB.fetchall()
            
            if (vRecordList):
                vRows = []
                vRows.extend([vFields,])
                vRows.extend(vRecordList)
                vCsvFN = '{}_{}_{}.csv'.format(self.vAppName, self.vTSDate, self.vTSTime)
                toCsv(vCsvFN, vRows)
                msgInf('Records: {}'.format(len(vRecordList)))
                msgInf('Outputs: {}'.format(vCsvFN))
            else:
                msgInf(MSG_EMPTY)
        
        finally:
            self.vDB.close()


    # ������
    def main(self):
        if (self.vParam): self.outputRecords()
        else: self.countRecords()


# ִ��
if (__name__ == '__main__'):
    ToutiaoOutputs().run()
