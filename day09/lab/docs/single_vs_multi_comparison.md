# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** E403_Team61  
**Ngày:** 14/04/2026

---

## 1. Metrics Comparison

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | 0.72 | 0.89 | +0.17 | Do chia context nhỏ |
| Avg latency (ms) | 1250 | 1550 | +300ms | Multi-step agent |
| Abstain rate (%) | 15% | 10% | -5% | % câu trả về "không đủ info" |
| Multi-hop accuracy | 35% | 80% | +45% | % câu multi-hop trả lời đúng |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | Rất dễ theo dõi flow |
| Debug time (estimate) | 20 phút | 5 phút | -15m | Thời gian tìm ra 1 bug |

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | 90% | 90% |
| Latency | ~1100ms | ~1300ms |
| Observation | Nhanh gọn và hiệu quả | Chỉ bị overhear latency xíu |

**Kết luận:** Multi-agent không có sự cải thiện rõ ràng cho Single-Document. Tại vì bản chất việc Retrieve 1 chunk cho 1 fact đơn giản thì cả hai system scale là như nhau, nhưng Multi lại bị delay thêm 1 nhịp từ node Supervisor.

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Khá tệ (Hay miss fact) | Tốt (MCP phân giải) |
| Routing visible? | ✗ | ✓ |
| Observation | Prompt nhồi quá nhiều doc bị quên | Tool gọi doc khi cần nên ít nhiễu |

**Kết luận:** 
Multi-agent vượt trội vì có thể tách tool (ví dụ check ticket, sau đó dùng tool policy check điều lệ ticket type đó).

### 2.3 Câu hỏi cần abstain

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | Đôi khi hallucinate quá trớn | Tự động HITL hoặc strict abstain |
| Hallucination cases | 2/15 | 0/15 |
| Observation | Single quá tham trả lời | Policy Worker chặn mồm Synthesis |

**Kết luận:** Node Policy Worker chặn trước nguồn in của Synthesis nên đã giảm thiểu triệt để hallucinating.

---

## 3. Debuggability Analysis

### Day 08 — Debug workflow
```
Khi answer sai → phải đọc toàn bộ RAG pipeline code → tìm lỗi ở indexing/retrieval/generation
Không có trace → không biết bắt đầu từ đâu
Thời gian ước tính: 20 phút
```

### Day 09 — Debug workflow
```
Khi answer sai → đọc trace → xem supervisor_route + route_reason
  → Nếu route sai → sửa supervisor routing logic
  → Nếu retrieval sai → test retrieval_worker độc lập
  → Nếu synthesis sai → test synthesis_worker độc lập
Thời gian ước tính: 5 phút
```

**Câu cụ thể nhóm đã debug:** Đã debug lỗi query hỏi thông tin User id mà bot trả lời SLA chunk. Ở Day08 sẽ phải tune vector search. Ở Day 09 chỉ cần check `supervisor` tại sao match tag sai vào branch retrieval là xong (lý do: bị thiếu keyword ID regex trong file Supervisor router).

---

## 4. Extensibility Analysis

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa toàn prompt | Thêm MCP tool + route rule |
| Thêm 1 domain mới | Phải retrain/re-prompt | Thêm 1 worker mới |
| Thay đổi retrieval strategy | Sửa trực tiếp trong pipeline | Sửa retrieval_worker độc lập |
| A/B test một phần | Khó — phải clone toàn pipeline | Dễ — swap worker (graph node) |

**Nhận xét:**
Multi-agent là chuẩn production cho việc scale team.

---

## 5. Cost & Latency Trade-off

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 1-2 LLM calls |
| Complex query | 1 LLM call | 3+ LLM calls (Supervisor + synthesis) |
| MCP tool call | N/A | Tốn API cost gọi ngoài |

**Nhận xét về cost-benefit:**
Cost cao hơn, nhưng bù lại tránh được lỗi chết người về policy hoặc hallucinate sai chế độ refund khiến công ty đền bù thì chi phí LLM là quá rẻ.

---

## 6. Kết luận

**Multi-agent tốt hơn single agent ở điểm nào?**
1. Scale tính năng độc lập (Tách dev ra các node).
2. Transparent logging và routing trace để debug.

**Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**
1. Overhead về Latency với những câu hỏi đơn giản.

**Khi nào KHÔNG nên dùng multi-agent?**
Chỉ cần chat qua PDF / Hỏi đáp thông thường dạng open-book không có business logic sâu.

**Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**
Cơ chế tự sửa lỗi tự động (Loop back) tại Node Synthesis nếu nó cảm thấy chunk từ Retrieval trả về kém chất lượng (Re-retrieve branch).
