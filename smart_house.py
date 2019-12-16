from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import Flask
from flask import request
import json
from gpiozero import Motor, LED
from werkzeug.routing import BaseConverter


class IntListConverter(BaseConverter):
    regex = r'\d+(?:,\d+)*,?'

    def to_python(self, value):
        return [int(x) for x in value.split(',')]

    def to_url(self, value):
        return ','.join(str(x) for x in value)

# criação do servidor
app = Flask(__name__)
app.url_map.converters['int_list'] = IntListConverter

# systemctl status mongodb
client = MongoClient("localhost", 27017)
smart_house_db = client["smart_house"]
components_table = smart_house_db["component"]
time_constraint_table = smart_house_db["time_constraint"]
sensor_config_table = smart_house_db["sensor_config"]
components = {}
ports_used = set()


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
        components[comp_id] = LED(int(ports[0]))
    elif data['component'] == 'motor':
        if len(ports) < 2:
            return False
        components[comp_id] = Motor(int(ports[0]), int(ports[1]))
    for port in ports:
        ports_used.add(port)
    return True


def load_from_db():
    all_data = components_table.find()
    for data in all_data:
        add_component(str(data['_id']), data)
    return


# definição de funções das páginas
@app.route("/insert-component", methods=['POST'])
def insert_component():
    content = request.get_json()
    if not check_valid_component(content):
        return "Esse documento não é válido", 500
    comp_id = str(components_table.insert(content))
    could_add = add_component(comp_id, content)
    if not could_add:
        return "As portas não são válidas", 500
    result = {"id": comp_id}
    return json.dumps(result), 200


@app.route("/insert-time-constraint/<string:comp_id>/<string:action_time>/<float:mode>", methods=['GET'])
def insert_time_constraint(comp_id, action_time, mode):
    insert_document = {'comp_id': comp_id, 'action_time': action_time, 'mode': mode}
    comp_id = str(time_constraint_table.insert(insert_document))
    result = {"id": comp_id}
    return json.dumps(result), 200


@app.route("/insert-sensor-config/<string:sensor_id>/<float:threshold>/<string:comp_id>/<float:mode>", methods=['GET'])
def insert_sensor_config(sensor_id, threshold, comp_id, mode):
    insert_document = {'sensor_id': sensor_id, 'threshold': threshold, 'comp_id': comp_id, 'mode': mode}
    comp_id = str(sensor_config_table.insert(insert_document))
    result = {"id": comp_id}
    return json.dumps(result), 200


@app.route("/control-motor/<string:comp_id>/<float:speed>/<int:mode>", methods=['GET'])
def control_motor(comp_id, speed, mode):
    if comp_id not in components:
        return "Erro ao encontrar motor", 500
    motor = components[comp_id]
    if mode > 0:
        motor.forward(speed)
    else:
        motor.backward(speed)
    return "Sucesso", 200


@app.route("/control-led/<string:comp_id>/<int:mode>", methods=['GET'])
def control_led(comp_id, mode):
    print(components)
    if comp_id not in components:
        return "Erro ao encontrar led", 500
    led = components[comp_id]
    if mode > 0:
        led.on()
    else:
        led.off()
    return "Sucesso!", 200

# rode o servidor
load_from_db()
app.run(port=5000, debug=False)


