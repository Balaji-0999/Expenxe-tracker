import os, time
import mysql.connector
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "db"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

@app.on_event("startup")
def init_db():
    for _ in range(15):          # DB ready hone tak retry
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS expenses(
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                category VARCHAR(50),
                date DATE NOT NULL)""")
            conn.commit(); conn.close()
            return
        except Exception:
            time.sleep(2)

class Expense(BaseModel):
    title: str
    amount: float
    category: str
    date: str   # YYYY-MM-DD

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/expenses")
def list_expenses():
    conn = get_db(); cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM expenses ORDER BY date DESC")
    rows = cur.fetchall(); conn.close()
    for r in rows:
        r["amount"] = float(r["amount"]); r["date"] = str(r["date"])
    return rows

@app.post("/expenses")
def add_expense(e: Expense):
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO expenses(title,amount,category,date) VALUES(%s,%s,%s,%s)",
                (e.title, e.amount, e.category, e.date))
    conn.commit(); conn.close()
    return {"message": "added"}

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id=%s", (expense_id,))
    conn.commit(); conn.close()
    return {"message": "deleted"}
