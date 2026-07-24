import tkinter.messagebox as messagebox
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
        
        # Bind Menu and Key events
        self.text.bind('<<toggle-ampxd-mode>>', self.toggle_mode)
        self.text.bind("<KeyPress-Up>", self.history_up)
        self.text.bind("<KeyPress-Down>", self.history_down)
        
        # Bind Ctrl + / for VS Code Style Toggling
        self.text.bind("<Control-slash>", self.toggle_comment)
        
        for opening_char in self.pairs.keys():
            self.text.bind(f"<Key-{opening_char}>", self.handle_keypress)

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
            messagebox.showinfo("AmpXD Override", "AmpXD Mode is now DISABLED [✗]")
            
        return "break"

    def handle_keypress(self, event):
        if not self.active:
            return None 
            
        opening = event.char
        closing = self.pairs.get(opening)
        
        if closing:
            self.text.insert("insert", opening + closing)
            self.text.mark_set("insert", "insert-1c")
            return "break"

    def get_current_line_text(self):
        return self.text.get("insert linestart", "insert lineend")

    def history_up(self, event):
        if not self.active:
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

        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.text.delete("insert linestart", "insert lineend")
            self.text.insert("insert linestart", self.history[self.history_index])
        else:
            self.history_index = -1
            self.text.delete("insert linestart", "insert lineend")
            self.text.insert("insert linestart", self.current_working_line)
            
        return "break"

    def toggle_comment(self, event=None):
        if not self.active:
            return None

        try:
            # Check for selected text lines
            start_idx = self.text.index("sel.first")
            end_idx = self.text.index("sel.last")
        except Exception:
            # Default to active single line if nothing is selected
            start_idx = self.text.index("insert linestart")
            end_idx = self.text.index("insert lineend")

        start_line = int(start_idx.split("."))
        end_line = int(end_idx.split("."))
        
        # Adjust boundary if selection snaps to the very beginning of the next row
        if end_line > start_line and end_idx.split(".")[1] == "0":
            end_line -= 1

        # Check if all highlighted lines are already commented out
        all_commented = True
        for line_num in range(start_line, end_line + 1):
            line_txt = self.text.get(f"{line_num}.0", f"{line_num}.end").lstrip()
            if line_txt and not line_txt.startswith("#"):
                all_commented = False
                break

        # Apply action to lines
        for line_num in range(start_line, end_line + 1):
            line_txt = self.text.get(f"{line_num}.0", f"{line_num}.end")
            
            if all_commented:
                # Remove comment marker safely
                lstripped = line_txt.lstrip()
                leading_spaces = len(line_txt) - len(lstripped)
                if lstripped.startswith("#"):
                    rem_len = 2 if lstripped.startswith("# ") else 1
                    self.text.delete(f"{line_num}.{leading_spaces}", f"{line_num}.{leading_spaces + rem_len}")
            else:
                # Insert comment marker respecting indentation limits
                if line_txt.strip():
                    lstripped = line_txt.lstrip()
                    leading_spaces = len(line_txt) - len(lstripped)
                    self.text.insert(f"{line_num}.{leading_spaces}", "# ")
                    
        return "break"
