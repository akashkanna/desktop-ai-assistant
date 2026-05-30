import sys
import os
from pathlib import Path

# Add project root to sys.path to allow absolute imports
sys.path.append(str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
