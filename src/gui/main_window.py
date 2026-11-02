from .. import __version__
from .. import paths

import base64
import sys, requests
import tempfile
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, QRadioButton,
    QComboBox, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QTextBrowser,
    QScrollArea, QFrame, QSizePolicy, QProgressBar, QDialog, QDialogButtonBox, QToolButton,
    QSystemTrayIcon
)
from PySide6.QtGui import (
    QAction, QIcon, QCursor, QFontMetrics, QPainter, QPalette, QPixmap, QDesktopServices
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QEvent, QObject, QSize, QUrl, Qt, QProcess, QThread, QTimer, Signal, Slot

from ..core.utils import process_notification_html
from ..services import general
from .taskbar import TaskbarProgress
from . import taskbar as taskbar
from ..core import download_progress
from ..core.coursera_dl import main_f
from ..core.downloaders import format_bytes

from ..services import livedb
from threading import Thread
import webbrowser
import os
from os import path
from math import ceil
from time import monotonic


class NoWheelComboBox(QComboBox):
    """A combo box that does not change its selection on page scrolling."""

    def wheelEvent(self, event):
        event.ignore()


GITHUB_URL = "https://github.com/touhid314/Coursera-Downloader"
# GitHub's mark (Octicons "mark-github"), drawn in the theme's text color.
GITHUB_MARK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
    '<path fill="{color}" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07'
    '.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94'
    '-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66'
    '.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36'
    '-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04'
    ' 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65'
    ' 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0'
    ' 0016 8c0-4.42-3.58-8-8-8z"/></svg>'
)


def svg_icon(svg, size, device_pixel_ratio):
    pixmap = QPixmap(int(size * device_pixel_ratio), int(size * device_pixel_ratio))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(svg.encode("utf-8")).render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(device_pixel_ratio)
    return QIcon(pixmap)


class FittedTextBrowser(QTextBrowser):
    """A text browser only as tall as its text, up to max_text_height."""

    def __init__(self, max_text_height):
        super().__init__()
        self.max_text_height = max_text_height
        # Also fires when a width change re-wraps the text.
        self.document().documentLayout().documentSizeChanged.connect(self.fit_height)

    @Slot()
    def fit_height(self):
        text_height = ceil(self.document().size().height())
        self.setFixedHeight(
            min(text_height + 2 * self.frameWidth(), self.max_text_height)
        )


class DownloadWorker(QObject):
    completed = Signal()
    failed = Signal(str, str)
    finished = Signal()
    progress = Signal(object)

    def __init__(self, command):
        super().__init__()
        self.command = command

    @Slot()
    def run(self):
        download_progress.reset(self.progress.emit)
        try:
            main_f(self.command)
        except KeyboardInterrupt:
            self.failed.emit("stopped", "")
        except SystemExit:
            # argparse exits like this when it rejects the download options.
            self.failed.emit("other", "The download options were not accepted.")
        except requests.exceptions.ConnectionError as exc:
            self.failed.emit("connection", str(exc))
        except requests.exceptions.HTTPError as exc:
            self.failed.emit("http", str(exc))
        except requests.exceptions.SSLError as exc:
            self.failed.emit("ssl", str(exc))
        except Exception as exc:
            self.failed.emit("other", str(exc))
        except BaseException as exc:
            # The download code raises some errors, such as "class not found",
            # as BaseException.
            self.failed.emit("other", str(exc) or type(exc).__name__)
        else:
            self.completed.emit()
        finally:
            download_progress.reset()
            self.finished.emit()


