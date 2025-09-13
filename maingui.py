__version__ = "3.0.0"

import sys, requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QRadioButton,
    QComboBox, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QGridLayout, QAction, QGroupBox, QTextBrowser
)
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal

from utils import process_notification_html
import general
from coursera_dl import main_f

import livedb
from threading import Thread
import webbrowser
from os import path


class MainWindow(QMainWindow):
    
    # Signals
    show_update_message = pyqtSignal(str,  str, str)
    show_notification_signal = pyqtSignal(str)      # notification HTML

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coursera Full Course Downloader")
        self.setMinimumSize(500, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint) # no maximize button
        icon_path = path.abspath(path.join(path.dirname(__file__), 'icon/icon.ico'))
        self.setWindowIcon(QIcon(icon_path))

        self.shouldResume = False
        self.notification = ""

        self.sllangschoices = general.LANG_NAME_TO_CODE_MAPPING
        self.allowed_browsers = general.ALLOWED_BROWSERS

        from localdb import SimpleDB
        self.localdb  = SimpleDB('data.bin')

        self.argdict = self.localdb.get_full_db()['argdict']
        
        self.initUI()

        # signals
        self.show_update_message.connect(self.display_update_message)
        self.show_notification_signal.connect(self.show_notification)

        # connect to remote database
        Thread(target=self.connect_to_db, daemon=True).start()

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
        self.browser_combo.addItems(self.allowed_browsers)
        # Set default value from localdb if present
        default_browser = self.localdb.read('browser')
        if default_browser in self.allowed_browsers:
            self.browser_combo.setCurrentText(default_browser)
        browser_layout.addWidget(browser_label)
        browser_layout.addWidget(self.browser_combo)
        layout.addWidget(browser_group)

        grid = QGridLayout()
        layout.addLayout(grid)
        # You can also set spacing for the grid layout if needed
        # grid.setSpacing(5) # Smaller spacing within the grid

        # Course URL
        grid.addWidget(QLabel("Course Home Page URL:"), 0, 0)
        self.classname_edit = QLineEdit(self.localdb.read('argdict')['classname'])
        grid.addWidget(self.classname_edit, 0, 1)

        # Download folder
        grid.addWidget(QLabel("Download Folder:"), 1, 0)
        self.path_btn = QPushButton("Select Folder")
        # self.path_btn.setFixedSize(100, 20) # FIX: Removed fixed size to allow scaling
        self.path_btn.clicked.connect(self.getPath)
        grid.addWidget(self.path_btn, 1, 1)
        self.path_label = QLabel(self.localdb.read('argdict')['path'])
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
        if self.localdb.read('argdict')['video_resolution'] == '540p':
            self.res_540.setChecked(True)
        elif self.localdb.read('argdict')['video_resolution'] == '360p':
            self.res_360.setChecked(True)
        else:
            self.res_720.setChecked(True)

        # Subtitle language
        grid.addWidget(QLabel("Subtitle Language:"), 4, 0)
        self.sl_combo = QComboBox()
        self.sl_combo.addItems(sorted(self.sllangschoices.keys()))
        # self.sl_combo.setFixedSize(150, 20) # FIX: Removed fixed size to allow scaling
        key = next((k for k, v in self.sllangschoices.items() if v == self.localdb.read('argdict')['sl']), None) # find name of langugage from lang code
        self.sl_combo.setCurrentText(key if key else 'English')  # Default to English if not found
        grid.addWidget(self.sl_combo, 4, 1)

                # Download/Resume buttons
        btn_layout = QHBoxLayout()

        # Spacer to push buttons to the right
        btn_layout.addStretch(1)

        # Resume Button
        self.resume_btn = QPushButton("Resume")
        # self.resume_btn.setFixedSize(100, 30) # FIX: Removed fixed size to allow scaling
        self.resume_btn.clicked.connect(self.resumeBtnHandler)
        btn_layout.addWidget(self.resume_btn)

        # Download Button
        self.download_btn = QPushButton("Download")
        # self.download_btn.setFixedSize(100, 30) # FIX: Removed fixed size to allow scaling
        self.download_btn.clicked.connect(self.downloadBtnHandler)
        btn_layout.addWidget(self.download_btn)

        layout.addLayout(btn_layout)

        # notification area
        self.notification_area = QTextBrowser()
        # self.notification_area.setMaximumSize(500, 100) # FIX: Changed to only set max height
        self.notification_area.setMaximumHeight(100) # FIX: Constrain height only, allowing width to be flexible
        self.notification_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.notification_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Wrap the notification area in a fixed-height container to prevent layout shifting
        self.notification_container = QWidget()
        notif_layout = QVBoxLayout()
        notif_layout.setContentsMargins(0, 0, 0, 0)
        notif_layout.addWidget(self.notification_area)
        self.notification_container.setLayout(notif_layout)
        self.notification_container.setFixedHeight(100)  # Reserve height
        layout.addWidget(self.notification_container)
        self.notification_area.setVisible(False)

        # Add a vertical stretch to push everything upwards
        layout.addStretch(1)

        # Footer label
        self.footer_msg = '<a href="https://coursera-downloader.rf.gd/" style="color:#0D47A1;">https://coursera-downloader.rf.gd/</a>'
        self.footer_label = QLabel(self.footer_msg)
        self.footer_label.setOpenExternalLinks(True)
        layout.addWidget(self.footer_label)

    # remote database connection and update check
    def connect_to_db(self):
        id_token = livedb.authenticate_anonymously()
        livedb.log_usage_info(id_token)

        self.notification = livedb.get_notification(id_token)
        self.show_notification_signal.emit(self.notification)  

        update_available, latest_version, latest_version_build_url, update_msg = livedb.check_for_update(id_token)

        if update_available:
            # Emit the signal with the latest_version string
            if self.localdb.read('show_update_prompt') != 'false':
                self.show_update_message.emit(latest_version, latest_version_build_url, update_msg)
            else:
                self.footer_msg = self.footer_msg + f'   * Update available. <a href="{latest_version_build_url}">Click to update.</a>'
                self.footer_label.setText(self.footer_msg)

    def display_update_message(self, latest_version, latest_version_build_url=None, update_msg=None):
        msg_box = QMessageBox(self)
        
        msg_box.setWindowTitle("Update Available")
        msg_box.setText(
            f"A new version ({latest_version}) is available. Please update the app."
            f"\n\n{f'Update log: {update_msg}' if update_msg else ''}"
        )

        update_btn = msg_box.addButton("Update", QMessageBox.AcceptRole)
        dont_show_again_btn = msg_box.addButton("Don't show again", QMessageBox.DestructiveRole)
        later_btn = msg_box.addButton("Later", QMessageBox.RejectRole)
        
        msg_box.exec_()

        clicked = msg_box.clickedButton()

        if clicked == update_btn and latest_version_build_url:
            webbrowser.open(latest_version_build_url)

        elif clicked == dont_show_again_btn:
            # Save preference to local database
            self.localdb.create('show_update_prompt', 'false')
        
        # TODO: add do not show again checkbox
        # TODO: maybe close the app when update button is clicked

    def show_notification(self, notification):
        """
        Show notification in the notification area.
        If the notification is empty, hide the notification area.
        """
        self.notification = notification
        if self.notification == "":
            self.notification_area.hide()
        else:
            # self.setMinimumSize(500, 400)  # FIX: Removed this line. The layout will handle resizing.
        
            # Process notification HTML to download images and replace src if there is an <img> tag
            processed_notification = process_notification_html(self.notification)

            self.notification_area.setHtml(processed_notification)
            self.notification_area.setVisible(True)
            self.notification_area.setOpenExternalLinks(True)
            self.notification_area.setCursor(QCursor(Qt.PointingHandCursor))
            self.notification_area.anchorClicked.connect(lambda url: webbrowser.open(url.toString()))

    # About and Help dialogs
    def show_about(self):
        from gui_components.about_text import get_about_text
        about_text = get_about_text(__version__)

        dlg = QMessageBox(self)
        dlg.setWindowTitle("About - Coursera Full Course Downloader")
        dlg.setTextFormat(Qt.RichText)
        dlg.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        dlg.setText(about_text)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

    def show_help(self):
        from gui_components.help_text import get_help_text
        help_text = get_help_text()

        dlg = QMessageBox(self)
        dlg.setWindowTitle("Help - Coursera Full Course Downloader")
        dlg.setTextFormat(Qt.RichText)
        dlg.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        dlg.setText(help_text)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()

    # Button handlers
    def downloadBtnHandler(self):
        # load cauth code automatically and store it in inputvardict
        browser = self.browser_combo.currentText()
        cauth = general.loadcauth('coursera.org', browser)
        if cauth == "":
            QMessageBox.warning(self, "Error", "Could not load authentication from  the browser.\nPlease make sure you are logged in on coursera.org in the selected browser and running the application as administrator.")
            return
        
        self.localdb.update('argdict.ca', cauth)

        # Get values from widgets
        self.localdb.update('browser', browser)
        self.localdb.update('argdict.classname', self.classname_edit.text())
        self.localdb.update('argdict.path', self.path_label.text())
        if self.res_720.isChecked():
            self.localdb.update('argdict.video_resolution', '720p')
        elif self.res_540.isChecked():
            self.localdb.update('argdict.video_resolution', '540p')
        else:
            self.localdb.update('argdict.video_resolution', '360p')
        self.localdb.update('argdict.sl', self.sl_combo.currentText())

        # check if path is valid
        if self.localdb.read('argdict')['path'] == '':
            QMessageBox.warning(self, "Error", "NO FOLDER SPECIFIED. PLEASE SELECT A FOLDER")
            return

        # make argdict from inputvarlist
        self.argdict = {}
        for key, value in self.localdb.get_full_db()['argdict'].items():
            if key == 'classname':
                courseurl = self.localdb.read('argdict')['classname']
                cname = general.urltoclassname(courseurl)
                if cname == "":
                    QMessageBox.warning(self, "Error", "INVALID COURSE NAME/ HOME PAGE URL")
                    return
                self.argdict[key] = cname
                continue
            if key == 'sl':
                langcode = self.sllangschoices[self.localdb.read('argdict')['sl']]
                if langcode == '':
                    self.argdict['ignore-formats'] = "srt"
                    self.argdict[key] = 'en'
                    continue
                else:
                    self.argdict[key] = langcode
                    continue
            self.argdict[key] = value

        # save the argdict to data.bin
        # self.saveargdic()
        self.localdb.update('argdict', self.argdict)

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
            cmd.append("--cache-syllabus")
        # cmd = ' '.join(str(x) for x in cmd)
        # QMessageBox.information(self, "Download", "INITIALIZING DOWNLOAD... PRESS CTRL+C TO STOP DOWNLOAD\nCheck the console for progress.")

        try:
            main_f(cmd)
        except KeyboardInterrupt:
            QMessageBox.information(self, "Stopped", "DOWNLOAD STOPPED, YOU CAN RESUME YOUR DOWNLOAD LATER")
        except requests.exceptions.ConnectionError:
            QMessageBox.warning(self, "Connection Error", "FAILED TO CONNECT TO COURSES SERVER. PLEASE CHECK YOUR INTERNET CONNECTION AND TRY AGAIN.")
        except requests.exceptions.HTTPError as e:
            QMessageBox.warning(self, "HTTP Error", f"HTTP ERROR: {e}\nMAKE SURE YOU ARE LOGGED IN ON coursera.org ON A BROWSER AND YOU ARE ENROLLED INTO THE COURSE")
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


if __name__ == "__main__":
    # FIX: Add these two lines to enable High DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())