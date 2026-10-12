# Nhóm thực hiện K4 Track 3B

Tên nhóm: NoName

Repo chung: https://github.com/duongk18FPTU/K4-L3-DAY24-NoName-Eval-Guard

Trưởng nhóm/người nộp: Nguyễn Thanh Dương - 2A202602961

Ngày lab/deadline áp dụng: 11:59 AM (13/10/2026) — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: `4189dab4ce94400637388f55634121e40f4ad859` (commit ngay sau đó chỉ ghi SHA này vào TEAM.md, không đổi mã hay kết quả).

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Nguyễn Thanh Dương | 2A202602961 | CP0: `src/m1_chunking.py` đến `m5_enrichment.py`, sinh 50 answers; Phase A (`src/phase_a_ragas.py` Task 1–4); `doc/reports/failure_clusters.md`, `blueprint.md`; tích hợp và nộp bài | Commit `3555f46`, `a39e774`, `eef8e49`, `def904a`; `artifacts/answers_50q.json`, `artifacts/ragas_50q.json` |
| 2 | Ngô Minh Trí | 2A202602993 | Phase B (`src/phase_b_judge.py` Task 5–8) và Phase C (`src/phase_c_guard.py` Task 9a–12), `guardrails/config.yml`, `doc/reports/bias_report.md`, `guard_handoff.md` | Commit `4237d9b` (tác giả Git hiển thị là "Long Tran"); `artifacts/guard_results.json` |

Phân công chi tiết và quyền sở hữu file nằm ở `doc/PLAN.md`.

Người tích hợp/chạy batch/nộp link: Nguyễn Thanh Dương. Đã dựng pipeline RAG m1–m5, chạy
`scripts/setup_answers.py --live` (50 answers) và `scripts/run_experiments.py --phase a --live`, đưa
`answers_50q.json` lên `main` (commit `eef8e49`) để Trí dùng cho Phase B; sẽ chạy `scripts/check_lab.py` và gửi link nộp.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows 10 Pro 10.0.19045; Python 3.12.10 (bản 3.11 mục tiêu của lab không có trên máy);
Docker 29.5.3; GPU NVIDIA (CUDA 13.2). Chưa kiểm tra/cài Microsoft C++ Build Tools.
Virtualenv/dependencies/imports: `.venv` (Python 3.12) cài tập con cho CP0 + Phase A: ragas 0.1.22,
langchain 0.2.17, langchain-core 0.2.43, langchain-openai 0.1.25, openai 1.109.1, numpy 1.26.4,
sentence-transformers 5.7.0, qdrant-client 1.9.2, torch 2.11.0+cu128 (`torch.cuda.is_available()` = True).
`pip check` báo "No broken requirements found". Phải hạ `pyarrow<20` (bản mới cần NumPy 2, trái pin NumPy 1.26.4)
và `setuptools<82`. NeMo Guardrails, Annoy, Presidio và spaCy **không** được cài trong venv này (thuộc Phase C của Trí),
nên NeMo 0.10.0 chưa được chứng minh chạy trên môi trường của Dương.
Models/Qdrant/50 answers đã chuẩn bị: Qdrant `qdrant/qdrant:v1.9.7` chạy bằng
`docker compose --env-file .env -f infra/docker-compose.yml up -d`; cổng 6333/6334 nằm trong dải Windows
reserved (6297–6396) nên máy Dương map sang 16333/16334 qua biến `QDRANT_PORT`/`QDRANT_GRPC_PORT` (mặc định
trong code vẫn là 6333). Ổ C: gần đầy (còn khoảng 3.6GB) nên cache HuggingFace/pip/tmp chuyển sang ổ D:.
BGE-M3 và `BAAI/bge-reranker-v2-m3` tải về và chạy trên GPU; index 140 chunk từ 26 tài liệu. Hai PDF
(`BCTC.pdf`, Nghị định 13) là bản scan không có lớp chữ nên bị bỏ qua (không OCR). 50 answers sinh bằng
`openai/gpt-oss-20b` qua Groq, cả 50 có `generation_mode=llm` và qua `validate_answers`. LLM evaluator dùng API
miễn phí (Groq, Gemini) vì không thanh toán được OpenAI; bị giới hạn quota nên RAGAS phải chia nhiều lượt có cache.
Phase B/C live cuối được chạy trên máy Dương trong `.venv-guard` (Python 3.12.10, riêng với `.venv`):
`nemoguardrails==0.10.0` cài bằng `--no-deps` cùng presidio-analyzer/anonymizer, spaCy `en_core_web_lg`, fastembed,
langchain 0.2.x. **Annoy 1.17.3 không cài được** (không có wheel Windows, không có MSVC và ổ C: không đủ chỗ), nên
`annoy` trong `.venv-guard` là **bản thay thế thuần Python do nhóm tự viết** (tìm kiếm chính xác bằng numpy, khoảng cách
angular, đủ API NeMo dùng); file này không nằm trong repo. NeMo 0.10.0 khởi tạo và chạy self-check input/output thật với
bản thay thế này, nhưng đó **không phải** cấu hình Annoy gốc mà lab yêu cầu. Python 3.12 cũng nằm ngoài phạm vi
được tài liệu NeMo 0.10.0 hỗ trợ (tối đa 3.11). Cấu hình của Trí trên macOS Python 3.11.9 xem `doc/LOCAL_SETUP.md`.

