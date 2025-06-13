import argparse
import csv
import time
import random
import statistics
import numpy as np
from itertools import combinations
from engine import Game
import matplotlib.pyplot as plt
from collections import defaultdict

# Danh sách các AI hiện có
AI_MAP = {
    "random": lambda game: game.random_ai(),
    "basic": lambda game: game.basic_ai(),
    "proba": lambda game: game.probabilistic_ai()
}


class AIAnalyzer:
    def __init__(self, ais=None, n_games=100, seeds=None):
        self.ais = ais if ais else list(AI_MAP.keys())
        self.n_games = n_games
        self.seeds = seeds if seeds else [None] * n_games
        self.results = []
        self.summary = defaultdict(dict)

    def run_match(self, ai1, ai2, seed=None):
        """Chạy một trận đấu đơn giữa hai AI và trả về kết quả."""
        if seed is not None:
            random.seed(seed)       #Nếu seed được cung cấp, thiết lập seed đó

        game = Game(human1=False, human2=False)     #No h vs h
        start_time = time.time()

        while not game.over:
            if game.player1_turn:
                AI_MAP[ai1](game)
            else:
                AI_MAP[ai2](game)

        end_time = time.time()
        match_time = end_time - start_time

        return {  #Trả về kết quả trận đấu
            'n_shots': game.n_shots,
            'shots_p1': game.shots_p1,
            'shots_p2': game.shots_p2,
            'winner': ai1 if game.result == 1 else ai2,
            'loser': ai2 if game.result == 1 else ai1,
            'time': match_time
        }

    def run_tournament(self):
        """Chạy một giải đấu giữa tất cả các cặp AI."""
        pairs = list(combinations(self.ais, 2))     #Tạo các cặp đấu khác nhau
        total_matches = len(pairs) * self.n_games

        print(f"🔍 Running {total_matches} matches across {len(pairs)} AI pairs...")

        match_count = 0
        for ai1, ai2 in pairs:
            print(f"\n⚔️ {ai1.upper()} vs {ai2.upper()}: ", end="")

            for i in range(self.n_games):
                seed = self.seeds[i]
                match_result = self.run_match(ai1, ai2, seed)
                match_result['ai1'] = ai1
                match_result['ai2'] = ai2
                match_result['game_id'] = i
                match_result['seed'] = seed
                self.results.append(match_result)

                match_count += 1
                if i % 10 == 0:
                    print(".", end="", flush=True)

            print(f" {self.n_games} matches complete")

        print(f"\n✅ Tournament complete: {match_count} matches played")
        self.analyze_results()

    def analyze_results(self):
        """Phân tích kết quả giải đấu và tạo ra các thống kê."""
        # Khởi tạo cấu trúc dữ liệu cho việc phân tích
        for ai in self.ais:
            self.summary[ai] = {
                'games': 0,
                'wins': 0,
                'shots': [],
                'times': [],
                'opponents': defaultdict(lambda: {'wins': 0, 'games': 0})
            }

        # Xử lý kết quả mỗi trận đấu
        for match in self.results:
            ai1, ai2 = match['ai1'], match['ai2']
            winner = match['winner']

            # Cập nhật tóm tắt cho cả hai AI
            for ai in [ai1, ai2]:
                self.summary[ai]['games'] += 1
                if ai == winner:
                    self.summary[ai]['wins'] += 1

                # Theo dõi số lượt bắn cho AI này
                if ai == ai1:
                    self.summary[ai]['shots'].append(match['shots_p1'])
                else:
                    self.summary[ai]['shots'].append(match['shots_p2'])

                self.summary[ai]['times'].append(match['time'] / 2)  # Thời gian ước tính cho mỗi AI

            # Cập nhật thống kê đối đầu
            opponent = ai2 if winner == ai1 else ai1
            self.summary[winner]['opponents'][opponent]['wins'] += 1
            self.summary[ai1]['opponents'][ai2]['games'] += 1
            self.summary[ai2]['opponents'][ai1]['games'] += 1

        # Tính toán các thống kê dẫn xuất
        for ai in self.ais:
            stats = self.summary[ai]
            shots = stats['shots']

            stats['win_rate'] = stats['wins'] / stats['games'] if stats['games'] > 0 else 0
            stats['avg_shots'] = sum(shots) / len(shots) if shots else 0
            stats['median_shots'] = statistics.median(shots) if shots else 0
            stats['min_shots'] = min(shots) if shots else 0
            stats['max_shots'] = max(shots) if shots else 0
            stats['std_shots'] = statistics.stdev(shots) if len(shots) > 1 else 0
            stats['avg_time'] = sum(stats['times']) / len(stats['times']) if stats['times'] else 0

            # Tính tỷ lệ thắng trước mỗi đối thủ
            for opp, data in stats['opponents'].items():
                data['win_rate'] = data['wins'] / data['games'] if data['games'] > 0 else 0

    def print_summary(self):
        """In ra một bản tóm tắt của kết quả giải đấu."""
        print("\n====== AI TOURNAMENT SUMMARY ======")

        # Sắp xếp các AI theo tỷ lệ thắng
        sorted_ais = sorted(self.ais, key=lambda ai: self.summary[ai]['win_rate'], reverse=True)

        # In bảng thống kê chính
        print("\n📊 OVERALL PERFORMANCE:")
        header = ["AI", "Games", "Wins", "Win Rate", "Avg Shots", "Std Dev", "Avg Time(s)"]
        rows = []

        for ai in sorted_ais:
            stats = self.summary[ai]
            rows.append([
                ai.upper(),
                stats['games'],
                stats['wins'],
                f"{stats['win_rate']:.1%}",
                f"{stats['avg_shots']:.1f}",
                f"{stats['std_shots']:.2f}",
                f"{stats['avg_time']:.3f}"
            ])

        self._print_table(header, rows)

        # In ma trận đối đầu
        print("\n🥊 MATCHUP WIN RATES (row vs column):")
        header = [""] + [ai.upper() for ai in sorted_ais]
        rows = []

        for ai1 in sorted_ais:
            row = [ai1.upper()]
            for ai2 in sorted_ais:
                if ai1 == ai2:
                    row.append("--")
                else:
                    win_rate = self.summary[ai1]['opponents'][ai2]['win_rate']
                    row.append(f"{win_rate:.1%}")
            rows.append(row)

        self._print_table(header, rows)

        # Đề xuất AI tốt nhất
        print("\n🏆 BEST AI BY CATEGORY:")
        best_win_rate = max(self.ais, key=lambda ai: self.summary[ai]['win_rate'])
        best_avg_shots = min(self.ais, key=lambda ai: self.summary[ai]['avg_shots'])

        print(f"- Highest Win Rate: {best_win_rate.upper()} ({self.summary[best_win_rate]['win_rate']:.1%})")
        print(f"- Lowest Avg Shots: {best_avg_shots.upper()} ({self.summary[best_avg_shots]['avg_shots']:.1f})")

        # Đề xuất tổng thể (chấm điểm đơn giản: 2 * xếp hạng tỷ lệ thắng + xếp hạng số lượt bắn trung bình)
        win_rate_ranking = {ai: i for i, ai in
                            enumerate(sorted(self.ais, key=lambda x: self.summary[x]['win_rate'], reverse=True))}
        shot_ranking = {ai: i for i, ai in enumerate(sorted(self.ais, key=lambda x: self.summary[x]['avg_shots']))}

        scores = {ai: 2 * win_rate_ranking[ai] + shot_ranking[ai] for ai in self.ais}
        best_overall = min(scores, key=scores.get)

        print(f"\n🎖️ OVERALL BEST AI: {best_overall.upper()}")

    def _print_table(self, header, rows):
        """In một bảng đã được định dạng."""
        # Tính toán độ rộng cột
        widths = [max(len(str(row[i])) for row in [header] + rows) for i in range(len(header))]

        # In tiêu đề
        header_str = " | ".join(f"{h:{w}}" for h, w in zip(header, widths))
        print(header_str)
        print("-" * len(header_str))

        # In các hàng
        for row in rows:
            print(" | ".join(f"{c:{w}}" for c, w in zip(row, widths)))

    def plot_results(self):
        """Tạo các biểu đồ trực quan hóa cho kết quả giải đấu."""
        # Tạo hình với các biểu đồ con
        fig = plt.figure(figsize=(15, 10))

        # 1. So sánh tỷ lệ thắng
        ax1 = plt.subplot(2, 3, 1)
        sorted_ais = sorted(self.ais, key=lambda ai: self.summary[ai]['win_rate'])
        win_rates = [self.summary[ai]['win_rate'] for ai in sorted_ais]
        bars = ax1.barh([ai.upper() for ai in sorted_ais], win_rates, color='skyblue')
        ax1.set_title('Win Rates')
        ax1.set_xlabel('Win Rate')
        ax1.set_xlim(0, 1)
        for bar in bars:
            width = bar.get_width()
            ax1.text(width + 0.01, bar.get_y() + bar.get_height() / 2, f'{width:.1%}',
                     va='center')

        # 2. So sánh số lượt bắn trung bình
        ax2 = plt.subplot(2, 3, 2)
        sorted_by_shots = sorted(self.ais, key=lambda ai: self.summary[ai]['avg_shots'])
        avg_shots = [self.summary[ai]['avg_shots'] for ai in sorted_by_shots]
        bars = ax2.barh([ai.upper() for ai in sorted_by_shots], avg_shots, color='lightgreen')
        ax2.set_title('Average Shots')
        ax2.set_xlabel('Shots')
        for bar in bars:
            width = bar.get_width()
            ax2.text(width + 0.5, bar.get_y() + bar.get_height() / 2, f'{width:.1f}',
                     va='center')

        # 3. Biểu đồ hộp của phân phối số lượt bắn
        ax3 = plt.subplot(2, 3, 3)
        shot_data = [self.summary[ai]['shots'] for ai in self.ais]
        ax3.boxplot(shot_data, vert=False, tick_labels=[ai.upper() for ai in self.ais])
        ax3.set_title('Shot Distribution')
        ax3.set_xlabel('Number of Shots')

        # 4. Bản đồ nhiệt tỷ lệ thắng
        ax4 = plt.subplot(2, 3, 4)
        matrix = np.zeros((len(self.ais), len(self.ais)))
        for i, ai1 in enumerate(self.ais):
            for j, ai2 in enumerate(self.ais):
                if ai1 != ai2:
                    matrix[i, j] = self.summary[ai1]['opponents'][ai2]['win_rate']

        im = ax4.imshow(matrix, cmap='YlGnBu')
        ax4.set_title('Win Rate Matrix')
        ax4.set_xticks(range(len(self.ais)))
        ax4.set_yticks(range(len(self.ais)))
        ax4.set_xticklabels([ai.upper() for ai in self.ais])
        ax4.set_yticklabels([ai.upper() for ai in self.ais])
        plt.colorbar(im, ax=ax4)

        # Thêm chú thích văn bản vào bản đồ nhiệt
        for i in range(len(self.ais)):
            for j in range(len(self.ais)):
                if i != j:
                    text = f"{matrix[i, j]:.1%}"
                else:
                    text = "--"
                ax4.text(j, i, text, ha="center", va="center", color="black")

        # 5. Biểu đồ tần suất phân phối số lượt bắn
        ax5 = plt.subplot(2, 3, (5, 6))
        for ai in self.ais:
            shots = self.summary[ai]['shots']
            values, counts = np.unique(shots, return_counts=True)
            ax5.plot(values, counts, marker='o', label=ai.upper())

        ax5.set_title('Shot Distribution (Line Chart)')
        ax5.set_xlabel('Number of Shots')
        ax5.set_ylabel('Frequency')
        ax5.legend()

    def save_results(self, filename):
        """Lưu kết quả vào các tệp CSV."""
        # Lưu kết quả trận đấu
        with open(f"{filename}_matches.csv", 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['ai1', 'ai2', 'winner', 'loser', 'n_shots',
                                                   'shots_p1', 'shots_p2', 'time', 'game_id', 'seed'])
            writer.writeheader()
            for match in self.results:
                writer.writerow(match)

        # Lưu thống kê tóm tắt
        with open(f"{filename}_summary.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['AI', 'Games', 'Wins', 'Win Rate', 'Avg Shots', 'Median Shots',
                             'Min Shots', 'Max Shots', 'Std Shots', 'Avg Time'])

            for ai in self.ais:
                stats = self.summary[ai]
                writer.writerow([
                    ai, stats['games'], stats['wins'], stats['win_rate'],
                    stats['avg_shots'], stats['median_shots'], stats['min_shots'],
                    stats['max_shots'], stats['std_shots'], stats['avg_time']
                ])

        print(f"\n💾 Results saved to {filename}_matches.csv and {filename}_summary.csv")


def main():
    parser = argparse.ArgumentParser(description="Enhanced AI comparison for Battleship")
    parser.add_argument("--ais", type=str, nargs='+', choices=AI_MAP.keys(),
                        help="AIs to compare (default: all)") # Các AI để so sánh (mặc định: tất cả)
    parser.add_argument("--n", type=int, default=100,
                        help="Number of games per AI pair (default: 100)") # Số trận mỗi cặp AI (mặc định: 100)
    parser.add_argument("--seeds", type=int, nargs='+',
                        help="Random seeds (for reproducibility)") # Các seed ngẫu nhiên (để có thể tái lặp)
    parser.add_argument("--output", type=str,
                        help="Base filename to save results") # Tên tệp cơ sở để lưu kết quả
    parser.add_argument("--no-plot", action="store_true",
                        help="Skip plotting results") # Bỏ qua việc vẽ biểu đồ kết quả
    args = parser.parse_args()

    analyzer = AIAnalyzer(ais=args.ais, n_games=args.n, seeds=args.seeds)
    analyzer.run_tournament()
    analyzer.print_summary()

    if args.output:
        analyzer.save_results(args.output)

    if not args.no_plot:
        analyzer.plot_results()


if __name__ == "__main__":
    main()
