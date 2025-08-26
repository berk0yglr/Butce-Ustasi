import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DB_NAME = 'finance_premium.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

class CustomButton(ttk.Button):
    def __init__(self, master=None, **kw):
        super().__init__(master=master, **kw)
        self.default_bg = "#0078d7"
        self.default_fg = "white"
        self.hover_bg = "#005a9e"
        self.configure(style="Custom.TButton")
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.configure(style="Hover.TButton")

    def on_leave(self, e):
        self.configure(style="Custom.TButton")

class FinanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Premium Finans Yönetim Uygulaması")
        self.geometry("900x650")
        self.configure(bg="#f9f9f9")

        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        self.style.configure("Custom.TButton",
                             background="#0078d7",
                             foreground="white",
                             font=('Segoe UI', 10, 'bold'),
                             borderwidth=0,
                             focusthickness=3,
                             focuscolor='none',
                             padding=8)
        self.style.map("Custom.TButton",
                       background=[('active', '#005a9e')],
                       foreground=[('active', 'white')])

        self.style.configure("Hover.TButton",
                             background="#005a9e",
                             foreground="white",
                             font=('Segoe UI', 10, 'bold'),
                             borderwidth=0,
                             padding=8)

        self.selected_transaction_id = None

        self.create_widgets()
        self.load_transactions()
        self.draw_chart()

    def create_widgets(self):
        form_frame = ttk.LabelFrame(self, text="İşlem Ekle / Güncelle", padding=15)
        form_frame.pack(fill='x', padx=15, pady=10)

        ttk.Label(form_frame, text="Tür:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(form_frame, textvariable=self.type_var, values=["Gelir", "Gider"], state="readonly", width=15)
        self.type_combo.grid(row=0, column=1, sticky='w', padx=5, pady=5)
        self.type_combo.current(0)

        ttk.Label(form_frame, text="Kategori:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.category_entry = ttk.Entry(form_frame, width=20)
        self.category_entry.grid(row=0, column=3, sticky='w', padx=5, pady=5)

        ttk.Label(form_frame, text="Tutar (TL):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.amount_entry = ttk.Entry(form_frame, width=20)
        self.amount_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(form_frame, text="Tarih:").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.date_entry = DateEntry(form_frame, date_pattern='yyyy-MM-dd', width=18)
        self.date_entry.grid(row=1, column=3, sticky='w', padx=5, pady=5)

        self.add_update_btn = CustomButton(form_frame, text="Ekle", command=self.add_or_update_transaction)
        self.add_update_btn.grid(row=2, column=0, columnspan=4, pady=10, sticky='ew')

        table_frame = ttk.Frame(self)
        table_frame.pack(fill='both', expand=True, padx=15, pady=10)

        columns = ("ID", "Tür", "Kategori", "Tutar", "Tarih")
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse')
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Kategori":
                self.tree.column(col, width=150)
            elif col == "ID":
                self.tree.column(col, width=40, anchor='center')
            else:
                self.tree.column(col, width=100, anchor='center')
        self.tree.pack(side='left', fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=15, pady=5)

        self.delete_btn = CustomButton(btn_frame, text="Seçili İşlemi Sil", command=self.delete_transaction)
        self.delete_btn.pack(side='left', padx=5)

        self.clear_btn = CustomButton(btn_frame, text="Formu Temizle", command=self.clear_form)
        self.clear_btn.pack(side='left', padx=5)

        self.report_btn = CustomButton(btn_frame, text="Aylık Rapor Göster", command=self.show_monthly_report)
        self.report_btn.pack(side='right', padx=5)

        chart_frame = ttk.LabelFrame(self, text="Gelir - Gider Grafiği", padding=10)
        chart_frame.pack(fill='both', padx=15, pady=10, expand=True)

        self.figure = plt.Figure(figsize=(8, 2.5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(top=0.85, bottom=0.25, left=0.15, right=0.95)

        self.chart_canvas = FigureCanvasTkAgg(self.figure, chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill='both', expand=True)

    def add_or_update_transaction(self):
        t_type = self.type_var.get().lower()
        if t_type == "gelir":
            t_type = "income"
        elif t_type == "gider":
            t_type = "expense"

        category = self.category_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        date_str = self.date_entry.get_date().strftime('%Y-%m-%d')

        if not category or not amount_str:
            messagebox.showwarning("Eksik Bilgi", "Lütfen kategori ve tutar alanlarını doldurun.")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Hatalı Tutar", "Lütfen geçerli bir pozitif sayı girin.")
            return

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        if self.selected_transaction_id is None:
            c.execute('INSERT INTO transactions (type, category, amount, date) VALUES (?, ?, ?, ?)',
                      (t_type, category, amount, date_str))
            messagebox.showinfo("Başarılı", "İşlem eklendi.")
        else:
            c.execute('UPDATE transactions SET type=?, category=?, amount=?, date=? WHERE id=?',
                      (t_type, category, amount, date_str, self.selected_transaction_id))
            messagebox.showinfo("Başarılı", "İşlem güncellendi.")
            self.selected_transaction_id = None
            self.add_update_btn.config(text="Ekle")

        conn.commit()
        conn.close()

        self.clear_form()
        self.load_transactions()
        self.draw_chart()

    def load_transactions(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT id, type, category, amount, date FROM transactions ORDER BY date DESC')
        rows = c.fetchall()
        conn.close()

        for row in rows:
            display_type = "Gelir" if row[1] == "income" else "Gider"
            self.tree.insert("", tk.END, values=(row[0], display_type, row[2], f"{row[3]:.2f}", row[4]))

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        values = item['values']
        self.selected_transaction_id = values[0]

        self.type_var.set("Gelir" if values[1] == "Gelir" else "Gider")
        self.category_entry.delete(0, tk.END)
        self.category_entry.insert(0, values[2])
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.insert(0, values[3])
        self.date_entry.set_date(datetime.strptime(values[4], '%Y-%m-%d'))

        self.add_update_btn.config(text="Güncelle")

    def delete_transaction(self):
        if self.selected_transaction_id is None:
            messagebox.showwarning("Seçim Yok", "Lütfen silmek için bir işlem seçin.")
            return

        if messagebox.askyesno("Onay", "Seçili işlemi silmek istediğinize emin misiniz?"):
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('DELETE FROM transactions WHERE id = ?', (self.selected_transaction_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Başarılı", "İşlem silindi.")
            self.selected_transaction_id = None
            self.add_update_btn.config(text="Ekle")
            self.clear_form()
            self.load_transactions()
            self.draw_chart()

    def clear_form(self):
        self.type_combo.current(0)
        self.category_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.date_entry.set_date(datetime.today())
        self.selected_transaction_id = None
        self.add_update_btn.config(text="Ekle")
        self.tree.selection_remove(self.tree.selection())

    def show_monthly_report(self):
        report_win = tk.Toplevel(self)
        report_win.title("Aylık Rapor")
        report_win.geometry("400x350")
        report_win.resizable(False, False)

        ttk.Label(report_win, text="Yıl:").pack(pady=5)
        year_entry = ttk.Entry(report_win)
        year_entry.pack()

        ttk.Label(report_win, text="Ay (1-12):").pack(pady=5)
        month_entry = ttk.Entry(report_win)
        month_entry.pack()

        result_label = ttk.Label(report_win, text="", justify='left')
        result_label.pack(padx=10, pady=10)

        def generate_report():
            try:
                year = int(year_entry.get())
                month = int(month_entry.get())
                if not (1 <= month <= 12):
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Hatalı Giriş", "Lütfen geçerli bir yıl ve ay girin.")
                return

            start_date = f"{year}-{month:02d}-01"
            end_date = f"{year}-{month:02d}-31"

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('SELECT type, SUM(amount) FROM transactions WHERE date BETWEEN ? AND ? GROUP BY type',
                      (start_date, end_date))
            results = c.fetchall()

            income = 0
            expense = 0
            for t_type, total in results:
                if t_type == 'income':
                    income = total if total else 0
                elif t_type == 'expense':
                    expense = total if total else 0

            report_text = f"{year}-{month:02d} Aylık Rapor\n"
            report_text += f"Toplam Gelir: {income:.2f} TL\n"
            report_text += f"Toplam Gider: {expense:.2f} TL\n"
            report_text += f"Bakiye: {income - expense:.2f} TL\n\n"

            c.execute('SELECT category, SUM(amount) FROM transactions WHERE type = "income" AND date BETWEEN ? AND ? GROUP BY category', (start_date, end_date))
            income_by_cat = c.fetchall()
            c.execute('SELECT category, SUM(amount) FROM transactions WHERE type = "expense" AND date BETWEEN ? AND ? GROUP BY category', (start_date, end_date))
            expense_by_cat = c.fetchall()
            conn.close()

            report_text += "Gelir Kategorileri:\n"
            for cat, total in income_by_cat:
                report_text += f"  {cat}: {total:.2f} TL\n"

            report_text += "\nGider Kategorileri:\n"
            for cat, total in expense_by_cat:
                report_text += f"  {cat}: {total:.2f} TL\n"

            result_label.config(text=report_text)

        gen_btn = CustomButton(report_win, text="Raporu Göster", command=generate_report)
        gen_btn.pack(pady=10)

    def draw_chart(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('SELECT type, SUM(amount) FROM transactions GROUP BY type')
        results = c.fetchall()
        conn.close()

        income = 0
        expense = 0
        for t_type, total in results:
            if t_type == 'income':
                income = total if total else 0
            elif t_type == 'expense':
                expense = total if total else 0

        self.ax.clear()

        categories = ['Gelir', 'Gider']
        values = [income, expense]
        colors = ['#4a90e2', '#e94e4e']

        bars = self.ax.bar(categories, values, color=colors, width=0.3)

        for bar in bars:
            height = bar.get_height()
            self.ax.annotate(f'{height:.2f} TL',
                             xy=(bar.get_x() + bar.get_width() / 2, height),
                             xytext=(0, 5),
                             textcoords="offset points",
                             ha='center', va='bottom',
                             fontsize=10,
                             fontweight='bold',
                             color='#333')

        self.ax.set_title('Toplam Gelir ve Gider', fontsize=14, fontweight='bold', color='#222')
        self.ax.set_ylabel('TL', fontsize=12)
        self.ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 10)
        self.ax.grid(axis='y', linestyle='--', alpha=0.7)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#888')
        self.ax.spines['bottom'].set_color('#888')

        self.chart_canvas.draw()


if __name__ == "__main__":
    init_db()
    app = FinanceApp()
    app.mainloop()
