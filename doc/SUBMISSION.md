# Nộp bài K4 Track 3B

**Bài nhóm: một repo chung của trưởng nhóm, một link nộp.**

## Tên repo và nơi nộp

Repo nhóm: `K4-L3-DAY24-NoName-Eval-Guard`. Tên nhóm không dấu, không khoảng
trắng, ngăn phần bằng dấu `-`. DAY24 theo tên repo nguồn; L3 trong mẫu tên chỉ
level, không phải nhãn số bài học. Không tạo repo nộp riêng cho từng thành viên.

Trưởng nhóm gửi link GitHub và commit dùng để chấm qua kênh coach công bố.
Repo phải truy cập được với người chấm; cấp quyền theo hướng dẫn nếu private.
Ngày lab/kênh nhận link lấy từ thông báo lớp.

Deadline mặc định **23:59 ngày làm lab, Asia/Ho_Chi_Minh (UTC+07:00)**; áp dụng
điều chỉnh của key coach trong 48 giờ sau lab theo quy ước. Nộp muộn/sửa sau
deadline theo [RULES.md](RULES.md); ghi phiên bản nộp trong TEAM.

## File phải có trong repo

Cây dưới đây là trạng thái **sau khi hoàn thành bài**. Starter chưa có năm
module RAG của nhóm, `artifacts/answers_50q.json` hay ba JSON kết quả trong `artifacts/`.
TEAM và các báo cáo Markdown ban đầu là templates để nhóm tự điền.

```text
K4-L3-DAY24-NoName-Eval-Guard/
+-- README.md
+-- config.py
+-- pytest.ini
+-- .env.example
+-- .gitignore
+-- doc/
|   +-- ASSIGNMENT.md
|   +-- SUBMISSION.md
|   +-- RUBRIC.md
|   +-- CHECKPOINTS.md
|   +-- RULES.md
|   +-- TEAM.md
|   +-- ENVIRONMENT.md
|   +-- PIPELINE_INTERFACE.md
|   +-- REPORT_SCHEMAS.md
|   +-- schemas/
|   |   +-- answers.schema.json
|   |   +-- phase_a.schema.json
|   |   +-- phase_b.schema.json
|   |   +-- phase_c.schema.json
|   +-- reports/
|       +-- failure_clusters.md
|       +-- bias_report.md
|       +-- blueprint.md
+-- src/
|   +-- m1_chunking.py
|   +-- m2_search.py
|   +-- m3_rerank.py
|   +-- m4_eval.py
|   +-- m5_enrichment.py
|   +-- phase_a_ragas.py
|   +-- phase_b_judge.py
|   +-- phase_c_guard.py
|   +-- experiment_support.py
|   +-- experiment_runners.py
|   +-- report_contracts.py
+-- scripts/
|   +-- __init__.py
|   +-- setup_answers.py
|   +-- run_experiments.py
|   +-- check_lab.py
+-- fixtures/
|   +-- test_set_50q.json
|   +-- human_labels_10q.json
|   +-- adversarial_set_20.json
|   +-- clean_set_8.json
|   +-- output_set_4.json
+-- requirements/
|   +-- requirements.txt
|   +-- constraints-core.txt
|   +-- requirements-test.txt
|   +-- requirements-test.lock.txt
+-- infra/
|   +-- docker-compose.yml
+-- tests/
+-- data/
+-- guardrails/
+-- artifacts/
    +-- answers_50q.json
    +-- ragas_50q.json
    +-- judge_results.json
    +-- guard_results.json
```

Giữ tests, dữ liệu và hỗ trợ của starter. Nếu mang `pipeline.py` từ bài trước,
có thể giữ tham khảo; không bắt buộc nếu giao diện năm module RAG đầy đủ. Không nộp
virtualenv, cache, compiler installer hay key. Chỉ `.env.example` rỗng secrets
được commit; `.env` nằm ngoài bài nộp.

## Bằng chứng và cách tạo

| Bằng chứng | Nội dung | Cách tạo |
|---|---|---|
| artifacts/answers_50q.json | 50 source ids, 20/20/10; answer/contexts/ground_truth; generation_mode/generation_model | Setup thật trước lớp |
| artifacts/ragas_50q.json | 50 per_question; distribution summaries; matrix/weakest means; 10 bottom rows Task 3 | Runner A |
| artifacts/judge_results.json | 5 cặp nguồn A/B; 10 binary judgments trên model_answer gốc; κ/bias | Runner B |
| artifacts/guard_results.json | 20 attacks, 8 clean, 4 outputs, raw/statistical latency; metadata | Runner C |
| doc/reports/failure_clusters.md | Đối chiếu điểm/contexts/bottom và đề xuất sửa | Điền tay |
| doc/reports/bias_report.md | Đối chiếu candidate sources, exact calibration answers, κ/bias và giới hạn | Điền tay |
| doc/reports/blueprint.md | Kiến trúc, failure action, measurement scope, CI gates/monitoring đề xuất | Điền tay |
| doc/TEAM.md | Thành viên, MSSV, công việc thật, evidence, INDIVIDUAL, môi trường | Từng người điền |

Xem [REPORT_SCHEMAS.md](REPORT_SCHEMAS.md) và các JSON Schema. Không nộp mock
results, file rỗng, số đo tự điền hoặc source hashes stale. Checker đối chiếu
counts/id/labels/averages/pass flags/percentiles, không chỉ kiểm tra file tồn tại.
Checker validate bốn JSON Schema trước khi đối chiếu hợp đồng. Metadata reports
dùng phiên bản 2 và model IDs tách generation/evaluator/judge/guard; Phase A
không được dùng model judge thay cho thông tin evaluator m4.

## Kiểm tra trước khi gửi

1. Khi TODO hoàn thành, chạy unit tests offline và batch thật theo đề bài.
   Không chạy live integration thêm lần nữa nếu artifacts đã có.
2. Thay mọi placeholder/bảng rỗng trong TEAM và ba Markdown reports.
   RAG/output/full guard latency ngoài Task 12 có thể ghi “chưa đo” và kế hoạch.
3. Chạy `python scripts/check_lab.py`; hoặc một lệnh `--with-tests` để gộp pytest.
4. Kiểm tra secrets rồi commit/push; mở đúng commit trên GitHub trước khi nộp.

```bash
git check-ignore artifacts/answers_50q.json artifacts/ragas_50q.json artifacts/judge_results.json artifacts/guard_results.json
git status --short
git rev-parse HEAD
```

Không có đường dẫn in ra từ check-ignore nghĩa là các file không bị ignore
(mã thoát 1 bình thường). Số checks đạt không phải điểm rubric. Trưởng nhóm nộp
một link bản cuối; các thành viên không gửi bản mã khác nhau.
