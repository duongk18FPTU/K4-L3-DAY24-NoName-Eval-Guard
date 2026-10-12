# Blueprint CI/CD cho RAG và guardrails

Nhóm: NoName

Người phụ trách: Nguyễn Thanh Dương - 2A202602961 (số liệu guard do Ngô Minh Trí - 2A202602993 cung cấp
trong `doc/reports/guard_handoff.md`)

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy. Repo không có
`.github/workflows` và chưa có job tự động nào chạy.
Nguồn kết quả: artifacts/ragas_50q.json, judge_results.json, guard_results.json.
Run timestamp: Phase A 2026-10-12T16:13:47Z; Phase C 2026-10-12T10:51:19Z; Phase B chưa có artifact.
Guard models: `openrouter/free` (router của OpenRouter, backend thực tế có thể thay đổi giữa các lượt).
Models theo vai trò: generation `openai/gpt-oss-20b` (Groq, từ answers_50q.json); evaluator RAGAS
`gemini-3.5-flash-lite` + `gemini-3.1-flash-lite` + embedding `BAAI/bge-m3` (từ ragas_50q.json);
judge Phase B chưa chạy live nên chưa có model thực dùng; guard `openrouter/free`.

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.
Request thực dừng sớm khi bị chặn; khác phép đo input layers chạy đủ hai tầng.

Data flow đề xuất:

1. **Presidio** (cục bộ, không gọi mạng) quét CCCD/CMND, số điện thoại VN và email. Nếu có PII thì
   chặn ngay, trả lời từ chối cố định và chỉ ghi log loại thực thể + vị trí, không ghi nội dung PII.
2. **NeMo input rail** (self-check bằng LLM) chặn jailbreak, prompt injection, off-topic và yêu cầu dữ liệu
   cá nhân. Quyết định đọc từ `activated_rails` của NeMo, không suy từ từ khóa "xin lỗi".
3. **RAG** (hybrid BM25 + BGE-M3 trên Qdrant → rerank → top 3 chunk → LLM sinh answer).
4. **NeMo output rail** kiểm tra answer trước khi trả; answer nhạy cảm bị thay bằng câu từ chối đã redact.

Failure action đề xuất: guard API lỗi, timeout hoặc self-check trả rỗng thì **chặn và báo lỗi (fail-closed)**,
không tự cho đi qua. Qdrant/LLM sinh answer lỗi thì trả thông báo lỗi thay vì answer trích đoạn. Log chỉ
gồm id request, quyết định, tầng chặn, thời gian và model; không log nội dung người dùng chưa redact, không
log API key. Secrets nằm trong `.env`/secret store của CI, `.env.example` chỉ có tên biến. Khi LLM của guard
bị giới hạn quota thì phải coi là sự cố (cảnh báo), vì ở bản chạy hiện tại self-check rỗng đã khiến NeMo
chặn nhầm toàn bộ câu sạch.

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Số mẫu timed: 20; warm-up: 2; phương pháp: linear.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 7.91 | 27.74 | 42.39 | Đo bằng Task 12, đạt rất xa mục tiêu |
| NeMo input | 665.63 | 1458.34 | 2710.37 | Đo bằng Task 12 trên batch lỗi (xem bên dưới) |
| Input guard sequential | 672.21 | 1464.61 | 2719.75 | Đo bằng Task 12, vượt budget 500ms |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer budget target: 500ms; kết quả thực tế: P95 = 1464.61ms, `latency_budget_ok = false`.
Nút thắt gần như hoàn toàn nằm ở NeMo input (P95 1458.34ms so với Presidio 27.74ms): mỗi lần kiểm tra là
một lời gọi LLM qua router miễn phí của OpenRouter, nên latency phụ thuộc mạng và hàng đợi của provider.
Cần lưu ý số này đến từ batch Phase C đầu tiên, trong đó self-check còn bị cấu hình budget 3 token và trả
completion rỗng, nên chưa đại diện cho cấu hình đã sửa; số đo sẽ được thay khi nhóm chạy lại Phase C.
Các phần chưa đo (RAG, NeMo output, full guard) giữ "chưa đo". Kế hoạch đo: chạy đủ ít nhất 20 request
thật đi qua cả pipeline với 2 warm-up, ghi timestamp từng tầng bằng `perf_counter`, tính P50/P95/P99 tuyến
tính trên raw samples, tách riêng request bị chặn sớm và request đi hết pipeline. Hướng giảm latency: dùng
model nhỏ, ổn định và có SLA cho self-check; cache quyết định cho câu hỏi lặp lại; chạy Presidio và NeMo input
song song khi chấp nhận tốn thêm một lời gọi cho request có PII.

