from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="RestaurantDB"
)

cursor = db.cursor(dictionary=True)

# -----------------------------
# CUSTOMER MANAGEMENT
# -----------------------------
@app.route('/add_customer', methods=['POST'])
def add_customer():
    data = request.json
    query = "INSERT INTO Customer (CustomerID, Name, Phone, Email) VALUES (%s, %s, %s, %s)"
    values = (data['id'], data['name'], data['phone'], data['email'])
    cursor.execute(query, values)
    db.commit()
    return jsonify({"message": "Customer added"})

@app.route('/customers', methods=['GET'])
def get_customers():
    cursor.execute("SELECT * FROM Customer")
    return jsonify(cursor.fetchall())

# -----------------------------
# MENU MANAGEMENT
# -----------------------------
@app.route('/add_menu_item', methods=['POST'])
def add_menu_item():
    data = request.json
    query = "INSERT INTO MenuItem (MenuID, ItemName, Price, Category) VALUES (%s, %s, %s, %s)"
    values = (data['id'], data['name'], data['price'], data['category'])
    cursor.execute(query, values)
    db.commit()
    return jsonify({"message": "Menu item added"})

@app.route('/menu', methods=['GET'])
def get_menu():
    cursor.execute("SELECT * FROM MenuItem")
    return jsonify(cursor.fetchall())

# -----------------------------
# ORDER PROCESSING
# -----------------------------
@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.json

    # Insert order
    order_query = """
    INSERT INTO RestaurantOrder (OrderID, OrderDate, Subtotal, CustomerID, StaffID, TableID)
    VALUES (%s, NOW(), %s, %s, %s, %s)
    """
    cursor.execute(order_query, (
        data['order_id'],
        0,
        data['customer_id'],
        data['staff_id'],
        data['table_id']
    ))

    # Insert order items
    for item in data['items']:
        item_query = """
        INSERT INTO OrderItem (OrderID, MenuID, Quantity, ItemPrice)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(item_query, (
            data['order_id'],
            item['menu_id'],
            item['quantity'],
            item['price']
        ))

    cursor.execute("""
        SELECT SUM(Quantity * ItemPrice) AS subtotal
        FROM OrderItem
        WHERE OrderID = %s
        """, (data['order_id'],))

    subtotal = cursor.fetchone()['subtotal']

    cursor.execute("""
        UPDATE RestaurantOrder
        SET Subtotal = %s
        WHERE OrderID = %s
        """, (subtotal, data['order_id']))


    db.commit()
    return jsonify({
        "message": "Order created",
        "order_id": data['order_id'],
        "calculated_subtotal": subtotal
        })

# -----------------------------
# RESERVATION MANAGEMENT
# -----------------------------
@app.route('/add_reservation', methods=['POST'])
def add_reservation():
    data = request.json
    query = """
    INSERT INTO Reservation (ReservationID, PartySize, ReservationDate, ReservationTime, CustomerID, TableID)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        data['id'],
        data['party_size'],
        data['date'],
        data['time'],
        data['customer_id'],
        data['table_id']
    ))
    db.commit()
    return jsonify({"message": "Reservation added"})

# -----------------------------
# PAYMENT MANAGEMENT
# -----------------------------
@app.route('/add_payment', methods=['POST'])
def add_payment():
    data = request.json
    query = """
    INSERT INTO Payment (PaymentID, OrderID, Amount, PaymentType, PaymentDate)
    VALUES (%s, %s, %s, %s, NOW())
    """
    cursor.execute(query, (
        data['id'],
        data['order_id'],
        data['amount'],
        data['type']
    ))
    db.commit()
    return jsonify({"message": "Payment recorded"})

# -----------------------------
# RUN APP
# -----------------------------




@app.route('/recommend/<int:menu_id>', methods=['GET'])
def recommend_items(menu_id):
    query = """
    SELECT 
        m.ItemName,
        COUNT(*) * 1.0 / (
            SELECT COUNT(*) 
            FROM OrderItem 
            WHERE MenuID = %s
        ) AS Confidence
    FROM OrderItem oi1
    JOIN OrderItem oi2 
        ON oi1.OrderID = oi2.OrderID
    JOIN MenuItem m ON oi2.MenuID = m.MenuID
    WHERE oi1.MenuID = %s
      AND oi2.MenuID != %s
    GROUP BY oi2.MenuID
    HAVING Confidence > 0.5
    ORDER BY Confidence DESC;
    """

    cursor.execute(query, (menu_id, menu_id, menu_id))
    results = cursor.fetchall()

    return jsonify(results)

@app.route('/analytics/revenue', methods=['GET'])
def revenue_over_time():
    query = """
    SELECT DATE(PaymentDate) AS Day, SUM(Amount) AS TotalRevenue
    FROM Payment
    GROUP BY DATE(PaymentDate)
    ORDER BY Day;
    """
    cursor.execute(query)
    return jsonify(cursor.fetchall())

@app.route('/analytics/top-items', methods=['GET'])
def top_items():
    query = """
    SELECT m.ItemName, SUM(oi.Quantity) AS TotalSold
    FROM OrderItem oi
    JOIN MenuItem m ON oi.MenuID = m.MenuID
    GROUP BY m.MenuID
    ORDER BY TotalSold DESC
    LIMIT 5;
    """
    cursor.execute(query)
    return jsonify(cursor.fetchall())

@app.route('/analytics/peak-hours', methods=['GET'])
def peak_hours():
    query = """
    SELECT HOUR(OrderDate) AS Hour, COUNT(*) AS OrderCount
    FROM RestaurantOrder
    GROUP BY HOUR(OrderDate)
    ORDER BY OrderCount DESC;
    """
    cursor.execute(query)
    return jsonify(cursor.fetchall())

@app.route('/analytics/category-revenue', methods=['GET'])
def category_revenue():
    query = """
    SELECT m.Category, SUM(oi.Quantity * oi.ItemPrice) AS TotalRevenue
    FROM OrderItem oi
    JOIN MenuItem m ON oi.MenuID = m.MenuID
    GROUP BY m.Category
    ORDER BY TotalRevenue DESC;
    """
    cursor.execute(query)
    return jsonify(cursor.fetchall())

if __name__ == '__main__':
    app.run(debug=True)
