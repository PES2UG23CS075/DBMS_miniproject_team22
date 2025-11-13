CREATE DATABASE food_delivery;
USE food_delivery;

CREATE TABLE Customer (Cust_ID INT PRIMARY KEY, Cust_Name VARCHAR(100) NOT NULL,PhoneNo VARCHAR(15) NOT NULL,Email VARCHAR(100) NOT NULL UNIQUE,
StreetName VARCHAR(100) NOT NULL,Pincode VARCHAR(10) NOT NULL,Allergy VARCHAR(100));

CREATE TABLE Employee (Emp_ID INT PRIMARY KEY,Emp_Name VARCHAR(100) NOT NULL,DOB DATE,Email VARCHAR(100) NOT NULL UNIQUE,
PhoneNo VARCHAR(15)NOT NULL, Gender VARCHAR(10),Address VARCHAR(200),Salary DECIMAL(10,2),Password VARCHAR(50) NOT NULL UNIQUE);

CREATE TABLE Chef (Chef_ID INT PRIMARY KEY,Chef_Name VARCHAR(100)NOT NULL,PhoneNo VARCHAR(15) NOT NULL ,Email VARCHAR(100) NOT NULL UNIQUE,
StreetName VARCHAR(100) NOT NULL,Pincode VARCHAR(10) NOT NULL,Password VARCHAR(50)NOT NULL UNIQUE);

CREATE TABLE Cuisine (Cuisine_ID INT,Chef_ID INT,Cuisine_Name VARCHAR(100),PRIMARY KEY (Cuisine_ID, Chef_ID),
FOREIGN KEY (Chef_ID) REFERENCES Chef(Chef_ID));

CREATE TABLE Ingredient (Ing_ID INT PRIMARY KEY,Ing_Name VARCHAR(100));

CREATE TABLE Food (Food_ID INT PRIMARY KEY,FName VARCHAR(100),Price DECIMAL(10,2),Quantity INT,Availability VARCHAR(10));

CREATE TABLE Drink (Drink_ID INT PRIMARY KEY,DName VARCHAR(100),Price DECIMAL(10,2),Quantity INT,Availability VARCHAR(10));

CREATE TABLE Orders (Order_ID INT PRIMARY KEY,Quantity INT, Cust_ID INT, FOREIGN KEY (Cust_ID) REFERENCES Customer(Cust_ID));

CREATE TABLE Delivery_Incharge (Delivery_ID INT,Del_Name VARCHAR(100) NOT NULL,VehicleNumber VARCHAR(20) NOT NULL UNIQUE,
DelCharge DECIMAL(10,2), DelDate DATE,DelTime TIME, Order_ID INT,PRIMARY KEY(Delivery_ID,Order_ID),
FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID));

CREATE TABLE Payment (Payment_ID INT PRIMARY KEY,Method VARCHAR(50),Amount DECIMAL(10,2),Order_ID INT UNIQUE,
 FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID));

CREATE TABLE Prepared_by (Food_ID INT,Chef_ID INT,PRIMARY KEY (Food_ID, Chef_ID),
FOREIGN KEY (Food_ID) REFERENCES Food(Food_ID),FOREIGN KEY (Chef_ID) REFERENCES Chef(Chef_ID));

CREATE TABLE Uses (Chef_ID INT,Ing_ID INT,PRIMARY KEY (Chef_ID, Ing_ID),
FOREIGN KEY (Chef_ID) REFERENCES Chef(Chef_ID),FOREIGN KEY (Ing_ID) REFERENCES Ingredient(Ing_ID));

CREATE TABLE Contains (Order_ID INT,Food_ID INT,Drink_ID INT,PRIMARY KEY(Order_ID,Drink_ID,Food_ID),
FOREIGN KEY (Order_ID) REFERENCES Orders(Order_ID), FOREIGN KEY (Food_ID) REFERENCES Food(Food_ID),
FOREIGN KEY (Drink_ID) REFERENCES Drink(Drink_ID));

CREATE TABLE Works_For (Cust_ID INT,Emp_ID INT, PRIMARY KEY(Cust_ID,Emp_ID),
FOREIGN KEY (Cust_ID) REFERENCES Customer(Cust_ID), FOREIGN KEY (Emp_ID) REFERENCES Employee(Emp_ID));

