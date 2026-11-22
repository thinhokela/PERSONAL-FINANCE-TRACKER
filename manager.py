"""Vai trò 1 - Data Logic Lead: toàn bộ xử lý dữ liệu lõi bằng Pandas."""
import pandas as pd
from validator import validate_row, ValidationError

COLUMNS = ["date", "category", "amount", "type", "note"]


class DataManager:
    def __init__(self, path: str = "transactions.csv"):
        self.path = path
        self.df = self._empty()
        self.error_rows: list[dict] = []   # các dòng CSV bị lỗi (để tô đỏ)

    @staticmethod
    def _empty() -> pd.DataFrame:
        df = pd.DataFrame(columns=COLUMNS)
        df["date"] = pd.to_datetime(df["date"])
        df["amount"] = df["amount"].astype(float)
        return df

    # ---------- Đọc / Ghi ----------
    def load_data(self, path: str | None = None) -> pd.DataFrame:
        """Đọc CSV. FileNotFoundError / ValueError được ném lên cho GUI bắt."""
        if path:
            self.path = path
        raw = pd.read_csv(self.path, dtype=str, keep_default_na=False)
        missing = set(COLUMNS) - set(raw.columns)
        if missing:
            raise ValueError(f"CSV thiếu cột: {', '.join(sorted(missing))}")

        good, self.error_rows = [], []
        for _, row in raw.iterrows():
            try:
                good.append(validate_row(row.to_dict()))
            except ValidationError as e:
                bad = row.to_dict()
                bad["_error"] = str(e)
                self.error_rows.append(bad)

        self.df = pd.DataFrame(good, columns=COLUMNS) if good else self._empty()
        self.df["date"] = pd.to_datetime(self.df["date"])
        self.df["amount"] = self.df["amount"].astype(float)
        return self.df

    def save_data(self, path: str | None = None) -> None:
        out = self.df.copy()
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
        out.to_csv(path or self.path, index=False)

    def add_transaction(self, record: dict) -> None:
        """record đã được validate_row() chuẩn hoá."""
        new = pd.DataFrame([record], columns=COLUMNS)
        new["date"] = pd.to_datetime(new["date"])
        self.df = pd.concat([self.df, new], ignore_index=True)
        self.save_data()

    # ---------- Bộ lọc (9%) ----------
    def get_filtered_data(self, type_filter: str = "Both") -> pd.DataFrame:
        df = self.df
        if type_filter == "Income":
            df = df[df["amount"] > 0]
        elif type_filter == "Expense":
            df = df[df["amount"] < 0]
        return df.sort_values("date").reset_index(drop=True)

    # ---------- Số dư hàng tháng (12%) ----------
    def calculate_monthly_balance(self) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame(columns=["month", "income", "expense", "balance"])
        d = self.df.copy()
        d["month"] = d["date"].dt.strftime("%Y-%m")
        res = pd.DataFrame({
            "income": d[d["amount"] > 0].groupby("month")["amount"].sum(),
            "expense": d[d["amount"] < 0].groupby("month")["amount"].sum(),
            "balance": d.groupby("month")["amount"].sum(),
        }).fillna(0.0)
        return res.reset_index().rename(columns={"index": "month"})

    # ---------- Top categories cho biểu đồ ----------
    def top_categories(self, n: int = 8) -> pd.DataFrame:
        if self.df.empty:
            return pd.DataFrame(columns=["category", "amount"])
        g = self.df.groupby("category", as_index=False)["amount"].sum()
        g["abs"] = g["amount"].abs()
        return g.nlargest(n, "abs").drop(columns="abs").reset_index(drop=True)

    def total_balance(self) -> float:
        return float(self.df["amount"].sum()) if not self.df.empty else 0.0


from datetime import date, datetime
def parse_month(month: str) -> tuple[int, int]:
    try:
        d = datetime.strptime(str(month).strip(), "%Y-%m")
    except ValueError:
        raise ValidationError(f"Invalid month '{month}' (need YYYY-MM)")
    return d.year, d.month



