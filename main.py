import sys
import os
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QVBoxLayout, 
                               QWidget, QLineEdit, QPushButton, QHBoxLayout, 
                               QToolBar)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

from database import HistoryManager

class BrowserTab(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # メモリの最適化設定 (低スペックPC向け)
        # メモリキャッシュを50MBに制限
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        profile.setHttpCacheMaximumSize(50 * 1024 * 1024) 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amadeus Browser")
        self.resize(1024, 768)
        
        # 履歴管理
        self.history_manager = HistoryManager()

        # トップレイアウト
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # ツールバーのセットアップ
        self.setup_toolbar()

        # タブウィジェットのセットアップ
        self.tabs = QTabWidget()
        # Chromeのようにタブの上部に余白を持たせない
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        
        # 新規タブボタン
        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.clicked.connect(lambda: self.add_new_tab(QUrl("https://www.google.com"), "New Tab"))
        self.tabs.setCornerWidget(self.new_tab_btn, Qt.Corner.TopRightCorner)

        self.layout.addWidget(self.tabs)

        # 初期タブ
        self.add_new_tab(QUrl("https://www.google.com"), "Google")

    def setup_toolbar(self):
        self.toolbar = QToolBar("Navigation")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        # ナビゲーションボタン
        self.back_btn = QAction("←", self)
        self.back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        self.toolbar.addAction(self.back_btn)

        self.forward_btn = QAction("→", self)
        self.forward_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        self.toolbar.addAction(self.forward_btn)

        self.reload_btn = QAction("↻", self)
        self.reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        self.toolbar.addAction(self.reload_btn)

        self.home_btn = QAction("🏠", self)
        self.home_btn.triggered.connect(self.navigate_home)
        self.toolbar.addAction(self.home_btn)

        # オムニボックス
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.toolbar.addWidget(self.url_bar)

    def navigate_home(self):
        self.tabs.currentWidget().setUrl(QUrl("https://www.google.com"))

    def navigate_to_url(self):
        url_text = self.url_bar.text().strip()
        if not url_text:
            return

        # URLか検索かの判別
        if "." in url_text and " " not in url_text:
            if not url_text.startswith("http://") and not url_text.startswith("https://"):
                url_text = "https://" + url_text
            url = QUrl(url_text)
        else:
            search_query = url_text.replace(" ", "+")
            url = QUrl(f"https://www.google.com/search?q={search_query}")
            
        self.tabs.currentWidget().setUrl(url)

    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None:
            qurl = QUrl("https://www.google.com")

        browser = BrowserTab()
        browser.setUrl(qurl)
        
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_url(qurl, browser))
        browser.loadFinished.connect(lambda _, i=i, browser=browser: self.update_title(browser))
        
    def close_tab(self, i):
        # 最後のタブは閉じないようにする
        if self.tabs.count() < 2:
            return
        widget = self.tabs.widget(i)
        self.tabs.removeTab(i)
        widget.deleteLater()

    def update_url(self, qurl, browser=None):
        if browser is not self.tabs.currentWidget():
            return
        self.url_bar.setText(qurl.toString())

    def update_title(self, browser):
        index = self.tabs.indexOf(browser)
        if index != -1:
            title = browser.title()
            self.tabs.setTabText(index, title)
            # 履歴に保存
            url = browser.url().toString()
            if url != "auto:" and url != "about:blank":
                self.history_manager.add_history(url, title)

    def current_tab_changed(self, i):
        qurl = self.tabs.currentWidget().url()
        self.update_url(qurl, self.tabs.currentWidget())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Amadeus Browser")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