INSERT INTO Customer (Cust_ID, Cust_Name, PhoneNo, Email, StreetName, Pincode, Allergy) VALUES
(1, 'John Doe', '9876543210', 'john.doe@email.com', '123 Main St', '560001', 'None'),
(2, 'Jane Smith', '8765432109', 'jane.smith@email.com', '456 Oak Ave', '560002', 'Peanuts');

SELECT * FROM Customer;

INSERT INTO Employee (Emp_ID, Emp_Name, DOB, Email, PhoneNo, Gender, Address, Salary, Password) VALUES
(101, 'Admin User', '1990-05-15', 'admin@fooddelivery.com', '1112223330', 'Male', '789 Pine Ln', 60000.00, 'adminpass'),
(102, 'Manager User', '1988-10-20', 'manager@fooddelivery.com', '4445556660', 'Female', '101 Maple Dr', 75000.00, 'managerpass');

SELECT * FROM Employee;

INSERT INTO Chef (Chef_ID, Chef_Name, PhoneNo, Email, StreetName, Pincode, Password) VALUES
(201, 'Marco Pierre', '5551112223', 'marco.p@email.com', '21 Baker St', '560003', 'chefpass1'),
(202, 'Priya Kumar', '5553334445', 'priya.k@email.com', '32 Temple Rd', '560004', 'chefpass2');
SELECT * FROM Chef;

INSERT INTO Ingredient (Ing_ID, Ing_Name) VALUES (1, 'Tomato'), (2, 'Cheese'), (3, 'Chicken'), (4, 'Flour');
SELECT * FROM Ingredient;

INSERT INTO Food (Food_ID, FName, Price, Quantity, Availability) VALUES
(301, 'Margherita Pizza', 350.00, 20, 'Yes'),
(302, 'Chicken Curry', 450.00, 15, 'Yes');
INSERT INTO Food (Food_ID, FName, Price, Quantity, Availability)
VALUES (0, 'No Food Item', 0.00, 999, 'Yes');
SELECT * FROM Food;

INSERT INTO Drink (Drink_ID, DName, Price, Quantity, Availability) VALUES
(401, 'Coke', 50.00, 100, 'Yes'),
(402, 'Lemonade', 70.00, 50, 'No');
INSERT INTO Drink (Drink_ID, DName, Price, Quantity, Availability)
VALUES (0, 'No Drink Item', 0.00, 999, 'Yes');
SELECT * FROM Drink;

INSERT INTO Cuisine (Cuisine_ID, Chef_ID, Cuisine_Name) VALUES (501, 201, 'Italian'), (502, 202, 'Indian');
SELECT * FROM Cuisine;

INSERT INTO Orders (Order_ID, Quantity, Cust_ID) VALUES (1001, 2, 1), (1002, 1, 2);
INSERT INTO Orders (Order_ID, Quantity, Cust_ID) VALUES (1004, 1, 1);
SELECT * FROM Orders;

INSERT INTO Prepared_by (Food_ID, Chef_ID) VALUES (301, 201), (302, 202);
SELECT * FROM Prepared_by;

INSERT INTO Uses (Chef_ID, Ing_ID) VALUES (201, 1), (201, 2), (202, 3);
SELECT * FROM Uses;

INSERT INTO Delivery_Incharge (Delivery_ID, Del_Name, VehicleNumber, DelCharge, DelDate, DelTime, Order_ID) VALUES
(601, 'Delivery Dave', 'KA-01-1234', 50.00, '2025-10-07', '21:30:00', 1001),
(602, 'Rider Rita', 'KA-02-5678', 50.00, '2025-10-07', '21:45:00', 1002);
SELECT * FROM Delivery_Incharge;

INSERT INTO Payment (Payment_ID, Method, Amount, Order_ID) VALUES
(701, 'Credit Card', 750.00, 1001), (702, 'UPI', 450.00, 1002);
SELECT * FROM Payment;

INSERT INTO Contains (Order_ID, Food_ID, Drink_ID) VALUES (1001, 301, 401), (1002, 302, 401);
INSERT INTO Contains (Order_ID, Food_ID, Drink_ID) VALUES (1004, 301, 0);
SELECT * FROM Contains;

INSERT INTO Works_For (Cust_ID, Emp_ID) VALUES (1, 102),(2, 101);
SELECT * FROM Works_For;

