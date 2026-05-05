import customtkinter as ctk
from tkinter import messagebox
import vgamepad as vg
import keyboard
import json
import os

# Set Appearance and Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "controller_config.json"

# Constants for Mappable Actions
XBOX_ACTIONS = {
    "A Button": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "B Button": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "X Button": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "Y Button": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "LB (Shoulder)": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "RB (Shoulder)": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "LT (Trigger)": "LT",
    "RT (Trigger)": "RT",
    "Start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "Back": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    "Guide": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
    "Left Stick Click": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    "Right Stick Click": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    "DPAD Up": "DPAD_UP",
    "DPAD Down": "DPAD_DOWN",
    "DPAD Left": "DPAD_LEFT",
    "DPAD Right": "DPAD_RIGHT"
}

PS4_ACTIONS = {
    "Cross": vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
    "Circle": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
    "Square": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
    "Triangle": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
    "L1 (Shoulder)": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
    "R1 (Shoulder)": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
    "L2 (Trigger)": "L2",
    "R2 (Trigger)": "R2",
    "Options": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
    "Share": vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
    "L3 (Stick Click)": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT,
    "R3 (Stick Click)": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT,
    "PS Button": ("special", vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS),
    "Touchpad": ("special", vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD),
    "DPAD Up": "DPAD_UP",
    "DPAD Down": "DPAD_DOWN",
    "DPAD Left": "DPAD_LEFT",
    "DPAD Right": "DPAD_RIGHT"
}

class MappingRow(ctk.CTkFrame):
    def __init__(self, master, action_name, current_key, bind_callback, clear_callback):
        super().__init__(master, fg_color="transparent")
        self.action_name = action_name
        self.bind_callback = bind_callback
        self.clear_callback = clear_callback

        self.label = ctk.CTkLabel(self, text=action_name, font=("Segoe UI", 12), width=120, anchor='w')
        self.label.pack(side='left', padx=10)

        # Container for the button and the clear icon
        self.btn_container = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_container.pack(side='right', padx=10)

        self.btn_bind = ctk.CTkButton(self.btn_container, text=current_key if current_key else "None", 
                                      width=150, height=28, fg_color="#333333", 
                                      hover_color="#444444",
                                      command=self.start_binding)
        self.btn_bind.pack(side='left', padx=(0, 5), pady=2)

        self.btn_clear = ctk.CTkButton(self.btn_container, text="×", width=28, height=28,
                                       fg_color="#333333", hover_color="#8B0000",
                                       font=("Segoe UI", 18, "bold"),
                                       command=self.clear_binding)
        self.btn_clear.pack(side='left')

    def start_binding(self):
        self.btn_bind.configure(text="Press any key...", fg_color="#E65100")
        self.master.after(10, lambda: self.bind_callback(self.action_name, self.update_ui))

    def clear_binding(self):
        self.clear_callback(self.action_name)
        self.update_ui("None")

    def update_ui(self, key_name):
        if self.winfo_exists():
            self.btn_bind.configure(text=key_name, fg_color="#333333")

