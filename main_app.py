# main_app.py
# -*- coding: utf-8 -*-
import sys
import os
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import customtkinter
import threading # Cần cho việc chạy tác vụ nền
import time # Cần cho time.strftime

# --- 1. Kiểm tra và Cài đặt Dependencies ---
# Phải thực hiện trước khi import các module khác và thư viện cần kiểm tra
from utils import check_and_install_dependencies
REQUIRED_LIBRARIES = ["selenium", "customtkinter"] # Các thư viện cần thiết cho tool
if not check_and_install_dependencies(REQUIRED_LIBRARIES):
    print("Thoát ứng dụng do thiếu dependencies hoặc lỗi cài đặt.")
    # Không cần sys.exit(1) vì check_and_install_dependencies đã hiển thị lỗi
    # và việc import sau sẽ thất bại nếu cần thiết
    # Tuy nhiên, để chắc chắn, có thể thêm sys.exit(1)
    sys.exit("Lỗi Dependency")


# --- 2. Import các thư viện và module khác ---
# Các thư viện chuẩn
import tempfile # Cần cho việc chạy script từ ô paste

# Các module tự định nghĩa
from gui_setup import setup_create_tab, setup_manage_tab, setup_script_tab
from profile_actions import create_chrome_profiles_threaded, launch_profile, delete_profiles
from script_runner import run_python_script_threaded
from utils import load_user_agents, get_chrome_executable_path, update_status, LOADED_USER_AGENT_LIST # Import các hàm và biến cần thiết

