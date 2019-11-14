import os
import matplotlib.pyplot as plt 
import pandas as pd
#from datetime import *
import calendar
import math
import numpy as np
import warnings

# Funcion que convierte una hora en formato HH:MM:SS en un entero que representa 
# los segundos transcurridos en el dia para dicha hora.
def hr_to_sec(hour):
  h,m,s = hour.split(':')
  sec = int(h)*3600+int(m)*60+int(s)
  return sec

# Funcion para leer los dos tipos de archivo de registro de patentes y convertirlos
# en un dataframe 
def file_to_df(filename):
    if ".csv" in filename:
        df_file = pd.read_csv(filename,sep=";")
        patentes = df_file["Patente"].values.tolist()
        hora = [ fecha.split(" ")[1] for fecha in df_file["Fecha"].values.tolist() ]
        hora_sec = [hr_to_sec(h) for h in hora]
        data = {'Patente':patentes, 'Hora': hora, 'Hora_sec':hora_sec}
        df = pd.DataFrame(data)
        df = df.sort_values(by=['Hora_sec'])
        df.drop_duplicates(subset = ['Patente','Hora_sec'],keep='first',inplace=True)
    if ".log" in filename:
        f = open(filename,"r")
        data_patentes = []
        data_hora = []
        data_hora_sec = []
        for line in f.readlines()[2:]:
            line_split = line.split(";")
            data_patentes.append(line_split[4].split("=")[1].strip())
            data_hora.append(line_split[0].split("=")[1][0:8])
            data_hora_sec.append(hr_to_sec(line_split[0].split("=")[1][0:8]))
        f.close()
        data = data = {'Patente':data_patentes, 'Hora': data_hora, 'Hora_sec':data_hora_sec}
        df = pd.DataFrame(data, columns = ["Patente","Hora","Hora_sec"])
        df.drop_duplicates(subset = ['Patente','Hora_sec'],keep='first',inplace=True)
    return df

# Funcion que encuentra todas las patentes que estan duplicadas
def get_dupes(a):
  seen = {}
  dupes = []
  for x in a:
      if x not in seen:
          seen[x] = 1
      else:
          if seen[x] == 1:
              dupes.append(x)
          seen[x] += 1
  return dupes

# Funcion que obtiene todos los time stamps presentes para una patente
def get_hora_sec(pat,df):

  df_patentes = df['Patente'].values.tolist()
  df_hora_sec = df['Hora_sec'].values.tolist()

  indices = [i for i, x in enumerate(df_patentes) if x == pat]
  hora_sec = []
  for i in indices:
    hora_sec.append(df_hora_sec[i])
  
  return hora_sec

# Funcion que obtiene los time stamps a excluir dada una patente duplicada
def get_tmstmp_exclude(pat,df, thr):
  hora_sec = get_hora_sec(pat,df)

  i = 0
  j = 1
  excluir = []
  while i < len(hora_sec)-1:
    while (hora_sec[j] - hora_sec[i]) < thr and j<len(hora_sec)-1:
      excluir.append(hora_sec[j])
      j+=1
    i=j
    j+=1
  if len(excluir)!=0:
    return excluir
  else: 
    return 0

def get_pat_dict(df,thr):
  duplicadas = get_dupes(df['Patente'].values.tolist())
  dict_exclude = {}
  for patente in duplicadas:
    excluir = get_tmstmp_exclude(patente,df,thr)
    if excluir != 0:
      dict_exclude[patente] = excluir
  return dict_exclude

def filtrar_patentes(df,thr):

  pat_exclude_dict = get_pat_dict(df,thr)
  patentes = df['Patente'].values.tolist()
  sec = df['Hora_sec'].values.tolist()
  hora = df['Hora'].values.tolist()

  patentes_filtradas = []
  hora_sec_filtrada = []
  hora_filtrada = []
  
  for i,pat in enumerate(patentes):

    if pat in pat_exclude_dict.keys():
      if sec[i] not in pat_exclude_dict[pat]:
        patentes_filtradas.append(pat)
        hora_sec_filtrada.append(sec[i])
        hora_filtrada.append(hora[i])
    else:
      patentes_filtradas.append(pat)
      hora_sec_filtrada.append(sec[i])
      hora_filtrada.append(hora[i])

  data = list(zip(patentes_filtradas,hora_filtrada,hora_sec_filtrada))
  df_filtrado = pd.DataFrame(data,columns = ["Patente","Hora","Hora_sec"])
  return df_filtrado

