/******************************************************************************
Este trabajo se ha cargado en el Arduino Nano 33 BLE Sense Rev2
******************************************************************************/
#include <project-3_inferencing.h>

int beat_old = 0;
float threshold = 630.0;  //Threshold at which BPM calculation occurs
boolean belowThreshold = true;

int ts = 0; // tiempo que pasa para recoger los valores (5ms)
int t_ciclo = 0; // tiempo que pasa para enviar los datos al modelo (4s)
float valor_ECG; // Valor del ECG, entrada 1
float BPM = 0.0;  // el valor del ritmo cardiaco, entrada 2

float output0 = 0.0; // valor de la clasificación del valor 0
float output1 = 0.0; // valor de la clasificación del valor 1
int cont_alarma = 0; // si llega a 3 se genera la alarma
boolean alarma = false;

int muestra_i = 0; // la posicion de features, E [0,1599]

float features[1600];

void setup () {

  Serial.begin(115200);

  // Asignamos los pines de la placa
  pinMode(10, INPUT); // Detectan ausencia de electrodos para
  pinMode(11, INPUT); // interrumpir el programa

  pinMode(D2, OUTPUT); // señal de alarma

  pinMode(LEDB, OUTPUT); //BLUE
  pinMode(LEDG, OUTPUT); //GREEN
  pinMode(LEDR, OUTPUT); //RED
  digitalWrite(LEDR, HIGH);
  digitalWrite(LEDB, HIGH);
  digitalWrite(LEDG, LOW);

  Serial.println("Inicializacion terminada. Leemos los datos del sensor de ECG...");
}

void loop() {
  if((digitalRead(10) == 1)||(digitalRead(11) == 1)){
    Serial.println("Error: comprueba los electrodos.");
  }
  else{
    int time = millis();
    valor_ECG = analogRead(A1); // si hay que reajustar la señal
    //valor_ECG*=GAIN;
    //valor_ECG-=OFFSET;
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
    if (time - ts >= 5) // cada 5ms añadimos información
    {
      features[muestra_i] = valor_ECG/335 - 1.5; //escalamos los datos, 
                          // esto puede variar dependiendo de la persona
      features[muestra_i+1] = BPM;
      muestra_i += 2;
      ts = time;
    }

    if (muestra_i >= 1600) // 800 muestras para cada entrada (2), cada una cada 5ms => 4s (mas tiempo si hay delay)
    {
      Serial.print("Tiempo del ciclo en milisegundos: ");
      Serial.println(time-t_ciclo);
      Serial.print("BPM: ");
      Serial.println(BPM);
      muestra_i = 0;
      t_ciclo = time;
      model1();
    }

    if (cont_alarma>=3 && alarma==false) { //luz roja
      alarma = true;
      digitalWrite(D2,HIGH); // enviamos señal de alarma al NodeMCU
      digitalWrite(LEDR, LOW); 
      digitalWrite(LEDG, HIGH);
    } else if (cont_alarma<3 && alarma==true) { //luz verde
      alarma = false;
      digitalWrite(D2,LOW);
    }
  }
  //Wait for a bit to keep serial data from saturating
  delay(1);
}

void calculateBPM () // calculamos el intervalo RR en bpm
{  
  int beat_new = millis();           
  int diff = beat_new - beat_old;    
  BPM = 60000 / diff;                
  beat_old = beat_new;
}

int raw_feature_get_data(size_t offset, size_t length, float *out_ptr) {
    memcpy(out_ptr, features + offset, length * sizeof(float));
    return 0;
}

void print_inference_result(ei_impulse_result_t result);

void model1()
{
  if (sizeof(features) / sizeof(float) != EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE) {
      ei_printf("The size of your 'features' array is not correct. Expected %lu items, but had %lu\n",
          EI_CLASSIFIER_DSP_INPUT_FRAME_SIZE, sizeof(features) / sizeof(float));
      delay(1000);
      return;
  }

  ei_impulse_result_t result = { 0 };

  // the features are stored into flash, and we don't want to load everything into RAM
  signal_t features_signal;
  features_signal.total_length = sizeof(features) / sizeof(features[0]);
  features_signal.get_data = &raw_feature_get_data;

  // invoke the impulse
  EI_IMPULSE_ERROR res = run_classifier(&features_signal, &result, false /* debug */);
  if (res != EI_IMPULSE_OK) {
      ei_printf("ERR: Failed to run classifier (%d)\n", res);
      return;
  }
  output0 = (float)result.classification[0].value;
  output1 = (float)result.classification[1].value;
  Serial.print("Predicted values: \n 0:");
  Serial.print(output0);
  Serial.print("; 1: ");
  Serial.println(output1);

  if (output1>0.9) {
    cont_alarma ++;
    if (alarma==false) { //luz amarilla
      digitalWrite(LEDR, LOW);
      digitalWrite(LEDG, LOW);
    }
  } else { //luz verde
    cont_alarma = 0;
    digitalWrite(LEDR, HIGH);
    digitalWrite(LEDG, LOW);
  }
  delay(1000);
}

void print_inference_result(ei_impulse_result_t result) {
    // Print how long it took to perform inference
    ei_printf("Timing: DSP %d ms, inference %d ms\n",
            result.timing.dsp,
            result.timing.classification);
    //Print the prediction results (classification)
    ei_printf("Predictions:\r\n");
    for (uint16_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
        ei_printf("  %s: ", ei_classifier_inferencing_categories[i]);
        ei_printf("%.5f\r\n", result.classification[i].value);
    }

}