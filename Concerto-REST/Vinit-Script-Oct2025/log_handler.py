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
            # Clear any existing handlers to avoid duplicates
            self.logger.handlers.clear()
            
            # Single file handler for all logs
            self.main_hdlr = logging.handlers.RotatingFileHandler(logFile,
                                   maxBytes=20000000, backupCount=10)
            # Use a flexible formatter that we can control per message
            formatter = logging.Formatter('%(message)s')
            self.main_hdlr.setFormatter(formatter)
            self.main_hdlr.setLevel(loglevel)
            self.logger.addHandler(self.main_hdlr)
            
            # No separate payload logger - use the same main logger
            self.payload_logger = self.logger
            
            return self.main_hdlr
        except Exception as ex:
            print("ERROR::An exception occurred while adding log handlers" + str(
                ex))
            exit(0)

    def log(self, msg, logLevel=logging.DEBUG):
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')
            
            for line in msg.split("\n"):
                if line.strip():  # Skip empty lines
                    # Add timestamp for regular logs
                    timestamped_line = f"{timestamp} {logging.getLevelName(logLevel)} {line}"
                    
                    if logLevel == logging.INFO:
                        print(line)  # Console without timestamp
                        self.logger.info(timestamped_line)  # File with timestamp
                    elif logLevel == logging.WARNING:
                        self.logger.warning(timestamped_line)
                    elif logLevel == logging.ERROR:
                        print(line)  # Console without timestamp
                        self.logger.error(timestamped_line)  # File with timestamp
                    else:
                        self.logger.debug(timestamped_line)
                    
            # Force flush for immediate writing
            for handler in self.logger.handlers:
                handler.flush()
                
        except Exception as ex:
            print("ERROR::An exception occurred while writing the log messages." + str(ex))
            import traceback
            traceback.print_exc()


    def info_log(self,msg):
        cmd_str = '%s \n' % msg
        self.log(logLevel=logging.INFO, msg=cmd_str)

    def debug_log(self,msg):
        cmd_str = '%s \n' % msg
        self.log(logLevel=logging.DEBUG, msg=cmd_str)

    def error_log(self,msg):
        cmd_str = '%s \n' % msg
        self.log(logLevel=logging.ERROR, msg=cmd_str)

    def banner_log(self,msg):
        import datetime
        timestamp = datetime.datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')
        
        # Banner format for console (with equals)
        console_banner = 80*'=' + '\n' + '%s \n' % msg + 80*'=' + '\n'
        print(console_banner)
        
        # Cleaner format for file (with timestamp)
        file_entry = f"{timestamp} INFO {80*'='}\n{timestamp} INFO {msg}\n{timestamp} INFO {80*'='}\n"
        self.logger.info(file_entry)
        
        # Force flush
        for handler in self.logger.handlers:
            handler.flush()

    def payload_log(self, title, payload_data, log_type="INFO"):
        """
        Log payloads/large data to file only (not console) with pretty formatting
        """
        try:
            separator = "=" * 80
            # No timestamp for payload logs - just the formatted content
            log_entry = f"\n{separator}\n{title}\n{separator}\n{payload_data}\n{separator}\n"
            
            # Write directly to file without timestamp formatting
            if log_type.upper() == "ERROR":
                self.logger.error(log_entry)
            else:
                self.logger.info(log_entry)
                
            # Force flush to ensure data is written
            for handler in self.logger.handlers:
                handler.flush()
                
        except Exception as ex:
            print("ERROR::An exception occurred while writing payload log: " + str(ex))
            import traceback
            traceback.print_exc()

    def console_log(self, msg, log_level="INFO"):
        """
        Log only to console (not to file) - for non-payload messages
        """
        try:
            if log_level.upper() == "ERROR":
                print(f"ERROR: {msg}")
            elif log_level.upper() == "INFO":
                print(f"INFO: {msg}")
            else:
                print(f"DEBUG: {msg}")
        except Exception as ex:
            print("ERROR::An exception occurred while writing console log: " + str(ex))



