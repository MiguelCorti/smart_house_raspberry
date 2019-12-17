from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import Flask
from flask import request
import json
from gpiozero import Motor, LED, DistanceSensor, MotionSensor, LightSensor
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

def check_ports(data):
    ports = data['ports']
    for port in ports:
        if port in ports_used:
            return False
    if data['component'] == 'motor':
        if len(ports) < 2:
            return False
    elif data['component'] == 'distance_sensor':
        if len(ports) < 2:
            return False
    return True

def add_component(comp_id, data):
    ports = data['ports']
    if data['component'] == 'led':
        components[comp_id] = (LED(int(ports[0])), data['component'])
    elif data['component'] == 'motor':
        components[comp_id] = (Motor(int(ports[0]), int(ports[1])), data['component'])
    elif data['component'] == 'distance_sensor':
        components[comp_id] = (DistanceSensor(trigger=int(ports[0]), echo=int(ports[1])), data['component'])
    elif data['component'] == 'motion_sensor':
        components[comp_id] = (MotionSensor(int(ports[0])), data['component'])
    elif data['component'] == 'light_sensor':
        components[comp_id] = (LightSensor(int(ports[0])), data['component'])
    for port in ports:
        ports_used.add(port)
    return


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
        return "Esse documento não é válido", 400
    if not check_ports(content):
        return "As portas não são válidas", 400
    comp_id = str(components_table.insert(content))
    add_component(comp_id, content)
    result = {"id": comp_id}
    return json.dumps(result), 200


@app.route("/insert-time-constraint", methods=['POST'])
def insert_time_constraint():
    content = request.get_json()
    comp_id = str(time_constraint_table.insert(content))
    result = {"id": comp_id}
    return json.dumps(result), 200


@app.route("/insert-sensor-config", methods=['POST'])
def insert_sensor_config():
    content = request.get_json()
    comp_id = str(sensor_config_table.insert(content))
    result = {"id": comp_id}
    return json.dumps(result), 200


@app.route("/control-motor/<string:comp_id>/<float:speed>", methods=['GET'])
def control_motor(comp_id, speed):
    if comp_id not in components:
        return "Erro ao encontrar motor", 400
    motor, comp_name = components[comp_id]
    if comp_name != 'motor':
        return "Esse componente nao eh um motor", 400
    motor.forward(speed)
    return "Sucesso", 200


@app.route("/control-led/<string:comp_id>/<float:mode>", methods=['GET'])
def control_led(comp_id, mode):
    if comp_id not in components:
        return "Erro ao encontrar led", 400
    led, comp_name = components[comp_id]
    if comp_name != 'led':
        return "Esse componente nao eh um led", 400
    if mode > 0.0:
        led.on()
    else:
        led.off()
    return "Sucesso!", 200


@app.route("/get-distance-sensor/<string:comp_id>", methods=['GET'])
def get_distance_sensor(comp_id):
    if comp_id not in components:
        return "Erro ao encontrar sensor de distancia", 400
    sensor, comp_name = components[comp_id]
    if comp_name != 'distance_sensor':
        return "Esse componente nao eh um sensor de distancia", 400
    return ('%.2f' % sensor.distance), 200


@app.route("/get-light-sensor/<string:comp_id>", methods=['GET'])
def get_light_sensor(comp_id):
    if comp_id not in components:
        return "Erro ao encontrar sensor de luz", 400
    sensor, comp_name = components[comp_id]
    if comp_name != 'light_sensor':
        return "Esse componente nao eh um sensor de luz", 400
    return ('%.2f' % sensor.value), 200

# rode o servidor
load_from_db()
app.run(port=5000, debug=False)


