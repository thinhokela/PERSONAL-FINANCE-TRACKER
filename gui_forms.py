"""Vai trò 3 - GUI Form: cửa sổ popup 'Add Transaction'."""
import tkinter as tk
from tkinter import ttk
from datetime import date
from validator import validate_row, ValidationError, show_warning, CATEGORIES

try:
    from tkcalendar import DateEntry
except ImportError:           # fallback nếu chưa cài tkcalendar
    DateEntry = None


class AddTransactionForm:
    def __init__(self, root, data_manager, on_saved):
        self.dm, self.on_saved = data_manager, on_saved
        self.win = tk.Toplevel(root)
        self.win.title("Add Transaction")
        self.win.resizable(False, False)
        self.win.grab_set()   # modal

        frm = ttk.Frame(self.win, padding=15)
        frm.pack()

        ttk.Label(frm, text="Date:").grid(row=0, column=0, sticky="w", pady=4)
        if DateEntry:
            self.date_w = DateEntry(frm, date_pattern="yyyy-mm-dd", width=18)
        else:
            self.date_w = ttk.Entry(frm, width=20)
            self.date_w.insert(0, date.today().isoformat())
        self.date_w.grid(row=0, column=1, pady=4)

        ttk.Label(frm, text="Category:").grid(row=1, column=0, sticky="w", pady=4)
        self.cat_w = ttk.Combobox(frm, values=CATEGORIES, state="readonly", width=18)
        self.cat_w.current(0)
        self.cat_w.grid(row=1, column=1, pady=4)

        ttk.Label(frm, text="Amount:").grid(row=2, column=0, sticky="w", pady=4)
        self.amount_w = ttk.Entry(frm, width=20)
        self.amount_w.grid(row=2, column=1, pady=4)

        ttk.Label(frm, text="Type:").grid(row=3, column=0, sticky="w", pady=4)
        self.type_var = tk.StringVar(value="Expense")
        tf = ttk.Frame(frm)
        tf.grid(row=3, column=1, sticky="w")
        ttk.Radiobutton(tf, text="Income", variable=self.type_var, value="Income").pack(side="left")
        ttk.Radiobutton(tf, text="Expense", variable=self.type_var, value="Expense").pack(side="left", padx=8)

        ttk.Label(frm, text="Note:").grid(row=4, column=0, sticky="w", pady=4)
        self.note_w = ttk.Entry(frm, width=20)
        self.note_w.grid(row=4, column=1, pady=4)

        ttk.Button(frm, text="Save", command=self.save).grid(row=5, column=0, columnspan=2, pady=(12, 0))

    def save(self):
        raw = {"date": self.date_w.get(), "category": self.cat_w.get(),
               "amount": self.amount_w.get(), "type": self.type_var.get(),
               "note": self.note_w.get()}
        try:
            record = validate_row(raw)
        except ValidationError as e:
            show_warning(str(e))          # không crash, báo lỗi rõ ràng
            return
        self.dm.add_transaction(record)
        self.win.destroy()
        self.on_saved()                    # cập nhật lại bảng ở cửa sổ chính






        import tkinter as tk
from tkinter import ttk
from datetime import date
from validator import ValidationError, show_warning, VARIABLE_CATEGORIES

RED, GREEN = "#d64545", "#2e9e5b"


def _parse_money(text: str, label: str) -> float:
    t = text.replace(",", "").replace(" ", "").strip()
    if t.count(".") > 1:          # kiểu 1.000.000
        t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        raise ValidationError(f"{label} '{text}' is not a number")


