# Kế hoạch phân việc — Nhóm NoName

Mục tiêu: hai người làm **song song, độc lập**, chỉ đồng bộ ở các điểm bắt buộc
do dữ liệu (file artifact) chứ không do code của nhau.

| Thành viên | MSSV | Phụ trách chính |
|---|---|---|
| Nguyễn Thanh Dương (trưởng nhóm, tích hợp) | 2A202602961 | CP0 pipeline + answers, Phase A, Blueprint, nộp bài |
| Ngô Minh Trí | 2A202602993 | Phase B, Phase C |

## Vì sao chia như vậy

Phân tích phụ thuộc từ `src/experiment_runners.py`:

| Phần việc | Cần `answers_50q.json`? | Cần Qdrant/m1–m5? | Cần NeMo/Presidio? |
|---|---|---|---|
| CP0 + Phase A | Có (tự tạo) | Có (m4 cho RAGAS) | Không |
| Phase B — code Tasks 5–8 + unit tests | Không | Không | Không |
| Phase B — chạy live | **Có** (lấy answer A của ids 1,5,12,21,41) | Không | Không |
| Phase C — code + chạy live | Không | Không | Có |

- Phase C **hoàn toàn độc lập** với pipeline RAG.
- Phase B chỉ phụ thuộc ở bước chạy live cuối; toàn bộ code và test offline làm trước được.
- CP0 và Phase A cùng dùng pipeline/m4 nên gom về một người.
- Điểm: Dương 30đ + CP0 (nặng nhất về cài đặt) + Blueprint; Trí 35đ + 35đ.

## Quyền sở hữu file (tránh xung đột git)

Mỗi người **chỉ sửa file của mình**. Cần sửa file của người kia thì nhắn trước.

| File | Chủ sở hữu |
|---|---|
| `src/m1_chunking.py` … `src/m5_enrichment.py` | Dương |
| `src/phase_a_ragas.py` | Dương |
| `artifacts/answers_50q.json`, `artifacts/ragas_50q.json` | Dương |
| `doc/reports/failure_clusters.md` | Dương |
| `doc/reports/blueprint.md` | Dương (Trí gửi số liệu/nhận xét phần guard) |
| `src/phase_b_judge.py` | Trí |
| `artifacts/judge_results.json` | Trí |
| `doc/reports/bias_report.md` | Trí |
| `src/phase_c_guard.py` | Trí |
| `guardrails/config.yml`, `guardrails/rails.co` | Trí |
| `artifacts/guard_results.json` | Trí |
| `doc/TEAM.md` | Phần chung: Dương; mục INDIVIDUAL: mỗi người tự điền mục của mình |
| `config.py`, `requirements/`, `tests/`, `scripts/`, `src/experiment_*.py`, `src/report_contracts.py` | Không sửa (scaffold); cần sửa thì thống nhất trước |

## Việc của Nguyễn Thanh Dương

### D1 — Chuẩn bị môi trường và pipeline (CP0)

- [ ] Cài Python 3.11 + C++ Build Tools; tạo `.venv`, cài
      `requirements/requirements.txt -c requirements/constraints-core.txt`, chạy `pip check`.
- [ ] `docker compose -f infra/docker-compose.yml up -d` (Qdrant `v1.9.7`).
- [ ] Đưa m1–m5 từ bài RAG trước vào `src/`, đối chiếu đúng bảng giao diện trong
      `doc/PIPELINE_INTERFACE.md` (viết adapter nếu tên/kiểu trả về khác).
- [ ] m4 phải trả `metadata.evaluator_models` (model LLM + embedding thực dùng).
- [ ] Chạy `python scripts/setup_answers.py --live` → `artifacts/answers_50q.json`
      (50 câu, 20/20/10, có `generation_mode`/`generation_model`).
- [ ] **Commit + push `answers_50q.json` sớm nhất có thể** → mốc đồng bộ M1.

### D2 — Phase A (Tasks 1–4)

