#  DBMS Mini Project – Restaurant Management System  
**Author:** PES2UG23CS075 – Anjali Gunti 
             PES2UG23CS110-Avani Ajith
**Course:** DBMS Laboratory  
**University:** PES University  


##  Project Overview  
This mini-project implements a **Restaurant Management System** using:

- **MySQL** (Database)
- **Python Tkinter GUI** (Frontend)
- **SQL Procedures, Functions & Triggers**
- **ER Diagram & Relational Schema Documentation**

The system allows management of customers, staff, menu items, ingredients, inventory, and order processing with automatic stock updates.

##  Features Implemented  

###  **1. Customer Management**
- Add new customers  
- View customer list  
- Edit customer details  
- Delete customers  

###  **2. Staff Management**
- Add new chefs & employees  
- Maintain roles & salary  
- View staff details  

###  **3. Menu & Inventory Management**
- Add food and drink items  
- Update stock levels  
- Toggle availability (In Stock / Out of Stock)  

###  **4. Order Management**
- Create new orders  
- Add items to order  
- **Automatically reduce stock quantity** via trigger  
- Compute total bill  

###  **5. Ingredient Management**
- Assign ingredients to menu items  
- Track ingredient stock usage  
- Maintain ingredient list  

### ✔ **6. SQL Functions, Procedures & Triggers**
Included in `miniproject.sql`:
- `calculate_total()` – function  
- `add_customer()` – procedure  
- `add_staff()` – procedure  
- `update_stock_trigger` – automatic stock reduction  
- `validate_order_trigger` – prevents orders when item stock is zero  


##  Database Design

###  **ER Diagram**
File: `fianlerdiagproj.drawio.pdf`  
Contains entities:
- Customer  
- Staff  
- Orders  
- Menu  
- OrderItems  
- Ingredients  
- Inventory  

###  **Relational Schema**
File: `finalrelschemaproj.drawio.pdf`  
Includes:
- Primary Keys  
- Foreign Keys  
- Cardinality Mapping  
- Relationship Types  





