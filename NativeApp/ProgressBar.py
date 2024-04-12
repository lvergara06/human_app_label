from PyQt5.QtWidgets import QApplication, QProgressBar, QProgressDialog, QWidget, QVBoxLayout, QSizePolicy, QLabel, QDesktopWidget
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (QMainWindow, QPushButton, 
                             QFileDialog, QListWidget, QLineEdit,
                             QApplication, QMessageBox, QComboBox, QStyle)
import sys

class ProgressBar(QMainWindow):
    
    flag = None
    icon_path = None
    title_label = None
    
    def __init__(self):
        
        super(ProgressBar, self).__init__()
        # self.matching_icon = QLabel()    

        self.widget = QWidget()
        self.layout = QVBoxLayout()

        # Initialize progress bar
        self.progress_dialog = QProgressBar()
        self.progress_dialog.setFixedHeight(20)
        self.progress_dialog.setFixedWidth(500)
        self.matching_icon = QLabel() 
    
    def update_progress(self, value):
        progress_dialog = self.progress_dialog
        progress_dialog.setValue(value)
        QApplication.processEvents()
        
    def close(self):
        self.widget.close()
    
    def show(self, flag):
        self.flag = flag 
          
        if (self.flag == 'url'):
            self.icon_path = "/opt/firefox/human_app_label/NativeApp/matching.png"
            self.title_label = QLabel("Matching URLs")
        elif(self.flag == 'whois'):
            self.icon_path = "/opt/firefox/human_app_label/NativeApp/whois.png"
            self.layout.removeWidget(self.title_label)
            self.title_label = QLabel("Making WHOIS Queries")
            
        self.matching_icon.clear()
        self.pixmap = QPixmap(self.icon_path)
        self.pixmap = self.pixmap.scaledToHeight(60)  
        self.matching_icon.setPixmap(self.pixmap)

        self.layout.addWidget(self.title_label, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.matching_icon, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.progress_dialog, alignment=Qt.AlignCenter)
        self.widget.setLayout(self.layout)

        # Get the screen geometry to position the progress bar in the center
        screen_rect = QDesktopWidget().screenGeometry()
        self.widget_width = 500
        self.widget_height = 30
        self.widget.setGeometry(
            screen_rect.width() // 2 - self.widget_width // 2,
            screen_rect.height() // 2 - self.widget_height // 2,
            self.widget_width,
            self.widget_height
        )

        self.widget.setWindowFlags(self.widget.windowFlags() | Qt.WindowStaysOnTopHint)

        self.widget.show()
        
app = QApplication([])