/*
  Este código se ha cargado en el NodeMCU con módulo WiFi ESP8266
  Envía la señal de alarma al ordenador
*/
#include <ESP8266WiFi.h>
#include <ArduinoMqttClient.h>
#include "arduino_secrets.h" // donde definimos el SSID y PASS

char ssid[] = SECRET_SSID;    // el nombre de la red
char pass[] = SECRET_PASS;    // la contraseña

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

const char broker[] = "test.mosquitto.org";
// segun "test.mosquitto.org", el puerto 1883 corresponde
//                 a "MQTT, unencrypted, unauthenticated"
int port = 1883;
const char topic1[] = "ECG/ALARMA";
const char topic2[] = "ECG/OK";

const long intervalo = 200; 
unsigned long tiempo_0 = 0;

boolean alarma = false;

void setup() {
  pinMode(D2,INPUT);
  pinMode(2,OUTPUT); //active on LOW

  Serial.begin(115200);

  // intentamos conectarnos a la red
  Serial.print("Attempting to connect to WPA SSID: ");
  Serial.println(ssid);
  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {
    // error, se vuelve a intentar
    Serial.print(".");
    delay(5000);
  }

  Serial.println("You're connected to the network");
  Serial.println();

  Serial.print("Attempting to connect to the MQTT broker: ");
  Serial.println(broker);

  if (!mqttClient.connect(broker, port)) {
    Serial.print("MQTT connection failed! Error code = ");
    Serial.println(mqttClient.connectError());

    while (1);
  }

  Serial.println("You're connected to the MQTT broker!");
  Serial.println();
}

void loop() {
  mqttClient.poll();

  unsigned long tiempo_1 = millis();
  // cada 200 milisegundos comprobamos el valor de la señal de alarma
  if (tiempo_1 - tiempo_0 >= intervalo) {
    tiempo_0 = tiempo_1;
    alarma = (digitalRead(D2) == HIGH);
    if (alarma) {
      digitalWrite(2,LOW);
      Serial.println("Se ha detectado un ataque epiléptico!");
      // se envía el mensaje de alarma via Wi-Fi
      mqttClient.beginMessage(topic1);
      mqttClient.print("Se ha detectado un ataque epiléptico!");
      mqttClient.endMessage();
    } else {
      digitalWrite(2,HIGH);
      Serial.println("Estado del paciente OK.");
      mqttClient.beginMessage(topic2);
      mqttClient.print("Estado del paciente OK.");
      mqttClient.endMessage();
    }
  }
}