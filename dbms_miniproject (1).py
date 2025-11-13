import tkinter as tk
from tkinter import ttk, messagebox, font
import mysql.connector
from datetime import date
import sv_ttk
from PIL import Image, ImageTk

# ==============================
# GLOBALS / PRICING MAPS
# ==============================
# For item lookups (id, price, stock)
food_info  = {}  # name -> {"id":..., "price":..., "qty":...}
drink_info = {}  # name -> {"id":..., "price":..., "qty":...}

# Cart items list (each: {"type":"Food"/"Drink","name":str,"id":int,"price":float,"qty":int})
cart_items = []
current_selected_order_id = None
# ==============================
# DB HELPERS
# ==============================
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="Avani@110",
            database="food_delivery"
        )
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Could not connect to database:\n{err}")
        return None

def execute_query(query, params=None, fetch=True, dictionary=True):
    cn = get_db_connection()
    if cn is None:
        return None if fetch else False
    try:
        cur = cn.cursor(dictionary=dictionary)
        cur.execute(query, params or ())
        if fetch:
            return cur.fetchall()
        cn.commit()
        return True
    except mysql.connector.Error as err:
        cn.rollback()
        messagebox.showerror("Query Error", f"{err}")
        return None if fetch else False
    finally:
        try: cur.close()
        except: pass
        cn.close()

def refresh_treeview(tree, query, params=None):
    for i in tree.get_children():
        tree.delete(i)
    rows = execute_query(query, params)
    if rows:
        for row in rows:
            tree.insert("", tk.END, values=list(row.values()))

# ==============================
# GLOBAL MAPS (for dropdowns)
# ==============================
customer_map  = {}
food_map      = {}
drink_map     = {}
chef_map      = {}
ingredient_map= {}
employee_map  = {}

# ==============================
# STATUS
# ==============================
def set_status(msg: str):
    status_var.set(msg)

# ==============================
# ORDER / CART HELPERS
# ==============================
def populate_order_dropdowns():
    """Fill New Order sources (customers + in-stock items) and cache price/qty."""
    customer_map.clear()
    food_map.clear();   food_info.clear()
    drink_map.clear();  drink_info.clear()

    # customers
    custs = execute_query("SELECT Cust_ID, Cust_Name FROM Customer")
    if custs:
        for c in custs:
            customer_map[c['Cust_Name']] = c['Cust_ID']

    # foods (in stock)
    foods = execute_query("SELECT Food_ID, FName, Price, Quantity FROM Food WHERE Availability='Yes' AND Food_ID!=0")
    if foods:
        for f in foods:
            nm = f['FName']
            food_map[nm] = f['Food_ID']
            food_info[nm] = {"id": f['Food_ID'], "price": float(f['Price'] or 0), "qty": int(f['Quantity'] or 0)}

    # drinks (in stock)
    drinks = execute_query("SELECT Drink_ID, DName, Price, Quantity FROM Drink WHERE Availability='Yes' AND Drink_ID!=0")
    if drinks:
        for d in drinks:
            nm = d['DName']
            drink_map[nm] = d['Drink_ID']
            drink_info[nm] = {"id": d['Drink_ID'], "price": float(d['Price'] or 0), "qty": int(d['Quantity'] or 0)}

    # UI lists
    po_cust_combo['values']  = list(customer_map.keys())
    food_list['values']      = [f"{n}  (₹{food_info[n]['price']:.2f})  [Stock: {food_info[n]['qty']}]" for n in food_info]
    drink_list['values']     = [f"{n}  (₹{drink_info[n]['price']:.2f})  [Stock: {drink_info[n]['qty']}]" for n in drink_info]

def money(x: float) -> str:
    return f"₹{x:,.2f}"

def cart_refresh_view():
    """Refresh cart tree and total label."""
    for i in cart_tree.get_children():
        cart_tree.delete(i)
    total = 0.0
    for it in cart_items:
        sub = it['price'] * it['qty']
        total += sub
        cart_tree.insert(
            "", tk.END,
            values=(it['type'], it['name'], money(it['price']), it['qty'], money(sub))
        )
    order_total_var.set(money(total))

def _extract_name_from_display(display_text: str) -> str:
    # display looks like "Name  (₹123.00)  [Stock: X]"
    # split by "  (" and take left part
    return display_text.split("  (", 1)[0].strip()

def cart_add_item(kind: str):
    """Add selected item (food/drink) with qty from spinbox; merge if exists."""
    if kind == "Food":
        sel = food_list.get()
        if not sel:
            messagebox.showinfo("Select Item", "Select a food from the list.")
            return
        name = _extract_name_from_display(sel)
        if name not in food_info:
            messagebox.showerror("Invalid", "Selected food not available.")
            return
        qty = int(food_qty_spin.get())
        if qty <= 0:
            messagebox.showwarning("Qty", "Quantity must be at least 1.")
            return
        info = food_info[name]
        # stock check (soft check; DB is the final gate)
        if qty > info['qty']:
            if info['qty'] <= 0:
                messagebox.showwarning("Out of Stock", f"'{name}' is out of stock.")
                return
            messagebox.showwarning("Stock", f"Only {info['qty']} left for '{name}'. Adding {info['qty']} instead.")
            qty = info['qty']
        _cart_merge_add("Food", name, info['id'], info['price'], qty)

    elif kind == "Drink":
        sel = drink_list.get()
        if not sel:
            messagebox.showinfo("Select Item", "Select a drink from the list.")
            return
        name = _extract_name_from_display(sel)
        if name not in drink_info:
            messagebox.showerror("Invalid", "Selected drink not available.")
            return
        qty = int(drink_qty_spin.get())
        if qty <= 0:
            messagebox.showwarning("Qty", "Quantity must be at least 1.")
            return
        info = drink_info[name]
        if qty > info['qty']:
            if info['qty'] <= 0:
                messagebox.showwarning("Out of Stock", f"'{name}' is out of stock.")
                return
            messagebox.showwarning("Stock", f"Only {info['qty']} left for '{name}'. Adding {info['qty']} instead.")
            qty = info['qty']
        _cart_merge_add("Drink", name, info['id'], info['price'], qty)

    cart_refresh_view()

def _cart_merge_add(kind, name, _id, price, qty):
    # if exists, just increase qty; else append
    for it in cart_items:
        if it['type']==kind and it['id']==_id:
            it['qty'] += qty
            return
    cart_items.append({"type":kind, "name":name, "id":_id, "price":price, "qty":qty})

def cart_get_selected_index():
    sel = cart_tree.focus()
    if not sel: return None
    vals = cart_tree.item(sel)['values']
    if not vals: return None
    # match by Type + Name
    t, n = vals[0], vals[1]
    for i, it in enumerate(cart_items):
        if it['type']==t and it['name']==n:
            return i
    return None

def cart_inc_qty():
    idx = cart_get_selected_index()
    if idx is None: return
    it = cart_items[idx]
    # stock check
    if it['type']=="Food":
        stock = food_info.get(it['name'],{}).get('qty', 0)
    else:
        stock = drink_info.get(it['name'],{}).get('qty', 0)
    if it['qty'] >= stock:
        messagebox.showwarning("Stock", f"Only {stock} available for '{it['name']}'.")
        return
    it['qty'] += 1
    cart_refresh_view()

def cart_dec_qty():
    idx = cart_get_selected_index()
    if idx is None: return
    it = cart_items[idx]
    if it['qty'] <= 1:
        return
    it['qty'] -= 1
    cart_refresh_view()

def cart_remove():
    idx = cart_get_selected_index()
    if idx is None: return
    cart_items.pop(idx)
    cart_refresh_view()

def reset_cart_ui():
    cart_items.clear()
    cart_refresh_view()
    po_cust_combo.set("")
    po_payment_method_combo.set("")
    # keep selected lists and qty spinners as-is

