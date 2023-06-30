import copy
from itertools import product

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib import colors
from scipy.optimize import curve_fit
from scipy.signal import find_peaks

from pyccapt.calibration.calibration_tools import variables


def voltage_corr(x, a, b, c):
    """
    Returns the voltage correction value for a given x using a quadratic equation.

    Parameters:
    - x (float): The input value.
    - a (float): Coefficient of x^0.
    - b (float): Coefficient of x^1.
    - c (float): Coefficient of x^2.

    Returns:
    - float: The voltage correction value.

    """
    return a + b * x + c * x ** 2


def calculate_dld_t_peak(dld_t_peak_selected, maximum_location, peak_mode):
    """
    Calculates the dld_t_peak value based on the given peak_mode.

    Parameters:
    - dld_t_peak_selected (array): Array of dld_t_peak values.
    - maximum_location (float): Maximum location value.
    - peak_mode (string): Type of peak mode (peak/mean/median).

    Returns:
    - float: The calculated dld_t_peak value.

    """
    if peak_mode == 'peak':
        try:
            peaks, properties = find_peaks(dld_t_peak_selected, height=0)
            index_peak_max_ini = np.argmax(properties['peak_heights'])
            max_peak = peaks[index_peak_max_ini]
            return dld_t_peak_selected[max_peak] / maximum_location
        except:
            print('Cannot find the maximum')
            return np.median(dld_t_peak_selected) / maximum_location
    elif peak_mode == 'mean':
        return np.mean(dld_t_peak_selected) / maximum_location
    elif peak_mode == 'median':
        return np.median(dld_t_peak_selected) / maximum_location


def voltage_correction(dld_highVoltage_peak, dld_t_peak, maximum_location, index_fig, figname, sample_size, mode,
                       calibration_mode, peak_mode, plot=True, save=False, fig_size=(7, 5)):
    """
    Performs voltage correction and plots the graph based on the passed arguments.

    Parameters:
    - dld_highVoltage_peak (array): Array of high voltage peaks.
    - dld_t_peak (array): Array of t peaks.
    - maximum_location (float): Maximum location value.
    - index_fig (string): Index of the saved plot.
    - figname (string): Name of the saved plot image.
    - sample_size (string): Sample size.
    - mode (string): Mode ('ion_seq'/'voltage').
    - calibration_mode (string): Type of calibration mode (tof/mc).
    - peak_mode (string): Type of peak mode (peak/mean/median).
    - plot (bool): Indicates whether to plot the graph. Default is True.
    - save (bool): Indicates whether to save the plot. Default is False.
    - fig_size (tuple): Figure size in inches. Default is (7, 5).

    Returns:
    - fitresult (array): Corrected voltage array.

    """

    high_voltage_mean_list = []
    dld_t_peak_list = []

    if mode == 'ion_seq':
        for i in range(int(len(dld_highVoltage_peak) / sample_size) + 1):
            dld_highVoltage_peak_selected = dld_highVoltage_peak[i * sample_size:(i + 1) * sample_size]
            dld_t_peak_selected = dld_t_peak[i * sample_size:(i + 1) * sample_size]

            high_voltage_mean = np.mean(dld_highVoltage_peak_selected)
            high_voltage_mean_list.append(high_voltage_mean)

            bins = np.linspace(np.min(dld_t_peak_selected), np.max(dld_t_peak_selected),
                               round(np.max(dld_t_peak_selected) / 0.1))
            y, x = np.histogram(dld_t_peak_selected, bins=bins)
            dld_t_peak_list.append(calculate_dld_t_peak(y, x, maximum_location, peak_mode))

    elif mode == 'voltage':
        for i in range(int((np.max(dld_highVoltage_peak) - np.min(dld_highVoltage_peak)) / sample_size) + 1):
            mask = np.logical_and((dld_highVoltage_peak >= (np.min(dld_highVoltage_peak) + (i) * sample_size)),
                                  (dld_highVoltage_peak < (np.min(dld_highVoltage_peak) + (i + 1) * sample_size)))
            dld_highVoltage_peak_selected = dld_highVoltage_peak[mask]
            dld_t_peak_selected = dld_t_peak[mask]

            high_voltage_mean = np.mean(dld_highVoltage_peak_selected)
            high_voltage_mean_list.append(high_voltage_mean)

            bins = np.linspace(np.min(dld_t_peak_selected), np.max(dld_t_peak_selected),
                               round(np.max(dld_t_peak_selected) / 0.1))
            y, x = np.histogram(dld_t_peak_selected, bins=bins)
            dld_t_peak_list.append(calculate_dld_t_peak(y, x, maximum_location, peak_mode))

    fitresult, _ = curve_fit(voltage_corr, np.array(high_voltage_mean_list), np.array(dld_t_peak_list))

    if plot:
        fig1, ax1 = plt.subplots(figsize=fig_size, constrained_layout=True)
        if calibration_mode == 'tof':
            ax1.set_ylabel("Time of Flight (ns)", fontsize=8)
            label = 't'
        elif calibration_mode == 'mc':
            ax1.set_ylabel("mc (Da)", fontsize=8)
            label = 'mc'

        x = plt.scatter(np.array(high_voltage_mean_list) / 1000, np.array(dld_t_peak_list) * maximum_location,
                        color="blue", label=label, s=1)
        ax1.set_xlabel("Voltage (kV)", fontsize=8)
        plt.grid(color='aqua', alpha=0.3, linestyle='-.', linewidth=0.4)

        ax2 = ax1.twinx()
        f_v = voltage_corr(np.array(high_voltage_mean_list), *fitresult)
        y = ax2.plot(np.array(high_voltage_mean_list) / 1000, f_v, color='r', label=r"$C_V$", linewidth=0.5)
        ax2.set_ylabel(r"$C_V$", color="red", fontsize=8)
        plt.legend(handles=[x, y[0]], loc='lower left', prop={'size': 6})

        if save:
            plt.savefig(variables.result_path + "//vol_corr_%s_%s.svg" % (figname, index_fig), format="svg", dpi=600)
            plt.savefig(variables.result_path + "//vol_corr_%s_%s.png" % (figname, index_fig), format="png", dpi=600)

        plt.show()

    return fitresult


