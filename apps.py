from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_mysqldb import MySQL
from decimal import Decimal
from flask import flash
from flask import request
 
app = Flask(__name__, static_folder='static')

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost' 
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'pass123'
app.config['MYSQL_DB'] = 'FinancialPlanner'

# Initialize MySQL
mysql = MySQL(app)


# Secret key for session management
app.secret_key = 'vanshika'

def calculate_total_savings(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT SavingAmount FROM savings WHERE UserID = %s", (user_id,))

    balance = cur.fetchone()[0]
    
    cur.execute("SELECT SUM(ExpenseAmount) FROM expenses WHERE UserID = %s", (user_id,))
    total_expenses = cur.fetchone()[0]
    
    total_savings = balance - total_expenses
    cur.close()
    return total_savings


def category_name(category_id):
    print("Category ID:", category_id)
    cur = mysql.connection.cursor()
    cur.execute("SELECT CategoryName FROM budgetcategories WHERE CategoryID = %s", (category_id,))
    category_row = cur.fetchone()
    cur.close()
    if category_row is not None:
        return category_row[0]
    else:
        return "Category Not Found"
    
def fetch_expense_limits(user_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT CategoryID, ExpenseLimit
        FROM expenses
        WHERE UserID = %s
    """, (user_id,))
    expense_limits = {row[0]: row[1] for row in cur.fetchall()}

    cur.close()
    return expense_limits  

def expenses_exceed_limits(expenses, expense_limits):
    for category, expense in expenses.items():
        limit = expense_limits.get(category, None)
        if limit is not None and expense > limit:
            return True
    return False

def fetch_expense_total(user_id, category_name):
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT SUM(ExpenseAmount)
        FROM expenses e
        JOIN budgetcategories bc ON e.CategoryID = bc.CategoryID
        WHERE e.UserID = %s AND bc.CategoryName = %s
    """, (user_id, category_name))
    
    total_expense_row = cur.fetchone()

    if total_expense_row and total_expense_row[0] is not None:
        total_expense = total_expense_row[0]
    else:
        total_expense = 0

    cur.close()

    return total_expense




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_username = request.form['username']
        login_password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT UserID FROM Users WHERE username=%s AND password=%s", (login_username, login_password))
        user_id = cur.fetchone()
        cur.close()

        if user_id:
            session['user_id'] = user_id[0]  # Store UserID in session
            if len(user_id) > 1 and user_id[1]:
                session['username'] = user_id[1]  # Store username in session if it exists
            else:
                session['username'] = login_username  # Store login username if database username is missing
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')   

@app.route('/index')
def index():
    if 'user_id' in session:  # Check if user is logged in
        user_id = session['user_id']
        expense_limits = fetch_expense_limits(user_id)

       
        
        cur = mysql.connection.cursor()

        # Fetch balance for the logged-in user
        cur.execute("SELECT SUM(IncomeAmount) FROM income WHERE UserID = %s", (user_id,))
        total_income = cur.fetchone()[0] or 0

        balance = total_income  

        # Fetching expenses for Groceries, Entertainment, and Utilities categories
        cur.execute("""
            SELECT SUM(e.ExpenseAmount) 
            FROM expenses e 
            JOIN budgetcategories bc ON e.CategoryID = bc.CategoryID 
            WHERE e.UserID = %s AND bc.CategoryName IN ('Groceries', 'Entertainment', 'Utilities')
            GROUP BY bc.CategoryName """, (user_id,))
        expenses = cur.fetchall()

        # Fetch recent transactions
        cur.execute("""
    SELECT bc.CategoryName, e.ExpenseAmount, e.ExpenseDate
    FROM expenses e
    JOIN budgetcategories bc ON e.CategoryID = bc.CategoryID
    WHERE e.UserID = %s
    ORDER BY e.ExpenseDate DESC
    LIMIT 10
""", (user_id,))

        recent_transactions = cur.fetchall()

        cur.execute("SELECT SectorName FROM sectors WHERE UserID = %s", (user_id,))
        sector_row = cur.fetchone()
        user_sector = sector_row[0] if sector_row else None

        cur.close()

        # Initialize variables for expenses
        groceries_expense = 0
        entertainment_expense = 0
        utilities_expense = 0

        # Update variables with fetched expenses if available
        if expenses:
            for i, expense in enumerate(expenses):
                if i == 0:
                    groceries_expense = expense[0] if expense[0] is not None else 0
                elif i == 1:
                    entertainment_expense = expense[0] if expense[0] is not None else 0
                elif i == 2:
                    utilities_expense = expense[0] if expense[0] is not None else 0

        
            

        # Calculate total expenses
        total_expenses = groceries_expense + entertainment_expense + utilities_expense

        # Calculate total savings
        if balance is not None:
            total_savings = balance - total_expenses
        else:
            total_savings = 0  # Set default value if balance is None

        # Fetch savings goal for the user
        

        # Calculate savings progress
        groceries_limit = expense_limits.get(1, 0)
        entertainment_limit = expense_limits.get(3, 0)
        utilities_limit = expense_limits.get(2, 0)
        alert_messages = []
        if groceries_limit is not None and groceries_expense > groceries_limit:
            alert_messages.append("Groceries expense limit exceeded!")
        if entertainment_limit is not None and entertainment_expense > entertainment_limit:
            alert_messages.append("Entertainment expense limit exceeded!")
        if utilities_limit is not None and utilities_expense > utilities_limit:
            alert_messages.append("Utilities expense limit exceeded!")
        if expenses_exceed_limits:
          flash('Alert: Expense limit exceeded for category XYZ', 'danger')    

    

        return render_template('index.html', username=session['username'], 
                               balance=balance,
                               groceries_expense=groceries_expense, 
                               entertainment_expense=entertainment_expense, 
                               utilities_expense=utilities_expense,
                               total_savings=total_savings,
                               recent_transactions=recent_transactions,category_name=category_name,
                               user_sector=user_sector, groceries_limit=groceries_limit,
                               entertainment_limit=entertainment_limit,
                               utilities_limit=utilities_limit, alert_messages=alert_messages)
    else:
        flash('Please log in to view this page', 'error')
        return redirect(url_for('login'))

@app.route('/')
def default():
    return redirect(url_for('login'))


@app.route('/add-expense', methods=['POST'])
def add_expense():
    if 'user_id' in session:  # Check if user is logged in
        user_id = session['user_id']

        purpose = request.form['Purpose']
        amount = request.form['Sum']
        date = request.form['Date']
        category = request.form['Category']

        cur = mysql.connection.cursor()
        cur = mysql.connection.cursor()

        # Retrieve the category ID for the given category name
        cur.execute("SELECT CategoryID FROM budgetcategories WHERE CategoryName = %s", (category,))
        category_row = cur.fetchone()
        if category_row:
            category_id = category_row[0]


        # Retrieve the expense limit from the expenses table based on the category
        cur.execute("""
            SELECT ExpenseLimit
            FROM expenses e
            JOIN budgetcategories bc ON e.CategoryID = bc.CategoryID
            WHERE e.UserID = %s AND bc.CategoryName = %s
        """, (user_id, category))
        expense_limit_row = cur.fetchone()

        if expense_limit_row:
            expense_limit = expense_limit_row[0]
        else:
            expense_limit = None

        # Insert the expense with the retrieved expense limit
        cur.execute("INSERT INTO expenses (UserID, CategoryID, ExpenseAmount, ExpenseDate, ExpenseLimit) VALUES (%s, %s, %s, %s, %s)", (user_id, category_id, amount, date, expense_limit))
        mysql.connection.commit()
        groceries_expense = fetch_expense_total(user_id, 'Groceries')
        entertainment_expense = fetch_expense_total(user_id, 'Entertainment')
        utilities_expense = fetch_expense_total(user_id, 'Utilities')

        cur.close()

        return jsonify({'message': 'Expense added successfully'}), 200
    else:
        return jsonify({'error': 'User not logged in'}), 401




@app.route('/add-cash', methods=['GET', 'POST'])
def add_cash():
    if request.method == 'POST':
        if 'user_id' in session:
            user_id = session['user_id']
            cash_amount = request.form.get('cash_amount')
            
            # Ensure the cash amount is valid (you can add additional validation)
            if cash_amount.isdigit():
                # Insert the cash amount into the income table
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO income (UserID, IncomeAmount) VALUES (%s, %s)", (user_id, cash_amount))
                cur.execute("SELECT IncomeAmount FROM income WHERE UserID = %s", (user_id,))
                balance_row = cur.fetchone()
                balance = balance_row[0] if balance_row else 0

                # Update balance
                cash_amount_decimal = Decimal(cash_amount)
                new_balance = balance + cash_amount_decimal  # Convert cash_amount to float

                # Update balance in the database
                
                mysql.connection.commit()
                cur.close()
                
                flash('Cash added successfully', 'success')
                return redirect(url_for('index'))  # Redirect to index page after adding cash
            else:
                flash('Invalid cash amount', 'error')
                return redirect(url_for('add_cash'))  # Redirect back to add cash page if amount is invalid
        else:
            flash('Please log in to add cash', 'error')
            return redirect(url_for('login'))
    else:
        return render_template('add_cash.html')



@app.route('/settings')
def settings():
    return render_template('settings.html')



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        sector = request.form['sector']  # Add sector field to the form
        
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (Username, Password, Email) VALUES (%s, %s, %s)", (username, password, email))
        
        # Insert sector details if provided
        if sector:
            cur.execute("INSERT INTO sectors (UserID, SectorName) VALUES (%s, %s)", (cur.lastrowid, sector))
        
        mysql.connection.commit()
        cur.close()
        
        flash('Signup successful. Please login.', 'success')
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')

    
@app.route('/set_expense_limits', methods=['POST'])
def set_expense_limits():
    if 'user_id' in session:
        user_id = session['user_id']
        
        groceries_limit = request.form.get('groceries_limit')
        entertainment_limit = request.form.get('entertainment_limit')
        utilities_limit = request.form.get('utilities_limit')

        cur = mysql.connection.cursor()
        # Update or insert expense limits directly in the expenses table
        cur.execute("""
            INSERT INTO expenses (UserID, CategoryID, ExpenseLimit)
            VALUES (%s, 1, %s)
            ON DUPLICATE KEY UPDATE ExpenseLimit = VALUES(ExpenseLimit)
        """, (user_id, groceries_limit))
        
        cur.execute("""
            INSERT INTO expenses (UserID, CategoryID, ExpenseLimit)
            VALUES (%s, 2, %s)
            ON DUPLICATE KEY UPDATE ExpenseLimit = VALUES(ExpenseLimit)
        """, (user_id, entertainment_limit))
        
        cur.execute("""
            INSERT INTO expenses (UserID, CategoryID, ExpenseLimit)
            VALUES (%s, 3, %s)
            ON DUPLICATE KEY UPDATE ExpenseLimit = VALUES(ExpenseLimit)
        """, (user_id, utilities_limit))
        
        mysql.connection.commit()
        cur.close()

        flash('Expense limits updated successfully', 'success')
        return redirect(url_for('index'))
    else:
        flash('Please log in to set expense limits', 'error')
        return redirect(url_for('login'))
    
@app.route('/add_sector', methods=['POST', 'GET'])
def add_sector():
    if 'user_id' in session:
        if request.method == 'POST':
            user_id = session['user_id']
            sector = request.form.get('sector')  # Use request.form.get to avoid KeyError

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO sectors (UserID, SectorName) VALUES (%s, %s)", (user_id, sector))
            mysql.connection.commit()
            cur.close()

            flash('Sector added successfully', 'success')
            return redirect(url_for('index'))
        else:
            # If it's a GET request, render the add sector form
            return render_template('sector.html')
    else:
        flash('Please log in to view this page', 'error')
        return redirect(url_for('login'))




@app.route('/execute_query', methods=['POST'])
def execute_query():
    category = request.form['category']
    date_from = request.form['date_from']
    date_to = request.form['date_to']
    include_limit = 'include_limit' in request.form

    # Construct SQL query based on user inputs
    query = "SELECT * FROM expenses WHERE Category = '{}'".format(category)
    if date_from and date_to:
        query += " AND ExpenseDate BETWEEN '{}' AND '{}'".format(date_from, date_to)
    if include_limit:
        query += " AND ExpenseLimit IS NOT NULL"

    # Execute the query and fetch results
    cur = mysql.connection.cursor()
    cur.execute(query)
    results = cur.fetchall()
    cur.close()

    # Process and display results as needed
    return render_template('query_results.html', results=results)



# Other routes and functions...
 
if __name__ == '__main__':
    app.run(debug=True)