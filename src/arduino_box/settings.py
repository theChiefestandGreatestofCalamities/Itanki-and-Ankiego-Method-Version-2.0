import random

from aqt import AnkiQt
from aqt.qt import *
from aqt.utils import qconnect, showWarning
from datetime import datetime

from ui.arduino_box_settings import Ui_ArduinoBox
from connection import ArduinoConnection, ArduinoConnectionException


class ArduinoBoxSettings(QDialog):
    def __init__(self, mw: AnkiQt, con: ArduinoConnection) -> None:
        super(ArduinoBoxSettings, self).__init__(mw)
        mw.garbage_collect_on_dialog_finish(self)
        self.mw = mw
        self.form = Ui_ArduinoBox()
        self.form.setupUi(self)
        self.con = con
        self.setup()

    def setup(self):
        self.form.portsComboBox.addItems(self.con.get_available_ports())
        if self.con.is_connected():
            self._show_connected()
        else:
            self._show_disconnected()
        qconnect(self.form.refreshStatusButton.clicked,
                 self._update_box_status)
        self._update_box_status()
        self._update_settings_info()
        qconnect(self.form.box2SettingsSaveButton.clicked,
                 self._save_box2_settings)
        qconnect(self.form.cooldownSave.clicked, self._save_cooldown_settings)

    def _show_connected(self):
        self.form.connectionStatusLabel.setText("Connected")
        self.form.connectionButton.setText("Disconnect")
        self._update_box_status()
        self.form.portsComboBox.setEnabled(False)
        qconnect(self.form.connectionButton.clicked,
                 self._close_connection)

    def _show_disconnected(self):
        self.form.connectionStatusLabel.setText("Disconnected")
        self.form.connectionButton.setText("Connect")
        self.form.box1StatusLabel.setText("-")
        self.form.box2StatusLabel.setText("-")
        self.form.portsComboBox.setEnabled(True)
        qconnect(self.form.connectionButton.clicked, self._open_connection)

    def _update_box_status(self):
        b1_last_open = self.mw.col.conf.get("box1LastOpen")
        if b1_last_open:
            b1_last_open = datetime.fromtimestamp(
                b1_last_open).strftime("%H:%M %m/%d/%Y")
        else:
            b1_last_open = "-"
        self.form.box1LastOpenLabel.setText(b1_last_open)

        b2_last_open = self.mw.col.conf.get("box2LastOpen")
        if b2_last_open:
            b2_last_open = datetime.fromtimestamp(
                b2_last_open).strftime("%H:%M %m/%d/%Y")
        else:
            b2_last_open = "-"
        self.form.box2LastOpenLabel.setText(b2_last_open)
        try:
            box_status = self.con.get_box_status()
            if box_status:
                b1_text = "Open" if box_status["b1_stat"] == "1" else "Closed"
                b1_text += " - " + \
                    ("Locked" if box_status["b1_lock"] == "1" else "Unlocked")
                self.form.box1StatusLabel.setText(b1_text)

                b2_text = "Open" if box_status["b2_stat"] == "1" else "Closed"
                b2_text += " - " + \
                    ("Locked" if box_status["b2_lock"] == "1" else "Unlocked")
                self.form.box2StatusLabel.setText(b2_text)
            else:
                showWarning("Error in the connection. Try again")
        except ArduinoConnectionException as e:
            self._show_disconnected()
            showWarning(e.args[0])

    def _open_connection(self):
        if self.con.open_connection(self.form.portsComboBox.currentText()):
            self._show_connected()
        else:
            showWarning("Unable to connect")

    def _close_connection(self):
        self.con.close_connection()
        self._show_disconnected()

    def _update_settings_info(self):
        actual_count = self.mw.col.conf.get("reviewCardCount")
        if actual_count is None:
            actual_count = 0
        self.form.variableRatioCountLabel.setText(str(actual_count))

        last_change = self.mw.col.conf.get("box2SettingsLastUpdate")
        last_change_str = "-"
        if last_change:
            last_change = datetime.fromtimestamp(
                last_change)
            last_change_str = last_change.strftime("%H:%M %m/%d/%Y")
        self.form.variableRatioLastUpdateLabel.setText(last_change_str)

        min_val = self.mw.col.conf.get("minBox2Open")
        max_val = self.mw.col.conf.get("maxBox2Open")
        self.form.box2MinEdit.setValue(min_val)
        self.form.box2MaxEdit.setValue(max_val)

        now = datetime.now()
        if last_change and (now - last_change).days < 30:
            self._disable_box2_settings()

        cooldownStart = self.mw.col.conf.get("cooldownStart")
        self.form.cooldownStartTimeEdit.setTime(
            QTime(*map(int, cooldownStart.split(":"))))
        cooldownEnd = self.mw.col.conf.get("cooldownEnd")
        self.form.cooldownEndTimeEdit.setTime(
            QTime(*map(int, cooldownEnd.split(":"))))

    def _disable_box2_settings(self):
        self.form.box2MinEdit.setDisabled(True)
        self.form.box2MaxEdit.setDisabled(True)
        self.form.box2SettingsSaveButton.setDisabled(True)

    def _save_box2_settings(self):
        min_val = self.form.box2MinEdit.value()
        max_val = self.form.box2MaxEdit.value()
        if max_val < min_val:
            showWarning("Max value should be greater or equal than Min")
            return
        now = datetime.now()
        self.mw.col.conf.set("reviewCardCount", 0)
        self.mw.col.conf.set("minBox2Open", min_val)
        self.mw.col.conf.set("maxBox2Open", max_val)
        self.mw.col.conf.set("box2SettingsLastUpdate", now.timestamp())
        self.mw.col.conf.set(
            "nextBox2Open", random.randint(min_val, max_val))

        self._update_settings_info()

    def _save_cooldown_settings(self):
        cooldownStart = self.form.cooldownStartTimeEdit.time()
        cooldownStart = "%s:%s" % (
            cooldownStart.hour(), cooldownStart.minute())
        self.mw.col.conf.set("cooldownStart", cooldownStart)

        cooldownEnd = self.form.cooldownEndTimeEdit.time()
        cooldownEnd = "%s:%s" % (cooldownEnd.hour(), cooldownEnd.minute())
        self.mw.col.conf.set("cooldownEnd", cooldownEnd)
