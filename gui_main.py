"""Vai trò 2 - GUI Lead: cửa sổ chính, thanh nút, bộ lọc, Treeview."""



import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from manager import DataManager
from gui_forms import AddTransactionForm
from gui_forms import BudgetWindow
from manager import BudgetManager
import chart_manager as charts
from validator import safe_divide


class FinanceApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Personal Finance Tracker")
        root.geometry("900x560")
        self.dm = DataManager()
        self.bm = BudgetManager()
        self.budget_win = None

        # --- Button bar ---
        bar = ttk.Frame(root, padding=8)
        bar.pack(fill="x")
        for text, cmd in [("Load Data", self.load_data),
                          ("Add Transaction", self.open_form),
                          ("Monthly Balance", self.show_monthly),
                          ("Top Categories", self.show_bar),
                          ("3D Chart", self.show_3d),
                          ("Budget", self.open_budget)]:
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=4)

        # --- Filter ---
        flt = ttk.LabelFrame(root, text="Filter", padding=6)
        flt.pack(fill="x", padx=8)
        self.filter_var = tk.StringVar(value="Both")
        for v in ("Income", "Expense", "Both"):
            ttk.Radiobutton(flt, text=v, variable=self.filter_var, value=v,
                            command=self.refresh_table).pack(side="left", padx=10)

        # --- Treeview ---
        wrap = ttk.Frame(root)
        wrap.pack(fill="both", expand=True, padx=8, pady=8)
        cols = ("Date", "Category", "Amount", "Type", "Note")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings")
        for c, w in zip(cols, (100, 120, 110, 90, 300)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="e" if c == "Amount" else "w")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.tag_configure("income", foreground="#2e9e5b")
        self.tree.tag_configure("expense", foreground="#d64545")
        self.tree.tag_configure("error", background="#ffcccc", foreground="#b00000")

        self.status = ttk.Label(root, text="", anchor="w", padding=6)
        self.status.pack(fill="x")

        self.auto_load()

    # ---------- Dữ liệu ----------
    def auto_load(self):
        try:
            self.dm.load_data()
        except FileNotFoundError:
            pass  # lần đầu chạy chưa có file -> bảng trống, không crash
        except Exception as e:
            messagebox.showwarning("Load error", str(e))
        self.refresh_table()

    def load_data(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            self.dm.load_data(path)
        except FileNotFoundError:
            messagebox.showwarning("File not found", "Không tìm thấy file đã chọn.")
            return
        except Exception as e:
            messagebox.showwarning("Invalid CSV", f"File CSV lỗi định dạng:\n{e}")
            return
        self.refresh_table()
        if self.dm.error_rows:
            messagebox.showwarning(
                "Warning", f"{len(self.dm.error_rows)} dòng bị lỗi (tô đỏ trong bảng).")

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for _, r in self.dm.get_filtered_data(self.filter_var.get()).iterrows():
            tag = "income" if r["amount"] > 0 else "expense"
            self.tree.insert("", "end", tags=(tag,), values=(
                r["date"].strftime("%Y-%m-%d"), r["category"],
                f"{r['amount']:,.0f}", r["type"], r["note"]))
        for e in self.dm.error_rows:          # dòng lỗi -> đỏ
            self.tree.insert("", "end", tags=("error",), values=(
                e["date"], e["category"], e["amount"], e["type"],
                f"⚠ {e['_error']}"))
        inc = self.dm.df.loc[self.dm.df["amount"] > 0, "amount"].sum()
        exp = -self.dm.df.loc[self.dm.df["amount"] < 0, "amount"].sum()
        rate = safe_divide(inc - exp, inc) * 100   # không lỗi chia 0
        self.status.config(text=f"Balance: {self.dm.total_balance():,.0f}   |   "
                                f"Income: {inc:,.0f}   Expense: {exp:,.0f}   |   "
                                f"Savings rate: {rate:.1f}%" + self._budget_hint())

    # ---------- Cửa sổ phụ ----------
    def open_form(self):
        AddTransactionForm(self.root, self.dm, self.on_transaction_saved)

    def show_monthly(self):
        mb = self.dm.calculate_monthly_balance()
        if mb.empty:
            messagebox.showinfo("Monthly Balance", "Chưa có dữ liệu.")
            return
        win = tk.Toplevel(self.root)
        win.title("Monthly Balance")
        t = ttk.Treeview(win, columns=("Month", "Income", "Expense", "Balance"),
                         show="headings", height=min(len(mb), 15))
        for c in ("Month", "Income", "Expense", "Balance"):
            t.heading(c, text=c)
            t.column(c, width=120, anchor="e")
        for _, r in mb.iterrows():
            t.insert("", "end", values=(r["month"], f"{r['income']:,.0f}",
                                        f"{r['expense']:,.0f}", f"{r['balance']:,.0f}"))
        t.pack(padx=10, pady=10)

    def _chart_window(self, title, fig):
        win = tk.Toplevel(self.root)
        win.title(title)
        charts.embed(fig, win)

    def show_bar(self):
        self._chart_window("Top Categories", charts.build_bar_figure(self.dm.top_categories()))

    def show_3d(self):
        self._chart_window("3D Chart", charts.build_3d_figure(self.dm.df))

    # ---------- Ngân sách ----------
    def open_budget(self):
        self.budget_win = BudgetWindow(self.root, self.dm, self.bm, on_change=self.refresh_table)

    def _budget_hint(self):
        try:
            st = self.bm.status(self.dm.df)
        except Exception:
            return ""
        if not st or not st["is_current"]:
            return ""
        return f"   |   Left today: {st['left_today']:,.0f}"

    def on_transaction_saved(self):
        """Gọi sau khi lưu giao dịch: cập nhật bảng, cửa sổ ngân sách và cảnh báo vượt mức."""
        self.refresh_table()
        if self.budget_win is not None and self.budget_win.win.winfo_exists():
            self.budget_win.refresh()
        alerts = self.bm.check_alerts(self.dm.df)
        if alerts:
            messagebox.showwarning("Budget Alert", "\n".join(alerts))