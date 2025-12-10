# Quy luật dịch thuật Hán Việt cho Game Kiếm Hiệp

Tài liệu này tổng hợp các quy tắc (heuristics) giúp nhận diện và xử lý các câu Hán Việt khó hiểu trong văn bản game kiếm hiệp (thường là dạng convert từ tiếng Trung).

---

## Phần 1: Dấu hiệu nhận biết (Cách tìm)

Những câu cần dịch lại thường có các đặc điểm sau:

### 1. Chứa các hư từ/đại từ cổ

Xuất hiện dày đặc các từ:

- **Hư từ:** Chi, Hồ, Giả, Dã, Hĩ, Yên, Giai, Dục, Tương, Sở...
- **Đại từ nhân xưng:**
  - **Ngã** (Ta)
  - **Nhữ** (Ngươi/Mày)
  - **Bỉ** (Hắn/Kẻ kia)
  - **Ngô** (Ta)
  - **Y** (Hắn)

### 2. Cấu trúc ngữ pháp ngược

Tính từ đứng trước danh từ một cách không tự nhiên trong tiếng Việt.

**Ví dụ:**

- "Tối đại công kích" → Công kích lớn nhất
- "Hồng y thiếu nữ" → Thiếu nữ áo đỏ

### 3. Vô nghĩa hoặc tối nghĩa

Đọc lên nghe "kêu" nhưng không hiểu gì, hoặc hiểu sai nghĩa.

**Ví dụ:**

- "Bách tính giai nhận khả" → Nghe lủng củng → "Trăm họ đều công nhận"
- "Ấm đêm" (sai) → Đúng phải là nghĩa khác
- "Du hành" (không phải du lịch)

---

## Phần 2: Quy tắc dịch thuật (Cách sửa)

Khi đã tìm ra câu cần sửa, hãy áp dụng 4 quy tắc vàng sau:

### Quy tắc 1: "Việt hóa" Đại từ và Động từ phổ thông

Đây là bước làm cho câu văn "mềm" ra ngay lập tức.

| Hán Việt  | Tiếng Việt                                  |
| --------- | ------------------------------------------- |
| Ngã / Ngô | Ta / Tôi / Tại hạ / Đệ / Huynh (tùy vai vế) |
| Nhữ / Nhĩ | Ngươi / Các hạ / Nàng / Đệ                  |
| Giai      | Đều / Cùng                                  |
| Dục       | Muốn                                        |
| Thị       | Là (hoặc "nhìn" tùy ngữ cảnh)               |
| Tương     | Đem / Sẽ / Cùng nhau                        |
| Thả / Nhi | Và / Mà còn                                 |
| Dữ        | Với / Cùng                                  |
| Diệc      | Cũng                                        |

**Ví dụ:**

```
Ngã dữ huynh giai dục khứ.
↓
Ta với huynh đều muốn đi.
```

### Quy tắc 2: Đảo ngữ pháp (Tính từ - Danh từ)

Tiếng Trung (và Hán Việt) thường để _Tính từ/Bổ ngữ_ trước _Danh từ_. Tiếng Việt thì ngược lại.

**Công thức:**

```
[A + B] trong Hán Việt → [B + A] trong tiếng Việt
```

**Ví dụ 1:**

```
Địch phương du hành
(Địch phương = phe địch; du hành = người chơi/khách)
↓ Đảo lại
Du khách phe địch
(hoặc hay hơn: Đối thủ phe địch)
```

**Ví dụ 2:**

```
Hồng vận đương đầu
↓
Vận đỏ (may mắn) phủ đầu / tới tấp
```

### Quy tắc 3: Giữ "Chất" Kiếm Hiệp (Từ chuyên môn)

Đừng dịch hết sang tiếng Việt hiện đại, nếu không sẽ mất "vị" kiếm hiệp. Hãy giữ lại các từ Hán Việt mang tính ước lệ.

#### Nên giữ:

- Giang hồ
- Hiệp khách
- Nội công
- Kinh mạch
- Chưởng môn
- Tiểu nhị
- Bổn toạ
- Tại hạ
- Thí chủ
- Huynh đài

#### Nên dịch:

| Hán Việt    | Tiếng Việt                                                  |
| ----------- | ----------------------------------------------------------- |
| Thương nhân | Có thể giữ, hoặc dùng "lái buôn"                            |
| Hỏa pháo    | Pháo hoa (nếu là đồ chơi)<br>Pháo thần công (nếu là vũ khí) |
| Ẩm tử       | Đồ uống / Quán nước                                         |

### Quy tắc 4: Giải mã các từ "Bẫy" (False Friends)

Có những từ Hán Việt nghe rất quen nhưng nghĩa trong game lại khác hẳn.

#### Du hành

- **Nghĩa trong game:** Người chơi (Player) hoặc Hiệp khách đi dạo
- **KHÔNG phải:** Phi hành gia hay đi du lịch

#### Thương

Cần nhìn bối cảnh để phân biệt:

- Đau thương
- Buôn bán (thương nhân)
- Cây thương (vũ khí)

#### Đạo

Có thể là:

- Đạo lý
- Con đường
- Đạo sĩ
- Đạo tặc (ăn trộm)

**Ví dụ:**

```
Thư thị tiềm nhập nga bằng đạo lai đích
↓
Chữ "đạo" ở đây là "đạo tặc/trộm"
↓
Sách này là lẻn vào chuồng ngỗng trộm về đấy.
```

---

## Quy trình thực hành nhanh

### Ví dụ thực tế

**Câu gốc:**

```
Ngã dĩ vị ngã bất tưởng Bị nhi? Bị nhi na ma thông minh, yếu thị hiện tại thị tha cân trứ ngã chủng sơn dược...
```

#### Bước 1: Nhận diện

Thấy "Ngã", "Bị nhi", "na ma", "yếu thị", "cân trứ". Đây là văn nói bị convert thô.

#### Bước 2: Việt hóa từ khóa

| Hán Việt  | Tiếng Việt                 |
| --------- | -------------------------- |
| Ngã       | Ta                         |
| Bất tưởng | Không nhớ / Không nghĩ đến |
| Na ma     | Như vậy / Thế              |
| Yếu thị   | Nếu như                    |
| Cân trứ   | Theo / Cùng                |
| Chủng     | Trồng                      |

#### Bước 3: Sắp xếp & Làm mượt

```
Ta tưởng ta không nhớ Bị nhi? Bị nhi thông minh thế, nếu như hiện tại nó cùng ta trồng sơn dược...
```

#### Bước 4: Hoàn thiện

```
Ngươi tưởng ta không nhớ Bị nhi sao? Bị nhi thông minh như vậy, nếu hiện giờ nó cùng ta trồng sơn dược...
```

---

## Tóm tắt

1. **Tìm:** Nhận diện hư từ cổ, cấu trúc ngược, câu vô nghĩa
2. **Việt hóa:** Đại từ, động từ phổ thông
3. **Đảo:** Tính từ - Danh từ
4. **Giữ chất:** Từ chuyên môn kiếm hiệp
5. **Giải mã:** False friends (du hành, thương, đạo...)

---

_Tài liệu được tạo: 2025-12-11_
