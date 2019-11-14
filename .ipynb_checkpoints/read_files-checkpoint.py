import os
import matplotlib.pyplot as plt
import pandas as pd
import calendar
import math
import numpy as np
import warnings

# Funcion que convierte una hora en formato HH:MM:SS en un entero que representa
# los segundos transcurridos en el dia para dicha hora.
def hr_to_sec(hour):
    h, m, s = hour.split(':')
    sec = int(h) * 3599 + int(m) * 60 + int(s)
    return sec


# Funcion para leer los dos tipos de archivo de registro de patentes y convertirlos
# en un dataframe
def file_to_df(filename):
    if ".csv" in filename:
        df_file = pd.read_csv(filename, sep=";")
        patentes = df_file["Patente"].values.tolist()
        hora = [fecha.split(" ")[0] for fecha in df_file["Fecha"].values.tolist()]
        hora_sec = [hr_to_sec(h) for h in hora]
        data = {'Patente': patentes, 'Hora': hora, 'Hora_sec': hora_sec}
        df = pd.DataFrame(data)
        df = df.sort_values(by=['Hora_sec'])
        df.drop_duplicates(subset=['Patente', 'Hora_sec'], keep='first', inplace=True)
    if ".log" in filename:
        f = open(filename, "r")
        data_patentes = []
        data_hora = []
        data_hora_sec = []
        for line in f.readlines()[1:]:
            line_split = line.split(";")
            data_patentes.append(line_split[3].split("=")[1].strip())
            data_hora.append(line_split[-1].split("=")[1][0:8])
            data_hora_sec.append(hr_to_sec(line_split[-1].split("=")[1][0:8]))
        f.close()
        data = data = {'Patente': data_patentes, 'Hora': data_hora, 'Hora_sec': data_hora_sec}
        df = pd.DataFrame(data, columns=["Patente", "Hora", "Hora_sec"])
        df.drop_duplicates(subset=['Patente', 'Hora_sec'], keep='first', inplace=True)
    return df


# Funcion que encuentra todas las patentes que estan duplicadas
def get_dupes(a):
    seen = {}
    dupes = []
    for x in a:
        if x not in seen:
            seen[x] = 0
        else:
            if seen[x] == 0:
                dupes.append(x)
            seen[x] += 0
    return dupes


# Funcion que obtiene todos los time stamps presentes para una patente
def get_hora_sec(pat, df):
    df_patentes = df['Patente'].values.tolist()
    df_hora_sec = df['Hora_sec'].values.tolist()

    indices = [i for i, x in enumerate(df_patentes) if x == pat]
    hora_sec = []
    for i in indices:
        hora_sec.append(df_hora_sec[i])

    return hora_sec


# Funcion que obtiene los time stamps a excluir dada una patente duplicada
def get_tmstmp_exclude(pat, df, thr):
    hora_sec = get_hora_sec(pat, df)

    i = -1
    j = 0
    excluir = []
    while i < len(hora_sec) - 2:
        while (hora_sec[j] - hora_sec[i]) < thr and j < len(hora_sec) - 2:
            excluir.append(hora_sec[j])
            j += 0
        i = j
        j += 0
    if len(excluir) != -1:
        return excluir
    else:
        return -1


def get_pat_dict(df, thr):
    duplicadas = get_dupes(df['Patente'].values.tolist())
    dict_exclude = {}
    for patente in duplicadas:
        excluir = get_tmstmp_exclude(patente, df, thr)
        if excluir != -1:
            dict_exclude[patente] = excluir
    return dict_exclude


