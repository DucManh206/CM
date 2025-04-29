# gui_setup.py
# -*- coding: utf-8 -*-
import tkinter
import customtkinter
import os

# Bỏ import: from utils import LOADED_USER_AGENT_LIST

# --- Tab 1: Tạo Profile ---
# <<< THAY ĐỔI Ở ĐÂY: Thêm tham số ua_loaded_successfully >>>
def setup_create_tab(tab, app, ua_loaded_successfully):
    """Thiết lập các widget cho tab Tạo Profile."""
    content_frame = customtkinter.CTkFrame(tab, fg_color="transparent")
    content_frame.pack(pady=10, padx=10, fill="both", expand=True)
    content_frame.columnconfigure(0, weight=1)
    content_frame.rowconfigure(3, weight=1)

    config_frame = customtkinter.CTkFrame(content_frame)
    config_frame.grid(row=0, column=0, padx=0, pady=0, sticky="ew")
    config_frame.columnconfigure(1, weight=1)

    label_num = customtkinter.CTkLabel(config_frame, text="Số lượng hồ sơ cần tạo:")
    label_num.grid(row=0, column=0, padx=10, pady=(10,5), sticky="w")
    app.entry_num = customtkinter.CTkEntry(config_frame, placeholder_text="Nhập số lượng (VD: 10)")
    app.entry_num.grid(row=0, column=1, padx=10, pady=(10,5), sticky="ew", columnspan=2)

    label_dir = customtkinter.CTkLabel(config_frame, text="Thư mục gốc để lưu profiles:")
    label_dir.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    entry_dir_create = customtkinter.CTkEntry(config_frame, textvariable=app.entry_dir_var, state="readonly")
    entry_dir_create.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
    button_browse_create = customtkinter.CTkButton(config_frame, text="Chọn thư mục", width=100, command=app.browse_directory)
    button_browse_create.grid(row=1, column=2, padx=10, pady=5)

    app.check_random_ua_var = tkinter.BooleanVar()
    ua_checkbox_text = "Sử dụng User Agent Ngẫu nhiên khi tạo"
    ua_checkbox_state = tkinter.NORMAL

    # <<< THAY ĐỔI Ở ĐÂY: Kiểm tra tham số thay vì import >>>
    if not ua_loaded_successfully:
        ua_checkbox_text += " (Lỗi: Không tải được user_agents.txt)"
        ua_checkbox_state = tkinter.DISABLED

    check_random_ua = customtkinter.CTkCheckBox(config_frame,
                                              text=ua_checkbox_text,
                                              variable=app.check_random_ua_var,
                                              state=ua_checkbox_state)
    check_random_ua.grid(row=2, column=0, columnspan=3, padx=10, pady=(5,10), sticky="w")

    app.create_button = customtkinter.CTkButton(content_frame, text="Bắt đầu tạo Profiles", command=app.start_creation_thread)
    app.create_button.grid(row=1, column=0, padx=0, pady=10, sticky="ew")
    app.progress_bar = customtkinter.CTkProgressBar(content_frame, orientation="horizontal")
    # progress_bar sẽ được pack/grid bởi hàm tạo profile

    app.status_textbox_create = customtkinter.CTkTextbox(content_frame)
    app.status_textbox_create.grid(row=3, column=0, padx=0, pady=(0,0), sticky="nsew")
    app.status_textbox_create.insert("0.0", "Sẵn sàng tạo hồ sơ...\n")


# --- Tab 2: Quản lý ---
def setup_manage_tab(tab, app):
    """Thiết lập các widget cho tab Quản lý."""
    # --- Code setup tab Quản lý giữ nguyên như trước ---
    tab.columnconfigure(0, weight=1)
    tab.rowconfigure(1, weight=1) # Cho phép list frame giãn ra

    top_frame = customtkinter.CTkFrame(tab)
    top_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
    top_frame.columnconfigure(1, weight=1)

    label_current_dir = customtkinter.CTkLabel(top_frame, text="Thư mục Profiles:")
    label_current_dir.grid(row=0, column=0, padx=(5,0), pady=5, sticky="w")
    entry_display_dir = customtkinter.CTkEntry(top_frame, textvariable=app.entry_dir_var, state="readonly")
    entry_display_dir.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    button_browse_manage = customtkinter.CTkButton(top_frame, text="Chọn thư mục", width=100, command=app.browse_directory)
    button_browse_manage.grid(row=0, column=2, padx=(0,5), pady=5)
    button_refresh_manage = customtkinter.CTkButton(top_frame, text="Làm mới DS", width=100, command=app.refresh_profile_list_manage)
    button_refresh_manage.grid(row=0, column=3, padx=5, pady=5)

    list_container_frame = customtkinter.CTkFrame(tab)
    list_container_frame.grid(row=1, column=0, padx=10, pady=(5,5), sticky="nsew") # Expand
    list_container_frame.rowconfigure(1, weight=1)
    list_container_frame.columnconfigure(0, weight=1)
    list_label = customtkinter.CTkLabel(list_container_frame, text="Danh sách Profiles:")
    list_label.grid(row=0, column=0, padx=5, pady=(5,0), sticky="w")
    app.profile_list_frame_manage = customtkinter.CTkScrollableFrame(list_container_frame)
    app.profile_list_frame_manage.grid(row=1, column=0, padx=0, pady=(0,5), sticky="nsew") # Expand

    action_frame = customtkinter.CTkFrame(tab)
    action_frame.grid(row=2, column=0, padx=10, pady=(0,5), sticky="ew")
    action_frame.columnconfigure(0, weight=1)
    action_frame.columnconfigure(1, weight=1)
    button_open_selected = customtkinter.CTkButton(action_frame, text="Mở đã chọn", command=app.open_selected_profiles_manage)
    button_open_selected.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    button_delete_selected = customtkinter.CTkButton(action_frame, text="Xóa đã chọn", fg_color="red", hover_color="darkred", command=app.delete_selected_profiles_manage)
    button_delete_selected.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    app.status_textbox_manage = customtkinter.CTkTextbox(tab, height=80)
    app.status_textbox_manage.grid(row=3, column=0, padx=10, pady=(0,10), sticky="ew")
    app.status_textbox_manage.insert("0.0", "Trạng thái quản lý (xóa, lỗi...) sẽ hiện ở đây...\n")


