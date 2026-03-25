# AI-Powered Learning App: Knowledge Graph Generator

Một nền tảng học tập thông minh giúp chuyển đổi tài liệu học thuật phức tạp thành **Sơ đồ tri thức (Knowledge Graph)** trực quan, giúp người học tối ưu hóa quá trình tiếp thu kiến thức.

![Project Status](https://img.shields.io/badge/Status-Development-orange)
![Tech Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20Supabase-blue)

---

## Tầm nhìn và Ý nghĩa của dự án

Trong kỷ nguyên bùng nổ thông tin, việc update kiến thức liên tục là vấn đề sống còn, nhưng vấn đề lớn nhất không phải là thiếu tài liệu, mà là việc chúng ta học như thế nào để tiết kiệm thời gian và hiệu quả nhất. Dự án này được thiết kế hỗ trợ người học dưới phương pháp tiếp cận học từ tổng quát đến chi tiết thông qua đồ thị kiến thức.

Dự án này ra đời nhằm giải quyết 3 thách thức lớn trong học tập:

1. **Bức tranh toàn cảnh (Big Picture Visualization):** Biến toàn bộ nội dung tài liệu thành một sơ đồ duy nhất. Giúp người học không còn cảm giác "thấy cây mà không thấy rừng".
2. **Tiết kiệm thời gian (High-Granularity Filtering):** Thay vì đọc và tự hệ thống lại, AI tự động quét và "sàng lọc" những đơn vị kiến thức cốt lõi nhất, giúp tập trung vào bản chất vấn đề.
3. **Xây dựng tư duy hệ thống (System Thinking):** Thay vì học từng kiến thức nhỏ rải rác, Đồ thị giúp hiểu rõ mối quan hệ ràng buộc: *"Chưa hiểu khái niệm A thì không thể nắm vững Procedure B"*. 

---

## Cấu trúc "Hạt nhân kiến thức" (Node Types)

Khác với các ứng dụng ghi chú thông thường chỉ lưu trữ văn bản, hệ thống này phân loại kiến thức thành 3 "hạt nhân" riêng biệt dựa trên **Tâm lý học nhận thức**:

- **Concept (Khái niệm):** Các đơn vị lý thuyết cần hiểu sâu và sử dụng các ví dụ minh họa để nắm bắt bản chất.
- **Fact (Sự thật/Dữ kiện):** Các thông tin mang tính ghi nhớ, tra cứu (số liệu, hằng số, định lý) giúp xây dựng nền tảng vững chắc.
- **Procedure (Quy trình):** Các bước thực hiện, thuật toán hoặc phương pháp mang tính thực hành, giúp người học chuyển đổi lý thuyết thành kỹ năng thực tế.

## Tại sao lại là Đồ thị (Graph)?

*"Kiến thức không đứng độc lập, chúng là một mạng lưới liên kết."*

- **Học tập không tuyến tính:** Thay vì đọc từ trang 1 đến trang 100, đồ thị cho phép bạn "nhảy" vào bất kỳ điểm nào và biết chính xác mình đang ở đâu trong hệ thống tri thức.
- **Phát hiện lỗ hổng kiến thức:** Bằng cách nhìn vào các cạnh `requires`, nếu bạn chưa hiểu Concept A, đồ thị sẽ cảnh báo bạn đừng vội vàng học Procedure B. 
- **Bảo tồn ngữ cảnh:** AI trích xuất kèm theo `source_ref` (nguồn trích dẫn), giúp bạn dễ dàng quay lại trang sách gốc để đọc kỹ hơn chỉ với một cú click chuột.

## Tính năng "Deep Dive": Giải thích sâu & Đa phương tiện

Chạm vào một Node không chỉ dừng lại ở việc đọc định nghĩa. Hệ thống cung cấp cơ chế **AI-Explainer** siêu cấp:

- **Giải thích theo ngữ cảnh:** AI sẽ thực hiện (On-demand request) để tạo ra các giải thích sâu sắc hơn, đưa ra các ví dụ thực tế liên quan đến đời sống hàng ngày (Analogy).
- **Yêu cầu & Điều kiện (Requirements):** Bên cạnh `requires` cứng từ đồ thị, hệ thống phân tích thêm các kỹ năng cần thiết để làm chủ khái niệm đó.
- **Tài nguyên học tập thời gian thực:** Tự động đề xuất các tài liệu tham khảo chất lượng cao từ thế giới bên ngoài như:
  - **YouTube Videos:** Các bài giảng chọn lọc dễ hiểu nhất.
  - **Learning Articles:** Các bài blog kỹ thuật sâu sắc (Medium, Towards Data Science...).

---

## Công nghệ và Kiến trúc

Dự án sử dụng sức mạnh của các Large Language Models (LLMs)
### Công nghệ lõi
- **AI Brain:** Google Gemini Pro & Groq (Llama 3).
- **Backend:** FastAPI (Python) - Xử lý tính toán song song, Pipeline trích xuất kiến thức đa tầng.
- **Frontend:** Next.js & TailwindCSS - Giao diện hiện đại, mượt mà với hiệu ứng kính mờ (Glassmorphism).
- **Database:** Supabase - Đồng bộ hóa dữ liệu thời gian thực.

### Quy trình xử lý (Pipeline)
1. **Parser:** Làm sạch và trích xuất text chất lượng cao từ PDF/DOCX/PPTX.
2. **Chunker:** Chia nhỏ văn bản thông minh kèm cơ chế Overlap bảo toàn ngữ cảnh.
3. **Extractor:** Trích xuất Nodes & Edges thông qua 2-Pass AI Flow.
4. **Deduplicator:** Chuẩn hóa và hợp nhất kiến thức toàn diện.

---

## Hướng dẫn cài đặt nhanh

### Yêu cầu
- Python 3.9+ | Node.js 18+

### Cài đặt
1. **Backend:** `cd backend && pip install -r requirements.txt && python main.py`
2. **Frontend:** `cd frontend && npm install && npm run dev`

---

**Dự án được thực hiện bởi [QNSang](https://github.com/QNSang)** - *Với mong muốn thay đổi cách chúng ta tiếp cận tri thức.*
