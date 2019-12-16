from pymongo import MongoClient
from bson.objectid import ObjectId
from time import sleep
from datetime import datetime, timedelta
import requests

client = MongoClient("localhost", 27017)
smart_house_db = client["smart_house"]
components_table = smart_house_db["component"]
sensor_config_table = smart_house_db["sensor_config"]
components = {}
ports_used = set()
config_to_process = []
config_used = set()


def find_component_db(comp_id):
    data = {"_id": ObjectId(comp_id)}
    return components_table.find_one(data)


def check_valid_component(document):
    return 'ports' in document and 'env' in document and 'component' in document


def add_component(comp_id, data):
    if not check_valid_component(data):
        return False
    ports = data['ports']
    for port in ports:
        if port in ports_used:
            return False
    if data['component'] == 'led':
        components[comp_id] = data['component']
    elif data['component'] == 'motor':
        if len(ports) < 2:
            return False
        components[comp_id] = data['component']
    elif data['component'] == 'distance_sensor':
        if len(ports) < 2:
            return False
        components[comp_id] = data['component']
    elif data['component'] == 'motion_sensor':
        components[comp_id] = data['component']
    elif data['component'] == 'light_sensor':
        components[comp_id] = data['component']
    for port in ports:
        ports_used.add(port)
    return True


def load_from_db():
    all_data = components_table.find()
    for data in all_data:
        add_component(str(data['_id']), data)
    return


def get_all_config():
    table_configs = sensor_config_table.find()
    for config in table_configs:
        if str(config['_id']) not in config_used:
            config_to_process.append(config)
            config_used.add(str(config['_id']))
    return

while True:
    get_all_config()
    load_from_db()
    cur_time = datetime.now()
    delta = timedelta(seconds=2)
    url = "http://localhost:5000/"
    for config in config_to_process:
        sensor_id = config['sensor_id']
        threshold = config['threshold']
        comp_id = config['comp_id']
        comp_mode = config['mode']
        sensor_name = components[sensor_id]
        comp_name = components[comp_id]
        cur_value = 0.0
        if sensor_name == 'distance_sensor':
            url += 'get-distance-sensor/%s' % sensor_id
            cur_value = float(requests.get(url).content)
        elif sensor_name == 'light_sensor':
            url += 'get-light-sensor/%s' % sensor_id
            cur_value = float(requests.get(url).content)
        if cur_value < threshold:
            if comp_name == 'led':
                url += 'control-led/%s/%f' % (comp_id, comp_mode)
            else:
                url += 'control-motor/%s/%f/1.0' % (comp_id, comp_mode)
            requests.get(url)
    sleep(2)
