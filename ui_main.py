# encoding: utf-8
from email.policy import default
from select import select
from turtle import update
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
from Flip_Chess.MCTS import Monte_Carlo_Tree_Search


class MCTS_AI(QtCore.QThread):
    finishSignal = QtCore.pyqtSignal(int, int)

    def __init__(self, chessboard, parent=None):
        super(MCTS_AI, self).__init__(parent)
        self.chessboard = chessboard

    def run(self):
        self.MCTS = Monte_Carlo_Tree_Search("MCTS_AI", WHITE)
        strategy = self.MCTS(self.chessboard)
        i, j = strategy[0], strategy[1]
        logging.debug(f"MCTS_AI put piece at {i} {j}")
        self.finishSignal.emit(i, j)


class LaBel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMouseTracking(True)

    def enterEvent(self, e):
        e.ignore()


class FlipChess(QWidget):
    def __init__(self, args):
        super().__init__()
        self.args = args
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

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.drawLines(qp)
        qp.end()

    def mouseMoveEvent(self, e):  # 黑色棋子随鼠标移动
        self.mouse_point.move(e.x() - 32, e.y() - 32)

    def mousePressEvent(self, e):  # 玩家下棋
        if e.button() == Qt.LeftButton and self.ai_down == True:
            x, y = e.x(), e.y()
            i, j = self.coordinate_transform_pixel2map(x, y)
            if not i is None and not j is None:
                piece_state = self.chessboard.get_xy_on_logic_state(i, j)
                if piece_state == EMPTY:
                    # 棋子落在空白处才进行反应，传入到chessboard进行处理，然后刷新GUI棋盘
                    can_put_piece = self.chessboard.put_piece(i, j, self.piece_now)
                    self.judge_winner()
                    if can_put_piece == 0:
                        self.update_UI_chessboard()
                        # 落子完毕后，当前棋子取反
                        self.piece_now = BLACK if self.piece_now == WHITE else WHITE
                        self.mouse_point.setPixmap(
                            self.black if self.piece_now == BLACK else self.white
                        )
                        if self.args.mode == "PVE":
                            # PVE时玩家先下，MCTS_AI是white
                            self.ai_down = False
                            self.AI = MCTS_AI(self.chessboard)
                            self.AI.finishSignal.connect(self.AI_draw)
                            self.AI.start()

    def AI_draw(self, i, j):
        # AI做出决策后，显示AI落子，get logic chessboard and update UI chessboard
        self.chessboard.put_piece(i, j, WHITE)
        self.judge_winner()
        self.x, self.y = self.coordinate_transform_map2pixel(i, j)
        self.ai_down = True
        self.update()
        self.update_UI_chessboard()
        self.mouse_point.setPixmap(self.black)
        self.piece_now = BLACK

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
        self.judge_winner()

    def drawLines(self, qp):  # 指示AI当前下的棋子
        pen = QtGui.QPen(QtCore.Qt.green, 4, QtCore.Qt.SolidLine)
        qp.setPen(pen)
        x = int(self.x)
        y = int(self.y)
        qp.drawLine(x - 10, y - 10, x + 6, y + 6)
        qp.drawLine(x + 6, y, x + 6, y + 6)
        qp.drawLine(x, y + 6, x + 6, y + 6)

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

    def judge_winner(self):
        winner = self.chessboard.judge_end()
        logging.info(f"Winner is {winner}")
        if winner != EMPTY:
            self.gameover(winner)

    def gameover(self, winner):
        logging.info("Game over")
        if winner == BLACK:
            reply = QMessageBox.question(
                self,
                "Winner is black player!",
                "Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
        else:
            reply = QMessageBox.question(
                self,
                "Winner is white player",
                "Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

        if reply == QMessageBox.Yes:  # 复位
            self.piece_now = BLACK
            self.mouse_point.setPixmap(self.black)
            for piece in self.pieces:
                piece.clear()
            self.chessboard.reset()
            self.update_UI_chessboard()
            self.update()
        else:
            self.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, choices=["PVP", "PVE"], default="PVP")
    parser.add_argument("--MCTS_SCALAR", type=int)
    args = parser.parse_args()
    app = QApplication(sys.argv)
    ex = FlipChess(args)
    sys.exit(app.exec_())