DELIMITER $$
CREATE TRIGGER before_payment_insert_calculate_total
BEFORE INSERT ON Payment FOR EACH ROW
BEGIN
    DECLARE total_cost DECIMAL(10, 2) DEFAULT 0.00;
    SELECT SUM(COALESCE(f.Price, 0) + COALESCE(d.Price, 0)) INTO total_cost 
    FROM Contains c 
    LEFT JOIN Food f ON c.Food_ID = f.Food_ID
    LEFT JOIN Drink d ON c.Drink_ID = d.Drink_ID 
    WHERE c.Order_ID = NEW.Order_ID;
    SET NEW.Amount = COALESCE(total_cost, 0.00);
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER after_contains_insert_update_inventory
AFTER INSERT ON Contains FOR EACH ROW
BEGIN
    IF NEW.Food_ID IS NOT NULL AND NEW.Food_ID != 0 THEN
        UPDATE Food SET Quantity = Quantity - 1 WHERE Food_ID = NEW.Food_ID;
    END IF;
    IF NEW.Drink_ID IS NOT NULL AND NEW.Drink_ID != 0 THEN
        UPDATE Drink SET Quantity = Quantity - 1 WHERE Drink_ID = NEW.Drink_ID;
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE PROCEDURE PlaceCompleteOrder(IN p_Cust_ID INT,IN p_Food_ID INT,IN p_Drink_ID INT,IN p_PaymentMethod VARCHAR(50))
BEGIN
    DECLARE new_OrderID INT;
    DECLARE new_PaymentID INT;
    SELECT COALESCE(MAX(Order_ID), 1000) + 1 INTO new_OrderID FROM Orders;
    SELECT COALESCE(MAX(Payment_ID), 700) + 1 INTO new_PaymentID FROM Payment;
    INSERT INTO Orders (Order_ID, Quantity, Cust_ID) VALUES (new_OrderID, 1, p_Cust_ID);
    INSERT INTO Contains (Order_ID, Food_ID, Drink_ID) VALUES (new_OrderID, p_Food_ID, p_Drink_ID);
    INSERT INTO Payment (Payment_ID, Method, Order_ID, Amount) VALUES (new_PaymentID, p_PaymentMethod, new_OrderID, 0); 
    SELECT new_OrderID AS 'NewOrderID';
END$$
DELIMITER ;

