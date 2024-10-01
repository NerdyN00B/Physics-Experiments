import time
from typing import List

import numpy as np
import pyqtgraph as pg
import sympy as sp
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
                             QVBoxLayout, QWidget)

from dmm import DMM, DMMHandler
from utils import MeasurementType

MAX_DATA_POINTS = 4096

class DMMWidgetHolder(QScrollArea):
    """
    This widget holds all the DMM widgets and the equation widgets (left side of the main window).
    """

    def __init__(self, main_window, handler: DMMHandler):
        super().__init__()
        self.handler = handler
        self.main_window = main_window

        self.dmm_widgets: List[DMMDataWidget] = []
        self.equation_widgets: List[EquationWidget] = []

        # Create a vertical scrollable layout
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setWidgetResizable(True)

        self.vertical_layout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(self.vertical_layout)
        self.setWidget(widget)

    def add_dmm(self, dmm: DMM):
        dmm_widget = DMMDataWidget(self, dmm, len(self.dmm_widgets))
        self.vertical_layout.addWidget(dmm_widget)
        self.dmm_widgets.append(dmm_widget)

        # Update the dropdown selections for the cross-relation widgets
        self.main_window.update_relation_selects()

    def add_equation(self, equation):
        equation_widget = EquationWidget(self, equation, len(self.equation_widgets))
        self.vertical_layout.addWidget(equation_widget)
        self.equation_widgets.append(equation_widget)

        # Update the dropdown selections for the cross-relation widgets
        self.main_window.update_relation_selects()

    def update_interface(self):
        self.update_labels()

        # Update all DMM widgets
        for dmm_widget in self.dmm_widgets:
            dmm_widget.update_interface()

        # Update all equation widgets
        for equation_widget in self.equation_widgets:
            equation_widget.update_interface()

    def update_labels(self):
        for i, dmm_widget in enumerate(self.dmm_widgets):
            dmm_widget.update_label(i)

        for i, equation_widget in enumerate(self.equation_widgets):
            equation_widget.update_index(i)

    def remove_dmm_widget(self, dmm_widget):
        # Close/Remove the DMM itself
        self.handler.dmms.remove(dmm_widget.dmm)
        # Remove the widget
        self.vertical_layout.removeWidget(dmm_widget)
        self.dmm_widgets.remove(dmm_widget)
        dmm_widget.setParent(None)
        dmm_widget.deleteLater()

        # Update the GUI and update the cross-correlation dropdown menu
        self.update_labels()
        self.main_window.update_relation_selects()

    def remove_all_dmm_widgets(self):
        for dmm_widget in self.dmm_widgets:
            self.remove_dmm_widget(dmm_widget)

    def remove_equation_widget(self, equation_widget):
        # Remove the widget
        self.equation_widgets.remove(equation_widget)
        equation_widget.setParent(None)
        equation_widget.deleteLater()

        # Update the GUI and update the cross-correlation dropdown menu
        self.update_labels()
        self.main_window.update_relation_selects()

    def clear_measurement(self):
        for dmm_widget in self.dmm_widgets:
            dmm_widget.clear_data()

        for equation_widget in self.equation_widgets:
            equation_widget.update_data()

    def update_data(self) -> bool:
        """
        Update the data of all the DMMs and equations. Return False if a DMM fails to update else True.
        """
        for dmm_widget in self.dmm_widgets:
            if not dmm_widget.update_data():
                return False

        for equation_widget in self.equation_widgets:
            equation_widget.update_data()
        return True


