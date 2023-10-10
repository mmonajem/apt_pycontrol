import matplotlib.pyplot as plt
import numpy as np
import pybaselines
from adjustText import adjust_text
from pybaselines import Baseline
from scipy.optimize import curve_fit
from scipy.signal import find_peaks, peak_widths, peak_prominences

from pyccapt.calibration.calibration_tools import intractive_point_identification
from pyccapt.calibration.data_tools import data_loadcrop, plot_vline_draw, selectors_data


def fit_background(x, a, b):
    """
    Calculate the fit function value for the given parameters.

    Args:
        x (array-like): Input array of values.
        a (float): Parameter a.
        b (float): Parameter b.

    Returns:
        array-like: Fit function values corresponding to the input array.
    """
    yy = (a / (2 * np.sqrt(b))) * 1 / (np.sqrt(x))
    return yy


class AptHistPlotter:
    def __init__(self, mc_tof, variables=None):
        self.original_x_limits = None
        self.bin_width = None
        self.fig = None
        self.ax = None
        self.mc_tof = mc_tof
        self.variables = variables
        self.x = None
        self.y = None
        self.peak_annotates = []
        self.annotates = []
        self.patches = None
        self.peaks = None
        self.properties = None
        self.peak_widths = None
        self.prominences = None
        self.mask_f = None
        self.legend_colors = []

    def find_peaks_and_widths(self, prominence=None, distance=None, percent=50):
        try:
            self.peaks, self.properties = find_peaks(self.y, prominence=prominence, distance=distance, height=0)
            self.peak_widths = peak_widths(self.y, self.peaks, rel_height=(percent / 100), prominence_data=None)
            self.prominences = peak_prominences(self.y, self.peaks, wlen=None)

            x_peaks = self.x[self.peaks]
            y_peaks = self.y[self.peaks]
            self.variables.peak_x = x_peaks
            self.variables.peak_y = y_peaks
            index_max_ini = np.argmax(y_peaks)
            self.variables.max_peak = x_peaks[index_max_ini]
        except ValueError:
            print('Peak finding failed.')
            self.peaks = None
            self.properties = None
            self.peak_widths = None
            self.prominences = None
            self.variables.peak_x = None
            self.variables.peak_y = None
            self.variables.max_peak = None

        return self.peaks, self.properties, self.peak_widths, self.prominences

    def plot_histogram(self, bin_width=0.1, mode=None, label='mc', log=True, grid=False, steps='stepfilled',
                       fig_size=(9, 5)):
        # Define the bins
        self.bin_width = bin_width
        bins = np.linspace(np.min(self.mc_tof), np.max(self.mc_tof), round(np.max(self.mc_tof) / bin_width))

        # Plot the histogram directly
        self.fig, self.ax = plt.subplots(figsize=fig_size)

        if steps == 'bar':
            edgecolor = None
        else:
            edgecolor = 'k'

        if mode == 'normalized':
            self.y, self.x, self.patches = self.ax.hist(self.mc_tof, bins=bins, alpha=0.9,
                                                        color='slategray', edgecolor=edgecolor, histtype=steps,
                                                        density=True)
        else:
            self.y, self.x, self.patches = self.ax.hist(self.mc_tof, bins=bins, alpha=0.9, color='slategray',
                                                        edgecolor=edgecolor, histtype=steps)
        self.ax.set_xlabel('Mass/Charge [Da]' if label == 'mc' else 'Time of Flight [ns]')
        self.ax.set_ylabel('Frequency [cts]')
        self.ax.set_yscale('log' if log else 'linear')
        if grid:
            plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5)
        if self.original_x_limits is None:
            self.original_x_limits = self.ax.get_xlim()  # Store the original x-axis limits
        plt.tight_layout()
        plt.show()

        return self.y, self.x

    def plot_range(self, range_data, legend=True):
        if len(self.patches) == len(self.x) - 1:
            colors = range_data['color'].tolist()
            mc_low = range_data['mc_low'].tolist()
            mc_up = range_data['mc_up'].tolist()
            mc = range_data['mc'].tolist()
            ion = range_data['ion'].tolist()
            color_mask = np.full((len(self.x)), '#708090')  # default color is slategray
            for i in range(len(ion)):
                mask = np.logical_and(self.x >= mc_low[i], self.x <= mc_up[i])
                color_mask[mask] = colors[i]

            for i in range(len(self.x) - 1):
                if color_mask[i] != '#708090':
                    self.patches[i].set_facecolor(color_mask[i])

            for i in range(len(ion)):
                self.legend_colors.append((r'%s' % ion[i], plt.Rectangle((0, 0), 1, 1, fc=colors[i])))
                x_offset = 0.1  # Adjust this value as needed
                y_offset = 10  # Adjust this value as needed

                # Find the bin that contains the mc[i]
                bin_index = np.searchsorted(self.x, mc[i])
                peak_height = self.y[bin_index - 1] * ((mc[i] - self.x[bin_index - 1]) / self.bin_width)
                print(mc[i])
                print(peak_height)
                self.peak_annotates.append(plt.text(mc[i] + x_offset, peak_height + y_offset,
                                                    r'%s' % ion[i], color='black', size=10, alpha=1))
                self.annotates.append(str(i + 1))

            if legend:
                self.plot_color_legend(loc='center right')
        else:
            print('plot_range only works in plot_histogram mode=bar')

    def plot_peaks(self, range_data=None, mode='peaks'):

        x_offset = 0.1  # Adjust this value as needed
        y_offset = 10  # Adjust this value as needed
        if range_data is not None:
            ion = range_data['ion'].tolist()
            x_peak_loc = range_data['mc'].tolist()
            y_peak_loc = range_data['peak_count'].tolist()
            for i in range(len(ion)):
                self.peak_annotates.append(plt.text(x_peak_loc[i] + x_offset, y_peak_loc[i] + y_offset,
                                                      r'%s' % ion[i], color='black', size=10, alpha=1))
                self.annotates.append(str(i + 1))
        else:
            for i in range(len(self.peaks)):
                if mode == 'range':
                    if i in self.variables.peaks_idx:
                        self.peak_annotates.append(
                            plt.text(self.x[self.peaks][i] + x_offset, self.y[self.peaks][i] + y_offset,
                                     '%s' % '{:.2f}'.format(self.x[self.peaks][i]), color='black', size=10, alpha=1))
                elif mode == 'peaks':
                    self.peak_annotates.append(
                        plt.text(self.x[self.peaks][i] + x_offset, self.y[self.peaks][i] + y_offset,
                                 '%s' % '{:.2f}'.format(self.x[self.peaks][i]), color='black', size=10, alpha=1))

                self.annotates.append(str(i + 1))

    def selector(self, selector='rect'):
        if selector == 'rect':
            # Connect and initialize rectangle box selector
            data_loadcrop.rectangle_box_selector(self.ax, self.variables)
            plt.connect('key_press_event', selectors_data.toggle_selector(self.variables))
        elif selector == 'peak':
            # connect peak_x selector
            af = intractive_point_identification.AnnoteFinder(self.x[self.peaks], self.y[self.peaks], self.annotates,
                                                              self.variables, ax=self.ax)
            self.fig.canvas.mpl_connect('button_press_event', lambda event: af.annotates_plotter(event))

            zoom_manager = plot_vline_draw.HorizontalZoom(self.ax, self.fig)
            self.fig.canvas.mpl_connect('key_press_event', lambda event: zoom_manager.on_key_press(event))
            self.fig.canvas.mpl_connect('key_release_event', lambda event: zoom_manager.on_key_release(event))
            self.fig.canvas.mpl_connect('scroll_event', lambda event: zoom_manager.on_scroll(event))
        elif selector == 'range':
            # connect range selector
            line_manager = plot_vline_draw.VerticalLineManager(self.variables, self.ax, self.fig, [], [])

            self.fig.canvas.mpl_connect('button_press_event',
                                        lambda event: line_manager.on_press(event))
            self.fig.canvas.mpl_connect('button_release_event',
                                        lambda event: line_manager.on_release(event))
            self.fig.canvas.mpl_connect('motion_notify_event',
                                        lambda event: line_manager.on_motion(event))
            self.fig.canvas.mpl_connect('key_press_event',
                                        lambda event: line_manager.on_key_press(event))
            self.fig.canvas.mpl_connect('scroll_event', lambda event: line_manager.on_scroll(event))
            self.fig.canvas.mpl_connect('key_release_event',
                                        lambda event: line_manager.on_key_release(event))

    def plot_color_legend(self, loc):
        self.ax.legend([label[1] for label in self.legend_colors], [label[0] for label in self.legend_colors],
                       loc=loc)

    def plot_hist_info_legend(self, label='mc', bin=0.1, background=None, loc='left'):
        index_peak_max = np.argmax(self.prominences[0])

        if label == 'mc':
            mrp = '{:.2f}'.format(
                self.x[self.peaks][index_peak_max] / (self.x[int(self.peak_widths[3][index_peak_max])] -
                                                      self.x[int(self.peak_widths[2][index_peak_max])]))

            if background is not None:
                txt = 'bin width: %s Da\nnum atoms: %.2f$e^6$\nbackG: %s ppm/Da\nMRP(FWHM): %s' \
                      % (bin, len(self.mc_tof) / 1000000, int(self.background_ppm), mrp)
            else:
                # annotation with range stats
                upperLim = 4.5  # Da
                lowerLim = 3.5  # Da
                mask = np.logical_and((self.x >= lowerLim), (self.x <= upperLim))
                BG4 = np.sum(self.y[np.array(mask[:-1])]) / (upperLim - lowerLim)
                BG4 = BG4 / len(self.mc_tof) * 1E6

                txt = 'bin width: %s Da\nnum atoms: %.2f$e^6$\nBG@4: %s ppm/Da\nMRP(FWHM): %s' \
                      % (bin, (len(self.mc_tof) / 1000000), int(BG4), mrp)

        elif label == 'tof':
            mrp = '{:.2f}'.format(self.x[self.peaks[index_peak_max]] / (self.x[int(self.peak_widths[3][index_peak_max])] -
                                                              self.x[int(self.peak_widths[2][index_peak_max])]))
            if background['calculation'] and background['plot_no_back']:
                txt = 'bin width: %s ns\nnum atoms: %.2f$e^6$\nbackG: %s ppm/ns\nMRP(FWHM): %s' \
                      % (bin, len(self.mc_tof) / 1000000, int(self.background_ppm), mrp)
            else:
                # annotation with range stats
                upperLim = 50.5  # ns
                lowerLim = 49.5  # ns
                mask = np.logical_and((self.x >= lowerLim), (self.x <= upperLim))
                BG50 = np.sum(self.y[np.array(mask[:-1])]) / (upperLim - lowerLim)
                BG50 = BG50 / len(self.mc_tof) * 1E6
                txt = 'bin width: %s ns\nnum atoms: %.2f$e^6$ \nBG@50: %s ppm/ns\nMRP(FWHM): %s' \
                      % (bin, len(self.mc_tof) / 1000000, int(BG50), mrp)

        props = dict(boxstyle='round', facecolor='wheat', alpha=1)
        if loc == 'left':
            self.ax.text(.01, .95, txt, va='top', ma='left', transform=self.ax.transAxes, bbox=props, fontsize=10, alpha=1,
                     horizontalalignment='left', verticalalignment='top')
        elif loc == 'right':
            self.ax.text(.98, .95, txt, va='top', ma='left', transform=self.ax.transAxes, bbox=props, fontsize=10, alpha=1,
                     horizontalalignment='right', verticalalignment='top')

    def plot_horizontal_lines(self):
        for i in range(len(self.variables.h_line_pos)):
            if np.max(self.mc_tof) + 10 > self.variables.h_line_pos[i] > np.max(self.mc_tof) - 10:
                plt.axvline(x=self.variables.h_line_pos[i], color='b', linestyle='--', linewidth=2)

    def plot_background(self, mode, non_peaks=None, lam=5e10, tol=1e-1, max_iter=100, num_std=3, poly_order=5,
                        plot_no_back=True, plot=True, patch=True):

        if mode == 'aspls':
            baseline_fitter = Baseline(x_data=self.bins[:-1])
            fit_1, params_1 = baseline_fitter.aspls(self.y, lam=lam, tol=tol, max_iter=max_iter)

        if mode == 'fabc':
            fit_2, params_2 = pybaselines.classification.fabc(self.y, lam=lam,
                                                              num_std=num_std,
                                                              pad_kwargs='edges')
        if mode == 'dietrich':
            fit_2, params_2 = pybaselines.classification.dietrich(self.y, num_std=num_std)
        if mode == 'cwt_br':
            fit_2, params_2 = pybaselines.classification.cwt_br(self.y, poly_order=poly_order,
                                                                num_std=num_std,
                                                                tol=tol)
        if mode == 'selective_mask_t':
            if non_peaks is None:
                print('Please give the non peaks')
            else:
                p = np.poly1d(np.polyfit(non_peaks[:, 0], non_peaks[:, 1], 5))
                baseline_handle = self.ax1.plot(self.x, p(self.x), '--')
        if mode == 'selective_mask_mc':
            if non_peaks is None:
                print('Please give the non peaks')
            else:
                fitresult, _ = curve_fit(fit_background, non_peaks[:, 0], non_peaks[:, 1])
                yy = fit_background(self.x, *fitresult)
                self.ax1.plot(self.x, yy, '--')

        if plot_no_back:
            mask_2 = params_2['mask']
            self.mask_f = np.full((len(self.mc_tof)), False)
            for i in range(len(mask_2)):
                if mask_2[i]:
                    step_loc = np.min(self.mc_tof) + bin * i
                    mask_t = np.logical_and((self.mc_tof < step_loc + bin), (self.mc_tof > step_loc))
                    self.mask_f = np.logical_or(self.mask_f, mask_t)
            self.background_ppm = (len(self.mask_f[self.mask_f == True]) * 1e6 / len(self.mask_f)) / np.max(self.mc_tof)

        if plot_no_back:
            if plot:
                self.ax1.plot(self.bins[:-1], fit_2, label='class', color='r')
                ax3 = self.ax1.twiny()
                ax3.axis("off")
                ax3.plot(fit_1, label='aspls', color='black')

            mask_2 = params_2['mask']
            if patch:
                self.ax1.plot(self.bins[:-1][mask_2], self.y[mask_2], 'o', color='orange')[0]

        return self.mask_f

    def adjust_labels(self):
        adjust_text(self.peak_annotates, arrowprops=dict(arrowstyle='-', color='red', lw=0.5))

    def zoom_to_x_range(self, x_min, x_max, reset=False):
        """
        Zoom the plot to a specific range of x-values.

        Args:
            x_min (float): Minimum x-value for the zoomed range.
            x_max (float): Maximum x-value for the zoomed range.
            reset (bool): If True, reset the zoom to the full range.
        """
        if reset:
            """Reset the plot to the original view."""
            if self.original_x_limits is not None:
                self.ax.set_xlim(self.original_x_limits)
                self.fig.canvas.draw()
        else:
            self.ax.set_xlim(x_min, x_max)
            self.fig.canvas.draw()

    def save_fig(self, label, fig_name):
        if label == 'mc':
            plt.savefig(self.variables.result_path + "//mc_%s.svg" % fig_name, format="svg", dpi=600)
            plt.savefig(self.variables.result_path + "//mc_%s.png" % fig_name, format="png", dpi=600)
        elif label == 'tof':
            plt.savefig(self.variables.result_path + "//tof_%s.svg" % fig_name, format="svg", dpi=600)
            plt.savefig(self.variables.result_path + "//tof_%s.png" % fig_name, format="png", dpi=600)


