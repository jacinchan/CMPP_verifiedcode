#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import logging
from time import sleep
from cmppclient import cmppclient
from queue import Queue


class cmpp(threading.Thread):
    def __init__(self, config, max_queue_size=0):
        threading.Thread.__init__(self)
        self.__config = config
        self.__max_conn = self.__config.pop('max_conn')
        self.__send_queue = Queue(max_queue_size)
        self.__recv_queue = Queue(max_queue_size)
        self.__workers = []
        self.__thread_stop = False
        self.__handle = self.__newcmppclient()
        self.logger = logging.getLogger('cmpp')

    def __newcmppclient(self):
        return cmppclient(send_queue=self.__send_queue,
                          recv_queue=self.__recv_queue,
                          **self.__config)

    def sendmessage(self, dest, content, isdelivery=0):
        self.__handle.sendmessage(dest, content, isdelivery)

    def run(self):
        self.logger.info('cmpp manager start')
        for i in range(self.__max_conn):
            self.__workers.append(self.__newcmppclient().start())
        while not self.__thread_stop:
            self.__workers = [x for x in self.__workers if x.is_alive()]
            died_workers = self.__max_conn - len(self.__workers)
            if died_workers > 1:
                self.logger.warning(
                    '%d workers died, recreating...' % died_workers)
                for i in range(died_workers):
                    self.__workers.append(self.__newcmppclient().start())
            sleep(30)

    def stop(self):
        self.logger('cmpp manager stop')
        for worker in self.__workers:
            worker.stop()
        self.__thread_stop = True
