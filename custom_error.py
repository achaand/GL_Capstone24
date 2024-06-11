"""Module for exception class"""
from taxi_ops_logger import TaxiOpsLogger


class IllegalTaxiStatusState(Exception):
    """Error Raised when Taxi status is not correct for an action to happen"""
    def __init__(self, error_string):
        TaxiOpsLogger().error(error_string)
        super().__init__(error_string)
