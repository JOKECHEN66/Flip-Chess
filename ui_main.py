# encoding: utf-8
from Flip_Chess.Board import Board

WIDTH = 540
HEIGHT = 540
MARGIN = 30
GRID = (WIDTH - 2 * MARGIN) / (8 - 1)
PIECE = 60
EMPTY = 0
BLACK = 1
WHITE = 2


import sys
from PyQt5 import QtCore, QtGui
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QPainter


class LaBel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMouseTracking(True)

    def enterEvent(self, e):
        e.ignore()


class GoBang(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
        self.chessboard = Board()

        palette1 = QPalette()
        palette1.setBrush(
            self.backgroundRole(),
            QtGui.QBrush(QtGui.QPixmap("img/chessboard.jpg").scaledToWidth(540)),
        )
        self.setPalette(palette1)
        self.setCursor(Qt.PointingHandCursor)

        self.resize(WIDTH, HEIGHT)  # 固定大小 540*540
        self.setMinimumSize(QtCore.QSize(WIDTH, HEIGHT))
        self.setMaximumSize(QtCore.QSize(WIDTH, HEIGHT))

        self.setWindowTitle("FlipChess")
        self.setWindowIcon(QIcon("img/black.png"))

        self.black = QPixmap("img/black.png")
        self.white = QPixmap("img/white.png")

        self.piece_now = BLACK  # 黑棋先行
        self.my_turn = True  # 玩家先行
        self.x, self.y = 1000, 1000

        self.mouse_point = LaBel(self)  # 将鼠标图片改为棋子
        self.mouse_point.setScaledContents(True)
        self.mouse_point.setPixmap(self.black)
        self.mouse_point.setGeometry(270, 270, PIECE, PIECE)
        self.pieces = [LaBel(self) for i in range(64)]  # 新建棋子标签，准备在棋盘上绘制棋子
        for piece in self.pieces:
            piece.setVisible(True)  # 图片可视
            piece.setScaledContents(True)  # 图片大小根据标签大小可变

        self.pieces_state = [EMPTY for _ in range(64)]

        self.mouse_point.raise_()  # 鼠标始终在最上层
        self.ai_down = (
            True  # AI已下棋，主要是为了加锁，当值是False的时候说明AI正在思考，这时候玩家鼠标点击失效，要忽略掉 mousePressEvent
        )
        self.setMouseTracking(True)
        self.show()
        self.update_UI_chessboard()

    # def paintEvent(self, event):
    #     qp = QPainter()
    #     qp.begin(self)
    #     self.drawLines(qp)
    #     qp.end()

    def mouseMoveEvent(self, e):  # 黑色棋子随鼠标移动
        self.mouse_point.move(e.x() - 32, e.y() - 32)

    def mousePressEvent(self, e):  # 玩家下棋
        if e.button() == Qt.LeftButton and self.ai_down == True:
            x, y = e.x(), e.y()
            i, j = self.coordinate_transform_pixel2map(x, y)
            if not i is None and not j is None:
                if self.chessboard.get_xy_on_logic_state(i, j) == EMPTY:
                    # 棋子落在空白处才进行反应，传入到chessboard进行处理，然后刷新GUI棋盘
                    if self.chessboard.put_piece(i, j, self.piece_now) == 0:
                        self.update_UI_chessboard()
                        # 落子完毕后，当前棋子取反
                        self.piece_now = BLACK if self.piece_now == WHITE else WHITE
                        self.mouse_point.setPixmap(
                            self.black if self.piece_now == BLACK else self.white
                        )

    def update_UI_chessboard(self):
        logic_chessboard = self.chessboard.get_logic_board()
        for piece_index in range(64):
            i, j = int(piece_index / 8), piece_index % 8
            if self.pieces_state[piece_index] != self.chessboard.get_xy_on_logic_state(
                i, j
            ):
                # 如果当前棋子非空，将棋子clear
                logging.debug(f"piece_index {piece_index} change")
                if self.pieces_state[piece_index] != EMPTY:
                    self.pieces[piece_index].clear()
                # 棋子放图片
                if logic_chessboard[piece_index] == BLACK:
                    self.pieces[piece_index].setPixmap(self.black)
                    self.pieces_state[piece_index] = BLACK
                else:
                    self.pieces[piece_index].setPixmap(self.white)
                    self.pieces_state[piece_index] = WHITE
                x, y = self.coordinate_transform_map2pixel(i, j)
                self.pieces[piece_index].setGeometry(int(x), int(y), PIECE, PIECE)
        logging.info("Updated UI_chessboard")

    def drawLines(self, qp):  # 指示AI当前下的棋子
        if self.step != 0:
            pen = QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.SolidLine)
            qp.setPen(pen)
            qp.drawLine(self.x - 5, self.y - 5, self.x + 3, self.y + 3)
            qp.drawLine(self.x + 3, self.y, self.x + 3, self.y + 3)
            qp.drawLine(self.x, self.y + 3, self.x + 3, self.y + 3)

    def coordinate_transform_map2pixel(self, i, j):
        # 从 chessMap 里的逻辑坐标到 UI 上的绘制坐标的转换
        return MARGIN + j * GRID - PIECE / 2, MARGIN + i * GRID - PIECE / 2

    def coordinate_transform_pixel2map(self, x, y):
        # 从 UI 上的绘制坐标到 chessMap 里的逻辑坐标的转换
        i, j = int(round((y - MARGIN) / GRID)), int(round((x - MARGIN) / GRID))
        # 有MAGIN, 排除边缘位置导致 i,j 越界
        if i < 0 or i >= 8 or j < 0 or j >= 8:
            return None, None
        else:
            return i, j

    def gameover(self, winner):
        if winner == BLACK:
            reply = QMessageBox.question(
                self,
                "You Win!",
                "Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
        else:
            reply = QMessageBox.question(
                self,
                "You Lost!",
                "Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

        if reply == QMessageBox.Yes:  # 复位
            self.piece_now = BLACK
            self.mouse_point.setPixmap(self.black)
            for piece in self.pieces:
                piece.clear()
            self.chessboard.reset()
            self.update()
        else:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = GoBang()
    sys.exit(app.exec_())
