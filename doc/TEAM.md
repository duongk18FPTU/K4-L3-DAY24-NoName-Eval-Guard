# Nhóm thực hiện K4 Track 3B

Tên nhóm: {{Tên nhóm}}

Repo chung: {{Link repo}}

Trưởng nhóm/người nộp: {{Họ tên và MSSV}}

Ngày lab/deadline áp dụng: {{Ngày giờ theo thông báo lớp}} — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: {{Commit SHA}}

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |
| 2 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |
| 3 | {{Họ tên}} | {{MSSV}} | {{Phase/file/hàm}} | {{Commit/PR/report}} |

Người tích hợp/chạy batch/nộp link: {{Họ tên, công việc và bằng chứng}}.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: {{Phiên bản thực tế}}.
Virtualenv/dependencies/imports: {{Lệnh và kết quả}}.
Models/Qdrant/50 answers đã chuẩn bị: {{Bằng chứng và giới hạn/fallback}}.
Nếu cài full NeMo chưa thành công, ghi lỗi thực tế; không dùng unit test pass
hoặc pip resolve để khẳng định runtime đã chạy.

## INDIVIDUAL

### NgoMinhTri-2A202602993

- Phần được giao theo PLAN: Phase B (Tasks 5–8), Phase C (Tasks 9a–12).
- Đã chuẩn bị code: pairwise JSON judge có validation, đổi thứ tự A/B và quy đổi scores,
  Cohen κ, thống kê bias; Presidio detect/redact, NeMo input/output theo quyết định rail,
  suite có short-circuit PII và latency đo hai input layers với hai warm-up thật.
- Bằng chứng hiện tại: `src/phase_b_judge.py`, `src/phase_c_guard.py`, `doc/LOCAL_SETUP.md`;
  chưa commit; artifact C live có nhưng chưa đạt, xem `doc/reports/guard_handoff.md`.
- Cách kiểm tra: Presidio engine thật detect/redact 4/4 PII attacks, không chặn 8/8
  clean inputs; cấu hình NeMo parse đạt. Phase C đã chạy live, kết quả và giới hạn ghi bên dưới.
- Nội dung cần giải thích khi nghiệm thu: winner A/B khác nhãn binary 0/1; pass 2 phải đổi
  cả winner và scores về thứ tự gốc; clean controls phát hiện always-block; input-layer latency
  không đại diện full guard/RAG latency. Thành viên tự đối chiếu trước khi nộp.
- Giới hạn: đã chạy Phase C live với OpenRouter free router; artifact batch đầu chưa đạt
  (attacks 20/20, clean 0/8, outputs 2/4, input P95 1464.614036ms).
  Diagnostic xác nhận self-check completion rỗng với budget 3 tokens; đã tăng budget 2048
  nhưng lượt chạy lại bị quota 50 requests/ngày (HTTP 429), chưa xác minh bản sửa live.
  Answers của Dương đã kéo về từ main `eef8e49` và validate đạt 50 câu 20/20/10;
  Phase B live đã đủ dữ liệu đầu vào nhưng chưa chạy, chưa có κ/bias thực nghiệm.
- AI hỗ trợ: Codex đọc tài liệu, cài môi trường, implement code B/C và chạy kiểm tra.
  Kiểm tra Presidio dùng engine thật, Phase C gọi API live. Thành viên cần tự review và giải thích code.

Sao chép mẫu cho mỗi thành viên; tiêu đề họ tên không dấu-MSSV.

### {{HoVaTen}}-{{MSSV}}

- Phần được giao và phần thực tế đã làm: {{Nhiệm vụ, file/hàm, mục đích}}.
- Bằng chứng: {{Commit/PR và artifacts/reports liên quan}}.
- Cách kiểm tra: {{Lệnh và kết quả kiểm tra thực tế}}.
- Điều đã học: {{Khái niệm và cách thể hiện trong bài}}.
- Giới hạn/cách xử lý: {{Vấn đề và kiểm chứng}}.
- Nguồn/AI hỗ trợ nếu có: {{Công cụ, phạm vi, cách tự kiểm chứng}}.

## Cập nhật sau khi nộp

{{Ghi phiên bản nộp; nếu sửa sau deadline, ghi commit/thời điểm/lý do và thông báo
coach cho phép áp dụng bản cập nhật. Nếu không có cập nhật, ghi rõ không có.}}