def hist_plot(variables, bin_size, log, target, mode, prominence, distance, percent, selector, figname, lim,
              peaks_find_plot, range_plot=False, selected_area=False, print_info=True):
    """
    Plot the mass spectrum or tof spectrum. It is helper function for tutorials.
    Args:
        variables (object): Variables object.
        bin_size (float): Bin size for the histogram.
        target (str): 'mc' for mass spectrum or 'tof' for tof spectrum.
        mode (str): 'normal' for normal histogram or 'normalized' for normalized histogram.
        prominence (float): Prominence for the peak_x finding.
        distance (float): Distance for the peak_x finding.
        percent (float): Percent for the peak_x finding.
        selector (str): Selector for the peak_x finding.
        figname (str): Figure name.
        lim (float): Limit for the histogram.
        peaks_find_plot (bool): Plot the peaks.
        selector (str): Selector for the peak_x finding.
        range_plot (bool): Plot the range.
        selected_area (bool): Plot the selected area.
        print_info: Print the information about the peaks.
    Returns:
        None

    """
    if target == 'mc':
        hist = variables.mc_calib
        label = 'mc'
    elif target == 'mc_c':
        hist = variables.mc_c
        label = 'mc'
    elif target == 'tof':
        hist = variables.dld_t_calib
        label = 'tof'
    elif target == 'tof_c':
        hist = variables.dld_t_c
        label = 'tof'
    if selector == 'peak':
        variables.peaks_idx = []

    if selected_area:
        mask_spacial = (variables.x >= variables.selected_x1) & (variables.x <= variables.selected_x2) & \
                       (variables.y >= variables.selected_y1) & (variables.y <= variables.selected_y2) & \
                       (variables.z >= variables.selected_z1) & (variables.z <= variables.selected_z2)
    else:
        mask_spacial = np.ones(len(hist), dtype=bool)

    hist = hist[mask_spacial]

    if range_plot:
        steps = 'bar'
    else:
        steps = 'stepfilled'
    if target == 'mc' or target == 'mc_c':
        mc_hist = AptHistPlotter(hist[hist < lim], variables)
        y, x = mc_hist.plot_histogram(bin_width=bin_size, mode=mode, label=label, steps=steps, log=log, fig_size=(9, 5))
    elif target == 'tof' or target == 'tof_c':
        mc_hist = AptHistPlotter(hist[hist < lim], variables)
        y, x = mc_hist.plot_histogram(bin_width=bin_size, mode=mode, label=label, steps=steps, log=log, fig_size=(9, 5))

    if mode != 'normalized' and peaks_find_plot and not range_plot:
        peaks, properties, peak_widths, prominences = mc_hist.find_peaks_and_widths(prominence=prominence,
                                                                                    distance=distance, percent=percent)
        mc_hist.plot_peaks()
        mc_hist.plot_hist_info_legend(label='mc', bin=0.1, background=None, loc='right')
    else:
        peaks = None
        peak_widths = None
        prominences = None

    mc_hist.selector(selector=selector)  # rect, peak_x, range
    if range_plot:
        mc_hist.plot_range(variables.range_data, legend=True)
        # mc_hist.plot_color_legend(loc='center right')

    mc_hist.save_fig(label=mode, fig_name=figname)

    if peaks is not None and print_info:
        index_max_ini = np.argmax(prominences[0])
        mrp = (prominences[0][index_max_ini] / (peak_widths[3][index_max_ini] - peak_widths[2][index_max_ini]))
        print('Mass resolving power for the highest peak_x at peak_x index %a (MRP --> m/m_2-m_1):' % index_max_ini,
              mrp)
        for i in range(len(peaks)):
            print('Peaks ', i,
                  'is at location and height: ({:.2f}, {:.2f})'.format(x[int(peaks[i])], prominences[0][i]),
                  'peak_x window sides ({:.1f}-maximum) are: ({:.2f}, {:.2f})'.format(percent,
                                                                                      x[int(peak_widths[2][i])],
                                                                                      x[int(peak_widths[3][i])]),
                  '-> MRP: {:.2f}'.format(x[int(peaks[i])] / (x[int(peak_widths[3][i])] - x[int(peak_widths[2][i])])))