class BudgetWindow:
    def __init__(self, root, dm, bm, on_change=None):
        self.dm, self.bm, self.on_change = dm, bm, on_change
        self.win = tk.Toplevel(root)
        self.win.title("Budget Manager")
        self.win.geometry("800x640")

        # --- Ngân sách tháng ---
        top = ttk.LabelFrame(self.win, text="Monthly budget (excluding Rent)", padding=10)
        top.pack(fill="x", padx=10, pady=(10, 5))
        self.month_var = tk.StringVar(value=date.today().strftime("%Y-%m"))
        self.total_var = tk.StringVar()
        ttk.Label(top, text="Month (YYYY-MM):").grid(row=0, column=0)
        ttk.Entry(top, textvariable=self.month_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Button(top, text="Load", command=self.load_month).grid(row=0, column=2, padx=5)
        ttk.Label(top, text="Budget:").grid(row=0, column=3, padx=(25, 0))
        ttk.Entry(top, textvariable=self.total_var, width=16).grid(row=0, column=4, padx=5)

        # --- Hạn mức theo ngày ---
        lim = ttk.LabelFrame(self.win, text="Daily limit per category (empty / 0 = no limit)", padding=10)
        lim.pack(fill="x", padx=10, pady=5)
        self.limit_vars = {}
        for i, c in enumerate(VARIABLE_CATEGORIES):
            r, col = divmod(i, 3)
            ttk.Label(lim, text=f"{c}:").grid(row=r, column=col * 2, sticky="e", padx=(12, 3), pady=3)
            v = tk.StringVar()
            ttk.Entry(lim, textvariable=v, width=12).grid(row=r, column=col * 2 + 1, pady=3)
            self.limit_vars[c] = v

        btns = ttk.Frame(self.win)
        btns.pack(fill="x", padx=10)
        ttk.Button(btns, text="Suggest split", command=self.suggest).pack(side="left")
        ttk.Button(btns, text="Save Budget", command=self.save).pack(side="left", padx=8)

        # --- Tóm tắt ---
        sm = ttk.LabelFrame(self.win, text="Summary", padding=10)
        sm.pack(fill="x", padx=10, pady=8)
        self.lbl_overview = tk.Label(sm, anchor="w", justify="left")
        self.lbl_overview.pack(fill="x")
        self.bar = ttk.Progressbar(sm, maximum=100)
        self.bar.pack(fill="x", pady=6)
        self.lbl_today = tk.Label(sm, anchor="w", justify="left", font=("TkDefaultFont", 11, "bold"))
        self.lbl_today.pack(fill="x")

        # --- Bảng theo danh mục ---
        cols = ("Category", "Daily limit", "Spent today", "Left today", "Spent month", "Month cap", "Status")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings", height=8)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=100, anchor="w" if c in ("Category", "Status") else "e")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree.tag_configure("over", background="#ffcccc", foreground="#b00000")

        self.load_month()

    # ---------- Thao tác ----------
    def load_month(self):
        month = self.month_var.get().strip()
        b = self.bm.get_budget(month)
        self.total_var.set(f"{b['total']:,.0f}" if b else "")
        for c, v in self.limit_vars.items():
            d = b["category_daily"].get(c, 0) if b else 0
            v.set(f"{d:,.0f}" if d else "")
        self.refresh()

    def _read_fields(self):
        total = _parse_money(self.total_var.get(), "Budget")
        limits = {}
        for c, v in self.limit_vars.items():
            if v.get().strip():
                limits[c] = _parse_money(v.get(), f"{c} limit")
        return total, limits

    def suggest(self):
        try:
            total = _parse_money(self.total_var.get(), "Budget")
            split = self.bm.suggest_split(total, self.month_var.get())
        except ValidationError as e:
            show_warning(str(e))
            return
        for c, v in self.limit_vars.items():
            v.set(f"{split.get(c, 0):,.0f}" if split.get(c) else "")

    def save(self):
        try:
            total, limits = self._read_fields()
            self.bm.set_budget(self.month_var.get().strip(), total, limits)
            self.bm.save()
        except ValidationError as e:
            show_warning(str(e))
            return
        except OSError as e:
            show_warning(f"Cannot save budget file:\n{e}", "Save error")
            return
        self.refresh()
        if self.on_change:
            self.on_change()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        try:
            st = self.bm.status(self.dm.df, self.month_var.get().strip())
        except ValidationError as e:
            show_warning(str(e))
            return
        if st is None:
            self.lbl_overview.config(text="No budget for this month yet. Enter an amount and press Save Budget.")
            self.lbl_today.config(text="")
            self.bar["value"] = 0
            return

        self.lbl_overview.config(text=(
            f"Budget: {st['total']:,.0f}   |   Spent: {st['spent']:,.0f}   |   "
            f"Remaining: {st['remaining']:,.0f}\n"
            f"Average per day: {st['base_daily']:,.0f}  ({st['days_in_month']} days, "
            f"{st['days_left']} days left)"),
            fg=RED if st["remaining"] < 0 else GREEN)
        self.bar["value"] = min(100, st["spent"] / st["total"] * 100)

        if st["is_current"]:
            self.lbl_today.config(
                text=(f"Max you can spend today: {st['allowed_today']:,.0f}   |   "
                      f"Spent today: {st['spent_today']:,.0f}   |   Left today: {st['left_today']:,.0f}"),
                fg=RED if st["left_today"] < 0 else GREEN)
        else:
            self.lbl_today.config(text="(Not the current month - no daily allowance)", fg=self.default_fg)

        for c in st["categories"]:
            self.tree.insert("", "end", tags=("over",) if c["state"] != "OK" else (), values=(
                c["category"], f"{c['daily']:,.0f}", f"{c['spent_today']:,.0f}",
                f"{c['left_today']:,.0f}", f"{c['spent_month']:,.0f}",
                f"{c['month_cap']:,.0f}", c["state"]))