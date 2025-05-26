# engine.py
import random

class Ship:
    def __init__(self, size):
        self.size = size
        # *** FIX: Assign orientation BEFORE using it ***
        self.orientation = random.choice(["h", "v"]) # Assign orientation first

        # Now determine row and col based on the assigned orientation and size
        if self.orientation == "h":
            self.row = random.randrange(0, 10) # 0 to 9
            self.col = random.randrange(0, 10 - size + 1) # Ensure horizontal ship fits
        else: # orientation == "v"
            self.row = random.randrange(0, 10 - size + 1) # Ensure vertical ship fits
            self.col = random.randrange(0, 10) # 0 to 9
        
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
                
                # Create a fully initialized temporary Ship object to test placement
                # This Ship object will have its orientation set correctly in its own __init__
                # The size passed here is the current 'size' we are trying to place
                temp_ship_for_placement = Ship(size) 
                current_ship_indexes = temp_ship_for_placement.indexes # Get indexes from the temp ship

                possible = True
                if not current_ship_indexes: # Should not happen if Ship.__init__ is correct
                    possible = False
                
                # Check if all indexes are valid and don't overlap
                if possible:
                    for index in current_ship_indexes:
                        if not (0 <= index < 100): # Boundary check
                            possible = False
                            break
                        for existing_ship in self.ships:
                            if index in existing_ship.indexes:
                                possible = False
                                break
                        if not possible:
                            break
                
                if possible:
                    # If placement is valid, add the temp_ship_for_placement itself
                    self.ships.append(temp_ship_for_placement)
                    placed = True
            if not placed:
                print(f"Warning: Could not place ship of size {size} after {attempts} attempts.")


    def show_ships(self): # For debugging
        indexes_display  = ["-" for _ in range (100)]
        for i_idx in self.indexes: # Renamed i to i_idx
            if 0 <= i_idx < 100:
                 indexes_display[i_idx] = "X"
        for r_idx in range(10): # Renamed r to r_idx
            print(" ".join(indexes_display[r_idx*10 : (r_idx+1)*10]))

    def get_remaining_ship_sizes(self, search_grid_of_opponent):
        current_remaining_sizes = []
        # Get initial sizes from the ships actually placed for this player
        for ship_obj in self.ships:
            current_remaining_sizes.append(ship_obj.size)

        sunk_ships_accounted_for_indices = set() # Store indices of ships already counted as sunk

        for i, ship in enumerate(self.ships):
            if i in sunk_ships_accounted_for_indices:
                continue 
            
            is_fully_sunk = True
            if not ship.indexes: # Should not happen with proper ship creation
                continue
            for ship_idx in ship.indexes:
                if not (0 <= ship_idx < 100 and search_grid_of_opponent[ship_idx] == "S"):
                    is_fully_sunk = False
                    break
            
            if is_fully_sunk:
                if ship.size in current_remaining_sizes:
                    current_remaining_sizes.remove(ship.size)
                    sunk_ships_accounted_for_indices.add(i)
        return current_remaining_sizes


# ... (Rest of engine.py remains the same as the previous "complete" version)
# Game class and its methods like __init__, make_move, AI methods, _calculate_heat_map, analyze_opponent_board
# are assumed to be correct from the previous complete file provided.
# The key fix was in Ship.__init__ and a refinement in Player.place_ships.

