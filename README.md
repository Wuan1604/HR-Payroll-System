# HR-Payroll-System


Trước khi làm thì đọc kĩ các file README.md 
để rõ cấu trúc thư mục của Back end và Front end
Để hiểu rõ đàng làm gì 
Backend
Chỉnh lại file cofig theo đúng với đường link đến hai DB của máy tính
Backend/app/fonfig.py
chỉnh SQL_SERVER_CONN=DRIVER= ở trong .env cho đúng đường link
tạo file .env và dán câu lệch ở dưới




# Thông tin kết nối SQL Server
SQL_SERVER_CONN=DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-QURO3OM;DATABASE=HUMAN_2025;trusted_connection=yes

# Thông tin kết nối MySQL
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=payroll

# Thông tin Email
SENDER_EMAIL=16.nguyenquan2004@gmail.com
SENDER_PASSWORD=dasw ctzo hzwe oyqg

# -------------------------
# Admin login (hardcoded)
# -------------------------
# ADMIN_USERNAME: tài khoản đăng nhập admin
ADMIN_USERNAME=admin123
# ADMIN_PASSWORD_HASH: bcrypt hash của mật khẩu admin
# Ví dụ format: $2b$12$...
ADMIN_PASSWORD_HASH=$2b$12$CwNZYjUW8tnO8iRFkgbYB.gEL0Zd.XG6FEimjzuQhF95Xsdss.7uu





Chạy hệ thống
Back end
cd đến đúng Backend
chạy các câu lệch cài đặt thư viện lên máy
# Cập nhật pip trước cho chắc
python -m pip install --upgrade pip

# Cài đặt Flask và các tiện ích mở rộng
pip install flask flask-cors python-dotenv

# Cài đặt thư viện kết nối MySQL
pip install mysql-connector-python

# Cài đặt thư viện kết nối SQL Server (Cần có ODBC Driver trên máy)
pip install pyodbc

# Cài đặt thư viện xử lý dữ liệu (Nếu bạn muốn làm thêm báo cáo Excel)
pip install pandas openpyxl


Tiếp đến .
Chạy lệch
python run.py 

DONE
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
------------------------------
Da khoi chay server THANH CONG!....
He thong dang chay tai cong 5000....
------------------------------
 * Debugger is active!
 * Debugger PIN: 923-507-648



Front end
chạy cài đặt các thư viện 
# Cài đặt React Router (Để chuyển trang giữa Dashboard, Employees, Payroll...)
npm install react-router-dom

# Cài đặt Axios (Để gọi API từ Flask Backend)
npm install axios

# Cài đặt Lucide React hoặc FontAwesome (Để dùng các Icon đẹp như ví tiền, người dùng)
npm install lucide-react 
# Hoặc nếu bạn dùng FontAwesome:
npm install @fortawesome/fontawesome-svg-core @fortawesome/free-solid-svg-icons @fortawesome/react-fontawesome

# Cài đặt Chart.js (Nếu bạn muốn làm trang Reports vẽ biểu đồ lương)
npm install chart.js react-chartjs-2

Tiếp đến .
Chạy lệch
npm run dev

DONE
PS D:\Visua Studio Code\HR-Payroll-System\frontend> npm run dev

> frontend@0.0.0 dev
> vite

9:45:50 AM [vite] (client) Re-optimizing dependencies because vite config has changed

  VITE v8.0.2  ready in 1078 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help


LƯU Ý: Khi chạy sẽ  có  tự sinh ra các file .pyc là file rác 
các khắc phục 
Bật CMD quyền Admin  và chạy lệch setx PYTHONDONTWRITEBYTECODE 1
sau đó khởi động lại máy 