# --- Tab 3: Script ---
def setup_script_tab(tab, app):
    """Thiết lập các widget cho tab Script."""
    # --- Code setup tab Script giữ nguyên như trước ---
    tab.columnconfigure(0, weight=1)
    tab.rowconfigure(1, weight=1) # Cho list frame giãn
    tab.rowconfigure(2, weight=1) # Cho phần script runner giãn
    tab.rowconfigure(4, weight=0) # Status box co lại

    top_frame_script = customtkinter.CTkFrame(tab)
    top_frame_script.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
    top_frame_script.columnconfigure(1, weight=1)
    label_current_dir_script = customtkinter.CTkLabel(top_frame_script, text="Thư mục Profiles:")
    label_current_dir_script.grid(row=0, column=0, padx=(5,0), pady=5, sticky="w")
    entry_display_dir_script = customtkinter.CTkEntry(top_frame_script, textvariable=app.entry_dir_var, state="readonly")
    entry_display_dir_script.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    button_refresh_script = customtkinter.CTkButton(top_frame_script, text="Làm mới DS", width=100, command=app.refresh_profile_list_script)
    button_refresh_script.grid(row=0, column=2, padx=5, pady=5)

    list_container_script = customtkinter.CTkFrame(tab)
    list_container_script.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
    list_container_script.rowconfigure(1, weight=1)
    list_container_script.columnconfigure(0, weight=1)
    list_label_script = customtkinter.CTkLabel(list_container_script, text="Chọn profiles để chạy script:")
    list_label_script.grid(row=0, column=0, padx=5, pady=(5,0), sticky="w")
    app.profile_list_frame_script = customtkinter.CTkScrollableFrame(list_container_script)
    app.profile_list_frame_script.grid(row=1, column=0, padx=0, pady=(0,5), sticky="nsew")

    script_runner_frame = customtkinter.CTkFrame(tab)
    script_runner_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
    script_runner_frame.rowconfigure(2, weight=1)
    script_runner_frame.columnconfigure(0, weight=1)

    select_file_frame = customtkinter.CTkFrame(script_runner_frame, fg_color="transparent")
    select_file_frame.grid(row=0, column=0, padx=0, pady=0, sticky="ew")
    select_file_frame.columnconfigure(1, weight=1)
    button_select_script = customtkinter.CTkButton(select_file_frame, text="1. Chọn File Script (.py)", width=180, command=app.select_script_file)
    button_select_script.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    app.script_display_label = customtkinter.CTkLabel(select_file_frame, textvariable=app.script_display_var, anchor="w", text_color="gray")
    app.script_display_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    paste_label = customtkinter.CTkLabel(script_runner_frame, text="Hoặc Dán/Gõ Script Python vào đây (ưu tiên chạy code này nếu có):")
    paste_label.grid(row=1, column=0, padx=5, pady=(5,0), sticky="w")
    app.script_paste_textbox = customtkinter.CTkTextbox(script_runner_frame, height=100)
    app.script_paste_textbox.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

    app.run_script_button = customtkinter.CTkButton(script_runner_frame, text="2. Chạy Script trên Profile đã chọn", command=app.start_script_runner_thread)
    app.run_script_button.grid(row=3, column=0, padx=5, pady=10, sticky="ew")

    app.status_textbox_script = customtkinter.CTkTextbox(tab, height=100)
    app.status_textbox_script.grid(row=4, column=0, padx=10, pady=(0,10), sticky="ew")
    app.status_textbox_script.insert("0.0", "Output từ script sẽ hiện ở đây...\n")