def voltage_corr_main(dld_highVoltage, sample_size, mode, calibration_mode, peak_mode, index_fig, plot, save,
                      maximum_cal_method='histogram', fig_size=(5, 5)):
    """
    Perform voltage correction on the given data.

    Args:
        dld_highVoltage (numpy.ndarray): Array of high voltages.
        sample_size (int): Size of the sample.
        mode (str): Mode of the correction.
        calibration_mode (str): Calibration mode ('tof' or 'mc').
        peak_mode (str): Peak mode.
        index_fig (int): Index of the figure.
        plot (bool): Whether to plot the results.
        save (bool): Whether to save the plots.
        maximum_cal_method (str, optional): Maximum calculation method ('histogram' or 'mean').
            Defaults to 'histogram'.
        fig_size (tuple, optional): Size of the figure. Defaults to (5, 5).
    """

    if calibration_mode == 'tof':
        mask_temporal = np.logical_and(
            (variables.dld_t_calib > variables.selected_x1),
            (variables.dld_t_calib < variables.selected_x2)
        )
        dld_peak_b = variables.dld_t_calib[mask_temporal]

        if maximum_cal_method == 'histogram':
            bins = np.linspace(np.min(dld_peak_b), np.max(dld_peak_b), round(np.max(dld_peak_b) / 0.1))
            y, x = np.histogram(dld_peak_b, bins=bins)
            peaks, properties = find_peaks(y, height=0)
            index_peak_max_ini = np.argmax(properties['peak_heights'])
            max_peak = peaks[index_peak_max_ini]
            maximum_location = x[max_peak]
        elif maximum_cal_method == 'mean':
            maximum_location = np.mean(dld_peak_b)
        print('The maximum of histogram is located at:', maximum_location)

    elif calibration_mode == 'mc':
        mask_temporal = np.logical_and(
            (variables.mc_calib > variables.selected_x1),
            (variables.mc_calib < variables.selected_x2)
        )
        dld_peak_b = variables.mc_calib[mask_temporal]

        if maximum_cal_method == 'histogram':
            bins = np.linspace(np.min(dld_peak_b), np.max(dld_peak_b), round(np.max(dld_peak_b) / 0.1))
            y, x = np.histogram(dld_peak_b, bins=bins)
            peaks, properties = find_peaks(y, height=0)
            index_peak_max_ini = np.argmax(properties['peak_heights'])
            max_peak = peaks[index_peak_max_ini]
            maximum_location = x[max_peak]
        elif maximum_cal_method == 'mean':
            maximum_location = np.mean(dld_peak_b)
        print('The maximum of histogram is located at:', maximum_location)

    dld_highVoltage_peak_v = dld_highVoltage[mask_temporal]
    print('The number of ions are:', len(dld_highVoltage_peak_v))
    print('The number of samples are:', int(len(dld_highVoltage_peak_v) / sample_size))

    fitresult = voltage_correction(dld_highVoltage_peak_v, dld_peak_b, maximum_location, index_fig=index_fig,
                                   figname='voltage_corr',
                                   sample_size=sample_size, mode=mode, calibration_mode=calibration_mode,
                                   peak_mode=peak_mode,
                                   plot=plot, save=save)

    f_v = voltage_corr(dld_highVoltage, *fitresult)
    print('The fit result are:', fitresult)

    if calibration_mode == 'tof':
        variables.dld_t_calib = variables.dld_t_calib / f_v
    elif calibration_mode == 'mc':
        variables.mc_calib = variables.mc_calib / f_v

    if plot:
        # Plot how correction factor for selected peak
        fig1, ax1 = plt.subplots(figsize=fig_size, constrained_layout=True)
        mask = np.random.randint(0, len(dld_highVoltage_peak_v), 1000)
        x = plt.scatter(dld_highVoltage_peak_v[mask], dld_peak_b[mask], color="blue", label=r"$t$", alpha=0.1, s=1)

        if calibration_mode == 'tof':
            ax1.set_ylabel("Time of Flight (ns)", fontsize=8)
        elif calibration_mode == 'mc':
            ax1.set_ylabel("mc (Da)", fontsize=8)
        ax1.set_xlabel("Voltage (V)", fontsize=8)
        plt.grid(color='aqua', alpha=0.3, linestyle='-.', linewidth=0.4)

        # Plot high voltage curve
        ax2 = ax1.twinx()
        f_v_plot = voltage_corr(dld_highVoltage_peak_v, *fitresult)

        y = ax2.plot(dld_highVoltage_peak_v, 1 / f_v_plot, color='r', label=r"$C_{V}^{-1}$")
        ax2.set_ylabel(r"$C_{V}^{-1}$", color="red", fontsize=8)

        plt.legend(handles=[x, y[0]], loc='upper right', prop={'size': 6})

        if save:
            plt.savefig(variables.result_path + "//vol_corr_%s.eps" % index_fig, format="svg", dpi=600)
            plt.savefig(variables.result_path + "//vol_corr_%s.png" % index_fig, format="png", dpi=600)

        plt.show()

        # Plot corrected tof/mc vs. uncalibrated tof/mc
        fig1, ax1 = plt.subplots(figsize=fig_size, constrained_layout=True)
        mask = np.random.randint(0, len(dld_highVoltage_peak_v), 10000)

        x = plt.scatter(dld_highVoltage_peak_v[mask], dld_peak_b[mask], color="blue", label='t', alpha=0.1, s=1)
        if calibration_mode == 'tof':
            ax1.set_ylabel("Time of Flight (ns)", fontsize=8)
        elif calibration_mode == 'mc':
            ax1.set_ylabel("mc (Da)", fontsize=8)
        ax1.set_xlabel("Voltage (V)", fontsize=8)
        plt.grid(color='aqua', alpha=0.3, linestyle='-.', linewidth=0.4)

        f_v_plot = voltage_corr(dld_highVoltage_peak_v[mask], *fitresult)

        dld_t_plot = dld_peak_b[mask] * (1 / f_v_plot)

        y = plt.scatter(dld_highVoltage_peak_v[mask], dld_t_plot, color="red", label=r"$t_{C_{V}}$", alpha=0.1, s=1)

        plt.legend(handles=[x, y], loc='upper right', prop={'size': 6})

        if save:
            plt.savefig(variables.result_path + "//peak_tof_V_corr_%s.svg" % index_fig, format="svg", dpi=600)
            plt.savefig(variables.result_path + "//peak_tof_V_corr_%s.png" % index_fig, format="png", dpi=600)

        plt.show()


