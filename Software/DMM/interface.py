import logging
import os
import sys
import time
from typing import Optional, TextIO, Union

import nidaqmx as dx
import numpy as np
import pyqtgraph as pg
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox
from nidaqmx._lib import DaqNotFoundError

from dmm import DMMHandler
from utils import MeasurementType, get_available_mydaq_devices
from widgets import DMMDataWidget, DMMWidgetHolder, EquationWidget, RelationWidgetHolder

CSV_FILE_FILTER = "Comma-Seperated Values (*.csv)"
FILE_FILTERS = [CSV_FILE_FILTER, ]

try:
    get_available_mydaq_devices()
    NIDAQMX_AVAILABLE = True
except DaqNotFoundError:
    logging.warning("NI myDAQ not supported on this system.")
    NIDAQMX_AVAILABLE = False

# Set some settings for the GUI
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")
pg.setConfigOptions(antialias=True)

# Configure logging.
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("PyQt5").setLevel(logging.WARNING)
logging.getLogger("pyvisa").setLevel(logging.WARNING)

# The file directory is used to find UI files.
working_directory, py_file = os.path.split(os.path.realpath(__file__))
logging.debug(f"Working directory: {working_directory}")
# Load the UI file.
ui_file = os.path.join(working_directory, py_file.replace(".py", ".ui"))
logging.debug(f"UI file: {ui_file}")


class DMMApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi(ui_file, self)

        self.handler = DMMHandler()

        # Add a timer for the measurements of the DMMs
        self.data_timer = pg.QtCore.QTimer()
        self.data_timer.setInterval(0)  # 0 ms means as fast as possible
        self.data_timer.timeout.connect(self.update_data)
        # Add a timer to periodically update the interface
        self.interface_timer = pg.QtCore.QTimer()
        self.interface_timer.setInterval(1000 // 10)
        self.interface_timer.timeout.connect(self.update_interface)
        self.interface_timer.start()

        self.is_measuring: bool = False
        self.measurement_start_time: int = 0
        self.decimals: int = 15

        self.last_save_directory: str = r"P:\Profile"
        self.save_file: Optional[TextIO] = None

        self.mydaq_task: Optional[dx.Task] = None
        self.mydaq_current_iteration: int = 0

        # Connect interface buttons
        self.toggle_measurement_button.clicked.connect(self.toggle_measurement)
        self.clear_data_button.clicked.connect(self.clear_measurement)
        self.add_dmm_button.clicked.connect(self.add_dmm)
        self.add_equation_button.clicked.connect(self.add_equation_widget)
        self.add_cross_correlation_button.clicked.connect(self.add_cross_correlation_widget)
        self.show_equation_info_button.clicked.connect(self.show_equation_info_dialog)

        # Add the different measurement_type quantities to the dropdown menu
        for measurement_type in MeasurementType:
            self.addDMMmeasurementSelect.addItem(measurement_type.name)

        # Initialize the widget which holds the DMM widgets
        self.dmm_widget_holder = DMMWidgetHolder(self, self.handler)
        self.dmm_layout.addWidget(self.dmm_widget_holder)

        # Initialize the widget which holds the cross-correlation widgets
        self.relation_widget_holder = RelationWidgetHolder(self, self.dmm_widget_holder)
        self.relation_layout.addWidget(self.relation_widget_holder)

        # Initialize the interface
        self.show()
        self.update_interface()

    def toggle_measurement(self):
        if self.is_measuring:
            self.stop_measurement()
        else:
            self.start_measurement()
        self.update_interface()

    def update_interface(self):
        """
        Updates all interactive elements in the interface based on the current state (whether we are measuring and if we
        have data).
        """
        self.update_toggle_measurement_button()
        self.update_add_dmm_button()
        self.update_change_settings_note_text()
        self.update_clear_data_button()
        self.update_mydaq_controls()

        self.dmm_widget_holder.update_interface()
        self.relation_widget_holder.update_interface()

    def update_toggle_measurement_button(self):
        if self.is_measuring:
            self.toggle_measurement_button.setText("Stop measurement")
            self.toggle_measurement_button.setStyleSheet("background-color: 'red'")
        else:
            self.toggle_measurement_button.setText("Start measurement")
            self.toggle_measurement_button.setStyleSheet("background-color: 'green'")

    def update_add_dmm_button(self):
        self.add_dmm_button.setEnabled(not self.has_data)

    def update_change_settings_note_text(self):
        self.changeSettingsNote.setHidden(not self.has_data)

    def update_clear_data_button(self):
        self.clear_data_button.setEnabled(not self.is_measuring)

    def update_mydaq_controls(self):
        self.mydaq_start_voltage_input.setEnabled(not self.is_measuring and NIDAQMX_AVAILABLE)
        self.mydaq_stop_voltage_input.setEnabled(not self.is_measuring and NIDAQMX_AVAILABLE)
        self.mydaq_step_voltage_input.setEnabled(not self.is_measuring and NIDAQMX_AVAILABLE)
        self.mydaq_name_input.setEnabled(False)

        available_mydaqs = get_available_mydaq_devices() if NIDAQMX_AVAILABLE else []
        if available_mydaqs:
            if not self.is_measuring:
                self.mydaq_name_input.setText(available_mydaqs[0])
            self.mydaq_enable_checkbox.setEnabled(not self.is_measuring and NIDAQMX_AVAILABLE)
        else:
            self.mydaq_name_input.setText("No MyDAQ found")
            self.mydaq_enable_checkbox.setEnabled(False)
            self.mydaq_enable_checkbox.setChecked(False)

    def add_dmm(self):
        self.add_dmm_button.setText("Loading...")
        self.add_dmm_button.setEnabled(False)
        self.add_dmm_button.repaint()

        measurement_type_name = self.addDMMmeasurementSelect.currentText()
        measurement_type = MeasurementType.__getitem__(measurement_type_name)

        dmm = self.handler.add_DMM(measurement_type)
        if dmm:
            self.dmm_widget_holder.add_dmm(dmm)
        else:
            message = QMessageBox()
            message.warning(self, "No devices detected", "Unable to detect any additional DMMs.")
            message.exec_()

        self.add_dmm_button.setText("Add DMM")
        self.add_dmm_button.setEnabled(True)
        self.add_dmm_button.repaint()

    def add_equation_widget(self):
        try:
            equation = self.equation_input.text()
            self.dmm_widget_holder.add_equation(equation)
        except:
            message = QMessageBox()
            message.warning(self, "Invalid equation", "The equation you entered is invalid.")
            message.exec_()

    def get_widget_from_name(self, name: str) -> Optional[Union[DMMDataWidget, EquationWidget]]:
        for widget in self.dmm_widget_holder.dmm_widgets + self.dmm_widget_holder.equation_widgets:
            if str(widget) == name:
                return widget
        return None

    def add_cross_correlation_widget(self):
        x_widget_name = self.relationSelect1.currentText()
        y_widget_name = self.relationSelect2.currentText()

        x_widget = self.get_widget_from_name(x_widget_name)
        y_widget = self.get_widget_from_name(y_widget_name)

        self.relation_widget_holder.add_relation_widget(x_widget, y_widget)

    def update_relation_selects(self):
        # Clear the dropdown menus
        self.relationSelect1.clear()
        self.relationSelect2.clear()

        for widget in self.dmm_widget_holder.dmm_widgets + self.dmm_widget_holder.equation_widgets:
            self.relationSelect1.addItem(str(widget))
            self.relationSelect2.addItem(str(widget))

    def start_measurement(self):
        if not self.dmm_widget_holder.dmm_widgets:
            message = QMessageBox()
            message.warning(
                self, "No devices configured", "You must configure at least one DMM before starting a measurement."
            )
            message.exec_()
            return

        if self.is_measuring:
            logging.warning("Measurement already running.")
            return

        # If this is the first time retrieving data, set the start time
        if not self.has_data:
            self.measurement_start_time = time.time()

        self.select_save_file()
        self.data_timer.start()
        self.is_measuring = True

    def stop_measurement(self):
        self.data_timer.stop()
        self.is_measuring = False

        if self.save_file and not self.save_file.closed:
            self.save_file.close()
        self.save_file = None

    def clear_measurement(self):
        if self.is_measuring:
            self.stop_measurement()

        # Tell the DMM widgets that measurement_type has been cleared
        self.dmm_widget_holder.clear_measurement()

        self.relation_widget_holder.update_interface()
        self.update_interface()

    def update_data(self):
        # Update the data of each DMM widget
        self.update_mydaq()
        if not self.dmm_widget_holder.update_data():
            self.stop_measurement()
        else:
            self.write_data()
        self.relation_widget_holder.update_interface()

    def write_data(self):
        data = self.get_data()
        data = ",".join([f"{value:.{self.decimals}f}" for value in data]) + "\n"
        self.save_file.write(data)

    def update_mydaq(self):
        if not self.is_measuring or not self.mydaq_enable_checkbox.isChecked():
            # Stop the MyDAQ task if it is running.
            if self.mydaq_task:
                logging.info("Closing MyDAQ task.")
                try:
                    self.mydaq_task.write(0, auto_start=True)
                except dx.errors.DaqError:
                    logging.warning("Unable to set MyDAQ voltage to 0.")
                self.mydaq_task.close()
                self.mydaq_task = None
            return

        if not self.mydaq_task:
            logging.info("Creating MyDAQ task.")
            # Create a new MyDAQ task.
            self.mydaq_task = dx.Task()
            self.mydaq_task.ao_channels.add_ao_voltage_chan(self.mydaq_name_input.text() + "/ao0")
            self.mydaq_task.write(0, auto_start=True)
            self.mydaq_current_iteration = 0

        start_voltage = self.mydaq_start_voltage_input.value()
        stop_voltage = self.mydaq_stop_voltage_input.value()
        step_voltage = self.mydaq_step_voltage_input.value()
        samples = np.linspace(start_voltage, stop_voltage, int(abs((stop_voltage - start_voltage) / step_voltage)) + 1)

        # Write a single sample to the MyDAQ task.
        logging.debug(f"Setting MyDAQ to {samples[self.mydaq_current_iteration]:.2f} V.")
        try:
            self.mydaq_task.write(samples[self.mydaq_current_iteration], auto_start=True)
            self.mydaq_current_iteration = (self.mydaq_current_iteration + 1) % len(samples)
        except dx.errors.DaqError as e:
            logging.warning(f"Error writing to MyDAQ: {e}")
            logging.info("Closing MyDAQ task.")
            self.mydaq_task.close()
            self.mydaq_task = None

    def update_relation_settings(self):
        # Update the cross-relation widgets
        self.relation_widget_holder.update_interface()

    @property
    def has_data(self) -> bool:
        return any(dmm_widget.has_data for dmm_widget in self.dmm_widget_holder.dmm_widgets)

    def get_data(self) -> list[float]:
        """
        Returns the last data point of each DMM widget as a list with the time in the first column.
        """
        data = [self.dmm_widget_holder.dmm_widgets[0].x_array[-1]]
        # Add the measurement_type values of all the DMMs in the other columns.
        for dmm_widget in self.dmm_widget_holder.dmm_widgets:
            data.append(dmm_widget.y_array[-1])
        return data

    def select_save_file(self):
        """
        Create a save dialog and let the user select an existing or new .csv file.
        """
        save_dialog_options = QFileDialog.Options()
        file, selected_filter = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save data",
            directory=self.last_save_directory,
            filter=";;".join(FILE_FILTERS),
            options=save_dialog_options,
        )

        if not file:
            logging.warning("No file specified.")
            return

        directory, file_name = os.path.split(file)
        self.last_save_directory = str(directory)

        # Check if the file already exists
        if os.path.isfile(file):
            # If the file already exists, check if the header is the same as the current header.
            with open(file) as f:
                file_header = f.readline().strip()
                own_header = self.get_csv_header()
                logging.debug(f"CSV header in file: {file_header}")
                logging.debug(f"Own CSV header:     {own_header}")

                if file_header == own_header:
                    logging.info("Header is the same as the current header. Data will be appended to the file.")
                    self.save_file = open(file, "a")
                    return
                else:
                    logging.warning("Header is different from the current header. Creating a new file.")
                    # Append the current time to the file name.
                    file_name = file_name.split(".")[0] + "_" + time.strftime("%Y%m%d-%H%M%S") + ".csv"
                    file = os.path.join(directory, file_name)
        else:
            logging.info("File does not exist. Creating a new file.")

        # Write the header to the file.
        with open(file, "w") as f:
            f.write(self.get_csv_header() + os.linesep)
        self.save_file = open(file, "a")

    def get_csv_header(self) -> str:
        header = ["Time (s)"] + [
            f"DMM {i + 1} ({dmm_widget.dmm.measurement_type})"
            for i, dmm_widget in enumerate(self.dmm_widget_holder.dmm_widgets)
        ]
        header = ",".join(header)
        return header

    def show_equation_info_dialog(self):
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Information)
        message_box.setText(
            "The package used for reading out the equations is SymPy. Therefore, the conventions of this package "
            "should be used.The datapoints of DMM1, DMM2, etc. are given by x1, x2, etc. and the time points by t1,t2, "
            "etc., respectively. A maximum of 4 DMMs can be used in the equation. Some example equations would be:"
            "\n\ncos(x1)\n\nsqrt(x1^2 + x2^2)\n\n30.84 + 2.232*x1 + 2.43*10^(-3)*x1^2 - 5.33 * 10^(-6)*x1^3"
        )
        message_box.exec_()

    def closeEvent(self, event):
        # If we are currently doing a measurement_type or if we have data, confirm if the user wants to close the
        # application.
        if self.is_measuring and not self.confirm_close_dialog():
            logging.debug("User cancelled closing the application.")
            event.ignore()
            return

        self.stop_measurement()
        self.dmm_widget_holder.remove_all_dmm_widgets()
        super().closeEvent(event)

    def confirm_close_dialog(self):
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Warning)
        message_box.setWindowTitle("Are you sure you want to close the application?")
        message_box.setText("The measurement will be stopped.")
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        button = message_box.exec_()
        return button == QMessageBox.Yes


if __name__ == "__main__":
    # here we check if there already exists an QApplication. If not we create a new one.
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    # here we create an instance of the TOO_DMM_Window class defined above
    window = DMMApplicationWindow()

    # here the application is started

    app.exec_()  # for use an in interactive shell
    # sys.exit(app.exec_()) #for use from terminal
