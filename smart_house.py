from pymongo import MongoClient
from flask import Flask
from flask import request
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


# definição de funções das páginas
@app.route("/insert-component", methods=['POST'])
def insert_component():
    content = request.get_json()
    response = collection.insert(content)
    result = {"id": str(response)}
    return result


@app.route("/control-motor/<string:comp_id>/<float:speed>/<int:mode>", methods=['GET'])
def control_motor(comp_id, speed, mode):
    motor_data = find_component_db(comp_id)
    if motor_data is None:
        return "Erro ao encontrar motor", 500
    port_list = motor_data['ports']
    if len(port_list) < 2:
        return "Motor deve ter duas portas especificadas", 500
    motor = Motor(port_list[0], port_list[1])
    if mode > 0:
        motor.forward(speed)
    else:
        motor.backward(speed)
    return "Sucesso", 200


@app.route("/control-led/<int:comp_id>/<int:mode>")
def control_led(comp_id, mode):
    led_data = find_component_db(comp_id)
    if led_data is None:
        return "Erro ao encontrar led", 500
    port = led_data['ports'][0]
    led = LED(port)
    if mode > 0:
        led.on()
    else:
        led.off()
    return "Sucesso!", 200


def find_component_db(comp_id):
    data = {"_id": comp_id}
    return collection.find_one(data)

# rode o servidor
app.run(port=5000, debug=False)

