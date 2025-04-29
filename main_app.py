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
# <<< THÊM THƯ VIỆN MỚI VÀO DANH SÁCH KIỂM TRA >>>
REQUIRED_LIBRARIES = ["selenium", "customtkinter", "webdriver-manager", "psutil"]
if not check_and_install_dependencies(REQUIRED_LIBRARIES):
    print("Thoát ứng dụng do lỗi dependencies.")
    sys.exit(1)

# --- 2. Import các thư viện và module khác ---
import customtkinter

from gui_setup import setup_create_tab, setup_manage_tab, setup_script_tab
# <<< Import hàm mới từ utils >>>
from profile_actions import create_chrome_profiles_threaded, launch_profile, delete_profiles
from script_runner import run_python_script_threaded
from utils import load_user_agents, get_chrome_executable_path, update_status, close_chrome_process_by_profile

# --- Lớp ứng dụng chính ---
class ProfileCreatorApp(customtkinter.CTk):
    def __init__(self):
        # ... (Phần __init__ khác giữ nguyên) ...
        super().__init__()
        self.title("Công cụ quản lý hồ sơ Chrome v3.5 - AutoDriver/Close")
        self.geometry("750x600")
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")
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
        self.profile_checkbox_vars_manage = {}
        self.profile_checkbox_vars_script = {}
        self.select_all_manage_var = tkinter.BooleanVar(value=False)
        self.select_all_script_var = tkinter.BooleanVar(value=False)
        self.loaded_ua_list = load_user_agents()
        self.ua_load_success = bool(self.loaded_ua_list)
        if not self.chrome_path:
             print("Cảnh báo: Không tự động tìm thấy Google Chrome.")
             self.after(100, lambda: tkinter.messagebox.showwarning("Không tìm thấy Chrome", "...")) # Giữ lại cảnh báo
        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.pack(pady=10, padx=10, fill="both", expand=True)
        self.tab_view.add("Tạo Profile")
        self.tab_view.add("Quản lý")
        self.tab_view.add("Script")
        self.tab_view.set("Tạo Profile")
        setup_create_tab(self.tab_view.tab("Tạo Profile"), self, self.ua_load_success)
        setup_manage_tab(self.tab_view.tab("Quản lý"), self)
        setup_script_tab(self.tab_view.tab("Script"), self)
        self.after(100, self.refresh_profile_list_manage)
        self.after(100, self.refresh_profile_list_script)

    # --- Các hàm xử lý sự kiện ---

    # ... (browse_directory, refresh_profile_list_manage, refresh_profile_list_script,
    #      _refresh_profile_list_internal, get_selected_profiles_manage,
    #      get_selected_profiles_script, toggle_select_all_manage,
    #      toggle_select_all_script, open_selected_profiles_manage giữ nguyên) ...

    def browse_directory(self):
        initial_dir = self.entry_dir_var.get() if os.path.isdir(self.entry_dir_var.get()) else self.home_dir
        directory = tkinter.filedialog.askdirectory(initialdir=initial_dir, title="Chọn thư mục gốc chứa Profiles")
        if directory:
            self.entry_dir_var.set(directory)
            self.refresh_profile_list_manage()
            self.refresh_profile_list_script()

    def refresh_profile_list_manage(self):
        if hasattr(self, 'select_all_manage_var'):
            self.select_all_manage_var.set(False)
        if hasattr(self, 'profile_list_frame_manage') and hasattr(self, 'status_textbox_manage'):
            self._refresh_profile_list_internal(self.profile_list_frame_manage, self.profile_checkbox_vars_manage, self.status_textbox_manage)
        else:
            print("Lỗi: Widget của tab Quản lý chưa được khởi tạo khi gọi refresh.")

    def refresh_profile_list_script(self):
        if hasattr(self, 'select_all_script_var'):
             self.select_all_script_var.set(False)
        if hasattr(self, 'profile_list_frame_script') and hasattr(self, 'status_textbox_script'):
             self._refresh_profile_list_internal(self.profile_list_frame_script, self.profile_checkbox_vars_script, self.status_textbox_script)
        else:
            print("Lỗi: Widget của tab Script chưa được khởi tạo khi gọi refresh.")

    def _refresh_profile_list_internal(self, target_frame, target_checkbox_dict, status_box_to_update):
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
                        item_frame, text=profile_name, anchor="w", height=24,
                        command=lambda p=profile_path: self.launch_profile(p)
                    )
                    button.pack(side=tkinter.LEFT, fill="x", expand=True, padx=0, pady=1)
        except Exception as e:
             label_error = customtkinter.CTkLabel(target_frame, text=f"Lỗi khi đọc thư mục:\n{e}", text_color="red")
             label_error.pack(pady=10, padx=5)
             update_status(status_box_to_update, f"Lỗi refresh list: {e}\n")

    def get_selected_profiles_manage(self):
        selected_paths = []
        for profile_path, var in self.profile_checkbox_vars_manage.items():
            if var.get():
                selected_paths.append(profile_path)
        return selected_paths

    def get_selected_profiles_script(self):
        selected_paths = []
        for profile_path, var in self.profile_checkbox_vars_script.items():
            if var.get():
                selected_paths.append(profile_path)
        return selected_paths

    def toggle_select_all_manage(self):
        target_state = self.select_all_manage_var.get()
        for var in self.profile_checkbox_vars_manage.values():
            var.set(target_state)

    def toggle_select_all_script(self):
        target_state = self.select_all_script_var.get()
        for var in self.profile_checkbox_vars_script.values():
            var.set(target_state)

    def open_selected_profiles_manage(self):
        selected = self.get_selected_profiles_manage()
        if not selected:
            tkinter.messagebox.showinfo("Thông báo", "Vui lòng chọn ít nhất một profile từ danh sách trên để mở.")
            return
        count = len(selected)
        print(f"Yêu cầu mở hàng loạt {count} profiles từ tab Quản lý...")
        if count > 5:
             if not tkinter.messagebox.askyesno("Cảnh báo", f"Bạn sắp mở {count} hồ sơ Chrome cùng lúc. Tiếp tục?"):
                 return
        opened_count = 0
        for profile_path in selected:
            if launch_profile(profile_path, self.chrome_path, show_error=False, status_textbox=self.status_textbox_manage):
                opened_count += 1
            else:
                 print(f"-> Bỏ qua mở profile lỗi: {os.path.basename(profile_path)}")
        print(f"Đã cố gắng mở {opened_count}/{count} profiles.")
        if opened_count < count:
             update_status(self.status_textbox_manage, f"Cảnh báo: Lỗi khi mở một số profile.\n")

    # <<< THAY ĐỔI HÀM XÓA >>>
    def delete_selected_profiles_manage(self):
        """Xóa profile đã chọn từ tab Quản lý, cố gắng đóng Chrome trước."""
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

        # Xác nhận xóa
        if tkinter.messagebox.askyesno("Xác nhận xóa",
                   f"Bạn sắp XÓA VĨNH VIỄN {count} profile sau:\n\n - {profile_names_display}\n\n"
                   f"Công cụ sẽ cố gắng đóng cửa sổ Chrome đang mở của các profile này trước khi xóa.\n"
                   f"Hành động này không thể hoàn tác! Bạn chắc chắn?"):

            profiles_to_delete_after_check = []
            update_status(self.status_textbox_manage, f"--- Bắt đầu quá trình xóa {count} profiles ---\n")

            # 1. Cố gắng đóng các tiến trình Chrome liên quan
            update_status(self.status_textbox_manage, "Bước 1: Cố gắng đóng các cửa sổ Chrome đang chạy...\n")
            closed_something = False
            for profile_path in selected:
                update_status(self.status_textbox_manage, f"Kiểm tra profile: {os.path.basename(profile_path)}...\n")
                # Gọi hàm đóng từ utils, truyền status box của tab quản lý
                if close_chrome_process_by_profile(profile_path, self.status_textbox_manage):
                     closed_something = True # Ghi nhận là đã cố gắng đóng (dù có thể không tìm thấy)
                     profiles_to_delete_after_check.append(profile_path) # Thêm vào danh sách sẽ xóa
                else:
                     # Nếu hàm đóng báo lỗi (ví dụ: Access Denied), có thể hỏi người dùng
                     # Hoặc đơn giản là ghi log và không xóa profile đó nữa
                     update_status(self.status_textbox_manage, f"-> Cảnh báo: Không thể đóng tiến trình cho {os.path.basename(profile_path)} hoặc có lỗi. Sẽ không xóa profile này.\n")

            if closed_something:
                 update_status(self.status_textbox_manage, "Chờ vài giây để tiến trình đóng hoàn toàn...\n")
                 # Dùng after thay vì sleep để GUI không bị đơ hoàn toàn
                 # Tuy nhiên, việc xóa file vẫn nên làm ngay sau đó. Sleep ngắn là chấp nhận được.
                 time.sleep(2) # Chờ 2 giây

            # 2. Thực hiện xóa các thư mục profile (chỉ những cái đã qua bước kiểm tra/đóng)
            if profiles_to_delete_after_check:
                update_status(self.status_textbox_manage, "\nBước 2: Thực hiện xóa thư mục profiles...\n")
                deleted_count, errors = delete_profiles(profiles_to_delete_after_check, self.status_textbox_manage) # Gọi hàm từ profile_actions

                if errors:
                    error_display = "\n".join(errors[:5])
                    if len(errors) > 5:
                        error_display += f"\n... (và {len(errors) - 5} lỗi khác, xem console)"
                    tkinter.messagebox.showerror("Lỗi khi xóa", f"Không thể xóa một số thư mục profile:\n\n" + error_display)
            else:
                 update_status(self.status_textbox_manage, "\nKhông có profile nào được xóa (do không tìm thấy hoặc lỗi đóng tiến trình).\n")


            update_status(self.status_textbox_manage, f"--- Kết thúc quá trình xóa ---\n")
            # Làm mới cả hai danh sách sau khi hoàn tất
            self.refresh_profile_list_manage()
            self.refresh_profile_list_script()
        else:
            update_status(self.status_textbox_manage, "Hủy bỏ thao tác xóa.\n")


    def launch_profile(self, profile_path):
        """Mở một profile đơn lẻ."""
        # Gọi hàm từ profile_actions
        launch_profile(profile_path, self.chrome_path, show_error=True, status_textbox=None)

    def select_script_file(self):
        """Mở hộp thoại chọn file script."""
        # ... (Code giữ nguyên) ...
        filetypes = (("Python files", "*.py"), ("All files", "*.*"))
        initial_dir = os.path.dirname(os.path.abspath(__file__))
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


    def clear_pasted_script(self):
        """Xóa nội dung trong ô paste script."""
        # ... (Code giữ nguyên) ...
        print("Yêu cầu xóa nội dung ô script.")
        if hasattr(self, 'script_paste_textbox') and self.script_paste_textbox.winfo_exists():
            self.script_paste_textbox.delete("1.0", tkinter.END)
            update_status(self.status_textbox_script, "Đã xóa nội dung trong ô dán script.\n")
        else:
            print("Lỗi: Không tìm thấy widget script_paste_textbox.")


    def start_script_runner_thread(self):
        """Kiểm tra nguồn script và bắt đầu luồng chạy."""
        # ... (Code giữ nguyên) ...
        selected_profiles = self.get_selected_profiles_script()
        script_content = ""
        if hasattr(self, 'script_paste_textbox') and self.script_paste_textbox.winfo_exists():
             script_content = self.script_paste_textbox.get("1.0", tkinter.END).strip()
        script_to_run_path = None
        temp_file_created_path = None
        if script_content:
            update_status(self.status_textbox_script, "Phát hiện script trong ô text. Sẽ tạo file tạm để chạy.\n")
            try:
                fd, temp_file_created_path = tempfile.mkstemp(suffix='.py', text=True)
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
        if hasattr(self, 'run_script_button') and self.run_script_button.winfo_exists():
             self.run_script_button.configure(state=tkinter.DISABLED)
        if hasattr(self, 'status_textbox_script') and self.status_textbox_script.winfo_exists():
            self.status_textbox_script.delete("1.0", tkinter.END)

        thread = threading.Thread(
            target=run_python_script_threaded,
            args=(script_to_run_path, selected_profiles, self.status_textbox_script, self.run_script_button, temp_file_created_path),
            daemon=True
        )
        thread.start()

    def start_creation_thread(self):
        """Bắt đầu luồng tạo profile."""
        # ... (Code giữ nguyên, truyền self.loaded_ua_list) ...
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
        use_random_ua = self.check_random_ua_var.get()

        if hasattr(self, 'create_button') and self.create_button.winfo_exists():
             self.create_button.configure(state=tkinter.DISABLED)
        if hasattr(self, 'status_textbox_create') and self.status_textbox_create.winfo_exists():
             self.status_textbox_create.delete("1.0", tkinter.END)

        thread = threading.Thread(
            target=create_chrome_profiles_threaded,
            args=(num_profiles, base_dir, use_random_ua,
                  self.status_textbox_create, self.progress_bar, self.create_button,
                  self.loaded_ua_list), # Truyền danh sách đã tải
            daemon=True
        )
        thread.start()


# --- Chạy ứng dụng ---
if __name__ == "__main__":
    # <<< THAY ĐỔI DANH SÁCH DEPENDENCY >>>
    REQUIRED_LIBRARIES = ["selenium", "customtkinter", "webdriver-manager", "psutil"]
    if not check_and_install_dependencies(REQUIRED_LIBRARIES):
        print("Thoát ứng dụng do lỗi dependencies.")
        sys.exit(1)

    import customtkinter

    try:
        local_time = time.localtime()
        print(f"Ứng dụng khởi chạy lúc (giờ hệ thống): {time.strftime('%Y-%m-%d %H:%M:%S', local_time)}")
    except Exception as e_time:
        print(f"Lỗi khi lấy thời gian: {e_time}")

    app = ProfileCreatorApp()
    app.mainloop()
