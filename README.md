# 🐍 Snake AI - Trò chơi Rắn săn mồi ứng dụng thuật toán A*

> Dự án xây dựng trò chơi **Rắn săn mồi (Snake Game)** sử dụng **thuật toán A*** để tự động tìm đường đến mục tiêu, tránh va chạm với chướng ngại vật động và lựa chọn mục tiêu thông minh.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Pygame](https://img.shields.io/badge/Pygame-2.x-green?logo=pygame)
![Algorithm](https://img.shields.io/badge/Algorithm-A*-orange)
![Status](https://img.shields.io/badge/Project-Hoàn%20thành-success)

---

# 📖 Giới thiệu

Đây là dự án mô phỏng trò chơi **Rắn săn mồi** được phát triển bằng **Python** và **Pygame**.

Khác với trò chơi truyền thống do người chơi điều khiển, trong dự án này con rắn được điều khiển hoàn toàn bằng **thuật toán A*** (A-Star Search Algorithm). Thuật toán sẽ liên tục tính toán đường đi ngắn nhất và an toàn nhất để đưa rắn đến mục tiêu, đồng thời tránh tường, thân rắn và các chướng ngại vật di động.

Khi môi trường thay đổi (chướng ngại vật di chuyển hoặc xuất hiện mục tiêu mới), thuật toán sẽ tự động tính toán lại đường đi để đảm bảo khả năng di chuyển tối ưu.

---

# ✨ Chức năng nổi bật

* 🤖 Điều khiển rắn hoàn toàn bằng thuật toán A*.
* 🍎 Tự động tìm đường đến thức ăn.
* ⭐ Hệ thống vật phẩm thưởng (Bonus).
* 🎯 Lựa chọn mục tiêu thông minh:

  * Nếu **Bonus** gần hơn thì ưu tiên ăn Bonus.
  * Nếu **Thức ăn** gần hơn thì ưu tiên ăn Thức ăn.
* 🚧 Chướng ngại vật di chuyển liên tục.
* 🔄 Tự động tính toán lại đường đi khi môi trường thay đổi.
* 📈 Hỗ trợ nhiều cấp độ chơi.
* 🎨 Giao diện trực quan, dễ theo dõi.
* ⚡ Mã nguồn được tổ chức theo hướng Clean Code.

---

# 🧠 Thuật toán sử dụng

Dự án sử dụng **thuật toán A*** để tìm đường.

Quy trình hoạt động:

1. Quét toàn bộ bản đồ.
2. Xác định vị trí thức ăn và Bonus.
3. Tính đường đi ngắn nhất đến từng mục tiêu.
4. So sánh khoảng cách.
5. Chọn mục tiêu gần nhất.
6. Điều khiển rắn di chuyển.
7. Khi môi trường thay đổi sẽ tính toán lại đường đi.

Thuật toán sử dụng **Manhattan Distance** làm hàm heuristic để tối ưu việc tìm kiếm trên bản đồ dạng lưới (Grid).

---

# 🎮 Luật chơi

* Rắn tự động di chuyển.
* Mỗi lần ăn thức ăn, chiều dài rắn tăng thêm 1.
* Bonus xuất hiện ngẫu nhiên trên bản đồ.
* AI sẽ tự động chọn mục tiêu gần nhất giữa Bonus và thức ăn.
* Chướng ngại vật thay đổi vị trí theo thời gian.
* Trò chơi kết thúc khi:

  * Rắn đâm vào tường.
  * Rắn đâm vào chính thân mình.

---

# 🕹 Các cấp độ

| Cấp độ     | Mô tả                                                           |
| ---------- | --------------------------------------------------------------- |
| Dễ         | Bản đồ nhỏ, ít chướng ngại vật                                  |
| Trung bình | Bản đồ lớn hơn, nhiều chướng ngại vật                           |
| Khó        | Bản đồ rộng, nhiều chướng ngại vật di động và đường đi phức tạp |

---

# 🛠 Công nghệ sử dụng

* Python
* Pygame
* Thuật toán A*
* Lập trình hướng đối tượng (OOP)

---

# 📂 Cấu trúc dự án

```text
Snake-AI/
│
├── main.py       
├── snake_config.json            
├── snake_history.json         
├── README.md
└── requirements.txt
```

---

# 🚀 Hướng dẫn cài đặt

### 1. Clone dự án

```bash
git clone https://github.com/your-username/Snake-AI.git
```

### 2. Di chuyển vào thư mục dự án

```bash
cd Snake-AI
```

### 3. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 4. Chạy chương trình

```bash
python main.py
```

---

# 📸 Demo

Demo Link: <a href="https://drive.google.com/file/d/1Nbu5WmFbzJ-COTXK8lOHlVEuKkkdF-8b/view?usp=sharing">Demo Game Snake A*</a>

---

# 🎯 Mục tiêu của đề tài

* Tìm hiểu và áp dụng thuật toán A* vào bài toán tìm đường.
* Xây dựng trò chơi trên môi trường Grid.
* Mô phỏng trí tuệ nhân tạo trong game.
* Nâng cao kỹ năng lập trình Python và Pygame.
* Thực hành lập trình hướng đối tượng và tối ưu thuật toán.

---

# 📈 Hướng phát triển

Trong tương lai, dự án có thể được mở rộng với các chức năng như:

* Thêm nhiều bản đồ mới.
* Nâng cấp AI với Hamiltonian Cycle.
* So sánh A* với các thuật toán khác.
* Thống kê hiệu năng thuật toán.
* Thêm chế độ người chơi và chế độ AI.
* Thiết kế hệ thống lưu điểm và bảng xếp hạng.

---


# 📄 Giấy phép

Dự án được thực hiện nhằm mục đích học tập và nghiên cứu.

Bạn có thể tham khảo, chỉnh sửa và phát triển thêm cho mục đích giáo dục.
