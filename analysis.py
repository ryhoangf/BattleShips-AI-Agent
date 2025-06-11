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
from scipy.stats import gaussian_kde
import psutil
import os
from datetime import datetime

# Danh sách các AI hiện có
AI_MAP = {
    "random": lambda game: game.random_ai(),
    "basic": lambda game: game.basic_ai(),
    "proba": lambda game: game.probabilistic_ai()
}

class ResourceMonitor:
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = None
        self.start_memory = None
        self.move_times = []
        self.peak_memory = 0
        self.current_memory = 0
        
    def start_monitoring(self):
        """Bắt đầu theo dõi tài nguyên"""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # Convert to MB
        self.current_memory = self.start_memory
        
    def record_move(self):
        """Ghi lại thời gian và bộ nhớ cho một lượt đi"""
        move_time = time.time() - self.start_time
        self.move_times.append(move_time)
        self.current_memory = self.process.memory_info().rss / 1024 / 1024
        self.peak_memory = max(self.peak_memory, self.current_memory)
        self.start_time = time.time()
        
    def get_stats(self):
        """Lấy thống kê về tài nguyên sử dụng"""
        return {
            'avg_move_time': statistics.mean(self.move_times) if self.move_times else 0,
            'max_move_time': max(self.move_times) if self.move_times else 0,
            'min_move_time': min(self.move_times) if self.move_times else 0,
            'std_move_time': statistics.stdev(self.move_times) if len(self.move_times) > 1 else 0,
            'peak_memory': self.peak_memory,
            'final_memory': self.current_memory,
            'memory_increase': self.current_memory - self.start_memory
        }