class Game:
    def __init__(self, human1, human2):
        self.human1 = human1
        self.human2 = human2
        self.player1 = Player()
        self.player2 = Player()
        self.player1_turn = True
        self.computer_turn = not self.human1 
        self.over = False
        self.result = None 
        self.shots_p1 = 0
        self.shots_p2 = 0
        self.n_shots = 0 
        self.analysis_results = {}

    def make_move(self, i):
        current_player = self.player1 if self.player1_turn else self.player2
        opponent = self.player2 if self.player1_turn else self.player1
        shot_is_hit = False 

        if not (0 <= i < 100): 
            # print(f"Error: Move index {i} is out of bounds.")
            if not self.over: # Only switch turn if game not over due to this error
                self.player1_turn = not self.player1_turn 
            return

        # Allow shooting at already shot squares, but don't re-count shots or change state if already M/S
        # However, re-shooting an 'H' could lead to 'S' if it completes a ship.
        if current_player.search[i] == "M" or current_player.search[i] == "S":
            if not self.over: # If game not over, non-hitting re-shot square means turn change
                 self.player1_turn = not self.player1_turn
            return # No further action on already fully resolved squares (M or S)
        
        original_search_state = current_player.search[i] # Store U or H

        shot_counted_this_move = False # Flag to ensure shot is counted only once per make_move call

        if i in opponent.indexes:
            current_player.search[i] = "H"
            shot_is_hit = True
            if original_search_state == "U" and not shot_counted_this_move: # Count as a new shot
                if current_player == self.player1: self.shots_p1 +=1
                else: self.shots_p2 +=1
                self.n_shots +=1
                shot_counted_this_move = True

            for ship in opponent.ships:
                if i in ship.indexes: 
                    is_sunk = True
                    for ship_idx in ship.indexes:
                        if current_player.search[ship_idx] != "H" and current_player.search[ship_idx] != "S":
                            is_sunk = False
                            break
                    if is_sunk:
                        for ship_idx in ship.indexes:
                            current_player.search[ship_idx] = "S"
                    break 
        else: # Miss
            if current_player.search[i] == "U": # Only mark as miss and count shot if it was unknown
                current_player.search[i] = "M"
                if not shot_counted_this_move:
                    if current_player == self.player1: self.shots_p1 +=1
                    else: self.shots_p2 +=1
                    self.n_shots +=1
                    shot_counted_this_move = True
        
        all_opponent_ships_hit = True
        for opponent_ship_idx in opponent.indexes:
            if current_player.search[opponent_ship_idx] not in ("H", "S"):
                all_opponent_ships_hit = False
                break
        
        if all_opponent_ships_hit:
            self.over = True
            self.result = 1 if self.player1_turn else 2
        
        if not shot_is_hit and not self.over : 
            self.player1_turn = not self.player1_turn
        
        # Update computer_turn based on the new player1_turn state
        if not self.over:
            self.computer_turn = (not self.human1 and self.player1_turn) or \
                                 (not self.human2 and not self.player1_turn)


    def random_ai(self):
        search_grid = self.player1.search if self.player1_turn else self.player2.search
        unknown_squares = [i for i, square_status in enumerate(search_grid) if square_status == "U"]
        if unknown_squares:
            random_index = random.choice(unknown_squares)
            self.make_move(random_index)

    def basic_ai(self):
        search = self.player1.search if self.player1_turn else self.player2.search
        unknown = [i for i, sq in enumerate(search) if sq == "U"]
        hits = [i for i, sq in enumerate(search) if sq == "H"]
        if not unknown: return 
        adj_to_hits = set()
        for h_idx in hits:
            for offset in [-1, 1, -10, 10]:
                neighbor = h_idx + offset
                if 0 <= neighbor < 100 and search[neighbor] == "U":
                    if (offset == -1 or offset == 1) and (neighbor // 10 == h_idx // 10): 
                        adj_to_hits.add(neighbor)
                    elif (offset == -10 or offset == 10): 
                        adj_to_hits.add(neighbor)
        if adj_to_hits: self.make_move(random.choice(list(adj_to_hits))); return
        checkerboard_unknown = [u for u in unknown if (u // 10 + u % 10) % 2 == 0]
        if checkerboard_unknown: self.make_move(random.choice(checkerboard_unknown)); return
        if unknown: self.make_move(random.choice(unknown))

    def _calculate_heat_map(self, search_grid, hit_squares, remaining_ship_sizes_on_opponent_board):
        heat = [0] * 100
        def fit(start, size, ori, current_search_grid):
            row, col = start // 10, start % 10
            idxs = [start + o if ori == "h" else start + o * 10 for o in range(size)]
            if ori == "h" and col + size > 10: return False, []
            if ori == "v" and row + size > 10: return False, []
            if any(idx not in range(100) or current_search_grid[idx] in ("M", "S") for idx in idxs): return False,[]
            return True, idxs
        for sz in remaining_ship_sizes_on_opponent_board:
            for st_idx in range(100):
                for ori in ("h", "v"):
                    ok, idxs_list = fit(st_idx, sz, ori, search_grid)
                    if ok:
                        bonus = 1 + sum(1 for h_idx in hit_squares if h_idx in idxs_list)
                        for current_idx in idxs_list:
                            if search_grid[current_idx] == "U": heat[current_idx] += bonus
        return heat

    def analyze_opponent_board(self, for_player_num):
        if for_player_num == 1: player = self.player1; opponent = self.player2
        else: player = self.player2; opponent = self.player1
        search_grid = player.search
        remaining_ships_on_opponent = opponent.get_remaining_ship_sizes(search_grid)
        unknown_squares = [i for i, sq in enumerate(search_grid) if sq == "U"]
        hit_squares = [i for i, sq in enumerate(search_grid) if sq == "H"]
        heat_map = self._calculate_heat_map(search_grid, hit_squares, remaining_ships_on_opponent)
        hottest_square_idx = -1; max_heat = -1
        if unknown_squares:
            for i in unknown_squares:
                if heat_map[i] > max_heat: max_heat = heat_map[i]; hottest_square_idx = i
        analysis = {"remaining_ships": remaining_ships_on_opponent, "hottest_square": hottest_square_idx, "max_heat_value": max_heat}
        self.analysis_results[for_player_num] = analysis
        return analysis

    def probabilistic_ai(self):
        player = self.player1 if self.player1_turn else self.player2
        opponent = self.player2 if self.player1_turn else self.player1
        search = player.search; unknown = [i for i, sq in enumerate(search) if sq == "U"]; hits = [i for i, sq in enumerate(search) if sq == "H"]
        if not unknown: return
        remaining = opponent.get_remaining_ship_sizes(search)
        heat = self._calculate_heat_map(search, hits, remaining)
        target_boost, line_boost = 100, 500
        if hits:
            lines, seen_in_lines = [], set()
            for h_idx in hits:
                if h_idx in seen_in_lines: continue
                current_line_hor = [h_idx]; temp_seen_hor = {h_idx}
                cur = h_idx + 1
                while (h_idx // 10 == cur // 10) and cur < 100 and search[cur] in ("H", "S"): current_line_hor.append(cur); temp_seen_hor.add(cur); cur += 1
                cur = h_idx - 1
                while (h_idx // 10 == cur // 10) and cur >= 0 and search[cur] in ("H", "S"): current_line_hor.insert(0, cur); temp_seen_hor.add(cur); cur -= 1
                if len(current_line_hor) > 1: lines.append(sorted(list(temp_seen_hor))); seen_in_lines.update(temp_seen_hor); continue
                current_line_ver = [h_idx]; temp_seen_ver = {h_idx}
                cur = h_idx + 10
                while cur < 100 and search[cur] in ("H", "S"): current_line_ver.append(cur); temp_seen_ver.add(cur); cur += 10
                cur = h_idx - 10
                while cur >= 0 and search[cur] in ("H", "S"): current_line_ver.insert(0, cur); temp_seen_ver.add(cur); cur -= 10
                if len(current_line_ver) > 1: lines.append(sorted(list(temp_seen_ver))); seen_in_lines.update(temp_seen_ver)
            for line_indices in lines:
                if not line_indices: continue
                a, b = line_indices[0], line_indices[-1]
                is_horizontal_line = all(idx // 10 == a // 10 for idx in line_indices) if line_indices else False
                if is_horizontal_line:
                    for n_idx in [a - 1, b + 1]:
                        if 0 <= n_idx < 100 and (n_idx // 10 == a // 10) and search[n_idx] == "U": heat[n_idx] *= line_boost
                else:
                    for n_idx in [a - 10, b + 10]:
                        if 0 <= n_idx < 100 and search[n_idx] == "U": heat[n_idx] *= line_boost
            single_hits_to_boost = set(hits) - seen_in_lines
            for h_idx in single_hits_to_boost:
                 for offset in [-1, 1, -10, 10]:
                    n_idx = h_idx + offset
                    if 0 <= n_idx < 100 and search[n_idx] == "U":
                        is_valid_adj = False
                        if (offset == -1 or offset == 1) and (n_idx // 10 == h_idx // 10): is_valid_adj = True
                        elif (offset == -10 or offset == 10): is_valid_adj = True
                        if is_valid_adj: heat[n_idx] *= target_boost
        if not unknown: self.random_ai(); return
        maxh_val = -1
        for i_idx in unknown:
            if heat[i_idx] > maxh_val: maxh_val = heat[i_idx]
        if maxh_val <= 0 and unknown : self.random_ai(); return
        best_moves = [i_idx for i_idx in unknown if heat[i_idx] == maxh_val]
        parity_best = [b_idx for b_idx in best_moves if (b_idx // 10 + b_idx % 10) % 2 == 0]
        move = random.choice(parity_best) if parity_best else random.choice(best_moves)
        self.make_move(move)