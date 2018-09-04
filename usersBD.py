import pymongo
from pymongo import MongoClient
import datetime


client = MongoClient()
db = client.test


class UsersDB:

    def __init__(self, db):
        self.db = db
        self.collection = db.users

    def set_settings(self, user_ID, param):
        self.collection.update_one({'user_ID': user_ID}, {'$set': param})

    def update_count(self, user_ID, param):
        self.collection.update_one({'user_ID': user_ID}, {'$inc': param})

    def push_word(self, user_ID, param):
        self.collection.update_one({'user_ID': user_ID}, {'$push': param})

    def create_new_user(self, params):
        _id = self.collection.insert_one(params).inserted_id

    def get_param(self, user_ID, param):
        if self.collection.find_one({'user_ID': user_ID}) is None:
            return None
        else:
            return self.collection.find_one({'user_ID': user_ID})[param]