def bowl_corr_fit(data_xy, a, b, c, d, e, f):
    """
    Compute the result of a quadratic equation based on the input data.

    Args:
        data_xy (tuple): Tuple containing the x and y data points.
        a, b, c, d, e, f (float): Coefficients of the quadratic equation.

    Returns:
        result (numpy.ndarray): Result of the quadratic equation.
    """
    x = data_xy[0]
    y = data_xy[1]
    result = (a + b * x + c * y + d * (x ** 2) + e * x * y + f * (y ** 2))
    return result


def bowl_correction(dld_x_bowl, dld_y_bowl, dld_t_bowl, det_diam, maximum_location, sample_size, index_fig, plot, save,
                    fig_size=(7, 5)):
    """
    Perform bowl correction on the input data.

    Args:
        dld_x_bowl (numpy.ndarray): X coordinates of the data points.
        dld_y_bowl (numpy.ndarray): Y coordinates of the data points.
        dld_t_bowl (numpy.ndarray): Time values of the data points.
        det_diam (float): Diameter of the detector.
        maximum_location (float): Maximum location for normalization.
        sample_size (int): Size of each sample.
        index_fig (int): Index for figure naming.
        plot (bool): Flag indicating whether to plot the surface.
        save (bool): Flag indicating whether to save the plot.
        fig_size (tuple): Size of the figure.

    Returns:
        parameters (numpy.ndarray): Optimized parameters of the bowl correction.
    """
    x_sample_list = []
    y_sample_list = []
    dld_t_peak_list = []

    w1 = -int(det_diam)
    w2 = int(det_diam)
    h1 = w1
    h2 = w2

    d = sample_size  # sample size is in mm - so we change it to cm
    grid = product(range(h1, h2 - h2 % d, d), range(w1, w2 - w2 % d, d))
    x_y = np.vstack((dld_x_bowl, dld_y_bowl)).T

    for i, j in grid:
        mask_x = np.logical_and((dld_x_bowl < j + d), (dld_x_bowl > j))
        mask_y = np.logical_and((dld_y_bowl < i + d), (dld_y_bowl > i))
        mask = np.logical_and(mask_x, mask_y)
        if len(mask[mask]) > 0:
            x_y_selected = x_y[mask]
            x_sample_list.append(np.median(x_y_selected[:, 0]))
            y_sample_list.append(np.median(x_y_selected[:, 1]))
            dld_t_peak_list.append(np.mean(dld_t_bowl[mask]) / maximum_location)

    parameters, covariance = curve_fit(bowl_corr_fit, [np.array(x_sample_list), np.array(y_sample_list)],
                                       np.array(dld_t_peak_list))

    if plot:
        model_x_data = np.linspace(-35, 35, 30)
        model_y_data = np.linspace(-35, 35, 30)
        X, Y = np.meshgrid(model_x_data, model_y_data)
        Z = bowl_corr_fit(np.array([X, Y]), *parameters)

        fig, ax = plt.subplots(figsize=fig_size, subplot_kw=dict(projection="3d"), constrained_layout=True)
        fig.add_axes(ax)
        ax.plot_surface(X, Y, 1 / Z, cmap=cm.plasma)
        ax.set_xlabel('X', fontsize=8, labelpad=0)
        ax.set_ylabel('Y', fontsize=8)
        ax.set_zlabel(r"${C_B}^{-1}$", fontsize=8, labelpad=2)
        ax.zaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))

        if save:
            plt.savefig(variables.result_path + "//bowl_corr_%s.svg" % index_fig, format="svg", dpi=600)
            plt.savefig(variables.result_path + "//bowl_corr_%s.png" % index_fig, format="png", dpi=600)
        plt.show()

    return parameters


