import networkx as nx
import random
import numpy as np
import operator
import itertools
import pprint
import matplotlib.pyplot as plt
from collections import OrderedDict
import sympy
# import esgame
# import class_graphs2

'''ゲームのプレイヤーに関するクラス'''
class Simple_players:
    #players_id = 0 #固有識別番号
    #このゲームでは混合戦略(ベイジアンゲームの純戦略を決める閾値)を与えている。
    """このクラスは4つの重要な変数（p_defect, belief, games_played, players_played）を持つが、当面beliefはコメントアウトする。"""
    def __init__(self, p, players_id):#初期化時点でbeliefを当面含めない。
        self.p_defect = p #純戦略も表記できる(p=0 or 1でC or D一択)。このゲームでDを選ぶ確率を与える。純化したベイジアンゲームの閾値にも見える。       
        self.reset() #初期化時点で、自分自身に自分自身のアトリビュートのresetを参照させて、このオブジェクトが保有する変数games_played, players_playedを初期化している。
        # self.belief = belief #これの初期化はclass beliefでやる。
        """生成したインスタンスの固有番号"""
        self.SPidNum = players_id
        #self.players_id += 1
    
    def reset(self):
        self.games_played = list() #empty list　
        self.players_played = list()
    def move(self):
        """playの仕方、その１（混合戦略）"""
        return random.uniform(0,1) < self.p_defect
        # 比較文はTrue, Falseを返すことを使っている。Trueが戻ってくると、下記のようにDなので、[0, p_defect)までが裏切りを選ぶ確率の範囲
        # PythonのルールでFalse = 0なので、以下の利得計算時に[0][0]になる利得行列の位置は（協力、協力）。つまり(False, False)がここではお互い協力の履歴となる。
    # def action(self, game):#delegation to belief
    #     """playの仕方、その２"""
    #     return self.belief.action(self, game)
    def record(self, game):
        self.games_played.append(game) #ゲームの記憶
        opponent = game.opponents[self] #辞書型からキーを使って取り出している。
        self.players_played.append(opponent)
    def history_memory(self, game):
        #playerの履歴の記憶
        #print("------",self)
        history_memory = list(map(operator.itemgetter(game.players.index(self)), game.history)) 
        return history_memory
    def count_own_CorD(self, game, x):#履歴の中のCないしDの回数を数える。
        #xは“defection” (represented by True or 1) or “cooperation” (represented by False or 0)
        own_CorD = self.history_memory(game)
        return own_CorD.count(x) #countは組み込み関数
    def payoff_memory(self, game):
        #playerの利得の記憶
        payoffs = [game.payoffmat[m1][m2] for (m1,m2) in game.history] #Hisoryをイテレーターにして最初の要素から順番に結果、例：(True, False)、を取り出し、それをペイオフ行列の要素の指定に使って各ステージゲームの結果利得をリスト化する。。。
        own_payoff_memory = [x[game.players.index(self)] for x in payoffs] #過去の全部の記憶（完全記憶）
        return own_payoff_memory
    '''update method'''
    def p_update(self,chosen_player_index, oppopnet_payoff, own_payoff, beta):#これは未完成
        # beta = 10
        tmp = np.exp(-(oppopnet_payoff-own_payoff)*beta)
        # print(tmp)
        fermi_prob = 1/(1+tmp)
        randb = random.random()
        #分岐
        if randb < fermi_prob:
            self.p_defect = player_list[chosen_player_index].p_defect
            #自分自身のp_defectを変更する
        else:
            pass
        return self.p_defect #これでdefectを選ぶ確率が変更される。

