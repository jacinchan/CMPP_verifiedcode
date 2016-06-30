#!/bin/usr/env python
# -*- coding: utf-8 -*-

import time
import logging
import threading
import socket
from cmppdefines import *


class guard(threading.Thread):

    def __init__(self, call, T=1):
        threading.Thread.__init__(self)
        self.__thread_stop = False
        self.__call = call
        self.__T = T
        self.__lastheartbeat = True
        self.logger = logging.getLogger('guard')

    def run(self):
        self.logger.info('guard thrad start')
        while not self.__thread_stop:
            if not self.__lastheartbeat:
                self.__call()
            else:
                self.__lastheartbeat = False
            time.sleep(self.__T)

    def stop(self):
        self.logger.info('guard thrad stop')
        self.__thread_stop = True

    def active(self):
        self.logger.info('heartbeat active is call')
        self.__lastheartbeat = True


class recvthread(threading.Thread):

    def __init__(self, recv, deliverresp, activeresp,
                 recv_queue, timeoutcallback, T=30):
        threading.Thread.__init__(self)
        self.__recv = recv
        self.__recv_queue = recv_queue
        self.__deliverresp = deliverresp
        self.__activeresp = activeresp
        self.__timeoutcallback = timeoutcallback
        self.__T = T
        self.__guard = guard(self.timeout, self.__T)
        self.__thread_stop = False
        self.__doubletimeout = False
        self.logger = logging.getLogger('recvthread')

    def run(self):
        self.__guard.setDaemon(True)
        self.__guard.start()
        self.logger.info('recv thread start')
        while not self.__thread_stop:
            try:
                # timeout is 5, set in cmppclient.connectgateway
                h, b = self.__recv()
                command_id = h.get('command_id', None)
                if command_id in (CMPP_CONNECT_RESP, CMPP_SUBMIT_RESP,
                                  CMPP_ACTIVE_TEST_RESP,
                                  CMPP_TERMINATE_RESP):
                    self.activebyrecv()
                elif command_id == CMPP_DELIVER:
                    self.__deliverresp(b['Msg_Id'], 0, h['sequence_id'])
                    self.__recv_queue.put(b)
                    self.activebyrecv()
                elif command_id == CMPP_ACTIVE_TEST:
                    self.__activeresp(h['sequence_id'])
                    self.activebyrecv()
            except socket.error as err:
                self.logger.error(err)
                time.sleep(5)

    def stop(self):
        self.logger.info('recv thread stop')
        self.__guard.stop()
        self.__thread_stop = True

    def timeout(self):
        self.__timeoutcallback(self.__doubletimeout)
        self.__doubletimeout = True

    def activebyrecv(self):
        self.__guard.active()
        self.__doubletimeout = False


class sendthread(threading.Thread):

    def __init__(self, send, send_queue, interval=0.5, rate=30, C=60):
        threading.Thread.__init__(self)
        self.__interval = interval
        self.__send = send
        self.__rate = rate
        self.__window = rate
        self.__send_queue = send_queue
        self.__guard = guard(self.resetwindow)
        self.__thread_stop = False
        self.logger = logging.getLogger('sendthread')

    def trywindow(self):
        self.__window -= 1
        return self.__window > 0

    def resetwindow(self):
        self.__window = self.__rate

    def run(self):
        self.logger.info('send thread start')
        self.__guard.setDaemon(True)
        self.__guard.start()
        while not self.__thread_stop:
            try:
                if self.trywindow():
                    msg, seq = self.__send_queue.get()
                    self.__send(msg)
                else:
                    self.logger.warning('window is full')
                    time.sleep(self.__interval)

            except socket.error as arg:
                self.logger.error(arg)
                time.sleep(5)

    def stop(self):
        self.logger.info('send thread stop')
        self.__guard.stop()
        self.__thread_stop = True
