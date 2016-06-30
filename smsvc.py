import sqlite3
import logging
from threading import Thread
from random import randint
from time import time, sleep
from cmpp.cmpp import cmpp
from config import config


class smsvc(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.__mobile_vc = {}
        self.__mobile_log = []
        self.__thread_stop = False
        self.__cmpp = cmpp(config)
        self.__sqliteDB = 'vclogs.db'
        self.__initDB()
        self.logger = logging.getLogger('smsvc')

    def __del__(self):
        self.stop()

    def stop(self):
        self.__thread_stop = True
        if self.__cmpp:
            self.__cmpp.stop()
        if self.__conn:
            self.__conn.close()

    def run(self):
        self.logger.info('smsvc thread start')
        self.__cmpp.start()
        while not self.__thread_stop:
            now = time()
            for i in range(len(self.__mobile_log)):
                # print(self.__mobile_log[i])
                vctime = self.__mobile_log[i][0]
                if now - vctime < 180 and i > 10:
                    olds = self.__mobile_log[:i]
                    self.__mobile_log = self.__mobile_log[i:]
                    for vctime, mobile in olds:
                        vc, lasttime = self.__mobile_vc.pop(mobile, ('', 0))
                        self.__logvc((mobile, vc, vctime))
                    break
            sleep(30)

    def sendsmsvc(self, mobile):
        now = time()
        vc, lasttime = self.__mobile_vc.get(mobile, (None, 0))
        if not vc:
            vc = self.__getrandstr()
            now = time()
            self.__mobile_vc[mobile] = (vc, lasttime)
            self.__mobile_log.append((now, mobile))
        if now - lasttime > 60:
            self.__cmpp.sendmessage([mobile], 'MM验证码：' + vc)
            self.__mobile_vc[mobile] = (vc, now)
        return vc

    def __getrandstr(self):
        return '{:04d}'.format(randint(0, 9999))

    def __initDB(self):
        self.__conn = sqlite3.connect(self.__sqliteDB)
        self.__conn.execute(
            "create table if not exists logs(mobile,vc,vctime);")

    def __logvc(self, logtosave):
        mobile, vc, vctime = logtosave
        vctime = str(vctime)
        self.__conn.execute(
            "insert into logs values (?, ?, ?)", (mobile, vc, vctime))
