# coding: utf-8

import math
import random
import time
import numpy

from Board import Board, Game
from copy import deepcopy


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

class Tree:
    def __init__(self, root = None):
        self.root = root
        self.depth = 0

class Monte_Carlo_Tree_Search:
    def __init__(self, name, chess_piece, SCALAR=2, MAX_DEPTH=64, cnt = 0):
        '''
        :param chess_piece: 玩家棋子 
        :param SCALAR: UCB公式中的超参
        :param MAX_DEPTH: 最大搜索深度
        '''
        self.name = name
        self.chess_piece = chess_piece
        self.SCALAR = SCALAR
        self.MAX_DEPTH = MAX_DEPTH
        self.cnt = cnt
    def set_root(self, node):
        self.root = node

    def set_state(self, state):
        self.root.state = state

    def expand_all(self, node):
        strategy_list = node.state.judge_all_drops(node.chess_piece)
        if len(strategy_list) == 0:
            return node.parent

        for strategy in strategy_list:
            for no in node.children:
                if no.strategy == strategy:
                    continue
            new_state = deepcopy(node.state)
            new_state.drop(strategy[0], strategy[1], node.chess_piece)
            chess_piece = 'O' if node.chess_piece == 'X' else 'X'
            node.add_child(new_state, strategy, chess_piece)

        return node.children[-1]


    def select(self, node, T):
        '''

        :param node: Node, 蒙特卡洛树的当前根节点
        :return: Node, 某一子节点
        '''
        count = deepcopy(T.depth)
        if node is not None:
            while node.state.judge_end() == '·' and count < self.MAX_DEPTH:
                if not node.full_expand():
                    return self.expand(node)
                else:
                    node = self.calculate_ucb(node)
                if node is None:
                    return node
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

        chess_piece = 'O' if node.chess_piece == 'X' else 'X'
        node.add_child(new_state, strategy, chess_piece)

        return node.children[-1]

    def simulate(self, node, T):
        '''
        随机演绎获得分数
        :param node:
        :return: 本次模拟终局时的AI得分
        '''
        if node is None:
            return node
        board = deepcopy(node.state)
        chess_piece = node.chess_piece
        count = deepcopy(T.depth)
        while board.judge_end() == '·':
            strategy_list = node.state.judge_all_drops(chess_piece)
            if len(strategy_list) == 0:
                chess_piece = 'O' if chess_piece == 'X' else 'X'
                strategy_list = node.state.judge_all_drops(chess_piece)
                if len(strategy_list) == 0:
                    break

            strategy = random.choice(strategy_list)
            board.drop(strategy[0], strategy[1], chess_piece)
            chess_piece = 'O' if chess_piece == 'X' else 'X'

            count += 1
            if count > self.MAX_DEPTH:
                break

        winner, d_value = board.calculate_winner()
        '''---------WARNING---------'''
        # might be buggy here
        if winner == '·':
            reward = 0
        elif winner == chess_piece:
            reward = -(10 + d_value)
        else:
            reward = 10 + d_value
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
        if node is None:
            return node
        best_score = -float('inf')
        best_children = []
        for child in node.children:
            if child.visits == 0:
                # print('catch zero')
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

    def find_best_strategy(self, root, T):
        '''

        :param root: 整个蒙特卡洛树的初始根节点, 其节点状态对应棋盘的当前状态
        :return: 当前的最佳行棋策略
        '''
        for t in range(self.MAX_DEPTH):
            leave_node = self.select(root, T)
            reward = self.simulate(leave_node, T)
            self.back_propagate(leave_node, reward)
            best_child = self.calculate_ucb(root)
        if best_child is None:
            return [1]
        T.root = best_child
        T.root.parent = None
        return best_child.strategy

    '''def __call__(self, board, tree):
        state = deepcopy(board)
            # debug here
        if state.judge_all_drops(self.chess_piece) == []:
            return [1]
        if tree.root is None:
            tree.root = Node(state=state, chess_piece=self.chess_piece)
        strategy = self.find_best_strategy(tree.root, tree)
        tree.depth += 1
        return strategy'''

    def __call__(self, board, tree1, tree2, flag):
        if flag == 1:
            state = deepcopy(board)
            # debug here
            if state.judge_all_drops(self.chess_piece) == []:
                return [1]
            if tree1.root is None:
                tree1.root = Node(state=state, chess_piece=self.chess_piece)
            strategy = self.find_best_strategy(tree1.root, tree1)
            tree1.depth += 1
            return strategy
        else:
            state = deepcopy(board)
            # debug here
            if state.judge_all_drops(self.chess_piece) == []:
                return []
            if tree1.root is None:
                tree1.root = Node(state=state, chess_piece=self.chess_piece)
            strategy = self.find_best_strategy(tree1.root, tree1)
            if strategy is [1]:
                return []
            if tree2.root is not None:
                self.expand_all(tree2.root)
                for child in tree2.root.children:
                    sign = 1
                    for i in range(8):
                        for j in range(8):
                            if child.state.get_state()[i][j] != tree1.root.state.get_state()[i][j]:
                                sign = 0
                                break
                    if sign == 1:
                        tree2.root = child
                        tree2.root.parent = None
                        tree2.depth += 1
                        tree2.root.visits += 1
                        break
            tree1.depth += 1
            return strategy

class Human_Player:
    def __init__(self, name, chess_piece):
        self.name = name
        self.chess_piece = chess_piece

    def __call__(self, board, T):
        '''

        :param board: 棋盘, 为保证与AI类的call函数参数一致, 无特殊含义,
        :param T: 蒙特卡洛搜索树
        :return: strategy->list, len = 2,
                 while:
                    strategy[0] = x
                    strategy[1] = y
        '''
        # 需要从UI界面获得玩家的点击坐标并反馈至该函数

        return strategy


if __name__ == '__main__':
    T1 = Tree()
    T2 = Tree()
    p1 = Monte_Carlo_Tree_Search('AI_1', 'X')
    p2 = Monte_Carlo_Tree_Search('AI_2', 'O')
    game = Game(p1, p2, T1, T2, 0)
    game.play_game()
