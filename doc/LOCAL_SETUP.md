# Môi trường local — 12/10/2026

Đã chuẩn bị trên macOS Apple Silicon, Python 3.11.9.

- `.venv`: full runtime theo requirements và constraints-core; `pip check` đạt.
- Import `ragas`, `nemoguardrails`, `presidio_analyzer`, `spacy` thành công.
- `en_core_web_lg==3.8.0`: tải và load thành công.
- Qdrant `v1.9.7`: Docker Compose đã chạy; `/healthz` đạt.
- `.env` đã có key OpenRouter hợp lệ; key không được in ra hoặc commit.

## Kích hoạt

```bash
source .venv/bin/activate
```

## Hai lỗi setup đã xử lý

Annoy không tìm thấy C++ header `cerrno`. Dùng headers từ macOS SDK và build
cho arm64. PyArrow 26 import lỗi vì yêu cầu NumPy 2 trong khi lab pin 1.26.4;
môi trường local dùng `pyarrow==17.0.0`, đã kiểm tra RAGAS import thành công.
Không sửa requirements/scaffold chung của nhóm.

Lệnh dựng lại full runtime trên máy này:

```bash
CPLUS_INCLUDE_PATH=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/c++/v1 ARCHFLAGS='-arch arm64' python -m pip install -r requirements/requirements.txt -c requirements/constraints-core.txt 'pyarrow==17.0.0'
python -m spacy download en_core_web_lg
python -m pip check
docker compose -f infra/docker-compose.yml up -d
```

## Trạng thái hiện tại

Main đã đồng bộ `eef8e49`: m1–m5 và 50 answers của Dương đã có;
answers validate schema/source đạt 20 factual, 20 multi_hop, 10 adversarial.
Không cần chạy lại setup/indexing để làm B/C.
B chưa chạy live; C có artifact thật nhưng chưa đạt. Quota OpenRouter đã hết.

## Tiến độ phần Ngô Minh Trí

Đã implement Tasks 5–8 trong `src/phase_b_judge.py` và Tasks 9a–12 trong
`src/phase_c_guard.py`.
Presidio engine thật detect/redact được 4/4 PII attacks và không phát hiện PII
trong 8/8 clean inputs. Phạm vi Presidio là VN_CCCD, VN_PHONE, EMAIL_ADDRESS,
PHONE_NUMBER: lọc các nhãn PERSON/LOCATION từ NER tiếng Anh nhận nhầm từ tiếng Việt.
NeMo config Colang 1.0 parse thành công với self-check input/output.
Đây là kiểm tra lớp Presidio/config, chưa chứng minh NeMo live đạt 20 attacks.

Phase C live không cần answers của Dương; sau khi quota reset chạy:

```bash
.venv/bin/python scripts/run_experiments.py --phase c --live --latency-samples 20
```

Phase B live cần `artifacts/answers_50q.json` từ Dương (đã kéo về từ main ở commit
`eef8e49`, validation đạt 50 câu với distribution 20/20/10). Chưa có dữ liệu judge live
để kết luận bias. Số đo C hiện tại thuộc batch lỗi, đã ghi trong guard_handoff.

## OpenRouter miễn phí cho B/C

Đã cấu hình endpoint `https://openrouter.ai/api/v1` và `openrouter/free` cho
judge và NeMo. Model cố định `openai/gpt-oss-120b:free` bị API từ chối với 404
(unavailable for free), nên dùng free router. Router có thể chọn model khác
nhau giữa các lượt; đây là giới hạn cần ghi trong báo cáo judge/guard. `config.py` đọc JUDGE_MODEL từ env;
NeMo khai model và base_url trong `guardrails/config.yml`.

Chỉ cần dán key OpenRouter vào dòng `OPENAI_API_KEY=` của `.env`. Tên biến này
được giữ để OpenAI SDK và LangChain cùng đọc key; không cần key OpenAI riêng.
`OPENAI_BASE_URL` phục vụ SDK; `OPENAI_API_BASE` phục vụ LangChain phiên bản cũ.
Không đưa key vào `.env.example`, Git hay chat. Key mới đã qua xác thực API.

Nguồn: [model miễn phí](https://openrouter.ai/openai/gpt-oss-120b:free),
[giới hạn free API](https://openrouter.ai/docs/api/reference/limits).
Nếu quota bị giới hạn, batch C có thể chưa hoàn tất; giữ số đo thật và kiểm tra
quota tài khoản trước khi chạy lại.

## Lần chạy live 12/10/2026

Đã chuyển key từ `.env.example` sang `.env` và làm sạch file mẫu trước khi chạy.
Runner Phase C khởi tạo được runtime nhưng OpenRouter trả HTTP 401:
`API key expired.` tại lời gọi NeMo self-check input đầu tiên. Batch dừng;
lần chạy với key cũ chưa tạo artifact. Key đã được thay ở lần sau.

Key mới đã qua xác thực. Đã sửa NeMo 0.10 dùng ChatOpenAI tường minh vì tên
model OpenRouter không được provider cũ nhận diện là chat. Batch free-router đầu
hoàn tất nhưng chặn nhầm 8/8 clean inputs. Diagnostic self-check trả completion
rỗng với budget mặc định 3 tokens; đã tăng max_tokens input/output lên 2048
và chạy lại. Bản batch đầu lưu tạm ở `/tmp/day24-guard-first-run.json`.

Lượt chạy lại với budget 2048 bị HTTP 429 `free-models-per-day`: quota 50/ngày,
remaining=0. Chưa kiểm chứng bản sửa token budget bằng API. Artifact hiện tại
là batch đầu chưa đạt: attacks 20/20, clean 0/8 (FPR=1), outputs 2/4,
input guard sequential P95=1464.614036ms, 20 samples, 2 warm-up.
Không coi attacks 20/20 này là đạt lab vì clean controls fail.

Đã đồng bộ main `eef8e49`: có m1–m5 và 50 answers từ Dương. Giữ cấu hình
model/Qdrant qua env của upstream và khôi phục thay đổi B/C local.

## Báo cáo và bước tiếp theo

Báo cáo B đã chuẩn bị phương pháp/nguồn/giới hạn, chưa có kết quả live.
`doc/reports/guard_handoff.md` chứa số đo C thật để Dương viết blueprint.
Checker toàn lab còn thiếu A/B artifacts, C quality chưa đạt, các mục TEAM
chung và báo cáo của Dương chưa điền. Không sửa phần sở hữu của Dương.

C dự kiến dùng khoảng 50 self-check calls; B dùng 20 calls. Với quota 50/ngày,
cần hai ngày quota riêng để chạy cả hai; không bỏ warm-up/clean/sample bắt buộc.
Quota lỗi lần trước ghi reset 07:00 ngày 13/10/2026 (giờ Việt Nam).
