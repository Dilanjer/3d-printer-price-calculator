import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

# Default config setup
DEFAULT_CONFIG_DIR = "3d-print-price-config"
CONFIG_FILE = "config.json"

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
        self.last_selected_printer = ""
        self.last_selected_plastic = ""
        self.config_dir = self._get_config_directory()
        self.config_file_path = os.path.join(self.config_dir, CONFIG_FILE)

    def _get_config_directory(self):
        """Get the configuration directory, preferring Documents folder"""
        # Try Documents folder first
        try:
            documents_path = os.path.expanduser("~/Documents")
            if os.path.exists(documents_path) and os.access(documents_path, os.W_OK):
                config_dir = os.path.join(documents_path, DEFAULT_CONFIG_DIR)
                return config_dir
        except Exception:
            pass
        
        # Fallback to current working directory if Documents is not accessible
        config_dir = os.path.join(os.getcwd(), DEFAULT_CONFIG_DIR)
        return config_dir

    def ensure_config_dir_exists(self):
        """Create config directory if it doesn't exist"""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create config directory:\n{e}")
            return False

    def find_existing_config(self):
        """Try to find existing config file in various locations"""
        # List of potential locations to check
        search_paths = [
            # Current config path (Documents or current dir)
            self.config_file_path,
            # Documents location (in case current detection failed)
            os.path.join(os.path.expanduser("~/Documents"), DEFAULT_CONFIG_DIR, CONFIG_FILE),
            # Current directory location
            os.path.join(os.getcwd(), DEFAULT_CONFIG_DIR, CONFIG_FILE),
            # Desktop location (legacy)
            os.path.join(os.path.expanduser("~/Desktop"), DEFAULT_CONFIG_DIR, CONFIG_FILE),
            # User home directory (legacy)
            os.path.join(os.path.expanduser("~"), DEFAULT_CONFIG_DIR, CONFIG_FILE),
        ]
        
        for config_path in search_paths:
            if os.path.exists(config_path):
                # Found existing config, update our paths to match
                self.config_dir = os.path.dirname(config_path)
                self.config_file_path = config_path
                return True
        return False

    def load(self):
        # First try to find existing config
        config_found = self.find_existing_config()
        
        if config_found and os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.electricity_cost_default = float(data.get("electricity_cost_default", 0.0))
                    self.margin_default = float(data.get("margin_default", 0.0))
                    self.last_selected_printer = data.get("last_selected_printer", "")
                    self.last_selected_plastic = data.get("last_selected_plastic", "")
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load settings:\n{e}")
                return False
        return False

    def save(self, printers=None, plastics=None):
        try:
            if not self.ensure_config_dir_exists():
                return
            
            data = {
                "electricity_cost_default": self.electricity_cost_default,
                "margin_default": self.margin_default,
                "last_selected_printer": self.last_selected_printer,
                "last_selected_plastic": self.last_selected_plastic,
                "printers": [p.to_dict() for p in (printers or [])],
                "plastics": [p.to_dict() for p in (plastics or [])]
            }
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}")

    def load_profiles(self):
        """Load printer and plastic profiles from config file"""
        printers = []
        plastics = []
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    printers = [PrinterProfile.from_dict(d) for d in data.get("printers", [])]
                    plastics = [PlasticProfile.from_dict(d) for d in data.get("plastics", [])]
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load profiles:\n{e}")
        return printers, plastics

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
        self.geometry("450x180")
        self.resizable(False, False)

        self._create_widgets()
        self._populate_fields()

    def _create_widgets(self):
        frm = ttk.Frame(self)
        frm.pack(padx=15, pady=15, fill="both", expand=True)

        labels = [
            ("Electricity Cost (price/kWh):", "electricity_cost_default"),
            ("Margin (%):", "margin_default")
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
        self.entries["electricity_cost_default"].delete(0, tk.END)
        self.entries["electricity_cost_default"].insert(0, str(self.settings.electricity_cost_default))

        self.entries["margin_default"].delete(0, tk.END)
        self.entries["margin_default"].insert(0, str(self.settings.margin_default))

    def _on_save(self):
        try:
            electricity_cost = float(self.entries["electricity_cost_default"].get().replace(",", ".").strip())
            margin = float(self.entries["margin_default"].get().replace(",", ".").strip())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values.")
            return

        self.settings.electricity_cost_default = electricity_cost
        self.settings.margin_default = margin
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
        self.title("3DPrintPrice")
        self.geometry("600x750")
        self.resizable(False, False)

        self.settings = Settings()
        
        # Try to load existing configuration
        config_loaded = self.settings.load()
        
        # If no configuration was found, create initial setup
        if not config_loaded:
            self._setup_initial_config()

        self.printers = []
        self.plastics = []

        self.current_printer = None
        self.current_plastic = None

        self._create_widgets()
        self._load_profiles()
        self._apply_defaults_to_inputs()
        
        # Register cleanup on window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_initial_config(self):
        """Setup initial configuration on first run"""
        try:
            if self.settings.ensure_config_dir_exists():
                # Create initial config file
                self.settings.save([], [])
                messagebox.showinfo("First Run Setup", 
                                  f"Configuration folder created at:\n{self.settings.config_dir}")
            else:
                # If we can't create config directory, show error and exit
                messagebox.showerror("Error", "Failed to create configuration directory. The application will close.")
                self.destroy()
                return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to setup initial configuration:\n{e}")
            self.destroy()

    def _create_widgets(self):
        menubar = tk.Menu(self)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Default Settings...", command=self._open_settings)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        
        # Config menu
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="Import Config...", command=self._import_config)
        config_menu.add_command(label="Export Config As...", command=self._export_config)
        menubar.add_cascade(label="Config", menu=config_menu)
        
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

        self.label_config_path = ttk.Label(frame_defaults, text=f"Config Path: {self.settings.config_dir}")
        self.label_config_path.pack(anchor="w", padx=10, pady=2)

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

        self.result_text = tk.Text(frame_result, height=15, state="disabled")
        self.result_text.pack(fill="both", expand=True, padx=5, pady=5)

    def _load_profiles(self):
        self.printers, self.plastics = self.settings.load_profiles()
        self._refresh_printer_combo()
        self._refresh_plastic_combo()

    def _save_profiles(self):
        # Update the last selected profiles before saving
        self._update_last_selected()
        self.settings.save(self.printers, self.plastics)

    def _update_last_selected(self):
        """Update the last selected printer and plastic in settings"""
        if self.current_printer:
            self.settings.last_selected_printer = self.current_printer.name
        if self.current_plastic:
            self.settings.last_selected_plastic = self.current_plastic.name

    def _refresh_printer_combo(self):
        names = [p.name for p in self.printers]
        self.printer_combo["values"] = names
        
        # Try to restore last selected printer
        if names:
            selected_idx = 0
            if self.settings.last_selected_printer:
                try:
                    selected_idx = names.index(self.settings.last_selected_printer)
                except ValueError:
                    # If last selected printer no longer exists, use first one
                    selected_idx = 0
            
            self.printer_combo.current(selected_idx)
            self._on_printer_selected()
        else:
            self.printer_combo.set("")
            self.current_printer = None

    def _on_printer_selected(self, event=None):
        idx = self.printer_combo.current()
        if 0 <= idx < len(self.printers):
            self.current_printer = self.printers[idx]
            # Save selection immediately when changed by user
            if event is not None:  # Only save if triggered by user interaction
                self._save_profiles()

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
            # Check for duplicate names except for the edited profile itself
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
            # Clear last selected if it was the deleted one
            if self.current_printer and self.current_printer.name == self.settings.last_selected_printer:
                self.settings.last_selected_printer = ""
            self._save_profiles()
            self._refresh_printer_combo()

    def _refresh_plastic_combo(self):
        names = [p.name for p in self.plastics]
        self.plastic_combo["values"] = names
        
        # Try to restore last selected plastic
        if names:
            selected_idx = 0
            if self.settings.last_selected_plastic:
                try:
                    selected_idx = names.index(self.settings.last_selected_plastic)
                except ValueError:
                    # If last selected plastic no longer exists, use first one
                    selected_idx = 0
            
            self.plastic_combo.current(selected_idx)
            self._on_plastic_selected()
        else:
            self.plastic_combo.set("")
            self.current_plastic = None

    def _on_plastic_selected(self, event=None):
        idx = self.plastic_combo.current()
        if 0 <= idx < len(self.plastics):
            self.current_plastic = self.plastics[idx]
            # Save selection immediately when changed by user
            if event is not None:  # Only save if triggered by user interaction
                self._save_profiles()

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
            # Clear last selected if it was the deleted one
            if self.current_plastic and self.current_plastic.name == self.settings.last_selected_plastic:
                self.settings.last_selected_plastic = ""
            self._save_profiles()
            self._refresh_plastic_combo()

    def _apply_defaults_to_inputs(self):
        # You can insert here if you want to populate input fields with default values
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

        # Calculations
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
        # Save the updated settings
        self._save_profiles()  # This will save with new settings
        
        # Update labels after settings change
        self.label_elec_cost.config(text=f"Electricity Cost (price/kWh): {self.settings.electricity_cost_default}")
        self.label_margin.config(text=f"Margin (%): {self.settings.margin_default}")

    def _import_config(self):
        path = filedialog.askopenfilename(
            title="Import Configuration JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=self.settings.config_dir
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Load settings
            if "electricity_cost_default" in data:
                self.settings.electricity_cost_default = float(data["electricity_cost_default"])
            if "margin_default" in data:
                self.settings.margin_default = float(data["margin_default"])
            
            # Load last selected profiles if they exist
            if "last_selected_printer" in data:
                self.settings.last_selected_printer = data["last_selected_printer"]
            if "last_selected_plastic" in data:
                self.settings.last_selected_plastic = data["last_selected_plastic"]
            
            # Load profiles
            imported_printers = [PrinterProfile.from_dict(d) for d in data.get("printers", [])]
            imported_plastics = [PlasticProfile.from_dict(d) for d in data.get("plastics", [])]

            # Add profiles if no duplicates exist
            for p in imported_printers:
                if not any(existing.name == p.name for existing in self.printers):
                    self.printers.append(p)
            for p in imported_plastics:
                if not any(existing.name == p.name for existing in self.plastics):
                    self.plastics.append(p)

            self._save_profiles()
            self._refresh_printer_combo()
            self._refresh_plastic_combo()
            
            # Update UI labels
            self.label_elec_cost.config(text=f"Electricity Cost (price/kWh): {self.settings.electricity_cost_default}")
            self.label_margin.config(text=f"Margin (%): {self.settings.margin_default}")
            
            messagebox.showinfo("Import", "Configuration imported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import configuration:\n{e}")

    def _export_config(self):
        path = filedialog.asksaveasfilename(
            title="Export Configuration As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=self.settings.config_dir
        )
        if not path:
            return
        try:
            # Ensure the directory exists before saving
            os.makedirs(os.path.dirname(path), exist_ok=True)
            # Update last selected before export
            self._update_last_selected()
            data = {
                "electricity_cost_default": self.settings.electricity_cost_default,
                "margin_default": self.settings.margin_default,
                "last_selected_printer": self.settings.last_selected_printer,
                "last_selected_plastic": self.settings.last_selected_plastic,
                "printers": [p.to_dict() for p in self.printers],
                "plastics": [p.to_dict() for p in self.plastics]
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Export", "Configuration exported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export configuration:\n{e}")

    def _on_closing(self):
        """Called when the application is closing"""
        # Save the current selections before closing
        self._save_profiles()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()