class AIAnalyzer:
    def __init__(self, ais=None, n_games=100, seeds=None):
        self.ais = ais if ais else list(AI_MAP.keys())
        self.n_games = n_games
        self.seeds = seeds if seeds else [None] * n_games
        self.results = []
        self.summary = defaultdict(dict)
        self.resource_stats = defaultdict(dict)
        self.shot_stats = defaultdict(lambda: {
            'hits': 0,
            'misses': 0,
            'shots_to_first_hit': [],
            'shots_to_sink': defaultdict(list),
            'wasted_shots': 0,
            'ship_sink_sequences': []
        })

    def run_match(self, ai1, ai2, seed=None):
        """Chạy một trận đấu đơn giữa hai AI và trả về kết quả."""
        if seed is not None:
            random.seed(seed)

        game = Game(human1=False, human2=False)
        monitor1 = ResourceMonitor()
        monitor2 = ResourceMonitor()
        
        monitor1.start_monitoring()
        monitor2.start_monitoring()

        # Khởi tạo theo dõi phát bắn
        current_ship_hits = 0
        first_hit_found = False
        shots_to_first_hit = 0
        current_ship_size = 0
        shots_since_first_hit = 0
        last_hit_position = None
        sunk_ships = set()

        while not game.over:
            if game.player1_turn:
                prev_search = game.player1.search.copy()  # Lưu trạng thái bảng trước khi bắn
                AI_MAP[ai1](game)
                monitor1.record_move()
                
                # Phân tích phát bắn
                if game.last_shot is not None:  # Kiểm tra last_shot không phải None
                    current_pos = game.last_shot
                    # Kiểm tra bắn trúng hay trượt
                    if game.player1.search[current_pos] == "H":
                        self.shot_stats[ai1]['hits'] += 1
                        if not first_hit_found:
                            first_hit_found = True
                            self.shot_stats[ai1]['shots_to_first_hit'].append(shots_to_first_hit)
                        current_ship_hits += 1
                        last_hit_position = current_pos
                    else:
                        self.shot_stats[ai1]['misses'] += 1
                        
                    # Kiểm tra tàu bị chìm
                    if game.player1.search[current_pos] == "S":
                        ship_size = game.get_ship_size(2, current_pos)
                        self.shot_stats[ai1]['shots_to_sink'][ship_size].append(shots_since_first_hit)
                        sunk_ships.add(current_pos)
                        current_ship_hits = 0
                        first_hit_found = False
                        shots_since_first_hit = 0
                        
                    # Kiểm tra phát bắn lãng phí
                    if self.is_wasted_shot(game, current_pos, prev_search, sunk_ships):
                        self.shot_stats[ai1]['wasted_shots'] += 1
                        
                    shots_to_first_hit += 1
                    if first_hit_found:
                        shots_since_first_hit += 1
            else:
                prev_search = game.player2.search.copy()
                AI_MAP[ai2](game)
                monitor2.record_move()
                
                # Tương tự cho AI2
                if game.last_shot is not None:  # Kiểm tra last_shot không phải None
                    current_pos = game.last_shot
                    if game.player2.search[current_pos] == "H":
                        self.shot_stats[ai2]['hits'] += 1
                        if not first_hit_found:
                            first_hit_found = True
                            self.shot_stats[ai2]['shots_to_first_hit'].append(shots_to_first_hit)
                        current_ship_hits += 1
                        last_hit_position = current_pos
                    else:
                        self.shot_stats[ai2]['misses'] += 1
                        
                    if game.player2.search[current_pos] == "S":
                        ship_size = game.get_ship_size(1, current_pos)
                        self.shot_stats[ai2]['shots_to_sink'][ship_size].append(shots_since_first_hit)
                        sunk_ships.add(current_pos)
                        current_ship_hits = 0
                        first_hit_found = False
                        shots_since_first_hit = 0
                        
                    if self.is_wasted_shot(game, current_pos, prev_search, sunk_ships):
                        self.shot_stats[ai2]['wasted_shots'] += 1
                        
                    shots_to_first_hit += 1
                    if first_hit_found:
                        shots_since_first_hit += 1

        # Lưu thống kê tài nguyên
        self.resource_stats[ai1] = monitor1.get_stats()
        self.resource_stats[ai2] = monitor2.get_stats()

        return {
            'n_shots': game.n_shots,
            'shots_p1': game.shots_p1,
            'shots_p2': game.shots_p2,
            'winner': ai1 if game.result == 1 else ai2,
            'loser': ai2 if game.result == 1 else ai1,
            'time': time.time() - monitor1.start_time,
            'resource_stats_p1': monitor1.get_stats(),
            'resource_stats_p2': monitor2.get_stats()
        }

    def is_wasted_shot(self, game, pos, prev_search, sunk_ships):
        """Kiểm tra xem một phát bắn có phải là lãng phí không."""
        # Kiểm tra bắn vào ô đã bắn
        if prev_search[pos] != "U":
            return True
            
        # Kiểm tra bắn xung quanh tàu đã chìm
        for sunk_pos in sunk_ships:
            if abs(pos - sunk_pos) <= 1 or abs(pos - sunk_pos) == 10:
                return True
                
        return False

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
                'move_times': [],
                'memory_usage': [],
                'opponents': defaultdict(lambda: {'wins': 0, 'games': 0})
            }

        # Xử lý kết quả mỗi trận đấu
        for match in self.results:
            ai1, ai2 = match['ai1'], match['ai2']
            winner = match['winner']

            # Cập nhật tóm tắt cho cả hai AI
            for ai, stats in [(ai1, match['resource_stats_p1']), (ai2, match['resource_stats_p2'])]:
                self.summary[ai]['games'] += 1
                if ai == winner:
                    self.summary[ai]['wins'] += 1

                # Theo dõi số lượt bắn cho AI này
                if ai == ai1:
                    self.summary[ai]['shots'].append(match['shots_p1'])
                else:
                    self.summary[ai]['shots'].append(match['shots_p2'])

                self.summary[ai]['times'].append(match['time'] / 2)
                self.summary[ai]['move_times'].append(stats['avg_move_time'])
                self.summary[ai]['memory_usage'].append(stats['peak_memory'])

            # Cập nhật thống kê đối đầu
            opponent = ai2 if winner == ai1 else ai1
            self.summary[winner]['opponents'][opponent]['wins'] += 1
            self.summary[ai1]['opponents'][ai2]['games'] += 1
            self.summary[ai2]['opponents'][ai1]['games'] += 1

        # Tính toán các thống kê dẫn xuất
        for ai in self.ais:
            stats = self.summary[ai]
            shots = stats['shots']
            move_times = stats['move_times']
            memory_usage = stats['memory_usage']

            stats['win_rate'] = stats['wins'] / stats['games'] if stats['games'] > 0 else 0
            stats['avg_shots'] = sum(shots) / len(shots) if shots else 0
            stats['median_shots'] = statistics.median(shots) if shots else 0
            stats['min_shots'] = min(shots) if shots else 0
            stats['max_shots'] = max(shots) if shots else 0
            stats['std_shots'] = statistics.stdev(shots) if len(shots) > 1 else 0
            stats['avg_time'] = sum(stats['times']) / len(stats['times']) if stats['times'] else 0
            
            # Thống kê về tài nguyên
            stats['avg_move_time'] = sum(move_times) / len(move_times) if move_times else 0
            stats['max_move_time'] = max(move_times) if move_times else 0
            stats['min_move_time'] = min(move_times) if move_times else 0
            stats['std_move_time'] = statistics.stdev(move_times) if len(move_times) > 1 else 0
            stats['avg_memory'] = sum(memory_usage) / len(memory_usage) if memory_usage else 0
            stats['max_memory'] = max(memory_usage) if memory_usage else 0

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
        header = ["AI", "Games", "Wins", "Win Rate", "Avg Shots", "Avg Time/Move(ms)", "Max Time/Move(ms)", "Avg Memory(MB)"]
        rows = []

        for ai in sorted_ais:
            stats = self.summary[ai]
            rows.append([
                ai.upper(),
                stats['games'],
                stats['wins'],
                f"{stats['win_rate']:.1%}",
                f"{stats['avg_shots']:.1f}",
                f"{stats['avg_move_time']*1000:.1f}",
                f"{stats['max_move_time']*1000:.1f}",
                f"{stats['avg_memory']:.1f}"
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
        best_avg_time = min(self.ais, key=lambda ai: self.summary[ai]['avg_move_time'])
        best_memory = min(self.ais, key=lambda ai: self.summary[ai]['avg_memory'])

        print(f"- Highest Win Rate: {best_win_rate.upper()} ({self.summary[best_win_rate]['win_rate']:.1%})")
        print(f"- Lowest Avg Shots: {best_avg_shots.upper()} ({self.summary[best_avg_shots]['avg_shots']:.1f})")
        print(f"- Fastest Avg Move Time: {best_avg_time.upper()} ({self.summary[best_avg_time]['avg_move_time']*1000:.1f}ms)")
        print(f"- Lowest Memory Usage: {best_memory.upper()} ({self.summary[best_memory]['avg_memory']:.1f}MB)")

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
        fig = plt.figure(figsize=(15, 12))
        plt.subplots_adjust(
            left=0.1,
            right=0.9,
            bottom=0.1,
            top=0.9,
            wspace=0.3,
            hspace=0.4
        )

        # 1. So sánh tỷ lệ thắng
        ax1 = plt.subplot(3, 2, 1)
        sorted_ais = sorted(self.ais, key=lambda ai: self.summary[ai]['win_rate'])
        win_rates = [self.summary[ai]['win_rate'] for ai in sorted_ais]
        bars = ax1.barh([ai.upper() for ai in sorted_ais], win_rates, color='skyblue')
        ax1.set_title('Win Rates', pad=20)
        ax1.set_xlabel('Win Rate', labelpad=10)
        ax1.set_xlim(0, 1)
        for bar in bars:
            width = bar.get_width()
            ax1.text(width + 0.01, bar.get_y() + bar.get_height() / 2, f'{width:.1%}',
                     va='center')

        # 2. So sánh số lượt bắn trung bình
        ax2 = plt.subplot(3, 2, 2)
        sorted_by_shots = sorted(self.ais, key=lambda ai: self.summary[ai]['avg_shots'])
        avg_shots = [self.summary[ai]['avg_shots'] for ai in sorted_by_shots]
        bars = ax2.barh([ai.upper() for ai in sorted_by_shots], avg_shots, color='lightgreen')
        ax2.set_title('Average Shots', pad=20)
        ax2.set_xlabel('Shots', labelpad=10)
        for bar in bars:
            width = bar.get_width()
            ax2.text(width + 0.5, bar.get_y() + bar.get_height() / 2, f'{width:.1f}',
                     va='center')

        # 3. Biểu đồ thời gian trung bình mỗi lượt
        ax3 = plt.subplot(3, 2, 3)
        sorted_by_time = sorted(self.ais, key=lambda ai: self.summary[ai]['avg_move_time'])
        avg_times = [self.summary[ai]['avg_move_time'] * 1000 for ai in sorted_by_time]  # Convert to ms
        bars = ax3.barh([ai.upper() for ai in sorted_by_time], avg_times, color='salmon')
        ax3.set_title('Average Move Time', pad=20)
        ax3.set_xlabel('Time (ms)', labelpad=10)
        for bar in bars:
            width = bar.get_width()
            ax3.text(width + 0.1, bar.get_y() + bar.get_height() / 2, f'{width:.1f}',
                     va='center')

        # 4. Biểu đồ bộ nhớ sử dụng
        ax4 = plt.subplot(3, 2, 4)
        sorted_by_memory = sorted(self.ais, key=lambda ai: self.summary[ai]['avg_memory'])
        avg_memory = [self.summary[ai]['avg_memory'] for ai in sorted_by_memory]
        bars = ax4.barh([ai.upper() for ai in sorted_by_memory], avg_memory, color='lightblue')
        ax4.set_title('Average Memory Usage', pad=20)
        ax4.set_xlabel('Memory (MB)', labelpad=10)
        for bar in bars:
            width = bar.get_width()
            ax4.text(width + 0.1, bar.get_y() + bar.get_height() / 2, f'{width:.1f}',
                     va='center')

        # 5. Biểu đồ phân phối thời gian
        ax5 = plt.subplot(3, 2, (5, 6))
        for ai in self.ais:
            move_times = self.summary[ai]['move_times']
            if len(move_times) > 1:
                kde = gaussian_kde(move_times, bw_method=0.3)
                x_grid = np.linspace(min(move_times), max(move_times), 200)
                ax5.plot(x_grid * 1000, kde(x_grid) * len(move_times), label=ai.upper())
            else:
                ax5.plot([t * 1000 for t in move_times], [1], 'o', label=ai.upper())

        ax5.set_title('Move Time Distribution', pad=20)
        ax5.set_xlabel('Time (ms)', labelpad=10)
        ax5.set_ylabel('Frequency', labelpad=10)
        ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.tight_layout()
        plt.show()

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

    def analyze_probabilistic_ai(self):
        """Phân tích chi tiết về hiệu suất của AI probabilistic."""
        if 'proba' not in self.ais:
            print("Probabilistic AI không có trong danh sách AI được phân tích")
            return

        stats = self.summary['proba']
        shot_stats = self.shot_stats['proba']
        print("\n====== PHÂN TÍCH CHI TIẾT AI PROBABILISTIC ======")
        
        # 1. Hiệu suất tổng thể
        print("\n🎯 HIỆU SUẤT TỔNG THỂ:")
        print(f"- Tỷ lệ thắng: {stats['win_rate']:.1%}")
        print(f"- Số lượt bắn trung bình: {stats['avg_shots']:.1f}")
        print(f"- Độ lệch chuẩn số lượt bắn: {stats['std_shots']:.2f}")
        
        # 2. Phân tích tài nguyên
        print("\n💻 PHÂN TÍCH TÀI NGUYÊN:")
        print(f"- Thời gian trung bình mỗi lượt: {stats['avg_move_time']*1000:.1f}ms")
        print(f"- Thời gian tối đa mỗi lượt: {stats['max_move_time']*1000:.1f}ms")
        print(f"- Bộ nhớ trung bình sử dụng: {stats['avg_memory']:.1f}MB")
        print(f"- Bộ nhớ tối đa sử dụng: {stats['max_memory']:.1f}MB")
        
        # 3. Phân tích hiệu quả bắn
        print("\n🎯 PHÂN TÍCH HIỆU QUẢ BẮN:")
        total_shots = shot_stats['hits'] + shot_stats['misses']
        hit_ratio = shot_stats['hits'] / total_shots if total_shots > 0 else 0
        print(f"- Tỷ lệ bắn trúng: {hit_ratio:.1%}")
        print(f"- Số phát bắn trúng: {shot_stats['hits']}")
        print(f"- Số phát bắn trượt: {shot_stats['misses']}")
        
        # Số phát bắn đến lần trúng đầu tiên
        if shot_stats['shots_to_first_hit']:
            avg_shots_to_first_hit = statistics.mean(shot_stats['shots_to_first_hit'])
            print(f"- Số phát bắn trung bình đến lần trúng đầu tiên: {avg_shots_to_first_hit:.1f}")
        
        # Số phát bắn để đánh chìm tàu
        print("\nSố phát bắn trung bình để đánh chìm tàu (sau khi trúng lần đầu):")
        for ship_size, shots in shot_stats['shots_to_sink'].items():
            if shots:
                avg_shots = statistics.mean(shots)
                print(f"- Tàu {ship_size} ô: {avg_shots:.1f} phát")
        
        # Phân tích phát bắn lãng phí
        wasted_ratio = shot_stats['wasted_shots'] / total_shots if total_shots > 0 else 0
        print(f"\n- Số phát bắn lãng phí: {shot_stats['wasted_shots']} ({wasted_ratio:.1%} tổng số phát)")
        
        # 4. So sánh với các AI khác
        print("\n📊 SO SÁNH VỚI CÁC AI KHÁC:")
        other_ais = [ai for ai in self.ais if ai != 'proba']
        
        # Tỷ lệ thắng
        win_rates = {ai: self.summary[ai]['win_rate'] for ai in other_ais}
        win_rate_improvement = {}
        for ai, rate in win_rates.items():
            if rate > 0:
                win_rate_improvement[ai] = (stats['win_rate'] - rate) / rate * 100
            else:
                win_rate_improvement[ai] = float('inf') if stats['win_rate'] > 0 else 0
        
        print("\nTỷ lệ thắng so với các AI khác:")
        for ai, improvement in win_rate_improvement.items():
            if improvement == float('inf'):
                print(f"- So với {ai.upper()}: +∞% (AI khác không thắng trận nào)")
            else:
                print(f"- So với {ai.upper()}: {improvement:+.1f}%")
            
        # So sánh hiệu quả bắn
        print("\nHiệu quả bắn so với các AI khác:")
        for ai in other_ais:
            other_total = self.shot_stats[ai]['hits'] + self.shot_stats[ai]['misses']
            if other_total > 0:
                other_hit_ratio = self.shot_stats[ai]['hits'] / other_total
                hit_ratio_diff = (hit_ratio - other_hit_ratio) / other_hit_ratio * 100 if other_hit_ratio > 0 else float('inf')
                print(f"- Tỷ lệ bắn trúng so với {ai.upper()}: {hit_ratio_diff:+.1f}%")
                
                other_wasted = self.shot_stats[ai]['wasted_shots'] / other_total
                wasted_diff = (wasted_ratio - other_wasted) / other_wasted * 100 if other_wasted > 0 else float('inf')
                print(f"- Tỷ lệ bắn lãng phí so với {ai.upper()}: {wasted_diff:+.1f}%")
            else:
                print(f"- Không có dữ liệu bắn cho {ai.upper()}")
            
        # 5. Đánh giá tổng thể
        print("\n📈 ĐÁNH GIÁ TỔNG THỂ:")
        strengths = []
        if stats['win_rate'] > 0.7:
            strengths.append("Tỷ lệ thắng rất cao (>70%)")
        if stats['avg_shots'] < 50:
            strengths.append("Số lượt bắn trung bình thấp (<50)")
        if stats['std_shots'] < 10:
            strengths.append("Độ ổn định cao (độ lệch chuẩn thấp)")
        if hit_ratio > 0.4:
            strengths.append(f"Tỷ lệ bắn trúng cao ({hit_ratio:.1%})")
        if wasted_ratio < 0.1:
            strengths.append(f"Tỷ lệ bắn lãng phí thấp ({wasted_ratio:.1%})")
            
        print("\nĐiểm mạnh:")
        for strength in strengths:
            print(f"- {strength}")
            
        print("\nSự đánh đổi:")
        print(f"- Thời gian tính toán cao hơn: {stats['avg_move_time']*1000:.1f}ms/lượt")
        print(f"- Sử dụng nhiều bộ nhớ hơn: {stats['avg_memory']:.1f}MB")
        
        # 6. Kết luận
        print("\n🎯 KẾT LUẬN:")
        if stats['win_rate'] > 0.7 and hit_ratio > 0.4 and wasted_ratio < 0.1:
            print("AI Probabilistic thể hiện sự vượt trội rõ rệt về mặt hiệu suất:")
            print("- Tỷ lệ thắng cao và ổn định")
            print("- Hiệu quả bắn cao (tỷ lệ trúng cao, lãng phí thấp)")
            print("- Chiến lược tìm kiếm và săn-diệt hiệu quả")
            print("\nTuy nhiên, sự vượt trội này đi kèm với chi phí tài nguyên cao hơn:")
            print(f"- Thời gian tính toán: {stats['avg_move_time']*1000:.1f}ms/lượt")
            print(f"- Bộ nhớ sử dụng: {stats['avg_memory']:.1f}MB")
        else:
            print("AI Probabilistic có hiệu suất tốt nhưng chưa thực sự vượt trội")


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

    analyzer.analyze_probabilistic_ai()


if __name__ == "__main__":
    main()