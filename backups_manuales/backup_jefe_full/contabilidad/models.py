from sqlalchemy import func

# --- Utilidades para dashboard del jefe ---
def get_company_kpis(db: Session, company_id: int):
    ingresos = db.query(func.sum(Income.amount)).filter(Income.company_id == company_id).scalar() or 0.0
    egresos = db.query(func.sum(Expense.amount)).filter(Expense.company_id == company_id).scalar() or 0.0
    deudas = db.query(func.sum(GeneralDebt.amount)).filter(GeneralDebt.company_id == company_id, GeneralDebt.status == "pending").scalar() or 0.0
    return {
        "ingresos": ingresos,
        "egresos": egresos,
        "deudas": deudas,
        "saldo": ingresos - egresos - deudas
    }

def get_all_companies_kpis(db: Session):
    companies = db.query(Company).all()
    resumen = []
    for company in companies:
        kpis = get_company_kpis(db, company.id)
        resumen.append({
            "empresa": company.name,
            **kpis
        })
    return resumen
from sqlalchemy import Column, Integer, String, Float, Date, create_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()


# --- Multiempresa y usuarios ---
class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(Date, default=datetime.date.today)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="empresa")  # 'admin' o 'empresa'
    company_id = Column(Integer)
    created_at = Column(Date, default=datetime.date.today)

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False)
    date = Column(Date, default=datetime.date.today)
    category = Column(String)
    amount = Column(Float)
    description = Column(String)
    type = Column(String, default="variable")


class Income(Base):
    __tablename__ = "income"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)
    source = Column(String)

class FixedCost(Base):
    __tablename__ = "fixed_costs"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)

class Loan(Base):
    __tablename__ = "loans"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    capital = Column(Float, default=0.0)
    interest = Column(Float, default=0.0)
    category = Column(String, nullable=False)
    status = Column(String, default="active")

class GeneralDebt(Base):
    __tablename__ = "general_debts"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date)
    status = Column(String, default="pending")

class Check(Base):
    __tablename__ = "checks"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, nullable=False)
    bank = Column(String)
    number = Column(String)
    amount = Column(Float)
    due_date = Column(Date)
    recipient = Column(String)
    status = Column(String, default="pending")

class ActivityLog(Base):
    __tablename__ = "activity_log"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Date, default=datetime.date.today)
    company_id = Column(Integer, nullable=False)
    action = Column(String)
    details = Column(String)

SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)

# --- Funciones de autenticación y utilidades de roles ---
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
import bcrypt
import os

def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt (Industry Standard)."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def authenticate_user(db: Session, username: str, password: str):
    try:
        user = db.query(User).filter(User.username == username).one()
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return user
        return None
    except NoResultFound:
        return None

def is_admin(user) -> bool:
    return user.role == "admin"

def is_company_user(user) -> bool:
    return user.role == "empresa"
