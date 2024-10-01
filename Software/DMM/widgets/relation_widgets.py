import logging
from typing import List, Union

import pyqtgraph as pg
from PyQt5 import QtCore
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from .dmm_widgets import DMMDataWidget, DMMWidgetHolder, EquationWidget


class RelationWidgetHolder(QScrollArea):
    """
    This widget contains the widgets for the cross-relations
    """

    def __init__(self, main_window, dmm_widget_holder: DMMWidgetHolder):
        super().__init__()
        self.main_window = main_window
        self.dmm_widget_holder = dmm_widget_holder

        self.relation_widgets: List[DMMRelationWidget] = []

        # Create a vertical scrollable layout
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setWidgetResizable(True)

        self.vertical_layout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(self.vertical_layout)
        self.setWidget(widget)

    def add_relation_widget(
        self, x_widget: Union[DMMDataWidget, EquationWidget], y_widget: Union[DMMDataWidget, EquationWidget]
    ):
        relation_widget = DMMRelationWidget(self, x_widget, y_widget)
        self.relation_widgets.append(relation_widget)
        self.vertical_layout.addWidget(relation_widget)

    def remove_relation_widget(self, relation_widget):
        # Remove a relation widget
        try:
            self.relation_widgets.remove(relation_widget)
        except ValueError:
            pass
        relation_widget.setParent(None)
        relation_widget.deleteLater()

    def remove_all_relation_widgets(self):
        # Remove all relation widgets
        [self.remove_relation_widget(relation_widget) for relation_widget in self.relation_widgets]

    def update_relation_selects(self):
        # Update the dropdown menus in the cross-relation widgets for the available DMM's
        # For the amount of DMM's currently connected
        N_dmms = len(self.dmm_widget_holder.dmm_widgets)
        N_equations = len(self.dmm_widget_holder.equation_widgets)

        if N_dmms > 0:
            [relation_widget.update_relation_selects() for relation_widget in self.relation_widgets]
        else:
            # If the amount of DMMs is equal to 0, remove all cross-relation widgets
            self.remove_all_relation_widgets()

    def update_interface(self):
        # Update the data in the cross-relation widgets
        for relation_widget in self.relation_widgets:
            relation_widget.update_interface()


class DMMRelationWidget(QWidget):
    """
    This widget plots the cross-relations between 2 DMM's
    """

    def __init__(
        self,
        relation_widget_holder: RelationWidgetHolder,
        x_widget: Union[DMMDataWidget, EquationWidget],
        y_widget: Union[DMMDataWidget, EquationWidget],
    ):
        super().__init__()

        self.relation_widget_holder = relation_widget_holder

        self.x_widget = x_widget
        self.y_widget = y_widget

        self.x_widget_select = QComboBox(self)  # The first dropdown menu (corresponding to the x-axis)
        self.y_widget_select = QComboBox(self)  # The second dropdown menu (corresponding to the y-axis)

        # Connect the dropdown menus to functions
        self.x_widget_select.activated.connect(self.update_relation)
        self.y_widget_select.activated.connect(self.update_relation)

        self.vs_label = QLabel("VS")
        self.vs_label.setMaximumWidth(12)

        # Create the plot widget
        plot_widget = pg.PlotWidget()
        self.plot_item = plot_widget.getPlotItem()
        self.plot_item.plot(pen=(100, 100, 100), symbol="o", symbolBrush=(0, 0, 0), symbolSize=5)

        # Create the remove button
        self.remove_button = QPushButton("X")
        self.remove_button.setMaximumWidth(30)
        self.remove_button.clicked.connect(self.remove_relation_widget)

        # Create layout for the top bar with buttons
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.x_widget_select)
        top_layout.addWidget(self.vs_label)
        top_layout.addWidget(self.y_widget_select)
        top_layout.addWidget(self.remove_button)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(plot_widget)

        # Update the dropdown menu
        self.update_relation_selects()
        self.setLayout(layout)

    def update_interface(self):
        self.update_axis()
        self.update_graph()

    def update_relation(self):
        # Update the indices when the dropdowns are changed
        for widget in (
            self.relation_widget_holder.dmm_widget_holder.dmm_widgets
            + self.relation_widget_holder.dmm_widget_holder.equation_widgets
        ):
            if str(widget) == self.x_widget_select.currentText():
                self.x_widget = widget
            if str(widget) == self.y_widget_select.currentText():
                self.y_widget = widget
        self.update_interface()

    def update_axis(self):
        x_label = str(self.x_widget)
        y_label = str(self.y_widget)

        self.plot_item.setLabels(bottom=x_label, left=y_label)

    def update_graph(self):
        try:
            self.plot_item.listDataItems()[0].setData(self.x_widget.y_array, self.y_widget.y_array)
        except Exception as e:
            logging.exception(e)

    def update_relation_selects(self):
        self.x_widget_select.clear()
        self.y_widget_select.clear()

        for widget in (
            self.relation_widget_holder.dmm_widget_holder.dmm_widgets
            + self.relation_widget_holder.dmm_widget_holder.equation_widgets
        ):
            self.x_widget_select.addItem(str(widget))
            self.y_widget_select.addItem(str(widget))
        self.x_widget_select.setCurrentText(str(self.x_widget))
        self.y_widget_select.setCurrentText(str(self.y_widget))

    def remove_relation_widget(self):
        # remove the relation widget.
        self.relation_widget_holder.remove_relation_widget(self)
