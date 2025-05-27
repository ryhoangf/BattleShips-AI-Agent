import random

class Ship:
    def __init__(self, size):
        self.size = size
        self.row = random.randrange(0,9)
        self.col = random.randrange(0,9)
        self.orientation = random.choice(["h", "v"])
        self.indexes = self.compute_indexes()
    
    def compute_indexes(self):
        start_index = self.row * 10 + self.col
        if self.orientation == "h":
            return [start_index + i for i in range(self.size)]
        elif self.orientation == "v":
            return [start_index + i*10 for i in range(self.size)]

class Player:
    def __init__(self):
        self.ships = []
        self.search = ["U" for i in range (100)]
        self.place_ships(sizes =  [5, 4, 3, 3, 2])
        list_of_lists = [ship.indexes for ship in self.ships]
        self.indexes = [index for sublist in list_of_lists for index in sublist]
    
    def place_ships(self, sizes):
        for size in sizes:
            placed = False
            while not placed:
                #create new ship
                ship = Ship(size)
                #check possible
                possible = True
                for i in ship.indexes:
                    #indexes must be < 100
                    if i >= 100:
                        possible = False
                        break
                    #ships cant behave like snake in snake game
                    new_row = i//10
                    new_col = i%10
                    if new_row != ship.row and new_col != ship.col:
                        possible = False
                        break
                    for other_ship in self.ships:
                        if i in other_ship.indexes:
                            possible = False
                            break
                #place the ship
                if possible:
                    self.ships.append(ship)
                    placed = True

   

#p = Player()
#p.show_ships()

class Game:
    def __init__(self, human1, human2):
        self.human1 = human1
        self.human2 = human2
        self.player1 = Player()
        self.player2 = Player()
        self.player1_turn = True
        self.computer_turn = True if not self.human1 else False
        self.over = False
        self.result = None
        self.shots_p1 = 0
        self.shots_p2 = 0
        self.n_shots = 0
    
    def make_move(self, i):
        player = self.player1 if self.player1_turn else self.player2
        opponent = self.player2 if self.player1_turn else self.player1
        hit = False
        
        #set miss (M) or hit (H)
        if i in opponent.indexes:
            player.search[i] ="H"
            hit = True
            #check ship is sunk (S)
            for ship in opponent.ships:
                sunk = True
                for i in ship.indexes:
                    if player.search[i] == "U":
                        sunk = False
                        break
                if sunk:
                    for i in ship.indexes:
                        player.search[i] = "S"
        else:
            player.search[i] = "M"
        
        #check game over     
        gameover = True
        for i in opponent.indexes:
            if player.search[i] == "U":
                gameover = False
        self.over = gameover
        self.result = 1 if self.player1_turn else 2
        
        #switch turn
        if not hit:
            self.player1_turn = not self.player1_turn
            
            #switch between human and computer
            if (self.human1 and not self.human2) or (not self.human1 and self.human2):
                self.computer_turn = not self.computer_turn
        #add to the number odd shots fired
        if self.player1_turn:
            self.shots_p1 += 1
        else:
            self.shots_p2 += 1
        self.n_shots += 1     

    def random_ai(self):
        search = self.player1.search if self.player1_turn else self.player2.search
        unknown = [i for i, square in enumerate(search) if square == "U"]
        if len(unknown) >0:
            random_index = random.choice(unknown)
            self.make_move(random_index)
            
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
            lines, seen = [], set()  # Chuỗi H liên tiếp và các ô đã xử lý
            for h in hits:
                if h in seen:
                    continue

            # Thử gom theo chiều ngang
                hor = [h]; cur = h + 1
                while cur % 10 != 0 and search[cur] in ("H", "S"):
                    hor.append(cur); seen.add(cur); cur += 1
                cur = h - 1
                while cur % 10 != 9 and cur >= 0 and search[cur] in ("H", "S"):
                    hor.insert(0, cur); seen.add(cur); cur -= 1

                if len(hor) > 1:
                    lines.append(hor)
                    seen.update(hor)
                    continue  #  Đã xác định là ngang, khỏi xét dọc

            # Nếu không phải ngang thì thử gom theo chiều dọc
                ver = [h]; cur = h + 10
                while cur < 100 and search[cur] in ("H", "S"):
                    ver.append(cur); seen.add(cur); cur += 10
                cur = h - 10
                while cur >= 0 and search[cur] in ("H", "S"):
                    ver.insert(0, cur); seen.add(cur); cur -= 10

                if len(ver) > 1:
                    lines.append(ver)
                    seen.update(ver)

            # Boost 2 đầu mút của các chuỗi H liên tiếp
            for line in lines:
                a, b = line[0], line[-1]    # lấy phần sử đầu, phần tử cuối của line
                if b - a < 10:  # ngang
                    for n in (b + 1, a - 1): #lặp qua 2 phần tử 
                        if 0 <= n < 100 and search[n] == "U":
                            heat[n] *= line_boost
                else:  # dọc
                    for n in (b + 10, a - 10):
                        if 0 <= n < 100 and search[n] == "U":
                            heat[n] *= line_boost

            # Boost các ô kề H đơn (không nằm trong line nào)
            for h in hits:
                for n in (h + 1, h - 1, h + 10, h - 10):
                    if 0 <= n < 100 and search[n] == "U":
                        heat[n] *= target_boost

            # Boost ô kề H đơn
            for h in hits:
                for n in (h+1,h-1,h+10,h-10):
                    if 0<=n<100 and search[n]=="U": heat[n]*=target_boost

        # 4) chọn ô U heat cao nhất (ưu tiên parity 0 khi hoà)
        maxh = max(heat[i] for i in unknown)    # tìm giá trị heat cao nhất trong các ô U
        best = [i for i in unknown if heat[i]==maxh] # tìm các ô U có heat bằng maxh ( có thể có nhiều ô cùng heat cao nhất)
        parity_best = [b for b in best if (b//10 + b%10)%2==0]  # kỹ thuật checker‑board: ưu tiên ô U có parity 0 (ô màu sáng) nếu có ( vì tàu dài >= 2 ô nên sẽ có ít nhất 1 ô parity 0 trong mỗi tàu)
        # 5) chọn ngẫu nhiên trong parity_best, nếu không có thì chọn trong best
        move = random.choice(parity_best) if parity_best else random.choice(best)
        self.make_move(move)
    
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
-> Nó không học, không dự đoán thống kê, mà là một cách tính toán xác suất “giả định thông minh” từ toàn bộ trạng thái bàn cờ.

"""