# ==============================
# EXISTING LISTS / ORDERS
# ==============================
def fetch_all_orders():
    q = """
    SELECT o.Order_ID, c.Cust_Name, p.Amount, p.Method, 
           COALESCE(d.Del_Name, 'Not Assigned') AS Del_Name
    FROM Orders o
    JOIN Customer c ON o.Cust_ID = c.Cust_ID
    LEFT JOIN Payment p ON o.Order_ID = p.Order_ID
    LEFT JOIN Delivery_Incharge d ON o.Order_ID = d.Order_ID
    ORDER BY o.Order_ID DESC
    """
    refresh_treeview(orders_tree, q)

def on_order_select(_e=None):
    sel = orders_tree.focus()
    if not sel:
        return
    vals = orders_tree.item(sel)['values']
    if not vals:
        return
    order_id = vals[0]
    global current_selected_order_id
    current_selected_order_id = order_id

    order_details_text.config(state=tk.NORMAL)
    order_details_text.delete(1.0, tk.END)

    dq = """
    SELECT c.Cust_Name, c.PhoneNo, c.StreetName,
           p.Amount, p.Method,
           di.Del_Name, di.VehicleNumber, di.DelDate, di.DelTime
    FROM Orders o
    JOIN Customer c ON o.Cust_ID = c.Cust_ID
    LEFT JOIN Payment p ON o.Order_ID = p.Order_ID
    LEFT JOIN Delivery_Incharge di ON o.Order_ID = di.Order_ID
    WHERE o.Order_ID=%s
    """
    # show items by joining both tables; ignore 0s
    items_q = """
    SELECT 
        CASE 
            WHEN f.Food_ID IS NOT NULL AND f.Food_ID!=0 THEN f.FName
            ELSE NULL
        END AS FName,
        CASE 
            WHEN d.Drink_ID IS NOT NULL AND d.Drink_ID!=0 THEN d.DName
            ELSE NULL
        END AS DName
    FROM Contains c
    LEFT JOIN Food f  ON c.Food_ID  = f.Food_ID
    LEFT JOIN Drink d ON c.Drink_ID = d.Drink_ID
    WHERE c.Order_ID=%s
    """
    d = execute_query(dq, (order_id,))
    it = execute_query(items_q, (order_id,))
    if not d:
        order_details_text.insert(tk.END, "Could not load order details.")
        order_details_text.config(state=tk.DISABLED)
        return

    d = d[0]
    out = []
    out.append("--- CUSTOMER ---")
    out.append(f"Name:    {d['Cust_Name']}")
    out.append(f"Phone:   {d['PhoneNo']}")
    out.append(f"Address: {d['StreetName']}\n")

    out.append("--- PAYMENT ---")
    if d['Amount'] is not None:
        out.append(f"Status:  Paid ({money(float(d['Amount']))})")
        out.append(f"Method:  {d['Method']}\n")
    else:
        out.append("Status:  Processing...\n")

    out.append("--- DELIVERY ---")
    if d['Del_Name']:
        out.append(f"Driver:  {d['Del_Name']} ({d['VehicleNumber']})")
        out.append(f"Time:    {d['DelDate']} at {d['DelTime']}\n")
    else:
        out.append("Status:  Not Dispatched\n")

    out.append("--- ITEMS ---")
    if it:
        # collapse duplicates for display (since we insert multiple rows for qty)
        counter = {}
        for r in it:
            nm = r['FName'] or r['DName']
            if not nm: 
                continue
            counter[nm] = counter.get(nm, 0) + 1
        for nm, qn in counter.items():
            out.append(f"- {nm}  x{qn}")
    else:
        out.append("No items in this order.")

    order_details_text.insert(tk.END, "\n".join(out))
    order_details_text.config(state=tk.DISABLED)

