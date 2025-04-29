# profile_actions.py
# -*- coding: utf-8 -*-
import os
import time
import random
import shutil
import tkinter.messagebox
import subprocess
import traceback # Import traceback để in lỗi chi tiết
from selenium import webdriver
# <<< THÊM IMPORT CHO WEBDRIVER-MANAGER >>>
from selenium.webdriver.chrome.service import Service as ChromeService
try:
    # Thử import webdriver_manager
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    # Nếu không có, đặt cờ thành False
    WEBDRIVER_MANAGER_AVAILABLE = False
    print("Cảnh báo: Thư viện 'webdriver-manager' chưa được cài đặt.")
    print("         Sẽ sử dụng cơ chế mặc định của Selenium (Selenium Manager).")
    print("         Để quản lý driver tốt hơn, hãy chạy: pip install webdriver-manager")
# <<< KẾT THÚC THÊM IMPORT >>>

from selenium.webdriver.chrome.options import Options

# Import từ utils
from utils import update_status # Chỉ cần update_status

def find_max_profile_number(base_profile_dir):
    # ... (Giữ nguyên code) ...
    max_num = 0
    import re
    profile_pattern = re.compile(r"^Profile_(\d+)$")
    try:
        if os.path.isdir(base_profile_dir):
            for item in os.listdir(base_profile_dir):
                item_path = os.path.join(base_profile_dir, item)
                if os.path.isdir(item_path):
                    match = profile_pattern.match(item)
                    if match:
                        try:
                            num = int(match.group(1))
                            max_num = max(max_num, num)
                        except ValueError: continue
    except Exception as e:
        print(f"Warning: Lỗi khi quét tìm số profile lớn nhất: {e}")
    return max_num

