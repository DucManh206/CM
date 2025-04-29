# main_app.py
# -*- coding: utf-8 -*-
import sys
import os
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import threading
import time
import tempfile

# --- 1. Kiểm tra và Cài đặt Dependencies ---
from utils import check_and_install_dependencies
REQUIRED_LIBRARIES = ["selenium", "customtkinter"]
if not check_and_install_dependencies(REQUIRED_LIBRARIES):
    print("Thoát ứng dụng do lỗi dependencies.")
    sys.exit(1)

# --- 2. Import các thư viện và module khác ---
import customtkinter

# Các module tự định nghĩa
# Đảm bảo các file này tồn tại trong cùng thư mục
from gui_setup import setup_create_tab, setup_manage_tab, setup_script_tab
from profile_actions import create_chrome_profiles_threaded, launch_profile, delete_profiles
from script_runner import run_python_script_threaded
from utils import load_user_agents, get_chrome_executable_path, update_status
# Không cần import LOADED_USER_AGENT_LIST ở đây nữa

# --- Lớp ứng dụng chính ---
class ProfileCreatorApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Công cụ quản lý hồ sơ Chrome v3.1 - Modular") # Đổi version nếu muốn
        self.geometry("750x600")

        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")

        # --- Biến dùng chung ---
        self.home_dir = os.path.expanduser("~")
        self.default_profile_path = os.path.join(self.home_dir, "ChromeProfiles")
        if not os.path.exists(self.default_profile_path):
            try:
                os.makedirs(self.default_profile_path)
                print(f"Đã tạo thư mục mặc định: {self.default_profile_path}")
            except OSError as e:
                print(f"Không thể tạo thư mục mặc định '{self.default_profile_path}': {e}")
                self.default_profile_path = self.home_dir

        self.entry_dir_var = tkinter.StringVar(value=self.default_profile_path)
        self.chrome_path = get_chrome_executable_path()
        self.selected_script_path = None
        self.script_display_var = tkinter.StringVar(value="Chưa chọn file script")

        # --- Biến trạng thái Checkbox ---
        self.profile_checkbox_vars_manage = {}
        self.profile_checkbox_vars_script = {}

        # --- Tải User Agents và Lưu kết quả ---
        # <<< THAY ĐỔI Ở ĐÂY: Lưu kết quả trả về (True/False) >>>
        self.ua_load_success = load_user_agents()

        if not self.chrome_path:
             print("Cảnh báo: Không tự động tìm thấy Google Chrome.")
             # Hiển thị cảnh báo một lần khi khởi động
             self.after(100, lambda: tkinter.messagebox.showwarning("Không tìm thấy Chrome", "Không thể tự động tìm thấy Google Chrome.\nChức năng 'Mở Profile' và 'Chạy Script' có thể không hoạt động đúng.\nHãy đảm bảo Chrome đã cài đặt và/hoặc nằm trong PATH hệ thống."))

        # --- Tạo TabView ---
        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.pack(pady=10, padx=10, fill="both", expand=True)
        self.tab_view.add("Tạo Profile")
        self.tab_view.add("Quản lý")
        self.tab_view.add("Script")
        self.tab_view.set("Tạo Profile")

        # --- Thiết lập từng tab ---
        # <<< THAY ĐỔI Ở ĐÂY: Truyền kết quả tải UA vào hàm setup_create_tab >>>
        setup_create_tab(self.tab_view.tab("Tạo Profile"), self, self.ua_load_success)
        setup_manage_tab(self.tab_view.tab("Quản lý"), self)
        setup_script_tab(self.tab_view.tab("Script"), self)

        # --- Tải danh sách profile ban đầu ---
        self.after(100, self.refresh_profile_list_manage)
        self.after(100, self.refresh_profile_list_script)


    # --- Các hàm xử lý sự kiện (commands của các nút) ---

    def browse_directory(self):
        """Mở hộp thoại chọn thư mục và cập nhật."""
        initial_dir = self.entry_dir_var.get() if os.path.isdir(self.entry_dir_var.get()) else self.home_dir
        directory = tkinter.filedialog.askdirectory(initialdir=initial_dir, title="Chọn thư mục gốc chứa Profiles")
        if directory:
            self.entry_dir_var.set(directory)
            self.refresh_profile_list_manage()
            self.refresh_profile_list_script()

    def refresh_profile_list_manage(self):
        """Làm mới danh sách profile cho tab Quản lý."""
        if hasattr(self, 'profile_list_frame_manage') and hasattr(self, 'status_textbox_manage'):
            self._refresh_profile_list_internal(self.profile_list_frame_manage, self.profile_checkbox_vars_manage, self.status_textbox_manage)
        else:
            print("Lỗi: Widget của tab Quản lý chưa được khởi tạo khi gọi refresh.")

    def refresh_profile_list_script(self):
        """Làm mới danh sách profile cho tab Script."""
        if hasattr(self, 'profile_list_frame_script') and hasattr(self, 'status_textbox_script'):
             self._refresh_profile_list_internal(self.profile_list_frame_script, self.profile_checkbox_vars_script, self.status_textbox_script)
        else:
            print("Lỗi: Widget của tab Script chưa được khởi tạo khi gọi refresh.")

    def _refresh_profile_list_internal(self, target_frame, target_checkbox_dict, status_box_to_update):
        """Hàm helper để làm mới danh sách profile."""
        # --- Code làm mới danh sách giữ nguyên ---
        for widget in target_frame.winfo_children():
            widget.destroy()
        target_checkbox_dict.clear()

        base_dir = self.entry_dir_var.get()

        if not os.path.isdir(base_dir):
            label_no_dir = customtkinter.CTkLabel(target_frame, text=f"Thư mục không tồn tại:\n{base_dir}", text_color="gray")
            label_no_dir.pack(pady=10, padx=5)
            update_status(status_box_to_update, f"Lỗi refresh list: Thư mục không tồn tại '{base_dir}'\n")
            return

        try:
            found_profiles = []
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if os.path.isdir(item_path) and item.startswith("Profile_"):
                    found_profiles.append((item, item_path))
                elif os.path.isdir(item_path):
                    print(f"Debug: Bỏ qua thư mục không đúng định dạng tên: {item}")

            if not found_profiles:
                label_empty = customtkinter.CTkLabel(target_frame, text="(Không tìm thấy profile nào dạng 'Profile_XXX')", text_color="gray")
                label_empty.pack(pady=10, padx=5)
            else:
                found_profiles.sort(key=lambda x: x[0])
                for profile_name, profile_path in found_profiles:
                    item_frame = customtkinter.CTkFrame(target_frame, fg_color="transparent")
                    item_frame.pack(fill="x", pady=(0, 0), padx=(5, 10))

                    checkbox_var = tkinter.BooleanVar()
                    checkbox = customtkinter.CTkCheckBox(item_frame, text="", variable=checkbox_var, width=10, height=10)
                    checkbox.pack(side=tkinter.LEFT, padx=(0, 5))
                    target_checkbox_dict[profile_path] = checkbox_var

                    button = customtkinter.CTkButton(
                        item_frame,
                        text=profile_name,
                        anchor="w",
                        height=24,
                        command=lambda p=profile_path: self.launch_profile(p)
                    )
                    button.pack(side=tkinter.LEFT, fill="x", expand=True, padx=0, pady=1)

        except Exception as e:
             label_error = customtkinter.CTkLabel(target_frame, text=f"Lỗi khi đọc thư mục:\n{e}", text_color="red")
             label_error.pack(pady=10, padx=5)
             update_status(status_box_to_update, f"Lỗi refresh list: {e}\n")

    def get_selected_profiles_manage(self):
        """Lấy danh sách profile đã chọn từ tab Quản lý."""
        selected_paths = []
        for profile_path, var in self.profile_checkbox_vars_manage.items():
            if var.get():
                selected_paths.append(profile_path)
        return selected_paths

    def get_selected_profiles_script(self):
        """Lấy danh sách profile đã chọn từ tab Script."""
        selected_paths = []
        for profile_path, var in self.profile_checkbox_vars_script.items():
            if var.get():
                selected_paths.append(profile_path)
        return selected_paths

    def open_selected_profiles_manage(self):
        """Mở hàng loạt profile đã chọn từ tab Quản lý."""
        selected = self.get_selected_profiles_manage()
        if not selected:
            tkinter.messagebox.showinfo("Thông báo", "Vui lòng chọn ít nhất một profile từ danh sách trên để mở.")
            return
        count = len(selected)
        print(f"Yêu cầu mở hàng loạt {count} profiles từ tab Quản lý...")
        if count > 5:
             if not tkinter.messagebox.askyesno("Cảnh báo", f"Bạn sắp mở {count} hồ sơ Chrome cùng lúc. Điều này có thể tốn nhiều tài nguyên. Tiếp tục?"):
                 return
        opened_count = 0
        for profile_path in selected:
            if launch_profile(profile_path, self.chrome_path, show_error=False, status_textbox=self.status_textbox_manage):
                opened_count += 1
            else:
                 print(f"-> Bỏ qua mở profile lỗi: {os.path.basename(profile_path)}")
        print(f"Đã cố gắng mở {opened_count}/{count} profiles.")
        if opened_count < count:
             update_status(self.status_textbox_manage, f"Cảnh báo: Đã xảy ra lỗi khi mở một số profile. Kiểm tra log console.\n")

    def delete_selected_profiles_manage(self):
        """Xóa profile đã chọn từ tab Quản lý."""
        selected = self.get_selected_profiles_manage()
        if not selected:
            tkinter.messagebox.showinfo("Thông báo", "Vui lòng chọn ít nhất một profile từ danh sách trên để xóa.")
            return
        count = len(selected)
        display_limit = 10
        profile_names_list = [os.path.basename(p) for p in selected]
        profile_names_display = "\n - ".join(profile_names_list[:display_limit])
        if count > display_limit:
            profile_names_display += f"\n - ... và {count - display_limit} profiles khác."

        if tkinter.messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn XÓA VĨNH VIỄN {count} profile sau?\n\n - {profile_names_display}\n\nHành động này không thể hoàn tác!"):
            deleted_count, errors = delete_profiles(selected, self.status_textbox_manage) # Gọi hàm từ profile_actions
            if errors:
                error_display = "\n".join(errors[:5])
                if len(errors) > 5:
                    error_display += f"\n... (và {len(errors) - 5} lỗi khác, xem console)"
                tkinter.messagebox.showerror("Lỗi khi xóa", f"Không thể xóa một số profile:\n\n" + error_display)
            self.refresh_profile_list_manage()
            self.refresh_profile_list_script()

    def launch_profile(self, profile_path):
        """Mở một profile đơn lẻ."""
        launch_profile(profile_path, self.chrome_path, show_error=True, status_textbox=None)

    def select_script_file(self):
        """Mở hộp thoại chọn file script."""
        filetypes = (("Python files", "*.py"), ("All files", "*.*"))
        initial_dir = os.path.dirname(os.path.abspath(__file__)) # Bắt đầu từ thư mục script chính
        filepath = tkinter.filedialog.askopenfilename(
            title="Chọn file script Python",
            initialdir=initial_dir,
            filetypes=filetypes
        )
        if filepath:
            self.selected_script_path = filepath
            self.script_display_var.set(os.path.basename(filepath))
            if hasattr(self, 'script_paste_textbox') and self.script_paste_textbox.winfo_exists():
                self.script_paste_textbox.delete("1.0", tkinter.END)
            update_status(self.status_textbox_script, f"Đã chọn file script: {filepath}\n")

    def start_script_runner_thread(self):
        """Kiểm tra nguồn script và bắt đầu luồng chạy."""
        selected_profiles = self.get_selected_profiles_script()
        script_content = ""
        if hasattr(self, 'script_paste_textbox') and self.script_paste_textbox.winfo_exists():
             script_content = self.script_paste_textbox.get("1.0", tkinter.END).strip()

        script_to_run_path = None
        temp_file_created_path = None

        if script_content:
            update_status(self.status_textbox_script, "Phát hiện script trong ô text. Sẽ tạo file tạm để chạy.\n")
            try:
                fd, temp_file_created_path = tempfile.mkstemp(suffix='.py', text=True, encoding='utf-8')
                with os.fdopen(fd, 'w', encoding='utf-8') as temp_file:
                    temp_file.write(script_content)
                script_to_run_path = temp_file_created_path
                print(f"Đã tạo file tạm: {script_to_run_path}")
            except Exception as e:
                tkinter.messagebox.showerror("Lỗi tạo file tạm", f"Không thể tạo file script tạm thời:\n{e}")
                if temp_file_created_path and os.path.exists(temp_file_created_path):
                     try: os.remove(temp_file_created_path)
                     except OSError: pass
                return
        elif self.selected_script_path and os.path.exists(self.selected_script_path):
            script_to_run_path = self.selected_script_path
            update_status(self.status_textbox_script, f"Sử dụng file script đã chọn: {os.path.basename(script_to_run_path)}\n")
        else:
            tkinter.messagebox.showerror("Lỗi", "Vui lòng chọn một file script Python hoặc dán mã vào ô text.")
            return

        if not selected_profiles:
            tkinter.messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất một profile (từ danh sách trên) để chạy script.")
            if temp_file_created_path:
                 try: os.remove(temp_file_created_path)
                 except OSError: pass
            return

        warning_script_name = os.path.basename(script_to_run_path)
        if not tkinter.messagebox.askyesno("CẢNH BÁO BẢO MẬT",
            f"Bạn sắp chạy script Python:\n\n{warning_script_name}\n{' (Từ ô text)' if temp_file_created_path else ' (Từ file)'}\n\n"
            f"RỦI RO BẢO MẬT! Chỉ chạy script bạn tin tưởng.\n\n"
            f"Đảm bảo script của bạn:\n"
            f"1. Nhận đường dẫn profile từ sys.argv[1].\n"
            f"2. Tự khởi tạo và đóng WebDriver (`driver.quit()`).\n"
            f"3. Mọi thư viện cần thiết đã được cài đặt.\n\n"
            f"Bạn có chắc chắn muốn tiếp tục?"
        ):
            if temp_file_created_path:
                 try: os.remove(temp_file_created_path)
                 except OSError: pass
            return

        self.run_script_button.configure(state=tkinter.DISABLED)
        self.status_textbox_script.delete("1.0", tkinter.END)

        thread = threading.Thread(
            target=run_python_script_threaded, # Gọi hàm từ script_runner
            args=(script_to_run_path, selected_profiles, self.status_textbox_script, self.run_script_button, temp_file_created_path),
            daemon=True
        )
        thread.start()

    def start_creation_thread(self):
        """Bắt đầu luồng tạo profile."""
        try:
            num_profiles = int(self.entry_num.get())
            if num_profiles <= 0:
                tkinter.messagebox.showerror("Lỗi", "Số lượng hồ sơ phải là số nguyên dương.")
                return
        except ValueError:
            tkinter.messagebox.showerror("Lỗi", "Vui lòng nhập một số hợp lệ.")
            return
        base_dir = self.entry_dir_var.get()
        if not base_dir:
            tkinter.messagebox.showerror("Lỗi", "Vui lòng chọn thư mục gốc.")
            return
        if not os.path.isdir(base_dir):
             try:
                 os.makedirs(base_dir)
                 update_status(self.status_textbox_create, f"Đã tạo thư mục gốc được chỉ định: {base_dir}\n")
             except OSError as e:
                 tkinter.messagebox.showerror("Lỗi thư mục", f"Thư mục gốc không tồn tại và không thể tạo:\n{base_dir}\nLỗi: {e}")
                 return

        # <<< THAY ĐỔI Ở ĐÂY: Sử dụng self.ua_load_success đã lưu >>>
        use_random_ua = self.check_random_ua_var.get() if self.ua_load_success else False
        # Hoặc bạn có thể disable checkbox nếu self.ua_load_success là False trong __init__
        # use_random_ua = self.check_random_ua_var.get() # Vẫn đọc checkbox, nhưng hàm tạo sẽ bỏ qua nếu list rỗng

        self.create_button.configure(state=tkinter.DISABLED)
        self.status_textbox_create.delete("1.0", tkinter.END)

        # Truyền đúng các widget đã được gán vào self
        thread = threading.Thread(
            target=create_chrome_profiles_threaded, # Gọi hàm từ profile_actions
            args=(num_profiles, base_dir, use_random_ua, self.status_textbox_create, self.progress_bar, self.create_button),
            daemon=True
        )
        thread.start()

# --- Chạy ứng dụng ---
if __name__ == "__main__":
    # 1. Kiểm tra Dependencies
    if not check_and_install_dependencies(REQUIRED_LIBRARIES):
        print("Thoát ứng dụng do lỗi dependencies.")
        sys.exit(1)

    # 2. Import CustomTkinter sau khi kiểm tra
    import customtkinter

    # 3. In thời gian và chạy App
    try:
        local_time = time.localtime()
        print(f"Ứng dụng khởi chạy lúc (giờ hệ thống): {time.strftime('%Y-%m-%d %H:%M:%S', local_time)}")
    except Exception as e_time:
        print(f"Lỗi khi lấy thời gian: {e_time}")

    app = ProfileCreatorApp()
    app.mainloop()