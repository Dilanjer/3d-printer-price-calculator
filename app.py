import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

PROFILES_FILE = "profiles.json"
SETTINGS_FILE = "settings.json"

class PrinterProfile:
    def __init__(self, name, power=0.0, amortization=0.0):
        self.name = name
        self.power = power
        self.amortization = amortization

    def to_dict(self):
        return {
            "name": self.name,
            "power": self.power,
            "amortization": self.amortization
        }

    @staticmethod
    def from_dict(d):
        return PrinterProfile(
            d.get("name", ""),
            float(d.get("power", 0.0)),
            float(d.get("amortization", 0.0))
        )

class PlasticProfile:
    def __init__(self, name, plastic_cost=0.0):
        self.name = name
        self.plastic_cost = plastic_cost

    def to_dict(self):
        return {
            "name": self.name,
            "plastic_cost": self.plastic_cost
        }

    @staticmethod
    def from_dict(d):
        return PlasticProfile(
            d.get("name", ""),
            float(d.get("plastic_cost", 0.0))
        )

class Settings:
    def __init__(self):
        self.electricity_cost_default = 0.0
        self.margin_default = 0.0
        self.profiles_path = PROFILES_FILE

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.electricity_cost_default = float(data.get("electricity_cost_default", 0.0))
                    self.margin_default = float(data.get("margin_default", 0.0))
                    self.profiles_path = data.get("profiles_path", PROFILES_FILE)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load settings:\n{e}")

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "electricity_cost_default": self.electricity_cost_default,
                    "margin_default": self.margin_default,
                    "profiles_path": self.profiles_path
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")

class CenteredToplevel(tk.Toplevel):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.withdraw()
        self.transient(master)
        self.grab_set()
        self.after(0, self._center_and_show)

    def _center_and_show(self):
        self.update_idletasks()
        if self.master is not None:
            master_x = self.master.winfo_rootx()
            master_y = self.master.winfo_rooty()
            master_width = self.master.winfo_width()
            master_height = self.master.winfo_height()
            win_width = self.winfo_width()
            win_height = self.winfo_height()
            x = master_x + (master_width - win_width) // 2
            y = master_y + (master_height - win_height) // 2
            self.geometry(f"+{x}+{y}")
        self.deiconify()

class ProfileWindow(CenteredToplevel):
    def __init__(self, master, profile_type, profile=None, settings=None):
        super().__init__(master)
        self.profile_type = profile_type
        self.profile = profile
        self.settings = settings
        self.result_profile = None

        self.title(f"{'Edit' if profile else 'Create'} {profile_type.capitalize()} Profile")
        self.geometry("350x180")
        self.resizable(False, False)

        self._create_widgets()
        self._populate_fields()

    def _create_widgets(self):
        frm = ttk.Frame(self)
        frm.pack(padx=15, pady=15, fill="both", expand=True)

        if self.profile_type == "printer":
            labels = [
                ("Printer Name:", "name"),
                ("Power (W):", "power"),
                ("Amortization (price/hour):", "amortization")
            ]
        else:
            labels = [
                ("Plastic Name:", "name"),
                ("Plastic Cost (price/kg):", "plastic_cost")
            ]

        self.entries = {}
        for i, (label_text, key) in enumerate(labels):
            lbl = ttk.Label(frm, text=label_text)
            lbl.grid(row=i, column=0, sticky="w", pady=5)
            ent = ttk.Entry(frm)
            ent.grid(row=i, column=1, sticky="ew", pady=5)
            self.entries[key] = ent
        frm.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10, fill="x")

        btn_save = ttk.Button(btn_frame, text="Save", command=self._on_save)
        btn_save.pack(side="right", padx=5)
        btn_cancel = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        btn_cancel.pack(side="right")

    def _populate_fields(self):
        if self.profile:
            if self.profile_type == "printer":
                self.entries["name"].insert(0, self.profile.name)
                self.entries["power"].insert(0, str(self.profile.power))
                self.entries["amortization"].insert(0, str(self.profile.amortization))
            else:
                self.entries["name"].insert(0, self.profile.name)
                self.entries["plastic_cost"].insert(0, str(self.profile.plastic_cost))
        else:
            if self.profile_type == "printer":
                self.entries["name"].insert(0, "")
                self.entries["power"].insert(0, "0")
                self.entries["amortization"].insert(0, "0")
            else:
                self.entries["name"].insert(0, "")
                self.entries["plastic_cost"].insert(0, "0")

    def _on_save(self):
        name = self.entries["name"].get().strip()
        if not name:
            messagebox.showwarning("Warning", "Please enter a name.")
            return
        try:
            if self.profile_type == "printer":
                power = float(self.entries["power"].get().replace(",", "."))
                amortization = float(self.entries["amortization"].get().replace(",", "."))
                self.result_profile = PrinterProfile(name, power, amortization)
            else:
                plastic_cost = float(self.entries["plastic_cost"].get().replace(",", "."))
                self.result_profile = PlasticProfile(name, plastic_cost)
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values.")
            return
        self.destroy()