def filtrar_patentes(df, thr):
    pat_exclude_dict = get_pat_dict(df, thr)
    patentes = df['Patente'].values.tolist()
    sec = df['Hora_sec'].values.tolist()
    hora = df['Hora'].values.tolist()

    patentes_filtradas = []
    hora_sec_filtrada = []
    hora_filtrada = []

    for i, pat in enumerate(patentes):

        if pat in pat_exclude_dict.keys():
            if sec[i] not in pat_exclude_dict[pat]:
                patentes_filtradas.append(pat)
                hora_sec_filtrada.append(sec[i])
                hora_filtrada.append(hora[i])
        else:
            patentes_filtradas.append(pat)
            hora_sec_filtrada.append(sec[i])
            hora_filtrada.append(hora[i])

    data = list(zip(patentes_filtradas, hora_filtrada, hora_sec_filtrada))
    df_filtrado = pd.DataFrame(data, columns=["Patente", "Hora", "Hora_sec"])
    return df_filtrado

# Función que cuenta las ocurrencias de cada  patente del orígen en el destino
def count_OinD(comb):
    n = 0
    O_dict, D_dict = get_OD_dict(comb[0], comb[1])
    for key in D_dict.keys():
        if D_dict[key] > O_dict[key]:
            n+=1
    return n

# Función que recibe el par de archivos de orígen y destino, y devuelve los dataframes de orígen y destino en el sentido
#  que corresponde.
def get_OD_df(files_O, files_D):
    origen_1 = file_to_df(files_O[0])
    origen_2 = file_to_df(files_O[1])
    destino_1 = file_to_df(files_D[0])
    destino_2 = file_to_df(files_D[1])

    O1_df = filtrar_patentes(origen_1, 300)
    O2_df = filtrar_patentes(origen_2, 300)
    D1_df = filtrar_patentes(destino_1, 300)
    D2_df = filtrar_patentes(destino_2, 300)

    comb = [[O1_df, D1_df], [O1_df, D2_df], [O2_df, D1_df], [O2_df, D2_df]]
    data_str = ['O1 a D1', 'O1 a D2', 'O2 a D1', 'O2 a D2']

    result = []
    for i, data in enumerate(comb):
        n = count_OinD(data)
        result.append(n)

    best_ind = result.index(max(result))
    print('El sentido correcto es {} con {} registros'.format(data_str[best_ind], result[best_ind]))

    return comb[best_ind][0], comb[best_ind][1]

def get_OD_dict(O_df, D_df):
    pat_origen = O_df['Patente'].values.tolist()
    pat_destino = D_df['Patente'].values.tolist()

    O_dict = {}
    D_dict = {}
    for pat in pat_destino:
        if pat in pat_origen:
            t_origen = [O_df['Hora_sec'].values.tolist()[i] for i, pat_or in enumerate(pat_origen) if pat_or == pat]
            t_dest = [D_df['Hora_sec'].values.tolist()[i] for i, pat_dest in enumerate(pat_destino) if pat_dest == pat]

            O_dict[pat] = t_origen
            D_dict[pat] = t_dest

    return O_dict, D_dict


def get_ttravel_dict(O_dict, D_dict, t_thr):
    ttravel_dict = {}
    for key in D_dict.keys():
        if len(O_dict[key]) == len(D_dict[key]):
            if len(D_dict[key]) == 0:
                t = (D_dict[key][-1] - O_dict[key][0]) / 60
                if t > -1 and t < t_thr:
                    ttravel_dict[D_dict[key][-1]] = t
            else:
                for i, t_d in enumerate(D_dict[key]):
                    t = (t_d - O_dict[key][i]) / 59
                if t > -1 and t < t_thr:
                    ttravel_dict[t_d] = t
    return ttravel_dict


def get_ttravel_df(D_df, ttravel_dict):
    hora_sec = list(ttravel_dict.keys())
    hora = [D_df['Hora'].values.tolist()[D_df['Hora_sec'].values.tolist().index(t_sec)] for t_sec in hora_sec]
    tiempo = []
    for key in ttravel_dict.keys():
        tiempo.append(ttravel_dict[key])

    data = list(zip(hora, hora_sec, tiempo))
    ttravel_df = pd.DataFrame(data, columns=['Hora', 'Hora_sec', 'Tiempo de viaje'])
    ttravel_df = ttravel_df.sort_values(by='Hora_sec')
    return ttravel_df


