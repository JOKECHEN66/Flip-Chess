# coding: utf-8

import time
import math
import random

from Flip_Chess.Board import Game
from copy import deepcopy

DRAW = -1
EMPTY = 0
BLACK = 1
WHITE = 2

VALUE = [
    [20, -3, 11,  8,  8, 11, -3, 20],
    [-3, -7, -4,  1,  1, -4, -7, -3],
    [11, -4,  2,  2,  2,  2, -4, 11],
    [8,  1,  2, -3, -3,  2,  1,  8],
    [8,  1,  2, -3, -3,  2,  1,  8],
    [11, -4,  2,  2,  2,  2, -4, 11],
    [-3, -7, -4,  1,  1, -4, -7, -3],
    [20, -3, 11,  8,  8, 11, -3, 20]
]

class Node:
    def __init__(self, state, parent=None, strategy=None, chess_piece=None):
        self.visits = 0                 # 当前节点访问次数
        self.reward = 0.0               # 当前节点价值评分
        self.state = state              # 当前节点棋盘状态
        self.children = []              # 当前节点的子节点
        self.parent = parent            # 当前节点的父节点
        self.strategy = strategy        # 当前节点的策略
        self.chess_piece = chess_piece  # 当前节点的棋子类型

    def add_child(self, child_state, strategy, chess_piece):
        '''

        :param child_state: 下一组棋盘状态
        :param strategy: 行棋策略
        :param chess_piece: 玩家棋子
        :return:
        '''
        child_node = Node(child_state, parent=self, strategy=strategy, chess_piece=chess_piece)
        self.children.append(child_node)

    def full_expand(self):
        if len(self.state.judge_all_drops(self.chess_piece)) != len(self.children):
            return False

        return True