class SettingsWindow(CenteredToplevel):
    def __init__(self, master, settings):
        super().__init__(master)
        self.settings = settings
        self.title("Default Settings")
        self.geometry("400x180")
        self.resizable(False, False)

        self._create_widgets()
        self._populate_fields()

    def _create_widgets(self):
        frm = ttk.Frame(self)
        frm.pack(padx=15, pady=15, fill="both", expand=True)

        labels = [
            ("Electricity Cost (price/kWh):", "electricity_cost_default"),
            ("Margin (%):", "margin_default"),
            ("Profiles File Path:", "profiles_path")
        ]

        self.entries = {}
        for i, (label_text, key) in enumerate(labels):
            lbl = ttk.Label(frm, text=label_text)
            lbl.grid(row=i, column=0, sticky="w", pady=5)
            ent = ttk.Entry(frm)
            ent.grid(row=i, column=1, sticky="ew", pady=5)
            self.entries[key] = ent
        frm.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10, fill="x")

        btn_browse = ttk.Button(btn_frame, text="Browse...", command=self._browse_profiles_path)
        btn_browse.pack(side="left")

        btn_save = ttk.Button(btn_frame, text="Save", command=self._on_save)
        btn_save.pack(side="right", padx=5)
        btn_cancel = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        btn_cancel.pack(side="right")

    def _browse_profiles_path(self):
        path = filedialog.asksaveasfilename(
            title="Select Profiles File",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            self.entries["profiles_path"].delete(0, tk.END)
            self.entries["profiles_path"].insert(0, path)

    def _populate_fields(self):
        self.entries["electricity_cost_default"].delete(0, tk.END)
        self.entries["electricity_cost_default"].insert(0, str(self.settings.electricity_cost_default))

        self.entries["margin_default"].delete(0, tk.END)
        self.entries["margin_default"].insert(0, str(self.settings.margin_default))

        self.entries["profiles_path"].delete(0, tk.END)
        self.entries["profiles_path"].insert(0, self.settings.profiles_path)

    def _on_save(self):
        try:
            electricity_cost = float(self.entries["electricity_cost_default"].get().replace(",", ".").strip())
            margin = float(self.entries["margin_default"].get().replace(",", ".").strip())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values.")
            return

        profiles_path = self.entries["profiles_path"].get().strip()
        if not profiles_path:
            messagebox.showerror("Error", "Profiles file path cannot be empty.")
            return

        self.settings.electricity_cost_default = electricity_cost
        self.settings.margin_default = margin
        self.settings.profiles_path = profiles_path
        self.settings.save()
        self.destroy()

def custom_round(value: float) -> int:
    remainder = value % 100
    base = value - remainder
    # Round to 50 if remainder < 25, else to 100
    if remainder < 25:
        return int(base + 50)
    else:
        return int(base + 100)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("3D Printing Cost Calculator")
        self.geometry("600x600")
        self.resizable(False, False)

        self.settings = Settings()
        self.settings.load()

        # Проверяем наличие файла профилей, если нет - запрашиваем путь
        if not os.path.exists(self.settings.profiles_path):
            self._ask_profiles_path()

        self.printers = []
        self.plastics = []

        self.current_printer = None
        self.current_plastic = None

        self._create_widgets()
        self._load_profiles()
        self._apply_defaults_to_inputs()

    def _ask_profiles_path(self):
        messagebox.showinfo("Profiles file not found",
                            "Profiles file not found.\nPlease select where to save your profiles.")
        path = filedialog.asksaveasfilename(
            title="Select Profiles File",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            self.settings.profiles_path = path
            self.settings.save()
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"printers": [], "plastics": []}, f, ensure_ascii=False, indent=4)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create profiles file:\n{e}")
                self.destroy()
        else:
            messagebox.showwarning("No file selected", "No profiles file selected. The app will exit.")
            self.destroy()

    def _create_widgets(self):
        menubar = tk.Menu(self)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Default Settings...", command=self._open_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="Import Profiles...", command=self._import_profiles)
        settings_menu.add_command(label="Export Profiles As...", command=self._export_profiles)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        self.config(menu=menubar)

        # Printer profiles frame
        frame_printers = ttk.LabelFrame(self, text="3D Printer Profiles")
        frame_printers.pack(padx=10, pady=5, fill="x")

        self.printer_combo = ttk.Combobox(frame_printers, state="readonly")
        self.printer_combo.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.printer_combo.bind("<<ComboboxSelected>>", self._on_printer_selected)

        ttk.Button(frame_printers, text="New", command=self._create_printer).pack(side="left", padx=3)
        ttk.Button(frame_printers, text="Edit", command=self._edit_printer).pack(side="left", padx=3)
        ttk.Button(frame_printers, text="Delete", command=self._delete_printer).pack(side="left", padx=3)

        # Plastic profiles frame
        frame_plastics = ttk.LabelFrame(self, text="Plastic Profiles")
        frame_plastics.pack(padx=10, pady=5, fill="x")

        self.plastic_combo = ttk.Combobox(frame_plastics, state="readonly")
        self.plastic_combo.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.plastic_combo.bind("<<ComboboxSelected>>", self._on_plastic_selected)

        ttk.Button(frame_plastics, text="New", command=self._create_plastic).pack(side="left", padx=3)
        ttk.Button(frame_plastics, text="Edit", command=self._edit_plastic).pack(side="left", padx=3)
        ttk.Button(frame_plastics, text="Delete", command=self._delete_plastic).pack(side="left", padx=3)

        # Default settings display (read-only)
        frame_defaults = ttk.LabelFrame(self, text="Default Settings (Read Only)")
        frame_defaults.pack(padx=10, pady=10, fill="x")

        self.label_elec_cost = ttk.Label(frame_defaults, text=f"Electricity Cost (price/kWh): {self.settings.electricity_cost_default}")
        self.label_elec_cost.pack(anchor="w", padx=10, pady=2)

        self.label_margin = ttk.Label(frame_defaults, text=f"Margin (%): {self.settings.margin_default}")
        self.label_margin.pack(anchor="w", padx=10, pady=2)

        # Input for calculation
        frame_input = ttk.LabelFrame(self, text="Input Data for Calculation")
        frame_input.pack(padx=10, pady=10, fill="x")

        self.entries_input = {}

        input_labels = [
            ("Weight (grams):", "weight"),
            ("Print Time (hours):", "time"),
            ("Additional Costs (price):", "extra")
        ]

        for i, (label_text, key) in enumerate(input_labels):
            lbl = ttk.Label(frame_input, text=label_text)
            lbl.grid(row=i, column=0, sticky="w", padx=5, pady=5)
            ent = ttk.Entry(frame_input)
            ent.grid(row=i, column=1, sticky="ew", padx=5, pady=5)
            self.entries_input[key] = ent
        frame_input.columnconfigure(1, weight=1)

        self.entries_input["extra"].insert(0, "0")

        # Checkbox for rounding final price
        self.round_var = tk.BooleanVar(value=False)
        chk_round = ttk.Checkbutton(self, text="Round final price", variable=self.round_var)
        chk_round.pack(pady=5)

        ttk.Button(self, text="Calculate Cost", command=self._calculate).pack(pady=10)

        # Result display
        frame_result = ttk.LabelFrame(self, text="Results")
        frame_result.pack(padx=10, pady=10, fill="both", expand=True)

        self.result_text = tk.Text(frame_result, height=10, state="disabled")
        self.result_text.pack(fill="both", expand=True, padx=5, pady=5)

    def _load_profiles(self):
        path = self.settings.profiles_path
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.printers = [PrinterProfile.from_dict(d) for d in data.get("printers", [])]
                self.plastics = [PlasticProfile.from_dict(d) for d in data.get("plastics", [])]
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load profiles:\n{e}")
                self.printers = []
                self.plastics = []
        else:
            self.printers = []
            self.plastics = []
        self._refresh_printer_combo()
        self._refresh_plastic_combo()

    def _save_profiles(self):
        path = self.settings.profiles_path
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "printers": [p.to_dict() for p in self.printers],
                    "plastics": [p.to_dict() for p in self.plastics]
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profiles:\n{e}")

    def _refresh_printer_combo(self):
        names = [p.name for p in self.printers]
        self.printer_combo["values"] = names
        if names:
            self.printer_combo.current(0)
            self._on_printer_selected()
        else:
            self.printer_combo.set("")
            self.current_printer = None

    def _on_printer_selected(self, event=None):
        idx = self.printer_combo.current()
        if 0 <= idx < len(self.printers):
            self.current_printer = self.printers[idx]

    def _create_printer(self):
        wnd = ProfileWindow(self, "printer", settings=self.settings)
        self.wait_window(wnd)
        if wnd.result_profile:
            if any(p.name == wnd.result_profile.name for p in self.printers):
                messagebox.showerror("Error", "Profile with this name already exists.")
                return
            self.printers.append(wnd.result_profile)
            self._save_profiles()
            self._refresh_printer_combo()
            self.printer_combo.set(wnd.result_profile.name)
            self._on_printer_selected()

    def _edit_printer(self):
        idx = self.printer_combo.current()
        if idx == -1:
            messagebox.showwarning("Warning", "No printer selected.")
            return
        profile = self.printers[idx]
        wnd = ProfileWindow(self, "printer", profile, settings=self.settings)
        self.wait_window(wnd)
        if wnd.result_profile:
            # Проверка на дублирование имени кроме самого редактируемого
            if any(p.name == wnd.result_profile.name and p != profile for p in self.printers):
                messagebox.showerror("Error", "Profile with this name already exists.")
                return
            self.printers[idx] = wnd.result_profile
            self._save_profiles()
            self._refresh_printer_combo()
            self.printer_combo.set(wnd.result_profile.name)
            self._on_printer_selected()

    def _delete_printer(self):
        idx = self.printer_combo.current()
        if idx == -1:
            messagebox.showwarning("Warning", "No printer selected.")
            return
        answer = messagebox.askyesno("Confirm", "Delete selected printer profile?")
        if answer:
            del self.printers[idx]
            self._save_profiles()
            self._refresh_printer_combo()

    def _refresh_plastic_combo(self):
        names = [p.name for p in self.plastics]
        self.plastic_combo["values"] = names
        if names:
            self.plastic_combo.current(0)
            self._on_plastic_selected()
        else:
            self.plastic_combo.set("")
            self.current_plastic = None

    def _on_plastic_selected(self, event=None):
        idx = self.plastic_combo.current()
        if 0 <= idx < len(self.plastics):
            self.current_plastic = self.plastics[idx]

    def _create_plastic(self):
        wnd = ProfileWindow(self, "plastic", settings=self.settings)
        self.wait_window(wnd)
        if wnd.result_profile:
            if any(p.name == wnd.result_profile.name for p in self.plastics):
                messagebox.showerror("Error", "Profile with this name already exists.")
                return
            self.plastics.append(wnd.result_profile)
            self._save_profiles()
            self._refresh_plastic_combo()
            self.plastic_combo.set(wnd.result_profile.name)
            self._on_plastic_selected()

    def _edit_plastic(self):
        idx = self.plastic_combo.current()
        if idx == -1:
            messagebox.showwarning("Warning", "No plastic selected.")
            return
        profile = self.plastics[idx]
        wnd = ProfileWindow(self, "plastic", profile, settings=self.settings)
        self.wait_window(wnd)
        if wnd.result_profile:
            if any(p.name == wnd.result_profile.name and p != profile for p in self.plastics):
                messagebox.showerror("Error", "Profile with this name already exists.")
                return
            self.plastics[idx] = wnd.result_profile
            self._save_profiles()
            self._refresh_plastic_combo()
            self.plastic_combo.set(wnd.result_profile.name)
            self._on_plastic_selected()

    def _delete_plastic(self):
        idx = self.plastic_combo.current()
        if idx == -1:
            messagebox.showwarning("Warning", "No plastic selected.")
            return
        answer = messagebox.askyesno("Confirm", "Delete selected plastic profile?")
        if answer:
            del self.plastics[idx]
            self._save_profiles()
            self._refresh_plastic_combo()

    def _apply_defaults_to_inputs(self):
        # Можно сюда вставить, если хочешь подставлять значения по умолчанию в поля ввода
        pass

    def _calculate(self):
        if self.current_printer is None:
            messagebox.showwarning("Warning", "Select a printer profile first.")
            return
        if self.current_plastic is None:
            messagebox.showwarning("Warning", "Select a plastic profile first.")
            return
        try:
            weight = float(self.entries_input["weight"].get().replace(",", "."))
            time = float(self.entries_input["time"].get().replace(",", "."))
            extra = float(self.entries_input["extra"].get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric input.")
            return

        # Расчёты
        power_kw = self.current_printer.power / 1000.0
        elec_cost = self.settings.electricity_cost_default
        margin = self.settings.margin_default / 100.0

        amort = self.current_printer.amortization * time
        elec = power_kw * time * elec_cost
        plastic_cost = (weight / 1000.0) * self.current_plastic.plastic_cost
        base_price = amort + elec + plastic_cost + extra
        price_with_margin = base_price * (1 + margin)

        if self.round_var.get():
            final_price = custom_round(price_with_margin)
        else:
            final_price = round(price_with_margin, 2)

        result = (
            f"Calculation Results:\n"
            f"Printer: {self.current_printer.name}\n"
            f"Plastic: {self.current_plastic.name}\n\n"
            f"Weight: {weight} g\n"
            f"Print Time: {time} h\n"
            f"Additional Costs: {extra}\n\n"
            f"Amortization Cost: {amort:.2f}\n"
            f"Electricity Cost: {elec:.2f}\n"
            f"Plastic Cost: {plastic_cost:.2f}\n"
            f"Base Price (sum): {base_price:.2f}\n"
            f"Price with Margin ({self.settings.margin_default}%): {price_with_margin:.2f}\n"
            f"Final Price (rounded): {final_price}\n"
        )
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, result)
        self.result_text.config(state="disabled")

    def _open_settings(self):
        wnd = SettingsWindow(self, self.settings)
        self.wait_window(wnd)
        # Обновляем надписи после изменения настроек
        self.label_elec_cost.config(text=f"Electricity Cost (price/kWh): {self.settings.electricity_cost_default}")
        self.label_margin.config(text=f"Margin (%): {self.settings.margin_default}")
        # Перезагружаем профили если путь изменился
        self._load_profiles()

    def _import_profiles(self):
        path = filedialog.askopenfilename(
            title="Import Profiles JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            imported_printers = [PrinterProfile.from_dict(d) for d in data.get("printers", [])]
            imported_plastics = [PlasticProfile.from_dict(d) for d in data.get("plastics", [])]

            # Можно добавить логику слияния или перезаписи. Сейчас просто добавляем, если нет дубликатов
            for p in imported_printers:
                if not any(existing.name == p.name for existing in self.printers):
                    self.printers.append(p)
            for p in imported_plastics:
                if not any(existing.name == p.name for existing in self.plastics):
                    self.plastics.append(p)

            self._save_profiles()
            self._refresh_printer_combo()
            self._refresh_plastic_combo()
            messagebox.showinfo("Import", "Profiles imported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import profiles:\n{e}")

    def _export_profiles(self):
        path = filedialog.asksaveasfilename(
            title="Export Profiles As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "printers": [p.to_dict() for p in self.printers],
                    "plastics": [p.to_dict() for p in self.plastics]
                }, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Export", "Profiles exported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export profiles:\n{e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
