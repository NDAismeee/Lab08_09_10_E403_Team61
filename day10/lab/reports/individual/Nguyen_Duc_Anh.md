# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Đức Anh - 2A202600146  
**Vai trò:** Cleaning / Quality Owner (Member 2)  
**Ngày nộp:** 2026-04-15  

---

## 1. Tôi phụ trách phần nào?

**File / module:**

- `day10/lab/transform/cleaning_rules.py`

Trong lab này tôi chịu trách nhiệm cải thiện lớp “cleaning” giữa ingestion và embedding để đảm bảo vector store chỉ chứa dữ liệu đúng version và đúng schema. Trọng tâm của tôi là xử lý các failure mode có thể làm retrieval “đúng bề ngoài nhưng sai ngữ cảnh”, đặc biệt là stale refund window và các ghi chú migration/legacy nằm lẫn trong nội dung chunk. Tôi cũng bổ sung kiểm tra/chuẩn hoá `exported_at` để tránh ảnh hưởng sai tới manifest và freshness monitoring.

**Kết nối với thành viên khác:**

- Tôi phối hợp với ETL owner để pipeline ghi log và xuất artifacts đúng run_id; phối hợp với evaluation owner để chứng minh before/after trên `eval_retrieval.py` và bộ câu hỏi trong `data/test_questions.json`.

**Bằng chứng (commit / comment trong code):**

- Thay đổi nằm trong `transform/cleaning_rules.py` (các rule `_strip_migration_notes`, `duplicate_after_canonicalization`, `_normalize_exported_at`) và các artifacts/log theo `run_id=mem2-cleaning-test`.

---

## 2. Một quyết định kỹ thuật

Tôi chọn chiến lược **sanitize + dedupe theo “canonical key” sau khi đã clean**, thay vì quarantine toàn bộ record có “migration note”. Lý do: nhiều chunk vẫn có “policy core” hữu ích (vd refund window), nhưng phần note kỹ thuật (policy-v3 / lỗi migration) làm tăng rủi ro `hits_forbidden` vì grading quét toàn bộ top-k context. Vì vậy tôi triển khai `_strip_migration_notes()` để cắt các đoạn trong ngoặc chứa marker `ghi chú`, `policy-v3`, `migration`, rồi mới áp dụng refund fix (14→7 nếu bật flag) và cuối cùng dedupe theo `_canonical_key()`. Quyết định này tạo tác động đo được: trên raw mẫu, 2 dòng refund giống nhau bị loại bằng `reason=duplicate_after_canonicalization`, và dòng refund stale được giữ nhưng đã sạch note và không còn “14 ngày làm việc”.

---

## 3. Một lỗi hoặc anomaly đã xử lý 

Anomaly lớn nhất tôi nhắm tới là **retrieval kéo về chunk refund có “14 ngày làm việc”** dù câu trả lời kỳ vọng là 7 ngày. Điều này xuất hiện rõ khi chạy inject scenario: `run_id=inject-bad` với `--no-refund-fix --skip-validate` khiến expectation `refund_no_stale_14d_window` fail (violations=1) nhưng vẫn embed để tạo “before” cho Sprint 3. Sau đó tôi chạy lại pipeline chuẩn (`run_id=after-fix`) để đảm bảo dataset publish không còn stale window. Ngoài ra, tôi thêm validate/normalize `exported_at` (ISO8601) để chặn timestamp bẩn lọt vào cleaned, vì `etl_pipeline.py` dùng `latest_exported_at` từ cleaned rows để ghi manifest và làm freshness check.

---

## 4. Bằng chứng trước / sau

Tôi dùng `data/test_questions.json` và `eval_retrieval.py` để tạo CSV evidence:

- **Before (inject)**: `artifacts/eval/eval_after_inject_bad.csv` cho thấy `q_refund_window` có `hits_forbidden=yes` và preview chứa “14 ngày làm việc”.
- **After (fixed publish)**: `artifacts/eval/eval_after_fix.csv` cho thấy `q_refund_window` chuyển sang `hits_forbidden=no` và preview chứa “7 ngày làm việc”.

Ngoài ra log `artifacts/logs/run_mem2-cleaning-test.log` xác nhận pipeline clean/expectation pass ở `run_id=mem2-cleaning-test` với `raw_records=10`, `cleaned_records=6`, `quarantine_records=4`.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ thêm một rule “doc_id content mismatch” (keyword-based per doc) kèm một file inject raw riêng để chứng minh metric impact rõ ràng (quarantine tăng khi cố tình gán sai nội dung cho `doc_id`). Tôi cũng sẽ đưa cutoff versioning (vd HR min effective date) đọc từ `contracts/data_contract.yaml` hoặc env để tránh hard-code, giúp đạt tiêu chí Distinction về versioning defense-in-depth.

