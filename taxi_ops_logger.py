"""
Logging module to be used in the project
"""

import logging


class TaxiOpsLogger(logging.Logger):
    """ Overriden Logger class to be used in the project """
    class TaxiOpsLogStreamHandler(logging.StreamHandler):
        """ Overriden StreamHandler class to be used in the project """
        def __init__(self):
            logging.StreamHandler.__init__(self)
            log_format = '%(asctime)s module:%(module)-15s func:%(funcName)s' \
                         ' line:%(lineno)d - %(message)s'
            fmt_date = '%Y-%m-%dT%T%Z'
            formatter = logging.Formatter(log_format, fmt_date)
            self.setFormatter(formatter)

    class TaxiOpsLogFileHandler(logging.FileHandler):
        """ Overriden FileHandler class to be used in the project """
        def __init__(self, filename):
            logging.FileHandler.__init__(self, filename)
            log_format = '%(asctime)s module:%(module)-15s func:%(funcName)s' \
                         ' line:%(lineno)d - %(message)s'
            fmt_date = '%Y-%m-%dT%T%Z'
            formatter = logging.Formatter(log_format, fmt_date)
            self.setFormatter(formatter)

    def __init__(self):
        logging.Logger.__init__(self, 'TaxiOps', 'DEBUG')
        self.addHandler(TaxiOpsLogger.TaxiOpsLogStreamHandler())
