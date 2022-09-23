# coding: utf-8
import time

EMPTY = 0
BLACK = 1
WHITE = 2


class Board:
    def __init__(self):
        self._board = []
        # 棋盘初始化
        for i in range(8):
            tmp = [EMPTY for i in range(8)]
            self._board.append(tmp)
        self._board[3][3], self._board[4][4] = BLACK, BLACK
        self._board[3][4], self._board[4][3] = WHITE, WHITE
        # 判断是否可以产生翻转的八个方向
        self._directions = [
            [-1, -1],
            [-1, 0],
            [-1, 1],
            [0, 1],
            [1, 1],
            [1, 0],
            [1, -1],
            [0, -1],
        ]

    def show_board(self):
        # 在UI中打印棋盘信息
        pass

    def display_board(self):
        # 在控制台上打印棋盘
        print("    1    2    3    4    5    6    7    8")
        for index, board in enumerate(self._board):
            print(index + 1, board)

    def put_piece(self, x, y, chess_piece):
        """

        :param x: 坐标x, 对应行
        :param y: 坐标y, 对应列
        :param chess_piece: 玩家棋子
        :return:
        """
        assert chess_piece in [WHITE, BLACK]
        # 不可重复落子
        if self._board[x][y] != EMPTY:
            print("Cannot repeat the drop...")
            return -1

        if self.drop(x, y, chess_piece):
            if self.judge_end() == EMPTY:
                return 0
        else:
            return -1

    def drop(self, x, y, chess_piece):
        can_flip, results = self._judge_flip(x, y, chess_piece)
        if can_flip:
            self._board[x][y] = chess_piece
            self._flip(x, y, results, chess_piece)
            return True
        else:
            return False

    def _judge_flip(self, x, y, chess_piece):
        """
        判断本次落子是否可以产生翻转
        :param x:
        :param y:
        :param chess_piece:
        :return:
        """
        results = []
        for direction in self._directions:
            i, j = x, y
            count = 1
            can_flip = True
            while 0 <= i < 8 and 0 <= y < 8:
                i += direction[0]
                j += direction[1]
                if i < 0 or j < 0 or i > 7 or j > 7:
                    can_flip = False
                    break
                if self._board[i][j] == EMPTY:
                    can_flip = False
                    break
                if self._board[i][j] == chess_piece:
                    can_flip = True if count > 1 else False
                    break
                count += 1
            results.append([can_flip, count])

        can_flip = False
        for result in results:
            can_flip |= result[0]

        return can_flip, results

    def _flip(self, x, y, results, chess_piece):
        for index, result in enumerate(results):
            if result[0]:
                i, j = x, y
                for count in range(result[1]):
                    i += self._directions[index][0]
                    j += self._directions[index][1]
                    self._board[i][j] = chess_piece

    def judge_all_drops(self, chess_piece):
        strategy = []
        for i in range(8):
            for j in range(8):
                if self._board[i][j] == EMPTY:
                    can_flip, _ = self._judge_flip(i, j, chess_piece)
                    if can_flip:
                        strategy.append([i, j])

        return strategy

    # 此函数暂时无调用, 闲置
    """
    def judge_area(self, chess_piece):
        flip = False
        for i in range(8):
            for j in range(8):
                if self._board[i][j] == EMPTY:
                    can_flip, _ = self._judge_flip(i, j, chess_piece)
                    flip |= can_flip

        return flip
    """

    def judge_end(self):
        # 判断全局是否仍有可以落子的坐标
        flip = False
        for i in range(8):
            for j in range(8):
                if self._board[i][j] == EMPTY:
                    can_flip, _ = self._judge_flip(i, j, WHITE)
                    flip |= can_flip
                    can_flip, _ = self._judge_flip(i, j, BLACK)
                    flip |= can_flip

        if not flip:
            winner, _ = self.calculate_winner()
            return winner

        return EMPTY

    def calculate_winner(self):
        count_O = 0
        count_X = 0
        for i in range(8):
            for j in range(8):
                if self._board[i][j] == WHITE:
                    count_O += 1
                if self._board[i][j] == BLACK:
                    count_X += 1
        if count_O != count_X:
            if count_O > count_X:
                return WHITE, abs(count_O - count_X)
            else:
                return BLACK, abs(count_O - count_X)
        else:
            return "D", 0

    def get_xy_on_logic_state(self, x, y):
        return self._board[x][y]

    def get_logic_board(self):
        pieces_state = [EMPTY for _ in range(64)]
        for i in range(8):
            for j in range(8):
                pieces_state[i * 8 + j] = self._board[i][j]
        return pieces_state

    def reset(self):
        self._board = []
        # 棋盘初始化
        for i in range(8):
            tmp = [EMPTY for i in range(8)]
            self._board.append(tmp)
        self._board[3][3], self._board[4][4] = BLACK, BLACK
        self._board[3][4], self._board[4][3] = WHITE, WHITE


class Game:
    def __init__(self, black_player, white_player):
        self._board = Board()
        self._black_player = black_player
        self._white_player = white_player

    def _switch_player(self, name):
        if name == self._black_player.name:
            return self._white_player
        else:
            return self._black_player

    def play_game(self):
        status = 0
        count_mistake = 0
        current_player = self._black_player
        while self._board.judge_end() == EMPTY and count_mistake < 3:
            """-------------------------------------------------------"""
            # 以下输出模块需要在UI上相应体现
            print(f"current player is: {current_player.name}")
            """-------------------------------------------------------"""
            strategy = current_player(self._board)
            status = self._board.put_piece(
                strategy[0], strategy[1], current_player.chess_piece
            )
            if status == 0:
                count_mistake = 0
                self._board.display_board()
                current_player = self._switch_player(current_player.name)
            elif status == -1:
                count_mistake += 1

        winner, d_value = self._board.calculate_winner()
        """-------------------------------------------------------"""
        # 以下输出模块需要在UI上相应体现
        if winner == "D":
            print("Draw...")
        elif winner == BLACK:
            print(f"The winner is {self._black_player.name} and win {d_value} pieces")
        elif winner == WHITE:
            print(f"The winner is {self._white_player.name} and win {d_value} pieces")
        """-------------------------------------------------------"""


if __name__ == "__main__":
    # debug here
    pass
