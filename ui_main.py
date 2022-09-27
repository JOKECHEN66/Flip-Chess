# encoding: utf-8
import time
from email.policy import default
from select import select
from turtle import update
from Flip_Chess.Board import Board

WIDTH = 540
HEIGHT = 640
MARGIN = 30
GRID = (WIDTH - 2 * MARGIN) / (8 - 1)
PIECE = 60
EMPTY = 0
BLACK = 1
WHITE = 2
DRAW = -1


import sys
from PyQt5 import QtCore, QtGui
import logging
from PyQt5.QtWidgets import QGridLayout, QFormLayout, QTextEdit
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QPainter
from Flip_Chess.MCTS import Monte_Carlo_Tree_Search


class MCTS_AI(QtCore.QThread):
    finishSignal = QtCore.pyqtSignal(int, int, list)

    def __init__(self, chessboard, SCALAR, MAX_DEPTH, WEIGHT, parent=None):
        super(MCTS_AI, self).__init__(parent)
        self.chessboard = chessboard
        self.SCALAR = SCALAR
        self.MAX_DEPTH = MAX_DEPTH
        self.WEIGHT = WEIGHT

    def run(self):
        self.MCTS = Monte_Carlo_Tree_Search("MCTS_AI", WHITE, self.SCALAR, self.MAX_DEPTH, self.WEIGHT)
        strategy, total_time = self.MCTS(self.chessboard)
        i, j = strategy[0], strategy[1]
        logging.debug(f"MCTS_AI put piece at {i} {j}")
        self.finishSignal.emit(i, j, total_time)


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
        # 记录无效落子次数
        self.black_count = 0
        self.white_count = 0

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

        self.resize(WIDTH, HEIGHT)  # 固定大小 540 * 590
        self.setMinimumSize(QtCore.QSize(WIDTH, HEIGHT))
        self.setMaximumSize(QtCore.QSize(WIDTH, HEIGHT))

        self.text = QTextEdit('Waiting AI to move...', self)
        self.text.resize(540, 100)
        self.text.move(0, 541)
        self.text.setReadOnly(True)

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

    def mousePressEvent(self, e, count=0):  # 玩家下棋
        if e.button() == Qt.LeftButton and self.ai_down == True:
            x, y = e.x(), e.y()
            i, j = self.coordinate_transform_pixel2map(x, y)
            if not i is None and not j is None:
                piece_state = self.chessboard.get_xy_on_logic_state(i, j)
                if piece_state == EMPTY:
                    # 棋子落在空白处才进行反应，传入到chessboard进行处理，然后刷新GUI棋盘
                    can_put_piece = self.chessboard.put_piece(i, j, self.piece_now)
                    if can_put_piece == -1:
                        QMessageBox.warning(self, 'WARNING', 'Invalid Place to Put!')
                        if self.piece_now == BLACK:
                            self.black_count += 1
                            count = self.black_count
                        else:
                            self.white_count += 1
                            count = self.white_count
                        # 三次无效落子判负
                        if count == 3:
                            self.black_count, self.white_count = 0, 0
                            winner = BLACK if self.piece_now == WHITE else WHITE
                            self.gameover(winner)
                    elif can_put_piece == 0:
                        # 清除当前的无效落子计数
                        if self.piece_now == BLACK:
                            self.black_count = 0
                        else:
                            self.white_count = 0
                        self.update_UI_chessboard()
                        # 落子完毕后，当前棋子取反
                        self.piece_now = BLACK if self.piece_now == WHITE else WHITE
                        self.mouse_point.setPixmap(
                            self.black if self.piece_now == BLACK else self.white
                        )
                        if self.args.mode == "PVE":
                            # PVE时玩家先下，MCTS_AI是white
                            self.ai_down = False
                            self.AI = MCTS_AI(self.chessboard, self.args.SCALAR, self.args.MAX_DEPTH, self.args.WEIGHT)
                            self.AI.finishSignal.connect(self.AI_draw)
                            self.AI.start()
                        self.judge_winner()
        elif e.button() == Qt.RightButton and self.ai_down == True:
            if self.chessboard.judge_all_drops(self.piece_now) == []:
                QMessageBox.information(self, 'INFORMATION', 'You Skip this Turn...')
                self.piece_now = BLACK if self.piece_now == WHITE else WHITE
                self.mouse_point.setPixmap(
                    self.black if self.piece_now == BLACK else self.white
                )
                if self.args.mode == "PVE":
                    # PVE时玩家先下，MCTS_AI是white
                    self.ai_down = False
                    self.AI = MCTS_AI(self.chessboard, self.args.SCALAR, self.args.MAX_DEPTH, self.args.WEIGHT)
                    self.AI.finishSignal.connect(self.AI_draw)
                    self.AI.start()
                self.judge_winner()
            else:
                QMessageBox.information(self, 'INFORMATION', 'Cannot Skip this Turn...\nYou Still Have Chance to Move')

    def AI_draw(self, i, j, total_time):
        if i != -999 and j != -999:
            self.text.setText('In this turn:\n'
                              f'total time for AI\'s decision is {total_time[0]}s\n'
                              f'select time for AI\'s decision is {total_time[1]}s\n'
                              f'simulate time for AI\'s decision is {total_time[2]}s\n'
                              f'propagate time for AI \'sdecision is {total_time[3]}s\n')
            # AI做出决策后，显示AI落子，get logic chessboard and update UI chessboard
            self.chessboard.put_piece(i, j, WHITE)
            self.x, self.y = self.coordinate_transform_map2pixel(i, j)
            self.ai_down = True
            self.update()
            self.update_UI_chessboard()
            self.mouse_point.setPixmap(self.black)
            self.piece_now = BLACK
            self.judge_winner()
        else:
            self.text.setText('')
            self.text.setText('AI skips this turn...')
            QMessageBox.information(self, 'INFORMATION', 'AI Skips this Turn...')
            self.ai_down = True
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
        time.sleep(1)
        logging.info("Game over")
        if winner == BLACK:
            reply = QMessageBox.question(
                self,
                "Flip chess",
                "Winner is black player!\nContinue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
        elif winner == WHITE:
            reply = QMessageBox.question(
                self,
                "Flip chess",
                "Winner is white player!\nContinue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
        elif winner == DRAW:
            reply = QMessageBox.question(
                self,
                "Flip chess",
                "Draw!\nContinue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

        if reply == QMessageBox.Yes:  # 复位
            for piece in self.pieces:
                piece.clear()
            self.chessboard = Board()
            self.pieces_state = [EMPTY for _ in range(64)]
            self.update_UI_chessboard()
            self.ai_down = True
            self.piece_now = BLACK
            self.text.setText('')
            self.mouse_point.setPixmap(self.black)
            self.update()
        else:
            self.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", "-m", type=str, choices=["PVP", "PVE"], default="PVE")
    parser.add_argument("--SCALAR", "-s", type=int, default=2)
    parser.add_argument("--MAX_DEPTH", "-md", type=int, default=150)
    parser.add_argument("--WEIGHT", "-w", type=int, default=10)
    args = parser.parse_args()
    app = QApplication(sys.argv)
    ex = FlipChess(args)
    sys.exit(app.exec_())
