"""
This is the main script of loading and cropping the dataset.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector, EllipseSelector
from matplotlib.patches import Circle, Rectangle
import pandas as pd
import h5py

# Local module and scripts
from pyccapt.calibration.calibration_tools import selectors_data
from pyccapt.calibration.calibration_tools import variables, data_tools
from pyccapt.calibration.calibration_tools import logging_library

logger = logging_library.logger_creator('data_loadcrop')


def fetch_dataset_from_dld_grp(filename: "type: string - Path to hdf5(.h5) file", tdc: "type: string - model of tdc") -> "type:list - list of dataframes":
    try:
        print("Filename>>",filename)
        hdf5Data = data_tools.read_hdf5(filename, tdc)
        print("here",hdf5Data)
        if hdf5Data is None:
            print("Helloo")
            raise FileNotFoundError
        if tdc == 'surface_concept':
            #if 'dld/high_voltage' or 'dld/pulse_voltage' or 'dld/start_counter' or 'dld/t' or 'dld/x' or 'dld/y' not in hdf5Data:
            #    raise KeyError 
            dld_highVoltage = hdf5Data['dld/high_voltage']
            dld_pulseVoltage = hdf5Data['dld/pulse_voltage']
            dld_startCounter = hdf5Data['dld/start_counter']
            dld_t = hdf5Data['dld/t']
            dld_x = hdf5Data['dld/x']
            dld_y = hdf5Data['dld/y']
            dldGroupStorage = [dld_highVoltage, dld_pulseVoltage, dld_startCounter, dld_t, dld_x, dld_y]
        elif tdc == 'roentdec':
            #if 'dld/high_voltage' or 'dld/laser_intensity' or 'dld/AbsoluteTimeStamp' or 'dld/t' or 'dld/x' or 'dld/y' not in hdf5Data:
            #    raise KeyError 
            dld_highVoltage = hdf5Data['dld/high_voltage']
            dld_laserPower = hdf5Data['dld/laser_intensity']
            dld_AbsoluteTimeStamp = hdf5Data['dld/AbsoluteTimeStamp']
            dld_t = hdf5Data['dld/t']
            dld_x = hdf5Data['dld/x']
            dld_y = hdf5Data['dld/y']
            # remove data that is location are out of the detector
            tt = dld_t.to_numpy()
            xx = dld_x.to_numpy()
            yy = dld_y.to_numpy()
            mask_local = np.logical_and((np.abs(xx) <= 50.0), (np.abs(yy) <= 50.0))
            mask_temporal = (tt > 0)
            mask = np.logical_and(mask_temporal, mask_local)
            dld_highVoltage = dld_highVoltage[mask]
            dld_laserPower = dld_laserPower[mask]
            dld_AbsoluteTimeStamp = dld_t[mask]
            dld_t = dld_t[mask]
            dld_x = dld_x[mask]
            dld_y = dld_y[mask]

            dldGroupStorage = [dld_highVoltage, dld_laserPower, dld_AbsoluteTimeStamp, dld_t, dld_x, dld_y]
        return dldGroupStorage
    except KeyError as error:
        logger.info(error)
        logger.critical("[*]Keys missing in the dataset")
    except FileNotFoundError as error:
        logger.info(error)
        logger.critical("[*] HDF5 file not found")


def concatenate_dataframes_of_dld_grp(
        dataframeList: "type:list - list of dataframes") -> "type:list - list of dataframes":
    dld_masterDataframeList = dataframeList
    dld_masterDataframe = pd.concat(dld_masterDataframeList, axis=1)
    return dld_masterDataframe


def plot_graph_for_dld_high_voltage(ax1: "type:object", dldGroupStorage: "type:list - list of dataframes",
                                    rect=None, save_name=None):
    # Plot tof and high voltage
    y = dldGroupStorage[3]  # dld_t
    y.loc[y['values'] > 5000, 'values'] = 0
    yaxis = y['values'].to_numpy()
    xaxis = np.arange(len(yaxis))

    high_voltage = dldGroupStorage[0]['values'].to_numpy()

    heatmap, xedges, yedges = np.histogram2d(xaxis, yaxis, bins=(1200, 800))
    heatmap[heatmap == 0] = 1  # to have zero after apply log
    heatmap = np.log(heatmap)
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    # set x-axis label
    ax1.set_xlabel("hit sequence number", color="red", fontsize=14)
    # set y-axis label
    ax1.set_ylabel("time of flight [ns]", color="red", fontsize=14)
    plt.title("Experiment history")
    plt.imshow(heatmap.T, extent=extent, origin='lower', aspect="auto")

    # plot high voltage curve
    ax2 = ax1.twinx()

    xaxis2 = np.arange(len(high_voltage))
    ax2.plot(xaxis2, high_voltage, color='r', linewidth=2)
    ax2.set_ylabel("DC voltage [V]", color="blue", fontsize=14)
    if rect is None:
        rectangle_box_selector(ax2)
        plt.connect('key_press_event', selectors_data.toggle_selector)
    else:
        left, bottom, width, height = (
            variables.selected_x1, 0, variables.selected_x2 - variables.selected_x1, np.max(yaxis))
        rect = Rectangle((left, bottom), width, height, fill=True, alpha=0.2, color="r", linewidth=2)
        ax1.add_patch(rect)

    if save_name is not None:
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


def crop_dataset(dld_masterDataframe: "type:list - list of dataframes") -> "type:list  - cropped list content":
    dld_masterDataframe = dld_masterDataframe.to_numpy()
    data_crop = dld_masterDataframe[int(variables.selected_x1):int(variables.selected_x2), :]
    return data_crop


def elliptical_shape_selector(axisObject: "type:object", figureObject: "type:object"):
    selectors_data.toggle_selector.ES = EllipseSelector(axisObject, selectors_data.onselect, useblit=True,
                                                        button=[1, 3],  # don't use middle button
                                                        minspanx=1, minspany=1,
                                                        spancoords='pixels',
                                                        interactive=True)
    figureObject.canvas.mpl_connect('key_press_event', selectors_data.toggle_selector)


def plot_crop_FDM(ax1, fig1, data_crop: "type:list  - cropped list content", bins=(256,556), save_name=None):
    # Plot and crop FDM

    FDM, xedges, yedges = np.histogram2d(data_crop[:, 4], data_crop[:, 5], bins=bins)

    FDM[FDM == 0] = 1  # to have zero after apply log
    FDM = np.log(FDM)

    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    # set x-axis label
    ax1.set_xlabel("x [mm]", color="red", fontsize=14)
    # set y-axis label
    ax1.set_ylabel("y [mm]", color="red", fontsize=14)
    plt.title("FDM")
    plt.imshow(FDM.T, extent=extent, origin='lower', aspect="auto")
    elliptical_shape_selector(ax1, fig1)
    if save_name != None:
        logger.info("Plot saved by the name {}".format(save_name))
        plt.savefig("%s.png" % save_name, format="png", dpi=600)
        plt.savefig("%s.svg" % save_name, format="svg", dpi=600)
    plt.show(block=True)


def plot_FDM_after_selection(ax1, fig1, data_crop: "type:list  - cropped list content", bins=(256,256), save_name=None):
    # Plot FDM with selected part
    FDM, xedges, yedges = np.histogram2d(data_crop[:, 4], data_crop[:, 5], bins=bins)
    FDM[FDM == 0] = 1  # to have zero after apply log
    FDM = np.log(FDM)
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    # set x-axis label
    ax1.set_xlabel("x [mm]", color="red", fontsize=14)
    # set y-axis label
    ax1.set_ylabel("y [mm]", color="red", fontsize=14)
    plt.title("FDM")
    plt.imshow(FDM.T, extent=extent, origin='lower', aspect="auto")
    logger.info("Circle selector Called")
    print('x:', variables.selected_x_fdm, 'y:', variables.selected_y_fdm, 'roi:', variables.roi_fdm)
    circ = Circle((variables.selected_x_fdm, variables.selected_y_fdm), variables.roi_fdm, fill=True,
                  alpha=0.2, color='r', linewidth=1)
    ax1.add_patch(circ)
    if save_name != None:
        logger.info("Plot saved by the name {}".format(save_name))
        plt.savefig("%s.png" % save_name, format="png", dpi=600)
        plt.savefig("%s.svg" % save_name, format="svg", dpi=600)
    plt.show(block=True)


def crop_data_after_selection(data_crop: "type:list  - cropped list content") -> list:
    # crop the data based on selected are of FDM
    detectorDist = np.sqrt(
        (data_crop[:, 4] - variables.selected_x_fdm) ** 2 + (data_crop[:, 5] - variables.selected_y_fdm) ** 2)
    mask_fdm = (detectorDist < variables.roi_fdm)
    return data_crop[np.array(mask_fdm)]


def plot_FDM(ax1, fig1, data_crop: "type:list  - cropped list content", bins=(256,256), save_name=None):
    # Plot FDM
    FDM, xedges, yedges = np.histogram2d(data_crop[:, 4], data_crop[:, 5], bins=bins)
    FDM[FDM == 0] = 1  # to have zero after apply log
    FDM = np.log(FDM)
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    # set x-axis label
    ax1.set_xlabel("x [mm]", color="red", fontsize=14)
    # set y-axis label
    ax1.set_ylabel("y [mm]", color="red", fontsize=14)
    plt.title("FDM")
    plt.imshow(FDM.T, extent=extent, origin='lower', aspect="auto")
    if save_name != None:
        logger.info("Plot saved by the name {}".format(save_name))
        plt.savefig("%s.png" % save_name, format="png", dpi=600)
        plt.savefig("%s.svg" % save_name, format="svg", dpi=600)
    plt.show(block=True)


def save_croppped_data_to_hdf5(data_crop: "type:list  - cropped list content",
                               dld_masterDataframe: "type:list - list of dataframes",
                               name: "type:string - name of h5 file", tdc: "type: string - model of tdc",):
    # save the cropped data
    hierarchyName = 'df'
    logger.info('tofCropLossPct {}'.format(str(int((1 - len(data_crop) / len(dld_masterDataframe)) * 100))))
    if tdc == 'surface_concept':
        hdf5Dataframe = pd.DataFrame(data=data_crop,
                                     columns=['dld/high_voltage', 'dld/pulse_voltage', 'dld/start_counter', 'dld/t',
                                              'dld/x', 'dld/y'])
    elif tdc == 'roentdec':
        hdf5Dataframe = pd.DataFrame(data=data_crop,
                                     columns=['dld/high_voltage', 'dld/laser_intensity', 'dld/start_counter', 'dld/t',
                                              'dld/x', 'dld/y'])
    data_tools.store_df_to_hdf(name, hdf5Dataframe, hierarchyName)


def add_croppped_data_to_hdf5(filename: "type: string - Path to hdf5(.h5) file", data_crop: "type:list  - cropped list content",
                dld_masterDataframe: "type:list - list of dataframes",
                tdc: "type: string - model of tdc") -> "type:list - list of dataframes":
    try:
        # add the cropped data
        hdf = h5py.File(filename, 'a')
        hdf.create_dataset("cropped_dld/x", data=data_crop[:, 5], dtype='f')
        hdf.create_dataset("cropped_dld/y", data=data_crop[:, 4], dtype='f')
        hdf.create_dataset("cropped_dld/t", data=data_crop[:, 3], dtype='f')
        hdf.create_dataset("cropped_dld/start_counter", data=data_crop[:, 2], dtype='f')
        if tdc == 'surface_concept':
            hdf.create_dataset("cropped_dld/pulse_voltage", data=data_crop[:, 1], dtype='f')
        elif tdc == 'roentdec':
            hdf.create_dataset("cropped_dld/laser_intensity", data=data_crop[:, 1], dtype='f')
        hdf.create_dataset("cropped_dld/high_voltage", data=data_crop[:, 0], dtype='f')

    except:
        hdf.close()

    with h5py.File(filename, 'r+') as hdf:
        del hdf["cropped_dld/x"]
        del hdf["cropped_dld/y"]
        del hdf["cropped_dld/t"]
        del hdf["cropped_dld/start_counter"]
        if tdc == 'surface_concept':
            del hdf["cropped_dld/pulse_voltage"]
        elif tdc == 'roentdec':
            del hdf["cropped_dld/laser_intensity"]

        del hdf["cropped_dld/high_voltage"]

        hdf["cropped_dld/x"] = data_crop[:, 5]
        hdf["cropped_dld/y"] = data_crop[:, 4]
        hdf["cropped_dld/t"] = data_crop[:, 3]
        hdf["cropped_dld/start_counter"] = data_crop[:, 2]
        if tdc == 'surface_concept':
            hdf.create_dataset("cropped_dld/pulse_voltage", data=data_crop[:, 1], dtype='f')
        elif tdc == 'roentdec':
            hdf.create_dataset("cropped_dld/laser_intensity", data=data_crop[:, 1], dtype='f')
        hdf["cropped_dld/high_voltage"] = data_crop[:, 0]


    print('tofCropLossPct', (1 - len(data_crop) / len(dld_masterDataframe)) * 100)


def add_tof_mc_data_to_hdf5(filename: "type: string - Path to hdf5(.h5) file", tof: "type:numpy array  - TOF",
                mc: "type:numpy array - mass-to-charge") -> "type:list - list of dataframes":
    try:
        # add the cropped data
        hdf = h5py.File(filename, 'a')
        hdf.create_dataset("cropped_dld/mc", data=mc, dtype='f')
        hdf.create_dataset("cropped_dld/t_c", data=tof, dtype='f')

    except:
        hdf.close()

    with h5py.File(filename, 'r+') as hdf:
        del hdf["cropped_dld/mc"]
        del hdf["cropped_dld/t_c"]

        hdf["cropped_dld/mc"] = mc
        hdf["cropped_dld/t_c"] = tof