## INDIVIDUAL

### NguyenThanhDuong-2A202602961

- Phần được giao và phần thực tế đã làm: theo `doc/PLAN.md` được giao CP0, Phase A và blueprint/nộp bài. Đã làm:
  (1) viết mới năm module RAG vì nhóm không có code Day 18: `m1_chunking.py` (chia theo heading, parent 2048 /
  child 256 ký tự, gắn tiêu đề tài liệu vào child), `m2_search.py` (BM25 + BGE-M3 trên Qdrant, RRF),
  `m3_rerank.py` (cross-encoder), `m4_eval.py` (RAGAS 0.1.22 với evaluator OpenAI-compat, embedding local, cache theo
  từng câu, tự lặp thay cho `n>1`), `m5_enrichment.py` (làm giàu theo luật, không gọi API);
  (2) `phase_a_ragas.py`: `group_by_distribution`, `run_ragas_50q`, `bottom_10`, `cluster_analysis`;
  (3) chạy setup 50 answers và Phase A thật, viết `failure_clusters.md` và `blueprint.md`.
- Bằng chứng: commit `a39e774` (Phase A Task 1–4), `3555f46` (m1–m5, cấu hình env), `eef8e49` (answers),
  `def904a` (kết quả Phase A, báo cáo lỗi, m4 cache); `artifacts/answers_50q.json`, `artifacts/ragas_50q.json`,
  `doc/reports/failure_clusters.md`, `doc/reports/blueprint.md`, `doc/PLAN.md`.
- Cách kiểm tra: `python -m pytest tests/test_phase_a.py -q` cho 6 passed (m4 mock); `scripts/setup_answers.py --live`
  cho 50 answers và `validate_answers` đạt; `scripts/run_experiments.py --phase a --live` cho `ragas_50q.json` qua
  schema và validator của runner (50 per_question, 10 bottom, matrix); smoke test retrieval thật trên Qdrant + GPU
  với 3 câu hỏi. Kết quả: mean factual 0.922, multi_hop 0.588 (yếu nhất), adversarial 0.844.
  `scripts/check_lab.py` chưa đạt toàn bộ vì còn thiếu `judge_results.json` và `guard_results.json` chưa đạt clean
  controls (phần của Trí), không phải do Phase A.
- Điều đã học: bốn metric faithfulness, answer_relevancy, context_precision, context_recall đo những thứ khác nhau
  và không nên suy nguyên nhân trước khi đọc câu hỏi, answer, contexts. Nhãn mặc định "LLM hallucinating" của
  `DIAGNOSTIC_TREE` sai với 8/10 câu bottom (thực tế là từ chối "Không tìm thấy" do chunk bị cắt). Matrix 20/20/10
  chỉ là kích thước nhóm, nhóm yếu phải chọn theo mean thấp nhất. Bẫy phiên bản policy xuất hiện ngay ở retrieval
  (top 3 chứa cả bản 2023 và 2024).
