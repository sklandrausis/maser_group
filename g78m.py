import sys
import argparse

from matplotlib import cm
from matplotlib import rcParams
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from parsers.configparser_ import ConfigParser


def gauss(x, *p):
    a, b, c = p
    return a*np.exp(-(x-b)**2*np.log(2)/(c**2))


def gauss2(x, *p):
    a1, b1, c1, a2, b2, c2 = p
    return a1*np.exp(-(x-b1)**2*np.log(2)/c1**2) + \
           a2*np.exp(-(x-b2)**2*np.log(2)/c2**2)


def get_configs(section, key):
    """
    :param section: configuration file secti
    :param key: configuration file sections
    :return: configuration file section key
    """
    config_file_path = "config/config.cfg"
    config = ConfigParser(config_file_path)
    return config.get_config(section, key)


def get_configs_items():
    """
    :return: None
    """
    config_file_path = "config/plot.cfg"
    config = ConfigParser(config_file_path)
    return config.get_items("main")


def check_if_group_is_in_file(file, group):
    input_file = "groups/" + "/" + file
    group_nr = np.loadtxt(input_file, unpack=True, usecols=0)

    if group not in group_nr:
        return False
    else:
        return True


def main(group_numbers):
    configuration_items = get_configs_items()
    for key, value in configuration_items.items():
        rcParams[key] = value

    minor_locatorx = MultipleLocator(20)
    minor_locatory = MultipleLocator(20)
    minor_locatorvel = MultipleLocator(1)

    gauss2_list = get_configs("parameters", "gauss").split(";")
    gauss2_dict = dict()

    for epoch in gauss2_list:
        gauss2_dict[epoch.split(":")[0]] = epoch.split(":")[1].split(",")

    file_order = [file.strip() for file in get_configs("parameters", "fileOrder").split(",")]
    input_files = []

    for file in file_order:
        input_files.append(file)

    v_max = []
    v_min = []
    for index in range(0, len(input_files)):
        input_file = "groups/" + "/" + input_files[index].split(".")[0] + ".groups"
        group_tmp, channel_tmp, velocity_tmp, intensity_tmp, integral_intensity_tmp, ra_tmp, dec_tmp = np.loadtxt(
            input_file, unpack=True)

        v_max.append(max(velocity_tmp))
        v_min.append(min(velocity_tmp))

    dates = {file.split("-")[0].strip(): file.split("-")[1].strip() for file in
             get_configs("parameters", "dates").split(",")}

    bad_epoch_dict = {}
    for g in group_numbers:
        for file in input_files:
            if not check_if_group_is_in_file(file.split(".")[0] + ".groups", g):
                if file not in bad_epoch_dict.keys():
                    bad_epoch_dict[file] = 1
                else:
                    bad_epoch_dict[file] = +1

    for file in bad_epoch_dict.keys():
        if bad_epoch_dict[file] == len(group_numbers):
            input_files.remove(file)
            del dates[file.split(".")[0]]

    fig, ax = plt.subplots(nrows=2, ncols=len(input_files), figsize=(16, 16), dpi=90)

    data_dict = dict()
    ra_max = []
    ra_min = []
    dec_max = []
    dec_min = []
    intensitys_max = []
    intensitys_min = []
    for index in range(0, len(input_files)):
        input_file = "groups/" + "/" + input_files[index].split(".")[0] + ".groups"

        group_tmp, channel_tmp, velocity_tmp, intensity_tmp, integral_intensity_tmp, ra_tmp, dec_tmp = np.loadtxt(
            input_file, unpack=True)
        for j in group_numbers:
            velocity = np.empty(0)
            intensity = np.empty(0)
            ra = np.empty(0)
            dec = np.empty(0)
            if j not in data_dict.keys():
                velocitys = []
                intensitys = []
                ras = []
                decs = []
                data_dict[j] = [velocitys, intensitys, ras, decs]

            for i in range(0, len(channel_tmp)):
                if group_tmp[i] == int(j):
                    velocity = np.append(velocity, velocity_tmp[i])
                    intensity = np.append(intensity, intensity_tmp[i])
                    intensitys_max.append(max(intensity))
                    intensitys_min.append(min(intensity))
                    ra = np.append(ra, ra_tmp[i])
                    dec = np.append(dec, dec_tmp[i])

            data_dict[j][0].append(velocity)
            data_dict[j][1].append(intensity)
            data_dict[j][2].append(ra)
            data_dict[j][3].append(dec)
            if len(ra) != 0:
                ra_max.append(np.max(ra))
                ra_min.append(np.min(ra))
                dec_max.append(np.max(dec))
                dec_min.append(np.min(dec))

    coord_range = max(max(ra_max) - min(ra_min), max(dec_max) - min(dec_min))
    symbols = ["o", "*", "v", "^", "<", ">", "1", "2", "3", "4"]
    for index in range(0, len(input_files)):
        for j in group_numbers:
            symbol = symbols[group_numbers.index(j)]
            velocity = data_dict[j][0][index]
            intensity = data_dict[j][1][index]
            ra = data_dict[j][2][index]
            dec = data_dict[j][3][index]

            if len(velocity) >= 3:
                p1 = [max(intensity), min(velocity) + 0.5 * (max(velocity) - min(velocity)), 0.2]
                p2 = [max(intensity), min(velocity) + 0.5 * (max(velocity) - min(velocity)), 0.3,
                      max(intensity) / 4, min(velocity) + 0.5 * (max(velocity) - min(velocity)), 0.1]
                q = np.linspace(min(velocity), max(velocity), 1000)

                gauss2_groups_for_epoch = gauss2_dict[input_files[index].split(".")[0].upper()]
                if str(j) in gauss2_groups_for_epoch:
                    try:
                        coeff, var_matrix = curve_fit(gauss2, velocity, intensity, p0=p2, maxfev=100000)
                        hist_fit = gauss2(q, *coeff)
                        ax[0][index].plot(q, hist_fit, 'k')
                    except:
                        pass
                else:
                    try:
                        coeff, var_matrix = curve_fit(gauss, velocity, intensity, p0=p1, maxfev=100000)
                        hist_fit = gauss(q, *coeff)
                        ax[0][index].plot(q, hist_fit, 'k')
                    except:
                        pass

            for i in range(len(velocity) - 1):
                if velocity[i] < min(v_min) or velocity[i] > max(v_max):
                    c = (0, 0, 0)
                else:
                    c = cm.jet((velocity[i] - min(v_min)) / (max(v_max) - min(v_min)), 1)

                ax[0][index].scatter((velocity[i], velocity[i + 1]), (intensity[i], intensity[i + 1]),
                                     color=c, lw=2, marker=symbol)
                ax[1][index].scatter(ra[i], dec[i], s=0.05 * coord_range * np.sqrt(intensity[i]),
                                     color=c, lw=2, marker=symbol)

        title = input_files[index].split(".")[0].upper() + "-" + dates[input_files[index].split(".")[0]]
        ax[0][index].xaxis.set_minor_locator(minor_locatorvel)
        ax[0][index].set_title(title)
        ax[0][index].set_xlabel('$V_{\\rm LSR}$ (km s$^{-1}$)')
        ax[1][index].set_aspect("equal", adjustable='box')
        ax[1][index].set_xlabel('$\\Delta$ RA (mas)')
        ax[1][index].xaxis.set_minor_locator(minor_locatorx)
        ax[1][index].yaxis.set_minor_locator(minor_locatory)
        ax[0][index].set_xlim(min(v_min) - 0.5, max(v_max) + 0.5)
        ax[0][index].set_ylim((min(intensitys_min)) - 0.1, (max(intensitys_max) + 0.1))
        centre = (np.mean([max(ra_max), min(ra_min)]), np.mean([max(dec_max), min(dec_min)]))
        ax[1][index].set_xlim(centre[0] - coord_range/2 - 10, centre[0] + coord_range/2 + 10)
        ax[1][index].set_ylim(centre[1] - coord_range/2 - 10, centre[1] + coord_range/2 + 10)
        ax[1][index].invert_xaxis()

    ax[0][0].set_ylabel('Flux density (Jy)')
    ax[1][0].set_ylabel('$\\Delta$ Dec (mas)')
    plt.tight_layout()
    plt.subplots_adjust(top=0.97, bottom=0, wspace=0.15, hspace=0, left=0.04, right=0.99)
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='plot group')
    parser.add_argument('group_numbers', type=int, help='group numbers',  nargs='+',)
    args = parser.parse_args()
    main(args.group_numbers)
    sys.exit(0)