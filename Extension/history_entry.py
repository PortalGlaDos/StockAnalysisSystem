import pandas as pd
from datetime import date
from os import sys, path

from PyQt5.QtWidgets import QWidget, QMainWindow, QButtonGroup
from PyQt5.QtWidgets import QApplication, QScrollBar, QSlider, QMenu

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QStyledItemDelegate, QTreeWidgetItem, QComboBox, QInputDialog, QFileDialog

from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidget, QHBoxLayout, QTableWidgetItem, \
    QWidget, QPushButton, QDockWidget, QLineEdit, QAction, qApp, QMessageBox, QDialog, QVBoxLayout, QLabel, QTextEdit, \
    QListWidget, QShortcut

root_path = path.dirname(path.dirname(path.abspath(__file__)))

try:
    from Extension.History.core import *
    from Extension.History.editor import *
    from Extension.History.filter import *
    from Extension.History.indexer import *
    from Extension.History.viewer_ex import *
    from Extension.History.Utility.candlestick import *
    from Extension.History.Utility.history_public import *
    from Extension.History.Utility.viewer_utility import *

    from Utiltity.ui_utility import *
    from DataHub.DataHubEntry import DataHubEntry
    from DataHub.DataHubEntry import DEPENDS_INDEX
    from Database.DatabaseEntry import DatabaseEntry
    from stock_analysis_system import StockAnalysisSystem
except Exception as e:
    sys.path.append(root_path)

    from Extension.History.core import *
    from Extension.History.editor import *
    from Extension.History.filter import *
    from Extension.History.indexer import *
    from Extension.History.viewer_ex import *
    from Extension.History.Utility.candlestick import *
    from Extension.History.Utility.history_public import *
    from Extension.History.Utility.viewer_utility import *

    from Utiltity.ui_utility import *
    from DataHub.DataHubEntry import DataHubEntry
    from DataHub.DataHubEntry import DEPENDS_INDEX
    from Database.DatabaseEntry import DatabaseEntry
    from stock_analysis_system import StockAnalysisSystem
finally:
    pass


# ----------------------------------------------------------------------------------------------------------------------

