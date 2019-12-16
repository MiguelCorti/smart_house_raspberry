from pymongo import MongoClient
from time import sleep
from datetime import datetime, timedelta

client = MongoClient("localhost", 27017)
smart_house_db = client["smart_house"]
time_constraint_table = smart_house_db["time_constraint"]
all_config = []


def get_all_config():
    table_configs = time_constraint_table.find()
    for config in table_configs:
        all_config.append(config)

get_all_config()
while True:

    sleep(2)
