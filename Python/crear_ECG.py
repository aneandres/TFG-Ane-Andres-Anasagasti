# ###########################################################################
#
#    Este fichero contiene las funciones que se han creado para 
#    trabajar con señales de ECG (tanto del sensor como de la BD)
#
#############################################################################

import serial  # pip install pyserial


def recoger_datos_Serial():
    """
    Función utilizada para recoger datos del puerto serie del ordenador,
    enviados desde Arduino y recogidos desde Python, para crear muestras
    para el modelo de ML a partir del sensor de ECG AD8232.
    """
    serial_port = 'COM6'
    baud_rate = 115200; # el mismo que en el programa de Arduino
    file_name = "mysample.csv"

    output_file = open(file_name, "w+")
    ser = serial.Serial(serial_port, baud_rate)
    while True:
        line = ser.readline()
        line = line.decode("utf-8") #ser.readline devuelve un binario, lo pasamos a string
        if (line!=""):
            print(line)
            output_file.write(line)


def crear_vector_ECG(dfrom,dto,afrom,ato,nsamples):
    """
    Crea los valores del vector de ECG utilizado para la simulación
    Contempla dos casos: uno de presencia de convulsiones y otro del
    paciente sin convulsiones.

    d(from,to) = rango digital; a(from,to) = rango analogico
    se utilizan para escalar los valores del csv a valores que puedan
    corresponder con los del sensor de ECG (rango de entrada de
    [330,800] a la placa del modelo)

    n_samples = tiempo_total/5ms => t_tot [seg] = 5*n/1000
    """
    txt_ecg = ""
    i = 0 # i E [0,nsamples-1]
    
    txtfile_caso1 = "./samples2/sz01_2.csv" # estado normal
    txtfile_caso2 = "./samples2/sz07_2.csv" # ataque epileptico
    file = open(txtfile_caso1,'r')
    lines = file.readlines()
    lines = lines[1:] #quitamos el titulo del csv

    file1 = open("mysamples/ECGnormal_10seg.txt",'w')
    #file2 = open("mysamples/ECGepilepsia_10seg.txt",'w')
    gain = (dto-dfrom)/(ato-afrom) # escala modificable
    offset = dto/gain-ato
    for line in lines:
        if (i==nsamples): break
        valor_ECG = line.split(',')[1]
        valor_ECG = int((float(valor_ECG)+offset)*gain) # escalamos la señal a los valores deseados

        if (valor_ECG<0): valor_ECG = 0
        elif (valor_ECG>2700): valor_ECG = 2700 # para que la salida no supere los 3.3V
        
        txt_ecg += str(valor_ECG)+', '
        i+=1
    file1.write(txt_ecg)