'''2人ゲーム、つまり２人のペアで行われる対戦インスタンスを作成するクラス'''
class SimpleGame:#あるプレイヤーとあるプレイヤーの対戦を生成する。
    def __init__(self, players, payoffmat):
        #initialize instance attributes
        self.players = players
        self.payoffmat = payoffmat
        self.history = [] #空の一次元リスト
        self.opponents = {self.players[0]:self.players[1], self.players[1]:self.players[0]}
        self.payoffs =[]
        self.row_player_id = self.players[0].SPidNum
        self.column_player_id = self.players[1].SPidNum

    def get_each_player_id(self, player):
        return self.players[self.get_players_index(player)].SPidNum

    def get_players_id_pair(self):
        return (self.row_player_id, self.column_player_id)

    def get_players_index(self, player):#引数で指定したプレイヤーがself.players[0]のself.players[1]のどちらにはいっているかを返す。
        return self.players.index(player)

    def move_run(self, game_iter):
        for _i in range(game_iter):#ここで繰り返す必要はない。かもしれないが、一応繰り返している。
            newmoves = self.players[0].move(), self.players[1].move() #このselfはSimpleGame, moveの引数だとgameに相当する
            # print("__________", newmoves)
            self.history.append(newmoves) 
            self.players[0].record(self)
            self.players[1].record(self)

    # def action_run(self, game_iter):
    #     for _i in range(game_iter):#ここで繰り返す必要はない。かもしれないが、同上
    #         newmoves = self.players[0].action(self), self.players[1].action(self) #このselfはSimpleGame, moveの引数だとgameに相当する
    #         self.history.append(newmoves) 
    #         self.players[0].record(self)
    #         self.players[1].record(self)
    
    def get_total_payoff(self):#累積の利得の合計
        it = iter(self.history)
        # print(it)
        # print("--------------------")
        payoffs = [self.payoffmat[m1][m2] for (m1,m2) in it]
        row_payoff = [x[0] for x in payoffs]
        column_payoff = [x[1] for x in payoffs]
        '''二次元配列なのでpayoffmat[0][0]で1行１列目の利得、例：PAYOFFMAT = [[(3,3),(0,5)], [(5,0),(1,1)]]'''
        total_row_payoff = sum(row_payoff)
        total_column_payoff = sum(column_payoff)
        return {self.players[0] : total_row_payoff, self.players[1] : total_column_payoff} 
    
    def average_payoff(self):
        it = iter(self.history)
        payoffs = [self.payoffmat[m1][m2] for (m1,m2) in it]
        row_payoff = [x[0] for x in payoffs]
        column_payoff = [x[1] for x in payoffs]
        '''二次元配列なのでpayoffmat[0][0]で1行１列目の利得、例：PAYOFFMAT = [[(3,3),(0,5)], [(5,0),(1,1)]]'''
        return {self.players[0] : np.mean(row_payoff), self.players[1] : np.mean(column_payoff)} 

    def get_last_move(self, player):#指定したプレイヤーのラストムーブを取得する。
        if self.history:
            last_move = self.history[-1][self.players.index(player)] #historyの最後の要素（タプル）が２個の要素からなっているので、それを[player]のインデクスで指定する。
        else:
            last_move = None
        return last_move

'''ネットワークを作るクラス、完全グラフ、直線、正方格子'''

"""完全グラフの作成"""

class make_graph_complete(object):

    def __init__(self):
        """空のグラフオブジェクトを生成する"""
        self.G = nx.Graph()

    def insert_nodes(self, nodes):
        """ノードをグラフに追加する"""
        self.G.add_nodes_from(list(range(nodes)))

    def insert_edges_complete(self, nodes):
        """ノードを追加し、そのコンビネーションを全部つなぐ"""
        self.G.add_nodes_from(list(range(nodes)))
        node_pairs = [(i, j) for i in self.G.nodes() for j in range(i+1, len(self.G.nodes()))]
        self.G.add_edges_from(node_pairs)

    def get_nodes_list(self):
        """各ノードの接続相手のリストを取得"""
        theta_all = [nx.node_connected_component(self.G, i) for i in self.G.nodes()] 
        #繋がっているノードの集合全部を取得している隣接ではないが、完全グラフなのでOK
        return theta_all
   
