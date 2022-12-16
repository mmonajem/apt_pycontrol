"""
This is the main script of loading and cropping the dataset.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector, EllipseSelector
from matplotlib.patches import Circle, Rectangle
import pandas as pd

# Local module and scripts
from pyccapt.calibration.calibration_tools import selectors_data
from pyccapt.calibration.calibration_tools import variables, data_tools
from pyccapt.calibration.calibration_tools import logging_library




def fetch_dataset_from_dld_grp(filename: "type: string - Path to hdf5(.h5) file", tdc: "type: string - model of tdc",
                               pulse_mode: "type: string - mode of pulse",
                               max_tof: "type: float - maximum possible tof") -> "type: dataframes":
    logger = logging_library.logger_creator('data_loadcrop')
    try:
        print("Filename>>", filename)
        hdf5Data = data_tools.read_hdf5(filename, tdc)
        if hdf5Data is None:
            raise FileNotFoundError
        if tdc == 'surface_concept':
            dld_highVoltage = hdf5Data['dld/high_voltage'].to_numpy()
            if pulse_mode == 'laser':
                dld_pulse = hdf5Data['dld/laser_intensity'].to_numpy()
            elif pulse_mode == 'voltage':
                dld_pulse = hdf5Data['dld/pulse_voltage'].to_numpy()
            dld_startCounter = hdf5Data['dld/start_counter'].to_numpy()
            dld_t = hdf5Data['dld/t'].to_numpy()
            dld_x = hdf5Data['dld/x'].to_numpy()
            dld_y = hdf5Data['dld/y'].to_numpy()
            # remove data that is location are out of the detector

            mask_local = np.logical_and((np.abs(dld_x) <= 40.0), (np.abs(dld_y) <= 40.0))
            mask_temporal = np.logical_and((dld_t > 0), (dld_t < max_tof))
            mask = np.logical_and(mask_temporal, mask_local)
            dld_highVoltage = dld_highVoltage[mask]
            dld_pulse = dld_pulse[mask]
            dld_startCounter = dld_startCounter[mask]
            dld_t = dld_t[mask]
            dld_x = dld_x[mask] * 0.1 # to convert them from mm to cm
            dld_y = dld_y[mask] * 0.1 # to convert them from mm to cm

            dld_highVoltage = np.expand_dims(dld_highVoltage, axis=1)
            dld_pulse = np.expand_dims(dld_pulse, axis=1)
            dld_startCounter = np.expand_dims(dld_startCounter, axis=1)
            dld_t = np.expand_dims(dld_t, axis=1)
            dld_x = np.expand_dims(dld_x, axis=1)
            dld_y = np.expand_dims(dld_y, axis=1)

            dldGroupStorage = np.concatenate((dld_highVoltage, dld_pulse, dld_startCounter, dld_t, dld_x, dld_y),
                                             axis=1)

        elif tdc == 'roentdec':
            dld_highVoltage = hdf5Data['dld/high_voltage'].to_numpy()
            if pulse_mode == 'laser':
                dld_pulse = hdf5Data['dld/laser_intensity'].to_numpy()
            elif pulse_mode == 'voltage':
                dld_pulse = hdf5Data['dld/pulse_voltage'].to_numpy()
            dld_AbsoluteTimeStamp = hdf5Data['dld/AbsoluteTimeStamp'].to_numpy()
            dld_t = hdf5Data['dld/t'].to_numpy()
            dld_x = hdf5Data['dld/x'].to_numpy()
            dld_y = hdf5Data['dld/y'].to_numpy()
            # remove data that is location are out of the detector

            mask_local = np.logical_and((np.abs(dld_x) <= 60.0), (np.abs(dld_y) <= 60.0))
            mask_temporal = np.logical_and((dld_t > 0), (dld_t < max_tof))
            mask = np.logical_and(mask_temporal, mask_local)
            dld_highVoltage = dld_highVoltage[mask]
            dld_pulse = dld_pulse[mask]
            # TODO
            # dld_AbsoluteTimeStamp = dld_AbsoluteTimeStamp[mask]
            dld_AbsoluteTimeStamp = dld_t[mask]
            dld_t = dld_t[mask]
            dld_x = dld_x[mask]
            dld_y = dld_y[mask]

            dld_highVoltage = np.expand_dims(dld_highVoltage, axis=1)
            dld_pulse = np.expand_dims(dld_pulse, axis=1)
            dld_AbsoluteTimeStamp = np.expand_dims(dld_AbsoluteTimeStamp, axis=1)
            dld_t = np.expand_dims(dld_t, axis=1)
            dld_x = np.expand_dims(dld_x, axis=1)
            dld_y = np.expand_dims(dld_y, axis=1)

            dldGroupStorage = np.concatenate((dld_highVoltage, dld_pulse, dld_AbsoluteTimeStamp, dld_t, dld_x, dld_y),
                                             axis=1)
        dld_group_storage = create_pandas_dataframe(dldGroupStorage, tdc, pulse_mode)
        return dld_group_storage
    except KeyError as error:
        logger.info(error)
        logger.critical("[*] Keys missing in the dataset")
    except FileNotFoundError as error:
        logger.info(error)
        logger.critical("[*] HDF5 file not found")


def concatenate_dataframes_of_dld_grp(
        dataframeList: "type:list - list of dataframes") -> "type:list - list of dataframes":
    dld_masterDataframeList = dataframeList
    dld_masterDataframe = pd.concat(dld_masterDataframeList, axis=1)
    return dld_masterDataframe

def plot_crop_experimetn_history(dldGroupStorage: "type: dataframes",
                                 rect=False, only_plot=False, save_name=False):
    fig1, ax1 = plt.subplots(figsize=(8, 4), constrained_layout=True)

    # Plot tof and high voltage
    yaxis = dldGroupStorage['t (ns)'].to_numpy()

    xaxis = np.arange(len(yaxis))

    high_voltage = dldGroupStorage['high_voltage (V)'].to_numpy()

    heatmap, xedges, yedges = np.histogram2d(xaxis, yaxis, bins=(1200, 800))
    heatmap[heatmap == 0] = 1  # to have zero after apply log
    heatmap = np.log(heatmap)
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    # set x-axis label
    ax1.set_xlabel("hit sequence number", color="red", fontsize=10)
    # set y-axis label
    ax1.set_ylabel("time of flight [ns]", color="red", fontsize=10)
    plt.title("Experiment history")
    img = plt.imshow(heatmap.T, extent=extent, origin='lower', aspect="auto")

    cax = ax1.inset_axes([1.14, 0.0, 0.05, 1])
    fig1.colorbar(img, ax=ax1, cax=cax)

    # plot high voltage curve
    ax2 = ax1.twinx()

    xaxis2 = np.arange(len(high_voltage))
    ax2.plot(xaxis2, high_voltage, color='b', linewidth=2)
    ax2.set_ylabel("DC voltage [V]", color="blue", fontsize=10)
    if not only_plot:
        if not rect:
            rectangle_box_selector(ax2)
            plt.connect('key_press_event', selectors_data.toggle_selector)
        else:
            left, bottom, width, height = (
                variables.selected_x1, 0, variables.selected_x2 - variables.selected_x1, np.max(yaxis))
            rect = Rectangle((left, bottom), width, height, fill=True, alpha=0.2, color="r", linewidth=2)
            ax1.add_patch(rect)

    if save_name:
        plt.savefig("%s.png" % save_name, format="png", dpi=600)
        plt.savefig("%s.svg" % save_name, format="svg", dpi=600)

    plt.show(block=True)


def plot_crop_FDM(data_crop: "type:list  - cropped list content", bins=(256, 256), circle=False,
                  save_name=False, only_plot=False):
    fig1, ax1 = plt.subplots(figsize=(6, 5), constrained_layout=True)
    logger = logging_library.logger_creator('data_loadcrop')
    # Plot and crop FDM
    x = data_crop['x_det (cm)'].to_numpy()
    y = data_crop['y_det (cm)'].to_numpy()
    FDM, xedges, yedges = np.histogram2d(x, y, bins=bins)

    FDM[FDM == 0] = 1  # to have zero after apply log
    FDM = np.log(FDM)

    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    # set x-axis label
    ax1.set_xlabel("x_det [cm]", color="red", fontsize=10)
    # set y-axis label
    ax1.set_ylabel("y_det [cm]", color="red", fontsize=10)
    plt.title("FDM")
    img = plt.imshow(FDM.T, extent=extent, origin='lower', aspect="auto")
    fig1.colorbar(img)

    if not only_plot:
        if not circle:
            elliptical_shape_selector(ax1, fig1)
        else:
            print('x:', variables.selected_x_fdm, 'y:', variables.selected_y_fdm, 'roi:', variables.roi_fdm)
            circ = Circle((variables.selected_x_fdm, variables.selected_y_fdm), variables.roi_fdm, fill=True,
                          alpha=0.2, color='r', linewidth=1)
            ax1.add_patch(circ)
    if save_name:
        logger.info("Plot saved by the name {}".format(save_name))
        plt.savefig("%s.png" % save_name, format="png", dpi=600)
        plt.savefig("%s.svg" % save_name, format="svg", dpi=600)
    plt.show(block=True)


def rectangle_box_selector(axisObject: "type:object"):
    # drawtype is 'box' or 'line' or 'none'
    selectors_data.toggle_selector.RS = RectangleSelector(axisObject, selectors_data.line_select_callback,
                                                          useblit=True,
                                                          button=[1, 3],  # don't use middle button
                                                          minspanx=1, minspany=1,
                                                          spancoords='pixels',
                                                          interactive=True)


def crop_dataset(dld_master_dataframe: "type: dataframes") -> "type: dataframe":
    data_crop = dld_master_dataframe.loc[int(variables.selected_x1):int(variables.selected_x2), :]
    data_crop.reset_index(inplace=True, drop=True)
    return data_crop


def elliptical_shape_selector(axisObject: "type:object", figureObject: "type:object"):
    selectors_data.toggle_selector.ES = EllipseSelector(axisObject, selectors_data.onselect, useblit=True,
                                                        button=[1, 3],  # don't use middle button
                                                        minspanx=1, minspany=1,
                                                        spancoords='pixels',
                                                        interactive=True)
    figureObject.canvas.mpl_connect('key_press_event', selectors_data.toggle_selector)


def crop_data_after_selection(data_crop: "dataframe") -> "dataframe":
    # crop the data based on selected are of FDM
    x = data_crop['x_det (cm)'].to_numpy()
    y = data_crop['y_det (cm)'].to_numpy()
    detector_dist = np.sqrt(
        (x - variables.selected_x_fdm) ** 2 + (y - variables.selected_y_fdm) ** 2)
    mask_fdm = (detector_dist > variables.roi_fdm)
    data_crop.drop(np.where(mask_fdm)[0], inplace=True)
    data_crop.reset_index(inplace=True, drop=True)
    return data_crop

def create_pandas_dataframe(data_crop: "type:numpy array", tdc: "type: string - model of tdc",
                            pulser_mode: "type: string - mode of pulser"):
    if tdc == 'surface_concept':
        if pulser_mode == 'voltage':
            hdf_dataframe = pd.DataFrame(data=data_crop,
                                         columns=['high_voltage (V)', 'pulse (V)', 'start_counter', 't (ns)',
                                                  'x_det (cm)', 'y_det (cm)'])
        elif pulser_mode == 'laser':
            hdf_dataframe = pd.DataFrame(data=data_crop,
                                         columns=['high_voltage (V)', 'pulse (deg)', 'start_counter', 't (ns)',
                                                  'x_det (cm)', 'y_det (cm)'])
    elif tdc == 'roentdec':
        if pulser_mode == 'voltage':
            hdf_dataframe = pd.DataFrame(data=data_crop,
                                         columns=['high_voltage (V)', 'pulse (V)', 'start_counter', 't (ns)',
                                                  'x_det (cm)', 'y_det (cm)'])
        elif pulser_mode == 'laser':
            hdf_dataframe = pd.DataFrame(data=data_crop,
                                         columns=['high_voltage (V)', 'pulse (deg)', 'start_counter', 't (ns)',
                                                  'x_det (cm)', 'y_det (cm)'])
    return hdf_dataframe