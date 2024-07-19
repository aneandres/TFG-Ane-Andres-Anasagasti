# ################################################################
#
#    Este fichero permite al ordenador recibir el mensaje de 
#    alarma del NodeMCU y reproducir el sonido (alarma.mp3)
#
##################################################################

import paho.mqtt.client as mqtt

import time
from pygame import mixer
    
def on_connect(client, userdata,flags,rc):
    print("Connected with result code"+str(rc))
    client.subscribe("ECG/OK")
    client.subscribe("ECG/ALARMA")

def on_message(client,userdata,msg):
    if msg.topic == "ECG/OK":
        print('Estado del paciente OK')
    elif msg.topic == "ECG/ALARMA":
        mixer.init()
        mixer.music.load("alarma.mp3")
        mixer.music.play()
        print("Se ha detectado un ataque epiléptico!")
        
    
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

    
broker = 'test.mosquitto.org'
port = 1883
keepalive = 60 # se define como "Maximum period in seconds
               # between communications with the broker"

client.connect(broker,port,keepalive)

client.loop_start()
while True:
    time.sleep(0.02)

client.loop_stop()