## CI gates đề xuất

- RAGAS faithfulness ≥0.75, avg_score ≥0.65 trên 50 câu, thêm ngưỡng riêng cho từng distribution
  (multi_hop avg_score ≥0.65).
- Attacks ≥18/20 cho CI đề xuất; clean 8/8 allowed; output cases đúng.
- Full guard P95 <500ms chỉ áp dụng sau khi thực sự đo full guard.

Mốc bắt buộc lab vẫn attacks ≥15/20; bonus ≥18/20 kèm clean controls đạt.

Đề xuất job (chưa triển khai): (1) job **offline** chạy mỗi lần push: `python -m pytest tests/ -m "not integration" -q`
rồi `python scripts/check_lab.py`, trả mã khác 0 khi schema, số lượng, placeholder hoặc ngưỡng artifact không đạt;
(2) job **live** chạy theo lịch hoặc thủ công, tách khỏi push để kiểm soát chi phí và quota:
`python scripts/run_experiments.py --phase a|b|c --live`. Các ngưỡng RAGAS/latency ở trên là biến đề xuất
(ví dụ `MIN_FAITHFULNESS`, `MIN_AVG_SCORE`); runner hiện chưa kiểm tra chúng nên chưa phải quality gate thật,
cần thêm bước script đọc artifact và so ngưỡng trước khi coi là gate.

## Monitoring và cải tiến

Metric theo dõi và ngưỡng cảnh báo đề xuất: tỉ lệ chặn nhầm câu sạch (cảnh báo khi >0), tỉ lệ answer
"Không tìm thấy" (hiện 8/50 = 16%, cảnh báo khi vượt 10%), faithfulness/avg_score trung bình theo
distribution, tỉ lệ HTTP 429/timeout của guard và của LLM sinh answer, P95 latency từng tầng, và drift của
model phía sau router `openrouter/free`. Lấy mẫu: gom ngẫu nhiên 1–5% request thật đã redact PII mỗi tuần
để chấm RAGAS và đọc thủ công các câu điểm thấp. False positive: người vận hành xem lại các câu bị chặn,
thêm vào clean set và chạy lại bộ 8 clean controls. Quyền riêng tư: chỉ lưu đoạn đã redact. Người xử lý: người
tích hợp pipeline (Dương) cho RAGAS/retrieval, người phụ trách guard (Trí) cho false positive và latency.
Giới hạn: bộ 50/20/8/4 nhỏ, mean mỗi nhóm dao động mạnh khi đổi 1–2 câu.

RAGAS mean/worst distribution: factual 0.922, adversarial 0.844, multi_hop 0.588 (nhóm yếu nhất, trung bình
cả 50 câu là 0.773).
Cohen’s κ: chưa có, vì Phase B chưa chạy live (chưa có artifacts/judge_results.json).
Attacks passed: 20/20; clean false_positive_rate: 1.0 (8/8 câu sạch bị chặn nhầm trong batch Phase C đầu,
nên kết quả 20/20 attacks chưa có giá trị kết luận).

Cải tiến có thể kiểm tra, gắn với bằng chứng:

1. **Sửa bộ tách câu của m1** (không cắt sau `:`/`;`, giữ nguyên mục danh sách). Bằng chứng: 8/50 answer là
   "Không tìm thấy", gồm 7/20 câu multi_hop và 6/8 câu có context_recall ≤0.67. Kiểm chứng bằng cách index
   lại, chạy lại Phase A và so số câu từ chối cùng mean multi_hop (0.588).
2. **Tăng `RERANK_TOP_K` và retrieve riêng theo từng phiên bản/tài liệu** cho câu hỏi so sánh. Bằng chứng: ID 39
   chỉ lấy được chunk "bản cũ đã bị thay thế" (context_recall 0.0), ID 37 thiếu chính sách phân loại dữ liệu.
3. **Nới prompt sinh answer** để cho phép cộng/so sánh từ nhiều đoạn, chỉ từ chối khi thật sự thiếu thông tin
   (ID 23 và 26 có context_recall 1.0 nhưng vẫn từ chối).
4. **Đặt guard LLM ổn định và fail-closed**: dùng model cố định thay router miễn phí, kiểm tra completion rỗng và
   429 như lỗi cảnh báo thay vì chặn thầm lặng; chạy lại 8 clean controls sau mỗi lần đổi cấu hình.
5. **Bẫy phiên bản**: thêm metadata `version`/`is_current` khi index và ưu tiên bản hiện hành khi câu hỏi hỏi
   "hiện nay"; kiểm chứng trên nhóm adversarial (hiện 0.844, ID 49 vẫn trả lời theo bản v2023).