"""完全グラフテスト"""

# Graph = make_graph_complete()
# Graph.insert_nodes(5)
# Graph.insert_edges_complete(5)
# print(Graph.get_nodes_list())

"""直線グラフの作成"""

class line_graph(make_graph_complete):
    line_G_id = 0 #直線グラフの識別番号

    def __init__(self, nodes):
        make_graph_complete.__init__(self)
        self.G = nx.path_graph(nodes)
        self.lGidNum = line_graph.line_G_id
        line_graph.line_G_id += 1
    
    # def line_graph(self, nodes):
    #     self.G = nx.path_graph(nodes)

    def getlGidNum(self):
        """生成したインスタンスに固有IDを付与する。"""
        return self.lGidNum
    
    def get_lnodes_list(self):
        """各ノードの接続相手のリストを取得"""
        theta_all = [list(nx.all_neighbors(self.G, i)) for i in list(self.G.nodes)]
        return theta_all

"""直線グラフテスト"""
# LGraph = line_graph(4)
# # LGraph.line_graph(4)
# print(list(LGraph.G.nodes()))
# print(LGraph.get_lnodes_list())
# print(LGraph.getlGidNum())

"""正方格子グラフの作成"""

class seihou_koushi(object):
    Seihou_G_id = 0

    def __init__(self, L, periodic):
        super().__init__()
        """次数４の2次元正方格子の作成"""
        self.G = nx.grid_2d_graph(L, L, periodic=periodic) #periodic=Trueで周期境界
        self.seihou_koushi_idNum = seihou_koushi.Seihou_G_id
        seihou_koushi.Seihou_G_id += 1

    # """次数４の2次元正方格子の作成"""
    # def seihou_koushi_4(self, L, periodic):#Lは正方格子の一辺のノード数
    #     self.G = nx.grid_2d_graph(L, L, periodic=periodic) #periodic=Trueで周期境界
    
    def add_cross_edge(self, shape): 
        """次数４のグラフに斜め方向のエッジを追加して次数８にする関数、shape = [リスト]で渡す。"""   
        for node in self.G.nodes():
            nx_node = (node[0] + 1, node[1] + 1)
            if nx_node[0] < shape[0] and nx_node[1] < shape[1]:
                self.G.add_edge(node, nx_node)
            nx_node = (node[0] + 1, node[1] - 1)
            if nx_node[0] < shape[0] and nx_node[1] >= 0:
                self.G.add_edge(node, nx_node)

    """grid_2d_graphで生成した正方格子はノードが二次元座標で与えられる。番号に変換したい時に以下の２つの関数を使う。"""
    
    def labelling(self, L): #Lは正方格子の一辺のノード数
        """正方格子のノードの座標に番号をつけて、番号をキーにした辞書を作成する"""
        self.labels = OrderedDict((i * L + j, (i, j)) for i, j in self.G.nodes())
        return self.labels

    def get_keys_from_value(self, val):
        """座標の辞書ができている前提（self.labelsがある前提）で値のキーを取得する。"""
        return [k for k, v in self.labels.items() if v == val]
    
    # def nodes_list(self, OrderedDict):#これは動かない。
    #     """labelingで作成した辞書からkeyを取り出してリスト化して、座標に一対一対応した番号リストを作成する。"""
    #     nodes_list = list(OrderedDict.keys())#この作業をしたい場合、このコードを本文中に書く。
    #     return nodes_list

    """座標の辞書ができている前提で隣人のリストを取得する。"""

    def get_rinjin(self, n): #ここではnodeをlabelling()で生成したリストの番号を与えることにしている。
        """あるノードの全ての隣人をリストで取得する。
        self.get_rijin(self.labels[n])#引数nの与え方に注意する。"""
        m_all = list(nx.all_neighbors(self.G, n)) 
        return m_all

    def degree_of_a_node(self, node):
        """ノードの次数を確認する関数"""
        degree_of_a_node = self.G.degree(node)
        return degree_of_a_node

    def getGGidNum(self):
        """生成したインスタンスに固有IDを付与する。"""
        return self.seihou_koushi_idNum


