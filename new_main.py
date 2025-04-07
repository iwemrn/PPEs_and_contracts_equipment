"""
попытка нового интерфейса
"""

import tkinter as tk
from modern_ui import ModernPPEApp

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernPPEApp(root)
    try:
        root.iconbitmap("icon.ico")
    except:
        pass
    
    root.mainloop()