def bowl_correction_main(dld_x, dld_y, dld_highVoltage, det_diam, sample_size, calibration_mode, index_fig, plot, save,
                         maximum_cal_method='mean', fig_size=(5, 5)):
    """
    Perform bowl correction on the input data and plot the results.

    Args:
        dld_x (numpy.ndarray): X positions.
        dld_y (numpy.ndarray): Y positions.
        dld_highVoltage (numpy.ndarray): High voltage values.
        det_diam (float): Detector diameter.
        sample_size (int): Sample size.
        calibration_mode (str): Calibration mode ('tof' or 'mc').
        index_fig (int): Index figure.
        plot (bool): Flag indicating whether to plot the results.
        save (bool): Flag indicating whether to save the plots.
        maximum_cal_method (str, optional): Maximum calculation method ('mean' or 'histogram').
        fig_size (tuple, optional): Figure size.

    Returns:
        tuple: Fit parameters.

    """

    if calibration_mode == 'tof':
        mask_temporal = np.logical_and((variables.dld_t_calib > variables.selected_x1),
                                       (variables.dld_t_calib < variables.selected_x2))
    elif calibration_mode == 'mc':
        mask_temporal = np.logical_and((variables.mc_calib > variables.selected_x1),
                                       (variables.mc_calib < variables.selected_x2))

    dld_peak = variables.dld_t_calib[mask_temporal] if calibration_mode == 'tof' else variables.mc_calib[mask_temporal]
    print('The number of ions is:', len(dld_peak))

    mask_1 = np.logical_and((dld_x[mask_temporal] > -0.2), (dld_x[mask_temporal] < 0.2))
    mask_2 = np.logical_and((dld_y[mask_temporal] > -0.2), (dld_y[mask_temporal] < 0.2))
    mask = np.logical_and(mask_1, mask_2)
    dld_peak_mid = dld_peak[mask]

    if maximum_cal_method == 'histogram':
        bins = np.linspace(np.min(dld_peak_mid), np.max(dld_peak_mid), round(np.max(dld_peak_mid) / 0.1))
        y, x = np.histogram(dld_peak_mid, bins=bins)
        peaks, properties = find_peaks(y, height=0)
        index_peak_max_ini = np.argmax(properties['peak_heights'])
        maximum_location = x[peaks[index_peak_max_ini]]
    elif maximum_cal_method == 'mean':
        maximum_location = np.mean(dld_peak_mid)

    print('The maximum of histogram is located at:', maximum_location)

    dld_x_peak = dld_x[mask_temporal]
    dld_y_peak = dld_y[mask_temporal]
    dld_highVoltage_peak = dld_highVoltage[mask_temporal]

    parameters = bowl_correction(dld_x_peak, dld_y_peak, dld_peak, det_diam, maximum_location,
                                 sample_size=sample_size, index_fig=index_fig, plot=plot, save=save)

    print('The fit result is:', parameters)

    f_bowl = bowl_corr_fit([dld_x_peak, dld_y_peak], *parameters)

    if calibration_mode == 'tof':
        variables.dld_t_calib *= 1 / f_bowl
    elif calibration_mode == 'mc':
        variables.mc_calib *= 1 / f_bowl

    if plot:
        # Plot how bowl correct tof/mc vs high voltage
        fig1, ax1 = plt.subplots(figsize=fig_size, constrained_layout=True)
        mask = np.random.randint(0, len(dld_highVoltage_peak), 10000)

        x = plt.scatter(dld_highVoltage_peak[mask], dld_peak[mask], color="blue", label=r"$t$", alpha=0.1, s=1)

        if calibration_mode == 'tof':
            ax1.set_ylabel("Time of Flight (ns)", fontsize=8)
        elif calibration_mode == 'mc':
            ax1.set_ylabel("mc (Da)", fontsize=8)

        ax1.set_xlabel("Voltage (V)", fontsize=8)
        plt.grid(color='aqua', alpha=0.3, linestyle='-.', linewidth=0.4)

        f_bowl_plot = bowl_corr_fit([dld_x_peak[mask], dld_y_peak[mask]], *parameters)
        dld_t_plot = dld_peak[mask] * 1 / f_bowl_plot

        y = plt.scatter(dld_highVoltage_peak[mask], dld_t_plot, color="red", label=r"$t_{C_{B}}$", alpha=0.1, s=1)

        plt.legend(handles=[x, y], loc='upper right', prop={'size': 6})

        if save:
            plt.savefig(variables.result_path + "//peak_tof_bowl_corr_%s.svg" % index_fig, format="svg", dpi=600)
            plt.savefig(variables.result_path + "//peak_tof_bowl_corr_%s.png" % index_fig, format="png", dpi=600)

        plt.show()

        # Plot how bowl correction correct tof/mc vs dld_x position
        fig1, ax1 = plt.subplots(figsize=fig_size, constrained_layout=True)
        mask = np.random.randint(0, len(dld_highVoltage_peak), 10000)

        f_bowl_plot = bowl_corr_fit([dld_x_peak[mask], dld_y_peak[mask]], *parameters)
        dld_t_plot = dld_peak[mask] * 1 / f_bowl_plot

        x = plt.scatter(dld_x_peak[mask], dld_peak[mask], color="blue", label=r"$t$", alpha=0.1, s=1)
        y = plt.scatter(dld_x_peak[mask], dld_t_plot, color="red", label=r"$t_{C_{B}}$", alpha=0.1, s=1)

        if calibration_mode == 'tof':
            ax1.set_ylabel("Time of Flight (ns)", fontsize=8)
        elif calibration_mode == 'mc':
            ax1.set_ylabel("mc (Da)", fontsize=8)

        ax1.set_xlabel("X_det(mm)", fontsize=8)
        plt.grid(color='aqua', alpha=0.3, linestyle='-.', linewidth=0.4)
        plt.legend(handles=[x, y], loc='upper right', prop={'size': 6})

        if save:
            plt.savefig(variables.result_path + "//peak_tof_bowl_corr_p_%s.svg" % index_fig, format="svg", dpi=600)
            plt.savefig(variables.result_path + "//peak_tof_bowl_corr_p_%s.png" % index_fig, format="png", dpi=600)

        plt.show()

    return parameters


