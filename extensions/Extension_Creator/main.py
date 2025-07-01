import os
import subprocess
from pathlib import Path
from zipfile import ZipFile
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QFormLayout, QFrame
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer

name = "Extension Creator"
enabled = True
description = "Tool to create new extensions from a template"

def setup(api):
    creator_widget = QWidget()
    main_layout = QVBoxLayout(creator_widget)

    # — Panel Create —
    create_panel = QFrame()
    cp_layout = QVBoxLayout(create_panel)

    form = QFormLayout()
    name_input = QLineEdit()
    desc_input = QLineEdit()
    form.addRow("Extension name:", name_input)
    form.addRow("Description:", desc_input)
    cp_layout.addLayout(form)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    custom_ext_dir = os.path.join(base_dir, "customext")
    os.makedirs(custom_ext_dir, exist_ok=True)
    default_root = custom_ext_dir
    path_label = QLabel(str(default_root))
    path_label.setStyleSheet("color: gray; font-size: 11px;")
    cp_layout.addWidget(path_label)

    create_btn = QPushButton("Create Extension")
    cp_layout.addWidget(create_btn)

    go_to_settings_btn = QPushButton("Go to Extension Settings")
    go_to_settings_btn.setVisible(False)
    cp_layout.addWidget(go_to_settings_btn)

    main_layout.addWidget(create_panel)

    # — Panel Settings —
    settings_panel = QFrame()
    sp_layout = QVBoxLayout(settings_panel)

    icon_label = QLabel(alignment=Qt.AlignCenter)
    extension_label = QLabel(alignment=Qt.AlignCenter)
    extension_label.setStyleSheet("font-weight:bold; font-size:16px;")

    desc_group = QWidget()
    desc_layout = QVBoxLayout(desc_group)
    desc_layout.setContentsMargins(0, 0, 0, 0)
    desc_layout.setSpacing(2)

    description_title = QLabel("Description:")
    description_title.setAlignment(Qt.AlignCenter)
    description_title.setStyleSheet("font-weight:bold;")
    description_label = QLabel()
    description_label.setAlignment(Qt.AlignCenter)
    description_label.setWordWrap(True)
    description_label.setStyleSheet("color:gray;")

    desc_layout.addWidget(description_title)
    desc_layout.addWidget(description_label)

    refresh_btn = QPushButton("Refresh Extension")
    bundle_btn  = QPushButton("Create bundle")
    open_folder_btn = QPushButton("Open extension folder")
    back_btn    = QPushButton("Back to Create")

    sp_layout.addWidget(icon_label)
    sp_layout.addWidget(extension_label)
    sp_layout.addWidget(desc_group)
    sp_layout.addWidget(refresh_btn)
    sp_layout.addWidget(bundle_btn)
    sp_layout.addWidget(open_folder_btn)
    sp_layout.addWidget(back_btn)

    settings_panel.hide()
    main_layout.addWidget(settings_panel)

    # Estado
    current_name = ""
    current_desc = ""
    current_path = ""

    def refresh_extension_info():
        nonlocal current_name, current_desc, current_path

        current_path = path_label.text().strip()
        if not os.path.isdir(current_path):
            path_label.setText(custom_ext_dir)
            switch_to_create()
            go_to_settings_btn.setVisible(False)
            return

        name_from_folder = os.path.basename(current_path)
        readme_path = os.path.join(current_path, "README.md")

        current_name = name_from_folder
        current_desc = ""

        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if len(lines) > 1:
                    current_desc = "".join(lines[1:]).strip()

        name_input.setText(current_name)
        desc_input.setText(current_desc)

        icon_file = os.path.join(current_path, "icons", "plugin.svg")
        if not os.path.exists(icon_file):
            icon_dir = os.path.join(current_path, "icons")
            if os.path.exists(icon_dir):
                for f in os.listdir(icon_dir):
                    if f.lower().endswith((".png", ".svg")):
                        icon_file = os.path.join(icon_dir, f)
                        break

        if os.path.exists(icon_file):
            pix = QPixmap(icon_file).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pix)
        else:
            icon_label.clear()

        extension_label.setText(f"Extension: {current_name}")
        description_label.setText(current_desc)

    def switch_to_settings():
        current_path_check = path_label.text().strip()
        pext_path = os.path.join(current_path_check, ".pext")
        if not (os.path.isdir(current_path_check) and os.path.exists(pext_path)):
            QMessageBox.warning(creator_widget, "Warning", "Extension path is invalid or missing .pext file. Returning to Create panel.")
            path_label.setText(custom_ext_dir)
            check_for_existing_extension(custom_ext_dir)
            switch_to_create()
            return

        refresh_extension_info()
        create_panel.hide()
        settings_panel.show()

    def switch_to_create():
        settings_panel.hide()
        create_panel.show()

    def check_for_existing_extension(folder):
        if not os.path.isdir(folder):
            go_to_settings_btn.setVisible(False)
            return
        pext_path = os.path.join(folder, ".pext")
        if os.path.exists(pext_path):
            go_to_settings_btn.setVisible(True)
            name_input.setText(os.path.basename(folder))
            readme = os.path.join(folder, "README.md")
            if os.path.exists(readme):
                with open(readme, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        desc_input.setText("".join(lines[1:]).strip())
            path_label.setText(folder)
        else:
            go_to_settings_btn.setVisible(False)

    go_to_settings_btn.clicked.connect(switch_to_settings)

    def on_create():
        ext_name = name_input.text().strip()
        ext_desc = desc_input.text().strip()
        base_folder = path_label.text().strip()

        if not ext_name:
            QMessageBox.warning(creator_widget, "Error", "Extension name is required.")
            return

        if QMessageBox.question(
            creator_widget, "Confirm",
            "All unsaved tabs will be closed and current project will be reset. Continue?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return

        for i in reversed(range(api.get_tab_count())):
            if not api.is_tab_modified(i):
                api.close_tab(i)

        ext_dir = os.path.join(base_folder, ext_name)
        icons_dir = os.path.join(ext_dir, "icons")
        bundle_dir = os.path.join(ext_dir, "bundle")
        os.makedirs(icons_dir, exist_ok=True)
        os.makedirs(bundle_dir, exist_ok=True)

        with open(os.path.join(ext_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(f"# {ext_name}\n\n{ext_desc}\n")
        with open(os.path.join(ext_dir, "main.py"), "w", encoding="utf-8") as f:
            f.write(f'''name = "{ext_name}"
enabled = False
def setup(api):
    def saludar():
        api.show_message("¡Hola desde la extensión!", "Hello")
    api.add_menu_action("Extensiones/Hello World", saludar)
''')
        with open(os.path.join(ext_dir, ".pext"), "w", encoding="utf-8") as f:
            f.write("power edit ext id local")

        QMessageBox.information(creator_widget, "Success", f"Extension '{ext_name}' created in:\n{ext_dir}")

        mp = os.path.join(ext_dir, "main.py")
        if hasattr(api.main_window, "open_file_from_explorer"):
            api.main_window.open_file_from_explorer(mp)
        else:
            ed = api.open_new_tab(file_path=mp)
            if ed and hasattr(ed, "set_language"):
                ed.set_language("python")
            if ed:
                api.main_window.current_files[ed] = mp

        if hasattr(api.main_window, "file_explorer"):
            api.main_window.file_explorer.set_root(ext_dir)

        path_label.setText(ext_dir)
        check_for_existing_extension(ext_dir)
        switch_to_settings()

    create_btn.clicked.connect(on_create)

    bundle_btn.clicked.connect(lambda: create_bundle(current_path, current_name, creator_widget))
    open_folder_btn.clicked.connect(lambda: open_folder(current_path))
    back_btn.clicked.connect(switch_to_create)

    refresh_btn.clicked.connect(refresh_extension_info)

    def create_bundle(path, name, parent):
        bundle_dir = os.path.join(path, "bundle")
        bundle_file = os.path.join(bundle_dir, f"{name}.ext")

        os.makedirs(bundle_dir, exist_ok=True)

        if os.path.exists(bundle_file):
            os.remove(bundle_file)
        with ZipFile(bundle_file, "w") as z:
            for root, _, files in os.walk(path):
                for fn in files:
                    z.write(os.path.join(root, fn), os.path.relpath(os.path.join(root, fn), path))
        QMessageBox.information(parent, "Bundle Created", f"Bundle saved at:\n{bundle_file}")
        if os.name == "nt":
            os.startfile(bundle_dir)
        else:
            subprocess.Popen(["xdg-open", bundle_dir])

    def open_folder(path):
        if os.name == "nt":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])

    def reset_path_if_no_pext():
        root_path = path_label.text().strip()
        pext_path = os.path.join(root_path, ".pext")
        if not (os.path.isdir(root_path) and os.path.exists(pext_path)):
            path_label.setText(custom_ext_dir)
            check_for_existing_extension(custom_ext_dir)
            refresh_extension_info()
            switch_to_create()

    def is_valid_extension_folder(folder):
        if not os.path.isdir(folder):
            return False
        pext = os.path.join(folder, ".pext")
        main_py = os.path.join(folder, "main.py")
        readme = os.path.join(folder, "README.md")
        return os.path.exists(pext) and (os.path.exists(main_py) or os.path.exists(readme))

    def update_root_from_file_explorer():
        # Esta función se llama para actualizar root y botón si la root cambió
        if hasattr(api.main_window, "file_explorer"):
            new_root = api.main_window.file_explorer.project_root or custom_ext_dir
            old_root = path_label.text().strip()
            if new_root != old_root:
                path_label.setText(new_root)
                if is_valid_extension_folder(new_root):
                    go_to_settings_btn.setVisible(True)
                else:
                    go_to_settings_btn.setVisible(False)
                refresh_extension_info()
                switch_to_create()

    # Timer para verificar periódicamente cambios en root del file explorer
    timer = QTimer()
    timer.timeout.connect(update_root_from_file_explorer)
    timer.start(1000)  # cada 1 segundo

    def on_dock_visibility_changed(visible):
        if visible:
            # Siempre que se muestre el dock, empezar en custom_ext_dir
            path_label.setText(custom_ext_dir)
            check_for_existing_extension(custom_ext_dir)
            refresh_extension_info()
            switch_to_create()

            # Después intenta actualizar si el file explorer tiene root válido
            if hasattr(api.main_window, "file_explorer"):
                root = api.main_window.file_explorer.project_root or custom_ext_dir
                if is_valid_extension_folder(root):
                    path_label.setText(root)
                    check_for_existing_extension(root)
                    refresh_extension_info()
                    switch_to_create()
        else:
            reset_path_if_no_pext()

    dock = api.create_dock_widget("Create Extension", creator_widget)

    # Conectamos señal del file_explorer una vez que esté listo
    def connect_project_root_signal():
        fe = getattr(api.main_window, "file_explorer", None)
        if fe and hasattr(fe, "project_root_changed"):
            print("[DEBUG] Conectando señal project_root_changed")
            def on_project_root_changed(new_root):
                print("[DEBUG] Señal project_root_changed recibida:", new_root)
                if settings_panel.isVisible():
                    if not is_valid_extension_folder(new_root):
                        path_label.setText(custom_ext_dir)
                        check_for_existing_extension(custom_ext_dir)
                        refresh_extension_info()
                        switch_to_create()
                        dock.hide()
                    else:
                        path_label.setText(new_root)
                        check_for_existing_extension(new_root)
                        refresh_extension_info()
                else:
                    path_label.setText(new_root)
                    if is_valid_extension_folder(new_root):
                        go_to_settings_btn.setVisible(True)
                    else:
                        go_to_settings_btn.setVisible(False)
                    refresh_extension_info()

            fe.project_root_changed.connect(on_project_root_changed)
        else:
            print("[DEBUG] No se pudo conectar project_root_changed")

    QTimer.singleShot(100, connect_project_root_signal)  # da tiempo a que se cree file_explorer

    # Estado inicial
    path_label.setText(custom_ext_dir)
    check_for_existing_extension(custom_ext_dir)
    refresh_extension_info()
    switch_to_create()

    dock.hide()

