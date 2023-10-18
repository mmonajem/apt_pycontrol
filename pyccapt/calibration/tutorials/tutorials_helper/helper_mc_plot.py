import ipywidgets as widgets
from IPython.display import display
from ipywidgets import Output

from pyccapt.calibration.calibration_tools import mc_plot

# Define a layout for labels to make them a fixed width
label_layout = widgets.Layout(width='200px')
def call_mc_plot(variables):
    out = Output()
    # Define widgets for fine_tune_t_0 function
    bin_size_widget = widgets.FloatText(value=0.1)
    log_widget = widgets.Dropdown(options=[('True', True), ('False', False)])
    mode_widget = widgets.Dropdown(options=[('normal', 'normal'), ('normalized', 'normalized')])
    target_widget = widgets.Dropdown(options=[('mc', 'mc'), ('tof', 'tof')])
    prominence_widget = widgets.IntText(value=10)
    distance_widget = widgets.IntText(value=100)
    lim_widget = widgets.IntText(value=400)
    percent_widget = widgets.IntText(value=50)
    figname_widget = widgets.Text(value='hist')

    # Create a button widget to trigger the function
    button_plot = widgets.Button(description="plot")

    def on_button_click(b, variables):
        # Disable the button while the code is running
        button_plot.disabled = True

        # Get the values from the widgets
        bin_size_value = bin_size_widget.value
        log_value = log_widget.value
        mode_value = mode_widget.value
        target_value = target_widget.value
        prominence_value = prominence_widget.value
        distance_value = distance_widget.value
        percent_value = percent_widget.value
        figname_value = figname_widget.value
        lim_value = lim_widget.value

        with out:  # Capture the output within the 'out' widget
            out.clear_output()  # Clear any previous output
            # Call the function
            if target_value == 'mc':
                mc_hist = mc_plot.AptHistPlotter(variables.mc_calib[variables.mc_calib < lim_value], variables)
                mc_hist.plot_histogram(bin_width=bin_size_value, mode=mode_value, label='mc', steps='stepfilled',
                                       log=log_value, fig_size=(9, 5))
            elif target_value == 'tof':
                mc_hist = mc_plot.AptHistPlotter(variables.dld_t_calib[variables.dld_t_calib < lim_value], variables)
                mc_hist.plot_histogram(bin_width=bin_size_value, mode=mode_value, label='tof', steps='stepfilled',
                                       log=log_value, fig_size=(9, 5))

            if mode_value != 'normalized':
                mc_hist.find_peaks_and_widths(prominence=prominence_value, distance=distance_value,
                                              percent=percent_value)
                mc_hist.plot_peaks()
                mc_hist.plot_hist_info_legend(label='mc', bin=0.1, background=None, loc='right')

            mc_hist.save_fig(label=mode_value, fig_name=figname_value)

        # Enable the button when the code is finished
        button_plot.disabled = False

    button_plot.on_click(lambda b: on_button_click(b, variables))

    widget_container = widgets.VBox([
        widgets.HBox([widgets.Label(value="Bin Size:", layout=label_layout), bin_size_widget]),
        widgets.HBox([widgets.Label(value="Log:", layout=label_layout), log_widget]),
        widgets.HBox([widgets.Label(value="Mode:", layout=label_layout), mode_widget]),
        widgets.HBox([widgets.Label(value="Target:", layout=label_layout), target_widget]),
        widgets.HBox([widgets.Label(value="Prominence:", layout=label_layout), prominence_widget]),
        widgets.HBox([widgets.Label(value="Distance:", layout=label_layout), distance_widget]),
        widgets.HBox([widgets.Label(value="Lim:", layout=label_layout), lim_widget]),
        widgets.HBox([widgets.Label(value="Percent:", layout=label_layout), percent_widget]),
        widgets.HBox([widgets.Label(value="Figname:", layout=label_layout), figname_widget]),
        widgets.HBox([button_plot]),
    ])

    display(widget_container)
    display(out)