class MainWindow(QMainWindow):
    
    # Signals
    show_update_message = Signal(str, str, str)
    show_notification_signal = Signal(str)      # notification HTML
    login_checked = Signal(str, str, object)    # cookie, source, valid?
    enrolled_courses_loaded = Signal(str, object)  # cookie, [(name, slug)]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coursera Full Course Downloader")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint) # no maximize button
        self.setWindowIcon(QIcon(paths.ICON_FILE))

        self.shouldResume = False
        self.notification = ""
        self.notification_html = ""
        self._sized = False
        self.webview_login_process = None
        self.webview_login_output = ""
        self.webview_login_result_path = None
        self.webview_login_had_result = False
        self.download_thread = None
        self.download_worker = None
        self.close_after_stop = False
        self.output_folder = ""  # folder of the current or last download
        self.reset_progress_counts()

        self.sllangschoices = general.LANG_NAME_TO_CODE_MAPPING
        from ..services.localdb import SimpleDB
        self.localdb  = SimpleDB('data.bin')

        # CAUTH is a session credential. Keep it in memory and remove any value
        # saved by older releases.
        if self.localdb.read('argdict').get('ca'):
            self.localdb.update('argdict.ca', '')
        self.cauth_cookie = ""
        self.auth_source = None
        self.rejected_cauth = set()  # login cookies Coursera refused

        self.argdict = self.localdb.get_full_db()['argdict']
        # The embedded browser is the default; afterwards the user's last
        # choice is kept.
        saved_method = self.localdb.read('login_method')
        self.login_browser = (
            saved_method
            if saved_method in general.LOGIN_METHODS
            else general.EMBEDDED_LOGIN
        )

        self.initUI()

        # signals
        self.show_update_message.connect(self.display_update_message)
        self.show_notification_signal.connect(self.show_notification)
        self.login_checked.connect(self.login_check_finished)
        self.enrolled_courses_loaded.connect(self.show_enrolled_courses)

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


        # Central widget: a scroll area so the UI stays usable (scrolls instead of
        # squashing its contents) whenever the window is smaller than the content.
        central = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(central)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.setCentralWidget(scroll)
        layout = QVBoxLayout()
        central.setLayout(layout)

        # Set a smaller spacing for the main vertical layout
        layout.setSpacing(5) # Reduced spacing between widgets
        layout.setContentsMargins(10, 10, 10, 10) # Sets margins for a layout

        # Coursera authentication is completed in the user's normal browser.
        login_group = QGroupBox("Coursera account")
        login_layout = QGridLayout(login_group)
        self.browser_combo = NoWheelComboBox()
        self.browser_combo.addItem("Embedded browser", general.EMBEDDED_LOGIN)
        for browser_name in general.ALLOWED_BROWSERS:
            self.browser_combo.addItem(browser_name.title(), browser_name)
        browser_index = self.browser_combo.findData(self.login_browser)
        if browser_index >= 0:
            self.browser_combo.setCurrentIndex(browser_index)
        self.browser_combo.currentIndexChanged.connect(self.browser_changed)

        self.login_status_label = QLabel()
        self.login_status_label.setWordWrap(True)
        self.set_login_status("Not logged in", "error")
        login_layout.addWidget(self.login_status_label, 0, 0, 1, 4)

        self.open_login_btn = QPushButton("Open Coursera login")
        self.open_login_btn.clicked.connect(self.open_coursera_login)
        self.check_login_btn = QPushButton("I've logged in")
        self.check_login_btn.clicked.connect(self.check_browser_login)
        login_layout.addWidget(QLabel("Browser:"), 1, 0)
        login_layout.addWidget(self.browser_combo, 1, 1)
        login_layout.addWidget(self.open_login_btn, 1, 2)
        login_layout.addWidget(self.check_login_btn, 1, 3)
        login_layout.setColumnStretch(1, 1)
        layout.addWidget(login_group)

        self.login_poll_timer = QTimer(self)
        self.login_poll_timer.setInterval(2000)
        self.login_poll_timer.timeout.connect(
            lambda: self.check_browser_login(silent=True)
        )
        QTimer.singleShot(0, self.restore_login)

        grid = QGridLayout()
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        # You can also set spacing for the grid layout if needed
        # grid.setSpacing(5) # Smaller spacing within the grid

        # Course: typed or pasted, or picked from the enrolled courses
        grid.addWidget(QLabel("Course:"), 0, 0)
        self.course_combo = NoWheelComboBox()
        self.course_combo.setEditable(True)
        self.course_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.course_combo.lineEdit().setPlaceholderText(
            "Pick an enrolled course or paste a course/specialization homepage URL"
        )
        # Starts empty, showing the hint, rather than the last course used.
        self.course_combo.setEditText("")
        grid.addWidget(self.course_combo, 0, 1)

        # Download folder
        grid.addWidget(QLabel("Download Folder:"), 1, 0)
        self.path_btn = QPushButton("Select Folder")
        # self.path_btn.setFixedSize(100, 20) # FIX: Removed fixed size to allow scaling
        self.path_btn.clicked.connect(self.getPath)
        grid.addWidget(self.path_btn, 1, 1)
        self.path_label = QLabel(self.localdb.read('argdict')['path'])
        self.path_label.setWordWrap(True)
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
        self.sl_combo = NoWheelComboBox()
        self.sl_combo.addItems(sorted(self.sllangschoices.keys()))
        # self.sl_combo.setFixedSize(150, 20) # FIX: Removed fixed size to allow scaling
        key = next((k for k, v in self.sllangschoices.items() if v == self.localdb.read('argdict')['sl']), None) # find name of langugage from lang code
        self.sl_combo.setCurrentText(key if key else 'English')  # Default to English if not found
        grid.addWidget(self.sl_combo, 4, 1)

                # Download/Resume/Stop buttons
        btn_layout = QHBoxLayout()

        # Spacer to push buttons to the right
        btn_layout.addStretch(1)

        # Stop Button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stopBtnHandler)
        btn_layout.addWidget(self.stop_btn)

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

        # download progress, hidden until the first download starts
        self.progress_panel = QWidget()
        progress_layout = QVBoxLayout(self.progress_panel)
        progress_layout.setContentsMargins(0, 4, 0, 4)
        progress_layout.setSpacing(4)

        title_row = QHBoxLayout()
        self.progress_title = QLabel()
        self.progress_title.setStyleSheet("font-weight: 600;")
        # Long lecture names must not widen the window.
        self.progress_title.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        title_row.addWidget(self.progress_title, 1)
        self.progress_percent = QLabel()
        self.progress_percent.setStyleSheet("font-weight: 600;")
        title_row.addWidget(self.progress_percent)
        self.open_folder_btn = QPushButton("Open folder")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.hide()
        title_row.addWidget(self.open_folder_btn)
        progress_layout.addLayout(title_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        progress_layout.addWidget(self.progress_bar)

        detail_row = QHBoxLayout()
        self.progress_detail = QLabel()
        self.progress_detail.setStyleSheet("color: #9ca3af;")
        detail_row.addWidget(self.progress_detail, 1)
        self.progress_speed = QLabel()
        self.progress_speed.setStyleSheet("font-weight: 600;")
        detail_row.addWidget(self.progress_speed)
        progress_layout.addLayout(detail_row)

        self.speed_timer = QTimer(self)
        self.speed_timer.setInterval(500)
        self.speed_timer.timeout.connect(self.update_speed)

        layout.addWidget(self.progress_panel)
        self.progress_panel.hide()

        # notification area
        self.notification_area = FittedTextBrowser(max_text_height=100)
        self.notification_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.notification_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.notification_container = QWidget()
        notif_layout = QVBoxLayout()
        notif_layout.setContentsMargins(0, 0, 0, 0)
        notif_layout.addWidget(self.notification_area)
        self.notification_container.setLayout(notif_layout)
        self.notification_container.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        layout.addWidget(self.notification_container)
        self.notification_container.setVisible(False)

        # Add a vertical stretch to push everything upwards
        layout.addStretch(1)

        # Footer label
        self.footer_msg = '<a href="https://coursera-downloader.rf.gd/">https://coursera-downloader.rf.gd/</a>'
        self.footer_label = QLabel(self.footer_msg)
        self.footer_label.setOpenExternalLinks(True)
        self.github_btn = QToolButton()
        self.github_btn.setAutoRaise(True)
        self.github_btn.setIconSize(QSize(18, 18))
        self.github_btn.setToolTip("GitHub project")
        self.github_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.github_btn.clicked.connect(lambda: webbrowser.open(GITHUB_URL))
        self.update_github_icon()
        footer_row = QHBoxLayout()
        footer_row.addWidget(self.footer_label)
        footer_row.addStretch(1)
        footer_row.addWidget(self.github_btn)
        layout.addLayout(footer_row)

        self.content_widget = central
        layout.activate()
        self.update_minimum_height()

    def update_minimum_height(self):
        """Keep the complete visible form above the window's minimum height."""
        self.setMinimumWidth(max(500, self.content_widget.sizeHint().width()))
        content_height = self.content_widget.sizeHint().height()
        menu_height = self.menuBar().sizeHint().height()
        self.setMinimumHeight(content_height + menu_height)

    def uses_embedded_login(self):
        return self.login_browser == general.EMBEDDED_LOGIN

    def browser_changed(self):
        self.login_poll_timer.stop()
        self.login_browser = self.browser_combo.currentData()
        if self.localdb.read('login_method') is None:  # settings from older versions
            self.localdb.create('login_method', self.login_browser)
        else:
            self.localdb.update('login_method', self.login_browser)
        self.cauth_cookie = ""
        self.auth_source = None
        self.set_login_status("Not logged in", "error")
        self.restore_login()

    def restore_login(self):
        """Pick up an existing login for the selected method, if there is one."""
        # Only a browser login can be re-checked by hand.
        self.check_login_btn.setVisible(not self.uses_embedded_login())
        if not self.uses_embedded_login():
            self.check_browser_login(silent=True)
            return
        saved_embedded_auth = general.load_embedded_auth()
        if saved_embedded_auth:
            self.set_auth_cookie(saved_embedded_auth, general.EMBEDDED_LOGIN)

    def set_login_status(self, text, state):
        colors = {
            "success": "#22c55e",
            "error": "#ef4444",
            "pending": "#f59e0b",
        }
        self.login_status_label.setText(text)
        self.login_status_label.setStyleSheet(
            f"color: {colors.get(state, '#f59e0b')}; font-weight: 600;"
        )

    def open_coursera_login(self):
        if self.uses_embedded_login():
            self.open_embedded_login()
            return
        if self.cauth_cookie:  # already logged in, or being checked
            return
        opened = general.open_browser(
            self.login_browser, "https://www.coursera.org/?authMode=login"
        )
        if not opened:
            self.set_login_status(
                f"Could not open {self.login_browser.title()}. Install it or select another browser.",
                "error",
            )
            return
        self.set_login_status(
            "Waiting for the Coursera login to finish in your browser…", "pending"
        )
        self.login_poll_timer.start()

    def check_browser_login(self, silent=False):
        cauth_cookie, access_error = general.loadcauth_with_error(
            "coursera.org", self.login_browser
        )
        if cauth_cookie and cauth_cookie not in self.rejected_cauth:
            self.set_auth_cookie(cauth_cookie, self.login_browser)
            return True
        if cauth_cookie:
            # Only the expired login is there. Keep waiting for a new one.
            return False

        if access_error:
            self.login_poll_timer.stop()
            self.set_login_status(access_error, "error")
            return False

        if not silent:
            self.set_login_status(
                f"No Coursera login was found in {self.login_browser.title()}. "
                "Finish logging in or select the browser you used.",
                "error",
            )
        return False

    def set_auth_cookie(self, cauth_cookie, browser):
        """Use a login cookie, once Coursera confirms that it is valid."""
        self.login_poll_timer.stop()
        self.cauth_cookie = cauth_cookie
        self.auth_source = browser
        self.set_login_status("Checking your Coursera login…", "pending")
        Thread(
            target=lambda: self.login_checked.emit(
                cauth_cookie, browser, general.check_cauth(cauth_cookie)
            ),
            daemon=True,
        ).start()

    @Slot(str, str, object)
    def login_check_finished(self, cauth_cookie, browser, valid):
        if cauth_cookie != self.cauth_cookie:
            return  # the user has switched login since
        if valid is False:
            self.login_expired()
            return
        if browser == general.EMBEDDED_LOGIN:
            general.save_embedded_auth(cauth_cookie)
        # valid is None when Coursera could not be reached. The login is kept;
        # a download will report the problem if there is one.
        self.set_login_status("Logged in", "success")
        self.load_enrolled_courses()

    def load_enrolled_courses(self):
        cauth_cookie = self.cauth_cookie

        def fetch():
            try:
                courses = general.get_enrolled_courses(cauth_cookie)
            except Exception:
                return  # the list is a convenience; typing a course still works
            self.enrolled_courses_loaded.emit(cauth_cookie, courses)

        Thread(target=fetch, daemon=True).start()

    @Slot(str, object)
    def show_enrolled_courses(self, cauth_cookie, courses):
        if cauth_cookie != self.cauth_cookie:
            return
        text = self.course_combo.currentText()
        self.course_combo.clear()
        for name, slug in courses:
            self.course_combo.addItem(name, slug)
            self.course_combo.setItemData(
                self.course_combo.count() - 1, slug, Qt.ItemDataRole.ToolTipRole
            )
        # Show a saved course by its name when it is in the list.
        index = self.course_combo.findData(text)
        if index >= 0:
            self.course_combo.setCurrentIndex(index)
        else:
            self.course_combo.setCurrentIndex(-1)
            self.course_combo.setEditText(text)

    def selected_course(self):
        """Return (text to save, slug, is_specialization) for the course field."""
        text = self.course_combo.currentText().strip()
        index = self.course_combo.findText(text, Qt.MatchFlag.MatchExactly)
        if index >= 0 and self.course_combo.itemData(index):
            slug = self.course_combo.itemData(index)
            return slug, slug, False
        slug, is_specialization = general.parse_course_input(text)
        return text, slug, is_specialization

    def login_expired(self):
        self.rejected_cauth.add(self.cauth_cookie)
        if self.auth_source == general.EMBEDDED_LOGIN:
            general.clear_embedded_auth()
        self.cauth_cookie = ""
        self.auth_source = None
        self.set_login_status(
            "Your Coursera login has expired. Click Open Coursera login to log in again.",
            "error",
        )

    def open_embedded_login(self):
        if (
            self.webview_login_process
            and self.webview_login_process.state() != QProcess.ProcessState.NotRunning
        ):
            return

        self.webview_login_output = ""
        self.webview_login_had_result = False
        result_handle, self.webview_login_result_path = tempfile.mkstemp(
            prefix="CourseraDownloader-login-", suffix=".txt"
        )
        os.close(result_handle)
        self.webview_login_process = QProcess(self)
        self.webview_login_process.readyReadStandardOutput.connect(
            self.read_webview_login_output
        )
        self.webview_login_process.finished.connect(self.webview_login_finished)

        if getattr(sys, "frozen", False):
            arguments = [
                "--webview-login", "--webview-result",
                self.webview_login_result_path,
            ]
            helper_program = sys.executable
        else:
            arguments = [
                paths.MAIN_SCRIPT, "--webview-login", "--webview-result",
                self.webview_login_result_path,
            ]
            helper_program = sys.executable
            if path.basename(helper_program).lower() == "pythonw.exe":
                helper_program = path.join(
                    path.dirname(helper_program), "python.exe"
                )

        self.set_login_status("Waiting for embedded-browser login…", "pending")
        self.webview_login_process.start(helper_program, arguments)

    def read_webview_login_output(self):
        output = bytes(
            self.webview_login_process.readAllStandardOutput()
        ).decode("utf-8", errors="replace")
        self.webview_login_output += output
        self.process_webview_login_output(self.webview_login_output)

    def process_webview_login_output(self, output):
        for line in output.splitlines():
            if line.startswith("COURsera_AUTH::"):
                self.webview_login_had_result = True
                encoded_cookie = line.split("::", 1)[1]
                cauth_cookie = base64.b64decode(encoded_cookie).decode("utf-8")
                self.set_auth_cookie(cauth_cookie, "embedded")
            elif line.startswith("COURsera_ERROR::"):
                self.webview_login_had_result = True
                encoded_error = line.split("::", 1)[1]
                error = base64.b64decode(encoded_error).decode("utf-8")
                self.set_login_status(f"Embedded login failed: {error}", "error")

    def webview_login_finished(self, exit_code, _exit_status):
        if self.webview_login_result_path:
            try:
                with open(
                    self.webview_login_result_path, "r", encoding="utf-8"
                ) as result_file:
                    self.process_webview_login_output(result_file.read())
            except OSError:
                pass
            finally:
                try:
                    os.remove(self.webview_login_result_path)
                except OSError:
                    pass
                self.webview_login_result_path = None
        if not self.cauth_cookie and not self.webview_login_had_result:
            self.set_login_status(
                "Embedded login closed before authentication completed.", "error"
            )

    def showEvent(self, event):
        super().showEvent(event)
        if not self._sized:
            self._sized = True
            self.resize(max(self.width(), 620), self.height())
            self.fit_to_content()

    def fit_to_content(self):
        """Grow the window so the whole form fits, without ever exceeding the screen."""
        needed = self.content_widget.sizeHint().height() + self.menuBar().sizeHint().height()
        available = QApplication.primaryScreen().availableGeometry().height() - 80
        if self.height() < needed:
            self.resize(self.width(), min(needed, available))

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

        update_btn = msg_box.addButton("Update", QMessageBox.ButtonRole.AcceptRole)
        dont_show_again_btn = msg_box.addButton(
            "Don't show again", QMessageBox.ButtonRole.DestructiveRole
        )
        later_btn = msg_box.addButton("Later", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()

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
            self.notification_container.hide()
        else:
            # Process notification HTML to download images and replace src if there is an <img> tag
            self.notification_html = process_notification_html(self.notification)

            self.notification_area.setHtml(self.notification_html)
            self.notification_container.setVisible(True)
            self.notification_area.setVisible(True)
            self.notification_area.setOpenExternalLinks(True)
            self.notification_area.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.notification_area.anchorClicked.connect(lambda url: webbrowser.open(url.toString()))
            self.content_widget.layout().activate()
            self.update_minimum_height()
            self.fit_to_content()

    # About and Help dialogs
    def show_about(self):
        from .about_text import get_about_text
        about_text = get_about_text(__version__)

        dlg = QMessageBox(self)
        dlg.setWindowTitle("About - Coursera Full Course Downloader")
        dlg.setTextFormat(Qt.TextFormat.RichText)
        dlg.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        dlg.setText(about_text)
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.exec()

    def create_help_dialog(self):
        from .help_text import get_help_text

        dlg = QDialog(self)
        dlg.setWindowTitle("Help - Coursera Full Course Downloader")
        dlg.resize(600, 640)

        help_view = QTextBrowser()
        help_view.setFrameShape(QFrame.Shape.NoFrame)
        help_view.setOpenExternalLinks(True)
        help_view.document().setDocumentMargin(16)
        help_view.setHtml(get_help_text())

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dlg.reject)

        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(0, 0, 0, 12)
        dlg_layout.addWidget(help_view)
        button_row = QHBoxLayout()
        button_row.setContentsMargins(12, 0, 12, 0)
        button_row.addWidget(buttons)
        dlg_layout.addLayout(button_row)
        return dlg

    def show_help(self):
        self.create_help_dialog().exec()

    # Button handlers
    def stopBtnHandler(self):
        download_progress.request_cancel()
        self.stop_btn.setEnabled(False)
        self.stop_btn.setText("Stopping…")
        self.set_progress_title("Stopping…")

    def downloadBtnHandler(self):
        if not self.cauth_cookie:
            QMessageBox.warning(
                self,
                "Login required",
                "Log in to Coursera from this app before downloading.",
            )
            self.open_coursera_login()
            return

        # Save exactly what the user chose. The download command is built
        # separately, so its derived values never end up in the settings.
        course, class_name, is_specialization = self.selected_course()
        folder = self.path_label.text()
        if self.res_720.isChecked():
            resolution = '720p'
        elif self.res_540.isChecked():
            resolution = '540p'
        else:
            resolution = '360p'
        subtitle_code = self.sllangschoices[self.sl_combo.currentText()]  # '' = none
        self.localdb.update('argdict', {
            'ca': '',
            'classname': course,
            'path': folder,
            'video_resolution': resolution,
            'sl': subtitle_code,
        })

        if folder == '':
            QMessageBox.warning(self, "Error", "NO FOLDER SPECIFIED. PLEASE SELECT A FOLDER")
            return
        if class_name == "":
            QMessageBox.warning(
                self, "Error",
                "Pick a course from the list, or paste a Coursera course or specialization link.",
            )
            return
        # Both a course and a specialization get a folder named after them.
        self.output_folder = path.join(folder, class_name)

        cmd = [
            '-ca', self.cauth_cookie,
            class_name,
            '--path', folder,
            '--video-resolution', resolution,
            # A language is required even when no subtitles are wanted.
            '-sl', subtitle_code or 'en',
        ]
        if subtitle_code == '':
            cmd += ['--ignore-formats', 'srt']
        if is_specialization:
            # Download every course in it, with a short pause between courses.
            cmd += ['--specialization', '--download-delay', '5']

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

        self.start_download(cmd)

    def start_download(self, command):
        if self.download_thread and self.download_thread.isRunning():
            return

        self.download_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.download_btn.setText("Downloading…")
        self.stop_btn.setEnabled(True)
        self.show_progress_panel()

        # Clear any earlier stop before the worker can start checking for one.
        download_progress.reset()
        self.download_thread = QThread(self)
        self.download_worker = DownloadWorker(command)
        self.download_worker.moveToThread(self.download_thread)

        self.download_thread.started.connect(self.download_worker.run)
        self.download_worker.progress.connect(self.download_progress_changed)
        self.download_worker.completed.connect(self.download_completed)
        self.download_worker.failed.connect(self.download_failed)
        self.download_worker.finished.connect(self.download_thread.quit)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread_finished)
        self.download_thread.start()

    def reset_progress_counts(self):
        self.files_total = 0          # in the current course
        self.files_done = 0
        self.all_files_total = 0      # across all courses of this run
        self.files_failed = 0
        self.course_index = 0
        self.courses_total = 1
        self.skipped_courses = []
        self.bytes_received = 0       # across all files in this run
        self.file_bytes_received = 0  # in the current file
        self.transfer_started = None  # time of the first byte of this run

    def update_speed(self):
        """Show the average speed since this run's first byte."""
        if self.transfer_started is None:
            return
        elapsed = monotonic() - self.transfer_started
        if elapsed > 0:
            speed = self.bytes_received / elapsed
            # format_bytes cannot handle values between 0 and 1.
            self.progress_speed.setText(
                f"{format_bytes(speed)}/s" if speed >= 1 else "0 B/s"
            )

    def show_progress_panel(self):
        self.reset_progress_counts()
        self.set_progress_style("#3b82f6")
        self.progress_bar.setRange(0, 0)  # moving "busy" bar
        self.set_progress_title("Connecting to Coursera…")
        self.progress_percent.clear()
        self.progress_speed.clear()
        self.progress_detail.setText("Preparing the download")
        self.open_folder_btn.hide()
        self.taskbar_progress().set_state(taskbar.INDETERMINATE)
        self.progress_panel.show()
        self.content_widget.layout().activate()
        self.update_minimum_height()
        self.fit_to_content()

    def set_progress_style(self, color):
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: rgba(128, 128, 128, 0.25);"
            " border: none; border-radius: 4px; }"
            f"QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}"
        )

    def set_progress_title(self, text):
        label = self.progress_title
        label.setToolTip(text)
        label.setText(
            QFontMetrics(label.font()).elidedText(
                text, Qt.TextElideMode.ElideMiddle, max(label.width(), 200)
            )
        )

    def set_overall_progress(self, fraction):
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(int(fraction * 1000))
        self.progress_percent.setText(f"{int(fraction * 100)}%")
        self.taskbar_progress().set_state(taskbar.NORMAL)
        self.taskbar_progress().set_value(fraction)

    def taskbar_progress(self):
        # Created on first use, once the window has its taskbar button.
        if not hasattr(self, "_taskbar_progress"):
            self._taskbar_progress = TaskbarProgress(self)
        return self._taskbar_progress

    def finish_progress(self, title, detail, color, taskbar_state=taskbar.NO_PROGRESS):
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 1000)
        self.taskbar_progress().set_state(taskbar_state)
        self.open_folder_btn.setVisible(path.isdir(self.output_folder))
        self.speed_timer.stop()
        self.progress_speed.clear()
        self.set_progress_style(color)
        self.set_progress_title(title)
        self.progress_detail.setText(detail)

    @Slot(object)
    def download_progress_changed(self, event):
        event_type = event["type"]
        if event_type == "class":
            self.course_index = event["index"]
            self.courses_total = event["total"]
        elif event_type == "syllabus":
            self.set_progress_title("Reading the course syllabus…")
            self.progress_detail.setText(
                self.course_prefix() + "This can take a few minutes for large courses"
            )
            if self.progress_bar.maximum() != 0:
                self.progress_bar.setRange(0, 0)
                self.progress_percent.clear()
                self.taskbar_progress().set_state(taskbar.INDETERMINATE)
        elif event_type == "course":
            self.files_total = event["total"]
            self.all_files_total += event["total"]
            self.files_done = 0
            self.set_overall_progress(0)
            self.speed_timer.start()
        elif event_type == "waiting":
            self.set_progress_title("Starting the next course…")
        elif event_type == "retry":
            # Show the retried files as the last ones of the course.
            self.files_done = max(self.files_total - event["count"], 0)
            self.set_progress_title(f"Retrying {event['count']} failed files…")
        elif event_type == "file":
            self.file_bytes_received = 0
            self.set_progress_title(event["name"])
            self.progress_detail.setText(self.files_summary())
        elif event_type == "file_done":
            self.files_done += 1
            self.set_overall_progress(self.overall_fraction())
        elif event_type == "bytes":
            if self.transfer_started is None:
                self.transfer_started = monotonic()
            self.bytes_received += event["received"] - self.file_bytes_received
            self.file_bytes_received = event["received"]
            self.show_file_progress(event["current"], event["total"])
        elif event_type == "summary":
            self.files_failed += event["failed"]
        elif event_type == "course_skipped":
            self.skipped_courses.append(event["name"])

    def course_prefix(self):
        if self.courses_total < 2:
            return ""
        return f"Course {self.course_index} of {self.courses_total}   ·   "

    def files_summary(self):
        current = min(self.files_done + 1, self.files_total)
        return f"{self.course_prefix()}File {current} of {self.files_total}"

    def overall_fraction(self, file_fraction=0):
        if not self.files_total:
            return 0
        return min((self.files_done + file_fraction) / self.files_total, 1)

    def show_file_progress(self, current, total):
        size = format_bytes(current)
        file_fraction = 0
        if total:
            size = f"{size} of {format_bytes(total)}"
            file_fraction = min(current / total, 1)
        self.progress_detail.setText(f"{self.files_summary()}   ·   {size}")
        self.set_overall_progress(self.overall_fraction(file_fraction))

    @Slot()
    def download_completed(self):
        self.set_overall_progress(1)
        courses = f"{self.courses_total} courses, " if self.courses_total > 1 else ""
        if self.skipped_courses:
            done = self.courses_total - len(self.skipped_courses)
            detail = (f"{done} of {self.courses_total} courses, {self.all_files_total} files. "
                      f"Skipped {len(self.skipped_courses)} that could not be read; check that "
                      f"you are enrolled in them: {', '.join(self.skipped_courses)}")
            if self.files_failed:
                detail += f". {self.files_failed} files failed; use Resume to retry them."
            self.finish_progress("Download finished with errors", detail, "#f59e0b",
                                 taskbar.ERROR)
            self.notify_finished("Download finished with errors", detail,
                                 QMessageBox.Icon.Warning)
            return
        if self.files_failed:
            detail = (f"{self.files_failed} of {self.all_files_total} files failed. "
                      "Use Resume to retry them.")
            self.finish_progress("Download finished with errors", detail, "#f59e0b",
                                 taskbar.ERROR)
            self.notify_finished("Download finished with errors", detail,
                                 QMessageBox.Icon.Warning)
            return
        detail = f"{courses}{self.all_files_total} files"
        self.finish_progress("Download complete", detail, "#22c55e")
        self.notify_finished("Download complete", detail, QMessageBox.Icon.Information)

    def notify_finished(self, title, detail, icon):
        """Tell the user, even when they are working in another window."""
        if not self.isActiveWindow():
            QApplication.alert(self)  # flash the taskbar button
            if QSystemTrayIcon.isSystemTrayAvailable():
                tray = QSystemTrayIcon(self.windowIcon(), self)
                tray.show()
                tray.showMessage(title, detail, self.windowIcon(), 10000)
                tray.messageClicked.connect(self.activate_window)
                QTimer.singleShot(15000, tray.deleteLater)

        box = QMessageBox(icon, title, detail, QMessageBox.StandardButton.Ok, self)
        open_button = None
        if path.isdir(self.output_folder):
            open_button = box.addButton("Open folder", QMessageBox.ButtonRole.ActionRole)
        box.exec()
        if open_button is not None and box.clickedButton() is open_button:
            self.open_output_folder()

    def activate_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def open_output_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_folder))

    @Slot(str, str)
    def download_failed(self, error_type, message):
        if error_type == "stopped":
            self.finish_progress(
                "Download stopped", "Use Resume to continue from here.", "#f59e0b",
                taskbar.PAUSED,
            )
            return

        self.finish_progress(
            "Download failed", "Use Resume to try again.", "#ef4444", taskbar.ERROR
        )
        if error_type == "connection":
            QMessageBox.warning(self, "Connection Error", "FAILED TO CONNECT TO COURSES SERVER. PLEASE CHECK YOUR INTERNET CONNECTION AND TRY AGAIN.")
        elif error_type == "http" and general.LOGIN_CHECK_URL.split("?")[0] in message \
                and ("401" in message or "403" in message):
            self.login_expired()
            QMessageBox.warning(self, "Login expired", "YOUR COURSERA LOGIN HAS EXPIRED. LOG IN AGAIN, THEN CLICK RESUME.")
        elif error_type == "http":
            QMessageBox.warning(self, "HTTP Error", f"HTTP ERROR: {message}\nMAKE SURE YOU ARE LOGGED IN ON coursera.org AND YOU ARE ENROLLED INTO THE COURSE")
        elif error_type == "ssl":
            QMessageBox.warning(self, "SSL Error", f"SSL ERROR: {message}")
        else:
            QMessageBox.warning(self, "Error", f"SOMETHING WENT WRONG, PLEASE TRY AGAIN\n{message}")

    @Slot()
    def download_thread_finished(self):
        self.download_btn.setEnabled(True)
        self.resume_btn.setEnabled(True)
        self.download_btn.setText("Download")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setText("Stop")
        self.download_thread.deleteLater()
        self.download_thread = None
        self.download_worker = None
        if self.close_after_stop:
            QTimer.singleShot(0, self.close)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.PaletteChange:
            # Children may not have the new palette yet.
            QTimer.singleShot(0, self.refresh_link_colors)

    def update_github_icon(self):
        color = self.palette().color(QPalette.ColorRole.WindowText).name()
        self.github_btn.setIcon(
            svg_icon(GITHUB_MARK_SVG.format(color=color), 18, self.devicePixelRatioF())
        )

    def refresh_link_colors(self):
        """Links keep the color they were rendered with until re-rendered."""
        self.update_github_icon()
        footer_text = self.footer_label.text()
        self.footer_label.clear()  # setText ignores an unchanged text
        self.footer_label.setText(footer_text)
        if self.notification_html:
            self.notification_area.setHtml(self.notification_html)

    def closeEvent(self, event):
        if self.download_thread and self.download_thread.isRunning():
            event.ignore()
            if self.close_after_stop:
                return  # already stopping
            answer = QMessageBox.question(
                self,
                "Download in progress",
                "Stop the download and close the app?\n\n"
                "You can continue it later with Resume.",
            )
            if answer == QMessageBox.StandardButton.Yes:
                self.close_after_stop = True
                self.stopBtnHandler()
            return
        super().closeEvent(event)

    def resumeBtnHandler(self):
        self.shouldResume = True
        self.downloadBtnHandler()
        self.shouldResume = False

    def getPath(self):
        dir = QFileDialog.getExistingDirectory(self, "Select Download Folder", "")
        self.path_label.setText(dir)


def main():
    # pythonw.exe and windowed builds have no console. Anything printing to it
    # would otherwise crash with "'NoneType' object has no attribute 'write'".
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    if "--webview-login" in sys.argv:
        from .webview_login import run_webview_login

        result_path = None
        if "--webview-result" in sys.argv:
            result_index = sys.argv.index("--webview-result") + 1
            if result_index < len(sys.argv):
                result_path = sys.argv[result_index]
        sys.exit(run_webview_login(result_path))

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
