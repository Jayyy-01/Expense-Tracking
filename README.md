# Secure Multi-User Expense Tracking & Analytics System

A RESTful API to track expenses, manage multi-user data securely, and analyze spending patterns — built with FastAPI.

##  Tech Stack

- Python, FastAPI
- MySQL + SQLAlchemy (ORM)
- JWT Authentication
- Pandas (analytics, Excel export)
- HTML/CSS/JS (frontend)

##  Setup Steps

1. Clone the repository
   ```
   git clone https://github.com/Jayyy-01/Expense-Tracking
   ```
2. Navigate to the project folder
   ```
   cd Expense-Tracking
   ```
3. Create a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate
   ```
4. Install dependencies
   ```
   pip install -r requirements.txt
   ```
5. Run the application
   ```
   uvicorn app:app --reload
   ```
6. Test APIs via the interactive docs
   ```
   http://localhost:8000/docs
   ```

##  Features

- Secure multi-user support with JWT authentication
- Add, update, delete, and categorize expenses
- 10+ REST API endpoints
- User-isolated analytics dashboard (500+ monthly transactions tracked)
- Automated Excel export — cuts manual reporting effort by ~80%
- Input validation and error handling

##  Future Improvements

- Budget limit alerts
- Additional data visualization (charts/graphs)
- Monthly/weekly automated email reports
```