'''正方格子を作る。'''
#次数４で生成
L=3 #最初に１辺のノード数を与える。L×Lの正方格子
GGraph = seihou_koushi(L, False)
#GGraph.seihou_koushi_4(L, False)
# print(GGraph.get_nodes_list())
# print(len(GGraph.get_nodes_list()))

'''ノード座標の順序付辞書を生成する（必須）'''
GGnodes = GGraph.labelling(L)#seihou_koushiのメソッドlabelling()を使用する。
print("ノードをlabellingした辞書=", GGnodes)

'''このノード座標のリスト化は絶対必要'''
#ノード座標のリスト化
nodes_list=list(GGnodes)
print('ノードリスト＝', nodes_list)
# print(list(GGraph.G.nodes))#生成した格子の全ノードを表示して確認。

# # 0番目のノード(0,0)にいるプレイヤーの隣人を取得して表示する。seihou_koushiのメソッドget_rinjin()を使う。
# rinjin_0 = GGraph.get_rinjin(GGnodes[0])
# print(rinjin_0)

# # 逆に座標(0,0)からノードリストの番号に変換する。
# keys = GGraph.get_keys_from_value((0,0))
# print("key=", keys)

"""各プレイヤーの隣人のノード番号のリストを作る。"""
all_neighbors_list =[]#[[ノード０が繋がっているノードのリスト],[ノード１が繋がっているノードのリスト],[ノード２が以下略],以下略]
for j in range(len(nodes_list)):
    current_rinjin = GGraph.get_rinjin(GGnodes[j])
    neighbors_of_a_player = []
    for i in range(len(current_rinjin)):
        keys = GGraph.get_keys_from_value(current_rinjin[i])[0] #keysが要素数１のリストであるため、[0]番目を指定すれば、中身を常に取得できる。
        neighbors_of_a_player.append(keys)
    all_neighbors_list.append(neighbors_of_a_player)
# print("____________", all_neighbors_list)

print('各ノードの隣人のリスト=', all_neighbors_list)
# print(type(all_neighbors_list))

"""与えられた正方格子上に配置された全プレイヤーが、隣接する各プレイヤーとゲームを規定の回数だけ繰り返し、それを隣接するプレイヤー全員と行なう。"""
"""現在は自分自身との対戦は無い。枝リストに着目して対戦を回す。"""
PAYOFFMAT = [[(3,3),(0,5)], [(5,0),(1,1)]] #ゲームの利得行列（囚人のジレンマ）
# PAYOFFMAT = [[(3,3),(0,0)], [(0,0),(1,1)]] #ゲームの利得行列（コーディネーションゲーム）

number_of_repetition = 1 #規定の繰り返し回数

print('利得行列', PAYOFFMAT)
print('隣接ペアとの繰り返し対戦回数', number_of_repetition)

# rA = PAYOFFMAT[0][0][0] #CC
# rB = PAYOFFMAT[1][0][0] #DC
# rC = PAYOFFMAT[0][1][0] #CD
# rD = PAYOFFMAT[1][1][0] #DD
# print("行プレイヤーの利得(CC,DC,CD,DD)=", rA,rB,rC,rD)

# Cp = sympy.Symbol('Cp')
# ep1c = Cp*rA+(1-Cp)*rC
# # print(ep1c.subs([(rA, rA), (rB, rB)]))
# ep1d = Cp*rB+(1-Cp)*rD
# # print(ep1d.subs([(rC, rC), (rD, rD)]))
# print("列プレイヤーの混ぜ=", sympy.solve(ep1c-ep1d))