def plot_FDM(x, y, save, bins_s, figure_size=(4, 5)):
    """
    Plot the Frequency Distribution Map (FDM) based on the given x and y data.

    Args:
        x (array-like): The x-coordinates of the data points.
        y (array-like): The y-coordinates of the data points.
        save (bool): Flag indicating whether to save the plot.
        bins_s (int or array-like): The number of bins or bin edges for histogram2d.
        figure_size (tuple, optional): The size of the figure in inches (width, height). Defaults to (4, 5).
    """

    fig1, ax1 = plt.subplots(figsize=figure_size, constrained_layout=True)

    FDM, xedges, yedges = np.histogram2d(x, y, bins=bins_s)

    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    # Set x-axis label
    ax1.set_xlabel(r"$X_{det}$ (cm)", fontsize=8)
    # Set y-axis label
    ax1.set_ylabel(r"$Y_{det}$ (cm)", fontsize=8)

    cmap = copy(plt.cm.plasma)
    cmap.set_bad(cmap(0))
    pcm = ax1.pcolormesh(xedges, yedges, FDM.T, cmap=cmap, norm=colors.LogNorm(), rasterized=True)
    fig1.colorbar(pcm, ax=ax1, pad=0)

    if save:
        plt.savefig(variables.result_path + "fdm.png", format="png", dpi=600)
        plt.savefig(variables.result_path + "fdm.svg", format="svg", dpi=600)
    plt.show()
