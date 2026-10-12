# Bàn giao Phase C cho Dương

Người phụ trách: Ngô Minh Trí — 2A202602993. Nhóm NoName.

**Batch hiện tại chưa đạt lab.** Nguồn: `artifacts/guard_results.json`.
Run timestamp UTC: `2026-10-12T10:51:19.603176+00:00`. Guard configuration: `openrouter/free`.
Router có thể chọn backend model khác nhau; metadata hiện tại ghi router, chưa ghi từng backend.

## Kết quả thật

- Attacks: 20/20; không đủ kết luận chất lượng vì chặn nhầm clean.
- Clean: 0/8; false-positive rate: 100%.
- Outputs: 2/4.
- Schema/counts/sources/percentiles hợp lệ; quality validation fail vì clean inputs bị chặn.

| Layer | P50 ms | P95 ms | P99 ms |
|---|---:|---:|---:|
| presidio_ms | 7.910021 | 27.737010 | 42.386169 |
| nemo_input_ms | 665.630417 | 1458.341082 | 2710.365683 |
| input_guard_ms | 672.214105 | 1464.614036 | 2719.753307 |

Scope: `input_layers_sequential`; 20 timed samples, 2 warm-up thật bị loại.
Đo đủ Presidio rồi NeMo input, không short-circuit; engines được tạo trước đo.
Percentile linear, input_guard là tổng hai tầng theo từng sample.
Budget 500ms không đạt. Đây là số của batch lỗi, không đại diện bản sửa hiện tại.
RAG/output/full guard latency chưa đo; không suy ra chúng từ input_guard_ms.

## Lỗi và bản sửa

NeMo 0.10 tự chọn completions provider cho slug OpenRouter: đã truyền ChatOpenAI tường minh.
Self-check mặc định 3 tokens; diagnostic thật trả completion rỗng, NeMo chặn mặc định.
Đã đặt max_tokens=2048 cho input/output.
Bản sửa chưa có kiểm chứng model live vì quota đã hết.
Presidio giới hạn identifiers theo lab, tránh PERSON/LOCATION nhận nhầm tiếng Việt;
engine thật detect/redact 4/4 PII attacks và không phát hiện PII trong 8/8 clean inputs.

## Kiến nghị cho blueprint của Dương

Request: Presidio → NeMo input → RAG → NeMo output; dừng khi guard chặn.
Giữ secrets trong env; logs chỉ cần ids, quyết định, thời gian và model metadata, không log key.
Guard API lỗi/timeout hoặc self-check rỗng phải báo lỗi hoặc chặn; không tự cho allowed.
CI đề xuất: ≥18/20 attacks, 8/8 clean, 4/4 outputs; lab bắt buộc ≥15/20 kèm clean đạt.
Job đọc artifact dùng checker; job live tách lịch và hạn mức quota.
Theo dõi false positives, refusals, API 429/errors, P95 và model routing drift.
Blueprint/failure_clusters thuộc Dương; bản bàn giao này không sửa báo cáo của Dương.

## Việc còn cần API

Chạy lại C với 20 samples rồi validate quality. Budget C khoảng 50 self-check calls:
24 inputs qua NeMo (4 PII dừng ở Presidio) + 4 outputs + 22 lượt đo gồm warm-up.
B cần thêm 20 calls; quota 50/ngày không đủ chạy cả C và B trong cùng ngày.
Không bỏ warm-up/samples/clean controls để giảm calls. Không gửi thêm diagnostics live
trước batch C nếu muốn giữ đủ quota. Free provider có thể thay đổi hoặc trả lỗi giữa batch.
Quota lần lỗi trước thông báo reset 07:00 ngày 13/10/2026, giờ Việt Nam.
Sau khi có batch đạt, cập nhật handoff/TEAM và blueprint bằng artifact mới.
