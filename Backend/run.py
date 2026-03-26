from app import create_app

app = create_app()

if __name__ == '__main__':
    # Xóa dòng print mặc định và thay bằng thông báo của bạn
    print("-" * 30)
    print("Da khoi chay server THANH CONG!....")
    print("He thong dang chay tai cong 5000....")
    
    print("-" * 30)
    
    app.run(debug=True, port=5000, use_reloader=True)