# Ca = PAYOFFMAT[0][0][1] #CC
# Cb = PAYOFFMAT[1][0][1] #DC
# Cc = PAYOFFMAT[0][1][1] #CD
# Cd = PAYOFFMAT[1][1][1] #DD
# print("列プレイヤーの利得(CC,DC,CD,DD)=", Ca,Cb,Cc,Cd)

# Rp = sympy.Symbol('Rp')
# ep2c = Rp*Ca+(1-Rp)*Cb
# # print(ep2c.subs([(Ca, Ca), (Cb, Cb)]))
# ep2d = Rp*Cc+(1-Rp)*Cd
# # print(ep2d.subs([(Cc, Cc), (Cd, Cd)]))
# print("行プレイヤーの混ぜ=", sympy.solve(ep2c-ep2d))

""""プレイヤーのオブジェクトを生成する。"""
player_list = list()
for i in range(9):#９人生成
    p = random.random()
    # p = 1#p=1を与えている、つまり確率１でDを選ぶ。
    tmp = Simple_players(p, players_id=i) 
    player_list.append(tmp)

print('player_list（プレイヤーオブジェクトのリスト）=', player_list)
# print(type(player_list))

"""上で作った正方格子のネットワーク上にプレイヤーオブジェクトを配置する"""
# print(nx.enumerate_all_cliques(GGraph))
# list(nx.enumerate_all_cliques(GGraph))
# print(GGraph.edges(GGnodes[0][0]))
# G =nx.grid_2d_graph(2,2, False)
# print("___________", G.edges(G[(0,0)]))
# print(list(nx.enumerate_all_cliques(G)))
# print(list(filter(lambda x: len(x) > 1, nx.enumerate_all_cliques(G))))

'''eda_listとは隣人リストを隣接関係として行列で表記したもの'''
#eda_list = [[len(nodes_list)][len(nodes_list)]]
eda_list = [[0 for i in range(len(nodes_list))] for j in range(len(nodes_list))] #node_list X node_list の２次元配列が返ってくる。
#print(eda_list)

for i in range(len(player_list)):
    for j in range(len(all_neighbors_list[i])):
        eda_list[i][all_neighbors_list[i][j]]+=1
#print(eda_list)

for i in range(len(player_list)):
    for j in range(len(all_neighbors_list[i])):
        tmp = all_neighbors_list[i][j]
        if eda_list[i][tmp] == 1:      
            #print(tmp)
            eda_list[tmp][i] = 0

# print(eda_list)

history_memory = []
payoff_memory = []
total_payoff_table = [[0 for i in range(len(nodes_list))] for j in range(len(nodes_list))]
# print(player_list[0])

'''ここまででプレイヤーを生成し、それをネットワーク上に配置しした'''

"""ここからネットワーク上のゲーミングシミュレーション"""
# 基本的にノードとプレイヤーのインデックスはk=kである。例）ノード０にいるプレイヤーのインデックスは０
for i in range(len(player_list)):
    # print('test----', i)
    for j in range(len(player_list)):
        if eda_list[i][j] == 1:
            # print('対戦リスト_', i, j)#自分と対戦相手を表示している。
            #あるプレイヤーとあるプレイヤーの対戦を生成する。
            a_game = SimpleGame(players=(player_list[i], player_list[j]), payoffmat=PAYOFFMAT)
            #対戦を規定回数行なう。
            a_game.move_run(game_iter=number_of_repetition) #この規定回数繰り返しとはラウンド一周中に同じ隣接ペアで何回繰り返すか、ラウンドは隣接ペアを一回りして終了する。
            
            #諸々の確認
            # print(a_game.history)#プレイの履歴を表示
            # print(player_list[i].payoff_memory(a_game))#自分の利得を表示
            # print(player_list[j].payoff_memory(a_game))#相手の利得を表示
            # print(a_game.average_payoff())
            # print(a_game.get_total_payoff())
            # print(player_list[i].history_memory(a_game))
            # print(player_list[i].payoff_memory(a_game))
            tmp_total = a_game.get_total_payoff()
            tmp_i = tmp_total.get(player_list[i])
            # print(tmp)
            tmp_j = tmp_total.get(player_list[j])
            total_payoff_table[i][j] = tmp_i
            total_payoff_table[j][i] = tmp_j
            # print(total_payoff_table[i][j])
            # print(total_payoff_table[j][i])

            # history_memory.append(player_list[i].history_memory(a_game))
            # payoff_memory.append(player_list[i].payoff_memory(a_game))
            # for j in range(len(all_neighbors_list[i]):

            #print(history_memory)
            #test = list(zip(history_memory, payoff_memory))
            # print(test)
            
            #print(player_list[0].record(a_game))

