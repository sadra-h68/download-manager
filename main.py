import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QProgressBar,
    QSpinBox, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
import requests
import os
from pathlib import Path
from threading import Lock


class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    speed = pyqtSignal(str)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, filepath, row_index):
        super().__init__()
        self.url = url
        self.filepath = filepath
        self.row_index = row_index
        self.is_running = True

    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=10)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            if total_size == 0:
                self.error.emit("نمی‌تونم سایز فایل رو مشخص کنم")
                return

            downloaded_size = 0
            chunk_size = 8192
            
            os.makedirs(os.path.dirname(self.filepath) or '.', exist_ok=True)
            
            with open(self.filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if not self.is_running:
                        f.close()
                        os.remove(self.filepath)
                        self.status.emit("متوقف شد")
                        return
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        progress_percent = int((downloaded_size / total_size) * 100)
                        self.progress.emit(progress_percent)
                        
                        speed_mbps = (downloaded_size / (1024 * 1024)) / max(1, len(chunk) / 1_000_000)
                        self.speed.emit(f"{speed_mbps:.2f} MB/s")
            
            self.status.emit("تمام شد")
            self.finished.emit()
            
        except requests.exceptions.RequestException as e:
            self.error.emit(f"خطا: {str(e)}")
        except Exception as e:
            self.error.emit(f"خطا: {str(e)}")

    def stop(self):
        self.is_running = False


class DownloadManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.downloads = {}
        self.lock = Lock()
        self.download_path = str(Path.home() / "Downloads")
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("دانلود منیجر")
        self.setGeometry(100, 100, 900, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # URL Input Section
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("لینک دانلود:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/file.zip")
        url_layout.addWidget(self.url_input)

        self.browse_btn = QPushButton("انتخاب مسیر")
        self.browse_btn.clicked.connect(self.browse_path)
        url_layout.addWidget(self.browse_btn)

        layout.addLayout(url_layout)

        # Number of Parallel Downloads
        parallel_layout = QHBoxLayout()
        parallel_layout.addWidget(QLabel("تعداد دانلود همزمان:"))
        self.parallel_spinbox = QSpinBox()
        self.parallel_spinbox.setMinimum(1)
        self.parallel_spinbox.setMaximum(10)
        self.parallel_spinbox.setValue(3)
        parallel_layout.addWidget(self.parallel_spinbox)
        parallel_layout.addStretch()

        layout.addLayout(parallel_layout)

        # Download Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["نام فایل", "وضعیت", "پیشرفت", "سرعت", "حذف"])
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 80)

        layout.addWidget(self.table)

        # Add Download Button
        self.add_btn = QPushButton("اضافه کردن دانلود")
        self.add_btn.clicked.connect(self.add_download)
        layout.addWidget(self.add_btn)

        central_widget.setLayout(layout)

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "انتخاب مسیر دانلود", self.download_path)
        if path:
            self.download_path = path

    def add_download(self):
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "خطا", "لطفا یک لینک وارد کنید")
            return

        if not url.startswith(('http://', 'https://')):
            QMessageBox.warning(self, "خطا", "لطفا یک لینک معتبر وارد کنید")
            return

        # Get filename from URL
        filename = url.split('/')[-1] or 'download'
        if '?' in filename:
            filename = filename.split('?')[0]

        filepath = os.path.join(self.download_path, filename)

        row = self.table.rowCount()
        self.table.insertRow(row)

        # Filename
        self.table.setItem(row, 0, QTableWidgetItem(filename))

        # Status
        status_item = QTableWidgetItem("در حال شروع...")
        self.table.setItem(row, 1, status_item)

        # Progress Bar
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        self.table.setCellWidget(row, 2, progress_bar)

        # Speed
        speed_item = QTableWidgetItem("0 MB/s")
        self.table.setItem(row, 3, speed_item)

        # Delete Button
        delete_btn = QPushButton("حذف")
        delete_btn.clicked.connect(lambda: self.cancel_download(row))
        self.table.setCellWidget(row, 4, delete_btn)

        # Start Download
        worker = DownloadWorker(url, filepath, row)
        worker.progress.connect(lambda p: progress_bar.setValue(p))
        worker.speed.connect(lambda s: self.table.item(row, 3).setText(s))
        worker.status.connect(lambda s: self.table.item(row, 1).setText(s))
        worker.error.connect(lambda e: self.show_error(row, e))
        worker.finished.connect(lambda: self.download_finished(row))

        with self.lock:
            self.downloads[row] = worker

        worker.start()
        self.url_input.clear()

    def cancel_download(self, row):
        with self.lock:
            if row in self.downloads:
                worker = self.downloads[row]
                worker.stop()
                worker.wait()
                del self.downloads[row]
        
        self.table.removeRow(row)
        self.reindex_downloads()

    def download_finished(self, row):
        with self.lock:
            if row in self.downloads:
                del self.downloads[row]

    def show_error(self, row, error):
        self.table.item(row, 1).setText(error)

    def reindex_downloads(self):
        new_downloads = {}
        for i in range(self.table.rowCount()):
            # Re-map row indices
            pass
        self.downloads = new_downloads


def main():
    app = QApplication(sys.argv)
    manager = DownloadManager()
    manager.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