def create_chrome_profiles_threaded(num_profiles_to_create, base_profile_dir, use_random_ua,
                                    status_textbox_create, progress_bar, create_button,
                                    loaded_ua_list_arg):
    """Hàm tạo hồ sơ Chrome, sử dụng webdriver-manager nếu có."""
    try:
        max_existing_num = find_max_profile_number(base_profile_dir)
        start_profile_num = max_existing_num + 1
        end_profile_num = start_profile_num + num_profiles_to_create - 1

        update_status(status_textbox_create, f"Bắt đầu tạo {num_profiles_to_create} hồ sơ tại:\n{base_profile_dir}\n")
        update_status(status_textbox_create, f"Tìm thấy số profile cao nhất là {max_existing_num}. Bắt đầu tạo từ số {start_profile_num}.\n")

        ua_list_available = bool(loaded_ua_list_arg)
        ua_list_count = len(loaded_ua_list_arg) if ua_list_available else 0

        if use_random_ua and ua_list_available:
             update_status(status_textbox_create, f"-> Tùy chọn: Sử dụng User Agent ngẫu nhiên từ danh sách ({ua_list_count} UAs).\n")
        elif use_random_ua:
             update_status(status_textbox_create, f"-> Cảnh báo: Bật random UA nhưng danh sách UA rỗng/lỗi tải. Sẽ dùng UA mặc định.\n")

        if progress_bar.winfo_exists():
            progress_bar.set(0)
            progress_bar.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="ew")
        else:
            print("Cảnh báo: Progress bar không tồn tại khi bắt đầu tạo profile.")

        if not os.path.exists(base_profile_dir):
             # ... (code tạo thư mục gốc giữ nguyên) ...
            try:
                os.makedirs(base_profile_dir)
                update_status(status_textbox_create, f"Đã tạo thư mục gốc: {base_profile_dir}\n")
            except OSError as e:
                update_status(status_textbox_create, f"Lỗi: Không thể tạo thư mục gốc '{base_profile_dir}': {e}\n")
                if create_button.winfo_exists():
                    create_button.master.after(0, lambda: create_button.configure(state="normal"))
                return


        profiles_actually_created = 0
        for i in range(num_profiles_to_create):
            # ... (code tính profile_name, profile_path, kiểm tra tồn tại, tạo thư mục giữ nguyên) ...
            if not create_button.winfo_exists():
                print("Nút Tạo hoặc cửa sổ chính đã đóng, dừng tạo profile.")
                break
            current_profile_number = start_profile_num + i
            profile_name = f"Profile_{current_profile_number:03d}"
            profile_path = os.path.join(base_profile_dir, profile_name)
            update_status(status_textbox_create, f"[{i+1}/{num_profiles_to_create}] Đang xử lý: {profile_path}\n")
            if os.path.exists(profile_path):
                 update_status(status_textbox_create, f"  Cảnh báo: Thư mục '{profile_name}' đã tồn tại. Bỏ qua tạo mới.\n")
                 continue
            try:
                os.makedirs(profile_path)
            except OSError as e:
                update_status(status_textbox_create, f"  Lỗi tạo thư mục '{profile_path}': {e}. Bỏ qua.\n")
                continue

            # --- Cấu hình Chrome Options ---
            chrome_options = Options()
            chrome_options.add_argument(f"--user-data-dir={profile_path}")
            # ... (các options khác giữ nguyên) ...
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-features=InterestFeedContentSuggestions")

            if use_random_ua and ua_list_available:
                # ... (code random UA giữ nguyên) ...
                try:
                    random_ua_string = random.choice(loaded_ua_list_arg)
                    chrome_options.add_argument(f'--user-agent={random_ua_string}')
                    update_status(status_textbox_create, f"  -> UA: {random_ua_string[:60]}...\n")
                except Exception as e:
                    update_status(status_textbox_create, f"  Lỗi khi chọn UA ngẫu nhiên: {e}. Dùng UA mặc định.\n")


            # --- Khởi tạo WebDriver ---
            driver = None
            selenium_success = False
            try:
                update_status(status_textbox_create, f"  [{i+1}/{num_profiles_to_create}] Khởi chạy Chrome...\n")

                # <<< THAY ĐỔI CÁCH KHỞI TẠO WEBDRIVER >>>
                if WEBDRIVER_MANAGER_AVAILABLE:
                    try:
                        update_status(status_textbox_create, "    -> Sử dụng webdriver-manager để lấy driver...\n")
                        # Tự động tải/cập nhật và lấy đường dẫn chromedriver
                        service = ChromeService(ChromeDriverManager().install())
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        print("WebDriver khởi tạo bằng webdriver-manager.")
                    except Exception as e_wdm:
                        update_status(status_textbox_create, f"    -> Lỗi webdriver-manager: {e_wdm}. Thử Selenium Manager...\n")
                        print(f"Warning: Lỗi khi dùng webdriver-manager: {e_wdm}. Fallback to Selenium Manager.")
                        # Thử fallback về Selenium Manager nếu webdriver-manager lỗi
                        driver = webdriver.Chrome(options=chrome_options)
                        print("WebDriver khởi tạo bằng Selenium Manager (fallback).")
                else:
                     # Nếu webdriver-manager không có sẵn, dùng Selenium Manager mặc định
                     update_status(status_textbox_create, "    -> Sử dụng Selenium Manager (mặc định)...\n")
                     driver = webdriver.Chrome(options=chrome_options)
                     print("WebDriver khởi tạo bằng Selenium Manager (do webdriver-manager không có sẵn).")
                # <<< KẾT THÚC THAY ĐỔI >>>

                time.sleep(1) # Chờ chút
                update_status(status_textbox_create, f"  [{i+1}/{num_profiles_to_create}] -> Hồ sơ '{profile_name}' OK.\n")
                selenium_success = True
            except Exception as e:
                update_status(status_textbox_create, f"  [{i+1}/{num_profiles_to_create}] Lỗi Selenium cho '{profile_name}': {e}\n")
                print(f"ERROR: Lỗi Selenium khi tạo profile {profile_name}:\n{traceback.format_exc()}")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception as e_quit:
                        print(f"Lỗi nhỏ khi quit driver cho {profile_name}: {e_quit}")
                        pass

            if selenium_success:
                 profiles_actually_created += 1

            if progress_bar.winfo_exists():
                # ... (cập nhật progress bar giữ nguyên) ...
                progress_percentage = (i + 1) / num_profiles_to_create
                progress_percentage = max(0.0, min(1.0, progress_percentage))
                progress_bar.set(progress_percentage)


        update_status(status_textbox_create, f"\nHoàn tất! Đã tạo {profiles_actually_created}/{num_profiles_to_create} hồ sơ yêu cầu (từ số {start_profile_num} đến {end_profile_num}).\n")

    except Exception as e:
        # ... (xử lý lỗi chung) ...
        update_status(status_textbox_create, f"\nLỗi không xác định trong quá trình tạo: {e}\n")
        print(f"ERROR: Lỗi không xác định trong create_chrome_profiles_threaded:\n{traceback.format_exc()}")
    finally:
        # ... (kích hoạt lại nút, ẩn progress bar) ...
        if create_button.winfo_exists():
             create_button.master.after(0, lambda: create_button.configure(state="normal"))
        if progress_bar.winfo_exists():
             progress_bar.master.after(100, progress_bar.grid_forget)


