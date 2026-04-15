# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

> User / agent thấy gì? (VD: trả lời “14 ngày” thay vì 7 ngày)

> User hoặc Agent phản hồi thông tin lỗi thời (Ví dụ: "Hoàn tiền trong 14 ngày" trong khi quy định mới là 7 ngày).
---

## Detection

> Metric nào báo? (freshness, expectation fail, eval `hits_forbidden`)

> Hệ thống báo freshness `FAIL` hoặc kết quả eval có `hits_forbidden=yes`.
---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Xem log chạy gần nhất | Tìm `run_id` bị báo lỗi `HALT`. |
| 2 | Kiểm tra `artifacts/manifests/*.json` | Xem expectation nào fail (ví dụ: `doc_id_in_allowlist`). |
| 3 | Mở `artifacts/quarantine/*.csv` | Xác định chính xác dòng dữ liệu nào gây ra lỗi. |
| 4 | Chạy `python eval_retrieval.py` | Xác định xem `hits_forbidden` có bằng `True` cho câu hỏi Refund không. |

---

## Mitigation

> Rerun pipeline, rollback embed, tạm banner “data stale”, …

1. Rerun pipeline với tham số `--run-id fix_manual`.
2. Nếu vẫn fail, rollback collection về snapshot gần nhất trong `chroma_db` (nếu có backup).
3. Tạm thời thông báo hệ thống đang bảo trì dữ liệu.
---

## Prevention

> Thêm expectation, alert, owner — nối sang Day 11 nếu có guardrail.

Thêm expectation kiểm tra chặt chẽ keyword "14 ngày" trong `quality/expectations.py` và set chế độ `HALT` nếu phát hiện dữ liệu cũ lọt vào.
