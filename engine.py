import random
import numpy as np

class Ship:
    def __init__(self, size):
        self.size = size
        self.orientation = random.choice(["h", "v"]) 

        if self.orientation == "h":
            self.row = random.randrange(0, 10) 
            self.col = random.randrange(0, 10 - size + 1) 
        else: # orientation == "v"
            self.row = random.randrange(0, 10 - size + 1) 
            self.col = random.randrange(0, 10) 
        
        self.indexes = self.compute_indexes()

    def compute_indexes(self):
        start_index = self.row * 10 + self.col
        if self.orientation == "h":
            return [start_index + i for i in range(self.size)]
        elif self.orientation == "v":
            return [start_index + i * 10 for i in range(self.size)]

class Player:
    def __init__(self):
        self.ships = []
        self.search = ["U" for _ in range(100)]
        self.place_ships(sizes=[5, 4, 3, 3, 2])
        list_of_lists = [ship.indexes for ship in self.ships]
        self.indexes = [index for sublist in list_of_lists for index in sublist]

    def place_ships(self, sizes):
        for size in sizes:
            placed = False
            attempts = 0
            while not placed and attempts < 200: 
                attempts += 1
                temp_ship_for_placement = Ship(size) 
                current_ship_indexes = temp_ship_for_placement.indexes

                possible = True
                if not current_ship_indexes: possible = False
                
                if possible:
                    for index in current_ship_indexes:
                        if not (0 <= index < 100): possible = False; break
                        for existing_ship in self.ships:
                            if index in existing_ship.indexes: possible = False; break
                        if not possible: break
                
                if possible:
                    self.ships.append(temp_ship_for_placement)
                    placed = True

   

#p = Player()
#p.show_ships()

