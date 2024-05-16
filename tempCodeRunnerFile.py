from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_mysqldb import MySQL

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

def fetch_expense(user_id, category):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT SUM(e.ExpenseAmount) 
        FROM expenses e 
        JOIN budgetcategories bc ON e.CategoryID = bc.CategoryID 
        WHERE e.UserID = %s AND bc.CategoryName = %s
    """, (user_id, category))
    expense = cur.fetchone()[0]
    cur.close()
    return expense

def fetch_savings_goal(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT SavingsGoal FROM SavingsGoal WHERE UserID = %s", (user_id,))
    savings_goal = cur.fetchone()[0]
    cur.close()
    return savings_goal

def calculate_savings_progress(total_savings, savings_goal):
    if savings_goal == 0:
        return 0
    else:
        return (total_savings / savings_goal) * 100

@app.route('/index')
def index():
    if 'user_id' in session:  # Check if user is logged in
        user_id = session['user_id']
        
        cur = mysql.connection.cursor()

        # Fetch balance for the logged-in user
        cur.execute("SELECT SavingAmount FROM savings WHERE UserID = %s", (user_id,))

        balance_row = cur.fetchone()
        balance = balance_row[0] if balance_row else None

        # Fetching expenses for Groceries, Entertainment, and Utilities categories
        cur.execute("""
            SELECT SUM(e.ExpenseAmount) 
            FROM expenses e 
            JOIN budgetcategories bc ON e.CategoryID = bc.CategoryID 
            WHERE e.UserID = %s AND bc.CategoryName IN ('Groceries', 'Entertainment', 'Utilities')
        """, (user_id,))
        expenses = cur.fetchall()

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

        return render_template('index.html', username=session['username'], 
                               balance=balance,
                               groceries_expense=groceries_expense, 
                               entertainment_expense=entertainment_expense, 
                               utilities_expense=utilities_expense,
                               total_savings=total_savings)
    else:
        flash('Please log in to view this page', 'error')
        return redirect(url_for('login'))


# Other routes and functions...

if __name__ == '__main__':
    app.run(debug=True)
