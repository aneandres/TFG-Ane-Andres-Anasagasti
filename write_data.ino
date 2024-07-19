
// Este código se ha cargado en el Arduino Nano 33 BLE Sense Rev2
// para recoger datos del sensor y crear un fichero.csv

int beat_old = 0;
float threshold = 700.0;  //Threshold at which BPM calculation occurs
boolean belowThreshold = true;

int ts = 0; // tiempo que pasa para recoger los valores (5ms)
float valor_ECG; // Valor del ECG, entrada 1
float BPM = 0.0;  // el valor del ritmo cardiaco, entrada 2
int muestra_i = 0; // la posicion de features, E [0,1599]

int timestamp = 0;

void setup() {
  Serial.begin(115200);
  pinMode(10, INPUT); // Setup for leads off detection LO +
  pinMode(11, INPUT); // Setup for leads off detection LO -
  Serial.println("timestamp,signal,heart_rate,seizure");
}

void loop() {
  
  if((digitalRead(10) == 1)||(digitalRead(11) == 1)){
    Serial.println('!');
  }
  else{
    int time = millis();
    valor_ECG = analogRead(A0); 
    
    // BPM calculation check
    if (valor_ECG > threshold && belowThreshold == true)
    {
      calculateBPM();
      belowThreshold = false;
    }
    else if(valor_ECG < threshold)
    {
      belowThreshold = true;
    }
    String tocsv="";
    if (time - ts >= 5) // cada 5ms añadimos información
    {
      valor_ECG = valor_ECG/335 - 1.2; //escalamos los datos
      timestamp += 5;
      if (timestamp >= 2000)
      { 
        int mytime = timestamp-2000;
        tocsv += mytime;
        tocsv += ",";
        tocsv += valor_ECG;
        tocsv += ",";
        tocsv += BPM;
        tocsv += ",0";
        Serial.println(tocsv);
      }
      ts = time;
    }
  }
  //Wait for a bit to keep serial data from saturating
  delay(1);
}

void calculateBPM () 
{  
  int beat_new = millis();    // get the current millisecond
  int diff = beat_new - beat_old;    // find the time between the last two beats
  BPM = 60000 / diff;    // convert to beats per minute
  beat_old = beat_new;
}