class ControllerRow(ctk.CTkFrame):
    def __init__(self, master, index, remove_callback, check_binding_callback, check_connection_callback, save_callback, controller_type="Xbox", initial_mappings=None):
        super().__init__(master, corner_radius=10)
        self.index = index
        self.remove_callback = remove_callback
        self.check_binding_callback = check_binding_callback
        self.check_connection_callback = check_connection_callback
        self.save_callback = save_callback
        self.controller_type = controller_type
        self.gamepad = None
        self.is_connected = False
        self.mappings = initial_mappings if initial_mappings else {}
        self.is_mapping_visible = False
        self.mapping_rows_ui = {}

        self.pack(fill='x', padx=20, pady=10)

        # Top Bar Container
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill='x')

        self.info_label = ctk.CTkLabel(self.top_bar, text="", font=("Segoe UI", 16, "bold"), width=200, anchor='w')
        self.info_label.pack(side='left', padx=20, pady=15)
        self.update_label(index)

        self.btn_remove = ctk.CTkButton(self.top_bar, text="Remove", width=80, height=32, 
                                        fg_color="#8B0000", hover_color="#B71C1C", command=self.remove)
        self.btn_remove.pack(side='right', padx=(5, 20))

        self.btn_toggle = ctk.CTkButton(self.top_bar, text="Connect", width=120, height=32, 
                                        fg_color="#1976D2", hover_color="#1565C0", command=self.toggle_connection)
        self.btn_toggle.pack(side='right', padx=5)

        self.btn_map = ctk.CTkButton(self.top_bar, text="Edit Bindings", width=100, height=32,
                                     fg_color="#455A64", hover_color="#607D8B", command=self.toggle_mapping_view)
        self.btn_map.pack(side='right', padx=5)

        # Mapping Content (Initially Hidden)
        self.mapping_frame = ctk.CTkFrame(self, fg_color="#222222", corner_radius=0)
        
        # Action Selection Bar
        self.add_bar = ctk.CTkFrame(self.mapping_frame, fg_color="transparent")
        self.add_bar.pack(fill='x', padx=10, pady=10)

        self.actions_dict = XBOX_ACTIONS if controller_type == "Xbox" else PS4_ACTIONS
        self.selector = ctk.CTkOptionMenu(self.add_bar, values=self.get_available_actions(), width=200)
        self.selector.set("Select action to add...")
        self.selector.pack(side='left', padx=5)

        self.btn_add = ctk.CTkButton(self.add_bar, text="+ ADD", width=60, fg_color="#1B5E20", hover_color="#2E7D32", command=self.add_selected_action)
        self.btn_add.pack(side='left', padx=5)

        # Container for active mappings
        self.rows_container = ctk.CTkFrame(self.mapping_frame, fg_color="transparent")
        self.rows_container.pack(fill='x')

        # Populate Initial Mapping Actions
        for action, key in self.mappings.items():
            self.create_mapping_row(action, key)

    def get_available_actions(self):
        actions = [a for a in self.actions_dict.keys() if a not in self.mappings]
        return actions if actions else ["(No actions available)"]

    def add_selected_action(self):
        action = self.selector.get()
        if action in self.actions_dict and action not in self.mappings:
            self.mappings[action] = None
            self.create_mapping_row(action, None)
            self.selector.configure(values=self.get_available_actions())
            self.selector.set("Select action to add...")
            self.save_callback()
        elif action == "(No actions available)":
            messagebox.showinfo("Limit Reached", "All possible buttons for this controller have already been added.")

    def create_mapping_row(self, action, key):
        row = MappingRow(self.rows_container, action, key, self.request_binding, self.remove_action)
        row.pack(fill='x', padx=10)
        self.mapping_rows_ui[action] = row

    def remove_action(self, action_name):
        if action_name in self.mappings:
            del self.mappings[action_name]
        if action_name in self.mapping_rows_ui:
            self.mapping_rows_ui[action_name].destroy()
            del self.mapping_rows_ui[action_name]
        self.selector.configure(values=self.get_available_actions())
        self.save_callback()
        print(f"[REMOVE] Controller {self.index + 1}: {action_name} removed.")

    def toggle_mapping_view(self):
        if self.is_mapping_visible:
            self.mapping_frame.pack_forget()
        else:
            self.mapping_frame.pack(fill='x', padx=10, pady=(0, 10))
        self.is_mapping_visible = not self.is_mapping_visible

    def request_binding(self, action_name, ui_callback):
        # Non-blocking key capture using keyboard.on_press
        def on_key(event):
            key_name = event.name
            keyboard.unhook(hook) # Stop listening
            
            # Safety Check: Does the controller/widget still exist?
            if not self.winfo_exists():
                return

            # Safety Check: Duplicate within same controller
            if not self.check_binding_callback(self.index, action_name, key_name):
                # Use after to update UI from main thread
                self.after(0, lambda: ui_callback(self.mappings[action_name] if self.mappings.get(action_name) else "None"))
                return

            self.mappings[action_name] = key_name
            self.after(0, lambda: ui_callback(key_name))
            self.save_callback()
            print(f"[BIND] Controller {self.index + 1}: {action_name} -> {key_name}")

        hook = keyboard.on_press(on_key)

    def clear_binding(self, action_name):
        self.mappings[action_name] = None
        self.save_callback()
        print(f"[CLEAR] Controller {self.index + 1}: {action_name} binding removed.")

    def update_label(self, new_index):
        self.index = new_index
        display_name = "Xbox 360" if self.controller_type == "Xbox" else "PS4"
        self.info_label.configure(text=f"🎮 {display_name} ({self.index + 1})")

    def toggle_connection(self, force_state=None):
        target_state = not self.is_connected if force_state is None else force_state
        if target_state == self.is_connected: return

        if target_state:
            # Check for cross-controller conflicts before connecting
            if not self.check_connection_callback(self):
                return
            try:
                self.gamepad = vg.VX360Gamepad() if self.controller_type == "Xbox" else vg.VDS4Gamepad()
                self.gamepad.reset()
                self.gamepad.update()
                self.is_connected = True
                self.btn_toggle.configure(text="Disconnect", fg_color="#388E3C", hover_color="#2E7D32")
                self.btn_remove.configure(state="disabled", fg_color="#555555")
                self.start_input_loop()
            except Exception as e:
                if force_state is None: messagebox.showerror("Driver Error", f"Failed to connect: {e}")
        else:
            self.is_connected = False
            if self.gamepad:
                self.gamepad.reset()
                self.gamepad.update()
                del self.gamepad
            self.gamepad = None
            self.btn_toggle.configure(text="Connect", fg_color="#1976D2", hover_color="#1565C0")
            self.btn_remove.configure(state="normal", fg_color="#8B0000")

    def start_input_loop(self):
        """High-frequency loop for real-time key-to-controller mapping (10ms)"""
        if not self.is_connected or not self.gamepad: return

        try:
            # Handle DPAD State (One directional update for multiple keys)
            dpad_up = keyboard.is_pressed(self.mappings["DPAD Up"]) if self.mappings.get("DPAD Up") else False
            dpad_down = keyboard.is_pressed(self.mappings["DPAD Down"]) if self.mappings.get("DPAD Down") else False
            dpad_left = keyboard.is_pressed(self.mappings["DPAD Left"]) if self.mappings.get("DPAD Left") else False
            dpad_right = keyboard.is_pressed(self.mappings["DPAD Right"]) if self.mappings.get("DPAD Right") else False

            # Update Standard Buttons
            for action, key in self.mappings.items():
                if not key or "DPAD" in action: continue
                
                vg_btn = self.actions_dict[action]
                is_pressed = keyboard.is_pressed(key)

                if isinstance(vg_btn, tuple) and vg_btn[0] == "special":
                    if is_pressed: self.gamepad.press_special_button(vg_btn[1])
                    else: self.gamepad.release_special_button(vg_btn[1])
                elif isinstance(vg_btn, str) and vg_btn in ["LT", "RT", "L2", "R2"]:
                    val = 255 if is_pressed else 0
                    if vg_btn in ["LT", "L2"]: self.gamepad.left_trigger(val)
                    else: self.gamepad.right_trigger(val)
                else:
                    if is_pressed: self.gamepad.press_button(vg_btn)
                    else: self.gamepad.release_button(vg_btn)

            # Update DPAD (Controller Specific)
            if self.controller_type == "Xbox":
                if dpad_up: self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
                else: self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
                if dpad_down: self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
                else: self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
                if dpad_left: self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
                else: self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
                if dpad_right: self.gamepad.press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
                else: self.gamepad.release_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)
            else:
                # PS4 uses a single directional_pad value
                direction = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE
                if dpad_up and dpad_right: direction = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST
                elif dpad_up and dpad_left: direction = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST
                elif dpad_down and dpad_right: direction = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST
                elif dpad_down and dpad_left: direction = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST
                elif dpad_up: direction = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH
                elif dpad_down: direction = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH
                elif dpad_left: direction = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST
                elif dpad_right: direction = vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST
                self.gamepad.directional_pad(direction)

            self.gamepad.update()
            self.after(10, self.start_input_loop)
        except Exception as e:
            print(f"[ERROR] Input loop failed: {e}")

    def remove(self):
        if self.is_connected: return
        self.remove_callback(self)
        self.destroy()

class ControllerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Virtual Controller Manager")
        self.geometry("800x850")
        
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill='x', pady=(20, 10))
        
        # Title and Reset Button Container
        self.title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_container.pack(fill='x', padx=20)
        
        ctk.CTkLabel(self.title_container, text="VIRTUAL CONTROLLER HUB", font=("Segoe UI", 24, "bold")).pack(side='left')
        
        self.btn_reset = ctk.CTkButton(self.title_container, text="CLEAR SAVED CONFIG", width=140, height=28,
                                       fg_color="#333333", hover_color="#8B0000", font=("Segoe UI", 10, "bold"),
                                       command=self.clear_config)
        self.btn_reset.pack(side='right')

        # Add Buttons
        self.btn_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.btn_container.pack(pady=15)
        ctk.CTkButton(self.btn_container, text="+ ADD XBOX 360", command=lambda: self.add_controller("Xbox"), fg_color="#1976D2").pack(side='left', padx=10)
        ctk.CTkButton(self.btn_container, text="+ ADD PS4", command=lambda: self.add_controller("PS4"), fg_color="#455A64").pack(side='left', padx=10)

        # Batch Row
        self.batch_header = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.batch_header.pack(fill='x', padx=20, pady=(0, 5))
        self.batch_btn_container = ctk.CTkFrame(self.batch_header, fg_color="transparent")
        self.batch_btn_container.pack(expand=True)

        self.colors = {
            "conn": {"on": {"base": "#1B5E20", "hover": "#2E7D32"}, "off": {"base": "#0D2B10", "hover": "#0D2B10"}},
            "disc": {"on": {"base": "#A83E00", "hover": "#E65100"}, "off": {"base": "#3D1600", "hover": "#3D1600"}},
            "rem": {"on": {"base": "#8B0000", "hover": "#B71C1C"}, "off": {"base": "#300000", "hover": "#300000"}}
        }

        self.conn_all_btn = ctk.CTkButton(self.batch_btn_container, text="CONNECT ALL", command=lambda: self.batch_action(True))
        self.conn_all_btn.pack(side='left', padx=5)
        self.disc_all_btn = ctk.CTkButton(self.batch_btn_container, text="DISCONNECT ALL", command=lambda: self.batch_action(False))
        self.disc_all_btn.pack(side='left', padx=5)
        self.rm_all_btn = ctk.CTkButton(self.batch_btn_container, text="REMOVE ALL", command=self.remove_all)
        self.rm_all_btn.pack(side='left', padx=5)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        self.controllers = []
        self.load_config()
        self.update_batch_visibility()

    def save_config(self):
        config_data = []
        for ctrl in self.controllers:
            config_data.append({
                "type": ctrl.controller_type,
                "mappings": ctrl.mappings
            })
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config_data, f, indent=4)
            print("[INFO] Configuration auto-saved.")
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config_data = json.load(f)
                    for item in config_data:
                        self.add_controller(item["type"], item.get("mappings", {}))
                print("[INFO] Configuration loaded.")
            except Exception as e:
                print(f"[ERROR] Failed to load config: {e}")

    def clear_config(self):
        if messagebox.askyesno("Clear Config", "This will disconnect all controllers and wipe your saved bindings. Proceed?"):
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            self.remove_all()
            messagebox.showinfo("Reset", "Saved configuration cleared.")

    def check_local_binding(self, caller_index, action_name, key_name):
        """Ensures a key isn't used by another button on the same controller."""
        ctrl = self.controllers[caller_index]
        for act, k in ctrl.mappings.items():
            if k == key_name:
                if act == action_name: continue
                messagebox.showwarning("Binding Conflict", f"Key '{key_name}' is already bound to this controller ({act})")
                return False
        return True

    def check_can_connect(self, caller_row):
        """Ensures the controller doesn't share keys with any already connected controllers."""
        my_keys = {k for k in caller_row.mappings.values() if k}
        for other in self.controllers:
            if other == caller_row or not other.is_connected:
                continue
            
            other_keys = {k for k in other.mappings.values() if k}
            conflicts = my_keys.intersection(other_keys)
            if conflicts:
                key_list = ", ".join(conflicts)
                messagebox.showerror("Connection Error", 
                    f"Cannot connect Controller {caller_row.index + 1}.\n"
                    f"Keys [{key_list}] are already in use by connected Controller {other.index + 1}.")
                return False
        return True

    def update_batch_visibility(self):
        has_controllers = len(self.controllers) > 0
        state = "normal" if has_controllers else "disabled"
        mode = "on" if has_controllers else "off"
        self.conn_all_btn.configure(state=state, fg_color=self.colors["conn"][mode]["base"], hover_color=self.colors["conn"][mode]["hover"])
        self.disc_all_btn.configure(state=state, fg_color=self.colors["disc"][mode]["base"], hover_color=self.colors["disc"][mode]["hover"])
        self.rm_all_btn.configure(state=state, fg_color=self.colors["rem"][mode]["base"], hover_color=self.colors["rem"][mode]["hover"])

    def add_controller(self, controller_type, initial_mappings=None):
        row = ControllerRow(self.scroll_frame, len(self.controllers), self.remove_row, self.check_local_binding, self.check_can_connect, self.save_config, controller_type, initial_mappings)
        self.controllers.append(row)
        self.update_batch_visibility()
        self.save_config()

    def remove_row(self, row):
        if row in self.controllers: self.controllers.remove(row)
        for i, c in enumerate(self.controllers): c.update_label(i)
        self.update_batch_visibility()
        self.save_config()

    def remove_all(self):
        self.batch_action(False)
        for c in list(self.controllers): c.destroy()
        self.controllers = []
        self.update_batch_visibility()
        self.save_config()

    def batch_action(self, connect):
        for c in self.controllers: c.toggle_connection(force_state=connect)

if __name__ == "__main__":
    app = ControllerApp()
    app.mainloop()
