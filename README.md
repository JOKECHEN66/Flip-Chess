# Flip-Chess
Use MCTS to achieve a flip chess game

## 环境准备
使用conda新建环境
```shell
-> conda env create -f env.yml
-> conda activate flip_chess
```
---
## 来一局
```shell
-> python3 ./ui_main.py --mode PVE  # fight with AI
-> python3 ./ui_main.py --mode PVP  # fight with your friend
```
### 扩展参数
```shell
--MCTS_SCALAR # type = int 
```
---
## 控制台调用方法
1. 实例化双方玩家对象（包括棋子类型和玩家昵称）  
2. 实例化Game类  
3. 调用play_game()函数  
