from pymongo import MongoClient
from bson.objectid import ObjectId
from time import sleep
from datetime import datetime, timedelta
import requests

client = MongoClient("localhost", 27017)
smart_house_db = client["smart_house"]
components_table = smart_house_db["component"]
time_constraint_table = smart_house_db["time_constraint"]
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
    table_configs = time_constraint_table.find()
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
    print("Checando se componente deve ser ativado")
    for config in config_to_process:
        comp_id = config['comp_id']
        comp_mode = config['mode']
        config_time_list = config['action_time'].split(":")
        config_time = datetime(year=cur_time.year, month=cur_time.month, day=cur_time.day,
                               hour=int(config_time_list[0]), minute=int(config_time_list[1]))
        print(config_time)
        print(cur_time)
        if config_time >= cur_time - delta and config_time <= cur_time + delta:
            print("COMPONENTE ATIVADO!")
            comp_name = components[comp_id]
            if comp_name == 'led':
                url += 'control-led/%s/%.2f' % (comp_id, comp_mode)
            else:
                url += 'control-motor/%s/%.2f/1.0' % (comp_id, comp_mode)
            response = requests.get(url)
            print(response)
    sleep(2)
