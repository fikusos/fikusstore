import sys
import subprocess
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox, QProgressBar, QListWidgetItem, QTabWidget,
    QInputDialog, QCheckBox, QStackedWidget, QScrollArea, QGridLayout, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QPixmap


class Worker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, command, password=None):
        super().__init__()
        self.command = command
        self.password = password

    def run(self):
        try:
            process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            if self.password:
                process.stdin.write(self.password + "\n")
                process.stdin.flush()

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.finished.emit(stdout)
            else:
                self.error.emit(stderr)
        except Exception as e:
            self.error.emit(str(e))


class LoadingDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading")
        self.setFixedSize(300, 100)
        self.setWindowModality(Qt.ApplicationModal)
        self.setStyleSheet("""
            background-color: #2E3440;
            color: #ECEFF4;
            font-size: 16px;
        """)
        layout = QVBoxLayout()
        self.label = QLabel("Loading all components, please wait...")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)


class PackageInfoDialog(QDialog):
    def __init__(self, package_name, parent=None):
        super().__init__(parent)
        self.package_name = package_name
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Package Info: {self.package_name}")
        self.setFixedSize(400, 300)
        layout = QVBoxLayout()
        self.icon_label = QLabel()
        self.icon_label.setPixmap(self.get_package_icon(self.package_name).pixmap(64, 64))
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        self.info_label = QLabel(self.get_package_info(self.package_name))
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        self.button_box = QDialogButtonBox()
        self.install_button = self.button_box.addButton("Install", QDialogButtonBox.ActionRole)
        self.remove_button = self.button_box.addButton("Remove", QDialogButtonBox.ActionRole)
        self.close_button = self.button_box.addButton("Close", QDialogButtonBox.RejectRole)
        self.install_button.clicked.connect(self.install_package)
        self.remove_button.clicked.connect(self.remove_package)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.button_box)
        self.setLayout(layout)
        self.update_button_state()

    def get_package_icon(self, package_name):
        icon = QIcon.fromTheme(package_name)
        if icon.isNull():
            icon = QIcon.fromTheme("applications-other")
        return icon

    def get_package_info(self, package_name):
        try:
            result = subprocess.run(["pacman", "-Si", package_name], capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else "No information available."
        except Exception:
            return "No information available."

    def is_package_installed(self):
        try:
            result = subprocess.run(["pacman", "-Q", self.package_name], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def update_button_state(self):
        if self.is_package_installed():
            self.install_button.setVisible(False)
            self.remove_button.setVisible(True)
        else:
            self.install_button.setVisible(True)
            self.remove_button.setVisible(False)

    def install_package(self):
        self.parent.install_selected_package(self.package_name)
        self.update_button_state()

    def remove_package(self):
        self.parent.remove_selected_package(self.package_name)
        self.update_button_state()


class PackageCard(QWidget):
    def __init__(self, package_name, parent=None):
        super().__init__(parent)
        self.package_name = package_name
        self.parent = parent
        self.init_ui()
        self.update_button_state()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setStyleSheet(
            """
            background-color: #3B4252;
            border-radius: 10px;
            padding: 10px;
            """
        )
        self.icon_label = QLabel()
        self.icon_label.setPixmap(self.get_package_icon(self.package_name).pixmap(64, 64))
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        self.label = QLabel(self.package_name)
        self.label.setStyleSheet("font-size: 14px; color: #ECEFF4; text-align: center;")
        layout.addWidget(self.label)
        self.action_button = QPushButton()
        self.action_button.setStyleSheet(
            """
            QPushButton {
                font-size: 14px;
                padding: 5px;
                border-radius: 5px;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        self.action_button.clicked.connect(self.toggle_package)
        layout.addWidget(self.action_button)
        self.setLayout(layout)

    def get_package_icon(self, package_name):
        icon = QIcon.fromTheme(package_name)
        if icon.isNull():
            icon = QIcon.fromTheme("applications-other")
        return icon

    def is_package_installed(self):
        try:
            if self.parent.package_manager_switch.isChecked():
                result = subprocess.run(["yay", "-Q", self.package_name], capture_output=True, text=True)
            else:
                result = subprocess.run(["pacman", "-Q", self.package_name], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def update_button_state(self):
        if self.is_package_installed():
            self.action_button.setText("Remove")
            self.action_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #F44336;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
                """
            )
        else:
            self.action_button.setText("Install")
            self.action_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #4CAF50;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                """
            )

    def toggle_package(self):
        if self.is_package_installed():
            self.parent.remove_selected_package(self.package_name)
        else:
            self.parent.install_selected_package(self.package_name)
        self.update_button_state()

    def mouseDoubleClickEvent(self, event):
        self.show_package_info()

    def show_package_info(self):
        dialog = PackageInfoDialog(self.package_name, self.parent)
        dialog.exec_()


class FKInstall(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fikus Store")
        self.setGeometry(100, 100, 1000, 700)
        self.set_style()
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.main_page = QWidget()
        self.init_main_page()
        self.central_widget.addWidget(self.main_page)
        self.log_file = os.path.expanduser("~/.local/share/fkinstall.log")
        self.ensure_log_file_exists()
        self.config_dir = os.path.expanduser("~/.config/fkinstall")
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.ensure_config_dir_exists()
        self.loading_dialog = LoadingDialog()
        self.loading_dialog.show()
        QApplication.processEvents()
        self.init_categories()
        self.loading_dialog.close()

    def ensure_log_file_exists(self):
        log_dir = os.path.dirname(self.log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("FKInstall Log\n")

    def log_message(self, message):
        with open(self.log_file, "a") as f:
            f.write(f"{message}\n")

    def ensure_config_dir_exists(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def set_style(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #2E3440;
            }
            QLabel {
                color: #ECEFF4;
                font-size: 16px;
            }
            QLineEdit {
                background-color: #3B4252;
                color: #ECEFF4;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
                background-color: #4CAF50;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTabBar::tab {
                background: #4C566A;
                color: #ECEFF4;
                padding: 10px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #81A1C1;
            }
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                font-size: 14px;
                background-color: #2E3440;
                color: #ECEFF4;
            }
            QProgressBar::chunk {
                background-color: #88C0D0;
                border-radius: 5px;
            }
            """
        )

    def init_main_page(self):
        layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages...")
        self.search_input.setStyleSheet(
            """
            font-size: 14px;
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #555;
            background-color: #3B4252;
            color: #ECEFF4;
            """
        )
        self.search_input.returnPressed.connect(self.on_search_enter_pressed)
        search_layout.addWidget(self.search_input)
        self.update_button = QPushButton("Update System")
        self.update_button.setStyleSheet(
            """
            QPushButton {
                font-size: 12px;
                padding: 5px;
                border-radius: 5px;
                background-color: #4CAF50;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        self.update_button.clicked.connect(self.update_system)
        search_layout.addWidget(self.update_button)
        layout.addLayout(search_layout)
        self.package_manager_switch = QCheckBox("Use yay instead of pacman")
        self.package_manager_switch.setStyleSheet(
            """
            font-size: 14px;
            color: #ECEFF4;
            """
        )
        self.package_manager_switch.setChecked(False)
        layout.addWidget(self.package_manager_switch)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            """
            QTabBar::tab {
                background: #4C566A;
                color: #ECEFF4;
                padding: 10px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #81A1C1;
            }
            """
        )
        layout.addWidget(self.tabs)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                font-size: 14px;
                background-color: #2E3440;
                color: #ECEFF4;
            }
            QProgressBar::chunk {
                background-color: #88C0D0;
                border-radius: 5px;
            }
            """
        )
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        self.main_page.setLayout(layout)

    def init_categories(self):
        categories = {
            "Internet": [
                "firefox", "chromium", "thunderbird", "brave", "opera", "vivaldi", "tor-browser", "falkon",
                "qutebrowser", "epiphany", "midori", "lynx", "links", "w3m", "surf", "dillo", "netsurf",
                "palemoon", "waterfox", "basilisk", "otter-browser", "slimjet", "iridium", "ungoogled-chromium",
                "seamonkey", "konqueror", "luakit", "arora", "qupzilla", "dooble", "uzbl", "min", "nyxt",
                "elinks", "retawq", "edbrowse", "w3", "amaya", "dillo2", "kazehakase", "galeon", "rekonq"
            ],
            "Terminal": [
                "vim", "emacs", "htop", "alacritty", "kitty", "tmux", "zsh", "fish", "bash", "neofetch",
                "ranger", "ncdu", "glances", "btop", "lazygit", "tig", "micro", "nano", "mc", "terminator",
                "tilix", "guake", "yakuake", "cool-retro-term", "hyper", "tabby", "wezterm", "xterm",
                "rxvt", "st", "sakura", "eterm", "terminology", "gnome-terminal", "konsole", "xfce4-terminal",
                "lxterminal", "mate-terminal", "deepin-terminal", "terminix", "blackbox", "alacritty", "kitty"
            ],
            "WM/DE": [
                "cinnamon", "gnome", "kde-plasma", "xfce4", "i3", "awesome", "bspwm", "dwm", "qtile", "lxde",
                "lxqt", "mate", "enlightenment", "openbox", "fluxbox", "icewm", "jwm", "pekwm", "spectrwm",
                "herbstluftwm", "xmonad", "sway", "hyprland", "river", "wayfire", "weston", "labwc",
                "budgie", "pantheon", "deepin", "lumina", "trinity", "ede", "ede2", "ede3", "ede4", "ede5"
            ],
            "Office": [
                "libreoffice", "onlyoffice", "wps-office", "abiword", "gnumeric", "scribus", "latexila",
                "lyx", "texmaker", "texstudio", "kile", "gummi", "focuswriter", "zathura", "calibre",
                "okular", "evince", "masterpdfeditor", "xournalpp", "joplin", "cherrytree", "zim",
                "notepadqq", "geany", "bluefish", "brackets", "atom", "sublime-text", "vscode", "codeblocks",
                "qtcreator", "kdevelop", "anjuta", "glade", "arduino", "platformio", "rustup", "gcc", "clang"
            ],
            "Multimedia": [
                "vlc", "audacity", "kdenlive", "obs-studio", "kodi", "handbrake", "ffmpeg", "gstreamer",
                "mpv", "smplayer", "celluloid", "shotcut", "pitivi", "openshot", "blender", "gimp", "inkscape",
                "darktable", "rawtherapee", "digikam", "krita", "mypaint", "pencil2d", "synfigstudio",
                "ardour", "lmms", "musescore", "rosegarden", "hydrogen", "qtractor", "audacious", "clementine",
                "rhythmbox", "amarok", "exaile", "guayadeque", "quodlibet", "deadbeef", "cmus", "mpd", "ncmpcpp"
            ],
            "Games": [
                "steam", "lutris", "minecraft-launcher", "wine", "playonlinux", "retroarch", "dolphin-emu",
                "pcsx2", "ppsspp", "mupen64plus", "scummvm", "dosbox", "openmw", "minetest", "supertuxkart",
                "xonotic", "wesnoth", "0ad", "openttd", "freeciv", "warzone2100", "megaglest", "teeworlds",
                "openra", "hedgewars", "armagetronad", "nethack", "angband", "dungeoncrawl", "cataclysm-dda",
                "cogmind", "adom", "tome4", "nethack", "angband", "dungeoncrawl", "cataclysm-dda", "cogmind"
            ],
            "Development": [
                "vscode", "sublime-text", "atom", "intellij-idea-community-edition", "pycharm-community-edition",
                "eclipse", "netbeans", "codeblocks", "qtcreator", "kdevelop", "geany", "bluefish", "brackets",
                "monodevelop", "anjuta", "glade", "arduino", "platformio", "rustup", "gcc", "clang", "llvm",
                "cmake", "meson", "ninja", "git", "mercurial", "subversion", "docker", "podman", "kubernetes",
                "ansible", "terraform", "vagrant", "packer", "puppet", "chef", "salt", "consul", "nomad", "vault"
            ],
            "System Utilities": [
                "htop", "gnome-disk-utility", "gparted", "timeshift", "grub-customizer", "gnome-system-monitor",
                "baobab", "stacer", "bleachbit", "grsync", "rsync", "timeshift", "cron", "systemd", "ufw",
                "gufw", "firewalld", "nmap", "wireshark", "tcpdump", "htop", "iotop", "iftop", "nethogs",
                "bmon", "glances", "neofetch", "screenfetch", "alsi", "archey", "inxi", "hardinfo", "lshw",
                "lsof", "strace", "ltrace", "gdb", "valgrind", "perf", "sysstat", "dstat", "sar", "iostat"
            ],
            "Education": [
                "kstars", "stellarium", "geogebra", "gcompris", "tuxmath", "tuxpaint", "kalzium", "kgeography",
                "klettres", "kmplot", "kwordquiz", "step", "marble", "cantor", "libreoffice-math", "scilab",
                "maxima", "wxmaxima", "octave", "rstudio", "jupyter-notebook", "moodle", "anki", "gperiodic"
            ],
            "Fonts": [
                "ttf-dejavu", "ttf-liberation", "ttf-ubuntu-font-family", "ttf-fira-code", "ttf-font-awesome",
                "ttf-roboto", "ttf-ms-fonts", "ttf-google-fonts-git", "ttf-nerd-fonts-symbols", "ttf-inconsolata",
                "ttf-droid", "ttf-opensans", "ttf-lato", "ttf-jetbrains-mono", "ttf-hack", "ttf-cascadia-code",
                "ttf-source-code-pro", "ttf-mononoki", "ttf-fantasque-sans-mono", "ttf-iosevka", "ttf-ibm-plex"
            ],
            "Icons": [
                "papirus-icon-theme", "breeze-icons", "oxygen-icons", "numix-icon-theme", "faenza-icon-theme",
                "moka-icon-theme", "elementary-icon-theme", "flat-remix-icon-theme", "la-capitaine-icon-theme",
                "paper-icon-theme", "arc-icon-theme", "tela-icon-theme", "zafiro-icon-theme", "whitesur-icon-theme",
                "suru-plus-aspromauros-icon-theme", "suru-plus-icon-theme", "yaru-icon-theme", "deepin-icon-theme",
                "gnome-icon-theme", "gnome-icon-theme-extras", "gnome-icon-theme-symbolic", "gnome-icon-theme-legacy"
            ],
            "Themes": [
                "arc-gtk-theme", "adapta-gtk-theme", "breeze-gtk", "materia-gtk-theme", "numix-gtk-theme",
                "paper-gtk-theme", "plata-theme", "sweet-theme", "vimix-gtk-themes", "yaru-theme",
                "deepin-gtk-theme", "gnome-themes-extra", "gnome-themes-standard", "gtk-theme-arc", "gtk-theme-elementary",
                "gtk-theme-numix", "gtk-theme-orion", "gtk-theme-qogir", "gtk-theme-sierra", "gtk-theme-vimix"
            ],
            "All Applications": [
                "firefox", "chromium", "thunderbird", "brave", "opera", "vivaldi", "tor-browser", "falkon",
                "qutebrowser", "epiphany", "midori", "lynx", "links", "w3m", "surf", "dillo", "netsurf",
                "palemoon", "waterfox", "basilisk", "otter-browser", "slimjet", "iridium", "ungoogled-chromium",
                "seamonkey", "konqueror", "luakit", "arora", "qupzilla", "dooble", "uzbl", "min", "nyxt",
                "elinks", "retawq", "edbrowse", "w3", "amaya", "dillo2", "kazehakase", "galeon", "rekonq",
                "vim", "emacs", "htop", "alacritty", "kitty", "tmux", "zsh", "fish", "bash", "neofetch",
                "ranger", "ncdu", "glances", "btop", "lazygit", "tig", "micro", "nano", "mc", "terminator",
                "tilix", "guake", "yakuake", "cool-retro-term", "hyper", "tabby", "wezterm", "xterm",
                "rxvt", "st", "sakura", "eterm", "terminology", "gnome-terminal", "konsole", "xfce4-terminal",
                "lxterminal", "mate-terminal", "deepin-terminal", "terminix", "blackbox", "alacritty", "kitty",
                "cinnamon", "gnome", "kde-plasma", "xfce4", "i3", "awesome", "bspwm", "dwm", "qtile", "lxde",
                "lxqt", "mate", "enlightenment", "openbox", "fluxbox", "icewm", "jwm", "pekwm", "spectrwm",
                "herbstluftwm", "xmonad", "sway", "hyprland", "river", "wayfire", "weston", "labwc",
                "budgie", "pantheon", "deepin", "lumina", "trinity", "ede", "ede2", "ede3", "ede4", "ede5",
                "libreoffice", "onlyoffice", "wps-office", "abiword", "gnumeric", "scribus", "latexila",
                "lyx", "texmaker", "texstudio", "kile", "gummi", "focuswriter", "zathura", "calibre",
                "okular", "evince", "masterpdfeditor", "xournalpp", "joplin", "cherrytree", "zim",
                "notepadqq", "geany", "bluefish", "brackets", "atom", "sublime-text", "vscode", "codeblocks",
                "qtcreator", "kdevelop", "anjuta", "glade", "arduino", "platformio", "rustup", "gcc", "clang",
                "vlc", "audacity", "kdenlive", "obs-studio", "kodi", "handbrake", "ffmpeg", "gstreamer",
                "mpv", "smplayer", "celluloid", "shotcut", "pitivi", "openshot", "blender", "gimp", "inkscape",
                "darktable", "rawtherapee", "digikam", "krita", "mypaint", "pencil2d", "synfigstudio",
                "ardour", "lmms", "musescore", "rosegarden", "hydrogen", "qtractor", "audacious", "clementine",
                "rhythmbox", "amarok", "exaile", "guayadeque", "quodlibet", "deadbeef", "cmus", "mpd", "ncmpcpp",
                "steam", "lutris", "minecraft-launcher", "wine", "playonlinux", "retroarch", "dolphin-emu",
                "pcsx2", "ppsspp", "mupen64plus", "scummvm", "dosbox", "openmw", "minetest", "supertuxkart",
                "xonotic", "wesnoth", "0ad", "openttd", "freeciv", "warzone2100", "megaglest", "teeworlds",
                "openra", "hedgewars", "armagetronad", "nethack", "angband", "dungeoncrawl", "cataclysm-dda",
                "cogmind", "adom", "tome4", "nethack", "angband", "dungeoncrawl", "cataclysm-dda", "cogmind",
                "vscode", "sublime-text", "atom", "intellij-idea-community-edition", "pycharm-community-edition",
                "eclipse", "netbeans", "codeblocks", "qtcreator", "kdevelop", "geany", "bluefish", "brackets",
                "monodevelop", "anjuta", "glade", "arduino", "platformio", "rustup", "gcc", "clang", "llvm",
                "cmake", "meson", "ninja", "git", "mercurial", "subversion", "docker", "podman", "kubernetes",
                "ansible", "terraform", "vagrant", "packer", "puppet", "chef", "salt", "consul", "nomad", "vault",
                "htop", "gnome-disk-utility", "gparted", "timeshift", "grub-customizer", "gnome-system-monitor",
                "baobab", "stacer", "bleachbit", "grsync", "rsync", "timeshift", "cron", "systemd", "ufw",
                "gufw", "firewalld", "nmap", "wireshark", "tcpdump", "htop", "iotop", "iftop", "nethogs",
                "bmon", "glances", "neofetch", "screenfetch", "alsi", "archey", "inxi", "hardinfo", "lshw",
                "lsof", "strace", "ltrace", "gdb", "valgrind", "perf", "sysstat", "dstat", "sar", "iostat",
                "kstars", "stellarium", "geogebra", "gcompris", "tuxmath", "tuxpaint", "kalzium", "kgeography",
                "klettres", "kmplot", "kwordquiz", "step", "marble", "cantor", "libreoffice-math", "scilab",
                "maxima", "wxmaxima", "octave", "rstudio", "jupyter-notebook", "moodle", "anki", "gperiodic",
                "ttf-dejavu", "ttf-liberation", "ttf-ubuntu-font-family", "ttf-fira-code", "ttf-font-awesome",
                "ttf-roboto", "ttf-ms-fonts", "ttf-google-fonts-git", "ttf-nerd-fonts-symbols", "ttf-inconsolata",
                "ttf-droid", "ttf-opensans", "ttf-lato", "ttf-jetbrains-mono", "ttf-hack", "ttf-cascadia-code",
                "ttf-source-code-pro", "ttf-mononoki", "ttf-fantasque-sans-mono", "ttf-iosevka", "ttf-ibm-plex",
                "papirus-icon-theme", "breeze-icons", "oxygen-icons", "numix-icon-theme", "faenza-icon-theme",
                "moka-icon-theme", "elementary-icon-theme", "flat-remix-icon-theme", "la-capitaine-icon-theme",
                "paper-icon-theme", "arc-icon-theme", "tela-icon-theme", "zafiro-icon-theme", "whitesur-icon-theme",
                "suru-plus-aspromauros-icon-theme", "suru-plus-icon-theme", "yaru-icon-theme", "deepin-icon-theme",
                "gnome-icon-theme", "gnome-icon-theme-extras", "gnome-icon-theme-symbolic", "gnome-icon-theme-legacy",
                "arc-gtk-theme", "adapta-gtk-theme", "breeze-gtk", "materia-gtk-theme", "numix-gtk-theme",
                "paper-gtk-theme", "plata-theme", "sweet-theme", "vimix-gtk-themes", "yaru-theme",
                "deepin-gtk-theme", "gnome-themes-extra", "gnome-themes-standard", "gtk-theme-arc", "gtk-theme-elementary",
                "gtk-theme-numix", "gtk-theme-orion", "gtk-theme-qogir", "gtk-theme-sierra", "gtk-theme-vimix"
            ]
        }

        for category, packages in categories.items():
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_content = QWidget()
            scroll_layout = QGridLayout(scroll_content)
            scroll_layout.setAlignment(Qt.AlignTop)
            for i, package in enumerate(packages):
                card = PackageCard(package, self)
                scroll_layout.addWidget(card, i // 3, i % 3)
            scroll_area.setWidget(scroll_content)
            self.tabs.addTab(scroll_area, category)

    def on_search_enter_pressed(self):
        query = self.search_input.text()
        if query:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.search_packages(query)
        else:
            self.clear_scroll_area(self.tabs.currentWidget())

    def search_packages(self, query):
        try:
            if self.package_manager_switch.isChecked():
                result = subprocess.run(
                    ["yay", "-Ss", query], capture_output=True, text=True, check=False
                )
            else:
                result = subprocess.run(
                    ["pacman", "-Ss", query], capture_output=True, text=True, check=False
                )
            
            if not result.stdout:
                QMessageBox.information(self, "Info", "No packages found.")
                self.clear_scroll_area(self.tabs.currentWidget())
                self.progress_bar.setVisible(False)
                return

            packages = result.stdout.splitlines()
            self.clear_scroll_area(self.tabs.currentWidget())
            scroll_content = self.tabs.currentWidget().widget()
            scroll_layout = scroll_content.layout()

            for package in packages:
                if "/" in package:
                    parts = package.split("/")
                    if len(parts) > 1 and len(parts[1].split()) > 0:
                        package_name = parts[1].split()[0]
                        card = PackageCard(package_name, self)
                        scroll_layout.addWidget(card)
            self.progress_bar.setVisible(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error searching for packages: {e}")
            self.progress_bar.setVisible(False)

    def clear_scroll_area(self, scroll_area):
        scroll_content = scroll_area.widget()
        if scroll_content:
            scroll_layout = scroll_content.layout()
            if scroll_layout:
                while scroll_layout.count():
                    item = scroll_layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()

    def install_selected_package(self, package_name):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        if self.package_manager_switch.isChecked():
            self.install_yay_package(package_name)
        else:
            self.install_pacman_package(package_name)

    def install_yay_package(self, package_name):
        self.worker = Worker(["yay", "-S", "--noconfirm", package_name])
        self.worker.finished.connect(self.on_install_finished)
        self.worker.error.connect(self.on_install_error)
        self.worker.start()

    def install_pacman_package(self, package_name):
        password, ok = QInputDialog.getText(
            self, "Enter Password", "Enter your sudo password:", QLineEdit.Password
        )
        if ok and password:
            self.worker = Worker(["sudo", "-S", "pacman", "-S", "--noconfirm", package_name], password)
            self.worker.finished.connect(self.on_install_finished)
            self.worker.error.connect(self.on_install_error)
            self.worker.start()

    def on_install_finished(self, output):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Success", "Package installed successfully!")
        self.log_message(f"Package installed: {output}")
        self.update_interface()

    def on_install_error(self, error):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Error installing package: {error}")
        self.log_message(f"Error installing package: {error}")

    def remove_selected_package(self, package_name):
        password, ok = QInputDialog.getText(
            self, "Enter Password", "Enter your sudo password:", QLineEdit.Password
        )
        if ok and password:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.worker = Worker(["sudo", "-S", "pacman", "-R", "--noconfirm", package_name], password)
            self.worker.finished.connect(self.on_remove_finished)
            self.worker.error.connect(self.on_remove_error)
            self.worker.start()

    def on_remove_finished(self, output):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Success", "Package removed successfully!")
        self.log_message(f"Package removed: {output}")
        self.update_interface()

    def on_remove_error(self, error):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Error removing package: {error}")
        self.log_message(f"Error removing package: {error}")

    def update_interface(self):
        for i in range(self.tabs.count()):
            scroll_area = self.tabs.widget(i)
            scroll_content = scroll_area.widget()
            for j in range(scroll_content.layout().count()):
                card = scroll_content.layout().itemAt(j).widget()
                if isinstance(card, PackageCard):
                    card.update_button_state()

    def update_system(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        if self.package_manager_switch.isChecked():
            self.worker = Worker(["yay", "-Syu", "--noconfirm"])
        else:
            password, ok = QInputDialog.getText(
                self, "Enter Password", "Enter your sudo password:", QLineEdit.Password
            )
            if ok and password:
                self.worker = Worker(["sudo", "-S", "pacman", "-Syu", "--noconfirm"], password)
            else:
                return

        self.worker.finished.connect(self.on_update_finished)
        self.worker.error.connect(self.on_update_error)
        self.worker.start()

    def on_update_finished(self, output):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Success", "System updated successfully!")
        self.log_message(f"System updated: {output}")

    def on_update_error(self, error):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Error updating system: {error}")
        self.log_message(f"Error updating system: {error}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = FKInstall()
    window.show()
    sys.exit(app.exec_())