class Monte_Carlo_Tree_Search:
    def __init__(self, name, chess_piece, SCALAR=2, MAX_DEPTH=150, WEIGHT=10):
        '''
        
        :param chess_piece: 玩家棋子 
        :param SCALAR: UCB公式中的超参
        :param MAX_DEPTH: 最大搜素深度
        '''
        self.name = name
        self.chess_piece = chess_piece
        self.SCALAR = SCALAR
        self.MAX_DEPTH = MAX_DEPTH
        self.WEIGHT = WEIGHT

    def select(self, node):
        '''

        :param node: Node, 蒙特卡洛树的当前根节点
        :return: Node, 某一子节点
        '''
        count = 0
        while node.state.judge_end() == EMPTY and count < self.MAX_DEPTH:
            if not node.full_expand():
                return self.expand(node)
            else:
                node = self.calculate_ucb(node)

            count += 1

        return node

    def expand(self, node):
        '''

        :param node: Node, 蒙特卡洛树的当前根节点
        :return: Node, 该节点的最后一个子节点
        '''
        strategy_list = node.state.judge_all_drops(node.chess_piece)
        if len(strategy_list) == 0:
            return node.parent

        strategy = random.choice(strategy_list)
        tried_strategy = [child.strategy for child in node.children]
        while strategy in tried_strategy:
            strategy = random.choice(strategy_list)

        new_state = deepcopy(node.state)
        new_state.drop(strategy[0], strategy[1], node.chess_piece)

        chess_piece = WHITE if node.chess_piece == BLACK else BLACK
        node.add_child(new_state, strategy, chess_piece)

        return node.children[-1]

    def simulate(self, node):
        '''
        随机演绎获得分数
        :param node:
        :return: 本次模拟终局时的AI得分
        '''
        board = deepcopy(node.state)
        chess_piece = node.chess_piece
        count = 0
        while board.judge_end() == EMPTY:
            strategy_list = node.state.judge_all_drops(chess_piece)
            if len(strategy_list) == 0:
                chess_piece = WHITE if chess_piece == BLACK else BLACK
                strategy_list = node.state.judge_all_drops(chess_piece)
                if len(strategy_list) == 0:
                    break

            strategy_dict = {}
            for strategy in strategy_list:
                strategy_dict[VALUE[strategy[0]][strategy[1]]] = strategy
            res = sorted(strategy_dict.keys(), reverse=True)
            strategy = strategy_dict[res[0]]

            board.drop(strategy[0], strategy[1], chess_piece)
            chess_piece = WHITE if chess_piece == BLACK else BLACK

            count += 1
            if count > self.MAX_DEPTH:
                break

        winner, d_value = board.calculate_winner()
        num = board.get_corner_number(self.chess_piece)
        '''---------WARNING---------'''
        # might be buggy here
        if winner == DRAW:
            reward = 0
        elif winner == chess_piece:
            reward = -(5 + math.log(d_value) +  self.WEIGHT * num)
        else:
            reward = 5 + math.log(d_value + self.WEIGHT * num)
        '''-------------------------'''

        return reward

    def back_propagate(self, node, reward):
        '''
        反向传播更新树
        :param node:
        :param reward:
        :return:
        '''
        while node is not None:
            node.visits += 1
            if node.chess_piece == self.chess_piece:
                node.reward += reward
            else:
                node.reward -= reward

            node = node.parent

    def calculate_ucb(self, node):
        '''
        按公式计算UCB并选出最佳节点
        :param node:
        :return:
        '''
        best_score = -float('inf')
        best_children = []
        for child in node.children:
            if child.visits == 0:
                best_children = [child]
                break

            score = (child.reward / child.visits) + \
                    self.SCALAR * math.sqrt(math.log(node.visits) / float(child.visits))

            if score > best_score:
                best_score = score
                best_children.append(child)
            if score == best_score:
                best_children.append(child)

        if len(best_children) == 0:
            return node.parent
        return random.choice(best_children)

    def find_best_strategy(self, root):
        '''

        :param root: 整个蒙特卡洛树的初始根节点, 其节点状态对应棋盘的当前状态
        :return: 当前的最佳行棋策略
        '''
        select_time = 0
        simulate_time = 0
        propagate_time = 0
        total_time = 0
        for t in range(self.MAX_DEPTH):
            start = time.time()
            leave_node = self.select(root)
            end_1 = time.time()
            select_time += round(end_1 - start, 5)
            reward = self.simulate(leave_node)
            end_2 = time.time()
            simulate_time += round(end_2 - end_1, 5)
            self.back_propagate(leave_node, reward)
            end_3 = time.time()
            propagate_time += round(end_3 - end_2, 5)
            best_child = self.calculate_ucb(root)
            end = time.time()
            total_time += round(end - start, 5)

        return best_child.strategy, [round(total_time, 5), round(select_time, 5),
                                     round(simulate_time, 5), round(propagate_time, 5)]

    def __call__(self, board):
        state = deepcopy(board)
        if state.judge_all_drops(self.chess_piece) == []:
            return [-999, -999], [0, 0, 0, 0]
        for strategy in state.judge_all_drops(self.chess_piece):
            if strategy in [[0, 0], [7, 7], [0, 7], [7, 0]]:
                return strategy, [0, 0, 0, 0]
        root = Node(state=state, chess_piece=self.chess_piece)
        strategy, total_time = self.find_best_strategy(root)

        return strategy, total_time


class Human_Player:
    def __init__(self, name, chess_piece):
        self.name = name
        self.chess_piece = chess_piece

    def __call__(self, board):
        '''

        :param board: 棋盘, 为保证与AI类的call函数参数一致, 无特殊含义
        :return: strategy->list, len = 2,
                 while:
                    strategy[0] = x
                    strategy[1] = y
        '''
        # 需要从UI界面获得玩家的点击坐标并反馈至该函数

        return strategy


if __name__ == '__main__':
    # p1 = Monte_Carlo_Tree_Search('AI_1', BLACK)
    # p2 = Monte_Carlo_Tree_Search('AI_2', WHITE)
    # game = Game(p1, p2)
    # game.play_game()
    d = {
        4: 2,
        2: 3,
        1: 5,
        3: 4
    }
    res = sorted(d, key=lambda d:d[1], reverse=True)
    print(res)