- Giới hạn/cách xử lý: (a) lỗi chunking trong m1 của chính tôi (bộ tách câu cắt sau `:`) làm 8/50 answers là
  "Không tìm thấy"; đã ghi rõ trong báo cáo cùng cách sửa, chưa sửa và chạy lại vì tốn quota và đổi answers mà
  Phase B của Trí đang dùng. (b) Gemini free tier giới hạn 500 lời gọi/ngày/model và Groq giới hạn 8k token/phút
  nên RAGAS phải chạy nhiều lượt; m4 lưu cache từng câu. (c) Câu 17 và 31 luôn ra `faithfulness` NaN với
  `gemini-3.5-flash-lite` nên được chấm lại bằng `gemini-3.1-flash-lite`; 11/50 câu do model khác chấm nên điểm
  không hoàn toàn đồng nhất. (d) Không có Python 3.11 và chưa cài NeMo trên máy này. (e) Deadline trong tài liệu
  không thống nhất (ASSIGNMENT/RULES ghi 23:59 ngày lab); nhóm áp dụng mốc 11:59 AM 13/10/2026 theo README, cần coach xác nhận.
- Nguồn/AI hỗ trợ nếu có: Claude Code (Claude Opus 5.5 và Sonnet 5.5) đọc tài liệu, viết m1–m5 và Task 1–4, chạy
  lệnh, chẩn đoán lỗi quota/NaN và soạn nháp báo cáo. Kiểm chứng: chạy unit test, chạy Phase A thật trên dữ liệu
  thật, đối chiếu từng nhận định trong `failure_clusters.md` với contexts/answers trong `ragas_50q.json`. Tôi tự
  review và chịu trách nhiệm với phần này; phần của Trí do Trí tự kê khai.

### NgoMinhTri-2A202602993

- Phần được giao theo PLAN: Phase B (Tasks 5–8), Phase C (Tasks 9a–12).
- Đã chuẩn bị code: pairwise JSON judge có validation, đổi thứ tự A/B và quy đổi scores,
  Cohen κ, thống kê bias; Presidio detect/redact, NeMo input/output theo quyết định rail,
  suite có short-circuit PII và latency đo hai input layers với hai warm-up thật.
- Bằng chứng hiện tại: `src/phase_b_judge.py`, `src/phase_c_guard.py`, `doc/LOCAL_SETUP.md`, commit `4237d9b`;
  `artifacts/judge_results.json` và `artifacts/guard_results.json` (lượt chạy live cuối do Dương thực hiện, xem mục
  "Cập nhật của người tích hợp" bên dưới), `doc/reports/bias_report.md`, `doc/reports/guard_handoff.md`.
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

**Cập nhật của người tích hợp (Dương), 12/10/2026:** vì OpenRouter free của Trí hết quota (50 lời gọi/ngày), Dương chạy
lại Phase B/C live bằng Groq (`openai/gpt-oss-120b`) trên máy Dương, dùng nguyên code `phase_b_judge.py` và
`phase_c_guard.py` của Trí (không sửa code B/C) và chỉ đổi `guardrails/config.yml` sang model/base_url của Groq.
Kết quả thật: Phase C attacks 18/20, clean 8/8 được qua (false-positive rate 0), outputs 4/4 đúng, input guard
sequential P95 = 3585.64ms (vượt budget 500ms; 20 mẫu timed, 2 warm-up); Phase B 5 cặp đều nhất quán sau khi đổi chỗ
(position inconsistency 0/5), 10 nhãn binary trùng hoàn toàn với nhãn người, Cohen κ = 1.0. Phần "Giới hạn" ở trên là
trạng thái trước lượt chạy này (batch OpenRouter lỗi); số liệu hiện hành nằm ở các artifact và báo cáo. Trí cần tự đọc
lại phần này và các báo cáo, xác nhận mình giải thích được code và kết quả trước khi nộp.

## Cập nhật sau khi nộp

Phiên bản nộp: commit `4189dab4ce94400637388f55634121e40f4ad859` trên nhánh `main`. Commit tiếp theo chỉ thêm SHA này vào `doc/TEAM.md`.
Hiện chưa có cập nhật nào sau deadline. Nếu sau này có sửa sau deadline, ghi commit/thời điểm/lý do tại đây và thông báo
coach cho phép áp dụng bản cập nhật.