# --- Hàm launch_profile (Giữ nguyên) ---
def launch_profile(profile_path, chrome_path, show_error=True, status_textbox=None):
    # ... (code giữ nguyên) ...
    message = f"Yêu cầu mở profile: {profile_path}\n"
    print(message.strip())
    if status_textbox: update_status(status_textbox, message)
    if not chrome_path:
        err_msg = "Lỗi: Không tìm thấy đường dẫn thực thi của Google Chrome."
        print(err_msg)
        if status_textbox: update_status(status_textbox, err_msg + "\n")
        if show_error: tkinter.messagebox.showerror("Lỗi", err_msg)
        return False
    if not os.path.isdir(profile_path):
         err_msg = f"Lỗi: Thư mục profile không tồn tại:\n{profile_path}"
         print(err_msg)
         if status_textbox: update_status(status_textbox, err_msg + "\n")
         if show_error: tkinter.messagebox.showerror("Lỗi", err_msg)
         return False
    try:
        command = [
            chrome_path,
            f"--user-data-dir={profile_path}",
            "--no-first-run",
            "--no-default-browser-check",
            ]
        exec_msg = f"  Đang thực thi: {' '.join(command)}\n"
        print(exec_msg.strip())
        if status_textbox: update_status(status_textbox, exec_msg)
        subprocess.Popen(command)
        return True
    except Exception as e:
        err_msg = f"Lỗi không thể khởi chạy Chrome cho profile:\n{profile_path}\n\nLỗi: {e}"
        print(err_msg)
        if status_textbox: update_status(status_textbox, err_msg + "\n")
        if show_error: tkinter.messagebox.showerror("Lỗi", err_msg)
        return False

# --- Hàm delete_profiles (Giữ nguyên) ---
def delete_profiles(profile_paths_to_delete, status_textbox_manage):
    # ... (code giữ nguyên) ...
    deleted_count = 0
    errors = []
    count = len(profile_paths_to_delete)
    update_status(status_textbox_manage, f"Bắt đầu xóa {count} profiles...\n")
    for profile_path in profile_paths_to_delete:
        try:
            if os.path.isdir(profile_path):
                 if not os.path.basename(profile_path).startswith("Profile_"):
                      msg = f"-> Cảnh báo: Tên thư mục '{os.path.basename(profile_path)}' không đúng chuẩn 'Profile_'. Bỏ qua xóa.\n"
                      update_status(status_textbox_manage, msg)
                      print(msg.strip())
                      errors.append(f"{os.path.basename(profile_path)}: Tên không hợp lệ")
                      continue
                 max_retries = 3
                 retries = 0
                 while retries < max_retries:
                     try:
                         shutil.rmtree(profile_path)
                         msg = f"-> Đã xóa: {os.path.basename(profile_path)}\n"
                         update_status(status_textbox_manage, msg)
                         print(msg.strip())
                         deleted_count += 1
                         break
                     except OSError as e_retry:
                         retries += 1
                         if retries >= max_retries:
                              raise e_retry
                         print(f"Lỗi tạm thời khi xóa '{os.path.basename(profile_path)}' (thử lại {retries}/{max_retries}): {e_retry}")
                         time.sleep(0.5)
            else:
                 msg = f"-> Bỏ qua (không phải thư mục): {os.path.basename(profile_path)}\n"
                 update_status(status_textbox_manage, msg)
                 print(msg.strip())
        except OSError as e:
            error_msg = f"Lỗi khi xóa '{os.path.basename(profile_path)}': {e}\n"
            update_status(status_textbox_manage, error_msg)
            print(error_msg.strip())
            errors.append(f"{os.path.basename(profile_path)}: {e}")
        except Exception as e:
            error_msg = f"Lỗi không xác định khi xóa '{os.path.basename(profile_path)}': {e}\n"
            update_status(status_textbox_manage, error_msg)
            print(error_msg.strip())
            errors.append(f"{os.path.basename(profile_path)}: {e}")
    final_msg = f"Đã xóa thành công {deleted_count}/{count} profiles.\n"
    update_status(status_textbox_manage, final_msg)
    print(final_msg.strip())
    return deleted_count, errors
