PREFIX = /usr
BINDIR = $(PREFIX)/bin
DATADIR = $(PREFIX)/share
APPLICATIONSDIR = $(DATADIR)/applications
ICONDIR = $(DATADIR)/icons/hicolor/scalable/apps
DESKTOP_FILE = fikusstore.desktop

all: build

build:
	python3 -m PyInstaller --onefile --windowed --name=fikusstore main.py

install:
	install -Dm755 dist/fkinstall $(DESTDIR)$(BINDIR)/fikusstore
	install -Dm644 $(DESKTOP_FILE) $(DESTDIR)$(APPLICATIONSDIR)/$(DESKTOP_FILE)
	install -Dm644 $(ICON_FILE) $(DESTDIR)$(ICONDIR)/$(ICON_FILE)

uninstall:
	rm -f $(DESTDIR)$(BINDIR)/fikusstore
	rm -f $(DESTDIR)$(APPLICATIONSDIR)/$(DESKTOP_FILE)
	rm -f $(DESTDIR)$(ICONDIR)/$(ICON_FILE)

clean:
	rm -rf build dist
	rm -f fikusstore.spec
