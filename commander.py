import os
import json
import requests
import paho.mqtt.client as paho
from paho import mqtt
from dotenv import load_dotenv

load_dotenv()


class JsonSerializable(object):
    def to_json(self):
        return json.dumps(self.__dict__)

    def __repr__(self):
        return self.to_json()


class DeviceType(JsonSerializable):
    def __init__(self, identifier):
        self.type = "server"
        self.id = identifier


class FetchStatus(JsonSerializable):
    def __init__(self, target):
        self.action = "status"
        self.target = target


class UpdateLocation(JsonSerializable):
    def __init__(self, target, lat, lon):
        self.action = "location"
        self.target = target
        self.lat = lat
        self.lon = lon


class ResultStatus(JsonSerializable):
    def __init__(self, current_device, data):
        self.id = current_device.id
        self.type = current_device.type
        self.battery = data['battery']
        self.online = int(data['online'])


class ResultLocation(JsonSerializable):
    def __init__(self, current_device, data):
        self.result = int(True)
        self.id = current_device.id
        self.type = current_device.type
        self.lat = data['lat']
        self.lon = data['lon']


commander_channel = 'adcs/commander'
client_channel = 'adcs/drones'
device = DeviceType('commander-server')
backend_url = 'https://adcs.test/'
headers = {
    'Content-type': 'application/json',
    'Key': str(os.getenv('ADCS_BACKED_KEY'))
}
qos = int(os.getenv('HIVEMQ_CLOUD_BROKER_QOS', 2))


def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s" % (rc))
    client.subscribe(client_channel, qos=qos)


def on_publish(client, userdata, mid):
    print("published: %s" % (str(mid)))


def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("subscribed: %s" % (str(mid)))


def on_message(client, userdata, msg):
    print("received: %s %s %s" % (msg.topic, str(msg.qos), str(msg.payload)))
    try:
        payload = json.loads(str(msg.payload.decode("utf-8")))
        action = payload['action']
        if payload['id'] is not None:
            target = payload['id']
            if action == "status":
                publish_status(target, payload)
            elif action == "location":
                publish_location(target, payload)
            else:
                print("error: unknown payload action, skipping...")
        elif payload['target'] is not None:
            target = payload['target']
            if action == "status":
                fetch_status(target)
            elif action == "location":
                update_location(target, payload)
            else:
                print("error: unknown payload action, skipping...")
        else:
            print("error: unknown payload format, skipping...")
    except Exception as e:
        print(str(e))


def fetch_status(target):
    publish_action(FetchStatus(target))


def update_location(target, location):
    publish_action(UpdateLocation(target, location['lat'], location['lon']))


def publish_action(action: JsonSerializable):
    client.publish(commander_channel, payload=action.to_json(), qos=qos)


def publish_status(target, status):
    http_post("api/drones", ResultStatus(device, status).to_json())


def publish_location(target, location):
    http_post("api/drones", ResultLocation(device, location).to_json())


def http_post(path, data):
    print('posting result to ADCS Backend...')
    response = requests.post(backend_url + path, data=json.loads(data), headers=headers, timeout=5)
    print('status code: %d' % (int(response.status_code)))
    print(response.text)


client = paho.Client(client_id=device.id, userdata=device.to_json(), protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set(str(os.getenv('HIVEMQ_CLOUD_BROKER_USERNAME')), str(os.getenv('HIVEMQ_CLOUD_BROKER_PASSWORD')))
client.connect(str(os.getenv('HIVEMQ_CLOUD_BROKER_HOST')), int(os.getenv('HIVEMQ_CLOUD_BROKER_PORT')))
client.loop_forever()
