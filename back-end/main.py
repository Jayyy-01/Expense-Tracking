from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
import io
import openpyxl

from database import SessionLocal, engine
from models import Base, User, Expense

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker API")

# ✅ CORS (needed for frontend on localhost:63342)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:63342",
        "http://127.0.0.1:63342",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT
SECRET_KEY = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# ---------- DB ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Schemas ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ExpenseIn(BaseModel):
    amount: float
    category: str
    description: Optional[str] = None


class ExpenseOut(BaseModel):
    id: int
    amount: float
    category: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Helpers ----------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = db.query(User).filter(User.email == sub).first()
    if not user:
        raise cred_exc
    return user


# ---------- Routes ----------
@app.get("/")
def home():
    return {"message": "Expense Tracker API running"}


@app.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Registered successfully", "user_id": user.id}


# ✅ Swagger OAuth2 (password flow) uses FORM fields: username + password
@app.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # form.username will contain your email
    user = db.query(User).filter(User.email == form.username).first()

    # ✅ FIX: user has hashed_password, not password
    if (not user) or (not verify_password(form.password, user.hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/expense", response_model=ExpenseOut)
def add_expense(payload: ExpenseIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    exp = Expense(
        amount=payload.amount,
        category=payload.category,
        description=payload.description,
        user_id=user.id,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@app.get("/expenses/me", response_model=List[ExpenseOut])
def get_my_expenses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Expense)
        .filter(Expense.user_id == user.id)
        .order_by(Expense.created_at.desc())
        .all()
    )


@app.put("/expense/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: int,
    payload: ExpenseIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user.id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    exp.amount = payload.amount
    exp.category = payload.category
    exp.description = payload.description
    db.commit()
    db.refresh(exp)
    return exp


@app.delete("/expense/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    exp = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user.id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(exp)
    db.commit()
    return {"message": "Deleted successfully"}


@app.get("/monthly-summary")
def monthly_summary(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = (
        db.query(Expense)
        .filter(
            Expense.user_id == user.id,
            extract("year", Expense.created_at) == year,
            extract("month", Expense.created_at) == month,
        )
        .order_by(Expense.created_at.desc())
        .all()
    )

    total_spent = float(sum(e.amount for e in q))
    total_expenses = len(q)

    category_rows = (
        db.query(Expense.category, func.sum(Expense.amount).label("total"))
        .filter(
            Expense.user_id == user.id,
            extract("year", Expense.created_at) == year,
            extract("month", Expense.created_at) == month,
        )
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )

    category_breakdown = [{"category": c, "total": float(t)} for c, t in category_rows]

    details = [
        {
            "id": e.id,
            "amount": float(e.amount),
            "category": e.category,
            "description": e.description,
            "created_at": e.created_at.isoformat(),
        }
        for e in q
    ]

    return {
        "user_id": user.id,
        "year": year,
        "month": month,
        "total_spent": total_spent,
        "total_expenses": total_expenses,
        "category_breakdown": category_breakdown,
        "details": details,
    }


@app.get("/yearly-summary")
def yearly_summary(
    year: int = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = (
        db.query(extract("month", Expense.created_at).label("m"), func.sum(Expense.amount).label("total"))
        .filter(Expense.user_id == user.id, extract("year", Expense.created_at) == year)
        .group_by("m")
        .order_by("m")
        .all()
    )

    month_map = {int(m): float(total) for m, total in rows}
    months = [{"month": m, "total_spent": month_map.get(m, 0.0)} for m in range(1, 13)]

    return {"user_id": user.id, "year": year, "months": months}


@app.get("/export/excel")
def export_excel(
    year: int = Query(...),
    month: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Expense).filter(
        Expense.user_id == user.id,
        extract("year", Expense.created_at) == year
    )

    if month:
        query = query.filter(extract("month", Expense.created_at) == month)

    expenses = query.all()

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Expenses"

    sheet.append(["ID", "Amount", "Category", "Description", "Created At"])

    for exp in expenses:
        sheet.append([
            exp.id,
            exp.amount,
            exp.category,
            exp.description,
            str(exp.created_at)
        ])

    stream = io.BytesIO()
    workbook.save(stream)
    stream.seek(0)

    filename = f"expenses_{year}"
    if month:
        filename += f"_{month}"

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}.xlsx"
        },
    )