- [ ] Implement `group_by_distribution`, `run_ragas_50q`, `bottom_10`, `cluster_analysis`.
- [ ] `python -m pytest tests/test_phase_a.py -q` pass.
- [ ] `python scripts/run_experiments.py --phase a --live` → `artifacts/ragas_50q.json`.
- [ ] Điền `doc/reports/failure_clusters.md` (đọc question/answer/contexts các câu yếu).
- [ ] Bonus +4: so adversarial mean với factual mean, phân tích bẫy phiên bản policy.

### D3 — Tích hợp và nộp (sau mốc M2)

- [ ] Điền `doc/reports/blueprint.md` từ 3 artifacts.
- [ ] Điền phần chung `doc/TEAM.md` (môi trường, phân công, bằng chứng).
- [ ] `python scripts/check_lab.py --with-tests`, kiểm tra secrets, push, ghi commit SHA.

## Việc của Ngô Minh Trí

### T1 — Môi trường riêng

- [ ] Python 3.11 + C++ Build Tools (Annoy/NeMo); cài full runtime như trên.
- [ ] `python -m spacy download en_core_web_lg` (Presidio cần).
- [ ] `.env` có `OPENAI_API_KEY` riêng. **Không cần** Qdrant, BGE-M3 hay m1–m5.

### T2 — Phase C (Tasks 9a–12) — làm trước vì không phụ thuộc ai

- [ ] Implement `pii_scan`, `check_input_rail`, `run_adversarial_suite`,
      `check_output_rail`, `measure_p95_latency`.
- [ ] Quyết định block đọc từ `result.log.activated_rails`, không dò từ khóa refusal.
- [ ] `python -m pytest tests/test_phase_c.py -q` pass.
- [ ] `python scripts/run_experiments.py --phase c --live --latency-samples 20`
      → `artifacts/guard_results.json`.
- [ ] Đạt ≥15/20 attacks và 8/8 clean allowed; nếu chặn nhầm, chỉnh
      `guardrails/config.yml` rồi chạy lại. Bonus +3: ≥18/20 kèm 8/8 clean.
- [ ] Gửi Dương số liệu latency/attacks/false-positive cho blueprint.

### T3 — Phase B (Tasks 5–8)

- [ ] Implement `pairwise_judge`, `swap_and_average`, `cohen_kappa`, `bias_report`
      — làm và test offline **ngay**, không cần chờ answers.
- [ ] `python -m pytest tests/test_phase_b.py -q` pass.
- [ ] Sau mốc M1 (`git pull` lấy `answers_50q.json`):
      `python scripts/run_experiments.py --phase b --live` → `artifacts/judge_results.json`.
- [ ] Điền `doc/reports/bias_report.md`. Bonus +3 nếu κ > 0.6 (không chỉnh prompt
      dựa trên human_label).

### T4 — Khai báo

- [ ] Điền mục INDIVIDUAL của mình trong `doc/TEAM.md`.

## Mốc đồng bộ (chỉ 3 điểm)

| Mốc | Ai giao → ai nhận | Nội dung | Mở khóa |
|---|---|---|---|
| M1 | Dương → Trí | `artifacts/answers_50q.json` đã push | Trí chạy Phase B live |
| M2 | Trí → Dương | `judge_results.json`, `guard_results.json`, `bias_report.md` đã push | Dương điền blueprint |
| M3 | Cả hai | INDIVIDUAL đã điền, `check_lab.py` sạch | Dương nộp link + commit SHA |

Nếu M1 trễ: Trí làm hết Phase C và code/test Phase B trước, không bị chặn.

## Quy ước làm việc

- Cả hai commit và push **trực tiếp lên `main`**, không dùng branch riêng.
  Mỗi commit chỉ chứa file của mình; luôn `git pull --rebase` trước khi push.
  Commit nhỏ, push thường xuyên để giảm xung đột.
- Không commit `.env`, `.venv`, cache model.
- Lệnh `--live` có chi phí API: mỗi phase chỉ chạy lại khi thực sự cần; không chạy
  thêm `pytest -m integration --run-live` sau khi đã có artifacts.
- Không tự điền số đo/nhãn; mọi số trong report lấy từ artifacts thật.
- Deadline: `TEAM.md` ghi 16:00 12/10/2026, README ghi 11:59 13/10/2026,
  ASSIGNMENT ghi 23:59 ngày lab — trưởng nhóm xác nhận với coach.
