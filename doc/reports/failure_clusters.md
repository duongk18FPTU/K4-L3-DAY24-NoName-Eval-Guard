# Phân tích lỗi Phase A

Nhóm: NoName

Người phụ trách: Nguyễn Thanh Dương - 2A202602961

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T16:13:47+00:00.
Generation mode/fallback và điều kiện chạy: cả 50 answers có `generation_mode=llm`
(không có extractive fallback), sinh bằng `scripts/setup_answers.py --live` qua endpoint
tương thích OpenAI của Groq. Retrieval: hybrid BM25 + BGE-M3 (Qdrant v1.9.7) → rerank
`BAAI/bge-reranker-v2-m3` → top 3 contexts. Corpus có 26 tài liệu; 2 PDF scan
(`BCTC.pdf`, Nghị định 13) không có lớp chữ nên không được index (không câu hỏi nào dùng tới).
Models generation/evaluator: generation = `openai/gpt-oss-20b`; evaluator =
`gemini-3.5-flash-lite` (39 câu), `gemini-3.1-flash-lite` (11 câu), embedding `BAAI/bge-m3` (chạy local).

Lưu ý về evaluator: Gemini free tier có hạn mức theo ngày và theo phút nên lượt chấm được
chia nhiều lần và lưu cache theo từng câu (`.ragas_cache/`, không commit). Câu 17 và 31 luôn
cho `faithfulness=NaN` với `gemini-3.5-flash-lite` (RAGAS báo "No statements were generated
from the answer"), nên được chấm lại bằng `gemini-3.1-flash-lite`. Không có điểm nào được điền
thay; nhưng 11 câu được chấm bởi model khác nên các điểm này không hoàn toàn đồng nhất giữa
các câu. Phiên bản RAGAS 0.1.22; metric `answer_relevancy` có lấy mẫu ngẫu nhiên nên chạy lại
có thể lệch nhẹ.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 0.950 | 0.633 | 0.925 |
| answer_relevancy | 0.890 | 0.539 | 0.878 |
| context_precision | 0.925 | 0.483 | 0.900 |
| context_recall | 0.925 | 0.696 | 0.675 |
| avg_score | 0.922 | 0.588 | 0.844 |

## Bottom 10 và nguyên nhân

| Rank | ID | Distribution | avg_score | worst_metric | diagnosis (Task 3) | suggested_fix (Task 3) |
|---|---|---|---|---|---|---|
| 1 | 30 | multi_hop | 0.125 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 2 | 33 | multi_hop | 0.125 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 3 | 39 | multi_hop | 0.25 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 4 | 29 | multi_hop | 0.375 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 5 | 8 | factual | 0.375 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 6 | 21 | multi_hop | 0.375 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 7 | 37 | multi_hop | 0.4723 | context_precision | Too many irrelevant chunks | Add reranking or metadata filter |
| 8 | 23 | multi_hop | 0.5 | faithfulness | LLM hallucinating | Tighten system prompt, lower temperature |
| 9 | 26 | multi_hop | 0.5 | answer_relevancy | Answer doesn't match question | Improve prompt template |
| 10 | 35 | multi_hop | 0.5039 | context_precision | Too many irrelevant chunks | Add reranking or metadata filter |

Cột diagnosis/suggested_fix là nhãn mặc định theo `DIAGNOSTIC_TREE` (map từ worst_metric), chưa
phải kết luận nguyên nhân. Đối chiếu answer/contexts/reference cho thấy nguyên nhân thực khác
nhãn này ở phần lớn các câu:

- **8/10 câu bottom 10 có answer đúng là "Không tìm thấy."** (ID 30, 33, 39, 29, 8, 21, 23, 26).
  Đây là lỗi *từ chối trả lời*, không phải "hallucinating": faithfulness thấp (0.0) chỉ vì câu
  "Không tìm thấy." không chứa mệnh đề nào được context hỗ trợ. Toàn bộ 50 answers có 8 câu từ chối
  như vậy (7 multi_hop, 1 factual).
- **Nguyên nhân chính nằm ở bước chunking (m1), không phải prompt.** Bộ tách câu của `m1_chunking`
  cắt sau dấu `:`/`;`, làm đứt các mục danh sách. Ví dụ ID 26 và ID 8: tài liệu gốc ghi
  `- **Tang lễ** (cha mẹ, vợ/chồng, con): 3 ngày làm việc`, nhưng context số 1 kết thúc ở
  `...con):` còn số "3 ngày làm việc" nằm ở chunk khác (context số 2 bắt đầu bằng
  `3 ngày làm việc - **Sinh con**...`). Sau rerank, mệnh đề "cha mẹ mất → 3 ngày" không còn nằm
  trọn trong top 3, nên LLM trả lời "Không tìm thấy". Hậu quả thấy trong số liệu:
  context_recall của 6/8 câu từ chối chỉ 0.0–0.67.
- **Hai câu từ chối dù context_recall cao (ID 23 và 26, recall = 1.0)** là lỗi generation/suy luận
  nhiều bước: thông tin có trong top 3 nhưng nằm rải rác nhiều chunk (hoặc đã bị cắt như trên) và
  model `gpt-oss-20b` với prompt "CHỈ dựa trên context" chọn từ chối thay vì tổng hợp/tính toán
  (ví dụ ID 26 cần cộng 3 + 1 ngày; ID 23 cần so sánh 8 tháng với cam kết 1 năm).
- **ID 39** (so sánh mật khẩu v1.0 và v2.0): top 3 chỉ có 2 chunk của v2.0 và một chunk "Lưu ý" của
  v1.0 (chỉ nói bản cũ đã bị thay thế); chunk chứa yêu cầu cũ (8 ký tự, 90 ngày) không được lấy
  nên context_recall = 0.0. Đây là lỗi retrieval cho câu hỏi cần *hai* phiên bản cùng lúc với
  `top_k=3`.
- **ID 37 và 35 (context_precision = 0.0)** không phải từ chối: answer có nội dung nhưng thiếu ý.
  ID 37 cần *hai* chính sách (xử lý sự cố bảo mật và phân loại dữ liệu); cả 3 context đều thuộc tài
  liệu sự cố bảo mật, không có chunk của chính sách phân loại dữ liệu nên answer chỉ nêu một
  chính sách. ID 35 cần bảng lương, chính sách thử việc và chính sách phụ cấp: 3 context gồm chính
  sách thử việc, khung lương và lương thử việc (đủ ý 85% và phụ cấp ăn trưa) nhưng không có chunk
  phụ cấp điện thoại, nên answer thiếu ý "Junior không có phụ cấp điện thoại" và không tính tổng
  11.200.000 VNĐ. Điểm context_precision = 0.0 của hai câu này do RAGAS đánh giá các context top đầu
  không hỗ trợ trực tiếp reference đầy đủ; đây là giới hạn của 1 lượt chấm bằng LLM nên cần đọc
  thủ công thay vì tin hoàn toàn vào con số. Hướng sửa chung: tăng `top_k` và retrieve riêng theo
  từng ý/tài liệu của câu hỏi nhiều bước.

## Matrix và nhóm yếu nhất

Mỗi câu được đếm theo worst_metric của chính câu đó (tổng mỗi cột = 20/20/10, không phải số lỗi).

| worst_metric | factual | multi_hop | adversarial |
|---|---|---|---|
| faithfulness | 1 | 7 | 1 |
| answer_relevancy | 16 | 5 | 2 |
| context_precision | 1 | 5 | 1 |
| context_recall | 2 | 3 | 6 |

Nhóm yếu theo mean thấp nhất: **multi_hop**; mean: **0.588** (factual 0.922, adversarial 0.844).
Worst metric xuất hiện nhiều nhất: **answer_relevancy**; số câu: **23** (16 + 5 + 2). Với factual,
16/20 câu có answer_relevancy là metric thấp nhất, nhưng mean factual vẫn là 0.89 nên đây chỉ là
metric thấp nhất *tương đối* trong một nhóm điểm cao, không phải lỗi nghiêm trọng.

multi_hop yếu vì câu hỏi cần tổng hợp nhiều chunk (phép cộng ngày nghỉ, so sánh hai phiên bản,
chính sách + bảng lương), trong khi pipeline chỉ giữ 3 chunk 256 ký tự và các chunk còn bị cắt
giữa danh sách. Đề xuất sửa, theo thứ tự ưu tiên:

1. **Sửa `_split_sentences` trong m1**: không cắt sau `:`/`;`, giữ nguyên mỗi mục `- ...` của danh
   sách trong cùng một chunk; có thể trả về parent chunk (2048 ký tự) cho LLM thay vì child 256.
2. Tăng `RERANK_TOP_K` từ 3 lên 5 và, với câu hỏi so sánh phiên bản, truy xuất riêng theo từng
   `doc_id` (v1.0 và v2.0).
3. Nới prompt sinh answer: cho phép tính toán/tổng hợp từ nhiều đoạn context, chỉ trả "Không tìm
   thấy" khi thật sự thiếu thông tin.

Cách kiểm chứng: index lại, chạy `scripts/setup_answers.py --live` và Phase A rồi so số câu từ chối
(hiện 8/50), mean multi_hop (hiện 0.588) và context_recall. Chưa thực hiện lượt chạy lại này trong bài nộp.

## Bẫy adversarial và giới hạn

Mean adversarial (0.844) **thấp hơn** factual (0.922) nhưng cao hơn multi_hop rất nhiều (0.588).
Điểm thấp nhất của nhóm này là context_recall (0.675; 6/10 câu có worst_metric = context_recall),
phù hợp với việc câu hỏi version-conflict cần lấy đúng chunk của phiên bản hiện hành trong khi
corpus giữ cả bản cũ. Với các câu 41, 42, 43, 44, 45, 49, 50, top 3 contexts chứa cả chunk của
phiên bản cũ lẫn mới. Đọc answers: ID 41 trả đúng "15 ngày phép năm" (v2024); ID 43 trả đúng 12 ký
tự; ID 44 đúng 120 ngày; ngược lại ID 49 trả lời theo "chính sách nghỉ phép cũ (v2023)" và ID 42 nêu
cả hai phiên bản, tức pipeline **không phải lúc nào cũng nhận ra** bản hiện hành. Điểm thấp hơn
factual chỉ cho thấy nhóm này khó hơn, không chứng minh pipeline xử lý được version conflict.

Giới hạn: chỉ 50 câu (10 adversarial) nên mean mỗi nhóm dao động mạnh khi đổi 1–2 câu; evaluator là
hai model Gemini bản flash-lite (không phải GPT-4 như RAGAS thường dùng) nên điểm tuyệt đối chỉ có
giá trị so sánh tương đối; 50 answers do `gpt-oss-20b` sinh một lần, không lặp lại để đo độ biến
thiên; 2 PDF scan không được OCR.
