import sys
import os
import pickle
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QRadioButton,
    QComboBox, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QGridLayout, QTextEdit,
    QMenuBar, QAction, QGroupBox, QTextBrowser
)
from PyQt5.QtGui import QIcon, QFont, QCursor
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal

import general
from coursera_dl import main_f
from PyQt5.QtGui import QFontDatabase

from dotenv import load_dotenv

import livedb
from threading import Thread
import webbrowser

load_dotenv()
__version__ = os.getenv("VERSION")

class MainWindow(QMainWindow):
    
    # Signals
    show_update_message = pyqtSignal(str,  str, str)
    show_notification_signal = pyqtSignal(str)       # notification HTML

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coursera Full Course Downloader")
        self.setMinimumSize(500, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint) # no maximize button
        self.setWindowIcon(QIcon("icon/icon.ico"))

        self.shouldResume = False
        self.notification = ""

        # Variables
        self.inputvardict = {
            'ca': '',
            'classname': '',
            'path': '',
            'video_resolution': '720p',
            'sl': 'English'
        }
        self.sllangschoices = general.LANG_NAME_TO_CODE_MAPPING
        self.allowed_browesers = general.ALLOWED_BROWSERS

        self.argdict = self.loadargdict() # data.bin is created if not exists
        for key in self.inputvardict:
            if key in self.argdict:
                self.inputvardict[key] = self.argdict[key]

        self.initUI()

        # signals
        self.show_update_message.connect(self.display_update_message)
        self.show_notification_signal.connect(self.show_notification)

        # connect to remote database
        Thread(target=self.connect_to_db, daemon=True).start()

    def connect_to_db(self):
        id_token = livedb.authenticate_anonymously()
        livedb.log_usage_info(id_token)

        self.notification = livedb.get_notification(id_token)
        self.show_notification_signal.emit(self.notification)  

        update_available, latest_version, latest_version_build_url, update_msg = livedb.check_for_update(id_token)
        if update_available:
            # Emit the signal with the latest_version string
            self.show_update_message.emit(latest_version, latest_version_build_url, update_msg)

    def display_update_message(self, latest_version, latest_version_build_url=None, update_msg=None):
        # This runs on the main (GUI) thread safely
        msg_box = QMessageBox(self)
        
        msg_box.setWindowTitle("Update Available")
        msg_box.setText(f"A new version ({latest_version}) is available. Please update the app. \n\n {f'Update log: {update_msg}' if update_msg else ''}")
        update_btn = msg_box.addButton("Update", QMessageBox.AcceptRole)
        later_btn = msg_box.addButton("Later", QMessageBox.RejectRole)
        # msg_box.setIcon(QMessageBox.Information)
        msg_box.exec_()

        if msg_box.clickedButton() == update_btn and latest_version_build_url:
            webbrowser.open(latest_version_build_url)
        
        # TODO: add do not show again checkbox
        # TODO: maybe close the app when update button is clicked

    def initUI(self):
        # Menu
        menubar = self.menuBar()
        menu = menubar.addMenu("Menu")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_action = QAction("Help", self)
        help_action.triggered.connect(self.show_help)
        menu.addAction(about_action)
        menu.addAction(help_action)

        # # Load Roboto font
        # font_path = os.path.join("font", "Roboto-Regular.ttf")
        # font_id = QFontDatabase.addApplicationFont(font_path)
        # if font_id != -1:
        #     family = QFontDatabase.applicationFontFamilies(font_id)[0]
        #     app_font = QFont(family, 9)
        #     QApplication.setFont(app_font)


        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        # Set a smaller spacing for the main vertical layout
        layout.setSpacing(5) # Reduced spacing between widgets
        layout.setContentsMargins(10, 10, 10, 10) # Sets margins for a layout

        # Info message
        info = QLabel(
            "<b>You must be logged in on coursera.org in a browser.</b><br>You can only download courses that you are enrolled in.\n"
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        # Browser selection widget (separate)
        browser_group = QGroupBox()
        browser_layout = QHBoxLayout()
        browser_group.setLayout(browser_layout)
        browser_label = QLabel("<i><b>Select browser where you are logged in on coursera.org:</b></i>")
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(self.allowed_browesers)
        browser_layout.addWidget(browser_label)
        browser_layout.addWidget(self.browser_combo)
        layout.addWidget(browser_group)

        grid = QGridLayout()
        layout.addLayout(grid)
        # You can also set spacing for the grid layout if needed
        # grid.setSpacing(5) # Smaller spacing within the grid

        # Course URL
        grid.addWidget(QLabel("Course Home Page URL:"), 0, 0)
        self.classname_edit = QLineEdit(self.inputvardict['classname'])
        grid.addWidget(self.classname_edit, 0, 1)

        # Download folder
        grid.addWidget(QLabel("Download Folder:"), 1, 0)
        self.path_btn = QPushButton("Select Folder")
        self.path_btn.setFixedSize(100, 20)
        self.path_btn.clicked.connect(self.getPath)
        grid.addWidget(self.path_btn, 1, 1)
        self.path_label = QLabel(self.inputvardict['path'])
        grid.addWidget(self.path_label, 2, 1)

        # Video resolution
        grid.addWidget(QLabel("Video Resolution:"), 3, 0)
        res_group = QGroupBox()
        res_layout = QHBoxLayout()
        res_group.setLayout(res_layout)
        self.res_720 = QRadioButton("720p")
        self.res_540 = QRadioButton("540p")
        self.res_360 = QRadioButton("360p")
        res_layout.addWidget(self.res_720)
        res_layout.addWidget(self.res_540)
        res_layout.addWidget(self.res_360)
        grid.addWidget(res_group, 3, 1)
        # Set checked
        if self.inputvardict['video_resolution'] == '540p':
            self.res_540.setChecked(True)
        elif self.inputvardict['video_resolution'] == '360p':
            self.res_360.setChecked(True)
        else:
            self.res_720.setChecked(True)

        # Subtitle language
        grid.addWidget(QLabel("Subtitle Language:"), 4, 0)
        self.sl_combo = QComboBox()
        self.sl_combo.addItems(sorted(self.sllangschoices.keys()))
        self.sl_combo.setFixedSize(150, 20)
        self.sl_combo.setCurrentText(self.inputvardict['sl'])
        grid.addWidget(self.sl_combo, 4, 1)

                # Download/Resume buttons
        btn_layout = QHBoxLayout()

        # Spacer to push buttons to the right
        btn_layout.addStretch(1)

        # Resume Button
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setFixedSize(100, 30)
        self.resume_btn.clicked.connect(self.resumeBtnHandler)
        btn_layout.addWidget(self.resume_btn)

        # Download Button
        self.download_btn = QPushButton("Download")
        self.download_btn.setFixedSize(100, 30)
        self.download_btn.clicked.connect(self.downloadBtnHandler)
        btn_layout.addWidget(self.download_btn)

        layout.addLayout(btn_layout)

        # Add a vertical stretch to push everything upwards
        layout.addStretch(1)

        # notification area
        self.notification_area = QTextBrowser()
        self.notification_area.setMaximumSize(500, 100)
        layout.addWidget(self.notification_area)
        self.notification_area.hide()

        # Website link
        link_label = QLabel(
            '<a href="https://coursera-downloader.rf.gd/" style="color:#0D47A1;">http://coursera-downloader.rf.gd/</a>'
        )
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label)

    def show_notification(self, notification):
        """
        Show notification in the notification area.
        If the notification is empty, hide the notification area.
        """
        self.notification = notification
        if self.notification == "":
            self.notification_area.hide()
        else:
            self.setMinimumSize(500, 400)  # Increase minimum size to accommodate notification area
            self.notification_area.setHtml(self.notification)
            self.notification_area.show()
            self.notification_area.setOpenExternalLinks(True)
            self.notification_area.setCursor(QCursor(Qt.PointingHandCursor))
            self.notification_area.anchorClicked.connect(lambda url: webbrowser.open(url.toString()))

    def show_about(self):
        about_text = """
    <b>Coursera Full Course Downloader</b><br>
    Version: {version}<br><br>
    Developed by: Touhidul Islam<br>
    Department of EEE, BUET<br>
    Email: <u>touhid3.1416@gmail.com</u>
    """.format(version=__version__)

        dlg = QMessageBox(self)
        dlg.setWindowTitle("About - Coursera Full Course Downloader")
        dlg.setTextFormat(Qt.RichText)
        dlg.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        dlg.setText(about_text)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

    def show_help(self):
        help_text = """
    <b>USING THE PROGRAM:</b><br>
    Using the program is very easy. Just enter the necessary things and hit download. Your download will start in a command prompt window. You can see the download progress in the command prompt window. It will take some moments for the processing to finish, and download to start.<br><br>
    Use CTRL+V to paste URL.<br><br>
    <b>STOP DOWNLOAD:</b><br>
    Press CTRL+C on the command prompt window.<br><br>
    <b>RESUME DOWNLOAD:</b><br>
    If you want to RESUME the download later on, just provide the same information and download folder as before, and click on the Resume button instead of download. Your download will be resumed from previous position.<br><br>
    <b>IF THE DOWNLOAD SCREEN STALLS:</b><br>
    If the download screen does not change and does not show update for some time, then click on the command prompt window and press any button, your download should resume.<br><br>
    <b>You can not download an entire specialization. For specialization enter url of the course within it.</b><br><br>
    <b>FOUND A BUG?</b> Feel free to email at <u>touhid3.1416@gmail.com</u>
    """

        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Coursera Full Course Downloader")
        dlg.setTextFormat(Qt.RichText)
        dlg.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        dlg.setText(help_text)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()
    
    def downloadBtnHandler(self):
        # load cauth code automatically and store it in inputvardict
        browser = self.browser_combo.currentText()
        cauth = general.loadcauth('coursera.org', browser)
        if cauth == "":
            QMessageBox.warning(self, "Error", "Could not load authentication from  the browser.\nPlease make sure you are logged in on coursera.org in the selected browser and running the application as administrator.")
            return
        self.inputvardict['ca'] = cauth

        # Get values from widgets
        self.inputvardict['classname'] = self.classname_edit.text()
        self.inputvardict['path'] = self.path_label.text()
        if self.res_720.isChecked():
            self.inputvardict['video_resolution'] = '720p'
        elif self.res_540.isChecked():
            self.inputvardict['video_resolution'] = '540p'
        else:
            self.inputvardict['video_resolution'] = '360p'
        self.inputvardict['sl'] = self.sl_combo.currentText()

        # check if path is valid
        if self.inputvardict['path'] == '':
            QMessageBox.warning(self, "Error", "NO FOLDER SPECIFIED. PLEASE SELECT A FOLDER")
            return

        # make argdict from inputvarlist
        self.argdict = {}
        for key, value in self.inputvardict.items():
            if key == 'classname':
                courseurl = self.inputvardict['classname']
                cname = general.urltoclassname(courseurl)
                if cname == "":
                    QMessageBox.warning(self, "Error", "INVALID COURSE NAME/ HOME PAGE URL")
                    return
                self.argdict[key] = cname
                continue
            if key == 'sl':
                langcode = self.sllangschoices[self.inputvardict['sl']]
                if langcode == '':
                    self.argdict['ignore-formats'] = "srt"
                    self.argdict[key] = 'en'
                    continue
                else:
                    self.argdict[key] = langcode
                    continue
            self.argdict[key] = value

        # save the argdict to data.bin
        self.saveargdic()

        # create command from argumentdict
        cmd = []
        self.argdict = general.move_to_first(self.argdict, 'ca')
        for item in self.argdict.items():
            if (item[0] == 'video_resolution') or (item[0] == 'path'):
                flag = '--' + item[0]
            else:
                flag = '-' + item[0]
            flag = flag.replace('_', '-')
            if not 'classname' in flag:
                cmd.append(flag)
            cmd.append(item[1])

        cmd.append('--download-quizzes')
        cmd.append('--download-notebooks')
        cmd.append('--disable-url-skipping')
        cmd.append('--unrestricted-filenames')
        cmd.append('--combined-section-lectures-nums')
        cmd.append('--jobs')
        cmd.append('1')

        if self.shouldResume:
            cmd.append("--resume")

        cmd = ' '.join(str(x) for x in cmd)
        # QMessageBox.information(self, "Download", "INITIALIZING DOWNLOAD... PRESS CTRL+C TO STOP DOWNLOAD\nCheck the console for progress.")

        try:
            main_f(cmd)
        except KeyboardInterrupt:
            QMessageBox.information(self, "Stopped", "DOWNLOAD STOPPED, YOU CAN RESUME YOUR DOWNLOAD LATER")
        except requests.exceptions.HTTPError as e:
            QMessageBox.warning(self, "HTTP Error", f"HTTP ERROR: {e}\nMAKE SURE YOU ARE LOGGED IN ON coursera.org ON CHROME OR FIREFOX AND YOU ARE ENROLLED INTO THE COURSE")
        except requests.exceptions.SSLError as e:
            QMessageBox.warning(self, "SSL Error", f"SSL ERROR: {e}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"SOMETHING WENT WRONG, PLEASE TRY AGAIN\n{e}")

    def resumeBtnHandler(self):
        self.shouldResume = True
        self.downloadBtnHandler()
        self.shouldResume = False

    def getPath(self):
        dir = QFileDialog.getExistingDirectory(self, "Select Download Folder", "")
        self.path_label.setText(dir)

    def loadargdict(self):
        dic = {i: '' for i in self.inputvardict.keys()}
        if not os.path.isfile("data.bin"):
            with open("data.bin", 'wb') as f:
                pickle.dump(dic, f)
            return dic
        else:
            with open("data.bin", 'rb') as f:
                dic = pickle.load(f)
            return dic

    def saveargdic(self):
        with open("data.bin", 'wb') as f:
            pickle.dump(self.argdict, f)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
