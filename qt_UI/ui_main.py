WIDTH = 800
HEIGHT = 800
EMPTY = 0
O_CHESS = 1
X_CHESS = 2

import sys
import math
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow,QLabel
from PyQt5.QtGui import QPixmap
from qt_ui import Ui_Form


# class ChessLabel(QLabel):
#     def __init__(self,index_x,index_y,pos_x,pos_y,parent=None):
#         super(ChessLabel, self).__init__(parent)
#         self.index_x = index_x
#         self.index_y = index_y
#         self.pos_x = pos_x
#         self.pos_y = pos_y
#         self.state = EMPTY
    

class MyMianForm(QMainWindow, Ui_Form):
    def __init__(self, parent=None):
        super(MyMianForm, self).__init__(parent)
        self.O_chess = QPixmap("img/O_chess.png")
        self.X_chess = QPixmap("img/X_chess.png")
        self.chessboard = UI_chessboard()
        self.step = 0
        self.current_player = O_CHESS
        self.setupUi(self)
        self.reset_UI()

    def reset_UI(self):
        self.setWindowTitle("FlipChess")
        self.chessboard_label.setScaledContents(True)
        self.chessboard_label.setPixmap(QtGui.QPixmap("img/chessboard.png"))

        self.mode_box.addItem("P V E 模式")
        self.mode_box.addItem("P V P 模式")
        self.mode_box.currentIndexChanged[int].connect(self.change_mode)
        self.current_player_img_label.setScaledContents(True)
        self.current_player_img_label.setPixmap(self.O_chess)

        self.chessboard_label.mousePressEvent = self.click_chessboard
        # self.chess_lists = []
        # for i in range(8):
        #     for j in range(8):
        #         self.chess_lists.append(ChessLabel(i,j,i*82,j*82))

        self.setMouseTracking(True)
        self.show()

    def change_mode(self, mode_index):
        print(mode_index)

    # def click_chess(self,event):
    #     if self.current_player == O_CHESS:


    def click_chessboard(self,event):
        # 获取点击index，将棋子图片贴上去，更新棋盘显示
        pos_x,pos_y = event.pos().x(),event.pos().y()
        chessboard_x = self.chessboard_label.x()
        chessboard_y = self.chessboard_label.y()
        index_x = math.floor(pos_x/82)
        index_y = math.floor(pos_y/82)
        chess_label = QLabel()
        chess_label.setScaledContents(True)
        if self.current_player == O_CHESS:
            chess_label.setPixmap(self.O_chess)
            self.current_player = X_CHESS
        else:
            chess_label.setPixmap(self.X_chess)
            self.current_player = O_CHESS
        chess_label.setGeometry(chessboard_x+index_x*82,chessboard_y+index_y*82,80,80)


class UI_chessboard():
    def __init__(self):
        self.chess_dict = {}
        for i in range(0,8):
            for j in range(8):
                self.chess_dict[(i,j)] = EMPTY



if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = MyMianForm()
    myWin.show()
    sys.exit(app.exec_())
