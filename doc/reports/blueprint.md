# Blueprint CI/CD cho RAG và guardrails

Nhóm: NoName

Người phụ trách: Nguyễn Thanh Dương - 2A202602961 (code Phase B/C do Ngô Minh Trí - 2A202602993 viết; lượt chạy
live cuối của B/C do Dương thực hiện, xem `doc/reports/guard_handoff.md`)

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy. Repo không có
`.github/workflows` và chưa có job tự động nào chạy.
Nguồn kết quả: artifacts/ragas_50q.json, judge_results.json, guard_results.json.
Run timestamp: Phase A 2026-10-12T16:13:47Z; Phase C 2026-10-12T16:27:17Z; Phase B 2026-10-12T16:28:40Z.
Guard models: `openai/gpt-oss-120b` (qua Groq, từ metadata.models.guard của guard_results.json).
Models theo vai trò: generation `openai/gpt-oss-20b` (Groq, từ answers_50q.json); evaluator RAGAS
`gemini-3.5-flash-lite` + `gemini-3.1-flash-lite` + embedding `BAAI/bge-m3` (từ ragas_50q.json);
judge Phase B `openai/gpt-oss-120b`; guard `openai/gpt-oss-120b`.

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
bị giới hạn quota thì phải coi là sự cố (cảnh báo), vì ở batch đầu của Trí self-check rỗng (budget 3 token) đã khiến
NeMo chặn nhầm 8/8 câu sạch; batch cuối đã đặt `max_tokens` 2048 và cho 8/8 câu sạch qua.

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Số mẫu timed: 20; warm-up: 2; phương pháp: linear.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 7.62 | 9.33 | 9.96 | Đo bằng Task 12, đạt rất xa mục tiêu |
| NeMo input | 2904.54 | 3578.42 | 4135.44 | Đo bằng Task 12, vượt budget |
| Input guard sequential | 2913.51 | 3585.64 | 4143.63 | Đo bằng Task 12, vượt budget 500ms |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer budget target: 500ms; kết quả thực tế: P95 = 3585.64ms, `latency_budget_ok = false` (vượt khoảng 7 lần).
Nút thắt gần như hoàn toàn nằm ở NeMo input (P95 3578.42ms so với Presidio 9.33ms): mỗi lần kiểm tra là một lời gọi
LLM tới Groq bằng model suy luận `gpt-oss-120b`, tốn thời gian "nghĩ" trước khi trả Yes/No, nên latency phụ thuộc mạng,
hàng đợi của provider và giới hạn token/phút của gói miễn phí. Số này thay thế batch đầu của Trí (P95 1464.61ms,
chạy khi self-check còn lỗi). Giữ nguyên số đo thật, không chỉnh cho đạt budget.
Các phần chưa đo (RAG, NeMo output, full guard) giữ "chưa đo". Kế hoạch đo: chạy đủ ít nhất 20 request
thật đi qua cả pipeline với 2 warm-up, ghi timestamp từng tầng bằng `perf_counter`, tính P50/P95/P99 tuyến
tính trên raw samples, tách riêng request bị chặn sớm và request đi hết pipeline. Hướng giảm latency: dùng
model không suy luận (hoặc `reasoning_effort` thấp), nhỏ và có SLA cho self-check; cache quyết định cho câu hỏi lặp lại; chạy Presidio và NeMo input
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
Cohen’s κ: 1.0 trên 10 nhãn (observed agreement 10/10, chance agreement 0.52); position inconsistency 0/5;
verbosity rate 5/5 nhưng đọc nội dung thì phần lớn trùng với độ đúng (xem `bias_report.md`).
Attacks passed: 18/20; clean false_positive_rate: 0.0 (8/8 câu sạch được cho qua); output cases 4/4 đúng.
Hai attack lọt là off_topic (id 11 yêu cầu viết thơ, id 14 giải phương trình vi phân): self-check chưa coi là off-topic.

Cải tiến có thể kiểm tra, gắn với bằng chứng:

1. **Sửa bộ tách câu của m1** (không cắt sau `:`/`;`, giữ nguyên mục danh sách). Bằng chứng: 8/50 answer là
   "Không tìm thấy", gồm 7/20 câu multi_hop và 6/8 câu có context_recall ≤0.67. Kiểm chứng bằng cách index
   lại, chạy lại Phase A và so số câu từ chối cùng mean multi_hop (0.588).
2. **Tăng `RERANK_TOP_K` và retrieve riêng theo từng phiên bản/tài liệu** cho câu hỏi so sánh. Bằng chứng: ID 39
   chỉ lấy được chunk "bản cũ đã bị thay thế" (context_recall 0.0), ID 37 thiếu chính sách phân loại dữ liệu.
3. **Nới prompt sinh answer** để cho phép cộng/so sánh từ nhiều đoạn, chỉ từ chối khi thật sự thiếu thông tin
   (ID 23 và 26 có context_recall 1.0 nhưng vẫn từ chối).
4. **Siết prompt off-topic và giảm latency của guard**: 2/20 attack off_topic lọt qua và P95 NeMo input 3.58 giây. Thêm ví dụ
   off-topic vào prompt self-check, dùng model không suy luận; kiểm completion rỗng và 429 như lỗi cảnh báo thay vì
   chặn thầm lặng; chạy lại 20 attacks + 8 clean controls sau mỗi lần đổi cấu hình.
5. **Bẫy phiên bản**: thêm metadata `version`/`is_current` khi index và ưu tiên bản hiện hành khi câu hỏi hỏi
   "hiện nay"; kiểm chứng trên nhóm adversarial (hiện 0.844, ID 49 vẫn trả lời theo bản v2023).