import calendar
import os
import zipfile
import math
from datetime import date, datetime

import pandas as pd
from validator import ValidationError, safe_divide, FIXED_CATEGORIES, VARIABLE_CATEGORIES

# Tỉ lệ gợi ý chia ngân sách cho từng danh mục (tổng = 1.0)
DEFAULT_WEIGHTS = {"Food": 0.35, "Transport": 0.15, "Shopping": 0.15,
                   "Entertainment": 0.10, "Health": 0.10, "Other": 0.15}


def parse_month(month: str) -> tuple[int, int]:
    try:
        d = datetime.strptime(str(month).strip(), "%Y-%m")
    except ValueError:
        raise ValidationError(f"Invalid month '{month}' (need YYYY-MM)")
    return d.year, d.month


class BudgetManager:
    """Ngân sách lưu trong sheet 'Budgets' của file Excel (cùng file với giao dịch).
    Mỗi dòng: month | total | category | daily_limit."""
    COLUMNS = ["month", "total", "category", "daily_limit"]

    def __init__(self, path: str = "budget.xlsx", sheet_name: str = "Budgets"):
        self.path = path
        self.sheet_name = sheet_name
        self.budgets: dict = {}   # {"2026-11": {"total": 9e6, "category_daily": {"Food": 150000}}}
        self.load()

    # ---------- Lưu / đọc (Excel) ----------
    def load(self):
        self.budgets = {}
        try:
            df = pd.read_excel(self.path, sheet_name=self.sheet_name, dtype={"month": str})
        except (FileNotFoundError, ValueError, OSError, zipfile.BadZipFile):
            return                      # chưa có file / chưa có sheet Budgets -> chưa đặt ngân sách
        if not set(self.COLUMNS) <= set(df.columns):
            return
        for _, r in df.iterrows():
            if pd.isna(r["month"]) or pd.isna(r["total"]):
                continue
            entry = self.budgets.setdefault(str(r["month"]).strip(),
                                            {"total": float(r["total"]), "category_daily": {}})
            cat = r["category"]
            if pd.notna(cat) and str(cat).strip() and pd.notna(r["daily_limit"]):
                entry["category_daily"][str(cat).strip()] = float(r["daily_limit"])

    def save(self):
        """Ghi sheet Budgets, giữ nguyên các sheet khác trong file (lỗi OSError nếu Excel đang mở file)."""
        rows = []
        for month, b in sorted(self.budgets.items()):
            if b["category_daily"]:
                for cat, d in b["category_daily"].items():
                    rows.append({"month": month, "total": b["total"], "category": cat, "daily_limit": d})
            else:
                rows.append({"month": month, "total": b["total"], "category": "", "daily_limit": 0})
        df = pd.DataFrame(rows, columns=self.COLUMNS)
        if os.path.exists(self.path):
            writer = pd.ExcelWriter(self.path, engine="openpyxl", mode="a", if_sheet_exists="replace")
        else:
            writer = pd.ExcelWriter(self.path, engine="openpyxl", mode="w")
        with writer as w:
            df.to_excel(w, sheet_name=self.sheet_name, index=False)

    # ---------- Thiết lập ----------
    def get_budget(self, month: str):
        """Ngân sách của tháng; nếu chưa đặt thì dùng lại ngân sách của tháng gần nhất trước đó."""
        if month in self.budgets:
            return self.budgets[month]
        earlier = [m for m in self.budgets if m < month]
        return self.budgets[max(earlier)] if earlier else None

    def set_budget(self, month: str, total: float, category_daily: dict) -> None:
        y, m = parse_month(month)
        dim = calendar.monthrange(y, m)[1]
        if total <= 0:
            raise ValidationError("Monthly budget must be greater than 0")
        cleaned = {}
        for cat, v in category_daily.items():
            if v < 0:
                raise ValidationError(f"Daily limit of {cat} must not be negative")
            if v > 0:
                cleaned[cat] = float(v)
        planned = sum(cleaned.values()) * dim
        if planned > total:
            raise ValidationError(
                f"Daily limits add up to {planned:,.0f} for {dim} days,\n"
                f"which is more than the monthly budget {total:,.0f}.")
        self.budgets[f"{y:04d}-{m:02d}"] = {"total": float(total), "category_daily": cleaned}

    @staticmethod
    def suggest_split(total: float, month: str) -> dict:
        """Gợi ý hạn mức/ngày cho từng danh mục (làm tròn xuống nghìn đồng)."""
        y, m = parse_month(month)
        dim = calendar.monthrange(y, m)[1]
        return {c: math.floor(total * w / dim / 1000) * 1000
                for c, w in DEFAULT_WEIGHTS.items() if c in VARIABLE_CATEGORIES}

    # ---------- Tính toán ----------
    def status(self, df: pd.DataFrame, month: str | None = None, today: date | None = None):
        today = today or date.today()
        cur = today.strftime("%Y-%m")
        month = month or cur
        b = self.get_budget(month)
        if b is None:
            return None
        y, m = parse_month(month)
        dim = calendar.monthrange(y, m)[1]
        is_current = (month == cur)
        if is_current:
            days_left = dim - today.day + 1        # gồm cả hôm nay
        elif month < cur:
            days_left = 0
        else:
            days_left = dim

        exp = df[df["amount"] < 0]
        exp = exp[(exp["date"].dt.strftime("%Y-%m") == month)
                  & (~exp["category"].isin(FIXED_CATEGORIES))]
        today_exp = exp[exp["date"].dt.normalize() == pd.Timestamp(today)] if is_current else exp.iloc[0:0]

        total = b["total"]
        spent = float(-exp["amount"].sum())
        spent_today = float(-today_exp["amount"].sum())
        remaining = total - spent
        # Mức được chi hôm nay = (ngân sách còn lại trước hôm nay) / số ngày còn lại
        allowed_today = max(0.0, safe_divide(total - (spent - spent_today), days_left)) if days_left else 0.0

        by_month = (-exp.groupby("category")["amount"].sum()).to_dict()
        by_today = (-today_exp.groupby("category")["amount"].sum()).to_dict()
        cats = []
        for cat, daily in b["category_daily"].items():
            s_m, s_t = float(by_month.get(cat, 0.0)), float(by_today.get(cat, 0.0))
            cap = daily * dim
            if s_m > cap:
                state = "OVER MONTH CAP"
            elif s_t > daily:
                state = "OVER TODAY"
            else:
                state = "OK"
            cats.append({"category": cat, "daily": daily, "spent_today": s_t,
                         "left_today": daily - s_t, "spent_month": s_m,
                         "month_cap": cap, "state": state})
        cats.sort(key=lambda r: r["category"])
        return {"month": month, "total": total, "spent": spent, "remaining": remaining,
                "days_in_month": dim, "days_left": days_left, "is_current": is_current,
                "base_daily": total / dim, "allowed_today": allowed_today,
                "spent_today": spent_today, "left_today": allowed_today - spent_today,
                "categories": cats}

    def check_alerts(self, df: pd.DataFrame, today: date | None = None) -> list[str]:
        st = self.status(df, today=today)
        if st is None:
            return []
        out = []
        if st["remaining"] < 0:
            out.append(f"Over the monthly budget by {-st['remaining']:,.0f}.")
        elif st["left_today"] < 0:
            out.append(f"Over today's allowance by {-st['left_today']:,.0f} "
                       f"(allowed {st['allowed_today']:,.0f}).")
        for c in st["categories"]:
            if c["state"] == "OVER MONTH CAP":
                out.append(f"{c['category']}: over the monthly cap by {c['spent_month'] - c['month_cap']:,.0f}.")
            elif c["state"] == "OVER TODAY":
                out.append(f"{c['category']}: over today's limit by {-c['left_today']:,.0f}.")
        return out