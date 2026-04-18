create database restaurantdb;
use restaurantdb;

CREATE TABLE Customer (
    CustomerID INT PRIMARY KEY,
    Name VARCHAR(50),
    Phone VARCHAR(15),
    Email VARCHAR(100)
);

CREATE TABLE Staff (
    StaffID INT PRIMARY KEY,
    Name VARCHAR(50),
    Phone VARCHAR(15),
    Role VARCHAR(50)
);

CREATE TABLE RestaurantTable (
    TableID INT PRIMARY KEY,
    Capacity INT,
    Status VARCHAR(20),
    Location VARCHAR(50)
);

CREATE TABLE MenuItem (
    MenuID INT PRIMARY KEY,
    ItemName VARCHAR(50),
    Price DECIMAL(10,2),
    Category VARCHAR(50)
);

CREATE TABLE RestaurantOrder (
    OrderID INT PRIMARY KEY,
    OrderDate DATETIME,
    Subtotal DECIMAL(10,2),
    CustomerID INT,
    StaffID INT,
    TableID INT,
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID),
    FOREIGN KEY (StaffID) REFERENCES Staff(StaffID),
    FOREIGN KEY (TableID) REFERENCES RestaurantTable(TableID)
);

CREATE TABLE OrderItem (
    OrderID INT,
    MenuID INT,
    Quantity INT,
    ItemPrice DECIMAL(10,2),
    PRIMARY KEY (OrderID, MenuID),
    FOREIGN KEY (OrderID) REFERENCES RestaurantOrder(OrderID),
    FOREIGN KEY (MenuID) REFERENCES MenuItem(MenuID)
);

CREATE TABLE Payment (
    PaymentID INT PRIMARY KEY,
    OrderID INT,
    Amount DECIMAL(10,2),
    PaymentType VARCHAR(20),
    PaymentDate DATETIME,
    FOREIGN KEY (OrderID) REFERENCES RestaurantOrder(OrderID),
    CHECK (PaymentType IN ('debit', 'credit', 'cash'))
);

CREATE TABLE Reservation (
    ReservationID INT PRIMARY KEY,
    PartySize INT,
    ReservationDate DATE,
    ReservationTime TIME,
    CustomerID INT,
    TableID INT,
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID),
    FOREIGN KEY (TableID) REFERENCES RestaurantTable(TableID)
);
