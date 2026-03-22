from email.message import EmailMessage
from tkinter import *
from tkinter.messagebox import showerror, showinfo, showwarning
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

        #for updated item to fetch in combobox
        self.updated_items = {}

        self.init_database()
        self.load_item_menu()
        self.main_window()
        self.navigation_frame()

        self.root.mainloop()
    # --- creating main database ---
    def init_database(self):
        try:
            self.conn = sqlite3.connect('billing_sft.db')
            self.c = self.conn.cursor()

            #database for main menu
            self.c.execute("create table if not exists menu(name text, price integer)")
            self.c.execute("create table if not exists daily_track(id integer, name text, total_sold integer, unit_price float, total_revenue float)")
            self.conn.commit()

            # database for daily sales track

            # self.conn.commit()

        except Exception as e:
            showerror("Database Error", f"Problem {e}")

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

        self.login_button = Button(self._nav_frame, text="Logout", font=('Arial',12),
                                   width=20, height=2, bg='#e74c3c',fg='white')
        self.login_button.pack(fill='x',pady=10,padx=10)

    # --- design to active button ---
    def set_active_button(self, active_page):
            for page, button in self.nav_buttons.items():
                if page == active_page:
                    button.config(bg='#3498db', fg='white')
                else:
                    button.config(bg='#ecf0f1', fg='black')

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

    #--- second root windows ---
    def window_for_buttons(self):
        self.button_root = Tk()
        self.button_root.title("Quick SVR")
        self.button_root.config(bg='white')
        self.button_root.geometry("500x500")


    #------------ BIlling Page Configuration -------------#
    def set_billing_page(self):
        self.clear_page()
        self.set_active_button('billing')
        self.content_frame = Frame(self.root, bg='white')
        self.content_frame.pack(fill='both',expand=True)
        self.current_widgets.append(self.content_frame)
        head_frame = Frame(self.content_frame, bg="#9B177E", relief="raised", bd=3)
        head_frame.pack(fill='x', padx=20, pady=10)

        Label(head_frame, text="Quick SVR - Billing System", font=('Arial', 18, 'bold')
              , bg='#9B177E', fg='white').pack(fill='x', padx=20, pady=10)

        item_frame = Frame(self.content_frame,bg='#FAF9F6',relief='raised', bd=2)
        item_frame.pack(fill='x', padx=20,pady=10)

        controls_frame = Frame(item_frame, bg='#FAF9F6')
        controls_frame.pack(fill='x', padx=20, pady=15)

        Label(controls_frame, text='Select Item:', font=('Arial',12),
              bg='#FAF9F6').pack(side='left',padx=10)

        self.selected_billing_item = ""
        self.billing_menu_items = []
        self.item_search_var = StringVar()
        self.item_search_wrapper = Frame(controls_frame, bg='#FAF9F6')
        self.item_search_wrapper.pack(side='left', padx=10)
        self.item_search_entry = ttk.Entry(self.item_search_wrapper, width=25, textvariable=self.item_search_var)
        self.item_search_entry.pack()
        self.item_search_entry.bind("<KeyRelease>", self.filter_billing_items)
        self.item_search_entry.bind("<Down>", self.focus_billing_menu)
        self.item_search_entry.bind("<Button-1>", self.show_billing_menu)
        self.item_search_entry.bind("<Escape>", self.hide_billing_menu)

        Label(controls_frame, text="Quantity", font=('Arial', 12), bg='#FAF9F6', fg='black'
              ).pack(side='left',padx=10)

        self.quantity_entry = ttk.Entry(controls_frame, width=15)
        self.quantity_entry.pack(side='left', padx=10)

        self.add_button = Button(controls_frame, text="Add Item", bg='#A4DD00',fg='white',
                                 font=('Arial',12,'bold'),command=self.add_to_combo)
        self.add_button.pack(side='left', padx=10)

        self.remove_button = Button(controls_frame, text="Remove Item", bg='#FF3F33',fg='white',
                                 font=('Arial',12,'bold'),command=self.remove_in_tree)
        self.remove_button.pack(side='left',padx=10)

        self.datetime_label = Label(controls_frame, text="", font=('Arial', 12),bg='#FAF9F6',fg='black')
        self.datetime_label.pack(side='right', padx=10)
        self.update_datetime()

        self.create_billing_menu_popup()
        if not self.billing_menu_global_binding_set:
            self.root.bind_all("<Button-1>", self.handle_global_billing_click, add="+")
            self.billing_menu_global_binding_set = True

        self.refresh_billing_item_menu()

        #ORDER TREE MAKING
        self.order_frame = Frame(self.content_frame, bg='#FAF9F6', relief='raised', bd=2)
        self.order_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.tree_frame = Frame(self.order_frame, bg='white', relief='raised')
        self.tree_frame.pack(fill="both", pady=20,padx=10)

        self.order_tree = Treeview(self.tree_frame, columns=("Order", "Item", "Quantity", "Price"),
                                   show="headings", height=18)

        self.order_tree.heading("Order", text="Order #")
        self.order_tree.heading("Item", text="Item Name")
        self.order_tree.heading("Quantity", text="Quantity")
        self.order_tree.heading("Price", text="Price (₹)")

        self.order_tree.column("Order", width=80, anchor="center")
        self.order_tree.column("Item", width=200, anchor="center")
        self.order_tree.column("Quantity", width=100, anchor="center")
        self.order_tree.column("Price", width=100, anchor="center")

        #Scrollbar
        scrollbar = Scrollbar(self.tree_frame, orient="vertical", command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.order_tree.pack(side="left", fill="both", expand=True)

        totaling_frame = Frame(self.order_frame, bg='#B2BEB5', height=50 )
        totaling_frame.pack(fill='x', padx=10, pady=10)
        totaling_frame.pack_propagate(False)

        self.total_item_order = StringVar(value='Total Items: 0')
        self.total_price_order = StringVar(value='Total Amount: ₹0')

        Label(totaling_frame, textvariable=self.total_price_order,
              font=("Arial", 14, "bold"), bg='#B2BEB5').pack(side="right", padx=100, pady=10)

        Label(totaling_frame, textvariable=self.total_item_order,
              font=('Arial', 14, 'bold'), bg='#B2BEB5', fg='black').pack(side="right", padx=20, pady=10)

        self.button_frame = Frame(self.content_frame, bg='#FAF9F6',relief="raised", bd=2)
        self.button_frame.pack(fill='x', padx=20, pady=10)

        self.generate_bill = Button(self.button_frame, text='Generate Bill', font=('Arial',12, 'bold'),
               width=15, height=2, bg='#28a745',fg='white', command=self.bill_generating)
        self.generate_bill.pack(side='right',padx=10,pady=10)

        self.clear_btn = Button(self.button_frame, text="Clear All", font=('Arial',12, 'bold'),
               width=15, height=2, bg='#ffc107',fg='white',command=self.clear_tree)
        self.clear_btn.pack(side='right',padx=10,pady=10)

        self.sale_btn = Button(self.button_frame, text="Toady's Sale", font=('Arial',12, 'bold'),
               width=15, height=2, bg='#17a2b8',fg='white', command=self.dashboard_page)
        self.sale_btn.pack(side='right',padx=10,pady=10)

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

        # if not re.match(pattern, customer_email) or not customer_email:
        #     showerror("Error", "Incorrect email format!")
        #     self.button_root.destroy()
        #     self.clear_second_window()
        #     self.window_for_buttons()
        #     self.single_order_emailing()
        #     return

        timestamp = datetime.now().strftime("%Y-%m-%d_%I-%M-%S_%p")
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
        full_path = os.path.join(desktop_path, filename)
        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "RESTAURANT BILL", ln=True, align='C')
        pdf.ln(5)

        # Customer & Date
        pdf.set_font("Arial", '', 12)
        date_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        pdf.cell(0, 10, f"Customer: {customer_name}", ln=True)
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

        self.owner_email = "ncerohan@gmail.com"
        self.app_password = "kxraktkjspeoeyga"
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

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(self.owner_email, self.app_password)
            smtp.send_message(message)
        showinfo("Success","Email send successfully")

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
            int(quantity)

            if isinstance(quantity, int):
                unit_price = self.updated_items[item]
                existing_item = False

                for order_item in self.order_items:
                    if order_item[0] == item:
                        order_item[1] += quantity
                        order_item[2] = unit_price * order_item[1]
                        existing_item = True
                        break

                if not existing_item:
                    price = unit_price * quantity
                    self.order_items.append([item, quantity, price])

                self.update_order_tree()
            else:
                showerror("Error", "Please Enter Quantity")
        except Exception as e:
            pass
        self.quantity_entry.delete(0, END)
        self.selected_billing_item = ""
        self.item_search_var.set("")
        self.refresh_billing_item_menu()
        self.hide_billing_menu()

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

        Label(update_btn_frame, text="Manage Item List: ",
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

        self.update_email_btn = Button(update_email_frame, text="Update Email", bg='#FFCC00', fg='white',
                                       font=('Arial', 12, 'bold'), width=15, height=2, command=self.updating_email)
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

        main_frame = Frame(self.button_root, bg="#FFEAD8")
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
                                      width=15, height=2, bg='#46edc8', fg='white',command=self.new_item_in_menu)
        self.submit_add_item.pack(padx=10,pady=10)
        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)

        self.button_root.mainloop()

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

        main_frame = Frame(self.button_root, bg="#FFEAD8")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)

        name_frame = Frame(main_frame, bg='#F9F3EF', relief="raised", bd=2)
        name_frame.pack(fill='x', padx=10, pady=100)

        item_frame = Frame(name_frame, bg='#F9F3EF', relief="raised", bd=1,height=40)
        item_frame.pack(fill='x', padx=10, pady=10)
        item_frame.pack_propagate(False)

        Label(item_frame, text='Select Item:', font=('Arial', 12),
              bg='#FAF9F6').pack(side='left', padx=10)

        self.combo_box = Combobox(item_frame, values=list(self.item_menu.keys()), width=25, font=('Arial', 10))
        self.combo_box['values'] = list(self.item_menu.keys())  # Set full item list
        self.combo_box.set("Choose Items")
        self.combo_box.pack(side='left', padx=10)
        self.updating_combo()

        self.delete_selected_item = Button(name_frame, text="Submit",font=('Arial', 12, 'bold'),
                                      width=15, height=2, bg='#46edc8', fg='white',command=self.deleting_selected_item)
        self.delete_selected_item.pack(padx=10,pady=10)

        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        self.button_root.mainloop()

    def deleting_selected_item(self):
        def close_btn():
            self.button_root.destroy()
            for i in self.four_btn_list:
                i.config(state=NORMAL)
        item = self.combo_box.get()

        if item == "Choose Items" or item == "":
            showerror("Error", "Select A item to Delete")

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


        main_frame = Frame(self.button_root, bg="#FFEAD8")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)

        second_frame = Frame(main_frame, bg='#F9F3EF', relief="raised", bd=2)
        second_frame.pack(fill='x', padx=10, pady=100)

        choose_frame = Frame(second_frame, bg='#F9F3EF')
        choose_frame.pack(fill='x', padx=10)

        Label(choose_frame, text="Choose item ", font=('Arial', 12, 'bold')
              , bg="#F9F3EF", fg='black').pack(side="left", fill='x',padx=10, pady=10)

        Label(choose_frame, text="Price ", font=('Arial', 12, 'bold')
              , bg="#F9F3EF", fg='black').pack(side="right",fill='x', padx=30, pady=10)

        first_frame = Frame(second_frame,bg='#F9F3EF')
        first_frame.pack(fill='x',pady=(0,10))
        self.combo_box = Combobox(first_frame, width=25, font=('Arial', 10),values=list(self.item_menu.keys()))
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
                                      width=15, height=2, bg='#46edc8', fg='white', command=self.new_updated_item)
        self.submit_update_btn.pack(padx=10, pady=10)
        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        self.button_root.mainloop()

    def new_updated_item(self):
        changed_name = self.updated_name_entry.get()
        changed_price = self.updated_price_entry.get()
        selected_item= self.combo_box.get()

        self.c.execute("UPDATE menu SET name = ? WHERE name = ?", (changed_name, selected_item))
        self.conn.commit()
        try:
            self.c.execute("UPDATE menu SET price = ? WHERE name = ?", (changed_price, changed_name))
            self.conn.commit()
        except Exception as e:
            print(e)
        self.updating_combo()


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
            self.button_root.destroy()
            try:
                for i in self.four_btn_list:
                    i.config(state=NORMAL)
            except:
                pass

            #------ Enable the email button on Account page -------#
            try:
                self.change_email_btn.configure(state=NORMAL)
            except:
                pass

        main_frame = Frame(self.button_root, bg="#FFEAD8")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)

        second_frame = Frame(main_frame, bg='#FFEAD8',relief="raised", bd=1)
        second_frame.pack(fill="both",padx=10,pady=100)

        label_frame = Frame(second_frame, bg='#EAD8A4',relief="raised", bd=1)
        label_frame.pack(fill='x',padx=10,pady=10)

        email_label = Label(label_frame, text="Current Email:",font=('Arial',12,'bold'),bg='#EAD8A4')
        email_label.pack(fill='x',side='left',padx=10, pady=10)

        self.old_mail_entry = ttk.Entry(label_frame,width=25)
        self.old_mail_entry.pack(side='left',padx=8, pady=10)

        label2_frame = Frame(second_frame, bg='#EAD8A4', relief="raised", bd=1)
        label2_frame.pack(fill='x', padx=10, pady=10)

        email_label = Label(label2_frame, text="New Email:", font=('Arial', 12, 'bold'), bg='#EAD8A4')
        email_label.pack(fill='x', side='left', padx=10, pady=10)

        self.new_mail_entry = ttk.Entry(label2_frame, width=25)
        self.new_mail_entry.pack(side='left', padx=30, pady=10)

        self.send_otp_new = Button(label2_frame, text="Send OTP", font=("Arial", 12, 'bold'), bg='#28a745', fg='white',command=self.send_otp_newmail)
        self.send_otp_new.pack(side="left" , pady=10)

        label3_frame = Frame(second_frame, bg='#EAD8A4', relief="raised", bd=1)
        label3_frame.pack(fill='x', padx=10, pady=10)

        Label(label3_frame, text="Verify OTP: ", font=('Arial', 12, 'bold'), bg='#EAD8A4').pack(fill='x', side='left', padx=10, pady=10)

        self.verify_otp_enrty = ttk.Entry(label3_frame, width=25)
        self.verify_otp_enrty.pack(side='left', padx=30, pady=10)

        self.email_updating_btn = Button(second_frame, text="Update", font=('Arial', 12, 'bold'),
                                      width=15, height=2, bg='#46edc8', fg='white')
        self.email_updating_btn.pack(padx=10, pady=10)

        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        self.button_root.mainloop()


    #------------ Sub Buttons of the 4 buttons of updata pages ----------

        #for adding new item in menu
    def new_item_in_menu(self):
        for i in self.four_btn_list:
            i.config(state=NORMAL)
        try:
            self.conn = sqlite3.connect('billing_sft.db')
            self.c = self.conn.cursor()
            self.c.execute("create table if not exists menu(name text, price integer)")

        # --- check add info is avalilable ---10.
            item_name = self.add_item_entry.get().strip()
            if not item_name:
                showerror("Error", "Add Name of Item")
                return  # Important: return to stop execution

            price_text = self.add_price_entry.get().strip()
            if not price_text:
                showerror("Error", "Add Price of Item")
                return  # Important: return to stop execution

            # --- check price is a number ----
            try:
                price = int(price_text)
                if price <= 0:
                    showerror("Error", "Price is 0")
                    return
            except ValueError:
                showerror("Error", "Invalid Price")
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
            showerror("Database Error", f"Database problem: {e}")
        except Exception as e:
            showerror("Adding Error", f"Problem: {e}")
        finally:
            # Always close connections
            # if hasattr(self, 'c') and self.c:
            #     self.c.close()
            # if hasattr(self, 'conn') and self.conn:
            #     self.conn.close()
            self.button_root.destroy()

    def updating_combo(self):
        self.combo_box['values'] = list(self.updated_items.keys())
        self.combo_box.set("Choose Items")

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
            self.show_billing_menu()
        else:
            self.selected_billing_item = ""
            self.hide_billing_menu()

    def filter_billing_items(self, event=None):
        search_text = self.item_search_var.get()
        self.selected_billing_item = ""
        self.refresh_billing_item_menu(search_text)

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

    def focus_billing_menu(self, event=None):
        if self.billing_item_listbox.size() == 0:
            return "break"

        self.show_billing_menu()
        self.billing_item_listbox.focus_set()
        self.billing_item_listbox.selection_clear(0, END)
        self.billing_item_listbox.selection_set(0)
        return "break"

    def show_billing_menu(self, event=None):
        if not hasattr(self, "billing_menu_popup") or not self.billing_menu_items:
            return

        self.root.update_idletasks()
        x = self.item_search_entry.winfo_rootx()
        y = self.item_search_entry.winfo_rooty() + self.item_search_entry.winfo_height() + 2
        width = max(self.item_search_entry.winfo_width(), 260)
        height = min(max(len(self.billing_menu_items), 1), 6) * 24 + 4

        self.billing_menu_popup.geometry(f"{width}x{height}+{x}+{y}")
        self.billing_menu_popup.deiconify()
        self.billing_menu_popup.lift()

    def hide_billing_menu(self, event=None):
        if hasattr(self, "billing_menu_popup"):
            self.billing_menu_popup.withdraw()
        return "break" if event else None

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

    def handle_global_billing_click(self, event):
        if not hasattr(self, "billing_menu_popup") or not self.billing_menu_popup.winfo_exists():
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


    #for sending OTP for email verification
    def send_otp_newmail(self):
        return

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
        # Label(label_frame, text="Daily Sales", bg='white', font=("Arial", 14, 'bold')).pack(side='left')
        Label(label_frame, text=f"{now.strftime('(%A) %d %B, %Y')}", bg='#FAF9F6', font=("Arial", 14, 'bold')).pack(
            side="left",padx=10)

        self.total_daily_revenue = StringVar(value='Total Amount: ₹0')
        Label(label_frame, textvariable=self.total_daily_revenue,
              font=("Arial", 14, "bold"), bg='#FAF9F6').pack(side="left", padx=100, pady=10)

        self.daily_print_btn = Button(label_frame, text="Generate PDF", bg='#28a745', fg='white',
                                      font=('Arial', 12, 'bold'))
        self.daily_print_btn.pack(side="right", padx=10, pady=10)

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
                                      font=('Arial', 12, 'bold'))
        self.monthly_print_btn.pack(side="right", padx=20, pady=10)

        monthly_tree_frame = Frame(monthly_track_frame, bg='#FAF9F6')
        monthly_tree_frame.pack(fill='both', expand=True, pady=10)
        # columns = ('Rank', 'Item', 'Total Sold', 'Total Revenue', 'Orders Count')
        self.monthly_track_tree = Treeview(monthly_tree_frame, columns=columns, show='headings', height=12)

        # Configure column headings and widths
        column_configs = {
            'Rank': {'width': 60, 'anchor': 'center'},
            'Item Name': {'width': 150, 'anchor': 'w'},
            'Unit Price': {'width': 100, 'anchor': 'center'},
            'Total Sold': {'width': 120, 'anchor': 'e'},
            'Total Revenue': {'width': 100, 'anchor': 'center'}
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
        self.monthly_track_tree.tag_configure('top3', background='#E8F5E8', foreground='#2E7D32')

        #calling loading data
        self.loading_data()
        # ---- for updaint the tatal revenue-----#
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

    def change_password(self):
        self.window_for_buttons()
        self.clear_second_window()

        self.change_pass_btn.config(state=DISABLED)

        def close_btn():
            self.button_root.destroy()
            self.change_pass_btn.config(state=NORMAL)

        main_frame = Frame(self.button_root, bg="#FAF7F3")
        main_frame.pack(fill='both', padx=10, pady=10, expand=True)
        self.current_second_button.append(main_frame)

        second_frame = Frame(main_frame, bg='#FFEAD8', relief="raised", bd=1)
        second_frame.pack(fill="both", padx=10, pady=100)

        label_frame = Frame(second_frame, bg='#F0E4D3', relief="raised", bd=1)
        label_frame.pack(fill='x', padx=10, pady=10)

        email_label = Label(label_frame, text="Current Email:", font=('Arial', 12, 'bold'), bg='#F0E4D3')
        email_label.pack(fill='x', side='left', padx=10, pady=10)

        self.old_mail_entry = Entry(label_frame, width=25)
        self.old_mail_entry.pack(side='left', padx=8, pady=10)

        self.send_otp_new = Button(label_frame, text="Send OTP", font=("Arial", 12, 'bold'), bg='#28a745', fg='white',
                                   command=self.send_otp_newmail)
        self.send_otp_new.pack(side="left",padx=5, pady=10)

        label2_frame = Frame(second_frame, bg='#F0E4D3', relief="raised", bd=1)
        label2_frame.pack(fill='x', padx=10, pady=10)

        Label(label2_frame, text="Verify OTP: ", font=('Arial', 12, 'bold')
              , bg='#F0E4D3').pack(fill='x', side='left',padx=10, pady=10)

        self.verify_otp_enrty = Entry(label2_frame, width=25)
        self.verify_otp_enrty.pack(side='left', padx=30, pady=10)

        label3_frame = Frame(second_frame, bg='#F0E4D3', relief="raised", bd=1)
        label3_frame.pack(fill='x', padx=10, pady=10)

        password_label = Label(label3_frame, text="New Password:", font=('Arial', 12, 'bold'), bg='#F0E4D3')
        password_label.pack(fill='x', side='left', padx=10, pady=10)

        self.new_password_entry = Entry(label3_frame, width=25)
        self.new_password_entry.pack(side='left', padx=8, pady=10)

        self.pass_updating_btn = Button(second_frame, text="Change", font=('Arial', 12, 'bold'),
                                         width=15, height=2, bg='#46edc8', fg='white')
        self.pass_updating_btn.pack(padx=5, pady=10)

        self.button_root.protocol("WM_DELETE_WINDOW", close_btn)
        self.button_root.mainloop()


    def accounts_page(self):
        self.clear_page()
        self.set_active_button('account')
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

        self.change_profile_btn = Button(label_frame, text="Update Profile", bg='#00DFA2', fg='white',
                                      font=('Arial', 12, 'bold'))
        self.change_profile_btn.pack(side="left", pady=10,padx=30)

        profile_frame= Frame(your_profile_frame, bg='#FAF9F6')
        profile_frame.pack(fill='x', padx=20, pady=10)

        left_container = Frame(profile_frame, bg='#FAF9F6')
        left_container.pack(side='left', fill='y', padx=10, pady=10)

        # Name label
        self.username = StringVar(value='Quick SVR')
        name_label = Label(left_container, text=f'Name : {self.username.get()}',
                           font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        name_label.pack(anchor='w', pady=2)

        # Subscription start label
        self.subscription_start = StringVar(value="-")
        subscription_label = Label(left_container, text=f'Subscription starts : {self.subscription_start.get()}',
                                   font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        subscription_label.pack(anchor='w', pady=2)

        self.subscription_end = StringVar(value="-")
        subscription_end_label = Label(left_container, text=f'Subscription ends : {self.subscription_end.get()}',
                                   font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        subscription_end_label.pack(anchor='w', pady=2)

        self.gst_number = StringVar(value="-")
        gst_number_label = Label(left_container, text=f'GST number : {self.gst_number.get()}',
                                       font=('Arial', 12, 'bold'), bg='#FAF9F6', fg='black')
        gst_number_label.pack(anchor='w', pady=2)

        #---------- Account Frame ----------#
        account_frame = Frame(self.accounts_frame, bg='#FAF9F6', relief='raised', bd=2)
        account_frame.pack(fill='x', padx=20, pady=10)

        account_label_frame = Frame(account_frame, bg='#FAF9F6',relief="raised",bd=2)
        account_label_frame.pack(fill='x', padx=20,pady=10)

        Label(account_label_frame, text='Your Account', font=('Arial', 14, 'bold'),
              bg='#FAF9F6').pack(side='left', padx=10,pady=10)

        self.change_email_btn = Button(account_label_frame, text="Update Email", bg='#0079FF', fg='white',
                                      font=('Arial', 12, 'bold'),command=self.updating_email)
        self.change_email_btn.pack(side="left", pady=10,padx=20)

        self.change_pass_btn = Button(account_label_frame, text="Change Password", bg='#FF0060', fg='white',
                                       font=('Arial', 12, 'bold'), command=self.change_password)
        self.change_pass_btn.pack(side="left", pady=10, padx=10)

        email_frame = Frame(account_frame, bg='#FAF9F6')
        email_frame.pack(fill='x', padx=20, pady=10)

        Label(email_frame, text="Your Email: ",font=("Arial",14,'bold'),bg='#FAF9F6'
              ,fg='black').pack(side="left",padx=20)

        self.email_name = StringVar(value='quicksvr@gmail.com')
        email_label = Label(email_frame, text=f'{self.email_name.get()}',font=('Arial',12,'bold'),bg='#FAF9F6',fg='#9929EA')
        email_label.pack(side="left")

        # ---------- Support Frame ----------#
        support_frame = Frame(self.accounts_frame, bg='#FAF9F6', relief='raised', bd=2)
        support_frame.pack(fill='x', padx=20, pady=10)

        support_label_frame = Frame(support_frame, bg='#FAF9F6', relief="raised", bd=2)
        support_label_frame.pack(fill='x', padx=20, pady=10)

        Label(support_label_frame, text='Support From Quick SVR', font=('Arial', 14, 'bold'),
              bg='#FAF9F6').pack(side='left', padx=10, pady=10)

        contact_frame = Frame(support_frame, bg='#FAF9F6')
        email_frame.pack(fill='x', padx=20, pady=10)

        Label(contact_frame, text="Contact Us: ", font=("Arial", 14, 'bold'), bg='#FAF9F6'
              , fg='black').pack(side="left", padx=20)


    def load_sales_data(self):
        # get the item of main tree in list
        get_data = self.order_tree.get_children()
        self.data_list = []
        if self.conn:
            self.c = self.conn.cursor()

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

    def clear_daily_tree(self):
        for row in self.daily_track_tree.get_children():
            self.daily_track_tree.delete(row)

        self.c.execute("delete from daily_track")
        self.conn.commit()


if __name__ == "__main__":
    app = Billing()
