#!/usr/bin/python3
import logging.handlers
import logging


class Logger:
    def __init__(self,logger_name='vFrameWork',
                 loglevel=logging.DEBUG):
        try:
            logFile = "rest.log"
            self.logger = logging.getLogger(logger_name)
            self.logger.setLevel(loglevel)
            self.addLogHandler(logFile, loglevel)
            self.ERROR_FLAG = False
        except Exception as ex:
            print("ERROR::An exception occurred while initialising loggers" + str(
                ex))
            exit(0)

    def addLogHandler(self, logFile,
                      loglevel=logging.DEBUG):
        try:
            hdlr = logging.handlers.RotatingFileHandler(logFile,
                                   maxBytes=10000000, backupCount=10000)
            formatter = logging.Formatter(
                    '%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')
            hdlr.setFormatter(formatter)
            hdlr.setLevel(loglevel)
            self.logger.addHandler(hdlr)
            return hdlr
        except Exception as ex:
            print("ERROR::An exception occurred while adding log handlers" + str(
                ex))
            exit(0)

    def log(self, msg, thread, logLevel=logging.DEBUG):
        try:
            for line in msg.split("\n"):
                log_line = line
                if logLevel == logging.INFO:
                    print(thread + ' : ' + log_line)
                    #self.logger.info("    "  + thread +  " : " + str(log_line.encode("UTF-8")))
                elif logLevel == logging.WARNING:
                    self.logger.warn("    "  + thread + " : "  + str(log_line.encode("UTF-8")))
                elif logLevel == logging.ERROR:
                    print(line)
                    self.logger.error("    "  + thread + " : " + str(log_line.encode("UTF-8")))
                else:
                    self.logger.debug("    "  + thread + " : " + str(log_line.encode("UTF-8")))
        except Exception as ex:
            print("ERROR::An exception occurred while writting the log messages." + str(
                ex))
            exit(0)


    def info_log(self,thread, msg):
        cmd_str = '%s \n' % msg
        self.log(logLevel=logging.INFO, msg=cmd_str, thread=thread)

    def debug_log(self,thread, msg):
        cmd_str = '%s \n' % msg
        self.log(logLevel=logging.DEBUG, msg=cmd_str, thread=thread)

    def error_log(self,thread, msg):
        cmd_str = '%s \n' % msg
        self.log(logLevel=logging.ERROR, msg=cmd_str, thread=thread)

    def banner_log(self,thread, msg):
        cmd_str = 80*'=' + '\n' + '%s \n' % msg + 80*'=' + '\n'
        self.log(logLevel=logging.ERROR, msg=cmd_str, thread=thread)



