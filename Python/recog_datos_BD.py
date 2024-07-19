###################################################################
#
#    Este fichero se ha creado para obtener los datos de ECG
#    de la base de datos y utilizarlos para crear gráficas y
#    generar los ficheros .csv
#
#    La base de datos utilizada se ha obtenido de Physionet:
#    https://archive.physionet.org/physiobank/database/szdb/
#
###################################################################

import wfdb
from wfdb import processing
import heartpy
import heartpy.filtering
import pandas as pd
import matplotlib.pyplot as plt


def plotdata(n,sfrom,sto):
    """
        Para graficar las señales de ECG de la base de 
        datos de Physionet
    """
    # Ejemplo de la Figura 6:
    # n = 1
    # sfrom = 10000
    # sto = 10500
    fs = 200
    rec_name = 'sz0'+n
    folder = 'szdb/'

    record = wfdb.rdrecord(record_name=folder+rec_name,sampfrom=sfrom,sampto=sto)

    # MOSTRAR LA SEÑAL SIN FILTRAR

    # wfdb.plot_wfdb(record=record,
    #           title='Señal de ECG normal de la grabación 0'+n,plot_sym=True)

    # MOSTRAR LA SEÑAL TRAS SER FILTRADA

    signal = record.p_signal
    time = []
    for i in range(0,sto-sfrom): time.append(i/fs)
    
    # heartpy elimina el offset de la señal, así que lo añadimos (para graficar únicamente)
    if (n=='6'): offset = 2.7
    else: offset = 1.05

    filtered = heartpy.filtering.filter_signal(data=signal[:,0],cutoff= [1,30], sample_rate=fs,filtertype='bandpass') + offset
    
    plt.plot(time,signal,'b',label='Señal de ECG sin filtrar')
    plt.plot(time,filtered,'r',label='Señal filtrada')
    plt.xlabel("tiempo (s)")
    plt.ylabel("Señal de ECG (mV)")
    plt.legend()
    plt.show()


def t2samp(time, fs=200):
    """
    Convertimos el formato de tiempo (hh:mm:ss) en número de muestras (n)
    time:   tiempo a convertir
    fs:     frecuencia de muestreo (= 200 en nuestro caso)
    """
    hour,min,sec = time.split(':')
    
    time_seg = int(hour)*3600+int(min)*60+int(sec)
    samples = time_seg * fs
    return samples


def readdata_v1(n,sfrom,sto,is_sz,fileName,fs=200):
    """
    Lee los datos de la grabación y escribe en un fichero .csv con una matriz
    de dimensión (sto-sfrom)x3, cada fila de tipo "tiempo[ms], ECG_value[mV], iz_sz"

    n:          número de la grabación
    sfrom:      inicio de la señal (sample_from)
    sto:        fin de la señal (sample_to)
    iz_sz:      0 si el ECG es normal
                1 si corresponde a una convulsión
    signal:     señal de ECG (200 muestras por segundo => ts = 5ms)
    fileName:   nombre del fichero .csv que creamos
    fs:         frecuencia de muestreo
    """
    rec_name = 'sz0'+n
    folder = 'szdb/'

    # Leemos la grabacion y obtenemos la señal física (en mV)
    record = wfdb.rdrecord(record_name=folder+rec_name,sampfrom=sfrom,sampto=sto)
    s_fisica = record.p_signal[:,0]

    # Filtramos la señal
    signal = heartpy.filtering.filter_signal(data=s_fisica,cutoff= [1,30], sample_rate=fs,filtertype='bandpass')

    # Obtenemos las listas de tiempo y convulsion, de la misma dimensión que signal
    t_array = []
    time = 0
    sz_array = []

    for i in range(0,sto-sfrom):
        t_array.append(time)
        time += 5 # sumamos 5 milisegundos
        sz_array.append(is_sz)

    data = {'timestamp':t_array,'signal':signal,'seizure':sz_array}
    df = pd.DataFrame(data=data)
    df.to_csv('samples/'+fileName+'.csv',index=False)


def readdata_v2(n,sfrom,sto,is_sz,fileName,fs=200):
    """
    Lee los datos de la grabación y escribe en un fichero .csv con una matriz
    de dimensión (sto-sfrom)x4, cada fila de tipo
    "tiempo[ms], ECG_value[mV], heart_rate[bpm], iz_sz"

    n:          número de la grabación
    sfrom:      inicio de la señal (sample_from)
    sto:        fin de la señal (sample_to)
    iz_sz:      0 si el ECG es normal
                1 si corresponde a una convulsión
    signal:     señal de ECG (200 muestras por segundo => ts = 5ms)
    fileName:   nombre del fichero .csv que creamos
    fs:         frecuencia de muestreo
    """
    rec_name = 'sz0'+n
    folder = 'szdb/'

    # Leemos la grabacion y obtenemos la señal física (en mV)
    record = wfdb.rdrecord(record_name=folder+rec_name,sampfrom=sfrom,sampto=sto)
    s_fisica = record.p_signal[:,0]

    # Recogemos en una lista el número de muestras de cada intervalo R-R
    rr_samples = processing.ann2rr(record_name=folder+rec_name,extension='ari')
    rr_samples = rr_samples.tolist()

    # Filtramos la señal
    signal = heartpy.filtering.filter_signal(data=s_fisica,cutoff= [1,30], sample_rate=fs,filtertype='bandpass')

    # Queremos una lista de dimensión 1x(sto-sfrom) que contenga el ritmo cardiaco de cada muestra
    RR_interval = []
    n_samp = 0
    for j in range(0,len(rr_samples)):
        rr_val = rr_samples[j]
        n_samp+=rr_val
        if (n_samp >= sfrom and n_samp <= sto):
            for i in range(0,rr_val): RR_interval.append(fs*60/rr_val) # [bpm]

    # RR_interval puede que no coincida exactamente con la longitud de signal
    # por errores en la medida o en las anotaciones => modificamos len(RR_interval)
    dif = len(signal)-len(RR_interval)
    if (dif>0):
        for i in range(0,dif): RR_interval.append(0)
    elif (dif<0):  RR_interval = RR_interval[:dif]

    # Obetnemos las listas de tiempo y convulsion, de la misma dimensión que signal
    t_array = []
    time = 0
    sz_array = []

    for i in range(0,sto-sfrom):
        t_array.append(time)
        time += 5 # sumamos 5 milisegundos
        sz_array.append(is_sz)

    data = {'timestamp':t_array,'signal':signal,'heart_rate':RR_interval,'seizure':sz_array}
    df = pd.DataFrame(data=data)
    df.to_csv('samples2/'+fileName+'.csv',index=False)


# Ejemplo de sz01:

# readdata_v2('1',t2samp('1:06:05'),t2samp('1:08:05'),0,'sz01_1')
# readdata_v2('1',t2samp('1:10:18'),t2samp('1:18:18'),0,'sz01_2')
# readdata_v2('1',t2samp('1:22:57'),t2samp('1:29:57'),0,'sz01_3')
# readdata_v2('1',t2samp('0:14:36'),t2samp('0:16:36'),1,'sz01_4')
