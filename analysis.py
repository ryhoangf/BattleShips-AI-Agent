from engine import Game
from matplotlib import pyplot

n_games = 1000
n_shots = []
nwins1 = 0
nwins2 = 0

for i in range(n_games):
    game = Game(human1= False, human2=False)
    #chỗ này có thể thay đổi logic để xem các thuật toán random và basic thuật toán nào tốt hơn
    while not game.over:
        if game.player1_turn:
            game.basic_ai()
        else:
            game.random_ai()
    n_shots.append(game.n_shots)
    if game.result == 1:
        nwins1 += 1
    elif game.result == 2:
        nwins2 += 1
print(n_shots)
print(nwins1)
print(nwins2)

values = []
for i in range(17, 200):
    values.append(n_shots.count(i))

pyplot.bar(range(17, 200), values)
pyplot.show()