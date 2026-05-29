import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog
from PySide6.QtWebEngineCore import QWebEngineProfile
# Import classes from main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import Investidor10SyncDialog

app = QApplication(sys.argv)
profile = QWebEngineProfile("TestProfile")
try:
    print("Creating dialog...")
    dialog = Investidor10SyncDialog(profile)
    print("Dialog created successfully.")
    # Show it non-modally first to see if it displays
    dialog.show()
    print("Dialog shown. Executing app...")
    sys.exit(app.exec())
except Exception as e:
    import traceback
    traceback.print_exc()
