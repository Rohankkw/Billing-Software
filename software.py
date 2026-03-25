import random
from email.message import EmailMessage
from tkinter import *
from tkinter.messagebox import askyesno, showerror, showinfo, showwarning
from tkinter.ttk import Combobox, Treeview
import sqlite3
from tkinter import ttk
from collections import defaultdict
from datetime import *
from fpdf import *
import smtplib
import os
import re

class Billing:
    def __init__(self):

        self.item_menu = {}
        self.order_items = []
        self.order_counter = 1
        self.current_widgets = []
        self.current_second_button = []
        self.billing_menu_global_binding_set = False
        self.is_logged_in = False

        #for updated item to fetch in combobox
        self.updated_items = {}

        #for date tracking
        self.daily_track_date = ""

        self.init_database()
        self.load_item_menu()
        self.main_window()
        self.navigation_frame()
        self.initialize_login_state()

        try:
            self.root.mainloop()
        except:
            pass
        #------ profile variables -----#
        self.shop_name=""
        self.gst_number=""
        self.email = ""
        self.app_password_value = ""
        self.login_email_value = ""
        self.account_login_password = ""

    #------- calling profile variables --------#
    def get_latest_profile_row(self):
        try:
            self.c.execute(
                "SELECT rowid, shop_name, gst_number, email, app_password, login_email, account_password, last_login_date "
                "FROM profile ORDER BY rowid DESC LIMIT 1"
            )
            return self.c.fetchone()
        except:
            return None

    def calling_profile_variables(self):
        row = self.get_latest_profile_row()

        if row:  # if there is data
            _, name, gst, email, app_password, login_email, account_password, _ = row
        else:
            name, gst, email, app_password, login_email, account_password = None, None, None, None, None, None

        # Assign to variables with fallback
        self.shop_name = name if name else "Not Provided"
        self.gst_number = gst if gst else "Not Provided"
        self.email = email
        self.app_password_value = app_password if app_password else ""
        self.login_email_value = login_email if login_email else ""
        self.account_login_password = account_password if account_password else ""

    # --- creating main database ---
    def init_database(self):
        try:
            self.conn = sqlite3.connect('billing_sft.db')
            self.c = self.conn.cursor()

            #database for main menu
            self.c.execute("create table if not exists menu(name text, price integer)")
            self.c.execute("create table if not exists daily_track(id integer, name text, total_sold integer, unit_price float, total_revenue float)")
            self.c.execute("create table if not exists monthly_track(rank integer, time text, total_revenue float, top_selling text)")
            self.c.execute("create table if not exists profile(shop_name text, gst_number text, email text, app_password text, login_email text, account_password text, last_login_date text)")
            self.c.execute("PRAGMA table_info(profile)")
            existing_columns = [column[1] for column in self.c.fetchall()]
            if "app_password" not in existing_columns:
                self.c.execute("ALTER TABLE profile ADD COLUMN app_password text")
            if "login_email" not in existing_columns:
                self.c.execute("ALTER TABLE profile ADD COLUMN login_email text")
            if "account_password" not in existing_columns:
                self.c.execute("ALTER TABLE profile ADD COLUMN account_password text")
            if "last_login_date" not in existing_columns:
                self.c.execute("ALTER TABLE profile ADD COLUMN last_login_date text")

            self.c.execute("SELECT COUNT(*) FROM profile")
            profile_count = self.c.fetchone()[0]

            if profile_count == 0:
                self.c.execute(
                    "INSERT INTO profile (shop_name, gst_number, email, app_password, login_email, account_password, last_login_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (None, None, None, None, None, "Admin@123", None)
                )
            else:
                self.c.execute(
                    "UPDATE profile SET account_password = ? WHERE account_password IS NULL OR TRIM(account_password) = ''",
                    ("Admin@123",)
                )
                self.c.execute(
                    "UPDATE profile SET login_email = email WHERE (login_email IS NULL OR TRIM(login_email) = '') AND email IS NOT NULL AND TRIM(email) <> ''"
                )
            self.conn.commit()
        except Exception as e:
            showerror("Database Error", f"Problem {e}")


    #------- OTP GENERATING --------#
    def otp_generating(self):
        self.otp_number = str(random.randint(1000,9999))


    def otp_expired(self):
        self.otp_number = None

    def guarded_showerror(self, title, message, button=None, reset_text=None):
        if getattr(self, "_error_dialog_open", False):
            return

        self._error_dialog_open = True

        try:
            if button and button.winfo_exists():
                button.config(state=DISABLED)

            showerror(title, message)
        finally:
            try:
                if button and button.winfo_exists():
                    if reset_text is not None:
                        button.config(text=reset_text)
                    button.config(state=NORMAL)
            except:
                pass

            self._error_dialog_open = False

    def add_password_toggle(self, parent, entry_widget):
        def toggle_password():
            if entry_widget.cget("show") == "":
                entry_widget.config(show="*")
                toggle_btn.config(text="Show")
            else:
                entry_widget.config(show="")
                toggle_btn.config(text="Hide")

        toggle_btn = Button(
            parent,
            text="Show",
            font=('Arial', 10, 'bold'),
            width=6,
            bg='#5D688A',
            fg='white',
            command=toggle_password
        )
        toggle_btn.pack(side='left', padx=(6, 10), pady=10)
        return toggle_btn

    def get_saved_email_credentials(self):
        try:
            row = self.get_latest_profile_row()
            if row:
                _, _, _, email, app_password, _, _, _ = row
            else:
                email, app_password = None, None
        except:
            email, app_password = None, None

        self.email = email if email else None
        self.app_password_value = app_password if app_password else ""
        return self.email, self.app_password_value

    def get_login_credentials(self):
        try:
            row = self.get_latest_profile_row()
            if row:
                _, _, _, _, _, login_email, account_password, last_login_date = row
            else:
                login_email, account_password, last_login_date = None, None, None
        except:
            login_email, account_password, last_login_date = None, None, None

        self.account_login_password = account_password if account_password else ""
        self.login_email_value = login_email if login_email else ""
        return self.login_email_value, self.account_login_password, last_login_date

    def get_email_display_lines(self):
        sending_email, _ = self.get_saved_email_credentials()
        login_email, _, _ = self.get_login_credentials()

        sending_email = sending_email.strip() if sending_email else ""
        login_email = login_email.strip() if login_email else ""

        if sending_email and login_email:
            if sending_email.lower() == login_email.lower():
                return [f"Sending & Login Email: {sending_email}"]
            return [
                f"Sending Email: {sending_email}",
                f"Login Email: {login_email}"
            ]

        if sending_email:
            return [f"Sending Email: {sending_email}"]

        if login_email:
            return [f"Login Email: {login_email}"]

        return ["Email: Not Provided"]

    def show_mail_connection_error(self, context_text="send email"):
        showerror(
            "Connection Error",
            f"Unable to {context_text} because the internet or DNS connection is not available."
        )

    def send_email_message(self, sender_email, sender_password, message, context_text="send email"):
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=20) as smtp:
                smtp.login(sender_email, sender_password)
                smtp.send_message(message)
            return True
        except OSError:
            self.show_mail_connection_error(context_text)
        except smtplib.SMTPAuthenticationError:
            showerror("Authentication Error", "Your sending email or app password is incorrect.")
        except smtplib.SMTPException as e:
            showerror("Email Error", f"Unable to {context_text}: {e}")
        except Exception as e:
            showerror("Email Error", f"Unable to {context_text}: {e}")
        return False

    #---------- EMAIl Sending --------#
    def sending_otp_email(self):
        sender_email, sender_password = self.get_saved_email_credentials()

        if not sender_email or not sender_password:
            showerror("Email Setup Required", "Add your email and app password first.")
            return

        # Create the email
        msg = EmailMessage()
        msg['Subject'] = self.mail_subject
        msg['From'] = sender_email
        msg['To'] = self.mail_address
        msg.set_content(self.html_message)
        if self.html_message:
            msg.add_alternative(self.html_message, subtype='html')

        return self.send_email_message(sender_email, sender_password, msg, "send OTP email")

    # --- adding items to menu ---
    def load_item_menu(self):
        try:
            self.c.execute('Select name,price from menu')
            items = self.c.fetchall()

            self.item_menu.clear()
            self.updated_items.clear()

            for name, price in items:
                self.item_menu[name] = price
            for name, price in items:
                self.updated_items[name] = price
        except Exception as e:
            print(e)

    def main_window(self):
        self.root = Tk()
        self.root.title("Quick SVR - Billing System")
        self.root.state('zoomed')
        self.root.config(bg='#f0f0f0')

        try:
            self.logo = PhotoImage(file='..png')
            self.root.iconphoto(True, self.logo)
        except:
            pass

    def navigation_frame(self):
        self._nav_frame = Frame(self.root, bg='#2c3e50', width=200)
        self._nav_frame.pack(side='left', fill='y')
        self._nav_frame.pack_propagate(False)

        title_label = Label(self._nav_frame, text="Quick SVR", font=('Arial',16,'bold'),bg='#2c3e50', fg='white')
        title_label.pack(pady=20, fill='x')

        self.nav_buttons={}

        self.nav_buttons['billing'] = Button(self._nav_frame, text='🧾 Billing', font=('Arial',12),
                                             width=20,bg='white',fg='black', height=2,
                                             command=self.set_billing_page)
        self.nav_buttons['billing'].pack(fill='x', padx=10, pady=10)


        self.nav_buttons['update'] = Button(self._nav_frame, text='⚙️ Update',
                                             font=('Arial',12), width=20, height=2,
                                             bg='white', fg='black', command=self.set_update_page)
        self.nav_buttons['update'].pack(fill='x',padx=10, pady=10)


        self.nav_buttons['dashboard'] = Button(self._nav_frame, text='Dashboard', font=('Arial',12),
                                               width=20, height=2, bg='white', fg='black', command=self.dashboard_page)
        self.nav_buttons['dashboard'].pack(fill='x', padx=10, pady=10)


        self.nav_buttons['account'] = Button(self._nav_frame, text='Account', font=('Arial, 12'),
                                             width=20, height=2, bg='white', fg='black', command=self.accounts_page)
        self.nav_buttons['account'].pack(fill='x',padx=10, pady=10)

        extra_space = Frame(self._nav_frame,bg='#2c3e50')
        extra_space.pack(fill='both',expand=True)

        self.login_button = Button(self._nav_frame, text="Login", font=('Arial',12),
                                   width=20, height=2, bg='#27ae60',fg='white',
                                   command=self.open_login_window)
        self.login_button.pack(fill='x',pady=10,padx=10)

    # --- design to active button ---
    def set_active_button(self, active_page):
            for page, button in self.nav_buttons.items():
                if page == active_page:
                    button.config(bg='#3498db', fg='white')
                else:
                    button.config(bg='#ecf0f1', fg='black')

    def initialize_login_state(self):
        email, account_password, last_login_date = self.get_login_credentials()
        today = date.today().isoformat()

        if account_password:
            self.is_logged_in = last_login_date == today
        else:
            self.is_logged_in = True

        self.update_navigation_access()

        if self.is_logged_in:
            self.set_billing_page()
        else:
            self.show_login_page()

    def update_navigation_access(self):
        nav_state = NORMAL if self.is_logged_in else DISABLED

        for button in self.nav_buttons.values():
            try:
                button.config(state=nav_state)
            except:
                pass

        if self.is_logged_in:
            self.login_button.config(text="Logout", bg='#e74c3c', fg='white', command=self.logout_user, state=NORMAL)
        else:
            self.login_button.config(text="Login", bg='#27ae60', fg='white', command=self.open_login_window, state=NORMAL)

    def show_login_page(self):
        self.clear_page()
        for button in self.nav_buttons.values():
            try:
                button.config(bg='#ecf0f1', fg='black')
            except:
                pass

        self.login_page_frame = Frame(self.root, bg='white')
        self.login_page_frame.pack(fill='both', expand=True)
        self.current_widgets.append(self.login_page_frame)

        center_frame = Frame(self.login_page_frame, bg='white')
        center_frame.place(relx=0.5, rely=0.5, anchor='center')

        Label(center_frame, text="QUICK SVR", font=('Arial', 30, 'bold'),
              bg='white', fg='#9B177E').pack(pady=(0, 20))

        Label(center_frame, text="Quick SVR is a Product by Quick Blockchains",
              font=('Arial', 13), bg='white', fg='#444444').pack(pady=(0, 25))

        self.login_page_button = Button(
            center_frame,
            text="Login",
            font=('Arial', 14, 'bold'),
            width=18,
            height=2,
            bg='#27ae60',
            fg='white',
            command=self.open_login_window
        )
        self.login_page_button.pack()

    def open_login_window(self):
        email, account_password, _ = self.get_login_credentials()

        if not email or not account_password:
            self.guarded_showerror(
                "Login Not Ready",
                "Set an account email and password first from the account section.",
                getattr(self, "login_page_button", None)
            )
            return

        self.window_for_buttons()
        self.clear_second_window()

        main_frame = Frame(self.button_root, bg="#4A9782")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)

        login_frame = Frame(main_frame, bg='#F9F3EF', relief="raised", bd=2)
        login_frame.pack(fill='x', padx=10, pady=120)

        Label(login_frame, text="Daily Login", font=('Arial', 18, 'bold'),
              bg='#F9F3EF', fg='black').pack(pady=(20, 10))

        email_frame = Frame(login_frame, bg='#F9F3EF', relief="raised", bd=1)
        email_frame.pack(fill='x', padx=10, pady=10)

        Label(email_frame, text="Email:", font=('Arial', 12, 'bold'),
              bg='#F9F3EF', fg='black').pack(side='left', padx=10, pady=10)

        self.login_email_entry = ttk.Entry(email_frame, width=30)
        self.login_email_entry.pack(side='left', padx=10, pady=10)
        if email:
            self.login_email_entry.insert(0, email)

        password_frame = Frame(login_frame, bg='#F9F3EF', relief="raised", bd=1)
        password_frame.pack(fill='x', padx=10, pady=10)

        Label(password_frame, text="Password:", font=('Arial', 12, 'bold'),
              bg='#F9F3EF', fg='black').pack(side='left', padx=10, pady=10)

        self.login_password_entry = ttk.Entry(password_frame, width=30, show='*')
        self.login_password_entry.pack(side='left', padx=10, pady=10)
        self.add_password_toggle(password_frame, self.login_password_entry)

        self.login_submit_btn = Button(
            login_frame,
            text="Login",
            font=('Arial', 12, 'bold'),
            width=15,
            height=2,
            bg='#0D5EA6',
            fg='white',
            command=self.process_daily_login
        )
        self.login_submit_btn.pack(pady=(20, 30))

    def process_daily_login(self):
        email, account_password, _ = self.get_login_credentials()
        entered_email = self.login_email_entry.get().strip()
        entered_password = self.login_password_entry.get().strip()

        if entered_email != email or entered_password != account_password:
            self.guarded_showerror("Login Failed", "Incorrect email or password.", self.login_submit_btn)
            return

        try:
            self.c.execute("UPDATE profile SET last_login_date = ?", (date.today().isoformat(),))
            self.conn.commit()
        except Exception as e:
            self.guarded_showerror("Login Error", f"Problem: {e}", self.login_submit_btn)
            return

        self.is_logged_in = True
        self.update_navigation_access()
        self.close_popup_window()
        self.set_billing_page()

    def logout_user(self):
        try:
            self.c.execute("UPDATE profile SET last_login_date = NULL")
            self.conn.commit()
        except:
            pass

        self.is_logged_in = False
        self.update_navigation_access()
        self.show_login_page()

    #Clearing widgets to swtich page---
    def clear_page(self):
        if hasattr(self, "billing_menu_popup"):
            try:
                self.billing_menu_popup.withdraw()
            except:
                pass

        for widget in self.current_widgets:
            try:
                if widget and widget.winfo_exists:
                    widget.destroy()
            except:
                pass
        self.current_widgets.clear()


    #--- Clearing 2nd root windows widgets ---
    def clear_second_window(self):
        for widget in self.current_second_button:
            try:
                if widget and widget.winfo_exists:
                    widget.destroy()
            except:
                pass
        self.current_second_button.clear()

    def close_popup_window(self, event=None):
        try:
            try:
                for button_name in (
                    "generate_bill",
                    "update_profile_btn",
                    "change_email_btn",
                    "change_login_email_btn",
                    "change_pass_btn",
                ):
                    button = getattr(self, button_name, None)
                    if button and button.winfo_exists():
                        button.config(state=NORMAL)
            except:
                pass

            try:
                if hasattr(self, "four_btn_list"):
                    for button in self.four_btn_list:
                        if button and button.winfo_exists():
                            button.config(state=NORMAL)
            except:
                pass

            if hasattr(self, "button_root") and self.button_root.winfo_exists():
                try:
                    self.button_root.grab_release()
                except:
                    pass
                self.button_root.destroy()
        except:
            pass
        return "break" if event else None

    #--- second root windows ---
    def window_for_buttons(self):
        try:
            if hasattr(self, "button_root") and self.button_root.winfo_exists():
                self.button_root.destroy()
        except:
            pass

        self.button_root = Toplevel(self.root)
        self.button_root.title("Quick SVR")
        self.button_root.config(bg='white')
        self.button_root.geometry("500x600")
        self.button_root.transient(self.root)
        self.button_root.grab_set()
        self.button_root.bind("<Escape>", self.close_popup_window)
        self.button_root.protocol("WM_DELETE_WINDOW", self.close_popup_window)


    #------------ BIlling Page Configuration -------------#
    def set_billing_page(self):
        self.clear_page()
        self.set_active_button('billing')
        self.content_frame = Frame(self.root, bg='white')
        self.content_frame.pack(fill='both',expand=True)
        self.current_widgets.append(self.content_frame)

        head_frame = Frame(self.content_frame, bg="#9B177E", relief="raised", bd=3)
        head_frame.pack(fill='x', padx=20, pady=10)

        Label(head_frame, text="Quick SVR - Billing System", font=('Arial', 18, 'bold'),
              bg='#9B177E', fg='white').pack(fill='x', padx=20, pady=10)

        item_frame = Frame(self.content_frame, bg='#FAF9F6', relief='raised', bd=2)
        item_frame.pack(fill='x', padx=20, pady=10)

        controls_frame = Frame(item_frame, bg='#FAF9F6')
        controls_frame.pack(fill='x', padx=20, pady=15)

        Label(controls_frame, text='Select Item:', font=('Arial', 12),
              bg='#FAF9F6').pack(side='left', padx=10)

        self.selected_billing_item = ""
        self.billing_menu_items = []
        self.item_search_var = StringVar()

        self.item_search_wrapper = Frame(controls_frame, bg='#FAF9F6')
        self.item_search_wrapper.pack(side='left', padx=10)

        self.item_search_entry = ttk.Entry(
            self.item_search_wrapper,
            width=25,
            textvariable=self.item_search_var
        )
        self.item_search_entry.pack()
        self.item_search_entry.bind("<KeyRelease>", self.filter_billing_items)
        self.item_search_entry.bind("<Down>", self.focus_billing_menu)
        self.item_search_entry.bind("<Return>", self.handle_billing_entry_return)
        self.item_search_entry.bind("<Button-1>", self.show_billing_menu)
        self.item_search_entry.bind("<Escape>", self.hide_billing_menu)

        self.create_billing_menu_popup()
        if not self.billing_menu_global_binding_set:
            self.root.bind_all("<Button-1>", self.handle_global_billing_click, add="+")
            self.billing_menu_global_binding_set = True

        self.refresh_billing_item_menu()

        Label(controls_frame, text="Quantity", font=('Arial', 12),
              bg='#FAF9F6', fg='black').pack(side='left', padx=10)

        self.quantity_entry = ttk.Entry(controls_frame, width=15)
        self.quantity_entry.pack(side='left', padx=10)

        self.add_button = Button(
            controls_frame, text="Add Item", bg='#A4DD00', fg='white',
            font=('Arial', 12, 'bold'), command=self.add_to_combo
        )
        self.add_button.pack(side='left', padx=10)

        self.remove_button = Button(
            controls_frame, text="Remove Item", bg='#FF3F33', fg='white',
            font=('Arial', 12, 'bold'), command=self.remove_in_tree
        )
        self.remove_button.pack(side='left', padx=10)

        self.datetime_label = Label(controls_frame, text="", font=('Arial', 12),
                                    bg='#FAF9F6', fg='black')
        self.datetime_label.pack(side='right', padx=10)
        self.update_datetime()

        self.order_frame = Frame(self.content_frame, bg='#FAF9F6', relief='raised', bd=2)
        self.order_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.tree_frame = Frame(self.order_frame, bg='white', relief='raised')
        self.tree_frame.pack(fill="both", pady=20, padx=10)

        self.order_tree = Treeview(
            self.tree_frame,
            columns=("Order", "Item", "Quantity", "Price"),
            show="headings",
            height=18
        )

        self.order_tree.heading("Order", text="Order #")
        self.order_tree.heading("Item", text="Item Name")
        self.order_tree.heading("Quantity", text="Quantity")
        self.order_tree.heading("Price", text="Price (₹)")

        self.order_tree.column("Order", width=80, anchor="center")
        self.order_tree.column("Item", width=200, anchor="center")
        self.order_tree.column("Quantity", width=100, anchor="center")
        self.order_tree.column("Price", width=100, anchor="center")

        scrollbar = Scrollbar(self.tree_frame, orient="vertical", command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.order_tree.pack(side="left", fill="both", expand=True)

        totaling_frame = Frame(self.order_frame, bg='#B2BEB5', height=50)
        totaling_frame.pack(fill='x', padx=10, pady=10)
        totaling_frame.pack_propagate(False)

        self.total_item_order = StringVar(value='Total Items: 0')
        self.total_price_order = StringVar(value='Total Amount: ₹0')

        Label(totaling_frame, textvariable=self.total_price_order,
              font=("Arial", 14, "bold"), bg='#B2BEB5').pack(side="right", padx=100, pady=10)

        Label(totaling_frame, textvariable=self.total_item_order,
              font=('Arial', 14, 'bold'), bg='#B2BEB5', fg='black').pack(side="right", padx=20, pady=10)

        self.button_frame = Frame(self.content_frame, bg='#FAF9F6', relief="raised", bd=2)
        self.button_frame.pack(fill='x', padx=20, pady=10)

        self.generate_bill = Button(self.button_frame, text='Generate Bill', font=('Arial', 12, 'bold'),
                                    width=15, height=2, bg='#28a745', fg='white', command=self.bill_generating)
        self.generate_bill.pack(side='right', padx=10, pady=10)

        self.clear_btn = Button(self.button_frame, text="Clear All", font=('Arial', 12, 'bold'),
                                width=15, height=2, bg='#ffc107', fg='white', command=self.clear_tree)
        self.clear_btn.pack(side='right', padx=10, pady=10)

        self.sale_btn = Button(self.button_frame, text="Toady's Sale", font=('Arial', 12, 'bold'),
                               width=15, height=2, bg='#17a2b8', fg='white', command=self.dashboard_page)
        self.sale_btn.pack(side='right', padx=10, pady=10)

        self.clear_tree()


    #pdf making-----------#
    def generate_bill_pdf(self):
        pdf = FPDF()
        pdf.add_page()
        filename = "restaurant_bill.pdf"
        customer_name = self.customer_name_entry.get().strip()
        customer_email = self.customer_email_entry.get().strip()
        if not customer_name:
            customer_name = "Walk-In Customer"

        #pattern to get a proper email format .gmail,hotmail,yahoo,domainname

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}$'

        if not re.match(pattern, customer_email) or not customer_email:
            showerror("Error", "Incorrect email format!")
            self.button_root.destroy()
            self.clear_second_window()
            self.window_for_buttons()
            self.single_order_emailing()
            return

        timestamp = datetime.now().strftime("%A_%I_%M_%S_%p")
        table_data  = self.order_tree.get_children()
        if not table_data:
            showerror("Error","No Order Placed yet")
            self.button_root.destroy()
            self.clear_second_window()
            self.window_for_buttons()
            self.single_order_emailing()
            return


        # Safe filename using customer name + timestamp
        safe_customer_name =customer_name.strip().replace(" ", "_")
        filename = f"{safe_customer_name}_{timestamp}.pdf"


        # Save to Desktop
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        path = os.path.join(desktop_path, 'Quick SVR', 'Customer Bills')
        os.makedirs(path, exist_ok=True)
        full_path = os.path.join(desktop_path, path, filename)
        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "RESTAURANT BILL", ln=True, align='C')
        pdf.ln(5)

        # Customer & Date
        pdf.set_font("Arial", '', 12)
        date_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        pdf.cell(0, 10, f"Customer: {customer_name}", ln=True)
        pdf.cell(0, 10, f"Customer Email: {customer_email}", ln=True)
        pdf.cell(0, 10, f"Date: {date_str}", ln=True)
        pdf.ln(5)

        # Table Header
        pdf.set_font("Arial", 'B', 12)
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(20, 10, "Item", border=1, align='C', fill=True)
        pdf.cell(70, 10, "Qty", border=1, align='C', fill=True)
        pdf.cell(40, 10, "Quantity", border=1, align='C', fill=True)
        pdf.cell(50, 10, "Total (Rs)", border=1, align='C', fill=True)
        pdf.ln()

        # Table Rows
        pdf.set_font("Arial", '', 12)
        grand_total = 0
        for child in self.order_tree.get_children():
            values = self.order_tree.item(child)["values"]
            order = str(values[0])  # Convert to string
            name = str(values[1])
            price = float(str(values[2]).replace("₹", "")) if isinstance(values[2], str) else float(values[2])
            total = float(str(values[3]).replace("₹", "")) if isinstance(values[3], str) else float(values[3])
            grand_total += total

            pdf.cell(20, 10, str(order), border=1)
            pdf.cell(70, 10, str(name), border=1, align='C')
            pdf.cell(40, 10, f"{price:.2f}", border=1, align='C')
            pdf.cell(50, 10, f"{total:.2f}", border=1, align='C')
            pdf.ln()

        # Grand Total
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(130, 10, "GRAND TOTAL", border=1, align='R')
        pdf.cell(50, 10, f"Rs {grand_total:.2f}", border=1, align='C')
        pdf.ln(15)

        # Thank You
        pdf.set_font("Arial", 'I', 12)
        pdf.cell(0, 10, "Thank you for dining with us!", ln=True, align='C')

        # Save File
        pdf.output(full_path)
        # print(f"PDF saved as {full_path}")
        self.sending_email(full_path)

    def sending_email(self, file_path):
        def close_btn():
            self.button_root.destroy()
            self.generate_bill.config(state=NORMAL)

        self.owner_email, self.app_password = self.get_saved_email_credentials()
        if not self.owner_email or not self.app_password:
            showerror("Email Setup Required", "Add your email and app password first.")
            close_btn()
            return

        message = EmailMessage()
        message['Subject'] = 'Your Restaurant Bill'
        message['From'] = self.owner_email
        message['To'] = self.customer_email_entry.get().strip()
        message.set_content(
            'Dear Customer,\n\nHere is your Bill. Thank you for visiting us!\n\nRegards,\nRestaurant Team')

        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(file_path)

        message.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

        if self.send_email_message(self.owner_email, self.app_password, message, "send bill email"):
            showinfo("Success", "Email send successfully")

        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        close_btn()
        #---- for sharing data in daily_tracking-----#
        self.load_sales_data()


    # --- Add Item Button ----
    def add_to_combo(self):
        item = self.get_selected_billing_item()
        quantity = self.quantity_entry.get()

        if item == "":
            showerror("ERROR", "SELECT MENU ITEMS")
            return

        if not quantity.isdigit():
            showerror("Error", "Enter a valid Quantity")
            return

        try:
            quantity = int(quantity)
            if quantity <= 0:
                quantity = 1

            unit_price = self.updated_items[item]
            item_found = False

            for order in self.order_items:
                if order[0] == item:
                    order[1] += quantity
                    order[2] = order[1] * unit_price
                    item_found = True
                    break

            if not item_found:
                total_price = unit_price * quantity
                self.order_items.append([item, quantity, total_price])

            self.update_order_tree()

        except Exception as e:
            print(e)

        self.quantity_entry.delete(0, END)
        self.selected_billing_item = ""
        self.item_search_var.set("")
        self.refresh_billing_item_menu()
        self.hide_billing_menu()

    def create_billing_menu_popup(self):
        self.billing_menu_popup = Toplevel(self.root)
        self.billing_menu_popup.withdraw()
        self.billing_menu_popup.overrideredirect(True)
        self.billing_menu_popup.transient(self.root)
        self.billing_menu_popup.configure(bg='white')

        popup_frame = Frame(self.billing_menu_popup, bg='white', relief='solid', bd=1)
        popup_frame.pack(fill='both', expand=True)

        self.billing_menu_scrollbar = Scrollbar(popup_frame, orient='vertical')
        self.billing_item_listbox = Listbox(
            popup_frame,
            height=6,
            width=32,
            font=('Arial', 10),
            exportselection=False,
            activestyle='none',
            yscrollcommand=self.billing_menu_scrollbar.set
        )
        self.billing_menu_scrollbar.config(command=self.billing_item_listbox.yview)

        self.billing_item_listbox.pack(side='left', fill='both', expand=True)
        self.billing_menu_scrollbar.pack(side='right', fill='y')

        self.billing_item_listbox.bind("<<ListboxSelect>>", self.select_billing_menu_item)
        self.billing_item_listbox.bind("<Double-Button-1>", self.select_billing_menu_item)
        self.billing_item_listbox.bind("<Return>", self.select_billing_menu_item)
        self.billing_item_listbox.bind("<Escape>", self.hide_billing_menu)

    def refresh_billing_item_menu(self, search_text=""):
        if not hasattr(self, "billing_item_listbox"):
            return

        search_value = search_text.strip().lower()
        self.billing_menu_items = []
        self.billing_item_listbox.delete(0, END)

        for item_name, price in self.updated_items.items():
            if search_value and search_value not in item_name.lower():
                continue
            self.billing_menu_items.append(item_name)
            self.billing_item_listbox.insert(END, f"{item_name} - ₹{price}")

        if self.billing_menu_items:
            self.billing_item_listbox.selection_clear(0, END)
            self.billing_item_listbox.selection_set(0)
        else:
            self.selected_billing_item = ""
            self.hide_billing_menu()

    def filter_billing_items(self, event=None):
        self.selected_billing_item = ""
        self.refresh_billing_item_menu(self.item_search_var.get())
        if self.billing_menu_items:
            self.show_billing_menu()

    def select_billing_menu_item(self, event=None):
        selection = self.billing_item_listbox.curselection()
        if not selection:
            return

        item_name = self.billing_menu_items[selection[0]]
        self.selected_billing_item = item_name
        self.item_search_var.set(item_name)
        self.item_search_entry.icursor(END)
        self.hide_billing_menu()
        self.quantity_entry.focus_set()

    def handle_billing_entry_return(self, event=None):
        typed_item = self.item_search_var.get().strip()

        if typed_item in self.updated_items:
            self.selected_billing_item = typed_item
            self.hide_billing_menu()
            self.quantity_entry.focus_set()
            return "break"

        if self.billing_menu_items:
            self.select_billing_menu_item()
            return "break"

        return "break"

    def focus_billing_menu(self, event=None):
        if not self.billing_menu_items:
            return "break"

        self.show_billing_menu()
        self.billing_item_listbox.focus_set()
        self.billing_item_listbox.selection_clear(0, END)
        self.billing_item_listbox.selection_set(0)
        return "break"

    def show_billing_menu(self, event=None):
        if not hasattr(self, "billing_menu_popup"):
            return

        if not self.billing_menu_items:
            self.refresh_billing_item_menu(self.item_search_var.get())

        if not self.billing_menu_items:
            return

        self.root.update_idletasks()
        x = self.item_search_entry.winfo_rootx()
        y = self.item_search_entry.winfo_rooty() + self.item_search_entry.winfo_height() + 2
        width = max(self.item_search_entry.winfo_width(), 260)
        height = min(len(self.billing_menu_items), 6) * 24 + 6

        self.billing_menu_popup.geometry(f"{width}x{height}+{x}+{y}")
        self.billing_menu_popup.deiconify()
        self.billing_menu_popup.lift()

    def hide_billing_menu(self, event=None):
        if hasattr(self, "billing_menu_popup"):
            self.billing_menu_popup.withdraw()
        return "break" if event else None

    def handle_global_billing_click(self, event):
        if not hasattr(self, "billing_menu_popup"):
            return

        clicked_widget = event.widget
        if self.is_billing_menu_widget(clicked_widget):
            return

        self.hide_billing_menu()

    def is_billing_menu_widget(self, widget):
        billing_widgets = {
            self.item_search_entry,
            self.item_search_wrapper,
            self.billing_item_listbox,
            self.billing_menu_scrollbar,
            self.billing_menu_popup,
        }

        current_widget = widget
        while current_widget is not None:
            if current_widget in billing_widgets:
                return True
            current_widget = getattr(current_widget, "master", None)

        return False

    def get_selected_billing_item(self):
        typed_item = self.item_search_var.get().strip()

        if typed_item in self.updated_items:
            self.selected_billing_item = typed_item
            return typed_item

        if self.selected_billing_item in self.updated_items:
            return self.selected_billing_item

        return ""

    def updating_combo(self):
        self.combo_box['values'] = list(self.updated_items.keys())
        self.combo_box.set("Choose Items")

    def open_email_settings(self):
        saved_email, _ = self.get_saved_email_credentials()
        if saved_email:
            self.updating_email()
        else:
            self.add_email_credentials_window()

    def open_login_credentials_window(self):
        self.window_for_buttons()
        self.clear_second_window()

        try:
            self.change_login_email_btn.configure(state=DISABLED)
        except:
            pass

        main_frame = Frame(self.button_root, bg="#4A9782")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)

        content_frame = Frame(main_frame, bg='#F9F3EF', relief="raised", bd=2)
        content_frame.pack(fill='x', padx=10, pady=110)

        Label(content_frame, text="Login Credentials", font=('Arial', 16, 'bold'),
              bg='#F9F3EF', fg='black').pack(pady=(20, 10))

        Label(
            content_frame,
            text="This email is only for daily login access.\nIt does not change your billing email or app password.",
            font=('Arial', 11),
            bg='#F9F3EF',
            fg='black',
            justify='center'
        ).pack(pady=(0, 20))

        login_email_frame = Frame(content_frame, bg='#F9F3EF', relief="raised", bd=1)
        login_email_frame.pack(fill='x', padx=10, pady=10)

        Label(login_email_frame, text="Login Email:", font=('Arial', 12, 'bold'),
              bg='#F9F3EF', fg='black').pack(side='left', padx=10, pady=10)

        self.login_email_setup_entry = ttk.Entry(login_email_frame, width=30)
        self.login_email_setup_entry.pack(side='left', padx=10, pady=10)

        existing_login_email, _, _ = self.get_login_credentials()
        if existing_login_email:
            self.login_email_setup_entry.insert(0, existing_login_email)

        self.save_login_email_btn = Button(
            content_frame,
            text="Save",
            font=('Arial', 12, 'bold'),
            width=15,
            height=2,
            bg='#0D5EA6',
            fg='white',
            command=self.save_login_credentials
        )
        self.save_login_email_btn.pack(pady=(20, 30))

    def save_login_credentials(self):
        login_email = self.login_email_setup_entry.get().strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}$'

        if not re.match(pattern, login_email):
            self.guarded_showerror(
                "Invalid Email",
                "Enter a valid login email address.",
                self.save_login_email_btn
            )
            return

        try:
            self.c.execute("SELECT COUNT(*) FROM profile")
            row_count = self.c.fetchone()[0]

            if row_count == 0:
                self.c.execute(
                    "INSERT INTO profile (shop_name, gst_number, login_email, account_password) VALUES (?, ?, ?, ?)",
                    (None, None, login_email, "Admin@123")
                )
            else:
                self.c.execute(
                    "UPDATE profile SET login_email = ?",
                    (login_email,)
                )

            self.conn.commit()
            self.login_email_value = login_email
            showinfo("Success", "Login email saved successfully.")
            self.close_popup_window()
            self.accounts_page()
        except Exception as e:
            self.guarded_showerror("Save Error", f"Problem: {e}", self.save_login_email_btn)

    def add_email_credentials_window(self):
        self.window_for_buttons()
        self.clear_second_window()

        try:
            for i in self.four_btn_list:
                i.config(state=DISABLED)
        except:
            pass

        try:
            self.change_email_btn.configure(state=DISABLED)
        except:
            pass

        def close_btn():
            self.close_popup_window()

        main_frame = Frame(self.button_root, bg="#4A9782")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)

        content_frame = Frame(main_frame, bg='#F9F3EF', relief="raised", bd=2)
        content_frame.pack(fill='x', padx=10, pady=100)

        Label(content_frame, text="Add Email Credentials", font=('Arial', 16, 'bold'),
              bg='#F9F3EF', fg='black').pack(pady=(20, 10))

        info_label = Label(
            content_frame,
            text="This email will be used for bills, sales reports and password OTP.",
            font=('Arial', 11),
            bg='#F9F3EF',
            fg='black'
        )
        info_label.pack(pady=(0, 20))

        email_frame = Frame(content_frame, bg='#F9F3EF', relief="raised", bd=1)
        email_frame.pack(fill='x', padx=10, pady=10)

        Label(email_frame, text="Email Address:", font=('Arial', 12, 'bold'),
              bg='#F9F3EF', fg='black').pack(side='left', padx=10, pady=10)

        self.setup_email_entry = ttk.Entry(email_frame, width=30)
        self.setup_email_entry.pack(side='left', padx=10, pady=10)

        password_frame = Frame(content_frame, bg='#F9F3EF', relief="raised", bd=1)
        password_frame.pack(fill='x', padx=10, pady=10)

        Label(password_frame, text="App Password:", font=('Arial', 12, 'bold'),
              bg='#F9F3EF', fg='black').pack(side='left', padx=10, pady=10)

        self.setup_app_password_entry = ttk.Entry(password_frame, width=30, show='*')
        self.setup_app_password_entry.pack(side='left', padx=10, pady=10)
        self.add_password_toggle(password_frame, self.setup_app_password_entry)

        self.save_email_setup_btn = Button(
            content_frame,
            text="Save",
            font=('Arial', 12, 'bold'),
            width=15,
            height=2,
            bg='#0D5EA6',
            fg='white',
            command=self.save_email_credentials
        )
        self.save_email_setup_btn.pack(pady=(20, 30))

        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        try:
            self.button_root.mainloop()
        except:
            pass

    def save_email_credentials(self):
        email_address = self.setup_email_entry.get().strip()
        app_password = self.setup_app_password_entry.get().strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}$'

        if not re.match(pattern, email_address):
            self.guarded_showerror("Invalid Email", "Enter a valid email address.", self.save_email_setup_btn)
            return

        if not app_password:
            self.guarded_showerror("Missing Password", "Enter your email app password.", self.save_email_setup_btn)
            return

        try:
            self.c.execute("SELECT COUNT(*) FROM profile")
            row_count = self.c.fetchone()[0]

            if row_count == 0:
                self.c.execute(
                    "INSERT INTO profile (shop_name, gst_number, email, app_password, login_email, account_password) VALUES (?, ?, ?, ?, ?, ?)",
                    (None, None, email_address, app_password, None, "Admin@123")
                )
            else:
                self.c.execute(
                    "UPDATE profile SET email = ?, app_password = ?",
                    (email_address, app_password)
                )

            self.conn.commit()
            self.email = email_address
            self.app_password_value = app_password
            showinfo("Success", "Email credentials saved successfully.")
            self.close_popup_window()
            self.accounts_page()
        except Exception as e:
            self.guarded_showerror("Save Error", f"Problem: {e}", self.save_email_setup_btn)


    def update_order_tree(self):
        for row in self.order_tree.get_children():
            self.order_tree.delete(row)
        total = 0
        total_amt = 0
        for idx, (item,quantity,price) in enumerate(self.order_items,1):
            self.order_tree.insert("", "end", values=(idx,item,quantity, f"₹{price}"))
            total_amt += quantity
            total += price
        self.total_price_order.set(f"Total Amount: ₹{total}")
        self.total_item_order.set(f"Total Units: {total_amt}")
        self.update_generate_bill_button_state()

    def update_generate_bill_button_state(self):
        if not hasattr(self, "generate_bill"):
            return

        if self.order_items:
            self.generate_bill.config(state=NORMAL, bg='#28a745', fg='white')
        else:
            self.generate_bill.config(state=DISABLED, bg='#9E9E9E', fg='white')

    #--- Remove button Function-----
    def remove_in_tree(self):
        try:
            select = self.order_tree.focus()
            if not select:
                showwarning("None Selected", "Please select a Item to remove")

            item_data = self.order_tree.item(select)
            item_index = item_data["values"][0]-1

            if 0 <= item_index < len(self.order_items):
                self.order_items.pop(item_index)
                self.update_order_tree()
        except:
            pass

    #--- Bill Generate Button Function ---

    def bill_generating(self):
        if not self.order_items:
            self.guarded_showerror("No Order", "Add items to the order before generating a bill.", self.generate_bill)
            self.update_generate_bill_button_state()
            return

        self.generate_bill.config(state=DISABLED)
        self.window_for_buttons()
        self.clear_second_window()

        try:
            logo = PhotoImage(file='..png')
            self.button_root.iconphoto(True, logo)
        except:
            pass

        def close_btn():
            self.button_root.destroy()
            self.generate_bill.config(state=NORMAL)

        main_frame = Frame(self.button_root, bg="#4A9782")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)


        Label(main_frame, text="Generate Bill Via", font=("Arial",18,"bold")
              ,bg="#4A9782",fg="black").pack(fill='x',padx=10,pady=20)

        name_frame = Frame(main_frame, bg='#F9F3EF', relief="raised", bd=2)
        name_frame.pack(fill='x', padx=10, pady=40)

        first_frame = Frame(name_frame,bg='white', relief="raised", bd=2 )
        first_frame.pack(fill='x',padx=10,pady=10)

        self.generate_via_email = Button(first_frame, text="✉ Email", font=('Arial', 12, 'bold'),
                                      width=15, height=2, bg='#3D74B6', fg='white', command=self.single_order_emailing)
        self.generate_via_email.pack(padx=10, pady=10)

        second_frame = Frame(name_frame, bg='white', relief="raised", bd=2)
        second_frame.pack(fill='x', padx=10, pady=10)

        self.generate_physical = Button(second_frame, text="📜 Paper", font=('Arial', 12, 'bold'),
                                      width=15, height=2, bg='#9929EA', fg='white')
        self.generate_physical.pack(padx=10, pady=10)

        third_frame = Frame(name_frame, bg='white', relief="raised", bd=2)
        third_frame.pack(fill='x', padx=10, pady=10)

        self.generate_via_both = Button(third_frame, text="Both", font=('Arial', 12, 'bold'),
                                        width=15, height=2, bg='#3D74B6', fg='white')
        self.generate_via_both.pack(padx=10, pady=10)

        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        self.button_root.mainloop()


    # --- clear Button Function ---
    def clear_tree(self):
        self.order_items = []
        self.update_order_tree()

    # ---- biling page's generate bill button's email funtcion-------------#
    def single_order_emailing(self):
        self.button_root.destroy()
        self.window_for_buttons()
        self.clear_second_window()
        try:
            logo = PhotoImage(file='..png')
            self.button_root.iconphoto(True, logo)
        except:
            pass

        def close_btn():
            self.button_root.destroy()
            self.generate_bill.config(state=NORMAL)

        main_frame = Frame(self.button_root, bg="#4A9782")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)


        Label(main_frame, text="Customer's Details", font=("Arial",18,"bold")
              ,bg="#4A9782",fg="Black").pack(fill='x',padx=10,pady=20)

        first_frame = Frame(main_frame, bg="#FAF9EE",relief="raised",bd=1)
        first_frame.pack(fill="both",padx=10,pady=10)

        name_frame = Frame(first_frame, bg="#FAF9EE")
        name_frame.pack(fill="both",padx=10,pady=30)

        Label(name_frame, text="Customer's Name:", font=("Arial", 12, "bold")
              , bg="#FAF9EE", fg="Black").pack(side="left", padx=10, pady=(20,0))

        self.customer_name_entry = ttk.Entry(name_frame,font=('Arial',10,'bold'),width=25)
        self.customer_name_entry.pack(side="left",padx=10,pady=(20,0))


        email_frame = Frame(first_frame, bg="#FAF9EE")
        email_frame.pack(fill="both", padx=10, pady=10)

        Label(email_frame, text="Customer Email:", font=("Arial", 12, "bold")
              , bg="#FAF9EE", fg="Black").pack(fill='x', side="left", padx=10, pady=10)

        self.customer_email_entry = ttk.Entry(email_frame, font=('Arial', 10, 'bold'), width=25)
        self.customer_email_entry.pack(fill='x', side="left", padx=25, pady=10)

        self.single_order_submit = Button(first_frame, text="Sent Email", font=('Arial', 12, 'bold'),
                                        width=15, height=2, bg='#3D74B6', fg='white', command=self.generate_bill_pdf)
        self.single_order_submit.pack(padx=10, pady=(50,30))

        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)

        self.button_root.mainloop()

    #---------------- Update Page Configuration -----------------@
    def set_update_page(self):
        self.clear_page()
        self.set_active_button('update')
        saved_email, _ = self.get_saved_email_credentials()

        self.update_frame = Frame(self.root,bg='white')
        self.update_frame.pack(fill="both", expand=True)
        self.current_widgets.append(self.update_frame)

        head_frame = Frame(self.update_frame, bg="#3674B5", relief="raised", bd=3)
        head_frame.pack(fill='x',padx=20,pady=10)

        Label(head_frame, text="Manage your Item List, Price and More",
              font=('Arial',18, 'bold'), bg='#3674B5',fg='white').pack(fill='both',pady=10,padx=20)

        button_frame = Frame(self.update_frame, bg="#FAF9F6", relief="raised", bd=2)
        button_frame.pack(fill='both', padx=20, pady=10)

        update_btn_frame= Frame(button_frame, bg='white',height=80)
        update_btn_frame.pack(fill='x',padx=10,pady=10)
        update_btn_frame.pack_propagate(False)

        Label(update_btn_frame, text="Manage Products: ",
              font=('Arial', 14, 'bold'), bg='white', fg='black').pack(side="left", pady=10, padx=10)

        self.add_item_btn = Button(update_btn_frame, text="Add New Item",bg='#A4DD00',fg='white',
                                      font=('Arial',12, 'bold'), width=15, height=2, command=self.updating_list)
        self.add_item_btn.place(x=200,y=15)

        self.delete_item_btn = Button(update_btn_frame, text="Delete Item", bg='#FF3F33', fg='white',
                                   font=('Arial', 12, 'bold'), width=15, height=2, command=self.deleteing_items)
        self.delete_item_btn.place(x=400, y=15)

        self.update_list_btn = Button(update_btn_frame, text="Update Items/Prices", bg='#0B1D51', fg='white',
                                      font=('Arial', 12, 'bold'), width=18, height=2, command=self.update_old_list)
        self.update_list_btn.place(x=600,y=15)

        update_email_frame = Frame(button_frame, bg='white',height=80)
        update_email_frame.pack(fill='x', padx=10,pady=10)
        update_email_frame.pack_propagate(False)

        Label(update_email_frame, text="Change Your Account Email: ",
              font=('Arial', 14, 'bold'), bg='white', fg='black').pack(side="left", pady=10, padx=10)

        email_button_text = "Add Email" if not saved_email else "Update Email"
        self.update_email_btn = Button(update_email_frame, text=email_button_text, bg='#FFCC00', fg='white',
                                       font=('Arial', 12, 'bold'), width=15, height=2, command=self.open_email_settings)
        self.update_email_btn.pack(side='left',padx=10, pady=10)

        self.four_btn_list = [self.add_item_btn, self.delete_item_btn, self.update_email_btn, self.update_list_btn]

    def updating_list(self):
        self.window_for_buttons()
        self.clear_second_window()

        # disabling buttons
        for i in self.four_btn_list:
            i.config(state=DISABLED)
        try:
            logo = PhotoImage(file='..png')
            self.button_root.iconphoto(True, logo)
        except:
            pass
        def close_btn():
            self.button_root.destroy()
            for i in self.four_btn_list:
                i.config(state=NORMAL)

        main_frame = Frame(self.button_root, bg="#4A9782")
        main_frame.pack(fill='both', padx=10,pady=10,expand=True)
        self.current_second_button.append(main_frame)

        name_frame = Frame(main_frame, bg='#F9F3EF',relief="raised", bd=2)
        name_frame.pack(fill='x',padx=10,pady=100)


        item_frame = Frame(name_frame, bg='#F9F3EF',relief="raised",bd=1)
        item_frame.pack(fill='x',padx=10,pady=10)

        Label(item_frame, text="Product Name: ", font=('Arial',12,'bold')
              ,bg="#F9F3EF",fg='black').pack(side="left",padx=10,pady=10)

        self.add_item_entry = ttk.Entry(item_frame, width=30)
        self.add_item_entry.pack(side="left",padx=10,pady=10)

        price_frame = Frame(name_frame, bg='#F9F3EF',relief="raised",bd=1)
        price_frame.pack(fill='x',padx=10,pady=10)

        Label(price_frame, text="Add Price: ", font=('Arial', 12, 'bold')
              , bg="#F9F3EF", fg='black').pack(side="left",pady=10,padx=10)

        self.add_price_entry = ttk.Entry(price_frame)

        self.add_price_entry.pack(side="left", padx=45, pady=10)

        self.submit_add_item = Button(name_frame, text="Submit",font=('Arial', 12, 'bold'),
                                      width=15, height=2, bg='#3D74B6', fg='white',command=self.new_item_in_menu)
        self.submit_add_item.pack(padx=10,pady=10)
        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        try:
            self.button_root.mainloop()
        except:
            pass

    # --- Delete Item from List ---
    def deleteing_items(self):
        self.window_for_buttons()
        self.clear_second_window()

        # disabling buttons
        for i in self.four_btn_list:
            i.config(state=DISABLED)

        try:
            logo = PhotoImage(file='..png')
            self.button_root.iconphoto(True, logo)
        except:
            pass

        def close_btn():
            self.button_root.destroy()
            for i in self.four_btn_list:
                i.config(state=NORMAL)

        main_frame = Frame(self.button_root, bg="#4A9782")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)

        name_frame = Frame(main_frame, bg='#F9F3EF', relief="raised", bd=2)
        name_frame.pack(fill='x', padx=10, pady=100)

        item_frame = Frame(name_frame, bg='#F9F3EF', relief="raised", bd=1,height=40)
        item_frame.pack(fill='x', padx=10, pady=10)
        item_frame.pack_propagate(False)

        Label(item_frame, text='Select Item:', font=('Arial', 12),
              bg='#FAF9F6').pack(side='left', padx=10)

        self.combo_box = Combobox(item_frame, values=list(self.item_menu.keys()), width=25, font=('Arial', 10), state='readonly')
        self.combo_box['values'] = list(self.item_menu.keys())  # Set full item list
        self.combo_box.set("Choose Items")
        self.combo_box.pack(side='left', padx=10)
        self.updating_combo()

        self.delete_selected_item = Button(name_frame, text="Submit",font=('Arial', 12, 'bold'),
                                      width=15, height=2, bg='#3D74B6', fg='white',command=self.deleting_selected_item)
        self.delete_selected_item.pack(padx=10,pady=10)

        self.delete_all_items_btn = Button(
            name_frame,
            text="Delete All Items",
            font=('Arial', 12, 'bold'),
            width=15,
            height=2,
            bg='#B22222',
            fg='white',
            command=self.delete_all_items_permanently
        )
        self.delete_all_items_btn.pack(padx=10, pady=(0, 10))

        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        try:
            self.button_root.mainloop()
        except:
            pass

    def deleting_selected_item(self):
        def close_btn():
            try:
                self.button_root.grab_release()
            except:
                pass
            self.button_root.destroy()
            for i in self.four_btn_list:
                i.config(state=NORMAL)
        item = self.combo_box.get()

        if item == "Choose Items" or item == "":
            self.guarded_showerror("Error", "Select A item to Delete", self.delete_selected_item)
            return

        else:
            self.c = self.conn.cursor()
            self.c.execute('delete from menu where name=?', (item,))
            self.conn.commit()
            showinfo("Action Completed", "Item has been Removed")

            try:
                if item in self.updated_items:
                    del self.updated_items[item]
            except:
                pass
            close_btn()
        # self.updating_combo()

    def delete_all_items_permanently(self):
        confirmed = askyesno(
            "Confirm Delete",
            "This will permanently delete all items from the menu. Do you want to continue?"
        )

        if not confirmed:
            return

        try:
            self.c = self.conn.cursor()
            self.c.execute("DELETE FROM menu")
            self.conn.commit()
            self.item_menu.clear()
            self.updated_items.clear()
            showinfo("Deleted", "All items have been deleted permanently.")
        except Exception as e:
            self.guarded_showerror("Delete Error", f"Problem: {e}", self.delete_all_items_btn)
            return

        try:
            self.button_root.grab_release()
        except:
            pass

        try:
            self.button_root.destroy()
        except:
            pass

        for i in self.four_btn_list:
            i.config(state=NORMAL)

    def update_old_list(self):
        self.window_for_buttons()
        self.clear_second_window()

        # disabling buttons
        for i in self.four_btn_list:
            i.config(state=DISABLED)

        def close_btn():
            self.button_root.destroy()
            for i in self.four_btn_list:
                i.config(state=NORMAL)

        def function_to_run(event=None):
            item = self.combo_box.get().strip()
            print(f"Selected item: {item}")
            data = self.updated_items.get(item)
            self.price_entry.config(text=data)


        main_frame = Frame(self.button_root, bg="#4A9782")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)

        second_frame = Frame(main_frame, bg='#F9F3EF', relief="raised", bd=2)
        second_frame.pack(fill='x', padx=10, pady=100)

        choose_frame = Frame(second_frame, bg='#F9F3EF')
        choose_frame.pack(fill='x', padx=10)

        Label(choose_frame, text="Choose item ", font=('Arial', 12, 'bold')
              , bg="#F9F3EF", fg='black').pack(side="left", fill='x',padx=10, pady=10)

        Label(choose_frame, text="Current Price ", font=('Arial', 12, 'bold')
              , bg="#F9F3EF", fg='black').pack(side="right",fill='x', padx=30, pady=10)

        first_frame = Frame(second_frame,bg='#F9F3EF')
        first_frame.pack(fill='x',pady=(0,10))
        self.combo_box = Combobox(first_frame, width=25, font=('Arial', 10),values=list(self.item_menu.keys()), state='readonly')
        self.combo_box.pack(side='left', padx=20)
        self.combo_box.bind("<<ComboboxSelected>>", function_to_run)
        self.updating_combo()

        self.price_entry = Label(first_frame, text="", font=("Arial",12,'bold'),fg='black',bg='#F9F3EF',width=50)
        self.price_entry.pack(padx=30,side='left')

        name_frame = Frame(second_frame, bg='#F9F3EF', relief="raised", bd=1)
        name_frame.pack(fill='x', padx=10, pady=10)

        Label(name_frame, text="Change Name: ", font=('Arial', 12, 'bold')
              , bg="#F9F3EF", fg='black').pack(side="left", padx=10, pady=10)

        self.updated_name_entry = ttk.Entry(name_frame, width=30)
        self.updated_name_entry.pack(side="left", padx=10, pady=10)

        price_frame = Frame(second_frame, bg='#F9F3EF', relief="raised", bd=1)
        price_frame.pack(fill='x', padx=10, pady=10)

        Label(price_frame, text="Change Price: ", font=('Arial', 12, 'bold')
              , bg="#F9F3EF", fg='black').pack(side="left", padx=10, pady=10)

        self.updated_price_entry = ttk.Entry(price_frame, width=30)
        self.updated_price_entry.pack(side="left", padx=10, pady=10)

        self.submit_update_btn = Button(second_frame, text="Update", font=('Arial', 12, 'bold'),
                                      width=15, height=2, bg='#3D74B6', fg='white', command=self.new_updated_item)
        self.submit_update_btn.pack(padx=10, pady=10)
        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        self.button_root.update()
        try:
            self.button_root.mainloop()
        except:
            pass

    def new_updated_item(self):
        changed_name = self.updated_name_entry.get().strip()
        changed_price = self.updated_price_entry.get().strip()
        selected_item = self.combo_box.get().strip()

        if not selected_item or selected_item == "Choose Items":
            self.guarded_showerror("Error", "Select a Item to Update", self.submit_update_btn)
            return

        if not changed_name and not changed_price:
            self.guarded_showerror("Error", "Enter a new name or price to update", self.submit_update_btn)
            return

        def close_btn():
            try:
                self.button_root.grab_release()
            except:
                pass
            self.button_root.destroy()
            for i in self.four_btn_list:
                i.config(state=NORMAL)

        try:
            self.c.execute("SELECT price FROM menu WHERE name = ?", (selected_item,))
            row = self.c.fetchone()

            if not row:
                self.guarded_showerror("Error", "Selected item not found", self.submit_update_btn)
                return

            final_name = changed_name if changed_name else selected_item
            final_price = row[0]

            if changed_price:
                try:
                    final_price = int(changed_price)
                    if final_price <= 0:
                        self.guarded_showerror("Error", "Price must be greater than 0", self.submit_update_btn)
                        return
                except ValueError:
                    self.guarded_showerror("Error", "Enter a valid numeric price", self.submit_update_btn)
                    return

            self.c.execute(
                "UPDATE menu SET name = ?, price = ? WHERE name = ?",
                (final_name, final_price, selected_item)
            )
            self.conn.commit()

            data = self.c.execute('select * from menu')
            values = data.fetchall()
            self.item_menu.clear()
            self.updated_items.clear()

            for name, price in values:
                self.item_menu[name] = price
                self.updated_items[name] = price

            self.updating_combo()
            showinfo("Success", "Item Updated Successfully")
            close_btn()
        except Exception as e:
            self.guarded_showerror("Update Error", f"Problem: {e}", self.submit_update_btn)



    def updating_email(self):
        self.window_for_buttons()
        self.clear_second_window()

        # disabling buttons
        try:
            for i in self.four_btn_list:
                i.config(state=DISABLED)
        except:
            pass
        #-------- Disable the email Button on Accounts Page ---------#
        try:
            self.change_email_btn.configure(state=DISABLED)
        except:
            pass

        def close_btn():
            try:
                self.button_root.destroy()
                for i in self.four_btn_list:
                    i.config(state=NORMAL)

            except:
                pass

            #------ Enable the email button on Account page -------#
            try:
                self.change_email_btn.configure(state=NORMAL)
            except:
                pass

        self.updating_main_frame = Frame(self.button_root, bg="#4A9782")
        self.updating_main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(self.updating_main_frame)

        self.updatingmail_second_frame = Frame(self.updating_main_frame, bg='#F9F3EF',relief="raised", bd=1)
        self.updatingmail_second_frame.pack(fill="both",padx=10,pady=100)

        label_frame = Frame(self.updatingmail_second_frame, bg='#F9F3EF',relief="raised", bd=1)
        label_frame.pack(fill='x',padx=10,pady=10)

        self.old_email_label = Label(label_frame, text="Current Email:",font=('Arial',12,'bold'),bg='#F9F3EF')
        self.old_email_label.pack(fill='x',side='left',padx=10, pady=10)

        self.old_mail_entry = ttk.Entry(label_frame,width=25)
        self.old_mail_entry.pack(side='left',padx=8, pady=10)

        self.send_new_otp = Button(label_frame, text="Send OTP", font=("Arial", 12, 'bold'), bg='#0D5EA6', fg='white',
                                   command=self.send_otp_newmail)
        self.send_new_otp.pack(side="left", pady=10,padx=(30,0))

        self.label3_frame = Frame(self.updatingmail_second_frame, bg='#F9F3EF', relief="raised", bd=1)
        self.label3_frame.pack(fill='x', padx=10, pady=10)

        self.verify_otp_label = (Label(self.label3_frame, text="Verify OTP: ", font=('Arial', 12, 'bold'), bg='#F9F3EF'))
        self.verify_otp_label.pack(fill='x', side='left', padx=10, pady=10)

        self.verify_otp_enrty = ttk.Entry(self.label3_frame, width=25, state=DISABLED)
        self.verify_otp_enrty.pack(side='left', padx=(30,0), pady=10)

        label2_frame = Frame(self.updatingmail_second_frame, bg='#F9F3EF', relief="raised", bd=1)
        label2_frame.pack(fill='x', padx=10, pady=10)

        self.new_email_label = Label(label2_frame, text="New Email:", font=('Arial', 12, 'bold'), bg='#F9F3EF')
        self.new_email_label.pack(fill='x', side='left', padx=10, pady=10)

        self.new_mail_entry = ttk.Entry(label2_frame, width=25)
        self.new_mail_entry.pack(side='left', padx=30, pady=10)

        label4_frame = Frame(self.updatingmail_second_frame, bg='#F9F3EF', relief="raised", bd=1)
        label4_frame.pack(fill='x', padx=10, pady=10)

        self.new_app_password_label = Label(label4_frame, text="New App Password:", font=('Arial', 12, 'bold'), bg='#F9F3EF')
        self.new_app_password_label.pack(fill='x', side='left', padx=10, pady=10)

        self.new_app_password_entry = ttk.Entry(label4_frame, width=25, show='*')
        self.new_app_password_entry.pack(side='left', padx=3, pady=10)
        self.add_password_toggle(label4_frame, self.new_app_password_entry)

        self.email_updating_btn = Button(self.updatingmail_second_frame, text="Request OTP", font=('Arial', 12, 'bold'),
                                      width=15, height=2, bg='#0D5EA6', fg='white', command=self.confirm_email_change, state=DISABLED)
        self.email_updating_btn.pack(padx=10, pady=10)

        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        try:
            self.button_root.mainloop()
        except:
            pass


    #------------ Sub Buttons of the 4 buttons of updata pages ----------

        #for adding new item in menu
    def new_item_in_menu(self):
        try:
            self.conn = sqlite3.connect('billing_sft.db')
            self.c = self.conn.cursor()
            self.c.execute("create table if not exists menu(name text, price integer)")

        # --- check add info is avalilable ---#.
            item_name = self.add_item_entry.get().strip()
            price_text = self.add_price_entry.get().strip()
            if not item_name:
                self.guarded_showerror("Error", "Add Name of Item", self.submit_add_item)
                return

            if not price_text:
                self.guarded_showerror("Error", "Add Price of Item", self.submit_add_item)
                return

            # --- check price is a number ----
            try:
                price = int(price_text)
                if price <= 0:
                    self.guarded_showerror("Error", "Price is 0", self.submit_add_item)
                    return
            except ValueError:
                self.guarded_showerror("Error", "Invalid Price", self.submit_add_item)
                return

            # Insert into database
            self.c.execute('INSERT INTO menu(name, price) VALUES(?, ?)', (item_name, price))
            self.conn.commit()
            showinfo("Success", "Item Added Successfully")
            data = self.c.execute('select * from menu')
            values = data.fetchall()
            for row in values:
                data1 = self.c.execute('select * from menu')
                values1 = data1.fetchall()
                self.c.execute("delete from menu")
                for row in values1:
                    item_name = row[0]
                    item_price = row[1]
                    self.updated_items[item_name] = item_price
                    self.c.execute('insert into menu(name, price) values(?,?)', (item_name, item_price) )
                    self.conn.commit()

            # --- clear entries ---
            self.add_item_entry.delete(0, 'end')
            self.add_price_entry.delete(0, 'end')


        except sqlite3.Error as e:
            self.guarded_showerror("Database Error", f"Database problem: {e}", self.submit_add_item)
        except Exception as e:
            self.guarded_showerror("Adding Error", f"Problem: {e}", self.submit_add_item)
        try:
            for i in self.four_btn_list:
                i.config(state=NORMAL)
        except:
            pass
        try:
            self.button_root.grab_release()
        except:
            pass
        try:
            self.button_root.destroy()
        except:
            pass


    def updating_combo(self):
        self.combo_box['values'] = list(self.updated_items.keys())
        self.combo_box.set("Choose Items")


    #-------------- for sending OTP for email verification ---------------#
    def send_otp_newmail(self):
        self.email_updating_btn.config(state=NORMAL, text="Update")
        email_add = self.old_mail_entry.get().strip()
        email_value = "" #verifying email exists or not
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}$'

        if not re.match(pattern,email_add) or not email_add:
            self.guarded_showerror("Not Found", "No Email Address Found! Enter a valid Email", self.send_new_otp, "Send OTP")
            return

        row = self.get_latest_profile_row()

        if row and row[3]:
            email_value = row[3]
        if email_add != email_value:
            self.guarded_showerror("Not Found", "Incorrect email! Kindly check your email", self.send_new_otp, "Send OTP")
            return

        #------- mail structure-------------
        self.mail_subject = 'Confirm Your Email Change Request'
        self.mail_address = self.old_mail_entry.get().strip()

        self.send_new_otp.config(text="Sent (✓)",bg='#ADE4DB',state=DISABLED)
        self.otp_generating()
        self.pass_change_message = (f"Hello,\n\n"
                                    f"We received a request to change the email address linked to your account.\n\n"
                                    f"Please use the One-Time Password (OTP) below to confirm this change:\n\n"
                                    f"Your OTP: {self.otp_number} \n\n"
                                    f"This code will expire in 5 minutes. If you did not request this change, please ignore this email or contact our support team immediately. \n"
                                    f"Best regards, \n"
                                    f"Quick SVR Team")

        self.html_message =f"""
<div style="font-family:Arial,Helvetica,sans-serif; max-width:600px; margin:auto; padding:20px; 
            background:#f9f9f9; border:1px solid #ddd; border-radius:12px;">

  <!-- Header -->
  <div style="background:#6C63FF; color:#fff; padding:15px; text-align:center; border-radius:10px 10px 0 0;">
    <h2 style="margin:0;">Quick SVR Security</h2>
  </div>

  <!-- Body -->
  <div style="padding:20px; color:#333;">
    <p>Hello,</p>
    <p>We received a request to <b>change the email address</b> linked to your account.</p>
    <p>Please use the One-Time Password (OTP) below to confirm this change:</p>

    <!-- OTP Box -->
    <div style="font-size:36px; font-weight:bold; color:#6C63FF; background:#fff; 
                border:2px dashed #6C63FF; border-radius:10px; 
                text-align:center; padding:15px; margin:25px 0;">
      {self.otp_number}
    </div>

    <p style="color:#555;">This code will expire in <b>5 minutes</b>. 
    If you did not request this change, please ignore this email or contact our support team immediately.</p>
  </div>

  <!-- Footer -->
  <div style="background:#f1f1f1; padding:12px; text-align:center; font-size:12px; color:#777; border-radius:0 0 10px 10px;">
    <p>Best regards,<br><b>Quick SVR Team</b></p>
  </div>
</div>
"""
        self.sending_otp_email()
        if self.verify_otp_enrty:
            self.verify_otp_enrty.config(state=NORMAL)


    # -------------- Confirm Email Change ----------------#
    def confirm_email_change(self):
        old_mail = self.old_mail_entry.get().strip()
        verify_otp = self.verify_otp_enrty.get().strip()
        self.new_email = self.new_mail_entry.get().strip()
        new_app_password = self.new_app_password_entry.get().strip()

        def close_btn():
            try:
                self.button_root.grab_release()
            except:
                pass
            self.button_root.destroy()
            try:
                for i in self.four_btn_list:
                    i.config(state=NORMAL)
            except:
                pass
            try:
                self.change_email_btn.configure(state=NORMAL)
            except:
                pass
        def button_back(): #for maintaining the expansion of frame for invalid otp
            self.email_updating_btn.config(state=NORMAL)
            self.email_updating_btn.config(text='Update', fg="black")

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}$'

        if not old_mail:
            self.old_email_label.config(fg='red')
            self.old_email_label.after(5000, lambda: self.old_email_label.config(fg="black"))
            return

        if not self.new_email:
            self.new_email_label.config(fg='red')
            self.new_email_label.after(5000, lambda: self.new_email_label.config(fg="black"))
            return

        if not new_app_password:
            self.new_app_password_label.config(fg='red')
            self.new_app_password_label.after(5000, lambda: self.new_app_password_label.config(fg="black"))
            return

        if not re.match(pattern,old_mail):
            error_mail = Label(self.updatingmail_second_frame,text="*Invalid Mail format",fg='red',font=('Arial',12,'bold'))
            error_mail.pack(side="left",pady=(10, 0),fill='x')
            error_mail.after(5000, error_mail.destroy)
            return

        if not re.match(pattern,self.new_email):
            error_mail = Label(self.updatingmail_second_frame, text="*Invalid Mail format", fg='red',font=('Arial',12,'bold'))
            error_mail.pack(side="left",pady=(10, 0),fill='x')
            error_mail.after(5000, error_mail.destroy)
            return

        if not verify_otp:
            self.verify_otp_label.config(fg='red')
            self.verify_otp_label.after(5000, lambda: self.verify_otp_label.config(fg="black"))
            return

        if old_mail:
            if verify_otp == str(self.otp_number):
                    showinfo("Success", "Your email has been Updated")
            else:
                error_text = Label(self.label3_frame,text="* Incorrect OTP",fg='red',bg="#F9F3EF",font=('Arial',12,'bold'))
                error_text.pack(pady=(10,0))
                error_text.after(1000, error_text.destroy)
                self.email_updating_btn.config(state=DISABLED)
                self.email_updating_btn.config(text='Wait',fg='white')
                self.email_updating_btn.after(1000, button_back)
                return

        row = self.get_latest_profile_row()
        existing_mail = row[3] if row and row[3] else None

        if existing_mail:
            # Update email if already exists
            self.c.execute("UPDATE profile SET email = ?, app_password = ?", (self.new_email, new_app_password))
            self.conn.commit()
        else:
            # Insert new row (if table empty)
            self.c.execute("INSERT INTO profile (email, app_password) VALUES (?, ?)", (self.new_email, new_app_password))
            self.conn.commit()

        self.email = self.new_email
        self.app_password_value = new_app_password
        close_btn()
        self.accounts_page()

    #-------------- DashBoard Page ----------------#

    def dashboard_page(self):
        self.clear_page()
        self.set_active_button('dashboard')
        self.dashboard_frame = Frame(self.root, bg='white')
        self.dashboard_frame.pack(fill='both', expand=True)
        self.current_widgets.append(self.dashboard_frame)
        now = datetime.now()

        head_frame = Frame(self.dashboard_frame, bg="#9B177E",relief="raised",bd=3)
        head_frame.pack(fill='x',padx=20,pady=10)

        Label(head_frame, text="Track your sales", font=('Arial',18,'bold')
              ,bg='#9B177E',fg='white').pack(fill='x',padx=10,pady=10)

        #daily sales Setup
        daily_track_frame = Frame(self.dashboard_frame, bg='#FAF9F6',relief="raised",bd=3)
        daily_track_frame.pack(fill='x',padx=20)

        label_frame = Frame(daily_track_frame, bg='#FAF9F6')
        label_frame.pack(fill='x')
        Label(label_frame, text="Your Daily Sales", bg='#FAF9F6', font=("Arial", 14, 'bold')).pack(side="left", pady=10,
                                                                                            padx=30)
        self.daily_track_date = now.strftime('(%A) %d %B %Y')
        self.daily_time_track_label = (Label(label_frame, text=f"{self.daily_track_date}", bg='#FAF9F6', font=("Arial", 14, 'bold')))
        self.daily_time_track_label.pack(side="left",padx=10)

        self.total_daily_revenue = StringVar(value='Total Amount: ₹0')
        Label(label_frame, textvariable=self.total_daily_revenue,
              font=("Arial", 14, "bold"), bg='#FAF9F6').pack(side="left", padx=100, pady=10)

        self.daily_print_btn = Button(label_frame, text="Generate PDF", bg='#28a745', fg='white',
                                      font=('Arial', 12, 'bold'), command=self.daily_track_pdf)
        self.daily_print_btn.pack(side="right", padx=(0,40), pady=10)

        self.clear_daily_btn =  Button(label_frame, text="Clear Tree", bg='red', fg='white',
                                      font=('Arial', 12, 'bold'), command=self.clear_daily_tree)
        self.clear_daily_btn.pack(side="right", padx=20, pady=10)

        daily_tree_frame = Frame(daily_track_frame, bg='#FAF9F6')
        daily_tree_frame.pack(fill='both', expand=True,pady=10)
        columns = ('Rank', 'Item Name', 'Unit Price', 'Total Sold', 'Total Revenue')
        self.daily_track_tree = Treeview(daily_tree_frame, columns=columns, show='headings', height=12)

        # Configure column headings and widths
        column_configs = {
            'Rank': {'width': 60, 'anchor': 'center'},
            'Item Name': {'width': 150, 'anchor': 'w'},
            'Unit Price': {'width': 100, 'anchor': 'center'},
            'Total Sold': {'width': 120, 'anchor': 'e'},
            'Total Revenue': {'width': 100, 'anchor': 'center'}
        }

        for col, config in column_configs.items():
            self.daily_track_tree.heading(col, text=col, anchor=config['anchor'])
            self.daily_track_tree.column(col, width=config['width'], anchor=config['anchor'])

        # Create scrollbar
        scrollbar = Scrollbar(daily_tree_frame, orient='vertical', command=self.daily_track_tree.yview)
        self.daily_track_tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.daily_track_tree.pack(side="left",fill='both',padx=20, expand=True)
        scrollbar.pack(side='right', fill='y')

        self.daily_track_tree.tag_configure('evenrow', background='#F8F9FA')
        self.daily_track_tree.tag_configure('oddrow', background='#FFFFFF')
        self.daily_track_tree.tag_configure('top3', background='#E8F5E8', foreground='#2E7D32')

        #------------------------------------------------------------------------
        #                   Monthly Sales Track Setup

        monthly_track_frame = Frame(self.dashboard_frame, bg='#FAF9F6', relief="raised", bd=3)
        monthly_track_frame.pack(fill='x', padx=20,pady=10)

        label_frame = Frame(monthly_track_frame, bg='#FAF9F6')
        label_frame.pack(fill='x', padx=10)
        Label(label_frame, text="Your Monthly Sales", bg='#FAF9F6', font=("Arial", 14, 'bold')).pack(side="left", pady=10,padx=40)

        self.monthly_print_btn = Button(label_frame, text="Generate PDF", bg='#28a745', fg='white',
                                      font=('Arial', 12, 'bold'), command=self.monthly_track_pdf)
        self.monthly_print_btn.pack(side="right", padx=(0,30), pady=10)

        self.monthly_delete_btn = Button(label_frame, text="Clear Tree", bg='#28a745', fg='white',
                                        font=('Arial', 12, 'bold'), command=self.clear_monthly_tree_once)
        self.monthly_delete_btn.pack(side="right", padx=20, pady=10)

        monthly_tree_frame = Frame(monthly_track_frame, bg='#FAF9F6')
        monthly_tree_frame.pack(fill='both', expand=True, pady=10)
        column = ('Sr.no', 'Day & Date', 'Total Revenue Generated', 'Top Selling Item')
        self.monthly_track_tree = Treeview(monthly_tree_frame, columns=column, show='headings', height=12)

        # Configure column headings and widths
        column_configs = {
            'Sr.no': {'width': 30, 'anchor': 'center'},
            'Day & Date': {'width': 150, 'anchor': 'center'},
            'Total Revenue Generated': {'width': 120, 'anchor': 'center'},
            'Top Selling Item': {'width': 130, 'anchor': 'center'}
        }

        for col, config in column_configs.items():
            self.monthly_track_tree.heading(col, text=col, anchor=config['anchor'])
            self.monthly_track_tree.column(col, width=config['width'], anchor=config["anchor"])

        # Create scrollbar
        scrollbar = Scrollbar(monthly_tree_frame, orient='vertical', command=self.daily_track_tree.yview)
        self.monthly_track_tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview and scrollbar
        self.monthly_track_tree.pack(side='left', fill='both', padx=20, expand=True)
        scrollbar.pack(side='right', fill='y')

        # Configure row colors
        self.monthly_track_tree.tag_configure('evenrow', background='#F8F9FA')
        self.monthly_track_tree.tag_configure('oddrow', background='#FFFFFF')

        self.loading_monthly_sales()
        #calling loading data
        self.loading_data()
        # ---- for updating the total revenue-----#
        self.update_daily_revenue()


    def update_daily_revenue(self):
        total_revenue = 0
        for child in self.daily_track_tree.get_children():
            row_data = self.daily_track_tree.item(child)["values"]
            if len(row_data) >= 5:
                try:
                    total_revenue += float(row_data[4])
                except ValueError:
                    continue  # Skip if value is not a number
        self.total_daily_revenue.set(f"Total Amount: ₹{total_revenue:.2f}")

    def update_datetime(self):
        if self.datetime_label.winfo_exists():  # only update if label still exists
            now = datetime.now().strftime("Time: %I:%M:%S %p")
            self.datetime_label.config(text=now)
            self.root.after(1000, self.update_datetime)

    def daily_track_pdf(self):
        if not self.daily_track_tree.get_children():
            showerror("No Data", "No data found!")
        else:
            pdf = FPDF()
            pdf.add_page()
            filename = f"{self.daily_track_date} Sales Report.pdf"

            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            path = os.path.join(desktop_path, 'Quick SVR', 'Daily Sales')
            os.makedirs(path, exist_ok=True)
            full_path = os.path.join(path, filename)

            # Title
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"{self.daily_track_date} Sales Report", ln=True, align='C')
            pdf.ln(5)

            # Table Header
            pdf.set_font("Arial", 'B', 12)
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(15, 10, "Rank", border=1, align='C', fill=True)  # smaller
            pdf.cell(65, 10, "Product Name", border=1, align='C', fill=True)
            pdf.cell(35, 10, "Unit Price", border=1, align='C', fill=True)
            pdf.cell(35, 10, "Total Sold", border=1, align='C', fill=True)
            pdf.cell(40, 10, "Total (Rs)", border=1, align='C', fill=True)
            pdf.ln()

            # Table Rows
            pdf.set_font("Arial", '', 12)
            grand_total = 0
            for child in self.daily_track_tree.get_children():
                values = self.daily_track_tree.item(child)["values"]
                order = str(values[0])  # Convert to string
                name = str(values[1])
                unit_price = float(str(values[2]).replace("₹", "")) if isinstance(values[2], str) else float(values[2])
                total_sold = float(str(values[3]).replace("₹", "")) if isinstance(values[3], str) else float(values[3])
                total_revenue = float(str(values[4]).replace("₹", "")) if isinstance(values[4], str) else float(values[4])
                grand_total += total_revenue

                pdf.cell(15, 10, str(order), border=1)
                pdf.cell(65, 10, str(name), border=1, align='C')
                pdf.cell(35, 10, f"{unit_price:.2f}", border=1, align='C')
                pdf.cell(35, 10, f"{total_sold:.2f}", border=1, align='C')
                pdf.cell(40, 10, f"{total_revenue:.2f}", border=1, align='C')
                pdf.ln()
            # Grand total row
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(150, 10, "GRAND TOTAL", border=1, align='R')
            pdf.cell(40, 10, f"Rs {grand_total:.2f}", border=1, align='C')

            # Save File
            pdf.output(full_path)
            # print(f"PDF saved as {full_path}")
            self.calling_profile_variables()
            self.sending_sales_track_mail(full_path)
            self.load_for_monthly()

    def monthly_track_pdf(self):
        if not self.monthly_track_tree.get_children():
            showerror("No Data", "No Data Found!")
        else:
            pdf = FPDF()
            pdf.add_page()
            timestamp = datetime.now().strftime("%B")
            filename = f"{timestamp} Sales Report.pdf"

            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            path = os.path.join(desktop_path, 'Quick SVR', 'Monthly Sales')
            os.makedirs(path, exist_ok=True)
            full_path = os.path.join(path, filename)

            # Title
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"{timestamp} Sales Report", ln=True, align='C')
            pdf.ln(5)

            # Table Header
            pdf.set_font("Arial", 'B', 12)
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(15, 10, "Sr.no", border=1, align='C', fill=True)
            pdf.cell(65, 10, "Day & Date", border=1, align='C', fill=True)
            pdf.cell(65, 10, "Total Revenue Generated", border=1, align='C', fill=True)
            pdf.cell(40, 10, "Top Selling item", border=1, align='C', fill=True)
            pdf.ln()

            #Table Rows
            pdf.set_font("Arial",'',12)
            grand_total = 0
            for child in self.monthly_track_tree.get_children():
                values = self.monthly_track_tree.item(child)['values']
                sr_no = str(values[0])
                day_date = str(values[1])
                revenue = float(str(values[2]))
                selling = str(values[3])
                grand_total += revenue

                pdf.cell(15, 10, str(sr_no), border=1, align='C')
                pdf.cell(65, 10, str(day_date), border=1, align='C')
                pdf.cell(65, 10, f"{revenue:.2f}", border=1, align='C')
                pdf.cell(40, 10, str(selling), border=1, align='C')
                pdf.ln()
            # Grand total row
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(145, 10, "GRAND TOTAL", border=1, align='R')  # (15 + 65 + 35 = 115)
            pdf.cell(40, 10, f"Rs {grand_total:.2f}", border=1, align='C')

            # Save File
            pdf.output(full_path)
            # print(f"PDF saved as {full_path}")
            self.calling_profile_variables()
            self.sending_sales_track_mail(full_path)

    #---------- send mail for montlhy and daily ---------#
    def sending_sales_track_mail(self,file_path):
        self.owner_email, self.app_password = self.get_saved_email_credentials()
        login_email, _, _ = self.get_login_credentials()

        if not self.owner_email or not self.app_password:
            showerror("Email Setup Required", "Add your sending email and app password first.")
            return

        if not login_email:
            showerror("Login Email Required", "Add a login email first to receive sales reports.")
            return

        message = EmailMessage()
        message['Subject'] = 'Your Sales Report'
        message['From'] = self.owner_email
        message['To'] = login_email
        message.set_content(
            "Dear Customer,\n\n"
            "As per your request, We’ve attached your Sales Report for your review.\n\n"
            "This report has been automatically generated by Quick SVR for your convenience.\n\n"
            "If you have any questions or require further assistance, please feel free to reach out to our support team.\n\n"
            "Best regards,\n"
            "Team Quick SVR"
        )

        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(file_path)

            message.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)
        except Exception as e:
            showerror("File Error", f"Unable to attach sales report: {e}")
            return

        if self.send_email_message(self.owner_email, self.app_password, message, "send sales report"):
            showinfo("Success", f"Sales report sent to {login_email}")

    #-------- fetch data for daily tree-------#
    def load_sales_data(self):
        # get the item of main tree in list
        get_data = self.order_tree.get_children()
        self.data_list = []
        if self.conn:
            self.c = self.conn.cursor()

        self.daily_time = self.daily_track_date

        try:
            for item in get_data:
                values = self.order_tree.item(item, 'values')  # e.g. values = ('1', 'Pizza', '2', '₹100')
                rank = values[0]
                name_element = values[1]
                quantity = values[2]
                value = (rank, name_element, quantity)

                self.c.execute("SELECT price FROM menu WHERE name = ?", (name_element,))
                data = self.c.fetchone()  # Use fetchone if expecting only one result

                if data:
                    price = data[0]
                    total_revenue = values[3]
                    combined_tuple = (*value,price,total_revenue)
                    self.data_list.append(combined_tuple)
                else:
                    # If name not found in menu
                    self.data_list.append((*value, "Price not found"))

        except:
            showerror("Error", f"No Item Found")
        self.c.executemany('insert into daily_track(id, name, total_sold, unit_price, total_revenue) values(?,?,?,?,?)',
                           self.data_list)
        self.conn.commit()

    #--------- loading daily data in tree-------#
    def loading_data(self):
        try:
            for item in self.daily_track_tree.get_children():
                self.daily_track_tree.delete(item)
        except Exception as e:
            print(e)

        self.c.execute("select  name, total_sold, unit_price, total_revenue from daily_track")
        orders = self.c.fetchall()

        self.monthly_stats = defaultdict(lambda: {
            'total_quantity': 0,
            'total_revenue': 0.0,
            'price': 0.0
        })

        for order in orders:
            name, total_sold, unit_price, total_revenue = order
            stats = self.monthly_stats[name]
            stats['total_quantity'] += int(total_sold)
            # stats['price'] += float(str(unit_price).replace('₹', '').replace(',', '').strip())
            stats['total_revenue'] += float(str(total_revenue).replace('₹', '').replace(',', '').strip())
            if stats['price'] == 0.0:
                stats['price'] = float(str(unit_price).replace('₹', '').replace(',', '').strip())


        sorted_item = sorted(self.monthly_stats.items(),
                             key=lambda x: x[1]['total_quantity'],
                             reverse=True)

        for rank, (name, stats) in enumerate(sorted_item, 1):

            if rank <=3:
                tag = 'top3'
            elif rank % 2 == 0:
                tag = 'evenrow'
            else:
                tag = 'oddrow'

            self.daily_track_tree.insert('','end', values=(
                rank, name,
                stats['price'],
                stats['total_quantity'],
                stats['total_revenue']
            ),tags=(tag,))

    #------ clear daily tree with data base--------#
    def clear_daily_tree(self):
        for row in self.daily_track_tree.get_children():
            self.daily_track_tree.delete(row)

        self.c.execute("delete from daily_track")
        self.conn.commit()

    #------clearimng montly tree temporary-------#
    def clear_monthly_tree_once(self):
        for row in self.monthly_track_tree.get_children():
            self.monthly_track_tree.delete(row)

    #--------- fetch data for montly tracking tree----------
    def load_for_monthly(self):
        get_data = self.daily_track_tree.get_children()

        if self.conn:
            self.c = self.conn.cursor()

        date = self.daily_track_date
        raw_amount  = self.total_daily_revenue.get()
        amount = raw_amount.replace("Total Amount:","").replace("₹","")
        total_revenue = amount
        check = self.c.execute("select * from monthly_track")
        data = check.fetchall()
        rank = 0
        for ranks in data:
            rank = ranks[0]

        top_selling = 0
        try:
            for idx,item in enumerate(get_data, 1):
                values = self.daily_track_tree.item(item, 'values')
                top_selling = values[1]
                rank = idx+rank
                break
            if not top_selling or top_selling == 0:
                top_selling = "Data Not Available"
        except:
            top_selling = "Data Not Available"

        if rank % 2 ==0:
            tag = 'evenrow'
        else:
            tag = 'oddrow'

        self.c.execute("select time from monthly_track where time =?", (str(date),))
        existing_date = self.c.fetchone()
        updated_rank = 0
        if existing_date:
            existing_date = existing_date[0]
            self.c.execute("select rank from monthly_track where time =?",(str(existing_date),))
            updated_rank = self.c.fetchone()
            updated_rank = updated_rank[0]


        if existing_date == date: # for stop duplicating the data
            # self.loading_monthly_sales()
            self.c.execute("delete from monthly_track where time=?", (existing_date,))
            self.conn.commit()
            rank = updated_rank
            self.c.execute("insert into monthly_track(rank,time,total_revenue,top_selling) values(?,?,?,?)",
                           (rank, str(date), str(total_revenue), str(top_selling),))
            self.conn.commit()
            self.clear_monthly_tree_once()
            self.monthly_track_tree.insert("", "end", values=(rank, date, total_revenue, top_selling), tags=(tag,))

        else:
            self.c.execute("insert into monthly_track(rank,time,total_revenue,top_selling) values(?,?,?,?)",
                           (rank, str(date), str(total_revenue), str(top_selling),))
            self.conn.commit()
        self.monthly_track_tree.insert("", "end", values=(rank, date, total_revenue, top_selling), tags=(tag,))
        self.dashboard_page()

    #--- for loading monthly sales in tree view-----#
    def loading_monthly_sales(self):
        # Fetch all rows from monthly_track table
        self.c.execute("SELECT rank, time, total_revenue, top_selling FROM monthly_track")
        data = self.c.fetchall()

        for row in data:
            rank, date, total_revenue, top_selling = row

            if int(rank) % 2 == 0:
                tag = "evenrow"
            else:
                tag = "oddrow"

            self.monthly_track_tree.insert(
                "", "end",
                values=(rank, date, total_revenue, top_selling),
                tags=(tag,)
            )


    def accounts_page(self):
        self.clear_page()
        self.set_active_button('account')
        self.calling_profile_variables()
        saved_email, _ = self.get_saved_email_credentials()
        login_email, _, _ = self.get_login_credentials()
        display_email_lines = self.get_email_display_lines()
        self.accounts_frame = Frame(self.root, bg='white')
        self.accounts_frame.pack(fill='both', expand=True)
        self.current_widgets.append(self.accounts_frame)

        head_frame = Frame(self.accounts_frame, bg="#3674B5", relief="raised", bd=3)
        head_frame.pack(fill='x', padx=20, pady=10)

        Label(head_frame, text="Account Settings", font=('Arial', 18, 'bold')
              , bg='#3674B5', fg='white').pack(fill='x', padx=20, pady=10)

        # ---------- Profile Frame ----------#
        your_profile_frame = Frame(self.accounts_frame, bg='#FAF9F6', relief='raised', bd=2)
        your_profile_frame.pack(fill='x', padx=20, pady=10)

        label_frame = Frame(your_profile_frame, bg='#FAF9F6',relief="raised",bd=2)
        label_frame.pack(fill='x', padx=20, pady=10)

        Label(label_frame, text='Your Profile', font=('Arial', 14, 'bold'),
              bg='#FAF9F6').pack(side='left', padx=10)

        self.update_profile_btn = Button(label_frame, text="Update Profile", bg='#00DFA2', fg='white',
                                      font=('Arial', 12, 'bold'), command=self.update_profile)
        self.update_profile_btn.pack(side="left", pady=10,padx=30)

        profile_frame= Frame(your_profile_frame, bg='#FAF9F6')
        profile_frame.pack(fill='x', padx=20, pady=10)

        left_container = Frame(profile_frame, bg='#FAF9F6')
        left_container.pack(side='left', fill='both', padx=10, pady=10)

        # Name label
        # self.username = StringVar(value='Quick SVR')
        name_frame = Frame(left_container,bg='#FAF9F6')
        name_frame.pack(fill='x')
        name_label = Label(name_frame, text='Shop Name : ',
                           font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        name_label.pack( side="left",pady=2)
        self.username = Label(name_frame, text=f"{self.shop_name}",
                           font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        self.username.pack(anchor='w', pady=2)

        # Subscription start label
        sub_start_frame = Frame(left_container,bg='#FAF9F6')
        sub_start_frame.pack(fill='x')
        subscription_label = Label(sub_start_frame, text=f'Subscription starts : ',
                                   font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        subscription_label.pack(side="left", pady=2)
        self.subscription_start = Label(sub_start_frame, text='Provide Name',
                           font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        self.subscription_start.pack(anchor='w', pady=2)

        sub_end_frame = Frame(left_container, bg='#FAF9F6')
        sub_end_frame.pack(fill='x')
        subscription_end_label = Label(sub_end_frame, text=f'Subscription ends : ',
                                   font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        subscription_end_label.pack(side='left', pady=2)
        self.subscription_end = Label(sub_end_frame, text='Provide Name',
              font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        self.subscription_end.pack(anchor='w', pady=2)

        gst_num_frame = Frame(left_container,bg='#FAF9F6')
        gst_num_frame.pack(fill='x')
        gst_number_label = Label(gst_num_frame, text=f'GST number : ',
                                       font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        gst_number_label.pack(side="left", pady=2)
        self.gst_number = Label(gst_num_frame, text=f"{self.gst_number}",
              font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        self.gst_number.pack(anchor='w', pady=2)

        #---------- Account Frame ----------#
        account_frame = Frame(self.accounts_frame, bg='#FAF9F6', relief='raised', bd=2)
        account_frame.pack(fill='x', padx=20, pady=10)

        account_label_frame = Frame(account_frame, bg='#FAF9F6',relief="raised",bd=2)
        account_label_frame.pack(fill='x', padx=20,pady=10)

        Label(account_label_frame, text='Your Account', font=('Arial', 14, 'bold'),
              bg='#FAF9F6').pack(side='left', padx=10,pady=10)

        email_button_text = "Add Email" if not saved_email else "Update Email"
        self.change_email_btn = Button(account_label_frame, text=email_button_text, bg='#0079FF', fg='white',
                                      font=('Arial', 12, 'bold'),command=self.open_email_settings)
        self.change_email_btn.pack(side="left", pady=10,padx=20)

        login_email_button_text = "Add Login Email" if not login_email else "Update Login Email"
        self.change_login_email_btn = Button(
            account_label_frame,
            text=login_email_button_text,
            bg='#5D688A',
            fg='white',
            font=('Arial', 12, 'bold'),
            command=self.open_login_credentials_window
        )
        self.change_login_email_btn.pack(side="left", pady=10, padx=10)

        self.change_pass_btn = Button(account_label_frame, text="Change Password", bg='#FF0060', fg='white',
                                       font=('Arial', 12, 'bold'), command=self.change_password)
        self.change_pass_btn.pack(side="left", pady=10, padx=10)

        email_section_frame = Frame(account_frame, bg='#FAF9F6')
        email_section_frame.pack(fill='x', padx=20, pady=10)

        Label(email_section_frame, text="Your Email:", font=("Arial", 14, 'bold'),
              bg='#FAF9F6', fg='black').pack(anchor='w', padx=20)

        for line in display_email_lines:
            Label(
                email_section_frame,
                text=line,
                font=('Arial', 12, 'bold'),
                bg='#FAF9F6',
                fg='#9929EA'
            ).pack(anchor='w', padx=40, pady=2)

        self.exist_email = saved_email if saved_email else "Not Provided"

        # ---------- Support Frame ----------#
        support_frame = Frame(self.accounts_frame, bg='#FAF9F6', relief='raised', bd=2)
        support_frame.pack(fill='x', padx=20, pady=10)

        support_label_frame = Frame(support_frame, bg='#FAF9F6', relief="raised", bd=2)
        support_label_frame.pack(fill='x', padx=20, pady=10)

        Label(support_label_frame, text='Support From Quick SVR', font=('Arial', 14, 'bold'),
              bg='#FAF9F6').pack(side='left', padx=10, pady=10)

        contact_frame = Frame(support_frame, bg='#FAF9F6')
        contact_frame.pack(fill='x', padx=20, pady=10)

        Label(contact_frame, text="Contact Us: ", font=("Arial", 14, 'bold'), bg='#FAF9F6'
              , fg='black').pack(side="left", padx=20)
        #------------ END of Account Section---------------#

    def update_profile(self):
        self.window_for_buttons()
        self.clear_second_window()
        screen_width = self.button_root.winfo_screenwidth()
        screen_height = self.button_root.winfo_screenheight()
        win_width = 500
        win_height = 600
        # X position → center horizontally
        x_offset = (screen_width // 2) - (win_width // 2)
        # Y position → center vertically
        y_offset = (screen_height // 2) - (win_height // 2)
        # Apply geometry
        self.button_root.geometry(f"{win_width}x{win_height}+{x_offset}+{y_offset}")

        self.update_profile_btn.config(state=DISABLED) #stopping to create duplicate tabs
        try: #ensure that image is available
            logo = PhotoImage(file='..png')
            self.button_root.iconphoto(True, logo)
        except:
            pass

        def close_btn():
            self.button_root.destroy()
            self.update_profile_btn.config(state=NORMAL)
            return

        main_frame = Frame(self.button_root, bg="#4A9782")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)

        frame_one = Frame(main_frame, bg='#F9F3EF', relief="raised", bd=2)
        frame_one.pack(fill='x', padx=10, pady=100)

        shop_name_frame = Frame(frame_one, bg='#F9F3EF', relief="raised", bd=2)
        shop_name_frame.pack(anchor='w',fill='x', padx=10, pady=(30,0))

        Label(shop_name_frame, text=" Update Shop Name: ",font=('Arial', 12, 'bold')
          , bg="#F9F3EF", fg='black').pack(side="left", padx=10, pady=10)

        self.updated_shop_name = ttk.Entry(shop_name_frame, width=30)
        self.updated_shop_name.pack(side="left",padx=(25,0))

        gst_frame = Frame(frame_one, bg='#F9F3EF', relief="raised", bd=2)
        gst_frame.pack(anchor='w', fill='x', padx=10, pady=(20,20))

        Label(gst_frame, text=" Update GST Number : ", font=('Arial', 12, 'bold')
              , bg="#F9F3EF", fg='black').pack(side="left", padx=10, pady=10)

        self.updated_gst_number = ttk.Entry(gst_frame, width=30)
        self.updated_gst_number.pack(side="left", padx=25)

        self.updating_profile_button = Button(frame_one, text="Update", font=('Arial', 12, 'bold'),
                                  width=15, height=2, bg='#3D74B6', fg='white', command=self.updating_profile)
        self.updating_profile_button.pack(pady=20)
        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        try:
            self.button_root.mainloop()
        except:
            pass

    #----- fetching and updaing the update profile ----#
    def updating_profile(self):
        shop_name = self.updated_shop_name.get()
        gst_number = self.updated_gst_number.get()

        self.c.execute("SELECT COUNT(*) FROM profile")
        row_count = self.c.fetchone()[0]

        if row_count == 0:
            # Insert an empty row first (so we can update later)
            self.c.execute("INSERT INTO profile (shop_name, gst_number) VALUES (?, ?)", (None, None))
            self.conn.commit()

        if shop_name and shop_name.strip() != "":
            self.c.execute("UPDATE profile SET shop_name = ?", (shop_name,))
            self.conn.commit()

        if gst_number and gst_number.strip() != "":
            self.c.execute("UPDATE profile SET gst_number = ?", (gst_number,))
            self.conn.commit()
        showinfo("Success", "Updated Successfully")
        self.update_profile_btn.config(state=NORMAL)
        self.accounts_page()
        self.calling_profile_variables()
        self.button_root.destroy()
        #---------------------------------------------------------#

    def change_password(self):
        try:
            row = self.get_latest_profile_row()
            saved_email = row[3] if row and row[3] else None
        except:
            saved_email = None

        if not saved_email or str(saved_email).strip() == "" or str(saved_email).strip() == "Not Provided":
            self.guarded_showerror(
                "No Email Found",
                "No email is provided for this account. Please add or update an email first.",
                getattr(self, "change_pass_btn", None)
            )
            return

        self.exist_email = saved_email
        self.window_for_buttons()
        self.clear_second_window()
        #Disable button
        self.change_pass_btn.config(state=DISABLED)
        try:
            logo = PhotoImage(file='..png')
            self.button_root.iconphoto(True, logo)
        except:
            pass

        main_frame = Frame(self.button_root, bg="#4A9782")
        main_frame.pack(fill='both', padx=10,pady=10,expand=True)
        self.current_second_button.append(main_frame)

        Label(main_frame, text=" * OTP has been sent to your mail kindly verify to proceed futher. ", font=('Times New Romen', 10, 'bold')
              , bg="white", fg='red').pack(fill="x", padx=10, pady=(40,0))

        self.verify_pass_frame = Frame(main_frame, bg='#F9F3EF', relief="raised", bd=2)
        self.verify_pass_frame.pack(fill='x', padx=10, pady=(70,0))

        self.verify_new_pass_label = Label(self.verify_pass_frame, text="Verify OTP : ", font=('Arial', 12, 'bold')
              , bg="#F9F3EF", fg='black')
        self.verify_new_pass_label.pack(side="left", padx=10, pady=10)

        self.verify_pass_otp = ttk.Entry(self.verify_pass_frame, width=25)
        self.verify_pass_otp.pack(side='left', padx=8, pady=10)

        self.send_pass_otp = Button(self.verify_pass_frame, text="Verify", font=("Arial", 12, 'bold'), bg='#0D5EA6', fg='white',
                                   command=self.verify_pass_change)
        self.send_pass_otp.pack(side="left", pady=10, padx=(30, 0))

        self.pass_otp_status_label = Label(main_frame, text="", font=('Arial', 11, 'bold'), bg="#4A9782", fg='red')
        self.pass_otp_status_label.pack(fill='x', padx=20, pady=(10, 0))

        frame_two = Frame(main_frame, bg='#F9F3EF', relief="raised", bd=2)
        frame_two.pack(fill='x', padx=10, pady=(25,0))

        self.new_pass_label = Label(frame_two, text="New Password : ", font=('Arial', 12, 'bold'),
                                    bg="#F9F3EF", fg='red')
        self.new_pass_label.pack(side="left", padx=10, pady=10)

        self.new_pass = ttk.Entry(frame_two, width=25, state=DISABLED, show='*')
        self.new_pass.pack(side='left', padx=8, pady=10)
        self.add_password_toggle(frame_two, self.new_pass)

        frame_three = Frame(main_frame, bg='#4A9782')
        frame_three.pack(fill='x', padx=10, pady=(25,0))

        self.pass_otp_button = Button(frame_three, text="Submit", font=('Arial', 12, 'bold'),
                                      width=15, height=2, bg='#0D5EA6', fg='white',command=self.pass_change_verification, state=DISABLED)
        self.pass_otp_button.pack(padx=10, pady=10)

        #-------- Mail Structure ------------#
        self.otp_generating()
        self.mail_address = self.exist_email
        self.mail_subject = "Confirm Your Password Change Request"
        self.html_message = self.html_message = f"""
            <div style="font-family:Arial,Helvetica,sans-serif; max-width:600px; margin:auto; padding:20px; 
            background:#f9f9f9; border:1px solid #ddd; border-radius:12px;">

            <!-- Header -->
            <div style="background:#6C63FF; color:#fff; padding:15px; text-align:center; border-radius:10px 10px 0 0;">
            <h2 style="margin:0;">Quick SVR Security</h2>
            </div>

            <!-- Body -->
            <div style="padding:20px; color:#333;">
            <p>Hello,</p>
            <p>We received a request to <b>change the password</b> linked to your account.</p>
            <p>Please use the One-Time Password (OTP) below to confirm this change:</p>

            <!-- OTP Box -->
            <div style="font-size:36px; font-weight:bold; color:#6C63FF; background:#fff; 
                border:2px dashed #6C63FF; border-radius:10px; 
                text-align:center; padding:15px; margin:25px 0;">
                {self.otp_number}
            </div>

            <p style="color:#555;">This code will expire in <b>5 minutes</b>. 
            If you did not request this change, please ignore this email or contact our support team immediately.</p>
             </div>

             <!-- Footer -->
            <div style="background:#f1f1f1; padding:12px; text-align:center; font-size:12px; color:#777; border-radius:0 0 10px 10px;">
            <p>Best regards,<br><b>Quick SVR Team</b></p>
            </div>
            </div>
            """

        self.sending_otp_email() #calling the send mail function
        self.button_root.protocol("WM_DELETE_WINDOW", self.close_popup_window)
        try:
            self.button_root.mainloop()
        except:
            pass
        #--------------------------------------------------------------------------------------------


    def verify_pass_change(self):
        otp = self.otp_number
        received_otp = self.verify_pass_otp.get().strip()

        if not received_otp:
            self.pass_otp_status_label.config(text="Incorrect or invalid OTP")
            self.verify_pass_otp.config(background='red')
            self.verify_new_pass_label.config(fg='red')
            return

        if otp == received_otp:
            self.pass_otp_status_label.config(text="OTP verified successfully", fg='green')
            self.verify_pass_otp.config(state=DISABLED)
            self.send_pass_otp.config(state=DISABLED)
            self.new_pass.config(state=NORMAL)
            self.new_pass_label.config(fg='black')
            self.pass_otp_button.config(state=NORMAL)
            self.verify_new_pass_label.config(fg='black')
            self.verify_pass_frame.after(300, self.verify_pass_frame.pack_forget)
        else:
            self.pass_otp_status_label.config(text="Incorrect or invalid OTP", fg='red')
            self.verify_pass_otp.config(background='red')
            self.verify_new_pass_label.config(fg='red')
        return

    def pass_change_verification(self):
        new_password = self.new_pass.get().strip()

        if not new_password:
            self.guarded_showerror("Password Required", "Enter a new password first.", self.pass_otp_button)
            return

        try:
            login_email, _, _ = self.get_login_credentials()
            fallback_email, _ = self.get_saved_email_credentials()
            login_email_to_store = login_email if login_email else fallback_email

            self.c.execute("SELECT COUNT(*) FROM profile")
            row_count = self.c.fetchone()[0]

            if row_count == 0:
                self.c.execute(
                    "INSERT INTO profile (email, app_password, login_email, account_password) VALUES (?, ?, ?, ?)",
                    (
                        self.exist_email if hasattr(self, "exist_email") else None,
                        None,
                        login_email_to_store,
                        new_password
                    )
                )
            else:
                self.c.execute(
                    "UPDATE profile SET account_password = ?, login_email = COALESCE(NULLIF(login_email, ''), ?)",
                    (new_password, login_email_to_store)
                )

            self.conn.commit()
            self.account_login_password = new_password
            self.login_email_value = login_email_to_store if login_email_to_store else self.login_email_value
            showinfo("Success", "Password updated successfully.")
            self.close_popup_window()
        except Exception as e:
            self.guarded_showerror("Password Error", f"Problem: {e}", self.pass_otp_button)

if __name__ == "__main__":
    app = Billing()
