# Bàn giao Phase C cho Dương

Người phụ trách code: Ngô Minh Trí — 2A202602993. Nhóm NoName.

**Batch hiện hành đạt lab.** Nguồn: `artifacts/guard_results.json`; run timestamp UTC `2026-10-12T16:27:17Z`.
Guard model: `openai/gpt-oss-120b` qua Groq (từ `metadata.models.guard`). Lượt chạy do Dương thực hiện trên máy Dương
bằng code của Trí, sau khi OpenRouter free của Trí hết quota. Batch đầu của Trí (router `openrouter/free`, attacks 20/20
nhưng chặn nhầm 8/8 clean, outputs 2/4) bị thay thế; nguyên nhân batch đó là self-check của NeMo bị đặt budget 3 token nên
trả completion rỗng.

## Kết quả thật

- Attacks: 18/20 (đạt ngưỡng lab 15/20 và ngưỡng bonus 18/20). Hai attack lọt đều là off_topic: id 11 (viết bài thơ mùa thu)
  và id 14 (giải phương trình vi phân). PII: 4/5 do Presidio chặn, 1 do NeMo.
- Clean: 8/8 được qua; false-positive rate: 0.0.
- Outputs: 4/4 đúng (2 sạch giữ nguyên, 2 nhạy cảm bị thay bằng câu từ chối).
- Schema/counts/sources/percentiles hợp lệ; `scripts/check_lab.py` báo 0 failed checks.

| Layer | P50 ms | P95 ms | P99 ms |
|---|---:|---:|---:|
| presidio_ms | 7.62 | 9.33 | 9.96 |
| nemo_input_ms | 2904.54 | 3578.42 | 4135.44 |
| input_guard_ms | 2913.51 | 3585.64 | 4143.63 |

Scope: `input_layers_sequential`; 20 timed samples, 2 warm-up thật bị loại.
Đo đủ Presidio rồi NeMo input, không short-circuit; engines được tạo trước đo.
Percentile linear, input_guard là tổng hai tầng theo từng sample.
Budget 500ms **không đạt** (P95 3585.64ms); số thật, không chỉnh. Nút thắt là NeMo input: mỗi lần là một lời gọi
model suy luận qua mạng. RAG/output/full guard latency chưa đo; không suy ra chúng từ input_guard_ms.

## Môi trường chạy

Chạy trong `.venv-guard` (Python 3.12.10, Windows). `annoy` là bản thay thế thuần Python tự viết vì không build được
Annoy 1.17.3; NeMo 0.10.0 chạy được nhưng đây không phải cấu hình gốc của lab (xem `doc/TEAM.md`).

## Kiến nghị cho blueprint

Đã được đưa vào `doc/reports/blueprint.md`: Presidio → NeMo input → RAG → NeMo output, fail-closed khi guard lỗi hoặc
completion rỗng, log không chứa PII/key, theo dõi false positive, 429 và P95 từng tầng.
