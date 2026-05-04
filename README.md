# Virtual Controller Manager 🎮

A modern Windows application to emulate virtual Xbox 360 and PS4 controllers using Python. This tool provides a professional GUI to map keyboard keys to gamepad inputs, recognized by Windows as legitimate hardware.

---

## 🚀 Features
- **Modern GUI:** Built with `CustomTkinter` for a sleek "Dark Mode" aesthetic.
- **Multi-Controller Support:** Emulate both **Xbox 360** and **DualShock 4 (PS4)** controllers simultaneously.
- **Custom Key Mapping:** Bind any keyboard key to specific controller buttons, triggers, or DPAD directions.
- **Persistent Profiles:** Your controllers and their specific key bindings are automatically saved and reloaded on startup.
- **Batch Management:** Quickly Connect, Disconnect, or Remove all virtual controllers with a single click.
- **Dynamic Management:** Add or remove as many controllers as you need.
- **Independent Control:** Connect/Disconnect controllers individually.
- **Legitimate Emulation:** Uses the ViGEmBus driver to ensure controllers show up in Device Manager and work with games/apps.
- **Conflict Detection:** Built-in logic prevents accidental duplicate key bindings across different actions or controllers.

---

## 🛠️ Prerequisites

Before running the application, you **MUST** install the following:

### 1. ViGEmBus Driver (Critical)
The application relies on the **ViGEmBus** driver to communicate with Windows.
- **Download:** [ViGEmBus Latest Release](https://github.com/nefarius/ViGEmBus/releases)
- **Installation:** Download the `.exe` or `.msi` and follow the installer prompts.

### 2. Python 3.7+
Ensure you have Python installed and added to your system PATH.

---

## 📦 Installation

1. **Clone or Download** this project to your local machine.
2. **Open a terminal** in the project directory.
3. **Install dependencies** using the requirements file:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🎮 How to Use

1. **Launch the app:**
   ```bash
   python virtual_controller.py
   ```
2. **Add Controllers:** Click `+ ADD XBOX 360` or `+ ADD PS4` to create a new virtual device.
3. **Configure Bindings:**
   - Click **Edit Bindings** on a controller row.
   - Use the dropdown to select an action (e.g., "A Button").
   - Click the binding button (labeled "None" initially) and press the desired key on your keyboard.
4. **Connect:** Click the blue **Connect** button. It will turn green when active. 
   - *Check your Device Manager under "Xbox 360 Peripherals" to see it appear.*
5. **Disconnect:** Click the green **Disconnect** button to remove the virtual device from Windows.
6. **Batch Controls:** Use the top-level buttons to manage multiple controllers at once.
7. **Remove:** Once disconnected, you can use the red **Remove** button to delete the controller from the list.
8. **Save/Reset:** Bindings save automatically to `controller_config.json`. Use **CLEAR SAVED CONFIG** in the header to wipe all settings.

---

## 🛠️ Building the Executable (.exe)

If you want to package this application into a standalone Windows executable, use **PyInstaller**.

### 1. Install PyInstaller
```bash
pip install pyinstaller
```

### 2. Run the Build Command
Use the following command to bundle the script, GUI assets (`CustomTkinter`), and the gamepad drivers (`vgamepad` DLLs) into a single file:

```bash
pyinstaller --noconsole --onefile --collect-all customtkinter --collect-all vgamepad virtual_controller.py
```

### 3. Locate your EXE
- Once finished, a new folder named **`dist/`** will be created.
- Your standalone **`virtual_controller.exe`** will be inside it.
- **Note:** The first time you launch the `.exe`, it may take 5–10 seconds to open while it extracts itself to a temporary folder. Subsequent launches are much faster.

---

## ⚠️ Troubleshooting

- **Error: "Failed to connect controller":** This usually means the ViGEmBus driver is missing or not installed correctly. Re-run the ViGEmBus installer and restart your computer.
- **Controller not showing in game:** Ensure the controller is "Connected" (Green button) before launching your game.
- **GUI looks weird:** Ensure you have installed the `customtkinter` library via the requirements file.
- **Key not registering:** Ensure you haven't bound the same key to multiple controllers, as the conflict detector will warn you but might prevent the binding if already in use.

---

## 📄 License
This project is provided "as-is" for simulation and development purposes. It uses the `vgamepad` library which is a wrapper for the [ViGEm Framework](https://github.com/ViGEm).
