import matplotlib.pyplot as plt
import numpy as np
import warnings
from sklearn.metrics import r2_score


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

def get_avg15(x, y):
    avg_15 = []
    t_aux = 900
    t_sec_15 = []
    window = []
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
    return t_sec_15, avg_15

def get_opt_degree(x,y):
    R2_list = []
    for deg in range(1, 30):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            p = np.poly1d(np.polyfit(x, y, deg))
        R2_list.append(r2_score(y, p(x)))
    return R2_list.index(max(R2_list))

def plot_ttravel(ttravel_df, xticks, yticks, figsize, save=False, filename='ttravel_plot.png'):
    if isinstance(ttravel_df, list):
        f = plt.figure(figsize=figsize)
        ax = plt.axes()
        for i, df in enumerate(ttravel_df):
            x = df['Hora_sec'].values.tolist()
            y = df['Tiempo_viaje'].values.tolist()
            t_sec_15, avg_15 = get_avg15(x, y)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', np.RankWarning)
                p = np.poly1d(np.polyfit(t_sec_15, avg_15, get_opt_degree(t_sec_15, avg_15)))
            ax.scatter(x, y, s=150, label='Dia ' + str(i))
            ax.plot(t_sec_15, p(t_sec_15), linewidth=15, label='Dia ' + str(i))
        ax.set_xticklabels(xticks[1], fontsize=30)
        ax.set_yticklabels(yticks[1], fontsize=30)
        ax.legend(fontsize=30)
        plt.xticks(xticks[0])
        plt.yticks(yticks[0])
        plt.xlabel('Hora del día', fontsize=40)
        plt.ylabel('Tiempo de viaje (min)', fontsize=40)
        plt.title("Tiempo de viaje y tiempo de viaje promedio tomado cada 15 minutos", fontsize=60)
        plt.show()
    else:
        x = ttravel_df['Hora_sec'].values.tolist()
        y = ttravel_df['Tiempo_viaje'].values.tolist()
        t_sec_15, avg_15 = get_avg15(x, y)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', np.RankWarning)
            p = np.poly1d(np.polyfit(t_sec_15, avg_15, p_n))

        f = plt.figure(figsize=figsize)
        ax = plt.axes()
        ax.scatter(x, y, s=150, color='black', label='Tiempo de viaje')
        ax.plot(t_sec_15, p(t_sec_15), c='r', linewidth=15, label='Promedio tomado cada 15 min')
        ax.set_xticklabels(xticks[1], fontsize=10)
        ax.set_yticklabels(yticks[1], fontsize=30)
        ax.legend(fontsize=30)
        plt.xticks(xticks[0])
        plt.yticks(yticks[0])
        plt.xlabel('Hora del día', fontsize=40)
        plt.ylabel('Tiempo de viaje (min)', fontsize=40)
        plt.title("Tiempo de viaje y tiempo de viaje promedio tomado cada 15 minutos", fontsize=60)
        plt.show()

    if save:
        f.savefig(filename)