class StockHistoryUi(QWidget):
    ADJUST_TAIL = 0
    ADJUST_HEAD = 1
    ADJUST_NONE = 2

    RETURN_LOG = 3
    RETURN_SIMPLE = 4

    def __init__(self, sas: StockAnalysisSystem):
        super(StockHistoryUi, self).__init__()

        self.__sas = sas
        self.__paint_securities = ''
        self.__paint_trade_data = None

        # History
        self.__history = History()
        self.__time_axis = TimeAxis()
        self.__time_axis.set_agent(self)
        self.__time_axis.set_history_core(self.__history)

        self.__thread_candlestick = TimeThreadBase()
        self.__thread_bottom = TimeThreadBase()

        # Timer for update stock list
        self.__timer = QTimer()
        self.__timer.setInterval(1000)
        self.__timer.timeout.connect(self.on_timer)
        self.__timer.start()

        # Ui component
        self.__combo_name = QComboBox()
        self.__button_ensure = QPushButton('确定')

        self.__check_memo = QCheckBox('笔记')
        self.__check_volume = QCheckBox('成交量')

        self.__radio_adj_tail = QRadioButton('后复权')
        self.__radio_adj_head = QRadioButton('前复权')
        self.__radio_adj_none = QRadioButton('不复权')
        self.__group_adj = QButtonGroup(self)

        self.__radio_log_return = QRadioButton('对数收益')
        self.__radio_simple_return = QRadioButton('算术收益')
        self.__group_return = QButtonGroup(self)

        self.__init_ui()
        self.__config_ui()

    def __init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.__group_adj.addButton(self.__radio_adj_tail)
        self.__group_adj.addButton(self.__radio_adj_head)
        self.__group_adj.addButton(self.__radio_adj_none)
        group_box_adj, group_layout = create_h_group_box('')
        group_layout.addWidget(self.__radio_adj_tail)
        group_layout.addWidget(self.__radio_adj_head)
        group_layout.addWidget(self.__radio_adj_none)

        self.__group_return.addButton(self.__radio_log_return)
        self.__group_return.addButton(self.__radio_simple_return)
        group_box_return, group_layout = create_h_group_box('')
        group_layout.addWidget(self.__radio_log_return)
        group_layout.addWidget(self.__radio_simple_return)

        group_box, group_layout = create_v_group_box('Securities')

        main_layout.addWidget(self.__time_axis, 99)
        main_layout.addWidget(group_box)

        group_layout.addLayout(horizon_layout([
            self.__combo_name, group_box_adj, group_box_return, self.__button_ensure,
            self.__check_volume, self.__check_memo
        ]))

    def __config_ui(self):
        self.__combo_name.setEditable(True)
        for key in DEPENDS_INDEX:
            self.__combo_name.addItem(key + ' | ' + DEPENDS_INDEX.get(key), key)

        self.__radio_adj_none.setChecked(True)
        self.__radio_simple_return.setChecked(True)

        self.__check_memo.clicked.connect(self.on_button_memo)
        self.__check_volume.clicked.connect(self.on_button_volume)
        self.__button_ensure.clicked.connect(self.on_button_ensure)

        self.__thread_candlestick.set_thread_min_track_width(9999)
        self.__thread_candlestick.set_thread_color(QColor(201, 211, 140))

        self.__thread_bottom.set_thread_min_track_width(9999)
        self.__thread_bottom.set_thread_color(QColor(130, 57, 53))

        self.__time_axis.set_axis_layout(LAYOUT_HORIZON)
        self.__time_axis.set_time_range(HistoryTime.years_to_seconds(2010), HistoryTime.years_to_seconds(2020))
        self.__time_axis.set_axis_time_range_limit(HistoryTime.years_to_seconds(1990), HistoryTime.now_tick())
        self.__time_axis.set_axis_scale_step(HistoryTime.TICK_LEAP_YEAR)
        self.__time_axis.set_axis_scale_step_limit(HistoryTime.TICK_DAY, HistoryTime.TICK_LEAP_YEAR * 2)

        self.__time_axis.add_history_thread(self.__thread_bottom, ALIGN_LEFT)
        self.__time_axis.add_history_thread(self.__thread_candlestick, ALIGN_RIGHT)

        self.setMinimumWidth(1280)
        self.setMinimumHeight(800)

    def on_timer(self):
        # Check stock list ready and update combobox
        data_utility = self.__sas.get_data_hub_entry().get_data_utility()
        if data_utility.stock_cache_ready():
            stock_list = data_utility.get_stock_list()
            for stock_identity, stock_name in stock_list:
                self.__combo_name.addItem(stock_identity + ' | ' + stock_name, stock_identity)
            self.__timer.stop()

    def on_button_memo(self):
        enable = self.__check_memo.isChecked()

    def on_button_volume(self):
        enable = self.on_button_volume.isChecked()

    def on_button_ensure(self):
        input_securities = self.__combo_name.currentText()
        if '|' in input_securities:
            input_securities = input_securities.split('|')[0].strip()

        if self.__radio_adj_tail.isChecked():
            adjust_method = StockHistoryUi.ADJUST_TAIL
        elif self.__radio_adj_head.isChecked():
            adjust_method = StockHistoryUi.ADJUST_HEAD
        elif self.__radio_adj_none.isChecked():
            adjust_method = StockHistoryUi.ADJUST_NONE
        else:
            adjust_method = StockHistoryUi.ADJUST_NONE

        if self.__radio_log_return.isChecked():
            return_style = StockHistoryUi.RETURN_LOG
        elif self.__radio_simple_return.isChecked():
            return_style = StockHistoryUi.RETURN_SIMPLE
        else:
            return_style = StockHistoryUi.RETURN_SIMPLE

        self.load_for_securities(input_securities, adjust_method, return_style)

    # ------------------------------- TimeAxis.Agent -------------------------------

    def on_r_button_up(self, pos: QPoint):
        pass

    # ------------------------------------------------------------------------------

    def load_for_securities(self, securities: str, adjust_method: int, return_style: int):
        if securities != self.__paint_securities or self.__paint_trade_data is None:
            if securities in DEPENDS_INDEX.keys():
                uri = 'TradeData.Index.Daily'
            else:
                uri = 'TradeData.Stock.Daily'
            trade_data = self.__sas.get_data_hub_entry().get_data_center().query(uri, securities)

            base_path = path.dirname(path.abspath(__file__))
            history_path = path.join(base_path, 'History')
            depot_path = path.join(history_path, 'depot')
            his_file = path.join(depot_path, securities + '.his')
            self.__history.load_source(his_file)

            self.__paint_trade_data = trade_data
            self.__paint_securities = securities

        if self.__paint_trade_data is None:
            return

        trade_data = pd.DataFrame()
        if adjust_method == StockHistoryUi.ADJUST_TAIL and 'adj_factor' in self.__paint_trade_data.columns:
            trade_data['open'] = self.__paint_trade_data['open'] * self.__paint_trade_data['adj_factor']
            trade_data['close'] = self.__paint_trade_data['close'] * self.__paint_trade_data['adj_factor']
            trade_data['high'] = self.__paint_trade_data['high'] * self.__paint_trade_data['adj_factor']
            trade_data['low'] = self.__paint_trade_data['low'] * self.__paint_trade_data['adj_factor']
            trade_data['trade_date'] = self.__paint_trade_data['trade_date']
        elif adjust_method == StockHistoryUi.ADJUST_HEAD and 'adj_factor' in self.__paint_trade_data.columns:
            trade_data['open'] = self.__paint_trade_data['open'] / self.__paint_trade_data['adj_factor']
            trade_data['close'] = self.__paint_trade_data['close'] / self.__paint_trade_data['adj_factor']
            trade_data['high'] = self.__paint_trade_data['high'] / self.__paint_trade_data['adj_factor']
            trade_data['low'] = self.__paint_trade_data['low'] / self.__paint_trade_data['adj_factor']
            trade_data['trade_date'] = self.__paint_trade_data['trade_date']
        else:
            trade_data = self.__paint_trade_data
        candle_sticks = build_candle_stick(trade_data)

        self.__thread_candlestick.clear()
        for candle_stick in candle_sticks:
            self.__thread_candlestick.add_axis_items(candle_stick)
        self.__thread_candlestick.refresh()


# ----------------------------------------------------------------------------------------------------------------------

def plugin_prob() -> dict:
    return {
        'plugin_id': 'b3767a36-123f-45ab-bfad-f352c2b48354',
        'plugin_name': 'History',
        'plugin_version': '0.0.0.1',
        'tags': ['History', 'Sleepy'],
    }


def plugin_adapt(method: str) -> bool:
    return method in ['widget']


def plugin_capacities() -> list:
    return [
        'widget',
    ]


# ----------------------------------------------------------------------------------------------------------------------

sasEntry = None


def init(sas: StockAnalysisSystem) -> bool:
    try:
        global sasEntry
        sasEntry = sas
    except Exception as e:
        print(e)
        return False
    finally:
        pass
    return True


def widget(parent: QWidget) -> (QWidget, dict):
    return StockHistoryUi(sasEntry), {'name': 'History', 'show': False}


















