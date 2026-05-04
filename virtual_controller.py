import customtkinter as ctk
from tkinter import messagebox
import vgamepad as vg
import sys
import time

# Set Appearance and Theme
ctk.set_appearance_mode("Dark")  # Dark mode by default
ctk.set_default_color_theme("blue")  # Modern blue accent

class ControllerRow(ctk.CTkFrame):
    def __init__(self, master, index, remove_callback, controller_type="Xbox"):
        super().__init__(master, corner_radius=10)
        self.index = index
        self.remove_callback = remove_callback
        self.controller_type = controller_type
        self.gamepad = None
        self.is_connected = False

        self.pack(fill='x', padx=20, pady=10)

        # Left: Controller Info
        display_name = "Xbox 360" if self.controller_type == "Xbox" else "PS4"
        self.info_label = ctk.CTkLabel(self, text=f"🎮 {display_name} ({index + 1})", 
                                        font=("Segoe UI", 16, "bold"), width=200, anchor='w')
        self.info_label.pack(side='left', padx=20, pady=15)

        # Right: Buttons (Remove, Connect/Disconnect)
        self.btn_remove = ctk.CTkButton(self, text="Remove", width=80, height=32, 
                                        fg_color="#d32f2f", hover_color="#b71c1c",
                                        command=self.remove)
        self.btn_remove.pack(side='right', padx=(5, 20))

        self.btn_toggle = ctk.CTkButton(self, text="Connect", width=120, height=32, 
                                        fg_color="#1976D2", hover_color="#1565C0",
                                        command=self.toggle_connection)
        self.btn_toggle.pack(side='right', padx=5)

    def toggle_connection(self):
        if not self.is_connected:
            try:
                if self.controller_type == "Xbox":
                    self.gamepad = vg.VX360Gamepad()
                else:
                    self.gamepad = vg.VDS4Gamepad()
                
                # WARM-UP SEQUENCE: Force driver to see a state change
                # 1. Start at absolute zero
                self.gamepad.left_joystick_float(0.0, 0.0)
                self.gamepad.right_joystick_float(0.0, 0.0)
                self.gamepad.update()
                time.sleep(0.05)
                
                # 2. Briefly send a tiny pulse to "wake up" the report
                self.gamepad.left_joystick_float(0.01, 0.01)
                self.gamepad.update()
                time.sleep(0.05)
                
                # 3. Final Reset to absolute zero
                self.gamepad.reset()
                self.gamepad.left_joystick_float(0.0, 0.0)
                self.gamepad.right_joystick_float(0.0, 0.0)
                self.gamepad.update()
                
                self.is_connected = True
                self.btn_toggle.configure(text="Disconnect", fg_color="#388E3C", hover_color="#2E7D32")
                self.btn_remove.configure(state="disabled", fg_color="#555555")
                
                print(f"[INFO] {self.controller_type} Controller {self.index + 1} connected. Warm-up sequence complete.")
                self.start_heartbeat()
            except Exception as e:
                messagebox.showerror("Driver Error", f"Failed to connect controller: {e}\n\nEnsure ViGEmBus driver is installed.")
        else:
            self.is_connected = False
            if self.gamepad:
                self.gamepad.reset()
                self.gamepad.update()
            del self.gamepad
            self.gamepad = None
            self.btn_toggle.configure(text="Connect", fg_color="#1976D2", hover_color="#1565C0")
            self.btn_remove.configure(state="normal", fg_color="#d32f2f")
            print(f"[INFO] {self.controller_type} Controller {self.index + 1} disconnected.")

    def start_heartbeat(self):
        if self.is_connected and self.gamepad:
            try:
                # Continuously re-apply absolute zero using floats for consistency
                self.gamepad.left_joystick_float(0.0, 0.0)
                self.gamepad.right_joystick_float(0.0, 0.0)
                self.gamepad.update()
                
                # Repeat every 1 second for higher persistence
                self.after(1000, self.start_heartbeat)
            except Exception as e:
                print(f"[ERROR] Heartbeat failed for {self.controller_type} Controller {self.index + 1}: {e}")

    def remove(self):
        if self.is_connected:
            return
        self.remove_callback(self)
        self.destroy()

class ControllerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Virtual Controller Manager")
        self.geometry("650x700")
        
        # Main Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill='x', pady=30)

        self.title_label = ctk.CTkLabel(self.header_frame, text="VIRTUAL CONTROLLER HUB", 
                                        font=("Segoe UI", 24, "bold"))
        self.title_label.pack()

        # Button Container for adding different types
        self.btn_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.btn_container.pack(pady=15)

        self.add_xbox_btn = ctk.CTkButton(self.btn_container, text="+ ADD XBOX 360 CONTROLLER", 
                                     font=("Segoe UI", 12, "bold"), height=40,
                                     fg_color="#1976D2", hover_color="#1565C0",
                                     command=lambda: self.add_controller("Xbox"))
        self.add_xbox_btn.pack(side='left', padx=10)

        self.add_ps4_btn = ctk.CTkButton(self.btn_container, text="+ ADD PS4 CONTROLLER", 
                                     font=("Segoe UI", 12, "bold"), height=40,
                                     fg_color="#455A64", hover_color="#37474F",
                                     command=lambda: self.add_controller("PS4"))
        self.add_ps4_btn.pack(side='left', padx=10)

        # Scrollable area for controllers
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        self.controllers = []
        self.counter = 0

    def add_controller(self, controller_type):
        row = ControllerRow(self.scroll_frame, self.counter, self.remove_row, controller_type)
        self.controllers.append(row)
        self.counter += 1

    def remove_row(self, row):
        self.controllers.remove(row)

if __name__ == "__main__":
    try:
        import customtkinter
        import vgamepad
    except ImportError as e:
        print(f"[ERROR] Missing library: {e}")
        print("Please run: pip install customtkinter vgamepad")
        sys.exit(1)

    app = ControllerApp()
    app.mainloop()
