from PyQt5.QtWidgets import QProgressDialog, QApplication
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt
import os

def load_large_file_to_editor(editor, file_path, show_progress=True):
    editor._ignore_change_signal = True
    doc = editor.document()
    doc.setUndoRedoEnabled(False)
    editor.setUpdatesEnabled(False)

    doc.clear()
    cursor = QTextCursor(doc)
    editor.setTextCursor(cursor)

    file_size = os.path.getsize(file_path)
    chunk_size = 32768
    total_read = 0

    progress = None
    if show_progress and file_size > 512 * 1024:
        progress = QProgressDialog(f"Loading {os.path.basename(file_path)}...", "Cancel", 0, file_size, editor)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.setMinimumDuration(300)
        progress.setStyleSheet(editor.styleSheet())
        progress.show()

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            cursor.insertText(chunk)
            total_read += len(chunk)

            if progress:
                progress.setValue(total_read)
                QApplication.processEvents()
                if progress.wasCanceled():
                    editor.setPlainText("⚠️ Load canceled.")
                    break

    # forzar al 100% y cerrar
    if progress:
        progress.setValue(file_size)
        progress.close()

    # volver al comienzo
    cursor.movePosition(QTextCursor.Start)
    editor.setTextCursor(cursor)

    editor.setUpdatesEnabled(True)
    doc.setUndoRedoEnabled(True)
    editor._ignore_change_signal = False
