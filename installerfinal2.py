import os
import sys
import ctypes
import shutil

# Updated with your customized pop-up window text
EXTENSION_CODE = """import tkinter.messagebox as messagebox
import os
import sys
import tkinter.simpledialog as simpledialog

class SmartPairs:
    # Adds the secured menu option under the Options tab
    menudefs = [
        ('options', [
            ('AmpXD Override', '<<toggle-ampxd-mode>>'),
        ])
    ]

    def __init__(self, editwin):
        self.editwin = editwin
        self.text = editwin.text
        self.active = False 
        
        self.SECRET_PASSWORD = "amphibiar"
        
        self.history = []
        self.history_index = -1
        self.current_working_line = ""

        self.pairs = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
        
        # Macro Configurations
        self.macros = {
            "pf": 'print(f"")\n',
            "fori": 'for i in range():\n',
            "main": 'if __name__ == "__main__":\n    \n',
            "imp": 'import os, sys, math\n'
        }
        
        # Configure the custom visual highlight tag for the Variable Spy Glass
        self.text.tag_config("spy_glass_match", background="#E0E6ED", foreground="#000000")
        
        # Bind Menu and Core Key events
        self.text.bind('<<toggle-ampxd-mode>>', self.toggle_mode)
        self.text.bind("<KeyPress-Up>", self.history_up)
        self.text.bind("<KeyPress-Down>", self.history_down)
        
        # VS Code Layout Keybinding Remaps
        self.text.bind("<Control-f>", self.vscode_find)       
        self.text.bind("<Control-h>", self.vscode_replace)    
        self.text.bind("<Control-g>", self.vscode_goto)       
        
        # Macro Tab Trigger
        self.text.bind("<Tab>", self.trigger_macro)
        
        # Terminal Executer Mode Binding (Ctrl + Enter)
        self.text.bind("<Control-Return>", self.terminal_execute)
        
        # VS Code-Style Line Duplication (Alt + Shift + Down)
        self.text.bind("<Alt-Shift-Down>", self.duplicate_line)
        
        # Trigger Spy Glass tracking on mouse selection release or cursor movements
        self.text.bind("<ButtonRelease-1>", self.run_spy_glass)
        self.text.bind("<KeyRelease>", self.run_spy_glass)
        
        for opening_char in self.pairs.keys():
            self.text.bind(f"<Key-{opening_char}>", self.handle_keypress)

        self.start_autosave_daemon()

    def toggle_mode(self, event=None):
        if not self.active:
            user_input = simpledialog.askstring(
                "Access Required", 
                "Enter Admin Password to enable AmpXD Override:", 
                show='*'
            )
            
            if user_input == self.SECRET_PASSWORD:
                self.active = True
                messagebox.showinfo("AmpXD Override", " Heyyy access granted! Mode is now ENABLED [✓]. Code works.")
            else:
                messagebox.showerror("Access Denied", "Incorrect password. Wrong user. Please run as Ghost. Mode remains disabled.")
        else:
            self.active = False
            # Clean up active highlights if the mode is shut off
            self.text.tag_remove("spy_glass_match", "1.0", "end")
            messagebox.showinfo("AmpXD Override", "AmpXD Mode is now DISABLED [✗]")
            
        return "break"

    def handle_keypress(self, event):
        if not self.active:
            return None 
            
        opening = event.char
        closing = self.pairs.get(opening)
        
        if closing:
            try:
                start_idx = self.text.index("sel.first")
                end_idx = self.text.index("sel.last")
                selected_text = self.text.get(start_idx, end_idx)
                
                self.text.delete(start_idx, end_idx)
                self.text.insert(start_idx, opening + selected_text + closing)
                
                new_end_idx = f"{start_idx} + {len(selected_text) + 2} chars"
                self.text.tag_add("sel", start_idx, new_end_idx)
                return "break"
                
            except Exception:
                self.text.insert("insert", opening + closing)
                self.text.mark_set("insert", "insert-1c")
                return "break"

    def get_current_line_text(self):
        return self.text.get("insert linestart", "insert lineend")

    def history_up(self, event):
        if not self.active:
            return None
        if event.state & 0x20000:  
            return None

        all_lines = self.text.get("1.0", "end-1c").split("\n")
        self.history = [line.strip() for line in all_lines if line.strip()]
        
        if not self.history:
            return "break"

        if self.history_index == -1:
            self.current_working_line = self.get_current_line_text()
            self.history_index = len(self.history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
            
        self.text.delete("insert linestart", "insert lineend")
        self.text.insert("insert linestart", self.history[self.history_index])
        return "break"

    def history_down(self, event):
        if not self.active or self.history_index == -1:
            return None
        if event.state & 0x20000:  
            return None

        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.text.delete("insert linestart", "insert lineend")
            self.text.insert("insert linestart", self.history[self.history_index])
        else:
            self.history_index = -1
            self.text.delete("insert linestart", "insert lineend")
            self.text.insert("insert linestart", self.current_working_line)
            
        return "break"

    def trigger_macro(self, event):
        if not self.active:
            return None
            
        cursor_idx = self.text.index("insert")
        line_start = self.text.index("insert linestart")
        line_text = self.text.get(line_start, cursor_idx)
        
        words = line_text.split()
        if not words:
            return None
            
        last_word = words[-1]
        expansion = self.macros.get(last_word)
        
        if expansion:
            word_len = len(last_word)
            start_delete_idx = f"insert - {word_len} chars"
            self.text.delete(start_delete_idx, "insert")
            self.text.insert("insert", expansion)
            
            if last_word == "pf":
                self.text.mark_set("insert", "insert - 3 chars")
            elif last_word == "fori":
                self.text.mark_set("insert", "insert - 4 chars")
                
            return "break" 
        return None

    def start_autosave_daemon(self):
        self.text.after(30000, self.execute_autosave)

    def execute_autosave(self):
        try:
            filename = self.editwin.io.filename
            if filename:
                backup_path = filename + ".ampxd.bak"
                current_content = self.text.get("1.0", "end-1c")
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(current_content)
        except Exception:
            pass
        self.start_autosave_daemon()

    def vscode_find(self, event=None):
        if self.active:
            self.text.event_generate("<<find>>") 
            return "break"
            
    def vscode_replace(self, event=None):
        if self.active:
            self.text.event_generate("<<replace>>") 
            return "break"
            
    def vscode_goto(self, event=None):
        if self.active:
            self.text.event_generate("<<goto-line>>") 
            return "break"

    def terminal_execute(self, event=None):
        if not self.active:
            return None
            
        try:
            start_idx = self.text.index("sel.first")
            end_idx = self.text.index("sel.last")
            target_code = self.text.get(start_idx, end_idx)
        except Exception:
            target_code = self.text.get("insert linestart", "insert lineend")
            
        if target_code.strip():
            flist = self.editwin.flist
            if flist and hasattr(flist, "pyshell") and flist.pyshell:
                shell = flist.pyshell
                shell.top.wakeup()
                shell.enter()
                shell.text.insert("insert", target_code)
                shell.enter()
                
        return "break"

    def duplicate_line(self, event=None):
        if not self.active:
            return None
        current_line_text = self.text.get("insert linestart", "insert lineend")
        self.text.insert("insert lineend", "\n" + current_line_text)
        return "break"

    def run_spy_glass(self, event=None):
        self.text.tag_remove("spy_glass_match", "1.0", "end")
        
        if not self.active:
            return None
            
        try:
            start_idx = self.text.index("sel.first")
            end_idx = self.text.index("sel.last")
            target_word = self.text.get(start_idx, end_idx).strip()
        except Exception:
            cursor_pos = self.text.index("insert")
            start_idx = self.text.search(r"\y", cursor_pos, backwards=True, regexp=True, stopindex="insert linestart")
            end_idx = self.text.search(r"\y", cursor_pos, regexp=True, stopindex="insert lineend")
            
            if start_idx and end_idx:
                target_word = self.text.get(start_idx, end_idx).strip()
            else:
                target_word = ""

        if target_word and target_word.isalnum():
            search_start = "1.0"
            while True:
                pos = self.text.search(rf"\y{target_word}\y", search_start, stopindex="end", regexp=True)
                if not pos:
                    break
                match_end = f"{pos} + {len(target_word)} chars"
                self.text.tag_add("spy_glass_match", pos, match_end)
                search_start = match_end
"""