class Game:
    def __init__(self, human1, human2):
        self.human1 = human1; self.human2 = human2
        self.player1 = Player(); self.player2 = Player()
        self.player1_turn = True
        self.computer_turn = not self.human1 
        self.over = False; self.result = None 
        self.shots_p1 = 0; self.shots_p2 = 0; self.n_shots = 0 
        self.analysis_results = {}

    def make_move(self, i):
        current_player = self.player1 if self.player1_turn else self.player2
        opponent = self.player2 if self.player1_turn else self.player1
        shot_is_hit = False 

        if not (0 <= i < 100): 
            if not self.over: self.player1_turn = not self.player1_turn 
            return

        if current_player.search[i] == "M" or current_player.search[i] == "S":
            if not self.over: self.player1_turn = not self.player1_turn
            return 
        
        original_search_state = current_player.search[i]
        shot_counted_this_move = False

        if i in opponent.indexes:
            current_player.search[i] = "H"; shot_is_hit = True
            if original_search_state == "U" and not shot_counted_this_move:
                if current_player == self.player1: self.shots_p1 +=1
                else: self.shots_p2 +=1
                self.n_shots +=1; shot_counted_this_move = True
            for ship in opponent.ships:
                if i in ship.indexes: 
                    is_sunk = True
                    for ship_idx in ship.indexes:
                        if current_player.search[ship_idx] not in ("H", "S"): is_sunk = False; break
                    if is_sunk:
                        for ship_idx in ship.indexes: current_player.search[ship_idx] = "S"
                    break 
        else: 
            if current_player.search[i] == "U":
                current_player.search[i] = "M"
                if not shot_counted_this_move:
                    if current_player == self.player1: self.shots_p1 +=1
                    else: self.shots_p2 +=1
                    self.n_shots +=1; shot_counted_this_move = True
        
        all_opponent_ships_hit = True
        for opponent_ship_idx in opponent.indexes:
            if current_player.search[opponent_ship_idx] not in ("H", "S"): all_opponent_ships_hit = False; break
        if all_opponent_ships_hit:
            self.over = True; self.result = 1 if self.player1_turn else 2
        
        if not shot_is_hit and not self.over : self.player1_turn = not self.player1_turn
        
        if not self.over:
            self.computer_turn = (not self.human1 and self.player1_turn) or \
                                 (not self.human2 and not self.player1_turn)

    def random_ai(self):
        search_grid = self.player1.search if self.player1_turn else self.player2.search
        unknown_squares = [i for i, square_status in enumerate(search_grid) if square_status == "U"]
        if unknown_squares: self.make_move(random.choice(unknown_squares))

    def basic_ai(self):
        search = self.player1.search if self.player1_turn else self.player2.search
        unknown = [i for i, square in enumerate(search) if square == "U"]
        hits = [i for i, square in enumerate(search) if square == "H"]
        #search neighbor of hits
        unknown_with_neighbor_hit1 = []
        unknown_with_neighbor_hit2 = []
        for u in unknown:
            if u + 1 in hits or u - 1 in hits or u - 10 in hits or u + 10 in hits:
                unknown_with_neighbor_hit1.append(u)
            if u+2 in hits or u-2 in hits or u - 20 in hits or u + 20 in hits:
                unknown_with_neighbor_hit2.append(u)
                
        #pick "U" square with direct and level 2 neighbor both marked as "H"
        for u in unknown:
            if u in unknown_with_neighbor_hit1 and u in unknown_with_neighbor_hit2:
                self.make_move(u)
                return
        
        #pick "U" square that has a neighbor marked as "H"
        if len(unknown_with_neighbor_hit1) > 0:
            self.make_move(random.choice(unknown_with_neighbor_hit1))
            return
        
        #checker board pattern
        checker_board = []
        for u in unknown:
            row = u // 10
            col = u % 10
            if (row+col)%2 == 0:
                checker_board.append(u)
        if len(checker_board) > 0:
            self.make_move(random.choice(checker_board))
            return
        #random move
        self.random_ai()

    def compute_heat_map(self):
        """Trả về list heat[0..99] cho player hiện tại."""
        search = (self.player1 if self.player1_turn else self.player2).search
        hits    = [i for i, sq in enumerate(search) if sq == "H"]
        # 1) tính remaining ships
        sunk = []; visited = set()
        for i, sq in enumerate(search):
            if sq == "S" and i not in visited:
                group, stack = {i}, [i]
                while stack:
                    cur = stack.pop()
                    for n in (cur+1,cur-1,cur+10,cur-10):
                        if 0 <= n < 100 and search[n]=="S" and n not in group:
                            group.add(n); stack.append(n)
                visited |= group; sunk.append(len(group))
        remaining = [5,4,3,3,2]
        for s in sunk:
            if s in remaining: remaining.remove(s)

        # 2) build heat
        heat = [0]*100
        def fit(start,size,ori):
            row,col = divmod(start,10)
            idxs = [start + (o if ori=="h" else o*10) for o in range(size)]
            if ori=="h" and col+size>10: return False,[]
            if ori=="v" and row+size>10: return False,[]
            if any(search[i] in ("M","S") for i in idxs): return False,[]
            return True, idxs

        for sz in remaining:
            for st in range(100):
                for ori in ("h","v"):
                    ok, idxs = fit(st, sz, ori)
                    if not ok: continue
                    bonus = 1 + sum(1 for h in hits if h in idxs)
                    for i in idxs:
                        if search[i]=="U": heat[i] += bonus

        # --- 3) Boost quanh các ô 'H' ---
        target_boost = 10    # hệ số boost cho các ô kề một hit đơn lẻ
        line_boost   = 20    # hệ số boost cho hai đầu mút của chuỗi H liên tiếp

        # 3.1 Gom các chuỗi H liên tiếp (cả ngang lẫn dọc)
        lines = []   # sẽ chứa list các chỉ số theo chuỗi H
        seen  = set()  # để không xét lại cùng một hit

        for h in hits:
            if h in seen:
                continue

            # --- Gom ngang ---
            hor = [h]
            cur = h + 1
            # mở rộng về bên phải
            while cur % 10 != 0 and search[cur] in ("H", "S"):
                hor.append(cur)
                seen.add(cur)
                cur += 1
            # mở rộng về bên trái
            cur = h - 1
            while cur % 10 != 9 and cur >= 0 and search[cur] in ("H", "S"):
                hor.insert(0, cur)
                seen.add(cur)
                cur -= 1

            if len(hor) > 1:
                lines.append(hor)
                seen.update(hor)
                continue  # nếu đã là chuỗi ngang thì bỏ qua xét dọc

            # --- Gom dọc ---
            ver = [h]
            cur = h + 10
            # mở rộng xuống dưới
            while cur < 100 and search[cur] in ("H", "S"):
                ver.append(cur)
                seen.add(cur)
                cur += 10
            # mở rộng lên trên
            cur = h - 10
            while cur >= 0 and search[cur] in ("H", "S"):
                ver.insert(0, cur)
                seen.add(cur)
                cur -= 10

            if len(ver) > 1:
                lines.append(ver)
                seen.update(ver)

        # 3.2 Boost 2 đầu mút của từng chuỗi H
        for line in lines:
            a, b = line[0], line[-1]  # index đầu và cuối của chuỗi
            if b - a < 10:
            # chuỗi ngang ⇒ tăng heat cho ô bên trái và phải
                for n in (b + 1, a - 1):
                    if 0 <= n < 100 and search[n] == "U":
                        heat[n] *= line_boost
            else:
            # chuỗi dọc ⇒ tăng heat cho ô trên và dưới
                for n in (b + 10, a - 10):
                    if 0 <= n < 100 and search[n] == "U":
                        heat[n] *= line_boost

        # 3.3 Boost xung quanh từng hit đơn lẻ (nếu không thuộc chuỗi nào)
        for h in hits:
            for n in (h + 1, h - 1, h + 10, h - 10):
                if 0 <= n < 100 and search[n] == "U":
                    heat[n] *= target_boost
        return heat



    # ---------------------------------------------------------------------
    # Probabilistic AI — Heat‑map full xác suất + boost quanh H
    # ---------------------------------------------------------------------
    def probabilistic_ai(self):
        player = self.player1 if self.player1_turn else self.player2
        search = player.search # Danh sách 100 ô ["U", "M", "H", "S"]
        unknown = [i for i, sq in enumerate(search) if sq == "U"] #Tập các ô có thể bắn tiếp.
        hits    = [i for i, sq in enumerate(search) if sq == "H"] #Tập các ô đã bắn trúng tàu nhưng chưa chìm.
        if not unknown:
            return
        # 1) tìm kích thước tàu chưa chìm bằng cách gom nhóm S
        sunk = [] #lưu lại kích thước các tàu đã chìm
        visited = set() # lưu lại tất cả các ô 'S' đã được duyệt
        for i, sq in enumerate(search):
            if sq == "S" and i not in visited:
                group = {i}; stack = [i] # dùng  set{} để tăng tốc độ tìm kiếm O(1), sử dụng stack để duyệt DFS
                while stack:
                    cur = stack.pop()
                    for n in (cur+1,cur-1,cur+10,cur-10):   # 4 hướng lân cận
                        if 0 <= n < 100 and search[n] == "S" and n not in group:
                            group.add(n); stack.append(n)
                visited |= group; sunk.append(len(group))   # sau khi gom xong cụm thêm toàn bộ ô trong group vào visited, tránh xử lý lại
        remaining = [5,4,3,3,2]
        for s in sunk:
            if s in remaining: remaining.remove(s)
        # 2) Heat‑map: quét mọi vị trí có thể của mỗi tàu còn lại
        """Mục tiêu của bước này là xây dựng một bản đồ "heat" gồm 100 ô (tương ứng với 10x10 bàn cờ), phản ánh xác suất có tàu tại mỗi ô "U" (chưa biết). 
        Xác suất này được tính dựa trên các vị trí hợp lệ mà các tàu chưa chìm còn có thể nằm."""

        # Mỗi phần tử trong heat[i] sẽ biểu thị mức độ nghi ngờ (độ nóng) rằng có tàu tại ô thứ i.
        heat = [0]*100 
        
        """Duyệt qua từng tàu trong remaining, thử đặt tại mọi ô (0 → 99) theo cả hướng ngang ("h") và dọc ("v").
           Hàm fit(start, size, ori) đảm nhiệm việc kiểm tra tính hợp lệ:"""
        
        def fit(start,size,ori): #kiểm tra xem tàu có vừa ở vị trí start theo hướng "h" hoặc "v" không.
            row,col = start//10, start%10
            idxs=[start+o if ori=="h" else start+o*10 for o in range(size)] #Tạo mảng `idxs` chứa **chỉ số tất cả các ô con tàu đi qua**.

            # Kiểm tra tràn biên
            if ori=="h" and col+size>10: return False,[]
            if ori=="v" and row+size>10: return False,[]

            # Nếu có ô nào đã là `"M"` (bắn hụt) hoặc `"S"` (tàu chìm) → **không thể đặt tàu ở đây**.
            if any(search[i] in ("M","S") for i in idxs): return False,[]
            return True,idxs
        
        for sz in remaining:
            for st in range(100):   #duyệt mọi ô từ 0 đến 99 để đặt thử tàu
                for ori in ("h","v"): # thử cả 2 hướng ngang và dọc
                    ok,idxs=fit(st,sz,ori)
                    if ok:  # nếu tàu có thể đặt ở vị trí này thì mới cộng heat
                        bonus=1+sum(1 for h in hits if h in idxs) # nếu đặt vị trí này không trùng hit nào thì bonus=1, nếu trùng 1 hit thì bonus=2, trùng 2 hit thì bonus=3...
                        for idx in idxs:
                            if search[idx]=="U": heat[idx]+=bonus


       # 3) Boost quanh H
        target_boost, line_boost = 10, 20
        if hits:
            lines, seen_in_lines = [], set()
            sorted_hits = sorted(list(hits))

            for h_idx in sorted_hits:
                if h_idx in seen_in_lines: continue
                current_line_hor = {h_idx}; cur = h_idx + 1
                while (h_idx // 10 == cur // 10) and cur < 100 and search[cur] in ("H", "S"): current_line_hor.add(cur); cur += 1
                cur = h_idx - 1
                while (h_idx // 10 == cur // 10) and cur >= 0 and search[cur] in ("H", "S"): current_line_hor.add(cur); cur -= 1
                current_line_ver = {h_idx}; cur = h_idx + 10
                while cur < 100 and search[cur] in ("H", "S"): current_line_ver.add(cur); cur += 10
                cur = h_idx - 10
                while cur >= 0 and search[cur] in ("H", "S"): current_line_ver.add(cur); cur -= 10
                chosen_line_indices = []
                if len(current_line_hor) > 1 and len(current_line_ver) > 1:
                    chosen_line_indices = sorted(list(current_line_hor)) if len(current_line_hor) >= len(current_line_ver) else sorted(list(current_line_ver))
                elif len(current_line_hor) > 1: chosen_line_indices = sorted(list(current_line_hor))
                elif len(current_line_ver) > 1: chosen_line_indices = sorted(list(current_line_ver))
                if chosen_line_indices and not any(idx in seen_in_lines for idx in chosen_line_indices):
                    lines.append(chosen_line_indices); seen_in_lines.update(chosen_line_indices)

            for line_indices in lines:
                if not line_indices: continue
                first_h, last_h = line_indices[0], line_indices[-1]
                is_horizontal = all(idx // 10 == first_h // 10 for idx in line_indices)
                if is_horizontal:
                    target_left = first_h - 1
                    if (first_h // 10 == target_left // 10) and target_left >= 0 and search[target_left] == "U":
                        heat[target_left] += LINE_BOOST_ENDS; priority_targets.append(target_left)
                    target_right = last_h + 1
                    if (last_h // 10 == target_right // 10) and target_right < 100 and search[target_right] == "U":
                        heat[target_right] += LINE_BOOST_ENDS; priority_targets.append(target_right)
                else: 
                    target_up = first_h - 10
                    if target_up >= 0 and search[target_up] == "U":
                        heat[target_up] += LINE_BOOST_ENDS; priority_targets.append(target_up)
                    target_down = last_h + 10
                    if target_down < 100 and search[target_down] == "U":
                        heat[target_down] += LINE_BOOST_ENDS; priority_targets.append(target_down)

            single_hits_to_boost = set(hits) - seen_in_lines
            for h_idx in single_hits_to_boost:
                 for offset in [-1, 1, -10, 10]:
                    n_idx = h_idx + offset
                    if 0 <= n_idx < 100 and search[n_idx] == "U":
                        is_valid_adj = False
                        if (offset == -1 or offset == 1) and (n_idx // 10 == h_idx // 10): is_valid_adj = True
                        elif (offset == -10 or offset == 10): is_valid_adj = True
                        if is_valid_adj: heat[n_idx] += TARGET_BOOST_SINGLE_H
        
        if priority_targets:
            best_priority_target = -1; max_priority_heat = -1
            unique_priority_targets = sorted(list(set(priority_targets)))
            for pt_idx in unique_priority_targets:
                if heat[pt_idx] > max_priority_heat: max_priority_heat = heat[pt_idx]; best_priority_target = pt_idx
            if best_priority_target != -1:
                top_priority_targets = [pt for pt in unique_priority_targets if heat[pt] == max_priority_heat]
                if top_priority_targets:
                    parity_priority = [p for p in top_priority_targets if (p//10 + p%10)%2 ==0]
                    move = random.choice(parity_priority) if parity_priority else random.choice(top_priority_targets)
                    self.make_move(move); return

        if not unknown: self.random_ai(); return
        maxh_val = -1
        for i_idx in unknown:
            if heat[i_idx] > maxh_val: maxh_val = heat[i_idx]
        if maxh_val < 0 and unknown : self.random_ai(); return # Use < 0 to catch all non-positive useful heat
        best_moves = [i_idx for i_idx in unknown if heat[i_idx] == maxh_val]
        if not best_moves: # If no best_moves (e.g. all unknown have heat <=0)
            if unknown: self.random_ai(); return
            else: return # No unknown and no best_moves
            
        parity_best = [b_idx for b_idx in best_moves if (b_idx // 10 + b_idx % 10) % 2 == 0]
        move = random.choice(parity_best) if parity_best else random.choice(best_moves)
        self.make_move(move)
    

    def monte_carlo_ai(self, n_sim=500):
        search = self.player1.search if self.player1_turn else self.player2.search
        hits = [i for i, sq in enumerate(search) if sq == "H"]
        misses = [i for i, sq in enumerate(search) if sq == "M"]
        unknown = [i for i, sq in enumerate(search) if sq == "U"]
        # Xác định các tàu còn lại
        sunk = []
        visited = set()
        for i, sq in enumerate(search):
            if sq == "S" and i not in visited:
                group, stack = {i}, [i]
                while stack:
                    cur = stack.pop()
                    for n in (cur+1,cur-1,cur+10,cur-10):
                        if 0 <= n < 100 and search[n]=="S" and n not in group:
                            group.add(n); stack.append(n)
                visited |= group; sunk.append(len(group))
        remaining = [5,4,3,3,2]
        for s in sunk:
            if s in remaining: remaining.remove(s)

        # Monte Carlo: sinh n_sim bàn cờ hợp lệ
        counts = np.zeros(100)
        for _ in range(n_sim):
            board = np.zeros(100, dtype=bool)
            ships = []
            for sz in remaining:
                placed = False
                for _ in range(100):  # thử tối đa 100 lần cho mỗi tàu
                    ori = np.random.choice(["h", "v"])
                    if ori == "h":
                        row = np.random.randint(0, 10)
                        col = np.random.randint(0, 11 - sz)
                        idxs = [row*10 + col + i for i in range(sz)]
                    else:
                        row = np.random.randint(0, 11 - sz)
                        col = np.random.randint(0, 10)
                        idxs = [row*10 + col + i*10 for i in range(sz)]
                    # Kiểm tra hợp lệ
                    if any(board[i] for i in idxs): continue
                    if any(i in misses for i in idxs): continue
                    if hits and not all(h in idxs for h in hits if h not in [i for s in ships for i in s]): continue
                    placed = True
                    for i in idxs: board[i] = True
                    ships.append(idxs)
                    break
                if not placed:
                    break  # không đặt được tàu này, bỏ qua bàn cờ này
            else:
                # Nếu đặt đủ tất cả tàu
                for i in unknown:
                    if board[i]: counts[i] += 1

        # Chọn ô có xác suất cao nhất
        if np.sum(counts) == 0:
            move = np.random.choice(unknown)
        else:
            best = np.argwhere(counts == np.amax(counts)).flatten()
            move = np.random.choice(best)
        self.make_move(move)

    def bayesian_ai(self):
        search = self.player1.search if self.player1_turn else self.player2.search
        unknown = [i for i, sq in enumerate(search) if sq == "U"]
        hits = [i for i, sq in enumerate(search) if sq == "H"]
        misses = [i for i, sq in enumerate(search) if sq == "M"]
        # Khởi tạo xác suất đều
        prob = {i: 1.0 for i in unknown}
        # Nếu có hit, tăng xác suất các ô lân cận
        for h in hits:
            for n in (h+1, h-1, h+10, h-10):
                if 0 <= n < 100 and n in prob:
                    prob[n] *= 3  # tăng mạnh xác suất quanh hit
        # Nếu có miss, giảm xác suất các ô lân cận
        for m in misses:
            for n in (m+1, m-1, m+10, m-10):
                if 0 <= n < 100 and n in prob:
                    prob[n] *= 0.5  # giảm xác suất quanh miss
        # Bình thường hóa
        total = sum(prob.values())
        if total > 0:
            for k in prob:
                prob[k] /= total
        # Chọn ô có xác suất cao nhất
        best = [k for k, v in prob.items() if v == max(prob.values())]
        move = np.random.choice(best)
        self.make_move(move)

AI_MAP = {
    "random": lambda game: game.random_ai(),
    "basic": lambda game: game.basic_ai(),
    "proba": lambda game: game.probabilistic_ai(),
    "montecarlo": lambda game: game.monte_carlo_ai(),
    "bayes": lambda game: game.bayesian_ai()
}

""" 
   Ý tưởng:
    Tính xác suất xuất hiện của tàu ở từng ô "U" => chọn ra ô có xác suất cao nhất để bắn.
    Bản chất thuật toán: Bayesian-like heuristic (xấp xỉ xác suất theo mô hình cấu trúc)
    Quy trình:
     1. Xác định các tàu chưa chìm:
        Duyệt qua các ô "S" -> gom nhóm để biết kích thước các tàu đã chìm => danh sách tàu còn lại
     2. Xây dựng Heat-map:
        Tạo heat[100] = 0
        Với mỗi tàu trong danh sách còn lại:
            Duyệt mọi ví trí có thể đặt tàu (0-99) theo cả 2 hướng "h" và "v"
            Nếu vị trí đặt hợp lệ (không trùng "M" hay "S"):
                Cộng điểm vào heat[i] cho mỗi i nằm trong vùng tàu
                Nếu i trùng "H" thì cộng thêm điểm (bonus) để ưu tiên bắn vào ô đó
                => tạo bản đồ nhiệt, phản ánh xác suất có tàu tại mỗi ô "U"
     3. Boost quanh ô "H":
        Gom các "H" liên tiếp thành chuỗi (horizontal/vertical) => xác định hướng tàu, tạo danh sách lines[] lưu các chuỗi "H" liền mạch
        Boost 2 đầu mút với mỗi chuỗi "H" vì tàu chưa chìm có thể kéo thêm về 2 đầu
        Boost "H" đơn: "H" đơn có thể là đầu mút của tàu chưa phát hiện, boost 4 hướng xung quanh
     4. Ra quyết định chọn hướng đi
        Từ heat[], tìm ô "U" có xác suất cao nhất
        Nếu có nhiều ô cùng xác suất cao, ưu tiên ô có parity 0 (ô màu sáng trong checkerboard)
        Chọn ngẫu nhiên trong các ô đó để bắn

Probabilistic AI là một chiến lược heuristic-based, kết hợp luật game (tàu dài ≥2, không chồng lên nhau) với heat-map xác suất và tăng cường dữ kiện "H" để đưa ra nước đi tối ưu.
-> Nó không học, không dự đoán thống kê, mà là một cách tính toán xác suất "giả định thông minh" từ toàn bộ trạng thái bàn cờ.
"""