print("全員の利得流列=", total_payoff_table)
print("ノード０のプレイヤーの得点=", sum(total_payoff_table[0])) #自分がその期において得た得点の合計

'''この得点の合計とランダムに選んだ隣人の同じ合計と比較して、アップデート（行動の選択を変える）する'''
#現在、updateはフェルミ関数で行っている。確率で戦略を変更する。

'''とりあえず一周してすべてのプレイヤーの全ての対戦終了後に、プレイヤーを０番に固定して０番のアップデートまでする作戦

# print(all_neighbors_list[0])#ノード０番にいるプレイヤー０の隣人のリスト、ノード１（プレイヤー１）とノード３（プレイヤー３）が出る。
print('1のD確率', player_list[1].p_defect)
print('3のD確率', player_list[3].p_defect)
# print(total_payoff_table[1])
# print(total_payoff_table[all_neighbors_list[0][0]])#ノード１（プレイヤー１）の得点
# print(total_payoff_table[all_neighbors_list[0][1]])#ノード３（プレイヤー３）の得点

#print(random.sample(all_neighbors_list[0], 1))
x = random.sample(all_neighbors_list[0], 1) #ノード０の隣人からランダムで１人選択する。リストで戻ってくる
# y = x[0] #この代入が必要な理由？？？
print("ランダムに選ばれたプレイヤー",x[0]) #選ばれた隣人のリストの要素は１個なので、０を指定すれば、選ばれた隣人のノード番号が得られる。
# print("x[0]の型", type(x[0]))
# print("x[0]を代入したyの型",type(y))
# ノード番号はそのままプレイヤーのインデックスなので, int型のx[0]はそのまま代入できそうだが、実際にはエラーがでるので、int(x[0])する。
chosen_player_index = int(x[0])
# print("x[0]を代入したchosen_player_indexの型", type(chosen_player_index))
# chosen_player_index = int(y)#この型変換が必要らしい。
# print("int(y)を代入したchosen_player_indexの型", type(chosen_player_index))
# chosen_player_index = y
# print("yを代入したchosen_player_indexの型", type(chosen_player_index))
# print('--------error-------', player_list[x[0]].p_defect)
# print('--------error-------', player_list[chosen_player_index].p_defect)
print("ランダムに選ばれたプレイヤーのp.defect=", player_list[chosen_player_index].p_defect)

print('隣人行列リスト内でのインデックス',all_neighbors_list[0].index(x[0]))#これは、当該０の隣人の配列[1,3]（全プレイヤーの配列ではない）の中で何番目かを返してくる。
chosen_neighbor_index = all_neighbors_list[0].index(x[0])
# print(chosen_neighbor_index)#ランダムに選ばれた隣人の隣人配列内でのインデックス
# print(type(chosen_neighbor_index))
# print('------試しにこれはエラーではない-------', player_list[chosen_neighbor_index].p_defect)
oppopnet_payoff = sum(total_payoff_table[all_neighbors_list[0][chosen_neighbor_index]]) #ランダムに選ばれた隣人のペイオフ
# print(oppopnet_payoff)
own_payoff = sum(total_payoff_table[0])
# print(own_payoff)

#フェルミ関数
beta = 10
tmp = np.exp(-(oppopnet_payoff-own_payoff)*beta)
# print(tmp)
fermi_prob = 1/(1+tmp) #アップデートの確率
print("フェルミ関数の値=", fermi_prob) 

print("ノード０のPlayer０のD確率（更新前）=", player_list[0].p_defect)
# print('選択された相手のD確率（更新前）=', player_list[chosen_player_index].p_defect)

# 戦略の更新
randb = random.random()
#分岐
if randb < fermi_prob:
    player_list[0].p_defect = player_list[chosen_player_index].p_defect
    # player_list[0].p_defectを変更する
else:
    pass

# 更新後の確認
print("ノード０のPlayer０のD確率（更新後）=",player_list[0].p_defect) 
# print('選ばれた相手のD確率（更新後）=',player_list[chosen_player_index].p_defect)

作戦ここまで'''

