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

client = MongoClient("localhost", 27017)
table = client["test"]
collection = table["sensores"]
components = {}
ports_used = set()


def check_valid_document(document):
    return 'ports' in document and 'env' in document and 'component' in document;


def load_from_db():
    all_data = collection.find()
    for data in all_data:
        if check_valid_document(data):
            comp_id = data['_id']
            ports = data['ports']
            used_port = False
            for port in ports:
                if port in ports_used:
                    used_port = True
            if used_port:
                continue
            if data['component'] == 'led':
                components[comp_id] = LED(ports[0])
                ports_used.add(ports[0])
            elif data['component'] == 'motor':
                if len(ports) < 2:
                    continue
                components[comp_id] = Motor(ports[0], ports[1])
                ports_used.add(ports[0])
                ports_used.add(ports[1])
    return


# definição de funções das páginas
@app.route("/insert-component", methods=['POST'])
def insert_component():
    content = request.get_json()
    response = collection.insert(content)
    result = {"id": str(response)}
    return json.dumps(result)


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
    if comp_id not in components:
        return "Erro ao encontrar led", 500
    led = components[comp_id]
    if mode > 0:
        led.on()
    else:
        led.off()
    return "Sucesso!", 200


def find_component_db(comp_id):
    data = {"_id": ObjectId(comp_id)}
    return collection.find_one(data)

# rode o servidor
load_from_db()
app.run(port=5000, debug=False)

