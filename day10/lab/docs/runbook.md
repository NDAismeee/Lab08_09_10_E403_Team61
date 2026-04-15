# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

> User / agent thấy gì? (VD: trả lời “14 ngày” thay vì 7 ngày)

User hoặc Agent phản hồi thông tin lỗi thời (Ví dụ: "Hoàn tiền trong 14 ngày" trong khi quy định mới là 7 ngày).

---

## Detection

> Metric nào báo? (freshness, expectation fail, eval `hits_forbidden`)

Hệ thống báo freshness `FAIL`, expectation `HALT`, hoặc kết quả eval có `hits_forbidden=yes`.

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Xem log chạy gần nhất trong `artifacts/logs/` | Tìm `run_id` và điểm fail (`HALT` hay freshness). |
| 2 | Kiểm tra `artifacts/manifests/manifest_<run-id>.json` | Xác nhận `raw/cleaned/quarantine` và cờ `skipped_validate`. |
| 3 | Mở `artifacts/quarantine/quarantine_<run-id>.csv` | Xác định record bị cách ly và nguyên nhân. |
| 4 | Chạy `python eval_retrieval.py --out artifacts/eval/clean_run_eval.csv` | Xác định `hits_forbidden` cho `q_refund_window` và `top1_doc_expected` cho `q_leave_version`. |

---

## Mitigation

> Rerun pipeline, rollback embed, tạm banner “data stale”, …

1. Nếu fail do dữ liệu stale/refund rule: chạy lại chuẩn
	- `python etl_pipeline.py run --run-id after-fix`
2. Nếu cần tái hiện lỗi để debug: chạy inject có kiểm soát
	- `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`
3. Đánh giá lại retrieval sau mỗi run
	- `python eval_retrieval.py --out artifacts/eval/eval_after_fix.csv`
4. Chỉ publish khi expectation không halt và `hits_forbidden=no` cho câu refund.
---

## Prevention

> Thêm expectation, alert, owner — nối sang Day 11 nếu có guardrail.

Thêm expectation kiểm tra keyword "14 ngày" ở luồng refund và giữ mức `HALT` khi phát hiện dữ liệu stale lọt vào cleaned output. Đồng thời chạy freshness check sau mỗi lần publish để chặn pipeline khi dữ liệu nguồn quá SLA 24 giờ.
