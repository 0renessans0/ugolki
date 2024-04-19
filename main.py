from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow

import sys


def application():
    app=QApplication(sys.argv)
    gwindow = QMainWindow()
    
    gwindow.setWindowTitle("Уголки")
    gwindow.setGeometry(0, 0, 1920, 1080)

    main_text=QtWidgets.Qlable(gwindow)
    main_text.setText("Уголки")
    main_text.move(870,60)
    main_text.adjustSize()
    

    btnn = QtWidgets.QPushButton(gwindow)
    btnn.move(860, 370)
    btnn.setText("Начать")
    btnn.setStyleSheet('''
                       background-color:#f5d742;
                       border:7px solid #cef794;
                       border-radius:40;
                      ''' )
    btnn.setFixedWidth(300)
    
    btnz = QtWidgets.QPushButton(gwindow)
    btnz.move(40, 40)
    btnz.setStyleSheet("")

 
    gwindow.show()
    sys.exit(app.exec_())


if __name__=="__main__":
    application()