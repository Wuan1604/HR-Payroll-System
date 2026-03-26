# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.


frontend/
├── dist/                  # Chứa mã nguồn đã build (production), dùng để triển khai lên server.
│   └── assets/            # Các file CSS/JS đã được nén và băm tên (hashing).
├── node_modules/          # Chứa tất cả các thư viện đã cài đặt (npm install).
├── public/                # Chứa các tài nguyên tĩnh không qua xử lý của Vite (favicon, icon...).
└── src/                   # Thư mục quan trọng nhất - Nơi chứa toàn bộ mã nguồn làm việc.
    ├── api/               # Chứa cấu hình Axios Client (axiosClient.js) để gọi lên Backend.
    ├── assets/            # Chứa hình ảnh, fonts hoặc CSS dùng chung trong mã nguồn.
    ├── components/        # Chứa các thành phần giao diện tái sử dụng (Button, Input, Navbar...).
    ├── pages/             # Chứa các trang chính (DashboardView, EmployeesView, PayrollView...).
    ├── App.css            # CSS tổng thể cho component App.
    ├── App.jsx            # Component gốc điều hướng (Route) toàn bộ ứng dụng.
    ├── index.css          # CSS toàn cục (Global Styles).
    ├── main.jsx           # Điểm khởi đầu của ứng dụng React (Render App vào DOM).
├── .gitignore             # Khai báo các file không đưa lên GitHub (như node_modules).
├── eslint.config.js       # Cấu hình kiểm tra lỗi cú pháp và chuẩn code JavaScript.
├── index.html             # File HTML chính (nơi React sẽ "nhúng" vào).
├── package-lock.json      # Lưu lịch sử phiên bản chi tiết của các thư viện.
├── package.json           # Khai báo thông tin dự án và danh sách các thư viện cài đặt.
├── README.md              # File hướng dẫn chạy dự án.
└── vite.config.js         # Cấu hình cho công cụ build Vite (Proxy, Plugins...).