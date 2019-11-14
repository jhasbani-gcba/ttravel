import os
import matplotlib.pyplot as plt
import pandas as pd
import calendar
import math
import numpy as np
import warnings


def get_ticks(min_frac, max_time):
    if min_frac == 0:
        sec = []
        hora_str = []
        for a in range(0, 25):
            sec.append(a * 3600)
            hora_str.append(str(a) + ":" + str(00))
    else:
        sec = []
        hora_str = []
        for a in range(0, 25):
            for b in range(0, np.int(60 / min_frac)):
                sec.append(a * 3600 + b * min_frac * 60)
                hora_str.append(str(a) + ":" + str(b * min_frac))

    t_viaje = []
    t_viaje_str = []
    for c in range(0, max_time):
        for d in range(0, 2):
            t_viaje.append(c + d * 30 / 60)
            t_viaje_str.append(str(c) + ":" + str(d * 30))

    return [sec, hora_str], [t_viaje, t_viaje_str]


def plot_ttravel(ttravel_df, xticks, yticks, figsize, p_n=30, save=False, filename='ttravel_plot.png'):
    avg_15 = []
    t_aux = 900
    t_sec_15 = []
    window = []
    x = ttravel_df['Hora_sec'].values.tolist()
    y = ttravel_df['Tiempo_viaje'].values.tolist()
    for i, tsec in enumerate(x):
        if i == 0 and tsec > t_aux:
            t_sec_15.append(t_aux)
            avg_15.append(y[i])
            t_aux += tsec
        if (tsec <= (t_aux)):
            window.append(y[i])
        else:
            avg = np.array(window).mean()
            avg_15.append(avg)
            t_aux += 900
            t_sec_15.append(t_aux)
            window = []
            window.append(y[i])

    f1, ax = plt.subplots(figsize=figsize)
    ax.scatter(x, y, s=50, color='black')
    # ax.scatter(x,y_avg,color = 'red',s=20)
    plt.xlabel('Hora del día', fontsize=40)
    plt.ylabel('Tiempo de viaje (min)', fontsize=40)
    plt.xticks(xticks[0])
    plt.yticks(yticks[0])
    ax.set_xticklabels(xticks[1], fontsize=30)
    ax.set_yticklabels(yticks[1], fontsize=30)

    ax2 = ax.twiny()
    legend = []
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', np.RankWarning)
        p = np.poly1d(np.polyfit(t_sec_15, avg_15, p_n))
    ax2.plot(t_sec_15, p(t_sec_15), c='r', linewidth=5)

    ax2.set_xticklabels(xticks[1], fontsize=10)
    ax2.set_yticklabels(yticks[1], fontsize=30)
    ax.legend(['Tiempo de viaje'], loc=1, fontsize=30)
    ax2.legend(['Promedio de tiempo de viaje cada 15 min.'], loc=4, fontsize=30)
    plt.title("Tiempo de viaje y tiempo de viaje promedio tomado cada 15 minutos", fontsize=40)
    plt.show()

    if save:
        f1.savefig(filename)