# --- Lớp ứng dụng chính ---
class ProfileCreatorApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Công cụ quản lý hồ sơ Chrome v3 - Modular")
        self.geometry("750x600")

        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")

        # --- Biến dùng chung ---
        self.home_dir = os.path.expanduser("~")
        self.default_profile_path = os.path.join(self.home_dir, "ChromeProfiles")
        self.entry_dir_var = tkinter.StringVar(value=self.default_profile_path)
        self.chrome_path = get_chrome_executable_path() # Gọi hàm từ utils
        self.selected_script_path = None
        self.script_display_var = tkinter.StringVar(value="Chưa chọn file script")

        # --- Biến trạng thái Checkbox (Riêng cho mỗi tab cần) ---
        self.profile_checkbox_vars_manage = {}
        self.profile_checkbox_vars_script = {}

        # --- Tải User Agents ---
        load_user_agents() # Gọi hàm từ utils
        if not self.chrome_path:
             print("Cảnh báo: Không tự động tìm thấy Google Chrome.")
             # Có thể hiển thị cảnh báo trên GUI nếu muốn

        # --- Tạo TabView ---
        self.tab_view = customtkinter.CTkTabview(self)
        self.tab_view.pack(pady=10, padx=10, fill="both", expand=True)
        self.tab_view.add("Tạo Profile")
        self.tab_view.add("Quản lý")
        self.tab_view.add("Script")

        # --- Thiết lập từng tab bằng cách gọi hàm từ gui_setup ---
        # Truyền self (instance của app) vào để các hàm setup có thể gán widget
        # và thiết lập command gọi đến các method của self
        setup_create_tab(self.tab_view.tab("Tạo Profile"), self)
        setup_manage_tab(self.tab_view.tab("Quản lý"), self)
        setup_script_tab(self.tab_view.tab("Script"), self)

        # --- Tải danh sách profile ban đầu ---
        self.refresh_profile_list_manage()
        self.refresh_profile_list_script()


    # --- Các hàm xử lý sự kiện (commands của các nút) ---

    def browse_directory(self):
        """Mở hộp thoại chọn thư mục và cập nhật cho cả 2 tab."""
        initial_dir = self.entry_dir_var.get() if os.path.isdir(self.entry_dir_var.get()) else self.home_dir
        directory = tkinter.filedialog.askdirectory(initialdir=initial_dir)
        if directory:
            self.entry_dir_var.set(directory)
            # Làm mới cả hai danh sách khi đổi thư mục
            self.refresh_profile_list_manage()
            self.refresh_profile_list_script()

    # --- Hàm làm mới danh sách cho tab Quản lý ---
    def refresh_profile_list_manage(self):
        self._refresh_profile_list_internal(self.profile_list_frame_manage, self.profile_checkbox_vars_manage, self.status_textbox_manage)

    # --- Hàm làm mới danh sách cho tab Script ---
    def refresh_profile_list_script(self):
        self._refresh_profile_list_internal(self.profile_list_frame_script, self.profile_checkbox_vars_script, self.status_textbox_script) # Log vào status box của script

    # --- Hàm nội bộ để làm mới danh sách (tránh lặp code) ---
    def _refresh_profile_list_internal(self, target_frame, target_checkbox_dict, status_box_to_update):
        """Hàm helper để làm mới danh sách profile cho một frame cụ thể."""
        # Xóa widget cũ
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
            # Chỉ liệt kê thư mục bắt đầu bằng "Profile_" để tránh thư mục lạ
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if os.path.isdir(item_path) and item.startswith("Profile_"):
                    found_profiles.append((item, item_path))
                elif os.path.isdir(item_path): # Log thư mục không đúng chuẩn nếu cần debug
                    print(f"Debug: Bỏ qua thư mục không đúng định dạng tên: {item}")


            if not found_profiles:
                label_empty = customtkinter.CTkLabel(target_frame, text="(Không tìm thấy profile nào dạng 'Profile_XXX')", text_color="gray")
                label_empty.pack(pady=10, padx=5)
            else:
                found_profiles.sort(key=lambda x: x[0]) # Sắp xếp
                for profile_name, profile_path in found_profiles:
                    item_frame = customtkinter.CTkFrame(target_frame, fg_color="transparent")
                    item_frame.pack(fill="x", pady=(1, 1), padx=(5, 10)) # Giảm pady, tăng padx phải

                    checkbox_var = tkinter.BooleanVar()
                    # Giảm kích thước checkbox nếu có thể (tùy thuộc vào theme)
                    checkbox = customtkinter.CTkCheckBox(item_frame, text="", variable=checkbox_var, width=10, height=10)
                    checkbox.pack(side=tkinter.LEFT, padx=(0, 5))
                    target_checkbox_dict[profile_path] = checkbox_var

                    button = customtkinter.CTkButton(
                        item_frame,
                        text=profile_name,
                        anchor="w",
                        height=24, # Giảm chiều cao nút
                        command=lambda p=profile_path: self.launch_profile(p) # Mở đơn lẻ
                    )
                    button.pack(side=tkinter.LEFT, fill="x", expand=True, padx=0, pady=0)

        except Exception as e:
             label_error = customtkinter.CTkLabel(target_frame, text=f"Lỗi khi đọc thư mục:\n{e}", text_color="red")
             label_error.pack(pady=10, padx=5)
             update_status(status_box_to_update, f"Lỗi refresh list: {e}\n")

    # --- Hàm lấy profile đã chọn cho tab Quản lý ---
    def get_selected_profiles_manage(self):
        selected_paths = []
        for profile_path, var in self.profile_checkbox_vars_manage.items():
            if var.get():
                selected_paths.append(profile_path)
        return selected_paths

    # --- Hàm lấy profile đã chọn cho tab Script ---
    def get_selected_profiles_script(self):
        selected_paths = []
        for profile_path, var in self.profile_checkbox_vars_script.items():
            if var.get():
                selected_paths.append(profile_path)
        return selected_paths

    # --- Hàm xử lý cho các nút ở tab Quản lý ---
    def open_selected_profiles_manage(self):
        selected = self.get_selected_profiles_manage()
        if not selected:
            tkinter.messagebox.showinfo("Thông báo", "Vui lòng chọn ít nhất một profile từ danh sách trên để mở.")
            return
        count = len(selected)
        print(f"Yêu cầu mở hàng loạt {count} profiles từ tab Quản lý...")
        if count > 10: # Giảm cảnh báo xuống 5 profile?
             if not tkinter.messagebox.askyesno("Cảnh báo", f"Bạn sắp mở {count} hồ sơ Chrome cùng lúc. Điều này có thể tốn nhiều tài nguyên. Tiếp tục?"):
                 return
        opened_count = 0
        for profile_path in selected:
            # Gọi hàm launch_profile từ profile_actions, truyền status box của tab quản lý
            if launch_profile(profile_path, self.chrome_path, show_error=False, status_textbox=self.status_textbox_manage):
                opened_count += 1
            else:
                 print(f"-> Bỏ qua mở profile lỗi: {os.path.basename(profile_path)}")
        print(f"Đã cố gắng mở {opened_count}/{count} profiles.")
        if opened_count < count:
             update_status(self.status_textbox_manage, f"Cảnh báo: Đã xảy ra lỗi khi mở một số profile. Kiểm tra log console.\n")

    def delete_selected_profiles_manage(self):
        selected = self.get_selected_profiles_manage()
        if not selected:
            tkinter.messagebox.showinfo("Thông báo", "Vui lòng chọn ít nhất một profile từ danh sách trên để xóa.")
            return
        count = len(selected)
        profile_names = "\n - ".join([os.path.basename(p) for p in selected])
        if tkinter.messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn XÓA VĨNH VIỄN {count} profile sau?\n\n - {profile_names}\n\nHành động này không thể hoàn tác!"):
            # Gọi hàm delete_profiles từ profile_actions
            deleted_count, errors = delete_profiles(selected, self.status_textbox_manage)
            if errors:
                tkinter.messagebox.showerror("Lỗi khi xóa", f"Không thể xóa một số profile:\n\n" + "\n".join(errors))
            # Làm mới cả hai danh sách sau khi xóa
            self.refresh_profile_list_manage()
            self.refresh_profile_list_script()

    # --- Hàm mở profile đơn lẻ (gọi từ nút trong danh sách) ---
    def launch_profile(self, profile_path):
        """Mở một profile đơn lẻ khi nhấn nút tương ứng."""
        # Gọi hàm launch_profile từ profile_actions, không ghi log vào status box cụ thể
        launch_profile(profile_path, self.chrome_path, show_error=True, status_textbox=None)

    # --- Hàm xử lý cho các nút ở tab Script ---
    def select_script_file(self):
        """Mở hộp thoại để chọn file script Python (.py)."""
        filetypes = (("Python files", "*.py"), ("All files", "*.*"))
        filepath = tkinter.filedialog.askopenfilename(
            title="Chọn file script Python",
            initialdir=os.getcwd(),
            filetypes=filetypes
        )
        if filepath:
            self.selected_script_path = filepath
            self.script_display_var.set(os.path.basename(filepath))
            if self.script_paste_textbox.winfo_exists(): # Xóa ô paste nếu chọn file
                self.script_paste_textbox.delete("1.0", tkinter.END)
            update_status(self.status_textbox_script, f"Đã chọn file script: {filepath}\n")
        # Không làm gì nếu người dùng hủy

    def start_script_runner_thread(self):
        """Kiểm tra nguồn script và bắt đầu luồng chạy."""
        selected_profiles = self.get_selected_profiles_script() # Lấy từ tab script
        script_content = ""
        if self.script_paste_textbox.winfo_exists(): # Lấy nội dung từ ô paste nếu có
             script_content = self.script_paste_textbox.get("1.0", tkinter.END).strip()

        script_to_run_path = None
        temp_file_created_path = None

        # Ưu tiên Textbox
        if script_content:
            update_status(self.status_textbox_script, "Phát hiện script trong ô text. Sẽ tạo file tạm để chạy.\n")
            try:
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, encoding='utf-8') as temp_file:
                    temp_file.write(script_content)
                    temp_file_created_path = temp_file.name
                    script_to_run_path = temp_file_created_path
                print(f"Đã tạo file tạm: {script_to_run_path}")
            except Exception as e:
                tkinter.messagebox.showerror("Lỗi tạo file tạm", f"Không thể tạo file script tạm thời:\n{e}")
                return
        # Nếu Textbox trống, dùng file đã chọn
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

        # Cảnh báo bảo mật
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

        # Vô hiệu hóa nút và xóa status box script
        self.run_script_button.configure(state=tkinter.DISABLED)
        self.status_textbox_script.delete("1.0", tkinter.END)

        # Bắt đầu thread, truyền đúng status box và nút, gọi hàm từ script_runner
        thread = threading.Thread(
            target=run_python_script_threaded, # Gọi hàm từ module script_runner
            args=(script_to_run_path, selected_profiles, self.status_textbox_script, self.run_script_button, temp_file_created_path),
            daemon=True
        )
        thread.start()

    # --- Hàm xử lý cho tab Tạo Profile ---
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
        use_random_ua = self.check_random_ua_var.get()

        self.create_button.configure(state=tkinter.DISABLED)
        self.status_textbox_create.delete("1.0", tkinter.END)

        # Bắt đầu thread, truyền đúng status box và nút, gọi hàm từ profile_actions
        thread = threading.Thread(
            target=create_chrome_profiles_threaded, # Gọi hàm từ module profile_actions
            args=(num_profiles, base_dir, use_random_ua, self.status_textbox_create, self.progress_bar, self.create_button),
            daemon=True
        )
        thread.start()
        # Sau khi tạo xong, có thể tự động gọi refresh ở đây nếu muốn, nhưng cần đợi thread hoàn thành
        # self.after(100, self._check_creation_thread_and_refresh, thread) # Ví dụ cách phức tạp hơn


# --- Chạy ứng dụng ---
if __name__ == "__main__":
    # 1. Kiểm tra Dependencies trước tiên
    REQUIRED_LIBRARIES = ["selenium", "customtkinter"]
    if not check_and_install_dependencies(REQUIRED_LIBRARIES):
        print("Thoát ứng dụng do lỗi dependencies.")
        sys.exit(1)

    # 2. Nếu dependencies OK, thì mới import và chạy app
    import customtkinter # Import sau khi kiểm tra

    try:
        local_time = time.localtime()
        print(f"Ứng dụng khởi chạy lúc (giờ hệ thống): {time.strftime('%Y-%m-%d %H:%M:%S', local_time)}")
    except Exception as e_time:
        print(f"Lỗi khi lấy thời gian: {e_time}")

    # 3. Khởi tạo và chạy App
    app = ProfileCreatorApp()
    app.mainloop()