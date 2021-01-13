import sys
import argparse

from matplotlib import cm
from matplotlib import rcParams
from matplotlib.patches import Circle
from matplotlib.ticker import MultipleLocator
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from parsers.configparser_ import ConfigParser


def gauss(x, *p):
    a, b, c = p
    return a*np.exp(-(x-b)**2*np.log(2)/(c**2))


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


def main(group_number):
    configuration_items = get_configs_items()
    for key, value in configuration_items.items():
        rcParams[key] = value

    minorLocatorx = MultipleLocator(20)
    minorLocatory = MultipleLocator(20)
    minorLocatorvel = MultipleLocator(1)

    file_order = [file.strip() for file in get_configs("parameters", "fileOrder").split(",")]
    input_files = []

    for file in file_order:
        input_files.append(file)

    dates = {file.split("-")[0].strip(): file.split("-")[1].strip() for file in
             get_configs("parameters", "dates").split(",")}

    fig, ax = plt.subplots(nrows=2, ncols=len(input_files), figsize=(16, 16))

    coord_ranges = []
    velocitys = []
    vms = []
    vxs = []
    dvs = []
    intensitys = []
    ras = []
    decs = []
    avgs_ra = []
    avgs_dec = []
    max_ra = []
    min_ra = []
    min_dec = []
    max_dec = []
    intensitys_max = []
    intensitys_min = []
    for index in range(0, len(input_files)):
        input_file = "groups/" + "/" + input_files[index].split(".")[0] + ".groups"
        velocity = np.empty(0)
        intensity = np.empty(0)
        ra = np.empty(0)
        dec = np.empty(0)
        group_tmp, channel_tmp, velocity_tmp, intensity_tmp, integral_intensity_tmp, ra_tmp, dec_tmp = np.loadtxt(
            input_file, unpack=True)
        for i in range(0, len(channel_tmp)):
            if group_tmp[i] == int(group_number):
                velocity = np.append(velocity, velocity_tmp[i])
                intensity = np.append(intensity, intensity_tmp[i])
                ra = np.append(ra, ra_tmp[i])
                dec = np.append(dec, dec_tmp[i])

        dv = (max(velocity) - min(velocity))
        vm = min(velocity)
        vx = max(velocity)

        coord_range = max(abs(abs(max(ra)) - abs(min(ra))), abs(abs(max(dec)) - abs(min(dec))))
        coord_ranges.append(coord_range)
        velocitys.append(velocity)
        vms.append(vm)
        vxs.append(vx)
        dvs.append(dv)
        intensitys.append(intensity)
        intensitys_max.append(max(intensity))
        intensitys_min.append(min(intensity))
        ras.append(ra)
        decs.append(dec)

        avgs_ra.append(np.mean(ra))
        avgs_dec.append(np.mean(dec))
        max_ra.append(np.max(ra))
        min_ra.append(np.min(ra))
        min_dec.append(np.min(dec))
        max_dec.append(np.max(dec))

    for index in range(0, len(input_files)):
        velocity = velocitys[index]
        vm = vms[index]
        vx = vxs[index]
        dv = dvs[index]
        intensity = intensitys[index]
        dec = decs[index]
        ra = ras[index]
        title = input_files[index].split(".")[0].upper() + "-" + dates[input_files[index].split(".")[0]]
        ax[0][0].set_ylabel('Flux density (Jy)')
        p0 = [max(intensity), min(velocity) + 0.5 * (max(velocity) - min(velocity)), 0.2]
        coeff, var_matrix = curve_fit(gauss, velocity, intensity, p0=p0, maxfev=100000)
        q = np.linspace(min(velocity), max(velocity), 1000)
        hist_fit = gauss(q, *coeff)
        ax[0][index].plot(q, hist_fit, 'k')

        for i in range(len(velocity) - 1):
            if velocity[i] < vm or velocity[i] > vx:
                c = (0, 0, 0)
            else:
                c = cm.jet((velocity[i] - vm) / dv, 1)

            ax[0][index].scatter((velocity[i], velocity[i + 1]), (intensity[i], intensity[i + 1]), color=c, lw=2)
            ax[0][index].set_xlim(min(velocity) - 0.5, max(velocity) + 0.5)
            ax[0][index].xaxis.set_minor_locator(minorLocatorvel)
            ax[0][index].set_title(title)
            ax[0][index].set_xlabel('$V_{\\rm LSR}$ (km s$^{-1}$)')

            rel = []
            ax[1][0].set_ylabel('$\\Delta$ Dec (mas)')
            for i in range(0, len(ra)):
                el = Circle((ra[i], dec[i]), radius=0.1 * np.sqrt(intensity[i]), angle=0, lw=2)
                ax[1][index].add_artist(el)
                c = cm.jet((velocity[i] - vm) / dv, 1)
                el.set_facecolor(c)
                rel.append([ra[i], dec[i], velocity[i]])

            coord_range = max(max(max_ra) - min(min_ra), max(max_dec) - min(min_dec))
            ax[0][index].set_ylim((min(intensitys_min)) - 0.1, (max(intensitys_max) + 0.1))
            ax[1][index].set_aspect("equal", adjustable='box')
            ax[1][index].set_xlim(np.mean((max(max_ra), min(min_ra))) - (coord_range/2) - 0.5, np.mean((max(max_ra), min(min_ra))) + (coord_range/2) + 0.5)
            ax[1][index].set_ylim(np.mean((max(max_dec), min(min_dec))) - (coord_range/2) - 0.5, np.mean((max(max_dec), min(min_dec))) + (coord_range/2) + 0.5)
            ax[1][index].set_xlabel('$\\Delta$ RA (mas)')
            ax[1][index].xaxis.set_minor_locator(minorLocatorx)
            ax[1][index].yaxis.set_minor_locator(minorLocatory)
            ax[1][index].invert_xaxis()

    plt.tight_layout()
    plt.subplots_adjust(top=0.97, bottom=0, wspace=0.18, hspace=0, left=0.05, right=0.99)
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='plot group')
    parser.add_argument('group_number', type=int, help='group number')
    args = parser.parse_args()
    main(args.group_number)
    sys.exit(0)
