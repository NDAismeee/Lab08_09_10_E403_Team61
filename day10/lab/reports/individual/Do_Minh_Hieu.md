# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Do Minh Hieu  
**Vai trò:** ETL & Pipeline Owner  
**Ngày nộp:** 2026-04-15

## 1. Tôi phụ trách phần nào?

Trong Day 10, tôi phụ trách ETL pipeline đầu-cuối: ingest dữ liệu raw, điều phối clean/validate/embed theo đúng thứ tự, và chốt artifact cho từng run. File tôi tập trung chính là `etl_pipeline.py`, kèm đối soát output trong `artifacts/manifests/`, `artifacts/cleaned/`, `artifacts/quarantine/` và `artifacts/eval/`. Tôi kiểm tra output tối thiểu theo rubric: có `run_id`, `raw_records`, `cleaned_records`, `quarantine_records`, và đường dẫn cleaned/quarantine CSV. Ở run `sprint1`, manifest ghi: `raw_records=10`, `cleaned_records=6`, `quarantine_records=4`, `latest_exported_at=2026-04-10T08:00:00`.

Về phối hợp nhóm, tôi nhận kết quả từ bạn phụ trách Cleaning/Quality và Embed rồi tích hợp vào luồng chạy chung, đảm bảo mỗi lần rerun đều cho ra artifact nhất quán để đối chiếu trước/sau. Bằng chứng tôi dùng là cặp file eval trước/sau fix và manifest theo run.

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật quan trọng nhất tôi chọn là giữ freshness ở mức `halt` theo SLA 24 giờ trong data contract, thay vì hạ thành `warn` để dễ qua bài. Lý do là Day 10 tập trung observability: pipeline không chỉ cần chạy thành công mà còn phải cho biết dữ liệu có còn đủ mới để agent sử dụng hay không.

Trong vai trò Pipeline Owner, tôi giữ `freshness.sla_hours: 24` để runner không publish dữ liệu stale. Tôi cũng thống nhất cách đọc freshness từ manifest (`latest_exported_at`) để khi fail có thể truy nguồn ngay từ artifact.

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly lớn nhất tôi xử lý là tình huống retrieval dính “stale policy” ở câu hỏi hoàn tiền. Triệu chứng xuất hiện rõ trong file `artifacts/eval/eval_after_inject_bad.csv`: với `q_refund_window`, hệ thống vẫn `contains_expected=yes` nhưng đồng thời `hits_forbidden=yes`, và `top1_preview` chứa “14 ngày làm việc”. Điều này cho thấy top-k context còn nhiễm chunk cũ dù câu trả lời nhìn qua có vẻ hợp lý.

Tín hiệu phát hiện đến từ việc kết hợp `hits_forbidden` + so sánh preview text + kiểm tra rule refund trong cleaning. Sau khi nhóm áp dụng lại đường clean chuẩn (không inject-bad), kết quả ở `artifacts/eval/eval_after_fix.csv` đổi đúng mong đợi: `q_refund_window` chuyển thành `hits_forbidden=no`, preview còn “7 ngày làm việc”.

## 4. Bằng chứng trước / sau

Bằng chứng before/after tôi chốt như sau:

- Trước fix (`artifacts/eval/eval_after_inject_bad.csv`):
  - `q_refund_window,...,contains_expected=yes,hits_forbidden=yes,...`
  - `top1_preview`: “... trong vòng 14 ngày làm việc ...”

- Sau fix (`artifacts/eval/eval_after_fix.csv`):
  - `q_refund_window,...,contains_expected=yes,hits_forbidden=no,...`
  - `top1_preview`: “... trong vòng 7 ngày làm việc ...”

Ngoài ra, ở run `sprint1` trong `artifacts/manifests/manifest_sprint1.json`, số liệu `10 -> 6 + 4` (raw/cleaned/quarantine) cho thấy pipeline đã phân luồng record rõ ràng trước khi publish.

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ thêm một bước kiểm tra “freshness theo doc_id” thay vì chỉ một timestamp tổng, để phát hiện trường hợp một phần nguồn mới còn phần khác stale. Kết quả sẽ được ghi thẳng vào manifest theo từng `doc_id` và thêm cảnh báo phân cấp (WARN/FAIL) để nhóm quyết định có publish toàn bộ hay publish có điều kiện.