class DMMDataWidget(QWidget):
    """
    This widget handles the measurements and data of one DMM.
    """

    def __init__(self, dmm_widget_holder: DMMWidgetHolder, dmm: DMM, index: int):
        super().__init__()

        self.dmm_widget_holder = dmm_widget_holder
        self.index = index
        self.dmm = dmm

        # Get a datapoint from the DMM to make sure the DMM works properly
        dmm.get_data_point()

        self.x_array = []  # array containing x data
        self.y_array = []  # array containing y data

        # Add the label containing the index number of the DMM
        self.index_label = QLabel("DMM{0}".format(self.index + 1))
        self.index_label.setMaximumWidth(30)

        self.id_label = QLabel(str(self.dmm.get_fingerprint()))  # add ID of the DMM
        self.id_label.setAlignment(QtCore.Qt.AlignLeft)

        # Configure the dropdown menu containing all the measurements
        self.measurement_select_input = QComboBox(self)

        for i, measurement_type in enumerate(MeasurementType):
            self.measurement_select_input.addItem(measurement_type.name)
            if dmm.measurement_type == measurement_type:
                self.measurement_select_input.setCurrentIndex(i)

        self.measurement_select_input.activated[str].connect(self.set_measurement)

        # Configure the remove button
        self.remove_button = QPushButton("X")
        self.remove_button.setMaximumWidth(30)
        self.remove_button.clicked.connect(self.remove)

        # Configure the identiy/reset button
        # (Identifying the DMM will actually just reset it)
        self.identify_button = QPushButton("Identify")
        self.identify_button.setMaximumWidth(100)
        self.identify_button.clicked.connect(self.identify)

        # Create the plot widget
        self.plot_widget = pg.PlotWidget()
        # Set minimum height to make sure the plot is visible
        self.plot_widget.setMinimumHeight(200)
        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.plot(pen=(100, 100, 100), symbol="o", symbolBrush=(0, 0, 0), symbolSize=5)
        self.update_axis()

        # Create the top row of buttons
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.index_label)
        top_layout.addWidget(self.measurement_select_input)
        top_layout.addWidget(self.identify_button)
        top_layout.addWidget(self.remove_button)

        # Create bottom row
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.id_label)

        # Add all the different widgets
        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.plot_widget)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def __str__(self):
        return f"DMM {self.index + 1}"

    @property
    def has_data(self):
        return len(self.x_array) > 0

    @property
    def measurement_type(self):
        return self.dmm.measurement_type

    @property
    def measurement_unit(self):
        return self.measurement_type.unit

    def update_interface(self):
        self.remove_button.setEnabled(not self.has_data)
        self.identify_button.setEnabled(not self.has_data)
        self.measurement_select_input.setEnabled(not self.has_data)

        self.update_label(self.index)
        self.update_graph()

    def identify(self):
        # Identity the DMM by resetting it
        try:
            self.dmm.reset()
            self.dmm.measurement_type = self.dmm.measurement_type
            self.dmm.get_data_point()
        except Exception as e:
            print(f"Exception occurred during device identification: {e}")
            self.removalError()

    def update_axis(self):
        measurement = self.dmm.measurement_type
        unit = measurement.unit
        self.plot_item.setLabels(bottom="Time (s)", left=f"{measurement} ({unit})")

    def update_label(self, index):
        self.index = index
        self.index_label.setText("DMM{0}".format(index + 1))

    def set_measurement(self, measurement_name):
        measurement_type = MeasurementType.__getitem__(measurement_name)
        self.dmm.measurement_type = measurement_type
        self.dmm.get_data_point()
        self.update_axis()

        # update the cross-relations
        self.dmm_widget_holder.main_window.update_relation_settings()

    def remove(self):
        # remove this DMM widget
        self.dmm_widget_holder.remove_dmm_widget(self)

    def update_data(self):
        # Update the data arrays by getting a datapoint from DMM
        try:
            value, _ = self.dmm.get_data_point()

            self.y_array.append(value)
            self.x_array.append(time.time() - self.dmm_widget_holder.main_window.measurement_start_time)

            # Remove the first element if the array is too long
            if len(self.x_array) > MAX_DATA_POINTS:
                self.x_array.pop(0)
                self.y_array.pop(0)

            return True
        except:
            self.removalError()
            return False

    def clear_data(self):
        # Clear the data
        self.x_array.clear()
        self.y_array.clear()

    def update_graph(self):
        # Update the graph
        self.plot_item.listDataItems()[0].setData(self.x_array, self.y_array)

    def removalError(self):
        # Give an error when the DMM is not connected properly anymore
        self.index_label.setStyleSheet("color : red")
        self.index_label.repaint()

        message_box = QMessageBox()
        message_box.critical(
            self,
            "Error",
            """
            The {0} (DMM{1}) device is not connected properly anymore. 
            Save your current data and reopen the program.
            """.format(
                self.dmm.__class__, self.index
            ),
        )
        message_box.exec_()


