from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="RestaurantDB",
        ssl_disabled=True
    )



# CUSTOMER MANAGEMENT

@app.route('/add_customer', methods=['POST'])
def add_customer():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        data = request.json

        if not data.get('name') or not data.get('phone') or not data.get('email'):
            return jsonify({"error": "Name, phone, and email are required"}), 400

        query = "INSERT INTO Customer (CustomerID, Name, Phone, Email) VALUES (%s, %s, %s, %s)"
        values = (data['id'], data['name'], data['phone'], data['email'])
        cursor.execute(query, values)
        db.commit()

        return jsonify({"message": "Customer added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()


@app.route('/customers', methods=['GET'])
def get_customers():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM Customer")
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()



# MENU MANAGEMENT

@app.route('/add_menu_item', methods=['POST'])
def add_menu_item():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        data = request.json

        if not data.get('name') or not data.get('price') or not data.get('category'):
            return jsonify({"error": "Name, price, and category are required"}), 400

        query = "INSERT INTO MenuItem (MenuID, ItemName, Price, Category) VALUES (%s, %s, %s, %s)"
        values = (data['id'], data['name'], data['price'], data['category'])
        cursor.execute(query, values)
        db.commit()

        return jsonify({"message": "Menu item added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()


@app.route('/menu', methods=['GET'])
def get_menu():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM MenuItem")
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()



# ORDER PROCESSING

@app.route('/create_order', methods=['POST'])
def create_order():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        data = request.json

        if not data.get('customer_id') or not data.get('staff_id') or not data.get('table_id'):
            return jsonify({"error": "Customer ID, Staff ID, and Table ID are required"}), 400

        if not data.get('items') or len(data['items']) == 0:
            return jsonify({"error": "Order must contain at least one item"}), 400

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

        subtotal_row = cursor.fetchone()
        subtotal = subtotal_row['subtotal'] if subtotal_row['subtotal'] is not None else 0

        cursor.execute("""
            UPDATE RestaurantOrder
            SET Subtotal = %s
            WHERE OrderID = %s
        """, (subtotal, data['order_id']))

        db.commit()

        return jsonify({
            "message": "Order created successfully",
            "order_id": data['order_id'],
            "calculated_subtotal": subtotal
        })
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()



# RESERVATION MANAGEMENT

@app.route('/add_reservation', methods=['POST'])
def add_reservation():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
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

        return jsonify({"message": "Reservation added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()



# PAYMENT MANAGEMENT

@app.route('/add_payment', methods=['POST'])
def add_payment():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        data = request.json

        if not data.get('order_id') or not data.get('amount') or not data.get('type'):
            return jsonify({"error": "Order ID, amount, and payment type are required"}), 400

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

        return jsonify({"message": "Payment recorded successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()



# RECOMMENDATIONS

@app.route('/recommend/<int:menu_id>', methods=['GET'])
def recommend_items(menu_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
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
        GROUP BY oi2.MenuID, m.ItemName
        HAVING Confidence > 0.5
        ORDER BY Confidence DESC;
        """

        cursor.execute(query, (menu_id, menu_id, menu_id))
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()



# ANALYTICS

@app.route('/analytics/revenue', methods=['GET'])
def revenue_over_time():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        query = """
        SELECT DATE(PaymentDate) AS Day, SUM(Amount) AS TotalRevenue
        FROM Payment
        GROUP BY DATE(PaymentDate)
        ORDER BY Day;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()


@app.route('/analytics/top-items', methods=['GET'])
def top_items():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        query = """
        SELECT m.ItemName, SUM(oi.Quantity) AS TotalSold
        FROM OrderItem oi
        JOIN MenuItem m ON oi.MenuID = m.MenuID
        GROUP BY m.MenuID, m.ItemName
        ORDER BY TotalSold DESC
        LIMIT 5;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()


@app.route('/analytics/peak-hours', methods=['GET'])
def peak_hours():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        query = """
        SELECT HOUR(OrderDate) AS Hour, COUNT(*) AS OrderCount
        FROM RestaurantOrder
        GROUP BY HOUR(OrderDate)
        ORDER BY OrderCount DESC;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()


@app.route('/analytics/category-revenue', methods=['GET'])
def category_revenue():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        query = """
        SELECT m.Category, SUM(oi.Quantity * oi.ItemPrice) AS TotalRevenue
        FROM OrderItem oi
        JOIN MenuItem m ON oi.MenuID = m.MenuID
        GROUP BY m.Category
        ORDER BY TotalRevenue DESC;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()


if __name__ == '__main__':
    app.run(debug=True)