CONFIG_TEXT = "\n\n[SmartPairs]\nenable=1\n[SmartPairs_cfgBindings]\ntoggle-ampxd-mode=\n"

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    # Force window privilege elevation
    if not is_admin():
        print("Requesting Administrator Permissions...")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    print("===================================================")
    print("             AmpXD Override Auto-Installer         ")
    print("===================================================")
    
    try:
        import idlelib
        idlelib_path = os.path.dirname(idlelib.__file__)
        print(f"✓ Found target folder: {idlelib_path}")
    except ImportError:
        print("❌ Error: Could not locate IDLE path automatically.")
        input("\nPress Enter to exit...")
        return

    script_file_path = os.path.join(idlelib_path, "SmartPairs.py")
    config_file_path = os.path.join(idlelib_path, "config-extensions.def")

    # Deploy extension
    try:
        with open(script_file_path, "w", encoding="utf-8") as f:
            f.write(EXTENSION_CODE)
        print("✓ SmartPairs.py created successfully with perfect code formatting.")
    except Exception as e:
        print(f"❌ Error: Failed to write file. {e}")
        input("\nPress Enter to exit...")
        return

    # Deploy configurations safely
    with open(config_file_path, "r", encoding="utf-8") as f:
        config_content = f.read()

    if "[SmartPairs]" in config_content:
        print("✓ Configurations are already active inside IDLE.")
    else:
        shutil.copyfile(config_file_path, config_file_path + ".bak")
        with open(config_file_path, "a", encoding="utf-8") as f:
            f.write(CONFIG_TEXT)
        print("✓ Registered configurations inside config-extensions.def (Backup created).")

    print("\n===================================================")
    print("Installation Complete! Please close and restart IDLE.")
    print("===================================================")
    input("\nPress Enter to finish...")

if __name__ == "__main__":
    main()