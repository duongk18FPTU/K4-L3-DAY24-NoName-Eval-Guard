# Đánh giá LLM Judge Phase B

Nhóm: NoName. Người phụ trách: Ngô Minh Trí — 2A202602993.

**Trạng thái: đã chuẩn bị code; chưa chạy judge live do quota OpenRouter.**
Chưa có `artifacts/judge_results.json`; chưa có winners, nhãn judge, κ hay rates bias thực nghiệm.

## Năm cặp A/B và hai lượt

A lấy nguyên `answer` từ answers của Dương; B lấy nguyên `model_answer` từ human fixture.
Question/reference lấy theo cùng id từ test set. Ids cố định: 1, 5, 12, 21, 41.
Generation model trong answers: `openai/gpt-oss-20b` qua Groq theo commit `eef8e49`.
Judge dự kiến: `openrouter/free` qua OpenRouter; model thực phục vụ có thể khác giữa các lượt.

| Id | Câu hỏi | Độ dài A (ký tự) | Độ dài B (ký tự) | Kết quả |
|---|---|---:|---:|---|
| 1 | Nhân viên được nghỉ bao nhiêu ngày khi kết hôn? | 16 | 57 | Chưa chạy live |
| 5 | Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt? | 38 | 33 | Chưa chạy live |
| 12 | Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là bao nhiêu? | 14 | 50 | Chưa chạy live |
| 21 | Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào? | 15 | 82 | Chưa chạy live |
| 41 | Nhân viên được nghỉ bao nhiêu ngày phép năm? | 41 | 37 | Chưa chạy live |

Pass 1 đánh giá A/B; pass 2 đánh giá B/A với cùng reference. Sau pass 2, đổi winner và
scores về nhãn gốc. Hai winners đồng thuận thì giữ winner đó; khác nhau trả tie.
Position inconsistency = số cặp không đồng thuận / tổng số cặp.
Verbosity rate = số winner dài hơn / số cặp decisive; tie không vào mẫu số.
Các rates là dấu hiệu thống kê, cần đọc nội dung và reasoning trước kết luận bias.

## Calibration đúng model_answer

10 lượt binary dùng đúng question và model_answer của human fixture, cùng reference từ
test set. Prompt không chứa human_label, human_note hoặc phân bố nhãn.
Runner thu đủ nhãn judge trước khi lấy human labels đối chiếu.
Nhãn phải là integer 0/1; bool, string và answer thay thế bị từ chối.

Cohen κ = (observed agreement − chance agreement) / (1 − chance agreement).
Nhãn rỗng, độ dài lệch, ngoài 0/1 hoặc unanimous constant labels không có κ xác định
được báo lỗi. κ thực nghiệm và bảng 10 judgments: chưa có, chờ lượt chạy live.

## Kiểm tra và giới hạn

Code JSON judge từ chối scores bool, NaN, ngoài [0,1]; không tự thay giá trị lỗi.
Bộ dữ liệu chỉ có 5 cặp và 10 nhãn, không đại diện mọi câu hỏi HR.
Free router có thể đổi model, nên position inconsistency còn bị nhiễu bởi model routing.
Chưa có bằng chứng κ >0.6; chưa đủ dữ liệu để khai bonus.

## Bước hoàn tất sau khi có quota

Chạy `.venv/bin/python scripts/run_experiments.py --phase b --live` một lần (20 API calls dự kiến).
Từ JSON thật bổ sung run timestamp, model metadata, 5 rows pairwise với reasoning/scores,
10 binary judgments, observed/chance agreement, κ và phân tích cases lệch.
Không chạy lại live integration sau batch chỉ để xác nhận cùng kết quả.

SHA256 nguồn hiện tại:

- `artifacts/answers_50q.json`: `d3519001b013d5fb11c1c5564d32edd0e5889d8a5769bf6bc2280c382d04f71c`.
- `fixtures/human_labels_10q.json`: `37231c1f4a635801e27a98333898d2d4c9c3c71167e8b9e7259b90cec5956782`.
- `fixtures/test_set_50q.json`: `3ad288426e3066e561737b35b66b671e6c411697dffd0d1161cc7b801e5954cc`.
