# Flip-Chess
Use MCTS to achieve a flip chess game

## 代码结构
|-root  
|--Board.py: 封装棋盘信息和比赛流程  
|--MCTS.py: 封装AI行为（蒙特卡洛树搜索）和玩家行为  

## UI需求
Board.py: 在Game中需要将比赛信息输出至UI中  
MCTS.py: 在Human_Player中需要获取UI点击信息并转化为数据结构list  

需要与UI进行交互的部分均已在代码块的注释中标明  

## 控制台调用方法
1. 实例化双方玩家对象（包括棋子类型和玩家昵称）  
2. 实例化Game类  
3. 调用play_game()函数  
