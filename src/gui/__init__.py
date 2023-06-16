"""PySide6"""
import asyncio

import qasync
from qasync import asyncSlot

from PySide6.QtCore import (Qt, QEvent, QObject, QTimer, Signal, Slot)
from PySide6.QtGui import (QColor, QFont, QPalette)
from PySide6.QtWidgets import (QApplication, QGridLayout, QLabel, QMainWindow, QVBoxLayout, QWidget, QPushButton)

from ..core.project_dol import ProjectDOL
from ..core.paratranz import Paratranz


class MainWindow(QMainWindow):
    def __init__(self, dol: ProjectDOL, pt: Paratranz):
        super().__init__()
        self._dol = dol
        self._pt = pt

        widget = QWidget()
        self.setCentralWidget(widget)
        self._layout = QVBoxLayout(widget)

        """ 下载按钮 """
        self._button_download_from_gitgud = QPushButton("下载源码")
        self._button_download_from_paratranz = QPushButton("下载汉化")

        self._button_create_dicts = QPushButton("更新词典")

        self._button_drop_all_dirs = QPushButton("删除所有下载的目录")
        self._button_drop_gitgud = QPushButton("删除源码")
        self._button_drop_paratranz = QPushButton("删除汉化")
        self._button_drop_dicts = QPushButton("删除词典")
        self._button_drop_temp = QPushButton("删除缓存")

        self._factory_button(self._button_download_from_gitgud, self._on_button_download_from_gitgud_clicked)
        self._factory_button(self._button_download_from_paratranz, self._on_button_download_from_paratranz_clicked)

        self._factory_button(self._button_create_dicts, self._on_button_create_dicts_clicked)

        self._factory_button(self._button_drop_all_dirs, self._on_button_drop_all_dirs_clicked)
        self._factory_button(self._button_drop_gitgud, self._on_button_drop_gitgud_clicked)
        self._factory_button(self._button_drop_paratranz, self._on_button_drop_paratranz_clicked)
        self._factory_button(self._button_drop_dicts, self._on_button_drop_dicts_clicked)
        self._factory_button(self._button_drop_temp, self._on_button_drop_temp_clicked)

    @asyncSlot()
    async def _on_button_download_from_gitgud_clicked(self):
        await self._dol.download_from_gitgud()

    @asyncSlot()
    async def _on_button_download_from_paratranz_clicked(self):
        await self._pt.download_from_paratranz()

    @asyncSlot()
    async def _on_button_create_dicts_clicked(self):
        await self._dol.create_dicts()
        await self._dol.update_dicts()

    @asyncSlot()
    async def _on_button_drop_all_dirs_clicked(self):
        await self._dol.drop_all_dirs()

    @asyncSlot()
    async def _on_button_drop_gitgud_clicked(self):
        await self._dol._drop_gitgud()

    @asyncSlot()
    async def _on_button_drop_paratranz_clicked(self):
        await self._dol._drop_paratranz()

    @asyncSlot()
    async def _on_button_drop_dicts_clicked(self):
        await self._dol._drop_dict()

    @asyncSlot()
    async def _on_button_drop_temp_clicked(self):
        await self._dol._drop_temp()

    def _factory_button(self, button: QPushButton, function):
        button.clicked.connect(function)
        self._layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)

    def closeEvent(self, event):
        loop = asyncio.get_event_loop()
        loop.stop()
        loop.close()
