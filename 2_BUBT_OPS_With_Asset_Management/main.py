import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import database as db

db.create_tables()

class BUBTOPS(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(db.get_setting("application_name", "BUBT-OPS"))
        self.geometry("1180x720")
        self.minsize(980, 600)
        self.current_admin = db.get_admin()[0] or "Admin"
        self.search_var = tk.StringVar()
        self.configure(bg="#f3f4f6")
        self.build_shell()
        self.show_dashboard()

    def build_shell(self):
        self.sidebar = tk.Frame(self, bg="#202938", width=215)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="BUBT-OPS", bg="#202938", fg="white",
                 font=("Arial", 20, "bold")).pack(pady=(25, 4))
        tk.Label(self.sidebar, text="University Asset System", bg="#202938",
                 fg="#cbd5e1", font=("Arial", 9)).pack(pady=(0, 25))
        items = [
            ("Dashboard", self.show_dashboard),
            ("Asset Management", self.show_assets),
            ("Settings", self.show_settings_home),
            ("About Application", self.show_about),
        ]
        for label, command in items:
            tk.Button(self.sidebar, text=label, command=command, anchor="w",
                      bg="#202938", fg="white", activebackground="#374151",
                      activeforeground="white", relief="flat", padx=20,
                      pady=12, font=("Arial", 10)).pack(fill="x", padx=8, pady=2)
        self.content = tk.Frame(self, bg="#f3f4f6")
        self.content.pack(side="right", fill="both", expand=True)

    def clear(self):
        target = self.settings_panel if getattr(self, "settings_mode", False) and hasattr(self, "settings_panel") else self.content
        for widget in target.winfo_children():
            widget.destroy()

    def heading(self, title, subtitle=""):
        target = self.settings_panel if getattr(self, "settings_mode", False) and hasattr(self, "settings_panel") else self.content
        tk.Label(target, text=title, bg="#f3f4f6", fg="#111827",
                 font=("Arial", 20, "bold")).pack(anchor="w", padx=25, pady=(22, 3))
        if subtitle:
            tk.Label(target, text=subtitle, bg="#f3f4f6", fg="#6b7280",
                     font=("Arial", 10)).pack(anchor="w", padx=27, pady=(0, 15))

    def show_dashboard(self):
        self.settings_mode = False
        self.clear()
        self.heading("Dashboard", "University Asset Overview")
        with db.connect_db() as con:
            total = con.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
            quantity = con.execute("SELECT COALESCE(SUM(quantity),0) FROM assets").fetchone()[0]
            categories = con.execute("SELECT COUNT(DISTINCT category) FROM assets").fetchone()[0]
        cards = tk.Frame(self.content, bg="#f3f4f6")
        cards.pack(fill="x", padx=25, pady=15)
        for label, value in [("Asset Records", total), ("Total Quantity", quantity), ("Categories Used", categories)]:
            card = tk.Frame(cards, bg="white", padx=25, pady=20, highlightbackground="#e5e7eb", highlightthickness=1)
            card.pack(side="left", padx=(0, 15))
            tk.Label(card, text=label, bg="white", fg="#6b7280", font=("Arial", 10)).pack(anchor="w")
            tk.Label(card, text=str(value), bg="white", fg="#111827", font=("Arial", 24, "bold")).pack(anchor="w", pady=(6,0))
        tk.Label(self.content, text="Use Asset Management to add, update, search and delete university assets.",
                 bg="#f3f4f6", fg="#374151", font=("Arial", 11)).pack(anchor="w", padx=27, pady=15)

    def show_assets(self):
        self.settings_mode = False
        self.clear()
        self.heading("Asset Management", "Add, view, update and delete university assets. Changes are recorded in History.")
        form = tk.Frame(self.content, bg="white", padx=15, pady=12)
        form.pack(fill="x", padx=25, pady=(0, 12))
        labels = ["Asset ID", "Asset Name", "Category", "Quantity", "Location", "Status", "Description"]
        self.asset_vars = {name: tk.StringVar() for name in labels}
        self.asset_vars["Quantity"].set("1")
        self.asset_vars["Status"].set("Available")
        for i, name in enumerate(labels):
            r, c = divmod(i, 4)
            cell = tk.Frame(form, bg="white")
            cell.grid(row=r, column=c, sticky="ew", padx=6, pady=5)
            tk.Label(cell, text=name, bg="white", fg="#374151", font=("Arial", 9, "bold")).pack(anchor="w")
            if name == "Category":
                w = ttk.Combobox(cell, textvariable=self.asset_vars[name],
                                 values=["IT Equipment", "Furniture", "Laboratory Equipment",
                                         "Electrical Equipment", "Office Equipment", "Other Assets"],
                                 state="readonly", width=23)
            elif name == "Status":
                w = ttk.Combobox(cell, textvariable=self.asset_vars[name],
                                 values=["Available", "Assigned", "Under Maintenance", "Damaged"],
                                 state="readonly", width=23)
            else:
                w = tk.Entry(cell, textvariable=self.asset_vars[name], width=26)
            w.pack(fill="x", pady=(3,0))
        for c in range(4):
            form.grid_columnconfigure(c, weight=1)
        actions = tk.Frame(form, bg="white")
        actions.grid(row=2, column=0, columnspan=4, sticky="w", padx=6, pady=8)
        tk.Button(actions, text="Add Asset", command=self.add_asset, bg="#2563eb", fg="white", relief="flat", padx=15, pady=7).pack(side="left", padx=(0,7))
        tk.Button(actions, text="Update Selected", command=self.update_asset, bg="#0f766e", fg="white", relief="flat", padx=15, pady=7).pack(side="left", padx=7)
        tk.Button(actions, text="Delete Selected", command=self.delete_asset, bg="#b91c1c", fg="white", relief="flat", padx=15, pady=7).pack(side="left", padx=7)
        tk.Button(actions, text="Clear Form", command=self.clear_asset_form, relief="flat", padx=15, pady=7).pack(side="left", padx=7)

        searchrow = tk.Frame(self.content, bg="#f3f4f6")
        searchrow.pack(fill="x", padx=25, pady=5)
        self.asset_search = tk.StringVar()
        tk.Label(searchrow, text="Search:", bg="#f3f4f6").pack(side="left")
        tk.Entry(searchrow, textvariable=self.asset_search, width=35).pack(side="left", padx=8)
        tk.Button(searchrow, text="Search", command=self.refresh_assets).pack(side="left")
        tk.Button(searchrow, text="Show All", command=lambda: (self.asset_search.set(""), self.refresh_assets())).pack(side="left", padx=6)

        columns = ("id","name","category","quantity","location","status","description")
        self.asset_tree = ttk.Treeview(self.content, columns=columns, show="headings", height=12)
        headings = ["Asset ID","Asset Name","Category","Quantity","Location","Status","Description"]
        widths = [95,150,155,75,130,125,180]
        for col, label, width in zip(columns, headings, widths):
            self.asset_tree.heading(col, text=label)
            self.asset_tree.column(col, width=width, anchor="w")
        self.asset_tree.pack(fill="both", expand=True, padx=25, pady=(4,20))
        self.asset_tree.bind("<<TreeviewSelect>>", self.load_selected_asset)
        self.refresh_assets()

    def get_asset_values(self):
        v = {k: x.get().strip() for k, x in self.asset_vars.items()}
        if not v["Asset ID"] or not v["Asset Name"] or not v["Category"]:
            raise ValueError("Asset ID, Asset Name and Category are required.")
        try:
            q = int(v["Quantity"])
            if q < 1: raise ValueError
        except ValueError:
            raise ValueError("Quantity must be a whole number greater than 0.")
        return v, q

    def add_asset(self):
        try:
            v, q = self.get_asset_values()
            db.add_asset(v["Asset ID"], v["Asset Name"], v["Category"], q, v["Location"],
                         v["Status"] or "Available", v["Description"], self.current_admin)
            messagebox.showinfo("Success", "Asset added. A history record was also created.")
            self.clear_asset_form()
            self.refresh_assets()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate Asset ID", "This Asset ID already exists.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def selected_asset_id(self):
        selected = self.asset_tree.selection()
        if not selected:
            messagebox.showwarning("Select Asset", "Please select an asset from the table.")
            return None
        return self.asset_tree.item(selected[0], "values")[0]

    def update_asset(self):
        asset_id = self.selected_asset_id()
        if not asset_id: return
        try:
            v, q = self.get_asset_values()
            if v["Asset ID"] != asset_id:
                messagebox.showerror("Asset ID", "Asset ID cannot be changed during update.")
                return
            db.update_asset(asset_id, v["Asset Name"], v["Category"], q, v["Location"],
                            v["Status"] or "Available", v["Description"], self.current_admin)
            messagebox.showinfo("Updated", "Asset updated. Previous and new information were saved in History.")
            self.clear_asset_form()
            self.refresh_assets()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_asset(self):
        asset_id = self.selected_asset_id()
        if not asset_id: return
        if not messagebox.askyesno("Confirm Delete", f"Delete asset {asset_id}? Its history record will be kept."):
            return
        try:
            db.delete_asset(asset_id, self.current_admin)
            messagebox.showinfo("Deleted", "Asset deleted. A Deleted record was saved in History.")
            self.clear_asset_form()
            self.refresh_assets()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def clear_asset_form(self):
        for k, var in self.asset_vars.items():
            var.set("1" if k == "Quantity" else ("Available" if k == "Status" else ""))

    def load_selected_asset(self, _event=None):
        selected = self.asset_tree.selection()
        if not selected: return
        vals = self.asset_tree.item(selected[0], "values")
        keys = ["Asset ID","Asset Name","Category","Quantity","Location","Status","Description"]
        for key, value in zip(keys, vals):
            self.asset_vars[key].set(str(value))

    def refresh_assets(self):
        for item in self.asset_tree.get_children():
            self.asset_tree.delete(item)
        for row in db.list_assets(self.asset_search.get()):
            self.asset_tree.insert("", "end", values=row)

    def show_settings_home(self):
        # Keep the settings navigation visible while only the selected page changes.
        self.settings_mode = True
        for widget in self.content.winfo_children():
            widget.destroy()

        top = tk.Frame(self.content, bg="#f3f4f6")
        top.pack(fill="x")
        tk.Label(top, text="Settings", bg="#f3f4f6", fg="#111827",
                 font=("Arial", 20, "bold")).pack(anchor="w", padx=25, pady=(22, 3))
        tk.Label(top, text="Select a section from the left menu.",
                 bg="#f3f4f6", fg="#6b7280", font=("Arial", 10)).pack(anchor="w", padx=27, pady=(0, 15))

        body = tk.Frame(self.content, bg="#f3f4f6")
        body.pack(fill="both", expand=True, padx=18, pady=(0, 15))
        nav = tk.Frame(body, bg="#202938", width=245)
        nav.pack(side="left", fill="y", padx=(0, 12))
        nav.pack_propagate(False)
        tk.Label(nav, text="SETTINGS MENU", bg="#202938", fg="#cbd5e1",
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=15, pady=(18, 12))

        self.settings_panel = tk.Frame(body, bg="#f3f4f6")
        self.settings_panel.pack(side="right", fill="both", expand=True)

        sections = [
            ("General Settings", self.show_general),
            ("Account Settings", self.show_account),
            ("Asset Configuration History", self.show_history),
            ("Appearance Settings", self.show_appearance),
            ("Database Settings", self.show_database),
        ]
        self.settings_nav_buttons = {}
        for label, command in sections:
            btn = tk.Button(nav, text=label, command=command, anchor="w",
                            bg="#202938", fg="white", activebackground="#374151",
                            activeforeground="white", relief="flat", padx=15,
                            pady=13, font=("Arial", 9))
            btn.pack(fill="x", padx=7, pady=2)
            self.settings_nav_buttons[label] = btn

        self.show_general()

    def back_settings(self):
        # Navigation remains visible; no separate back page is needed.
        return

    def page_title(self, title, subtitle=""):
        self.heading(title, subtitle)

    def setting_form(self):
        frame = tk.Frame(self.settings_panel, bg="white", padx=20, pady=18)
        frame.pack(anchor="nw", fill="x", padx=25, pady=8)
        return frame

    def show_general(self):
        if hasattr(self, "settings_nav_buttons"):
            for nav_label, nav_button in self.settings_nav_buttons.items():
                nav_button.configure(bg="#2563eb" if nav_label == "General Settings" else "#202938")
        self.clear(); self.page_title("General Settings")
        f = self.setting_form()
        vars_ = {
            "Application Name": tk.StringVar(value=db.get_setting("application_name")),
            "Language": tk.StringVar(value=db.get_setting("language")),
            "Date Format": tk.StringVar(value=db.get_setting("date_format")),
            "Default Dashboard": tk.StringVar(value=db.get_setting("default_dashboard")),
        }
        opts = {
            "Language": ["English", "Bangla"],
            "Date Format": ["DD-MM-YYYY", "MM-DD-YYYY", "YYYY-MM-DD"],
            "Default Dashboard": ["Dashboard", "Asset Management"],
        }
        for i, (label, var) in enumerate(vars_.items()):
            tk.Label(f, text=label, bg="white").grid(row=i, column=0, sticky="w", pady=7)
            if label in opts:
                ttk.Combobox(f, textvariable=var, values=opts[label], state="readonly", width=35).grid(row=i, column=1, sticky="w", padx=12)
            else:
                tk.Entry(f, textvariable=var, width=38).grid(row=i, column=1, sticky="w", padx=12)
        def save():
            for label, var in vars_.items():
                key = label.lower().replace(" ", "_")
                db.save_setting(key, var.get())
            self.title(vars_["Application Name"].get())
            messagebox.showinfo("Saved", "General settings saved.")
        tk.Button(f, text="Save Changes", command=save, bg="#2563eb", fg="white", relief="flat", padx=15, pady=7).grid(row=4, column=1, sticky="w", pady=12)

    def show_account(self):
        if hasattr(self, "settings_nav_buttons"):
            for nav_label, nav_button in self.settings_nav_buttons.items():
                nav_button.configure(bg="#2563eb" if nav_label == "Account Settings" else "#202938")
        self.clear(); self.page_title("Account Settings")
        f = self.setting_form()
        admin = db.get_admin()
        name_var, user_var = tk.StringVar(value=admin[0]), tk.StringVar(value=admin[1])
        old_var, new_var, confirm_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for i, (label, var) in enumerate([("Admin Name",name_var),("Username",user_var)]):
            tk.Label(f, text=label, bg="white").grid(row=i,column=0,sticky="w",pady=7)
            tk.Entry(f,textvariable=var,width=35).grid(row=i,column=1,padx=10,sticky="w")
        tk.Label(f,text="Current Password (if already set)",bg="white").grid(row=2,column=0,sticky="w",pady=7)
        tk.Entry(f,textvariable=old_var,show="*",width=35).grid(row=2,column=1,padx=10,sticky="w")
        tk.Label(f,text="New Password",bg="white").grid(row=3,column=0,sticky="w",pady=7)
        tk.Entry(f,textvariable=new_var,show="*",width=35).grid(row=3,column=1,padx=10,sticky="w")
        tk.Label(f,text="Confirm New Password",bg="white").grid(row=4,column=0,sticky="w",pady=7)
        tk.Entry(f,textvariable=confirm_var,show="*",width=35).grid(row=4,column=1,padx=10,sticky="w")
        def save():
            if not name_var.get().strip() or not user_var.get().strip():
                messagebox.showerror("Required","Admin Name and Username are required."); return
            current = db.get_admin()
            if new_var.get():
                if current[2] and not db.verify_password(old_var.get()):
                    messagebox.showerror("Password","Current password is incorrect."); return
                if len(new_var.get()) < 8:
                    messagebox.showerror("Password","New password must be at least 8 characters."); return
                if new_var.get() != confirm_var.get():
                    messagebox.showerror("Password","New password and confirmation do not match."); return
            try:
                db.update_admin(name_var.get().strip(), user_var.get().strip())
                if new_var.get(): db.set_password(new_var.get())
                self.current_admin = name_var.get().strip()
                messagebox.showinfo("Saved","Account settings saved.")
                self.show_account()
            except sqlite3.IntegrityError:
                messagebox.showerror("Username","This username is already used.")
        tk.Button(f,text="Save Changes",command=save,bg="#2563eb",fg="white",relief="flat",padx=15,pady=7).grid(row=5,column=1,sticky="w",pady=12)
        tk.Label(f,text="First time? Leave Current Password blank and set a new password.",bg="white",fg="#6b7280").grid(row=6,column=0,columnspan=2,sticky="w")

    def show_history(self):
        if hasattr(self, "settings_nav_buttons"):
            for nav_label, nav_button in self.settings_nav_buttons.items():
                nav_button.configure(bg="#2563eb" if nav_label == "Asset Configuration History" else "#202938")
        self.clear(); self.page_title("Asset Configuration History", "Records are created automatically when assets are added, updated or deleted.")
        bar = tk.Frame(self.settings_panel,bg="#f3f4f6"); bar.pack(fill="x",padx=25,pady=5)
        search = tk.StringVar(); action = tk.StringVar(value="All")
        tk.Label(bar,text="Search Asset ID/Name:",bg="#f3f4f6").pack(side="left")
        tk.Entry(bar,textvariable=search,width=25).pack(side="left",padx=6)
        ttk.Combobox(bar,textvariable=action,values=["All","Added","Updated","Deleted"],state="readonly",width=14).pack(side="left",padx=6)
        columns=("record","assetid","name","action","previous","updated","by","time")
        tree=ttk.Treeview(self.settings_panel,columns=columns,show="headings",height=17)
        titles=["Record","Asset ID","Asset Name","Action","Previous Information","Updated Information","Performed By","Date & Time"]
        widths=[60,90,120,80,210,210,100,145]
        for c,t,w in zip(columns,titles,widths):
            tree.heading(c,text=t); tree.column(c,width=w,anchor="w")
        tree.pack(fill="both",expand=True,padx=25,pady=8)
        def refresh():
            for item in tree.get_children(): tree.delete(item)
            for row in db.list_history(search.get().strip(),action.get()):
                tree.insert("","end",values=row)
        def delete_selected():
            sel=tree.selection()
            if not sel:
                messagebox.showwarning("Select Record","Select a history record first."); return
            rid=tree.item(sel[0],"values")[0]
            if messagebox.askyesno("Confirm Permanent Delete","Permanently delete this history record? The actual asset will not be affected."):
                db.delete_history(rid); refresh()
        buttons=tk.Frame(self.settings_panel,bg="#f3f4f6"); buttons.pack(anchor="w",padx=25,pady=(0,15))
        tk.Button(bar,text="Search / Filter",command=refresh).pack(side="left",padx=6)
        tk.Button(bar,text="Show All",command=lambda:(search.set(""),action.set("All"),refresh())).pack(side="left")
        tk.Button(buttons,text="Permanent Delete Selected",command=delete_selected,bg="#b91c1c",fg="white",relief="flat",padx=12,pady=6).pack(side="left")
        refresh()

    def show_appearance(self):
        if hasattr(self, "settings_nav_buttons"):
            for nav_label, nav_button in self.settings_nav_buttons.items():
                nav_button.configure(bg="#2563eb" if nav_label == "Appearance Settings" else "#202938")
        self.clear(); self.page_title("Appearance Settings")
        f=self.setting_form()
        theme=tk.StringVar(value=db.get_setting("theme","Light"))
        font=tk.StringVar(value=db.get_setting("font_size","10"))
        tk.Label(f,text="Theme",bg="white").grid(row=0,column=0,sticky="w",pady=8)
        ttk.Combobox(f,textvariable=theme,values=["Light","Dark"],state="readonly",width=30).grid(row=0,column=1,padx=10,sticky="w")
        tk.Label(f,text="Font Size",bg="white").grid(row=1,column=0,sticky="w",pady=8)
        ttk.Combobox(f,textvariable=font,values=["9","10","11","12","14","16"],state="readonly",width=30).grid(row=1,column=1,padx=10,sticky="w")
        def save():
            db.save_setting("theme",theme.get()); db.save_setting("font_size",font.get())
            messagebox.showinfo("Saved","Appearance preferences saved. Restart the app to apply consistently.")
        tk.Button(f,text="Save Changes",command=save,bg="#2563eb",fg="white",relief="flat",padx=15,pady=7).grid(row=2,column=1,sticky="w",pady=12)

    def show_database(self):
        if hasattr(self, "settings_nav_buttons"):
            for nav_label, nav_button in self.settings_nav_buttons.items():
                nav_button.configure(bg="#2563eb" if nav_label == "Database Settings" else "#202938")
        self.clear(); self.page_title("Database Settings")
        f=self.setting_form()
        tk.Label(f,text="Database Location",bg="white").grid(row=0,column=0,sticky="w",pady=7)
        tk.Label(f,text=db.DB_PATH,bg="white",wraplength=650,justify="left").grid(row=0,column=1,sticky="w",padx=10)
        def connection():
            try:
                with db.connect_db() as con: con.execute("SELECT 1")
                messagebox.showinfo("Connection Status","Database connection is working.")
            except Exception as e: messagebox.showerror("Connection Error",str(e))
        def backup():
            path=filedialog.asksaveasfilename(defaultextension=".db",filetypes=[("SQLite Database","*.db")],initialfile="bubt_ops_backup.db")
            if not path:return
            try:
                src=sqlite3.connect(db.DB_PATH); dest=sqlite3.connect(path)
                src.backup(dest); dest.close(); src.close()
                with db.connect_db() as con:
                    con.execute("INSERT INTO backup_history(file_path,backup_time) VALUES (?,?)",(path,datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                messagebox.showinfo("Backup","Database backup created successfully.")
            except Exception as e: messagebox.showerror("Backup Error",str(e))
        def restore():
            path=filedialog.askopenfilename(filetypes=[("SQLite Database","*.db"),("All Files","*.*")])
            if not path:return
            if os.path.abspath(path)==os.path.abspath(db.DB_PATH):
                messagebox.showerror("Restore","Choose a backup file, not the current database.");return
            try:
                test=sqlite3.connect(f"file:{os.path.abspath(path)}?mode=ro",uri=True)
                tables={r[0] for r in test.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                test.close()
                if not {"assets","app_settings","admin","asset_history"}.issubset(tables):
                    messagebox.showerror("Invalid Backup","This file is not a valid BUBT-OPS database backup.");return
                if not messagebox.askyesno("Confirm Restore","Restore will replace the current database. Make a backup first. Continue?"):return
                source=sqlite3.connect(path); target=sqlite3.connect(db.DB_PATH)
                source.backup(target); target.close(); source.close()
                messagebox.showinfo("Restore Complete","Database restored. Please restart BUBT-OPS.")
            except Exception as e:messagebox.showerror("Restore Error",str(e))
        tk.Button(f,text="Check Connection",command=connection).grid(row=1,column=0,sticky="w",pady=8)
        tk.Button(f,text="Backup Database",command=backup).grid(row=1,column=1,sticky="w",padx=10,pady=8)
        tk.Button(f,text="Restore Database",command=restore).grid(row=2,column=1,sticky="w",padx=10,pady=8)
        tk.Label(f,text="Backup History",bg="white",font=("Arial",11,"bold")).grid(row=3,column=0,sticky="w",pady=(18,5))
        history_frame=tk.Frame(f,bg="white");history_frame.grid(row=4,column=0,columnspan=2,sticky="ew")
        cols=("file","time")
        tree=ttk.Treeview(history_frame,columns=cols,show="headings",height=6)
        tree.heading("file",text="Backup File");tree.heading("time",text="Backup Date & Time")
        tree.column("file",width=430);tree.column("time",width=180)
        tree.pack(fill="x")
        def load_history(days=None):
            for item in tree.get_children():tree.delete(item)
            with db.connect_db() as con:
                if days:
                    cutoff=(datetime.now()-timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                    rows=con.execute("SELECT file_path,backup_time FROM backup_history WHERE backup_time>=? ORDER BY id DESC",(cutoff,)).fetchall()
                else: rows=con.execute("SELECT file_path,backup_time FROM backup_history ORDER BY id DESC").fetchall()
            for row in rows:tree.insert("","end",values=row)
        buttons=tk.Frame(f,bg="white");buttons.grid(row=5,column=0,columnspan=2,sticky="w",pady=8)
        tk.Button(buttons,text="View All History",command=lambda:load_history()).pack(side="left",padx=(0,6))
        tk.Button(buttons,text="Last 30 Days",command=lambda:load_history(30)).pack(side="left")
        load_history()

    def show_about(self):
        self.settings_mode = False
        self.clear(); self.heading("About Application")
        f=self.setting_form()
        info=[
            ("Application Name","BUBT-OPS"),("Version","1.0"),
            ("Application Type","Offline Desktop Application"),
            ("Programming Language","Python"),("GUI Framework","Tkinter"),
            ("Database","SQLite"),("Developed By","Team Name"),
            ("Purpose","University Asset Management"),
        ]
        for i,(a,b) in enumerate(info):
            tk.Label(f,text=a,bg="white",font=("Arial",10,"bold")).grid(row=i,column=0,sticky="w",pady=7)
            tk.Label(f,text=b,bg="white").grid(row=i,column=1,sticky="w",padx=18)

if __name__ == "__main__":
    app=BUBTOPS()
    app.mainloop()
