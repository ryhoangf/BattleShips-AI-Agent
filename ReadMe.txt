BÀI TẬP LỚN MÔN LẬP TRÌNH TRÍ TUỆ NHÂN TẠO
-----------------------------------------

Tên đề tài: AI chơi game BattleShip — Chiến lược Probabilistic Heatmap

1. MỤC TIÊU
-----------
Xây dựng một AI có khả năng chơi game Battleship thông minh, không bắn ngẫu nhiên mà sử dụng chiến lược suy luận dựa trên dữ liệu bàn cờ hiện có. Mục tiêu là:
- Tối ưu số lượt bắn để tiêu diệt toàn bộ tàu
- So sánh hiệu quả giữa các chiến lược AI
- Thể hiện các kỹ thuật AI cổ điển: suy diễn, heuristic, đại diện tri thức

2. CÁC CHIẾN LƯỢC ĐÃ TRIỂN KHAI
-------------------------------
- Random AI        : Bắn ngẫu nhiên vào các ô chưa bị bắn
- Basic AI         : Nếu có ô "H", bắn vào các ô xung quanh
- Probabilistic AI : Sử dụng heat-map, phân tích tàu chưa chìm, boost xác suất theo dữ kiện

3. THUẬT TOÁN PROBABILISTIC AI
------------------------------
✔ Xây dựng heat-map: 
   - Với mỗi tàu chưa chìm, duyệt mọi vị trí hợp lệ có thể đặt tàu
   - Tăng heat cho mỗi ô mà tàu có thể nằm lên, cộng thêm nếu trùng với "H"

✔ Boost xung quanh "H":
   - Gom các "H" thành chuỗi ngang/dọc để xác định hướng tàu
   - Boost 2 đầu mút để mở rộng theo chiều dài tàu
   - Nếu là "H" đơn, boost 4 ô kề

✔ Ưu tiên checkerboard (parity):
   - Do tàu dài ≥ 2 nên việc ưu tiên ô checkerboard giúp giảm số lượt dò bắn

✔ Ra quyết định:
   - Chọn ô "U" có heat cao nhất
   - Nếu có nhiều ô đồng heat, chọn ô parity 0 trước
   - Nếu vẫn hòa → chọn ngẫu nhiên trong danh sách tốt nhất

4. KIỂM THỬ & ĐÁNH GIÁ
-----------------------
Chạy thử nghiệm hàng trăm trận, đo các chỉ số:
- Mean / Median / Min / Max số lượt bắn
- Probabilistic AI cho kết quả ổn định, thường vượt Basic và Hunter
- Một số phiên bản tinh chỉnh quá chặt logic (lọc H đã xử lý) dẫn đến giảm hiệu năng → đã được điều chỉnh lại

5. NHẬN XÉT
-----------
- Dự án thể hiện rõ tư duy heuristic trong AI cổ điển
- Biết phân tích không gian trạng thái, áp dụng tri thức domain (tàu dài ≥2, không chồng, không gấp khúc)
- Kết hợp suy luận + thực nghiệm → đúng hướng lập trình AI

6. MỞ RỘNG
----------
- Có thể nâng cấp thành giao diện chơi người-máy
- Có thể thêm chiến lược học tăng cường (reinforcement learning)
- Có thể cho AI học mô hình heat-map từ dữ liệu


