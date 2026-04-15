# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Tiến Dũng
**Vai trò:** Monitoring — Kiểm tra freshness, theo dõi điền 3 docs
**Ngày nộp:** 15/04/2026  
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (115 từ)

Trong Lab Day 10, tôi đảm nhận vai trò **Monitoring / Docs Owner**. Trách nhiệm chính của tôi bao gồm thiết lập hạ tầng giám sát dữ liệu và quản lý bộ tài liệu vận hành. Tôi trực tiếp quản lý module `monitoring/freshness_check.py` để đảm bảo SLA về độ tươi của dữ liệu và xây dựng 3 tài liệu quan trọng: `pipeline_architecture.md`, `data_contract.md`, và `runbook.md`. 

Tôi đóng vai trò là điểm kết nối cuối cùng trong pipeline; tôi nhận `run_id` và manifest từ **Member 1 (Pipeline)**, đối chiếu kết quả validation từ **Member 3 (Quality)** và kiểm tra hiệu quả retrieval từ **Member 4 (Embed)** để hoàn thiện file `quality_report.md`. 

Bằng chứng đóng góp của tôi thể hiện rõ qua các file cấu hình SLA trong `.env` và nội dung chi tiết trong thư mục `docs/`.

---

## 2. Một quyết định kỹ thuật (145 từ)

Một quyết định kỹ thuật quan trọng tôi đã thực hiện là thiết lập **SLA Freshness ở mức 24 giờ** và phân loại mức độ nghiêm trọng cho **Expectation E10 (exported_at ISO format)** là `warn` thay vì `halt`. 

Về SLA 24h, do hệ thống CS và IT Helpdesk thường xuyên cập nhật chính sách (như việc đổi từ 14 ngày xuống 7 ngày hoàn tiền), việc sử dụng dữ liệu cũ hơn 1 ngày sẽ trực tiếp gây ra sai sót trong tư vấn của Agent. 

Về E10, tôi quyết định chỉ để mức `warn` vì nếu định dạng ngày xuất bản bị sai lệch nhỏ (ví dụ thiếu phần giây), nó sẽ khiến module freshness không thể tính toán được độ tuổi dữ liệu (Age Hours), dẫn đến trạng thái `FAIL` trên monitor. Tuy nhiên, lỗi format này không làm hỏng nội dung tri thức bên trong `chunk_text`. Việc chọn `warn` giúp pipeline không bị dừng đột ngột (halt), đảm bảo tính liên tục của dịch vụ tri thức trong khi vẫn gửi cảnh báo để tôi kịp thời điều chỉnh lại hệ thống export.

---

## 3. Một lỗi hoặc anomaly đã xử lý (135 từ)

Trong quá trình chạy thực tế, tôi phát hiện một anomaly nghiêm trọng: hệ thống báo **freshness_check=FAIL** ngay cả khi pipeline vừa mới kết thúc thành công (`PIPELINE_OK`). 

Triệu chứng: Terminal hiển thị `age_hours: ~120` dù `run_timestamp` là thời điểm hiện tại. Tôi đã sử dụng kỹ năng chẩn đoán theo Runbook, kiểm tra file `artifacts/manifests/manifest_2026-04-15T08-27Z.json`. Kết quả cho thấy trường `latest_exported_at` bị lấy từ một bản ghi cũ trong file `policy_export_dirty.csv` (có ngày 2026-04-10). 

Nguyên nhân là do Ingestion source cung cấp dữ liệu snapshot cũ. Tôi đã xử lý bằng cách cập nhật quy trình trong `docs/runbook.md`: hướng dẫn người vận hành kiểm tra cột `exported_at` trong file Raw trước khi chạy. Đồng thời, tôi phối hợp với Member 1 để viết script log cảnh báo nếu ngày export xa hơn 3 ngày so với ngày chạy máy chủ.

---

## 4. Bằng chứng trước / sau (110 từ)

Tôi đã thực hiện so sánh kết quả giữa **Clean Run** và **Inject-bad Run** (sử dụng `run_id: 2026-04-15T08-27Z`). 

Dữ liệu từ `artifacts/eval/clean_run_eval.csv` cho thấy:
- **Scenario Inject-bad:** Câu hỏi `q_refund_window` trả về `hits_forbidden=yes`, nguyên nhân do context chứa thông tin "14 ngày làm việc" cũ.
- **Scenario Clean Run:** Câu hỏi tương tự trả về `hits_forbidden=no`.

Bằng chứng này (được trích xuất từ cột `hits_forbidden` trong file eval) xác nhận rằng các rule cleaning và expectation (đặc biệt là E3) mà nhóm thiết lập đã hoạt động chính xác, giúp bộ lọc monitoring của tôi ghi nhận trạng thái tri thức "sạch" trước khi đưa ra phục vụ người dùng.

---

## 5. Cải tiến tiếp theo (65 từ)

Nếu có thêm 2 giờ, tôi sẽ triển khai một **Dashboard giám sát thời gian thực** bằng Streamlit để hiển thị trực quan tỷ lệ `quarantine / total_records` qua các `run_id`. Điều này giúp bộ phận Monitoring phát hiện sớm xu hướng suy giảm chất lượng dữ liệu từ nguồn (data drift) thay vì phải đọc file JSON manifest thủ công sau mỗi lần chạy.