# # 上がわかれば、fermi関数から更新までをプレイヤークラスのメソッドで行いたい。未完成
# player_list[0].p_update(chosen_player_index, oppopnet_payoff, own_payoff, beta=10)
# print(player_list[0].p_defect)

#更新は同期更新で行なうとし、更新前のp_defectを格納する配列をつくる
l = list()
for i in range(len(player_list)):
    # print(player_list[i])
    # print(player_list[i].p_defect)
    # present_p_defects.append(player_list[i].p_defect)
    l.insert(i, player_list[i].p_defect)
present_p_defects = tuple(l)
print("D確率（更新前）一覧=",present_p_defects)

# '''動的に変更されている。０が１を真似たとして、その０を３が真似るとして、３は１を真似た０の真似をしている。'''
# 上記の理由により、同期更新で行なう。ここで動的というのは私的定義だが、公式定義では非同期の一種らしい。
for i in range(len(player_list)):
    print("ノード", i, "のPlayer", i, "の更新")
    print("ノード", i, "のPlayer", i, "のD確率（更新前）=", player_list[i].p_defect)
    # '''隣人の中から真似る相手の候補をランダムに選ぶ'''
    x = random.sample(all_neighbors_list[i], 1)
    chosen_player_index = int(x[0])
    print("ランダムに選ばれたプレイヤー", chosen_player_index)
    # '''自分とランダムに選んだプレイヤーの利得の差分を計算する。'''
    neighbor_index_ofchosenplayer = all_neighbors_list[i].index(x[0])#これは、当該の隣人だけの配列（全プレイヤーの配列ではない）の中で何番目かを返してくる。
    oppopnet_payoff = sum(total_payoff_table[all_neighbors_list[i][neighbor_index_ofchosenplayer]]) #ランダムに選ばれた隣人の総利得
    own_payoff = sum(total_payoff_table[i])#自分の総利得
    # '''フェルミ関数'''
    beta = 10
    tmp = np.exp(-(oppopnet_payoff-own_payoff)*beta)
    # print(tmp)
    fermi_prob = 1/(1+tmp) #アップデートの確率
    print("フェルミ関数の値=", fermi_prob) 
    # '''アップデート'''
    randb = random.random()#サイコロはプレイヤーごとに振る。
    #分岐
    if randb < fermi_prob:
        player_list[i].p_defect = present_p_defects[chosen_player_index]
        # player_list[i].p_defect = player_list[chosen_player_index].p_defect
        # ここでplayer_list[0].p_defectを変更すると動的変更となるため、これはペンディング
    else:
        pass
    # 更新後の確認
    print("ノード", i, "のPlayer", i, "のD確率（更新後）=",player_list[i].p_defect) 

# 更新後のp_defectsの確認
post_p_defects = list()
for i in range(len(player_list)):
    post_p_defects.insert(i, player_list[i].p_defect)
print("D確率（更新後）一覧=", post_p_defects)