class EquationWidget(QWidget):
    def __init__(self, dmm_widget_holder, equation: str, index: int):
        super().__init__()

        self.index = index  # Set the index of this DMM

        self.dmmWidgetHolder = dmm_widget_holder
        self.set_equation(equation)

        # Keep track of the previous equation, for error managing.
        self.prev_equation = "x1"
        self.quantity = ""
        self.unit = "a.u."

        # Add the label containing the index number of the DMM
        self.dmmIndexLabel = QLabel("EQ{0}".format(self.index + 1))
        self.dmmIndexLabel.setMaximumWidth(30)

        # Configure Equation label
        self.eqLineEdit = QLineEdit(self.equation)
        self.eqLineEdit.setPlaceholderText("Equation")
        self.eqLineEdit.editingFinished.connect(self.update_properties)

        self.quantityLineEdit = QLineEdit(self.quantity)
        self.quantityLineEdit.setPlaceholderText("Quantity")
        self.quantityLineEdit.editingFinished.connect(self.update_properties)

        self.unitLineEdit = QLineEdit(self.unit)
        self.unitLineEdit.setPlaceholderText("Unit")
        self.unitLineEdit.editingFinished.connect(self.update_properties)

        self.updateButton = QPushButton("OK")
        self.updateButton.setMaximumWidth(30)
        self.updateButton.clicked.connect(self.update_properties)

        # Configure the remove button
        self.removeButton = QPushButton("X")
        self.removeButton.setMaximumWidth(30)
        self.removeButton.clicked.connect(self.remove_EQWidget)

        # Create the plot widget
        self.plotWidget = pg.PlotWidget()
        self.plotItem = self.plotWidget.getPlotItem()
        self.plotItem.plot(pen=(100, 100, 100), symbol="o", symbolBrush=(0, 0, 0), symbolSize=5)
        self.update_axis()

        # Create the top row of buttons
        topLayout = QHBoxLayout()
        topLayout.addWidget(self.dmmIndexLabel)
        topLayout.addWidget(self.eqLineEdit)
        topLayout.addWidget(self.quantityLineEdit)
        topLayout.addWidget(self.unitLineEdit)
        topLayout.addWidget(self.updateButton)
        topLayout.addWidget(self.removeButton)

        # Add all the different widgets
        vLayout = QVBoxLayout()
        vLayout.addLayout(topLayout)
        vLayout.addWidget(self.plotWidget)

        self.setLayout(vLayout)
        self.update_data()

    def __str__(self):
        return f"Equation {self.index + 1}"

    def set_equation(self, equation):
        t1, x1, t2, x2, t3, x3, t4, x4 = sp.symbols("t1 x1 t2 x2 t3 x3 t4 x4")

        self.f = sp.lambdify((t1, x1, t2, x2, t3, x3, t4, x4), sp.sympify(equation), "numpy")
        self.equation = equation

    def update_properties(self):
        try:
            self.set_equation(self.eqLineEdit.text())
        except:
            self.eqLineEdit.setText(self.equation)
            messageBox = QMessageBox()
            messageBox.warning(
                self,
                "Equation not valid",
                """
                               An invalid equation was put into the equation line. Please press the info
                               button for help.
                               """,
            )

        self.quantity = self.quantityLineEdit.text()
        self.unit = self.unitLineEdit.text()

        self.update_axis()

    def update_interface(self):
        self.update_axis()
        self.update_data()
        self.update_graph()

    def update_axis(self):
        # Update the units on the graphs
        self.plotItem.setLabels(bottom="Time (s)", left="{0} ({1})".format(self.quantity, self.unit))

    def update_index(self, index):
        # Update the index of the dmm widget
        self.index = index
        self.dmmIndexLabel.setText(str(self))

    def remove_EQWidget(self):
        # remove this DMM widget
        self.dmmWidgetHolder.remove_equation_widget(self)

    def update_data(self):
        # Update the data arrays by manipulating the data of the DMM's

        if len(self.dmmWidgetHolder.dmm_widgets) == 0:
            self.x_array = []
            self.y_array = []
            return 0

        if len(self.dmmWidgetHolder.dmm_widgets[0].x_array) == 0:
            self.x_array = []
            self.y_array = []
            return 0

        ts = []
        xs = []

        self.x_array = self.dmmWidgetHolder.dmm_widgets[0].x_array

        for i in range(4):
            if i < len(self.dmmWidgetHolder.dmm_widgets):
                ts.append(np.array(self.dmmWidgetHolder.dmm_widgets[i].x_array))
                xs.append(np.array(self.dmmWidgetHolder.dmm_widgets[i].y_array))

                if "t" + str(i + 1) in self.equation or "x" + str(i + 1) in self.equation:
                    self.x_array = self.dmmWidgetHolder.dmm_widgets[i].x_array
            else:
                ts.append(np.zeros(len(ts[0])))
                xs.append(np.zeros(len(xs[0])))

        self.y_array = self.f(ts[0], xs[0], ts[1], xs[1], ts[2], xs[2], ts[3], xs[3])

        return

    def update_graph(self):
        # Update the graph
        if self.equation != self.prev_equation:
            try:
                self.plotItem.listDataItems()[0].setData(self.x_array, self.y_array)
                self.prev_equation = self.equation
            except:
                self.set_equation(self.prev_equation)
                self.eqLineEdit.setText(self.prev_equation)
                messageBox = QMessageBox()
                messageBox.warning(
                    self,
                    "Equation not valid",
                    """
                                   An invalid equation was put into the equation line. Please press the info
                                   button for help.
                                   """,
                )
        else:
            self.plotItem.listDataItems()[0].setData(self.x_array, self.y_array)
