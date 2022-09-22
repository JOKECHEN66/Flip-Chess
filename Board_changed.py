# coding: utf-8
import time


class Board:
    def __init__(self):
        self._board = []
        # 棋盘初始化
        for i in range(8):
            tmp = ['·' for i in range(8)]
            self._board.append(tmp)
        self._board[3][3], self._board[4][4] = 'X', 'X'
        self._board[3][4], self._board[4][3] = 'O', 'O'
        # 判断是否可以产生翻转的八个方向
        self._directions = [[-1, -1], [-1, 0], [-1, 1], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1]]
        
    def show_board(self):
        # 在UI中打印棋盘信息
        pass

    def display_board(self):
        # 在控制台上打印棋盘
        print('    1    2    3    4    5    6    7    8')
        for index, board in enumerate(self._board):
            print(index + 1, board)

    def put_piece(self, x, y, chess_piece):
        '''

        :param x: 坐标x, 对应行
        :param y: 坐标y, 对应列
        :param chess_piece: 玩家棋子
        :return:
        '''
        assert isinstance(chess_piece, str)
        # 不可重复落子
        if self._board[x][y] != '·':
            print('Cannot repeat the drop...')
            return -1

        if self.drop(x, y, chess_piece):
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
        '''
        判断本次落子是否可以产生翻转
        :param x:
        :param y:
        :param chess_piece:
        :return:
        '''
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
                if self._board[i][j] == '·':
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
                if self._board[i][j] == '·':
                    can_flip, _ = self._judge_flip(i, j, chess_piece)
                    if can_flip:
                        strategy.append([i, j])

        return strategy

    # 此函数暂时无调用, 闲置
    '''
    def judge_area(self, chess_piece):
        flip = False
        for i in range(8):
            for j in range(8):
                if self._board[i][j] == '·':
                    can_flip, _ = self._judge_flip(i, j, chess_piece)
                    flip |= can_flip

        return flip
    '''

    def judge_end(self):
        # 判断全局是否仍有可以落子的坐标
        flip = False
        for i in range(8):
            for j in range(8):
                if self._board[i][j] == '·':
                    can_flip, _ = self._judge_flip(i, j, 'O')
                    flip |= can_flip
                    can_flip, _ = self._judge_flip(i, j, 'X')
                    flip |= can_flip

        if not flip:
            winner, _ = self.calculate_winner()
            return winner

        return '·'

    def calculate_winner(self):
        count_O = 0
        count_X = 0
        for i in range(8):
            for j in range(8):
                if self._board[i][j] == 'O':
                    count_O += 1
                if self._board[i][j] == 'X':
                    count_X += 1
        if count_O != count_X:
            if count_O > count_X:
                return 'O', abs(count_O - count_X)
            else:
                return 'X', abs(count_O - count_X)
        else:
            return 'D', 0

    def get_state(self):
        return self._board

    def judge_some(self, root2):
        return 0
class Game:
    def __init__(self, black_player, white_player, tree1, tree2, flag):
        self._board = Board()
        self._black_player = black_player
        self._white_player = white_player
        self.tree1 = tree1
        self.tree2 = tree2
        self.flag = flag

    def _switch_player(self, name):
        if name == self._black_player.name:
            return self._white_player
        else:
            return self._black_player


    def play_game(self):
        status = 0
        count_mistake = 0
        current_player = self._black_player
        while self._board.judge_end() == '·' and count_mistake < 3:
            '''-------------------------------------------------------'''
            # 以下输出模块需要在UI上相应体现
            print(f'current player is: {current_player.name}')
            '''-------------------------------------------------------'''
            strategy = current_player(self._board, self.tree1, self.tree2, self.flag)

            if strategy == []:
                print('catch no strategy here...')
                input()
                tree = self.tree1
                self.tree1 = self.tree2
                self.tree2 = tree
                current_player = self._switch_player(current_player.name)
                continue
            status = self._board.put_piece(strategy[0], strategy[1], current_player.chess_piece)
            if status == 0:
                tree = self.tree1
                self.tree1 = self.tree2
                self.tree2 = tree
                count_mistake = 0
                self._board.display_board()
                current_player = self._switch_player(current_player.name)
            elif status == -1:
                count_mistake += 1


        winner, d_value = self._board.calculate_winner()
        '''-------------------------------------------------------'''
        # 以下输出模块需要在UI上相应体现
        if winner == 'D':
            print('Draw...')
        elif winner == 'X':
            print(f'The winner is {self._black_player.name} and win {d_value} pieces')
        elif winner == 'O':
            print(f'The winner is {self._white_player.name} and win {d_value} pieces')
        '''-------------------------------------------------------'''


if __name__ == '__main__':
    # debug here
    pass

