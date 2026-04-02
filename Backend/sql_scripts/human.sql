/* 
   DATABASE: HUMAN_2025
   Sử dụng lệnh tạo cấu trúc bảng và các ràng buộc
*/

-- 1. TẠO BẢNG PHÒNG BAN (Departments)
CREATE TABLE [dbo].[Departments](
	[DepartmentID] [int] IDENTITY(1,1) NOT NULL,
	[DepartmentName] [nvarchar](100) NOT NULL,
	[CreatedAt] [datetime] DEFAULT (getdate()),
	[UpdatedAt] [datetime] DEFAULT (getdate()),
	PRIMARY KEY CLUSTERED ([DepartmentID] ASC)
) ON [PRIMARY];
GO

-- 2. TẠO BẢNG CHỨC VỤ (Positions)
CREATE TABLE [dbo].[Positions](
	[PositionID] [int] IDENTITY(1,1) NOT NULL,
	[PositionName] [nvarchar](100) NOT NULL,
	[CreatedAt] [datetime] DEFAULT (getdate()),
	[UpdatedAt] [datetime] DEFAULT (getdate()),
	PRIMARY KEY CLUSTERED ([PositionID] ASC)
) ON [PRIMARY];
GO

-- 3. TẠO BẢNG NHÂN VIÊN (Employees)
CREATE TABLE [dbo].[Employees](
	[EmployeeID] [int] IDENTITY(1,1) NOT NULL,
	[FullName] [nvarchar](100) NOT NULL,
	[DateOfBirth] [date] NOT NULL,
	[Gender] [nvarchar](10) NULL,
	[PhoneNumber] [nvarchar](15) NULL,
	[Email] [nvarchar](100) NULL,
	[HireDate] [date] NOT NULL,
	[DepartmentID] [int] NULL,
	[PositionID] [int] NULL,
	[Status] [nvarchar](50) NULL,
	[CreatedAt] [datetime] DEFAULT (getdate()),
	[UpdatedAt] [datetime] DEFAULT (getdate()),
	PRIMARY KEY CLUSTERED ([EmployeeID] ASC),
	UNIQUE NONCLUSTERED ([Email] ASC)
) ON [PRIMARY];
GO

-- 4. TẠO BẢNG CỔ TỨC/THƯỞNG (Dividends)
CREATE TABLE [dbo].[Dividends](
	[DividendID] [int] IDENTITY(1,1) NOT NULL,
	[EmployeeID] [int] NULL,
	[DividendAmount] [decimal](12, 2) NOT NULL,
	[DividendDate] [date] NOT NULL,
	[CreatedAt] [datetime] DEFAULT (getdate()),
	PRIMARY KEY CLUSTERED ([DividendID] ASC)
) ON [PRIMARY];
GO

-- 5. THIẾT LẬP CÁC RÀNG BUỘC KHÓA NGOẠI (Foreign Keys)

-- Liên kết Dividends -> Employees
ALTER TABLE [dbo].[Dividends]  WITH CHECK ADD  CONSTRAINT [FK_Dividends_Employees] FOREIGN KEY([EmployeeID])
REFERENCES [dbo].[Employees] ([EmployeeID]);
GO
ALTER TABLE [dbo].[Dividends] CHECK CONSTRAINT [FK_Dividends_Employees];
GO

-- Liên kết Employees -> Departments
ALTER TABLE [dbo].[Employees]  WITH CHECK ADD  CONSTRAINT [FK_Employees_Departments] FOREIGN KEY([DepartmentID])
REFERENCES [dbo].[Departments] ([DepartmentID]);
GO
ALTER TABLE [dbo].[Employees] CHECK CONSTRAINT [FK_Employees_Departments];
GO

-- Liên kết Employees -> Positions
ALTER TABLE [dbo].[Employees]  WITH CHECK ADD  CONSTRAINT [FK_Employees_Positions] FOREIGN KEY([PositionID])
REFERENCES [dbo].[Positions] ([PositionID]);
GO
ALTER TABLE [dbo].[Employees] CHECK CONSTRAINT [FK_Employees_Positions];
GO