DELIMITER $$
CREATE FUNCTION GetCustomerOrderCount(p_Cust_ID INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE order_count INT;
    SELECT COUNT(*) INTO order_count FROM Orders WHERE Cust_ID = p_Cust_ID;
    RETURN order_count;
END$$
DELIMITER ;

SELECT FName, Quantity FROM Food WHERE Food_ID = 301;
INSERT INTO Contains (Order_ID, Food_ID, Drink_ID) VALUES (1002, 301, 0);
SELECT FName, Quantity FROM Food WHERE Food_ID = 301;

CALL PlaceCompleteOrder(1, 301, 401, 'Credit Card');
SELECT GetCustomerOrderCount(1) AS JohnDoeOrders;

INSERT INTO Orders (Order_ID, Quantity, Cust_ID) VALUES (1007, 2, 2);
INSERT INTO Contains (Order_ID, Food_ID, Drink_ID) VALUES (1007, 302, 401);
INSERT INTO Payment (Payment_ID, Method, Order_ID, Amount) VALUES (705, 'Credit Card', 1007, 1.00);
SELECT * FROM Payment WHERE Order_ID = 1007;

SELECT c.Cust_Name,SUM(p.Amount) AS Total_Spent_By_Customer FROM Customer c JOIN Orders o ON c.Cust_ID = o.Cust_ID
JOIN Payment p ON o.Order_ID = p.Order_ID GROUP BY c.Cust_Name ORDER BY Total_Spent_By_Customer DESC;

SELECT o.Order_ID,c.Cust_Name,f.FName AS Food_Ordered,d.DName AS Drink_Ordered FROM Orders o JOIN Customer c ON o.Cust_ID = c.Cust_ID
JOIN Contains con ON o.Order_ID = con.Order_ID LEFT JOIN Food f ON con.Food_ID = f.Food_ID LEFT JOIN Drink d ON con.Drink_ID = d.Drink_ID
WHERE f.Food_ID != 0 OR d.Drink_ID != 0;

SELECT Cust_Name, Email FROM Customer WHERE Cust_ID IN (SELECT o.Cust_ID FROM Orders o JOIN Contains c ON o.Order_ID = c.Order_ID
WHERE c.Food_ID = 301 );

SELECT FName, Quantity FROM Food WHERE Food_ID = 302;
INSERT INTO Contains (Order_ID, Food_ID, Drink_ID) VALUES (1001, 302, 0);
SELECT FName, Quantity FROM Food WHERE Food_ID = 302;

CALL PlaceCompleteOrder(2, 302, 401, 'UPI');
SELECT * FROM Orders ORDER BY Order_ID DESC LIMIT 1;
SELECT * FROM Payment ORDER BY Payment_ID DESC LIMIT 1;

SELECT GetCustomerOrderCount(2) AS JaneSmithTotalOrders;


INSERT INTO Orders (Order_ID, Quantity, Cust_ID) VALUES (1020, 1, 2);
INSERT INTO Contains (Order_ID, Food_ID, Drink_ID) VALUES (1020, 302, 402);
INSERT INTO Payment (Payment_ID, Method, Order_ID, Amount) VALUES (720, 'Debit Card', 1020, 1.00);
SELECT * FROM Payment WHERE Order_ID = 1020;



SELECT FName, Quantity FROM Food WHERE Food_ID = 305;
INSERT INTO Contains (Order_ID, Food_ID, Drink_ID) VALUES (1003, 305, 0);
SELECT FName, Quantity FROM Food WHERE Food_ID = 305;

CALL PlaceCompleteOrder(5, 305, 421, 'UPI');
SELECT * FROM Orders ORDER BY Order_ID DESC LIMIT 1;
SELECT * FROM Payment ORDER BY Payment_ID DESC LIMIT 1;

SELECT GetCustomerOrderCount(2) AS JaneSmithTotalOrders;


INSERT INTO Orders (Order_ID, Quantity, Cust_ID) VALUES (1009, 1, 97);
INSERT INTO Contains (Order_ID, Food_ID, Drink_ID) VALUES (1009, 302, 402);
INSERT INTO Payment (Payment_ID, Method, Order_ID, Amount) VALUES (750, 'Debit Card', 1009, 1.00);
SELECT * FROM Payment WHERE Order_ID = 1009;

ALTER TABLE Food 
ADD CONSTRAINT chk_qty_positive CHECK (Quantity >= 0);

ALTER TABLE Drink
ADD CONSTRAINT chk_qty_positive_drink CHECK (Quantity >= 0);


DELIMITER $$
CREATE TRIGGER update_food_status
BEFORE UPDATE ON Food
FOR EACH ROW
BEGIN
  IF NEW.Quantity <= 0 THEN
    SET NEW.Availability = 'No';
  ELSE
    SET NEW.Availability = 'Yes';
  END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER update_drink_status
BEFORE UPDATE ON Drink
FOR EACH ROW
BEGIN
  IF NEW.Quantity <= 0 THEN
    SET NEW.Availability = 'No';
  ELSE
    SET NEW.Availability = 'Yes';
  END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER check_food_status_on_insert
BEFORE INSERT ON Food
FOR EACH ROW
BEGIN
  IF NEW.Quantity <= 0 THEN
    SET NEW.Availability = 'No';
  ELSE
    SET NEW.Availability = 'Yes';
  END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER check_drink_status_on_insert
BEFORE INSERT ON Drink
FOR EACH ROW
BEGIN
  IF NEW.Quantity <= 0 THEN
    SET NEW.Availability = 'No';
  ELSE
    SET NEW.Availability = 'Yes';
  END IF;
END$$
DELIMITER ;

SELECT FName, Quantity, Availability FROM Food WHERE FName = 'Garlic Bread';
SELECT FName, Quantity, Availability FROM Food WHERE FName = 'Tiramisu';
SELECT FName, Quantity, Price FROM Food WHERE FName = 'Garlic Bread';
SELECT DName, Quantity FROM Drink WHERE DName = 'Iced Tea';
Select * from Customer;
Select * from Drink;
SELECT Amount, Method FROM Payment ORDER BY Payment_ID DESC LIMIT 1;


SELECT Del_Name, VehicleNumber 
FROM Delivery_Incharge 
WHERE Order_ID = 1002;


