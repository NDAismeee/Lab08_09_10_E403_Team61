# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Trần Long Hải
**Vai trò:** Embedding & Retrieval Evaluation Owner
**Ngày nộp:** 2026-04-15  
**Độ dài yêu cầu:** **400–650 từ**

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `eval_retrieval.py`
- `grading_run.py`
- artifacts/eval/before_after_eval.csv
- artifacts/eval/after_inject_bad.csv
- artifacts/eval/eval_after_fix.csv

**Kết nối với thành viên khác:**

Tôi phối hợp chặt với Member 2 và Member 3 để xác định phần dữ liệu cần inject xấu và chuẩn hoá trước khi đánh giá retrieval. Member 1 cung cấp pipeline ổn định để tôi chạy embed, còn Member 5 dùng kết quả tôi thu thập để bổ sung báo cáo chất lượng.

**Bằng chứng (commit / comment trong code):**

- Chạy `python eval_retrieval.py --out artifacts/eval/after_inject_bad.csv`
- So sánh với `artifacts/eval/eval_after_fix.csv`
- Dựa trên `artifacts/manifests/manifest_after-fix.json` và `manifest_inject-bad.json`

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Tôi chọn tập trung vào chiến lược **idempotent embedding** và **trước/sau retrieval** để chứng minh tác động của sprint 3. Cụ thể, tôi dùng `chunk_id` làm key lên ChromaDB, đảm bảo lênsert không tạo vector duplicate và prune vector cũ sau khi cleaned data thay đổi. Điều này giúp artifact `artifacts/eval/after_inject_bad.csv` phản ánh đúng lỗi dữ liệu sản phẩm, không phải vector cũ. Kết quả là khi chạy lại pipeline chuẩn, `artifacts/eval/eval_after_fix.csv` cho thấy `hits_forbidden` về 0 trong khi run inject xấu vẫn còn `hits_forbidden=yes` cho câu `q_refund_window`.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Triệu chứng: trong kịch bản inject xấu, tìm được câu trả lời refund vẫn xuất hiện `14 ngày` thay vì `7 ngày`, dẫn đến `hits_forbidden=yes` trên `q_refund_window`. Metric này phát hiện được ngay vì tôi giám sát cột `hits_forbidden` trong `artifacts/eval/after_inject_bad.csv`. Tôi xác định lỗi đến từ chế độ `--no-refund-fix --skip-validate` và dữ liệu cũ chưa bị prune khỏi ChromaDB, nên tôi sửa lại bằng cách buộc chạy pipeline chuẩn với sửa rule refund và kiểm tra idempotency. Fix xong, `artifacts/eval/eval_after_fix.csv` cho thấy `hits_forbidden=no` và `top1_doc_expected` được duy trì cho câu `q_leave_version`.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Run `after-fix` (`artifacts/manifests/manifest_after-fix.json`): `quarantine_records=4`, `cleaned_records=6`.  

`after_inject_bad.csv`:
- `q_refund_window` → `hits_forbidden=yes`, preview chứa `14 ngày`  
- `q_leave_version` → `top1_doc_expected=,` (vẫn giữ expected nhưng có forbidden)

`eval_after_fix.csv`:
- `q_refund_window` → `hits_forbidden=no`, preview sửa về `7 ngày`  
- `q_leave_version` → `top1_doc_expected=yes`

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ mở rộng `eval_retrieval.py` để ghi thêm cột `scenario` và so sánh trực tiếp với `grading_run.jsonl`, đồng thời thêm một query kiểm tra `gq_d10_03` để chứng minh cả retrieval và grading đều cải thiện sau clean. Điều này giúp báo cáo chất lượng rõ ràng hơn và dễ đối chiếu với SCORING.

