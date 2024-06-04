"""
DB operations
"""
from typing import Mapping, Any, Union

import certifi
import pymongo
from bson import SON
# Imports MongoClient for base level access to the local MongoDB
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from pymongo.typings import _Pipeline

from taxi_ops_backend.taxi_ops_logger import TaxiOpsLogger


class Database:
    """
    Class for DB operations
    """
    # Class variables used for database host ip and port information, database name
    # variables are referred to by using <class_name>.<variable_name>
    # AK_URI = "mongodb+srv://apache_abhinav_official:6g6RRf2UZiJy8G2" \
    #          "@taxiops.jdfqcmn.mongodb.net/?retryWrites=true&w=majority"
    # AK_DB_NAME = 'TaxiOps'
    # _instance = None initially
    # _db_conn = database connection client
    # _db = database
    # _logger = applevel logger

   # DB_URI = "mongodb+srv://iitmcloudfeb22g1:iitmcloudfeb22g1@spn.xqzqo3y.mongodb.net/ " \
   #          "?retryWrites=true&w=majority"

    # DB_URI = "mongodb://adminuser:<insertYourPassword>@docdb-2024-05-16-11-22-24.cluster-cw6d27j9m09a.us-east-1.docdb.amazonaws.com:27017/" \
    #         "?retryWrites=false"

    # DB_URI = "mongodb://localhost:27017"
    DB_URI = "mongodb+srv://mogodbcloud:UYWhDW9VEOoYoEjf@mongodbcloudcluster.1l4vovv.mongodb.net/" \
            "?retryWrites=false"
    DB_NAME = 'ProjectTaxi'
    _instance = None
    _db_conn = MongoClient(DB_URI,tlsCAFile=certifi.where())
    _db = _db_conn[DB_NAME]
    _logger = TaxiOpsLogger()

    def __new__(cls):
        """
        making database object singleton class
        :return: Database instance
        """
        if cls._instance is None:
            cls._logger.info('Creating the database instance')
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def find_one(self, collection, key):
        """
        This method finds a single document using field information provided in the key parameter.
        It assumes that the key returns a unique document. It returns None if no document is found
        :param collection:
        :param key:
        :return:
        """
        db_collection = self._db[collection]
        document = db_collection.find_one(key)
        return document

    def find_multiple(self, collection, data):
        """
        This method finds multiple documents using field information provided in the key parameter.
        It returns cursor on valid query fetch. Here we have suppressed _id being sent out
        :param collection:
        :param data:
        :return:
        """
        try:
            if data is None:
                self._logger.warning("No data is available. Please provide the data.")
                return True
            db_collection = self._db[collection]
            result = db_collection.find(data)
            return result
        except TypeError as exception:
            self._logger.error("An exception occurred :: %s", exception)
            return False

    def insert_single_data(self, collection: str, data: dict, index_key: str = "") -> str:
        """ This method inserts the data in a new document. It assumes that any uniqueness check
        is done by the caller. index_key is currently supported for geo_spatial only in this
        project, and it should only once. It is also assumed that developers will use insert single
         or multiple insert, which in turn creates the collection.
        :param collection:
        :param data:
        :param index_key:
        :return:
        """
        db_collection = self._db[collection]
        document = db_collection.insert_one(data)
        # The pymongo.collection.Collection.create_index method only creates an index
        # if an index of the same specification does not already exist.
        # https://www.mongodb.com/docs/manual/indexes/
        # if index_key != "": #Actual Code
        if index_key: #Added by SUraj
            # self.__create_geo_spatial_index(self._db[collection], index_key)
            # self._create_geo_spatial_index(self._db[collection], index_key)
            self._create_geo_spatial_index(collection, index_key)
        return document.inserted_id

    def insert_multiple(self, collection, data, index_key: str = ""):
        """
        This method inserts data.
        :param collection:
        :param data:
        :param index_key:
        :return:
        """
        try:
            if data is None:
                self._logger.warning("No data is available.")
                return True
            result = self._db[collection].insert_many(data)
            if index_key != "":
                # self.__create_geo_spatial_index(collection, index_key)  #Changed by Suraj
                self._create_geo_spatial_index(collection, index_key)
            self._logger.info(result.inserted_ids)
            return True
        except TypeError as exception:
            self._logger.error("An exception occurred :: %s", exception)
            return False

    def delete_single(self, collection, data):
        """ This method deletes the data from collection
        :param collection:
        :param data:
        :return:
        """
        if data is not None:
            result = self._db[collection].delete_one(data)
            return result
        self._logger.warning("No data is available. Please provide the data.")
        return True

    def delete_multiple(self, collection, data):
        """ This method deletes the data from collection
        :param collection:
        :param data:
        :return:
        """
        if data is not None:
            result = self._db[collection].delete_many(data)
            return result
        self._logger.warning("No data is available. Please provide the data.")
        return True

    def update_single(self, collection, update_filter: Mapping[str, Any],
                      update: Union[Mapping[str, Any], _Pipeline]):
        """
        This method update the data from Collection
        {{{
        collection = db.[collection]

        # Updating fan quantity from 10 to 25.
        filter = { 'appliance': 'fan' }

        # Values to be updated.
        new_values = { "$set": { 'quantity': 25 } }

        collection.update_one(filter, new_values)
        }}}
        :param collection: The Collection on which the operation needs to run
        :param update_filter: filter to be used
        :param update: data to be updated
        :return:
        """
        if update_filter is not None and update is not None:
            result = self._db[collection].update_one(filter=update_filter, update=update)
            return result.matched_count, result.modified_count
        self._logger.warning("No data is available. Please provide the data.")
        return None, None

    def update_multiple(self, collection, update_filter: Mapping[str, Any],
                        update: Union[Mapping[str, Any], _Pipeline], upsert: bool = False):
        """ This method deletes the data from collection
        :param collection:
        :param update_filter:
        :param update:
        :param upsert:
        :return:
        """
        if update_filter is None or update is None:
            self._logger.warning("No data is available. Please provide the data.")
            return True
        return self._db[collection].update_many(filter=update_filter, update=update, upsert=upsert)

    def run_as_transactions(self, func_list: []):
        """Work in Progress. Transactions"""
        with self._db_conn.start_session() as session:
            with session.start_transaction():
                for func in func_list:
                    func(session)

    def aggregate_data(self, collection, query):
        """
        This method perform aggregation on collection. Created by Abhinav
        :param collection:
        :param query:
        :return:
        """
        result = self._db[collection].aggregate(query)
        return result

    def drop_collection(self, collection):
        """
        This is only created to support testing
        :param collection:
        :return:
        """
        try:
            self._db[collection].drop()
            self._logger.info("Collection: %s dropped", collection)
            return True
        except ConfigurationError as exception:
            self._logger.error("An exception occurred :: %s", exception)
            return False

    def count_collection(self, collection, key):
        """
        This method returns counts of document for the filter in collection
        :param collection:
        :param key:
        :return:
        """
        result = self._db[collection].count(key)
        return result

    def find_nearest_entities_in_collection(self, collection,
                                            lon, lat, max_distance, max_number_of_taxi):
        """
        Finding the nearest entities in collection
        @param collection:
        @param lon:
        @param lat:
        @param max_distance:
        @param max_number_of_taxi:
        @return:
        """

        try:
            db_collection = self._db[collection]
            # query = {"location": SON([("$nearSphere", [lon, lat]),
            #                           ("$maxDistance", max_distance)]
            #                          )
            #          } #Non accurate results changed by SURAJ
            query = {
                "location": {
                    "$nearSphere": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "$maxDistance": max_distance
                    }
                }
            }
            # documents_near = db_collection.find(query).limit(max_number_of_taxi)
            # document_list = []
            # for doc in documents_near:
            #     document_list.append(doc)
            # return document_list
            documents_near = db_collection.find(query).limit(max_number_of_taxi)
            document_list = list(documents_near)
            return document_list
        except Exception as exception:
            self._logger.error('Exception in geoNear: %s', exception)
            raise

    # def __create_geo_spatial_index(self, collection, key: str):
    # Just making it to Refactor the method to be protected (single underscore):
    def _create_geo_spatial_index(self, collection: object, key: str) -> object:
        try:
            self._db[collection].create_index([(key, pymongo.GEOSPHERE)])
            self._logger.info("Geospatial index created on collection - %s, key - %s",
                              collection, key)
        except TypeError as exception:
            self._logger.error("An exception occurred :: %s", exception)
        except ConfigurationError as exception:
            self._logger.error("An exception occurred :: %s", exception)
        except Exception as exception:
            self._logger.error("An unexpected exception occurred :: %s", exception)