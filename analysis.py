import argparse
import csv
from engine import Game
from matplotlib import pyplot as plt
import statistics

# Danh sách các AI hiện có
AI_MAP = {
    "random": lambda game: game.random_ai(),
    "basic": lambda game: game.basic_ai(),
    "proba": lambda game: game.probabilistic_ai()
}

def run_simulation(ai1, ai2, n_games):
    n_shots = []
    wins_1, wins_2 = 0, 0

    for _ in range(n_games):
        game = Game(human1=False, human2=False)
        while not game.over:
            if game.player1_turn:
                AI_MAP[ai1](game)
            else:
                AI_MAP[ai2](game)
        n_shots.append(game.n_shots)
        if game.result == 1:
            wins_1 += 1
        else:
            wins_2 += 1

    return n_shots, wins_1, wins_2

def plot_results(n_shots, ai1, ai2):
    # Histogram
    plt.figure(figsize=(10, 5))
    plt.hist(n_shots, bins=range(min(n_shots), max(n_shots)+1), color='skyblue', edgecolor='black')
    plt.title(f"Lượt bắn trong {ai1.upper()} vs {ai2.upper()}")
    plt.xlabel("Số lượt bắn để kết thúc trận")
    plt.ylabel("Số trận")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Boxplot
    plt.figure(figsize=(6, 4))
    plt.boxplot(n_shots, vert=False, patch_artist=True, boxprops=dict(facecolor='lightgreen'))
    plt.title("Boxplot số lượt bắn")
    plt.xlabel("Lượt bắn")
    plt.tight_layout()
    plt.show()

def main():
    parser = argparse.ArgumentParser(description="So sánh các AI trong BattleShip")
    parser.add_argument("--ai1", type=str, choices=AI_MAP.keys(), default="basic", help="AI cho player 1")
    parser.add_argument("--ai2", type=str, choices=AI_MAP.keys(), default="random", help="AI cho player 2")
    parser.add_argument("--n", type=int, default=500, help="Số trận mô phỏng")
    args = parser.parse_args()

    print(f"🔍 Đang chạy {args.n} trận: {args.ai1.upper()} vs {args.ai2.upper()}...\n")
    n_shots, wins1, wins2 = run_simulation(args.ai1, args.ai2, args.n)

    print(f"📊 Trung bình lượt bắn: {round(statistics.mean(n_shots), 2)}")
    print(f"📊 Trung vị: {statistics.median(n_shots)}")
    print(f"📉 Min: {min(n_shots)} — Max: {max(n_shots)}")
    print(f"🏆 {args.ai1.upper()} thắng: {wins1} trận ({wins1/args.n*100:.1f}%)")
    print(f"🏆 {args.ai2.upper()} thắng: {wins2} trận ({wins2/args.n*100:.1f}%)")

    plot_results(n_shots, args.ai1, args.ai2)

if __name__ == "__main__":
    main()
