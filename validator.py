"""Vai trò 5 - QA & Exception Handling: kiểm tra dữ liệu, bắt lỗi, tránh crash."""
from datetime import datetime

CATEGORIES = ["Food", "Rent", "Salary", "Transport", "Shopping",
              "Entertainment", "Health", "Bonus", "Other"]
TYPES = ("Income", "Expense")


class ValidationError(Exception):
    """Lỗi dữ liệu nhập vào (từ form hoặc từ file CSV)."""


def validate_row(row: dict) -> dict:
    """Kiểm tra 1 giao dịch. Trả về dict chuẩn hoá, hoặc raise ValidationError.
    Quy ước: Income -> amount > 0, Expense -> amount < 0."""
    date = str(row.get("date", "")).strip()
    if not date:
        raise ValidationError("Date is empty")
    try:
        date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"Invalid date '{date}' (need YYYY-MM-DD)")

    category = str(row.get("category", "")).strip()
    if not category:
        raise ValidationError("Category is empty")

    try:
        amount = float(str(row.get("amount", "")).replace(",", "").strip())
    except ValueError:
        raise ValidationError(f"Amount '{row.get('amount')}' is not a number")
    if amount == 0:
        raise ValidationError("Amount must not be 0")

    t = str(row.get("type", "")).strip().capitalize()
    if t not in TYPES:
        raise ValidationError(f"Type '{row.get('type')}' must be Income or Expense")

    amount = abs(amount) if t == "Income" else -abs(amount)
    return {"date": date, "category": category, "amount": amount,
            "type": t, "note": str(row.get("note", "")).strip()}


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Tránh ZeroDivisionError khi chưa có dữ liệu."""
    try:
        return a / b
    except ZeroDivisionError:
        return default


def show_warning(message: str, title: str = "Invalid Input"):
    from tkinter import messagebox  # import muộn để module test được không cần GUI
    messagebox.showwarning(title, message)




    from datetime import datetime

CATEGORIES = ["Food", "Rent", "Salary", "Transport", "Shopping",
              "Entertainment", "Health", "Bonus", "Other"]
TYPES = ("Income", "Expense")
FIXED_CATEGORIES = ("Rent",)                      # khoản cố định, không tính vào ngân sách theo ngày
VARIABLE_CATEGORIES = [c for c in CATEGORIES
                       if c not in ("Salary", "Bonus") + FIXED_CATEGORIES]


class ValidationError(Exception):
    """Lỗi dữ liệu nhập vào (từ form hoặc từ file CSV)."""


def validate_row(row: dict) -> dict:
    """Kiểm tra 1 giao dịch. Trả về dict chuẩn hoá, hoặc raise ValidationError.
    Quy ước: Income -> amount > 0, Expense -> amount < 0."""
    date = str(row.get("date", "")).strip()
    if not date:
        raise ValidationError("Date is empty")
    try:
        date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"Invalid date '{date}' (need YYYY-MM-DD)")

    category = str(row.get("category", "")).strip()
    if not category:
        raise ValidationError("Category is empty")

    try:
        amount = float(str(row.get("amount", "")).replace(",", "").strip())
    except ValueError:
        raise ValidationError(f"Amount '{row.get('amount')}' is not a number")
    if amount == 0:
        raise ValidationError("Amount must not be 0")

    t = str(row.get("type", "")).strip().capitalize()
    if t not in TYPES:
        raise ValidationError(f"Type '{row.get('type')}' must be Income or Expense")

    amount = abs(amount) if t == "Income" else -abs(amount)
    return {"date": date, "category": category, "amount": amount,
            "type": t, "note": str(row.get("note", "")).strip()}


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Tránh ZeroDivisionError khi chưa có dữ liệu."""
    try:
        return a / b
    except ZeroDivisionError:
        return default


def show_warning(message: str, title: str = "Invalid Input"):
    from tkinter import messagebox  # import muộn để module test được không cần GUI
    messagebox.showwarning(title, message)