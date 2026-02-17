from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

#MySQL connection (your existing one is correct)
DATABASE_URL = "mysql+pymysql://root:iamfunny0%40@localhost/expense_tracker"

# create engine
engine = create_engine(DATABASE_URL)

# session maker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# base class
Base = declarative_base()


# dependency (VERY IMPORTANT for FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
