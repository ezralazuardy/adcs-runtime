import os
import sys
import json
import argparse
import paho.mqtt.client as paho
from paho import mqtt
from dotenv import load_dotenv

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--id", help="Drone identifier")
args = parser.parse_args()

if not args.id:
    sys.exit("Drone identifier must be set! (using --id)")

load_dotenv()


class JsonSerializable(object):
    def to_json(self):
        return json.dumps(self.__dict__)

    def __repr__(self):
        return self.to_json()


class DeviceType(JsonSerializable):
    def __init__(self, identifier):
        self.type = "drone"
        self.id = identifier


class ResultStatus(JsonSerializable):
    def __init__(self, device, battery, online):
        self.action = 'status'
        self.id = device.id
        self.type = device.type
        self.battery = battery
        self.online = int(online)


class ResultLocation(JsonSerializable):
    def __init__(self, device, lat, lon):
        self.action = 'location'
        self.id = device.id
        self.type = device.type
        self.lat = lat
        self.lon = lon


commander_channel = "adcs/commander"
client_channel = "adcs/drones"
device = DeviceType(args.id)
qos = int(os.getenv('HIVEMQ_CLOUD_BROKER_QOS', 2))


def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s" % (rc))
    client.subscribe(commander_channel, qos=qos)
    publish_status()


def on_publish(client, userdata, mid):
    print("published: %s" % (str(mid)))


def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("subscribed: %s" % (str(mid)))


def on_message(client, userdata, msg):
    print("received: %s %s %s" % (msg.topic, str(msg.qos), str(msg.payload)))
    try:
        payload = json.loads(str(msg.payload.decode("utf-8")))
        target = payload['target'].strip()
        action = payload['action'].strip()
        if target != device.id:
            return
        if action == "status":
            publish_status()
        elif action == "location":
            publish_location(payload)
        else:
            print("error: unknown payload action, skipping...")
    except Exception as e:
        print(str(e))


def publish_status():
    publish_result(ResultStatus(device, 100, True))


def publish_location(location):
    publish_result(ResultLocation(device, location['lat'], location['lon']))


def publish_result(result):
    client.publish(client_channel, payload=result.to_json(), qos=qos)


client = paho.Client(client_id=args.id, userdata=device.to_json(), protocol=paho.MQTTv5)
client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message
client.on_publish = on_publish
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set(str(os.getenv('HIVEMQ_CLOUD_BROKER_USERNAME')), str(os.getenv('HIVEMQ_CLOUD_BROKER_PASSWORD')))
client.connect(str(os.getenv('HIVEMQ_CLOUD_BROKER_HOST')), int(os.getenv('HIVEMQ_CLOUD_BROKER_PORT')))
client.loop_forever()
