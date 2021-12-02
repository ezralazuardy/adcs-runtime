<a href="https://www.python.org">
    <img alt="Python Version" src="https://img.shields.io/badge/python-%3E%3D%203-blue">
</a>
<a href="https://pypi.org/project/pip">
    <img alt="PIP Version" src="https://img.shields.io/badge/pip-%3E%3D%2021-cadetblue">
</a>
<a href="https://github.com/ezralazuardy/adcs-runtime/blob/master/LICENSE">
  <img src="https://img.shields.io/github/license/ezralazuardy/pluvia-api" alt="License">
</a>

# 🤖 adcs-runtime

A simple virtual runtime for Automated Autonomous Drone Communication System.

This repository contains python script to simulate the several ADCS components runtime such as Drone processes and the Commander Server process.

ADCS Backend repository is accesible at https://adcs.ezralazuardy.com.

### ✅ Prerequisites

* [Python](https://www.python.org) `v3`
* [pip](https://pypi.org/project/pip) `v21`
* [paho-mqtt](https://pypi.org/project/paho-mqtt) `v1.6`
* [requests](https://pypi.org/project/requests) `v2.26`
* [dotenv](https://pypi.org/project/dotenv) `v0.0.5`
* [HiveMQ Cloud Broker Credential](https://www.hivemq.com/mqtt-cloud-broker)

> You need to deploy a new `HiveMQ Cloud Broker` instance for the MQTT Broker (AWS / Azure provider is acceptable).

### 🚀 Getting Started

Clone this repository.

```bash
# clone repo
git clone https://github.com/ezralazuardy/adcs-runtime.git
```

On the root project directory, copy the `.env.example` to `.env` and add your
[HiveMQ Cloud Broker](https://www.hivemq.com/mqtt-cloud-broker) credential and
[ADCS Backend](https://github.com/ezralazuardy/adcs) key.

```bash
# copy the .env.example
cp .env.example .env
```

Now you can run the instance.

``` bash
# run the commander server instance
python commander.py

# run the drone instance
python drone.py --id drone-1 --type drone-a
python drone.py --id drone-2 --type drone-b
python drone.py --id drone-3 --type drone-c
```