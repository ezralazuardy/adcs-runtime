import os
import json
import requests
import logging
import paho.mqtt.client as paho
from paho import mqtt
from dotenv import load_dotenv

load_dotenv()
logging.getLogger('requests').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)


class JsonSerializable(object):
    def to_json(self):
        return json.dumps(self.__dict__)

    def __repr__(self):
        return self.to_json()


class DeviceType(JsonSerializable):
    def __init__(self, identifier):
        self.type = 'server'
        self.id = identifier


class FetchStatus(JsonSerializable):
    def __init__(self, drone):
        self.action = 'status'
        self.target_id = drone['target_id']
        self.target_type = drone['target_type']


class UpdateLocation(JsonSerializable):
    def __init__(self, location):
        self.action = 'location'
        self.target_id = location['target_id']
        self.target_type = location['target_type']
        self.lat = location['lat']
        self.lon = location['lon']


class ResultStatus(JsonSerializable):
    def __init__(self, device, data):
        self.id = device.id
        self.type = device.type
        self.target_id = data['id']
        self.target_type = data['type']
        self.battery = data['battery']
        self.online = int(data['online'])


class ResultLocation(JsonSerializable):
    def __init__(self, device, data):
        self.result = int(True)
        self.id = device.id
        self.type = device.type
        self.target_id = data['id']
        self.target_type = data['type']
        self.lat = data['lat']
        self.lon = data['lon']


device = DeviceType('commander-server')
backend_channel = str(os.getenv('HIVEMQ_CLOUD_BROKER_BACKEND_CHANNEL'))
commander_channel = str(os.getenv('HIVEMQ_CLOUD_BROKER_COMMANDER_CHANNEL'))
drone_channel = str(os.getenv('HIVEMQ_CLOUD_BROKER_DRONE_CHANNEL'))
backend_url = 'https://adcs.test/'
headers = {
    'Accept': 'application/json',
    'Content-type': 'application/json',
    'User-Agent': 'mqtt',
    'Key': str(os.getenv('ADCS_BACKED_KEY'))
}
qos = int(os.getenv('HIVEMQ_CLOUD_BROKER_QOS', 2))


def on_connect(client, userdata, flags, rc, properties=None):
    print('CONNACK received with code %s' % (rc))
    client.subscribe(drone_channel, qos=qos)
    client.subscribe(backend_channel, qos=qos)


def on_publish(client, userdata, mid):
    print('published: %s' % (str(mid)))


def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print('subscribed: %s' % (str(mid)))


def on_message(client, userdata, msg):
    print('received: %s %s %s' % (msg.topic, str(msg.qos), str(msg.payload)))
    try:
        payload = json.loads(str(msg.payload.decode('utf-8')))
        action = payload['action']
        if action == 'status':
            if msg.topic == drone_channel:
                publish_status(payload)
            elif msg.topic == backend_channel:
                fetch_status(payload)
            else:
                print('error: unknown topic, skipping...')
        elif action == 'location':
            if msg.topic == drone_channel:
                publish_location(payload)
            elif msg.topic == backend_channel:
                update_location(payload)
            else:
                print('error: unknown topic, skipping...')
        else:
            print('error: unknown action, skipping...')
    except Exception as e:
        print(str(e))


def fetch_status(target):
    publish_action(FetchStatus(target))


def update_location(location):
    publish_action(UpdateLocation(location))


def publish_action(action: JsonSerializable):
    client.publish(commander_channel, payload=action.to_json(), qos=qos)


def publish_status(status):
    http_post('api/drones', ResultStatus(device, status).to_json())


def publish_location(location):
    http_post('api/drones', ResultLocation(device, location).to_json())


def http_post(path, data):
    print('posting result to ADCS Backend...')
    response = requests.post(
        headers=headers,
        url=backend_url + path,
        data=str(data),
        timeout=5,
        verify=bool(int(os.getenv('SSL_VERIFICATION')))
    )
    print('status code: %d' % (int(response.status_code)))
    try:
        print(json.loads(str(response.text)))
    except:
        print('error: backend response is not a valid JSON format, skipping...')


client = paho.Client(client_id=device.id, userdata=device.to_json(), protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set(str(os.getenv('HIVEMQ_CLOUD_BROKER_USERNAME')), str(os.getenv('HIVEMQ_CLOUD_BROKER_PASSWORD')))
client.connect(str(os.getenv('HIVEMQ_CLOUD_BROKER_HOST')), int(os.getenv('HIVEMQ_CLOUD_BROKER_PORT')))
client.loop_forever()
