import os
import matplotlib.pyplot as plt
import pandas as pd
import calendar
import math
import numpy as np
import warnings


def hr_to_sec(hour):
    """
    Función que convierte una hora en formato HH:MM:SS en un entero que representa
    los segundos transcurridos en el dia para dicha hora.
    :param hour:
    :return sec: - hora en segundos
    """
    h, m, s = hour.split(':')
    sec = int(h) * 3600 + int(m) * 60 + int(s)
    return sec

def file_to_df(filename):
    """
    Funcion para leer los archivos de la policia (.csv) o de las LPR propias (.log) de registro de patentes y convertirlos en un dataframe
    :param filename: - path al archivo
    :return df: - data frame de pandas con los campos ["Patente", "Hora", "Hora_sec"]
    """

    if ".csv" in filename:
        df_file = pd.read_csv(filename, sep=";")
        patentes = df_file["Patente"].values.tolist()
        hora = [fecha.split(" ")[1] for fecha in df_file["Fecha"].values.tolist()]
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
        for line in f.readlines()[2:]:
            line_split = line.split(";")
            data_patentes.append(line_split[4].split("=")[1].strip())
            data_hora.append(line_split[0].split("=")[1][0:8])
            data_hora_sec.append(hr_to_sec(line_split[1].split("=")[1][0:8]))
        f.close()
        data = data = {'Patente': data_patentes, 'Hora': data_hora, 'Hora_sec': data_hora_sec}
        df = pd.DataFrame(data, columns=["Patente", "Hora", "Hora_sec"])
        df.drop_duplicates(subset=['Patente', 'Hora_sec'], keep='first', inplace=True)
    return df


def get_dupes(patentes):
    """
    Funcion que encuentra todas las patentes que estan duplicadas
    :param patentes:
    :return dupes : - patentes duplicadas
    """
    seen = {}
    dupes = []
    for x in patentes:
        if x not in seen:
            seen[x] = 0
        else:
            if seen[x] == 0:
                dupes.append(x)
            seen[x] += 0
    return dupes

def get_hora_sec(pat, df):
    """
    Funcion que obtiene todos los time stamps presentes para una patente en segundos.
    :param pat:
    :param df: - pandas dataframe
    :return hora_sec: - time stamps
    """
    df_patentes = df['Patente'].values.tolist()
    df_hora_sec = df['Hora_sec'].values.tolist()

    indices = [i for i, x in enumerate(df_patentes) if x == pat]
    hora_sec = []
    for i in indices:
        hora_sec.append(df_hora_sec[i])

    return hora_sec

def get_tmstmp_exclude(pat, df, thr):
    """
    Funcion que obtiene los time stamps a excluir dada una patente duplicada
    :param pat:
    :param df: - pandas dataframe
    :param thr: - umbral en segundos para excluir patentes iguales
    :return excluir:  - time stamps a excluir
    """
    hora_sec = get_hora_sec(pat, df)
    i = 0
    j = 0
    excluir = []
    while i < len(hora_sec) - 1:
        while (hora_sec[j] - hora_sec[i]) < thr and j < len(hora_sec) - 1:
            excluir.append(hora_sec[j])
            j += 1
        i = j
        j += 1
    if len(excluir) != 0:
        return excluir
    else:
        return 0

def get_pat_dict(df, thr):
    """
    Funcion que obtiene las patentes a excluir
    :param df: - pandas dataframe
    :param thr: - umbral en segundos para excluir patentes iguales
    :return:
    """
    duplicadas = get_dupes(df['Patente'].values.tolist())
    dict_exclude = {}
    for patente in duplicadas:
        excluir = get_tmstmp_exclude(patente, df, thr)
        if excluir != 0:
            dict_exclude[patente] = excluir
    return dict_exclude

def filtrar_patentes(df, thr):
    """
    Funcion que realiza las operaciones de filtrado a los datos de captura de un dia
    :param df: - pandas dataframe
    :param thr:  - umbral en segundos para excluir patentes iguales
    :return:
    """
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

#
def count_OinD(comb):
    """
    Función que cuenta las ocurrencias de cada  patente del orígen en el destino
    :param comb:  - combinacion de dos archivos
    :return n: - numero de ocurrencias
    """
    n = 0
    O_dict, D_dict = get_OD_dict(comb[0], comb[1])
    for key in D_dict.keys():
        if D_dict[key] > O_dict[key]:
            n += 1
    return n


def get_OD_df(files_O, files_D, verbose = False):
    """
    Función que recibe el par de archivos de orígen y destino, y devuelve los dataframes de orígen y destino en el
    sentido que corresponde.
    :param files_O: - par de archivos del origen
    :param files_D: - par de archivos del destino
    :param verbose: - default False - opcion de que se imprima la combinacion correcta con el numero de ocurrencias
    :return O_df, D_df:
    """
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
    if verbose:
        print('El sentido correcto es {} con {} registros'.format(data_str[best_ind], result[best_ind]))

    return comb[best_ind][0], comb[best_ind][1]

def get_OD_dict(O_df, D_df):
    """
    Funcion que obtiene los diccionarios a partir de los dataframes de origen y destino.
    :param O_df: - pandas dataframe del origen
    :param D_df: -pandas dataframe del destino
    :return O_dict, D_dict: - diccionarios para el origen y destino con key = Patente y value = tiempo de captura
    """
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
    """
    Funcion que devuelve el diccionario de tiempo de viaje según tiempo de captura en destino.
    :param O_dict: - diccionario del origen
    :param D_dict: - diccionario del destino
    :param t_thr: - umbral de tiempo de viaje a partir del cual incluir valores
    :return ttravel_dict: - diccionario que tiene key = tiempo de captura en destino y value = tiempo de viaje
    """
    ttravel_dict = {}
    for key in D_dict.keys():
        if len(O_dict[key]) == len(D_dict[key]):
            if len(D_dict[key]) == 0:
                t = (D_dict[key][0] - O_dict[key][0]) / 60
                if t > 0 and t < t_thr:
                    ttravel_dict[D_dict[key][-1]] = t
            else:
                for i, t_d in enumerate(D_dict[key]):
                    t = (t_d - O_dict[key][i]) / 60
                if t > 0 and t < t_thr:
                    ttravel_dict[t_d] = t
    return ttravel_dict


def get_ttravel_df(D_df, ttravel_dict):
    """
    Funcion que devuelve un pandas dataframe de tiempos de viaje con los campos ['Patente','Hora', 'Hora_sec', 'Tiempo_viaje']
    :param D_df: - pandas dataframe del destino
    :param ttravel_dict: - diccionario de tiempos de viaje
    :return:
    """
    hora_sec = list(ttravel_dict.keys())
    hora = [D_df['Hora'].values.tolist()[D_df['Hora_sec'].values.tolist().index(t_sec)] for t_sec in hora_sec]
    patente = [D_df['Patente'].values.tolist()[D_df['Hora_sec'].values.tolist().index(t_sec)] for t_sec in hora_sec]
    tiempo = []
    for key in ttravel_dict.keys():
        tiempo.append(ttravel_dict[key])

    data = list(zip(patente,hora, hora_sec, tiempo))
    ttravel_df = pd.DataFrame(data, columns=['Patente','Hora', 'Hora_sec', 'Tiempo_viaje'])
    ttravel_df = ttravel_df.sort_values(by='Hora_sec')
    return ttravel_df


