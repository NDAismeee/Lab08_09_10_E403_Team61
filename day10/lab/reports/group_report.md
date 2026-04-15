# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** 61  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Do Minh Hieu | ETL & Pipeline Owner | dohieunt1102@gmail.com |
| Nguyen Duc Anh | Cleaning Rules Owner | ndaismeee@gmail.com |
| Khuong Quang Vinh | Expectations & Quality Owner | vinhkhuongquang@gmail.com |
| Tran Long Hải | Embed & Eval Owner | longhai7803@gmail.com |
| Nguyễn Tiến Dũng | Monitoring & Docs Owner | dungnguyentien138@gmail.com |

**Ngày nộp:** 15/04/2026  
**Repo:** https://github.com/NDAismeee/Lab08_09_10_E403_Team61  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

Nguồn dữ liệu raw của nhóm là file `policy_export_dirty.csv` chứa các bản ghi xuất từ hệ thống cũ, bao gồm nhiều lỗi về định dạng ngày tháng, trùng lặp và các chính sách lỗi thời (stale policy). Pipeline được thiết kế để xử lý dữ liệu theo lô (batch) với cơ chế bảo vệ đa lớp.

**Tóm tắt luồng:**
1. **Ingest**: Đọc dữ liệu CSV và gán `run_id` (timestamp ISO) để theo dõi dấu vết.
2. **Transform (Cleaning)**: Áp dụng các hàm regex và chuẩn hóa để loại bỏ migration notes và sửa lỗi refund window.
3. **Quality (Expectations)**: Kiểm tra dữ liệu sau khi clean bằng bộ 10 quy tắc (E1-E10). Nếu vi phạm mức `halt`, pipeline sẽ dừng ngay lập tức.
4. **Load (Embed)**: Thực hiện Upsert vào ChromaDB sử dụng MD5 hash làm `chunk_id` để đảm bảo tính Idempotency.
5. **Monitor**: Xuất file manifest.json và kiểm tra Freshness SLA (24h).

**Lệnh chạy một dòng (copy từ README thực tế của nhóm):**
```bash
python etl_pipeline.py run --run-id 2026-04-15T08-27Z
```

---

## 2. Cleaning & expectation (150–200 từ)

Nhóm đã mở rộng hệ thống với 3 rule mới: `_strip_migration_notes` (xóa ghi chú kỹ thuật), `duplicate_after_canonicalization` (xử lý trùng lặp sau chuẩn hóa), và `_normalize_exported_at` (ép kiểu ISO8601).

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| `refund_no_stale_14d_window` | violations=0 | violations=1 (Halt) | `run_id=inject-bad` log |
| `doc_id_in_allowlist` | embed noise | quarantine_records=4 | `artifacts/quarantine/` |
| `chunk_text_not_empty` | valid=10 | valid=6, quarantine=4 | `manifest_after-fix.json` |

**Rule chính (baseline + mở rộng):**
- `apply_refund_window_fix`: Chuyển 14 ngày về 7 ngày cho `policy_refund_v4`.
- `E7 doc_id_in_allowlist`: Chặn các document ID lạ không thuộc phạm vi CS/IT.
- `E9 no_conflicting_version`: Chặn việc nạp 2 phiên bản chính sách có ngày hiệu lực khác nhau.

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**
Trong lần chạy `inject-bad`, expectation E3 (refund stale) báo lỗi `halt`. Nhóm đã xử lý bằng cách kiểm tra file Quarantine, phát hiện dòng dữ liệu chứa "14 ngày làm việc", sau đó kích hoạt lại rule `apply_refund_window_fix` trong code và rerun pipeline.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

Nhóm thực hiện kịch bản inject corruption bằng cách giữ nguyên thông tin hoàn tiền 14 ngày (phiên bản cũ) vào database.

**Kịch bản inject:** 
Sử dụng flag `--no-refund-fix --skip-validate` để ép dữ liệu bẩn vào ChromaDB. Điều này mô phỏng lỗi dữ liệu nguồn chưa được làm sạch lọt vào production.

**Kết quả định lượng (từ CSV / bảng):**
Dựa trên `artifacts/eval/after_inject_bad.csv`:
- Câu hỏi `q_refund_window` có `hits_forbidden=yes`. Agent tìm thấy chunk chứa "14 ngày" và trả lời sai cho khách hàng.
- Sau khi chạy `after-fix.csv`, `hits_forbidden` chuyển về `no`. `top1_preview` hiển thị đúng "7 ngày làm việc". Điều này chứng minh pipeline đã bảo vệ Agent khỏi việc đưa ra thông tin sai lệch.

---

## 4. Freshness & monitoring (100–150 từ)

Nhóm thiết lập SLA Freshness là **24 giờ**. Trong manifest mẫu, trạng thái hiện tại là `FAIL` vì dữ liệu nguồn export từ ngày 10/04/2026, trong khi ngày chạy là 15/04/2026 (trễ 120h). 
- **PASS**: Dữ liệu < 24h.
- **WARN**: Dữ liệu > 24h nhưng < 48h (Agent vẫn chạy nhưng cần thông báo).
- **FAIL**: Dữ liệu quá cũ, vi phạm Data Contract, cần trigger Runbook để cập nhật nguồn raw.

---

## 5. Liên hệ Day 09 (50–100 từ)

Dữ liệu sau khi qua pipeline này được nạp trực tiếp vào collection `day10_kb`. Hệ thống Multi-Agent từ Day 09 (đặc biệt là `retrieval_worker` của Vinh và `policy_tool` của Dũng) sẽ chuyển sang sử dụng collection này. Việc tích hợp này giúp Agent ở Day 09 đạt điểm Faithfulness cao hơn vì không còn bị nhiễu bởi migration notes hay stale refund window.

---

## 6. Rủi ro còn lại & việc chưa làm

- **Freshness Monitoring**: Chưa tự động gửi thông báo (Slack/Email) khi Freshness FAIL.
- **Schema Evolution**: Pipeline chưa xử lý tốt nếu file CSV thay đổi cấu trúc cột (thêm/bớt cột).
- **Pruning Logic**: Cần kiểm tra kỹ hơn trường hợp xóa nhầm dữ liệu khi có 2 `doc_id` khác nhau nhưng nội dung chunk giống hệt nhau (MD5 collision).