def get_OD_dict(O_df, D_df):
    pat_origen = O_df['Patente'].values.tolist()
    pat_destino = D_df['Patente'].values.tolist()

    O_dict = {}
    D_dict = {}
    for pat in pat_destino:
        if pat in pat_origen:
            t_origen = [O_df['Hora_sec'].values.tolist()[i] for i,pat_or in enumerate(pat_origen) if pat_or == pat]
            t_dest = [D_df['Hora_sec'].values.tolist()[i] for i,pat_dest in enumerate(pat_destino) if pat_dest == pat]

            O_dict[pat] = t_origen
            D_dict[pat] = t_dest
    
    return O_dict, D_dict

def get_ttravel_dict(O_dict,D_dict, t_thr):
    ttravel_dict = {}
    for key in D_dict.keys():
        if len(O_dict[key]) == len(D_dict[key]):
            if len(D_dict[key]) == 1:
                t = (D_dict[key][0] - O_dict[key][0])/60
                if t > 0 and t < t_thr:
                    ttravel_dict[D_dict[key][0]] = t
            else:
                for i, t_d in enumerate(D_dict[key]):
                    t = (t_d - O_dict[key][i])/60
                if t > 0 and t < t_thr:
                    ttravel_dict[t_d] = t
    return ttravel_dict
                    

def get_ttravel_df(D_df,ttravel_dict):
    hora_sec = list(ttravel_dict.keys())
    hora = [D_df['Hora'].values.tolist()[D_df['Hora_sec'].values.tolist().index(t_sec)] for t_sec in hora_sec]
    tiempo = []
    for key in ttravel_dict.keys():
        tiempo.append(ttravel_dict[key])
    
    data = list(zip(hora,hora_sec,tiempo))
    ttravel_df = pd.DataFrame(data, columns = ['Hora','Hora_sec','Tiempo de viaje'])
    ttravel_df = ttravel_df.sort_values(by = 'Hora_sec')
    return ttravel_df

def get_ticks(min_frac,max_time):
    if min_frac == 0:
        sec = []
        hora_str = []
        for a in range(0,25):
            sec.append(a*3600)
            hora_str.append(str(a)+":"+str(00))
    else:
        sec = []
        hora_str = []
        for a in range(0,25):
            for b in range(0,np.int(60/min_frac)):
                sec.append(a*3600+b*min_frac*60)
                hora_str.append(str(a)+":"+str(b*min_frac))
             
    t_viaje = []
    t_viaje_str = []
    for c in range(0,max_time):
        for d in range(0,2):
            t_viaje.append(c + d*30/60)
            t_viaje_str.append(str(c)+":"+str(d*30))

    return [sec,hora_str],[t_viaje,t_viaje_str]
    
    
def plot_ttravel(ttravel_df, xticks, yticks,  figsize, p_n = 30, save = False, filename = 'ttravel_plot.png'):
    avg_15 =[]
    t_aux = 900
    t_sec_15 = []
    window = []
    x = ttravel_df['Hora_sec'].values.tolist()
    y = ttravel_df['Tiempo de viaje'].values.tolist()
    for i,tsec in enumerate(x):
        if i == 0 and tsec > t_aux:
            t_sec_15.append(t_aux)
            avg_15.append(y[i])
            t_aux += tsec
        if (tsec <= (t_aux)) :
            window.append(y[i])
        else:
            avg = np.array(window).mean()
            avg_15.append(avg)
            t_aux +=900
            t_sec_15.append(t_aux)
            window = []
            window.append(y[i])
            
    f1,ax = plt.subplots(figsize = figsize)
    ax.scatter(x,y,s=50,color = 'black')
    #ax.scatter(x,y_avg,color = 'red',s=20)
    plt.xlabel('Hora del día',fontsize = 40)
    plt.ylabel('Tiempo de viaje (min)',fontsize = 40)
    plt.xticks(xticks[0])
    plt.yticks(yticks[0])
    ax.set_xticklabels(xticks[1], fontsize = 30)
    ax.set_yticklabels(yticks[1], fontsize = 30)

    ax2 = ax.twiny()
    legend = []
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', np.RankWarning)
        p = np.poly1d(np.polyfit(t_sec_15,avg_15, p_n))
    ax2.plot(t_sec_15,p(t_sec_15),c = 'r', linewidth = 5)

    ax2.set_xticklabels(xticks[1], fontsize = 10)
    ax2.set_yticklabels(yticks[1],fontsize = 30)
    ax.legend(['Tiempo de viaje'],loc=1, fontsize = 30)
    ax2.legend(['Promedio de tiempo de viaje cada 15 min.'], loc = 4, fontsize = 30)
    plt.title("Tiempo de viaje y tiempo de viaje promedio tomado cada 15 minutos", fontsize = 40)
    plt.show()
    
    if save:
        f1.savefig(filename)
    