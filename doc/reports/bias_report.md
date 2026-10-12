# Đánh giá LLM Judge Phase B

Nhóm: NoName. Người phụ trách: Ngô Minh Trí — 2A202602993 (viết code `src/phase_b_judge.py`).

**Trạng thái: đã chạy live.** Lượt chạy thật do Nguyễn Thanh Dương thực hiện trên máy của Dương bằng
`python scripts/run_experiments.py --phase b --live` (20 lời gọi API), vì OpenRouter free của Trí hết quota.
Nguồn: `artifacts/judge_results.json`; run timestamp 2026-10-12T16:28:40Z.
Judge: `openai/gpt-oss-120b` qua Groq (một model cố định cho cả pairwise và binary). Generation của cột A:
`openai/gpt-oss-20b`. Báo cáo này viết lại từ JSON thật, thay bản nháp "chưa chạy live" trước đó.

## Năm cặp A/B và hai lượt

A lấy nguyên `answer` từ answers của Dương; B lấy nguyên `model_answer` từ human fixture.
Question/reference lấy theo cùng id từ test set. Ids cố định: 1, 5, 12, 21, 41.

| Id | Độ dài A | Độ dài B | Winner pass 1 | Winner pass 2 (đã quy về A/B gốc) | Final | Scores pass 1 (A / B) | Scores pass 2 (A / B) |
|---|---:|---:|---|---|---|---|---|
| 1 | 16 | 57 | B | B | B | 0.60 / 0.80 | 0.50 / 0.80 |
| 5 | 38 | 33 | A | A | A | 1.00 / 0.10 | 1.00 / 0.00 |
| 12 | 14 | 50 | B | B | B | 0.75 / 0.80 | 0.65 / 0.75 |
| 21 | 15 | 82 | B | B | B | 0.00 / 1.00 | 0.00 / 0.97 |
| 41 | 41 | 37 | A | A | A | 0.85 / 0.25 | 0.80 / 0.00 |

Pass 1 đánh giá A/B; pass 2 đánh giá B/A với cùng reference. Sau pass 2, đổi winner và
scores về nhãn gốc. Hai winners đồng thuận thì giữ winner đó; khác nhau trả tie.
Position inconsistency = số cặp không đồng thuận / tổng số cặp.
Verbosity rate = số winner dài hơn / số cặp decisive; tie không vào mẫu số.
Các rates là dấu hiệu thống kê, cần đọc nội dung và reasoning trước kết luận bias.

## Bias: số đo và diễn giải

| Chỉ số | Giá trị |
|---|---|
| Position inconsistency | 0/5 = 0.0 |
| Cặp decisive (không tie) | 5/5 |
| A thắng và A dài hơn | 2 (ids 5, 41) |
| B thắng và B dài hơn | 3 (ids 1, 12, 21) |
| Verbosity rate (winner dài hơn) | 5/5 = 1.0 |

**Position bias:** cả 5 cặp cho cùng winner sau khi đổi chỗ, nên trong mẫu này không thấy dấu hiệu judge
chọn theo vị trí. Với chỉ 5 cặp và 2 lượt, kết quả 0/5 chưa đủ để kết luận judge không có position bias; các
điểm số cũng ổn định giữa hai lượt (chênh tối đa 0.25, ở id 41).

**Verbosity:** tỉ lệ 5/5 vượt ngưỡng đáng lo (0.6), nhưng đọc nội dung cho thấy nó không phải bằng chứng bias:
- Ids 5 và 41: câu thắng chỉ dài hơn 5 và 4 ký tự và thắng vì **đúng** (id 5: CEO duyệt trên 50 triệu, B sai
  "Giám đốc phòng ban"; id 41: A nêu đúng 15 ngày theo v2024, B nêu bản cũ 12 ngày của v2023). Judge nêu đúng
  nguyên nhân trong cả hai lượt, kể cả việc ưu tiên phiên bản hiện hành.
- Id 21: A là "Không tìm thấy." nên B thắng do nội dung, không do độ dài.
- Ids 1 và 12 là hai cặp đáng ngờ nhất: cả hai đáp án cùng đúng về con số (3 ngày; 1 tháng lương), câu dài
  hơn thắng với biên nhỏ (id 12: 0.75 vs 0.80 và 0.65 vs 0.75) vì "đầy đủ ngữ cảnh hơn" (nêu "có lương",
  "Nhân viên"). Đây có thể là ảnh hưởng nhẹ của độ dài/diễn đạt, nhưng 2 mẫu không đủ để khẳng định.
Kết luận: verbosity rate cao ở đây phần lớn trùng với độ đúng; chỉ ids 1 và 12 là dấu hiệu cần theo dõi, cần
bộ cặp lớn hơn (độ dài ngược chiều độ đúng) mới kiểm chứng được.

## Calibration đúng model_answer

10 lượt binary dùng đúng question và model_answer của human fixture, cùng reference từ
test set. Prompt không chứa human_label, human_note hoặc phân bố nhãn.
Runner thu đủ nhãn judge trước khi lấy human labels đối chiếu.
Nhãn phải là integer 0/1; bool, string và answer thay thế bị từ chối.

| Question id | Judge | Human |
|---|---:|---:|
| 1 | 1 | 1 |
| 5 | 0 | 0 |
| 12 | 1 | 1 |
| 21 | 1 | 1 |
| 23 | 1 | 1 |
| 29 | 0 | 0 |
| 33 | 1 | 1 |
| 41 | 0 | 0 |
| 46 | 1 | 1 |
| 50 | 0 | 0 |

Cohen κ = (observed agreement − chance agreement) / (1 − chance agreement).
Observed agreement = 10/10 = 1.0. Judge có 6 nhãn 1 và 4 nhãn 0, trùng phân bố của người, nên chance agreement =
0.6×0.6 + 0.4×0.4 = 0.52. **κ = (1.0 − 0.52) / (1 − 0.52) = 1.0.** Theo thang Landis–Koch đây là "almost perfect"
và vượt ngưỡng bonus κ > 0.6.

Các lý do judge nêu khớp với ghi chú: id 5 sai người phê duyệt; id 29 thiếu "Kế toán trưởng"; id 41 dùng chính
sách cũ 12 ngày; id 50 nói được dùng VPN cá nhân trái với reference "cấm". Không có cặp lệch nào để phân tích.

## Kiểm tra và giới hạn

Code JSON judge từ chối scores bool, NaN, ngoài [0,1]; không tự thay giá trị lỗi.
- Chỉ 10 nhãn và 5 cặp: κ = 1.0 trên 10 mẫu có khoảng tin cậy rất rộng, không chứng minh judge hoàn hảo trên
  mọi câu hỏi HR. Dữ liệu 6/4 cũng làm chance agreement khá cao (0.52).
- Judge được đưa cả question, answer và **reference**, nên bài toán dễ hơn so với chấm không có đáp án. Kết quả
  không áp dụng cho trường hợp không có reference.
- Cùng một model (`gpt-oss-120b`) chấm cả hai lượt; chưa so sánh với judge model khác. Cột A do `gpt-oss-20b` sinh,
  cùng họ model với judge nên có thể có thiên vị cùng họ, chưa kiểm tra.
- Judge là model suy luận, reasoning pass 2 dùng nhãn đã hoán đổi (A/B của lượt hai), nên khi đọc phải đối chiếu.
- Chạy một lần (không lặp) nên chưa đo độ biến thiên giữa các lượt chạy; temperature của pairwise do code Task 5 đặt.