def assign_driver():
    if current_selected_order_id is None:
        messagebox.showwarning("No Order", "Please select an order from the list first.")
        return
        
    driver_str = driver_combo.get()
    if not driver_str:
        messagebox.showwarning("No Driver", "Please select a driver from the dropdown.")
        return

    # Check if driver is already assigned
    existing = execute_query(
        "SELECT Delivery_ID FROM Delivery_Incharge WHERE Order_ID = %s", 
        (current_selected_order_id,)
    )
    if existing:
        messagebox.showerror("Error", "A driver is already assigned to this order.")
        return

    # Parse the driver name and vehicle
    try:
        driver_name, vehicle_part = driver_str.split(" (")
        vehicle_num = vehicle_part[:-1] # Remove trailing ')'
    except:
        messagebox.showerror("Format Error", "The driver format is incorrect.")
        return

    # Get next Delivery_ID
    next_id_row = execute_query("SELECT COALESCE(MAX(Delivery_ID), 600) + 1 AS id FROM Delivery_Incharge")
    if not next_id_row:
        messagebox.showerror("DB Error", "Could not get next Delivery ID.")
        return
    next_id = next_id_row[0]['id']

    # Get current date and time
    today = date.today()
    now_time = date.strftime(date.today(), "%H:%M:%S")

    # Insert the new delivery record
    ok = execute_query(
        """
        INSERT INTO Delivery_Incharge 
        (Delivery_ID, Del_Name, VehicleNumber, DelDate, DelTime, Order_ID)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (next_id, driver_name, vehicle_num, today, now_time, current_selected_order_id),
        fetch=False
    )
    
    if ok:
        messagebox.showinfo("Success", f"Assigned {driver_name} to Order {current_selected_order_id}.")
        set_status(f"Driver {driver_name} assigned to Order {current_selected_order_id}.")
        # Refresh the order list and details
        fetch_all_orders()
        on_order_select() # Re-run select to update details
    else:
        messagebox.showerror("Error", "Could not assign driver.")
# ==============================
# CUSTOMERS / STAFF / INVENTORY (unchanged behavior)
# ==============================
def refresh_customer_list():
    q = "SELECT Cust_ID, Cust_Name, PhoneNo, Email, Allergy FROM Customer"
    refresh_treeview(customer_tree, q)

def on_customer_select(_e=None):
    sel = customer_tree.focus()
    if not sel:
        return
    vals = customer_tree.item(sel)['values']
    if not vals:
        return
    cust_id = vals[0]
    r = execute_query("SELECT GetCustomerOrderCount(%s) AS c", (cust_id,))
    if r:
        cust_order_count_label.config(text=f"Total Orders for selected customer: {r[0]['c']}")

def add_new_customer():
    name = cust_name_entry.get().strip()
    phone = cust_phone_entry.get().strip()
    email = cust_email_entry.get().strip()
    street = cust_street_entry.get().strip()
    pincode = cust_pincode_entry.get().strip()
    allergy = (cust_allergy_entry.get().strip() or "None")

    if not all([name, phone, email, street, pincode]):
        messagebox.showwarning("Input Error", "Fill all fields except Allergy.")
        return

    nxt = execute_query("SELECT (COALESCE(MAX(Cust_ID),0)+1) AS id FROM Customer")
    next_id = nxt[0]['id']

    ok = execute_query(
        "INSERT INTO Customer (Cust_ID,Cust_Name,PhoneNo,Email,StreetName,Pincode,Allergy) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (next_id, name, phone, email, street, pincode, allergy), fetch=False
    )
    if ok:
        messagebox.showinfo("Success", "Customer added.")
        set_status(f"Customer '{name}' added (ID {next_id}).")
        refresh_customer_list()
        populate_order_dropdowns()
        for e in [cust_name_entry, cust_phone_entry, cust_email_entry, cust_street_entry, cust_pincode_entry, cust_allergy_entry]:
            e.delete(0, tk.END)

def refresh_staff_lists():
    refresh_treeview(chef_tree, "SELECT Chef_ID, Chef_Name, PhoneNo, Email FROM Chef")
    refresh_treeview(emp_tree, "SELECT Emp_ID, Emp_Name, Email, Gender, Salary FROM Employee")
    populate_admin_dropdowns()

def add_new_chef():
    name = chef_name_entry.get().strip()
    phone = chef_phone_entry.get().strip()
    email = chef_email_entry.get().strip()
    street = chef_street_entry.get().strip()
    pincode = chef_pincode_entry.get().strip()
    password = chef_pass_entry.get().strip()

    if not all([name, phone, email, street, pincode, password]):
        messagebox.showwarning("Input Error", "All fields are required.")
        return

    nxt = execute_query("SELECT (COALESCE(MAX(Chef_ID),200)+1) AS id FROM Chef")
    next_id = nxt[0]['id']
    ok = execute_query(
        "INSERT INTO Chef (Chef_ID,Chef_Name,PhoneNo,Email,StreetName,Pincode,Password) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (next_id, name, phone, email, street, pincode, password), fetch=False
    )
    if ok:
        messagebox.showinfo("Success", "Chef added.")
        set_status(f"Chef '{name}' added (ID {next_id}).")
        refresh_staff_lists()
        for e in [chef_name_entry, chef_phone_entry, chef_email_entry, chef_street_entry, chef_pincode_entry, chef_pass_entry]:
            e.delete(0, tk.END)

def add_new_employee():
    name = emp_name_entry.get().strip()
    dob_str = emp_dob_entry.get().strip()
    email = emp_email_entry.get().strip()
    phone = emp_phone_entry.get().strip()
    gender = emp_gender_combo.get().strip()
    address = emp_addr_entry.get().strip()
    salary = emp_salary_entry.get().strip()
    password = emp_pass_entry.get().strip()

    if not all([name, dob_str, email, phone, gender, salary, password]):
        messagebox.showwarning("Input Error", "All fields are required.")
        return
    try:
        dob = date.fromisoformat(dob_str)
        sal = float(salary)
        if sal < 0:
            raise ValueError
    except:
        messagebox.showwarning("Input Error", "Invalid DOB or salary.")
        return

    nxt = execute_query("SELECT (COALESCE(MAX(Emp_ID),100)+1) AS id FROM Employee")
    next_id = nxt[0]['id']
    ok = execute_query(
        "INSERT INTO Employee (Emp_ID,Emp_Name,DOB,Email,PhoneNo,Gender,Address,Salary,Password) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (next_id, name, dob, email, phone, gender, address, sal, password), fetch=False
    )
    if ok:
        messagebox.showinfo("Success", "Employee added.")
        set_status(f"Employee '{name}' added (ID {next_id}).")
        refresh_staff_lists()
        for e in [emp_name_entry, emp_dob_entry, emp_email_entry, emp_phone_entry, emp_addr_entry, emp_salary_entry, emp_pass_entry]:
            e.delete(0, tk.END)
        emp_gender_combo.set("")

# ---------- Inventory (Food/Drink) ----------
def refresh_inventory():
    refresh_treeview(food_tree, "SELECT Food_ID, FName, Price, Quantity, Availability FROM Food WHERE Food_ID!=0")
    refresh_treeview(drink_tree, "SELECT Drink_ID, DName, Price, Quantity, Availability FROM Drink WHERE Drink_ID!=0")
    populate_order_dropdowns()

def refresh_ingredients():
    refresh_treeview(ing_tree, "SELECT Ing_ID, Ing_Name FROM Ingredient")

def add_new_food():
    name = food_name_entry.get().strip()
    price = food_price_entry.get().strip()
    qty = food_qty_entry.get().strip()
    avail = food_avail_var.get()

    if not (name and price and qty):
        messagebox.showwarning("Input Error", "Name, Price and Quantity are required.")
        return
    try:
        price_val = float(price)
        qty_val = int(qty)
    except ValueError:
        messagebox.showwarning("Input Error", "Price must be a number and Quantity must be an integer.")
        return

    existing = execute_query("SELECT Food_ID, Quantity FROM Food WHERE LOWER(FName) = LOWER(%s)", (name,))
    if existing:
        food_id = existing[0]['Food_ID']
        new_qty = existing[0]['Quantity'] + qty_val
        
        # Manually set availability based on the new qty
        avail_status = 'Yes' if new_qty > 0 else 'No'
        
        update_query = "UPDATE Food SET Price=%s, Quantity=%s, Availability=%s WHERE Food_ID=%s"
        execute_query(update_query, (price_val, new_qty, avail_status, food_id), fetch=False)
        messagebox.showinfo("Updated", f"'{name}' already exists. Quantity updated!")
    else:
        next_id = execute_query("SELECT COALESCE(MAX(Food_ID), 300) + 1 AS next_id FROM Food")[0]['next_id']
        
        # Manually set availability based on the new qty
        avail_status = 'Yes' if qty_val > 0 else 'No'

        insert_query = "INSERT INTO Food (Food_ID, FName, Price, Quantity, Availability) VALUES (%s,%s,%s,%s,%s)"
        execute_query(insert_query, (next_id, name, price_val, qty_val, avail_status), fetch=False)
        messagebox.showinfo("Success", f"New food '{name}' added!")

    refresh_inventory()
    for e in [food_name_entry, food_price_entry, food_qty_entry]:
        e.delete(0, tk.END)

def add_new_drink():
    name = drink_name_entry.get().strip()
    price = drink_price_entry.get().strip()
    qty = drink_qty_entry.get().strip()
    # Use 'Yes'/'No' to match the database triggers
    avail = drink_avail_var.get() 

    if not all([name, price, qty]):
        messagebox.showwarning("Input Error", "Name, Price, Quantity are required.")
        return
    try:
        p = float(price)
        q = int(qty)
        if p < 0 or q < 0:
            raise ValueError
    except:
        messagebox.showwarning("Input Error", "Price/Quantity must be non-negative numbers.")
        return

    # --- THIS IS THE NEW LOGIC ---
    existing = execute_query("SELECT Drink_ID, Quantity FROM Drink WHERE LOWER(DName) = LOWER(%s)", (name,))
    if existing:
        drink_id = existing[0]['Drink_ID']
        # Note: We add to existing quantity, not just set it
        new_qty = existing[0]['Quantity'] + q 
        
        # We also need to manually set availability based on the new qty
        # because our trigger is for UPDATE, and this will call the trigger
        avail_status = 'Yes' if new_qty > 0 else 'No' 
        
        update_query = "UPDATE Drink SET Price=%s, Quantity=%s, Availability=%s WHERE Drink_ID=%s"
        ok = execute_query(update_query, (p, new_qty, avail_status, drink_id), fetch=False)
        if ok:
             messagebox.showinfo("Updated", f"'{name}' already exists. Quantity updated!")
             set_status(f"Drink '{name}' quantity updated to {new_qty}.")
    else:
        # This is the original logic for new items
        nxt = execute_query("SELECT (COALESCE(MAX(Drink_ID),400)+1) AS id FROM Drink")
        next_id = nxt[0]['id']
        
        # Manually set availability based on the new qty
        avail_status = 'Yes' if q > 0 else 'No'
        
        ok = execute_query(
            "INSERT INTO Drink (Drink_ID,DName,Price,Quantity,Availability) VALUES (%s,%s,%s,%s,%s)",
            (next_id, name, p, q, avail_status), fetch=False
        )
        if ok:
            messagebox.showinfo("Success", "Drink added.")
            set_status(f"Drink '{name}' added (ID {next_id}) with stock: {q}.")
    
    # Refresh everything
    refresh_inventory()
    for e in [drink_name_entry, drink_price_entry, drink_qty_entry]:
        e.delete(0, tk.END)

def set_item_stock(table: str, id_col: str, item_id: int, in_stock: bool):
    val = "Yes" if in_stock else "No"
    ok = execute_query(f"UPDATE {table} SET Availability=%s WHERE {id_col}=%s", (val, item_id), fetch=False)
    if ok:
        set_status(f"{table[:-1]} ID {item_id} marked {'In Stock' if in_stock else 'Out of Stock'}.")
        refresh_inventory()

def stock_toggle_from_tree(tree, table, id_col, make_in_stock: bool):
    sel = tree.focus()
    if not sel:
        messagebox.showinfo("Select Row", "Select an item first.")
        return
    vals = tree.item(sel)['values']
    if not vals:
        return
    item_id = vals[0]
    set_item_stock(table, id_col, item_id, make_in_stock)

# ---------- Admin Dropdown Linking ----------
def populate_admin_dropdowns():
    chef_map.clear(); ingredient_map.clear(); employee_map.clear()

    chefs = execute_query("SELECT Chef_ID, Chef_Name FROM Chef")
    if chefs:
        for c in chefs:
            chef_map[c['Chef_Name']] = c['Chef_ID']
    ingredients = execute_query("SELECT Ing_ID, Ing_Name FROM Ingredient")
    if ingredients:
        for i in ingredients:
            ingredient_map[i['Ing_Name']] = i['Ing_ID']
    foods = execute_query("SELECT Food_ID, FName FROM Food")
    if foods:
        food_map_admin = {f['FName']: f['Food_ID'] for f in foods}
        link_food_combo['values'] = list(food_map_admin.keys())
        link_food_combo.food_map_admin = food_map_admin
    employees = execute_query("SELECT Emp_ID, Emp_Name FROM Employee")
    if employees:
        for e in employees:
            employee_map[e['Emp_Name']] = e['Emp_ID']
    customers = execute_query("SELECT Cust_ID, Cust_Name FROM Customer")
    if customers:
        link_cust_combo['values'] = [c['Cust_Name'] for c in customers]
        link_cust_combo.cust_map = {c['Cust_Name']: c['Cust_ID'] for c in customers}

    link_chef_combo['values'] = list(chef_map.keys())
    link_ing_combo['values'] = list(ingredient_map.keys())
    link_emp_combo['values'] = list(employee_map.keys())
    cuisine_chef_combo['values'] = list(chef_map.keys())

def add_link_prep():
    food_name = link_food_combo.get().strip()
    chef_name = link_chef_combo.get().strip()
    if not (food_name and chef_name):
        messagebox.showwarning("Input Error", "Select Food and Chef.")
        return
    food_id = link_food_combo.food_map_admin.get(food_name)
    chef_id = chef_map.get(chef_name)
    if execute_query("INSERT INTO Prepared_by (Food_ID,Chef_ID) VALUES (%s,%s)", (food_id, chef_id), fetch=False):
        set_status(f"Assigned '{food_name}' to Chef '{chef_name}'.")
        refresh_link_views()

def add_link_uses():
    chef_name = link_chef_combo.get().strip()
    ing_name = link_ing_combo.get().strip()
    if not (chef_name and ing_name):
        messagebox.showwarning("Input Error", "Select Chef and Ingredient.")
        return
    chef_id = chef_map.get(chef_name)
    ing_id = ingredient_map.get(ing_name)
    if execute_query("INSERT INTO Uses (Chef_ID,Ing_ID) VALUES (%s,%s)", (chef_id, ing_id), fetch=False):
        set_status(f"Ingredient '{ing_name}' assigned to Chef '{chef_name}'.")
        refresh_link_views()

def add_link_corporate():
    cust_name = link_cust_combo.get().strip()
    emp_name  = link_emp_combo.get().strip()
    if not (cust_name and emp_name):
        messagebox.showwarning("Input Error", "Select Customer and Employee.")
        return
    cust_id = link_cust_combo.cust_map.get(cust_name)
    emp_id  = employee_map.get(emp_name)
    if execute_query("INSERT INTO Works_For (Cust_ID,Emp_ID) VALUES (%s,%s)", (cust_id, emp_id), fetch=False):
        set_status(f"Customer '{cust_name}' assigned to Employee '{emp_name}'.")
        refresh_link_views()

def add_cuisine_link():
    chef_name = cuisine_chef_combo.get().strip()
    cuisine_name = cuisine_name_entry.get().strip()
    if not (chef_name and cuisine_name):
        messagebox.showwarning("Input Error", "Select Chef and enter Cuisine.")
        return
    chef_id = chef_map.get(chef_name)
    nxt = execute_query("SELECT (COALESCE(MAX(Cuisine_ID),500)+1) AS id FROM Cuisine")
    next_id = nxt[0]['id']
    if execute_query("INSERT INTO Cuisine (Cuisine_ID,Chef_ID,Cuisine_Name) VALUES (%s,%s,%s)",
                     (next_id, chef_id, cuisine_name), fetch=False):
        set_status(f"Chef '{chef_name}' specialty added: {cuisine_name}.")
        cuisine_name_entry.delete(0, tk.END)
        cuisine_chef_combo.set("")
        refresh_link_views()

def refresh_link_views():
    refresh_treeview(link_cuisine_tree, """
        SELECT c.Cuisine_Name, ch.Chef_Name
        FROM Cuisine c JOIN Chef ch ON c.Chef_ID = ch.Chef_ID
    """)
    refresh_treeview(link_prep_tree, """
        SELECT f.FName, ch.Chef_Name
        FROM Prepared_by p
        JOIN Food f ON p.Food_ID = f.Food_ID
        JOIN Chef ch ON p.Chef_ID = ch.Chef_ID
    """)
    refresh_treeview(link_uses_tree, """
        SELECT ch.Chef_Name, i.Ing_Name
        FROM Uses u
        JOIN Chef ch ON u.Chef_ID = ch.Chef_ID
        JOIN Ingredient i ON u.Ing_ID = i.Ing_ID
    """)
    refresh_treeview(link_works_tree, """
        SELECT c.Cust_Name, e.Emp_Name
        FROM Works_For w
        JOIN Customer c ON w.Cust_ID = c.Cust_ID
        JOIN Employee e ON w.Emp_ID = e.Emp_ID
    """)

# ==============================
# PLACE ORDER (CART → DB)  **NO SQL CHANGES NEEDED**
# ==============================
def place_order():
    cust_name = po_cust_combo.get().strip()
    paym      = po_payment_method_combo.get().strip()

    if not cust_name:
        messagebox.showwarning("Input", "Please select a customer.")
        return
    if not cart_items:
        messagebox.showwarning("Cart", "Cart is empty. Add items first.")
        return
    if not paym:
        messagebox.showwarning("Payment", "Select a payment method.")
        return

    cust_id = customer_map.get(cust_name)
    if cust_id is None:
        messagebox.showerror("Selection Error", "Invalid customer.")
        return

    # Create order manually (like your procedure), then insert Contains rows per quantity, then Payment.
    cn = get_db_connection()
    if cn is None: return
    try:
        cur = cn.cursor()

        # Next IDs
        cur.execute("SELECT COALESCE(MAX(Order_ID),1000)+1 FROM Orders")
        new_order_id = cur.fetchone()[0]

        cur.execute("SELECT COALESCE(MAX(Payment_ID),700)+1 FROM Payment")
        new_payment_id = cur.fetchone()[0]

        # Orders: Quantity = total items count (sum of qty) for reference
        tot_items = sum(it['qty'] for it in cart_items)
        cur.execute("INSERT INTO Orders (Order_ID, Quantity, Cust_ID) VALUES (%s,%s,%s)",
                    (new_order_id, tot_items, cust_id))

        # Contains: insert one row per qty (works with your existing triggers)
        for it in cart_items:
            if it['type']=="Food":
                for _ in range(it['qty']):
                    cur.execute("INSERT INTO Contains (Order_ID, Food_ID, Drink_ID) VALUES (%s,%s,%s)",
                                (new_order_id, it['id'], 0))
            else:
                for _ in range(it['qty']):
                    cur.execute("INSERT INTO Contains (Order_ID, Food_ID, Drink_ID) VALUES (%s,%s,%s)",
                                (new_order_id, 0, it['id']))

        # Payment: Amount will be auto-set by your BEFORE INSERT trigger
        cur.execute("INSERT INTO Payment (Payment_ID, Method, Order_ID, Amount) VALUES (%s,%s,%s,%s)",
                    (new_payment_id, paym, new_order_id, 0))

        cn.commit()
        messagebox.showinfo("Success", f"Order {new_order_id} placed.")
        set_status(f"Order {new_order_id} placed. Method: {paym}")

    except mysql.connector.Error as err:
        cn.rollback()
        messagebox.showerror("Order Error", f"{err}")
        return
    finally:
        try: cur.close()
        except: pass
        cn.close()

    # Refresh UI & inventory
    reset_cart_ui()
    fetch_all_orders()
    refresh_inventory()

# ==============================
# UI
# ==============================
root = tk.Tk()
root.title("Food Delivery Management System")
root.geometry("1200x860")
sv_ttk.set_theme("light")

HEADING_FONT = font.Font(family="Segoe UI", size=14, weight="bold")
BODY_FONT    = font.Font(family="Segoe UI", size=11)
BUTTON_FONT  = font.Font(family="Segoe UI", size=11, weight="bold")

style = ttk.Style()
style.configure("TNotebook.Tab", font=font.Font(family="Segoe UI", size=12, weight="bold"), padding=[10,5])
style.configure("Treeview.Heading", font=font.Font(family="Segoe UI", size=12, weight="bold"))
style.configure("Treeview", rowheight=28, font=BODY_FONT)
style.configure("TLabelframe.Label", font=HEADING_FONT, padding=[10,5])
style.configure("TButton", font=BUTTON_FONT, padding=10)
style.configure("TLabel", font=BODY_FONT)
style.configure("TEntry", font=BODY_FONT, padding=5)
style.configure("TCombobox", font=BODY_FONT, padding=5)

# icons optional
try:
    icon_dashboard = ImageTk.PhotoImage(Image.open("dashboard.png").resize((24,24)))
    icon_new_order = ImageTk.PhotoImage(Image.open("new_order.png").resize((24,24)))
    icon_customer  = ImageTk.PhotoImage(Image.open("customer.png").resize((24,24)))
    icon_staff     = ImageTk.PhotoImage(Image.open("staff.png").resize((24,24)))
    icon_menu      = ImageTk.PhotoImage(Image.open("menu.png").resize((24,24)))
    icon_admin     = ImageTk.PhotoImage(Image.open("admin.png").resize((24,24)))
except:
    icon_dashboard = icon_new_order = icon_customer = icon_staff = icon_menu = icon_admin = None

tabControl = ttk.Notebook(root)
tab1 = ttk.Frame(tabControl, padding=10)
tab2 = ttk.Frame(tabControl, padding=10)
tab3 = ttk.Frame(tabControl, padding=10)
tab4 = ttk.Frame(tabControl, padding=10)
tab5 = ttk.Frame(tabControl, padding=10)
tab6 = ttk.Frame(tabControl, padding=10)
for frame, text, icon in [
    (tab1, 'Dashboard', icon_dashboard),
    (tab2, 'New Order', icon_new_order),
    (tab3, 'Customers', icon_customer),
    (tab4, 'Staff', icon_staff),
    (tab5, 'Menu', icon_menu),
    (tab6, 'Admin', icon_admin)
]:
    if icon:
        tabControl.add(frame, text=text, image=icon, compound=tk.LEFT)
    else:
        tabControl.add(frame, text=text)
tabControl.pack(expand=1, fill="both")

# ----- Dashboard -----
dash_frame = ttk.Frame(tab1, padding="10")
dash_frame.pack(fill="both", expand=True)
ttk.Button(dash_frame, text="Refresh Order List", command=fetch_all_orders).pack(pady=10)
paned = ttk.PanedWindow(dash_frame, orient=tk.HORIZONTAL); paned.pack(fill="both", expand=True)
order_list_frame = ttk.Frame(paned, padding="5")
order_cols = ("Order ID","Customer","Amount","Method","Driver")
orders_tree = ttk.Treeview(order_list_frame, columns=order_cols, show="headings")
for c in order_cols: 
    orders_tree.heading(c, text=c)
    orders_tree.column(c, anchor=tk.CENTER) # Apply to all
orders_tree.column("Order ID", width=90, anchor=tk.CENTER)
orders_tree.pack(fill="both", expand=True)
paned.add(order_list_frame, weight=3)
detail_frame = ttk.LabelFrame(paned, text="Order Details", padding=10)
order_details_text = tk.Text(detail_frame, height=20, width=50, font=("Consolas", 11), state=tk.DISABLED, relief=tk.FLAT)
order_details_text.pack(fill="both", expand=True)
paned.add(detail_frame, weight=2)
# --- ADD THIS NEW SECTION FOR ASSIGNING DRIVERS ---
assign_frame = ttk.Frame(detail_frame, padding=(0, 10))
assign_frame.pack(fill="x", side=tk.BOTTOM)

ttk.Label(assign_frame, text="Assign Driver:", font=BUTTON_FONT).pack(side=tk.LEFT, padx=(0, 6))

driver_combo = ttk.Combobox(assign_frame, state="readonly", width=25, font=BODY_FONT)
driver_combo['values'] = [
    "Delivery Dave (KA-01-1234)",
    "Rider Rita (KA-02-5678)",
    "Speedy Sam (KA-03-9999)",
    "Quick Qadir (KA-04-5555)"
]
driver_combo.pack(side=tk.LEFT, fill="x", expand=True, padx=6)

assign_driver_btn = ttk.Button(
    assign_frame, 
    text="Assign", 
    command=lambda: assign_driver(), 
    style="Accent.TButton"
)
assign_driver_btn.pack(side=tk.LEFT)
# --- END OF NEW SECTION ---

orders_tree.bind("<<TreeviewSelect>>", on_order_select)

# ----- New Order (CART UI) -----
po_frame = ttk.Frame(tab2, padding=18)
po_frame.pack(fill="both", expand=True)
po_frame.columnconfigure(1, weight=1)
ttk.Label(po_frame, text="Create a New Order", font=HEADING_FONT).grid(row=0, column=0, columnspan=4, pady=(0,12))

# row 1: customer + payment
ttk.Label(po_frame, text="Customer:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
po_cust_combo = ttk.Combobox(po_frame, state="readonly", width=38); po_cust_combo.grid(row=1, column=1, sticky="w", pady=6)
ttk.Label(po_frame, text="Payment:").grid(row=1, column=2, sticky="e", padx=6, pady=6)
po_payment_method_combo = ttk.Combobox(po_frame, values=["Cash","Card","UPI","Net Banking"], state="readonly", width=32)
po_payment_method_combo.grid(row=1, column=3, sticky="w", pady=6)

# row 2-3: food list + qty + add
food_box = ttk.LabelFrame(po_frame, text="Food", padding=10)
food_box.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0,8), pady=8)
food_box.columnconfigure(0, weight=1)
food_list = ttk.Combobox(food_box, state="readonly", width=60)
food_list.grid(row=0, column=0, columnspan=3, sticky="ew", pady=4)
ttk.Label(food_box, text="Qty:").grid(row=1, column=0, sticky="e")
food_qty_spin = ttk.Spinbox(food_box, from_=1, to=99, width=6); food_qty_spin.set(1); food_qty_spin.grid(row=1, column=1, sticky="w", padx=6)
ttk.Button(food_box, text="Add Food to Cart", command=lambda: cart_add_item("Food")).grid(row=1, column=2, sticky="w", padx=6)

drink_box = ttk.LabelFrame(po_frame, text="Drink", padding=10)
drink_box.grid(row=2, column=2, columnspan=2, sticky="nsew", padx=(8,0), pady=8)
drink_box.columnconfigure(0, weight=1)
drink_list = ttk.Combobox(drink_box, state="readonly", width=60)
drink_list.grid(row=0, column=0, columnspan=3, sticky="ew", pady=4)
ttk.Label(drink_box, text="Qty:").grid(row=1, column=0, sticky="e")
drink_qty_spin = ttk.Spinbox(drink_box, from_=1, to=99, width=6); drink_qty_spin.set(1); drink_qty_spin.grid(row=1, column=1, sticky="w", padx=6)
ttk.Button(drink_box, text="Add Drink to Cart", command=lambda: cart_add_item("Drink")).grid(row=1, column=2, sticky="w", padx=6)

# row 4: cart table + controls
cart_frame = ttk.LabelFrame(po_frame, text="Cart", padding=10)
cart_frame.grid(row=3, column=0, columnspan=4, sticky="nsew", pady=8)
cart_cols = ("Type","Item","Price","Qty","Subtotal")
cart_tree = ttk.Treeview(cart_frame, columns=cart_cols, show="headings", height=8)
for c in cart_cols:
    cart_tree.heading(c, text=c)
cart_tree.column("Type", width=80, anchor=tk.CENTER)
cart_tree.column("Item", width=320, anchor=tk.CENTER)
cart_tree.column("Price", width=100, anchor=tk.CENTER)
cart_tree.column("Qty", width=60, anchor=tk.CENTER)
cart_tree.column("Subtotal", width=120, anchor=tk.CENTER)
cart_tree.pack(fill="both", expand=True)

ctrls = ttk.Frame(cart_frame); ctrls.pack(pady=6)
ttk.Button(ctrls, text="+  Increase Qty", command=cart_inc_qty).grid(row=0, column=0, padx=4)
ttk.Button(ctrls, text="-  Decrease Qty", command=cart_dec_qty).grid(row=0, column=1, padx=4)
ttk.Button(ctrls, text="Remove Item", command=cart_remove).grid(row=0, column=2, padx=4)
order_total_var = tk.StringVar(value="₹0.00")
ttk.Label(ctrls, text="Total:", font=HEADING_FONT).grid(row=0, column=3, padx=(16,6))
ttk.Label(ctrls, textvariable=order_total_var, font=HEADING_FONT).grid(row=0, column=4, padx=6)

# row 5: actions
act = ttk.Frame(po_frame); act.grid(row=4, column=0, columnspan=4, pady=8)
ttk.Button(act, text="Place Order", style="Accent.TButton", command=place_order).grid(row=0, column=0, padx=6)
ttk.Button(act, text="Clear Cart", command=reset_cart_ui).grid(row=0, column=1, padx=6)

# ----- Customers -----
cust_frame = ttk.Frame(tab3, padding=10); cust_frame.pack(fill="both", expand=True)
cust_pw = ttk.PanedWindow(cust_frame, orient=tk.VERTICAL); cust_pw.pack(fill="both", expand=True)

cust_add_frame = ttk.LabelFrame(cust_pw, text="Add New Customer", padding=10)
form = ttk.Frame(cust_add_frame); form.pack(pady=8)
ttk.Label(form, text="Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
cust_name_entry = ttk.Entry(form, width=30); cust_name_entry.grid(row=0, column=1)
ttk.Label(form, text="Phone:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
cust_phone_entry = ttk.Entry(form, width=30); cust_phone_entry.grid(row=0, column=3)
ttk.Label(form, text="Email:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
cust_email_entry = ttk.Entry(form, width=30); cust_email_entry.grid(row=1, column=1)
ttk.Label(form, text="Street:").grid(row=1, column=2, sticky="e", padx=5, pady=5)
cust_street_entry = ttk.Entry(form, width=30); cust_street_entry.grid(row=1, column=3)
ttk.Label(form, text="Pincode:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
cust_pincode_entry = ttk.Entry(form, width=30); cust_pincode_entry.grid(row=2, column=1)
ttk.Label(form, text="Allergy:").grid(row=2, column=2, sticky="e", padx=5, pady=5)
cust_allergy_entry = ttk.Entry(form, width=30); cust_allergy_entry.grid(row=2, column=3)
ttk.Button(cust_add_frame, text="Add Customer", command=add_new_customer).pack(pady=8)
cust_pw.add(cust_add_frame, weight=0)

cust_list_frame = ttk.LabelFrame(cust_pw, text="All Customers", padding=10)
ttk.Button(cust_list_frame, text="Refresh List", command=refresh_customer_list).pack(anchor="w", pady=5)
cust_order_count_label = ttk.Label(cust_list_frame, text="Click a customer to see their total order count.", font=font.Font(family="Segoe UI", size=11, slant="italic"))
cust_order_count_label.pack(anchor="w", pady=5)
cust_cols = ("ID","Name","Phone","Email","Allergy")
customer_tree = ttk.Treeview(cust_list_frame, columns=cust_cols, show="headings")
for c in cust_cols: 
    customer_tree.heading(c, text=c)
    customer_tree.column(c, anchor=tk.CENTER) # Apply to all
customer_tree.column("ID", width=60, anchor=tk.CENTER)
customer_tree.pack(fill="both", expand=True)
customer_tree.bind("<<TreeviewSelect>>", on_customer_select)
cust_pw.add(cust_list_frame, weight=1)

# ----- Staff -----
staff_frame = ttk.Frame(tab4, padding=10); staff_frame.pack(fill="both", expand=True)
ttk.Button(staff_frame, text="Refresh Both Lists", command=refresh_staff_lists).pack(pady=5)
staff_pw = ttk.PanedWindow(staff_frame, orient=tk.HORIZONTAL); staff_pw.pack(fill="both", expand=True)

chef_frame = ttk.LabelFrame(staff_pw, text="Chefs", padding=10)
chef_cols = ("ID","Name","Phone","Email")
chef_tree = ttk.Treeview(chef_frame, columns=chef_cols, show="headings", height=5)
for c in chef_cols: 
    chef_tree.heading(c, text=c)
    chef_tree.column(c, anchor=tk.CENTER) # Apply to all
chef_tree.column("ID", width=60, anchor=tk.CENTER); chef_tree.pack(fill="x", pady=5)
f = ttk.Frame(chef_frame); f.pack(pady=5)
ttk.Label(f, text="Name:").grid(row=0, column=0, sticky="e", pady=3); chef_name_entry = ttk.Entry(f); chef_name_entry.grid(row=0, column=1, padx=5)
ttk.Label(f, text="Phone:").grid(row=1, column=0, sticky="e", pady=3); chef_phone_entry = ttk.Entry(f); chef_phone_entry.grid(row=1, column=1, padx=5)
ttk.Label(f, text="Email:").grid(row=2, column=0, sticky="e", pady=3); chef_email_entry = ttk.Entry(f); chef_email_entry.grid(row=2, column=1, padx=5)
ttk.Label(f, text="Street:").grid(row=3, column=0, sticky="e", pady=3); chef_street_entry = ttk.Entry(f); chef_street_entry.grid(row=3, column=1, padx=5)
ttk.Label(f, text="Pincode:").grid(row=4, column=0, sticky="e", pady=3); chef_pincode_entry = ttk.Entry(f); chef_pincode_entry.grid(row=4, column=1, padx=5)
ttk.Label(f, text="Password:").grid(row=5, column=0, sticky="e", pady=3); chef_pass_entry = ttk.Entry(f, show="*"); chef_pass_entry.grid(row=5, column=1, padx=5)
ttk.Button(f, text="Add Chef", command=add_new_chef).grid(row=6, column=0, columnspan=2, pady=8)
staff_pw.add(chef_frame, weight=1)

emp_frame = ttk.LabelFrame(staff_pw, text="Admin Staff", padding=10)
emp_cols = ("ID","Name","Email","Gender","Salary")
emp_tree = ttk.Treeview(emp_frame, columns=emp_cols, show="headings", height=5)
for c in emp_cols: 
    emp_tree.heading(c, text=c)
    emp_tree.column(c, anchor=tk.CENTER) # Apply to all
emp_tree.column("ID", width=60, anchor=tk.CENTER); emp_tree.pack(fill="x", pady=5)
f2 = ttk.Frame(emp_frame); f2.pack(pady=5)
ttk.Label(f2, text="Name:").grid(row=0, column=0, sticky="e", pady=3); emp_name_entry = ttk.Entry(f2); emp_name_entry.grid(row=0, column=1, padx=5)
ttk.Label(f2, text="DOB (YYYY-MM-DD):").grid(row=1, column=0, sticky="e", pady=3); emp_dob_entry = ttk.Entry(f2); emp_dob_entry.grid(row=1, column=1, padx=5)
ttk.Label(f2, text="Email:").grid(row=2, column=0, sticky="e", pady=3); emp_email_entry = ttk.Entry(f2); emp_email_entry.grid(row=2, column=1, padx=5)
ttk.Label(f2, text="Phone:").grid(row=3, column=0, sticky="e", pady=3); emp_phone_entry = ttk.Entry(f2); emp_phone_entry.grid(row=3, column=1, padx=5)
ttk.Label(f2, text="Gender:").grid(row=4, column=0, sticky="e", pady=3); emp_gender_combo = ttk.Combobox(f2, values=["Male","Female","Other"], state="readonly"); emp_gender_combo.grid(row=4, column=1, padx=5)
ttk.Label(f2, text="Address:").grid(row=5, column=0, sticky="e", pady=3); emp_addr_entry = ttk.Entry(f2); emp_addr_entry.grid(row=5, column=1, padx=5)
ttk.Label(f2, text="Salary:").grid(row=6, column=0, sticky="e", pady=3); emp_salary_entry = ttk.Entry(f2); emp_salary_entry.grid(row=6, column=1, padx=5)
ttk.Label(f2, text="Password:").grid(row=7, column=0, sticky="e", pady=3); emp_pass_entry = ttk.Entry(f2, show="*"); emp_pass_entry.grid(row=7, column=1, padx=5)
ttk.Button(f2, text="Add Employee", command=add_new_employee).grid(row=8, column=0, columnspan=2, pady=8)
staff_pw.add(emp_frame, weight=1)

# ----- Menu / Inventory -----
menu_frame = ttk.Frame(tab5, padding=10); menu_frame.pack(fill="both", expand=True)
menu_pw = ttk.PanedWindow(menu_frame, orient=tk.VERTICAL); menu_pw.pack(fill="both", expand=True)

lists = ttk.Frame(menu_pw)
ttk.Button(lists, text="Refresh Inventory Lists", command=refresh_inventory).pack(pady=5)
hpw = ttk.PanedWindow(lists, orient=tk.HORIZONTAL); hpw.pack(fill="both", expand=True)

food_list_frame = ttk.LabelFrame(hpw, text="Food Items", padding=8)
food_cols = ("ID","Name","Price","Qty","Available")
food_tree = ttk.Treeview(food_list_frame, columns=food_cols, show="headings", height=8)
for c in food_cols: 
    food_tree.heading(c, text=c)
    food_tree.column(c, anchor=tk.CENTER) # Apply to all
food_tree.pack(fill="both", expand=True)
btns = ttk.Frame(food_list_frame); btns.pack(pady=6)
ttk.Button(btns, text="Mark In Stock",  command=lambda: stock_toggle_from_tree(food_tree,"Food","Food_ID",True)).grid(row=0, column=0, padx=4)
ttk.Button(btns, text="Mark Out of Stock", command=lambda: stock_toggle_from_tree(food_tree,"Food","Food_ID",False)).grid(row=0, column=1, padx=4)
hpw.add(food_list_frame, weight=1)

drink_list_frame = ttk.LabelFrame(hpw, text="Drink Items", padding=8)
drink_cols = ("ID","Name","Price","Qty","Available")
drink_tree = ttk.Treeview(drink_list_frame, columns=drink_cols, show="headings", height=8)
for c in drink_cols: 
    drink_tree.heading(c, text=c)
    drink_tree.column(c, anchor=tk.CENTER) # Apply to all
drink_tree.pack(fill="both", expand=True)
btns2 = ttk.Frame(drink_list_frame); btns2.pack(pady=6)
ttk.Button(btns2, text="Mark In Stock",  command=lambda: stock_toggle_from_tree(drink_tree,"Drink","Drink_ID",True)).grid(row=0, column=0, padx=4)
ttk.Button(btns2, text="Mark Out of Stock", command=lambda: stock_toggle_from_tree(drink_tree,"Drink","Drink_ID",False)).grid(row=0, column=1, padx=4)
hpw.add(drink_list_frame, weight=1)

menu_pw.add(lists, weight=1)

addwrap = ttk.Frame(menu_pw)
addpw = ttk.PanedWindow(addwrap, orient=tk.HORIZONTAL); addpw.pack(fill="both", expand=True, pady=10)

add_food_frame = ttk.LabelFrame(addpw, text="Add New Food", padding=10)
ttk.Label(add_food_frame, text="Name:").grid(row=0, column=0, sticky="e");     food_name_entry = ttk.Entry(add_food_frame); food_name_entry.grid(row=0, column=1, padx=5, pady=2)
ttk.Label(add_food_frame, text="Price:").grid(row=1, column=0, sticky="e");    food_price_entry = ttk.Entry(add_food_frame); food_price_entry.grid(row=1, column=1, padx=5, pady=2)
ttk.Label(add_food_frame, text="Quantity:").grid(row=2, column=0, sticky="e"); food_qty_entry = ttk.Entry(add_food_frame); food_qty_entry.grid(row=2, column=1, padx=5, pady=2)
food_avail_var = tk.StringVar(value="Yes")
ttk.Radiobutton(add_food_frame, text="In Stock",  variable=food_avail_var, value="Yes").grid(row=3, column=0, pady=4)
ttk.Radiobutton(add_food_frame, text="Out of Stock", variable=food_avail_var, value="No").grid(row=3, column=1, pady=4)
ttk.Button(add_food_frame, text="Add Food", command=add_new_food).grid(row=4, column=0, columnspan=2, pady=8)
addpw.add(add_food_frame, weight=1)

add_drink_frame = ttk.LabelFrame(addpw, text="Add New Drink", padding=10)
ttk.Label(add_drink_frame, text="Name:").grid(row=0, column=0, sticky="e");     drink_name_entry = ttk.Entry(add_drink_frame); drink_name_entry.grid(row=0, column=1, padx=5, pady=2)
ttk.Label(add_drink_frame, text="Price:").grid(row=1, column=0, sticky="e");    drink_price_entry = ttk.Entry(add_drink_frame); drink_price_entry.grid(row=1, column=1, padx=5, pady=2)
ttk.Label(add_drink_frame, text="Quantity:").grid(row=2, column=0, sticky="e"); drink_qty_entry = ttk.Entry(add_drink_frame); drink_qty_entry.grid(row=2, column=1, padx=5, pady=2)
drink_avail_var = tk.StringVar(value="Yes")
ttk.Radiobutton(add_drink_frame, text="In Stock",  variable=drink_avail_var, value="Yes").grid(row=3, column=0, pady=4)
ttk.Radiobutton(add_drink_frame, text="Out of Stock", variable=drink_avail_var, value="No").grid(row=3, column=1, pady=4)
ttk.Button(add_drink_frame, text="Add Drink", command=add_new_drink).grid(row=4, column=0, columnspan=2, pady=8)
addpw.add(add_drink_frame, weight=1)

add_ing_frame = ttk.LabelFrame(addpw, text="Ingredients", padding=10)
ttk.Label(add_ing_frame, text="Name:").grid(row=0, column=0, sticky="e"); ing_name_entry = ttk.Entry(add_ing_frame); ing_name_entry.grid(row=0, column=1, padx=5, pady=2)
ttk.Button(add_ing_frame, text="Add Ingredient", command=refresh_ingredients).grid(row=1, column=0, columnspan=2, pady=8)
ing_tree_frame = ttk.Frame(add_ing_frame); ing_tree_frame.grid(row=2, column=0, columnspan=2, pady=5)
ing_cols = ("ID","Name")
ing_tree = ttk.Treeview(ing_tree_frame, columns=ing_cols, show="headings", height=5)
for c in ing_cols: 
    ing_tree.heading(c, text=c)
    ing_tree.column(c, anchor=tk.CENTER) # Apply to all
ing_tree.column("ID", width=60, anchor=tk.CENTER); ing_tree.pack(fill="x")
ttk.Button(add_ing_frame, text="Refresh List", command=refresh_ingredients).grid(row=3, column=0, columnspan=2, pady=8)
addpw.add(add_ing_frame, weight=1)

menu_pw.add(addwrap, weight=0)

# ----- Admin (linking) -----
links_frame = ttk.Frame(tab6, padding=10); links_frame.pack(fill="both", expand=True)
ttk.Button(links_frame, text="Refresh All Views", command=lambda: [refresh_link_views(), populate_admin_dropdowns()]).pack(pady=5)

links_pw = ttk.PanedWindow(links_frame, orient=tk.VERTICAL); links_pw.pack(fill="both", expand=True)

links_add_frame = ttk.Frame(links_pw)
addh = ttk.PanedWindow(links_add_frame, orient=tk.HORIZONTAL); addh.pack(fill="both", expand=True)

left = ttk.LabelFrame(addh, text="Assignments (Dropdowns)", padding=10)
ttk.Label(left, text="Food:").grid(row=0, column=0, sticky="e", pady=3); link_food_combo = ttk.Combobox(left, state="readonly", width=25); link_food_combo.grid(row=0, column=1, padx=5)
ttk.Label(left, text="Chef:").grid(row=1, column=0, sticky="e", pady=3); link_chef_combo = ttk.Combobox(left, state="readonly", width=25); link_chef_combo.grid(row=1, column=1, padx=5)
ttk.Button(left, text="Assign Food → Chef", command=add_link_prep).grid(row=2, column=0, columnspan=2, pady=6, sticky="ew")

ttk.Label(left, text="Ingredient:").grid(row=3, column=0, sticky="e", pady=3); link_ing_combo = ttk.Combobox(left, state="readonly", width=25); link_ing_combo.grid(row=3, column=1, padx=5)
ttk.Button(left, text="Assign Ingredient → Chef", command=add_link_uses).grid(row=4, column=0, columnspan=2, pady=6, sticky="ew")

ttk.Label(left, text="Customer:").grid(row=5, column=0, sticky="e", pady=3); link_cust_combo = ttk.Combobox(left, state="readonly", width=25); link_cust_combo.grid(row=5, column=1, padx=5)
ttk.Label(left, text="Employee:").grid(row=6, column=0, sticky="e", pady=3); link_emp_combo = ttk.Combobox(left, state="readonly", width=25); link_emp_combo.grid(row=6, column=1, padx=5)
ttk.Button(left, text="Assign Corporate Account", command=add_link_corporate).grid(row=7, column=0, columnspan=2, pady=6, sticky="ew")
addh.add(left, weight=1)

right = ttk.LabelFrame(addh, text="Assign Chef Specialty", padding=10)
ttk.Label(right, text="Chef:").grid(row=0, column=0, sticky="e", pady=3); cuisine_chef_combo = ttk.Combobox(right, state="readonly", width=25); cuisine_chef_combo.grid(row=0, column=1, padx=5)
ttk.Label(right, text="Cuisine Name:").grid(row=1, column=0, sticky="e", pady=3); cuisine_name_entry = ttk.Entry(right, width=27); cuisine_name_entry.grid(row=1, column=1, padx=5)
ttk.Button(right, text="Assign Cuisine", command=add_cuisine_link).grid(row=2, column=0, columnspan=2, pady=6, sticky="ew")
addh.add(right, weight=1)

links_pw.add(links_add_frame, weight=0)

views = ttk.Frame(links_pw)
vpan = ttk.PanedWindow(views, orient=tk.HORIZONTAL); vpan.pack(fill="both", expand=True, pady=10)

f1 = ttk.LabelFrame(vpan, text="Chef's Specialties", padding=5)
link_cuisine_tree = ttk.Treeview(f1, columns=("Cuisine","Chef"), show="headings", height=6)
link_cuisine_tree.heading("Cuisine", text="Cuisine"); link_cuisine_tree.column("Cuisine", anchor=tk.CENTER)
link_cuisine_tree.heading("Chef", text="Chef"); link_cuisine_tree.column("Chef", anchor=tk.CENTER)
link_cuisine_tree.pack(fill="both", expand=True)
vpan.add(f1, weight=1)

f2 = ttk.LabelFrame(vpan, text="Who Prepares What", padding=5)
link_prep_tree = ttk.Treeview(f2, columns=("Food","Chef"), show="headings", height=6)
link_prep_tree.heading("Food", text="Food"); link_prep_tree.column("Food", anchor=tk.CENTER)
link_prep_tree.heading("Chef", text="Chef"); link_prep_tree.column("Chef", anchor=tk.CENTER)
link_prep_tree.pack(fill="both", expand=True)
vpan.add(f2, weight=1)

f3 = ttk.LabelFrame(vpan, text="Chef's Ingredients", padding=5)
link_uses_tree = ttk.Treeview(f3, columns=("Chef","Ingredient"), show="headings", height=6)
link_uses_tree.heading("Chef", text="Chef"); link_uses_tree.column("Chef", anchor=tk.CENTER)
link_uses_tree.heading("Ingredient", text="Ingredient"); link_uses_tree.column("Ingredient", anchor=tk.CENTER)
link_uses_tree.pack(fill="both", expand=True)
vpan.add(f3, weight=1)

f4 = ttk.LabelFrame(vpan, text="Corporate Accounts", padding=5)
link_works_tree = ttk.Treeview(f4, columns=("Customer","Employee"), show="headings", height=6)
link_works_tree.heading("Customer", text="Customer"); link_works_tree.column("Customer", anchor=tk.CENTER)
link_works_tree.heading("Employee", text="Employee"); link_works_tree.column("Employee", anchor=tk.CENTER)
link_works_tree.pack(fill="both", expand=True)
vpan.add(f4, weight=1)

links_pw.add(views, weight=1)

# ----- Status bar -----
status_var = tk.StringVar(value="Ready.")
status_bar = ttk.Label(root, textvariable=status_var, anchor="w", padding=(10,4))
status_bar.pack(side=tk.BOTTOM, fill="x")

# ----- initial load -----
def load_initial_data():
    fetch_all_orders()
    populate_order_dropdowns()
    refresh_customer_list()
    refresh_staff_lists()
    refresh_inventory()
    refresh_ingredients()
    refresh_link_views()
    populate_admin_dropdowns()
    cart_refresh_view()
    set_status("Loaded.")

root.after(100, load_initial_data)
root.mainloop()
