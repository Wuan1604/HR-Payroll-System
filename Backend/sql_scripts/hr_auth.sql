CREATE DATABASE IF NOT EXISTS hr_auth
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE hr_auth;

CREATE TABLE IF NOT EXISTS roles (
    RoleID INT AUTO_INCREMENT PRIMARY KEY,
    RoleName VARCHAR(50) NOT NULL UNIQUE,
    Description VARCHAR(255) NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    EmployeeID INT NULL,
    FullName VARCHAR(100) NOT NULL,
    Email VARCHAR(100) NOT NULL UNIQUE,
    Username VARCHAR(50) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    RoleID INT NOT NULL,
    Status ENUM('Active', 'Locked', 'Inactive') DEFAULT 'Active',
    LastLogin DATETIME NULL,
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_roles
        FOREIGN KEY (RoleID) REFERENCES roles(RoleID)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS user_login_logs (
    LogID INT AUTO_INCREMENT PRIMARY KEY,
    UserID INT NULL,
    Email VARCHAR(100) NULL,
    LoginStatus ENUM('Success', 'Failed') NOT NULL,
    Message VARCHAR(255) NULL,
    LoginTime DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_login_logs_users
        FOREIGN KEY (UserID) REFERENCES users(UserID)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

INSERT INTO roles (RoleName, Description)
VALUES
('Admin', 'Toàn quyền quản trị hệ thống'),
('Manager', 'Quản lý nhân sự, bảng lương và chấm công'),
('Employee', 'Nhân viên chỉ xem thông tin cá nhân, lương và chấm công của bản thân')
ON DUPLICATE KEY UPDATE Description = VALUES(Description);
