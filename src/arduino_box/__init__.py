import sys
import os
import random

sys.path.append(os.path.dirname(__file__))

from aqt import mw, gui_hooks
from aqt.utils import qconnect, showInfo, showWarning
from aqt.qt import *
from anki import hooks_gen
from datetime import datetime, timedelta

from connection import ArduinoConnection, ArduinoConnectionException
from settings import ArduinoBoxSettings

arduino_connection = ArduinoConnection()
# try to open a connection
for port in arduino_connection.get_available_ports():
    if arduino_connection.open_connection(port, attempts=3):
        break


def onArduinoBoxSettings() -> None:
    d = ArduinoBoxSettings(mw, arduino_connection)
    d.show()


action = QAction("Arduino box settings", mw)
qconnect(action.triggered, onArduinoBoxSettings)
mw.form.menuTools.addSeparator()
mw.form.menuTools.addAction(action)


def check_variable_reward_settings(*args):
    check = mw.col.conf.get("nextBox2Open")
    if check is None:
        # start box 2 settings
        config = mw.addonManager.getConfig(__name__)
        mw.col.conf.set("reviewCardCount", 0)
        mw.col.conf.set("minBox2Open", config["minBox2Open"])
        mw.col.conf.set("maxBox2Open", config["maxBox2Open"])
        mw.col.conf.set("nextBox2Open", config["nextBox2Open"])


gui_hooks.profile_did_open.append(check_variable_reward_settings)


def check_cooldown_settings(*args):
    check = mw.col.conf.get("cooldownStart")
    if check is None:
        config = mw.addonManager.getConfig(__name__)
        mw.col.conf.set("cooldownStart", config["cooldownStart"])
        mw.col.conf.set("cooldownEnd", config["cooldownEnd"])


gui_hooks.profile_did_open.append(check_cooldown_settings)


def check_cooldown_time():
    cooldownStart = mw.col.conf.get("cooldownStart")
    cooldownEnd = mw.col.conf.get("cooldownEnd")
    now = datetime.now()
    cooldownStart = datetime.strptime(now.strftime(
        "%Y-%m-%d") + " " + cooldownStart, "%Y-%m-%d %H:%M")
    cooldownEnd = datetime.strptime(now.strftime(
        "%Y-%m-%d") + " " + cooldownEnd, "%Y-%m-%d %H:%M")
    while cooldownEnd < cooldownStart:
        cooldownEnd += timedelta(days=1)
    if now >= cooldownStart and now <= cooldownEnd:
        # in cooldown period
        return False
    return True


def try_open_box1():
    if check_cooldown_time():
        # open box
        showInfo(
            "Congratulations, you don't have due cards! You now can take your reward")
        try:
            box_status = arduino_connection.get_box_status()
            if box_status:
                ret = arduino_connection.open_box_1()
                if ret:
                    now = datetime.now()
                    mw.col.conf.set("box1LastOpen", now.timestamp())
                    mw.col.conf.set("shouldOpen1", 0)
                else:
                    mw.col.conf.set("shouldOpen1", 1)
        except ArduinoConnectionException as e:
            mw.col.conf.set("shouldOpen1", 1)
            showWarning(e.args[0])
    else:
        now = datetime.now()
        mw.col.conf.set("box1LastOpen", now.timestamp())
        mw.col.conf.set("shouldOpen1", 1)
        showInfo(
            "You don't have due cards! You will be able to take your reward when cooldown time is over")


def check_constant_reward(*args) -> None:
    last_reward = mw.col.conf.get("box1LastOpen")  # timestamp
    now = datetime.now()
    # check if last reward was before 1 day
    if last_reward is None or (now.date() - datetime.fromtimestamp(last_reward).date()).days > 0:
        deck_tree = mw.col.sched.deck_due_tree()
        if deck_tree.learn_count == 0 and deck_tree.review_count == 0:
            try_open_box1()


gui_hooks.reviewer_did_answer_card.append(check_constant_reward)
gui_hooks.profile_did_open.append(check_constant_reward)


def try_open_box2():
    if check_cooldown_time():
        showInfo("Well done, have a little reward")
        try:
            box_status = arduino_connection.get_box_status()
            if box_status:
                ret = arduino_connection.open_box_2()
                if ret:
                    now = datetime.now()
                    mw.col.conf.set("box2LastOpen", now.timestamp())
                    mw.col.conf.set("shouldOpen2", 0)
                else:
                    mw.col.conf.set("shouldOpen2", 1)
        except ArduinoConnectionException as e:
            mw.col.conf.set("shouldOpen2", 1)
            showWarning(e.args[0])
    else:
        now = datetime.now()
        mw.col.conf.set("box2LastOpen", now.timestamp())
        mw.col.conf.set("shouldOpen2", 1)
        showInfo(
            "You don't have due cards! You will be able to take your reward when cooldown time is over")


def check_variable_reward(card, ease, early):
    if ease != 1:
        # not again
        act_count = mw.col.conf.get("reviewCardCount")
        if act_count is None:
            act_count = 0
        act_count += 1
        expected_count = mw.col.conf.get("nextBox2Open")
        print("count = ", act_count)
        print("expected = ", expected_count)
        if expected_count and act_count >= expected_count:
            try_open_box2()
            act_count = 0
            min_count = mw.col.conf.get("minBox2Open")
            max_count = mw.col.conf.get("maxBox2Open")
            if min_count and max_count:
                mw.col.conf.set(
                    "nextBox2Open", random.randint(min_count, max_count))
        mw.col.conf.set("reviewCardCount", act_count)


hooks_gen.schedv2_did_answer_review_card.append(check_variable_reward)


def check_should_open(*args):
    shouldOpen1 = mw.col.conf.get("shouldOpen1")
    if shouldOpen1:
        try_open_box1()
    shouldOpen2 = mw.col.conf.get("shouldOpen2")
    if shouldOpen2:
        try_open_box2()


gui_hooks.profile_did_open.append(check_should_open)
