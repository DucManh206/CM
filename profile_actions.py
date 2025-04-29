# profile_actions.py
import os
import time
import random
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Import các hàm tiện ích cần thiết từ utils
from utils import update_status, LOADED_USER_AGENT_LIST

def create_chrome_profiles_threaded(num_profiles, base_profile_dir, use_random_ua, status_textbox_create, progress_bar, create_button):
    """Hàm tạo hồ sơ Chrome, chạy trong thread, cập nhật vào status box của tab Tạo."""
    try:
        update_status(status_textbox_create, f"Bắt đầu tạo {num_profiles} hồ sơ tại:\n{base_profile_dir}\n")
        if use_random_ua and LOADED_USER_AGENT_LIST:
             update_status(status_textbox_create, f"-> Tùy chọn: Sử dụng User Agent ngẫu nhiên từ file ({len(LOADED_USER_AGENT_LIST)} UAs).\n")
        elif use_random_ua:
             update_status(status_textbox_create, f"-> Cảnh báo: Bật random UA nhưng không tải được UA từ file. Sẽ dùng UA mặc định.\n")

        # Chỉ pack progress bar nếu widget còn tồn tại
        if progress_bar.winfo_exists():
            progress_bar.set(0)
            progress_bar.pack(pady=(10, 5), padx=20, fill="x")
        else:
            print("Cảnh báo: Progress bar không tồn tại khi bắt đầu tạo profile.")


        if not os.path.exists(base_profile_dir):
            try:
                os.makedirs(base_profile_dir)
                update_status(status_textbox_create, f"Đã tạo thư mục gốc: {base_profile_dir}\n")
            except OSError as e:
                update_status(status_textbox_create, f"Lỗi: Không thể tạo thư mục gốc '{base_profile_dir}': {e}\n")
                return # Thoát nếu không tạo được thư mục gốc

        total_profiles = num_profiles
        for i in range(1, total_profiles + 1):
            profile_name = f"Profile_{i:03d}"
            profile_path = os.path.join(base_profile_dir, profile_name)
            update_status(status_textbox_create, f"[{i}/{total_profiles}] Đang xử lý: {profile_path}\n")

            try:
                os.makedirs(profile_path, exist_ok=True)
            except OSError as e:
                update_status(status_textbox_create, f"  Lỗi tạo thư mục '{profile_path}': {e}. Bỏ qua.\n")
                continue

            chrome_options = Options()
            chrome_options.add_argument(f"--user-data-dir={profile_path}")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

            random_ua_string = None
            if use_random_ua and LOADED_USER_AGENT_LIST:
                try:
                    random_ua_string = random.choice(LOADED_USER_AGENT_LIST)
                    chrome_options.add_argument(f'--user-agent={random_ua_string}')
                    update_status(status_textbox_create, f"  -> UA: {random_ua_string[:60]}...\n")
                except Exception as e:
                    update_status(status_textbox_create, f"  Lỗi khi chọn UA ngẫu nhiên: {e}. Dùng UA mặc định.\n")

            driver = None
            try:
                update_status(status_textbox_create, f"  [{i}/{total_profiles}] Khởi chạy Chrome...\n")
                # Giả sử Selenium Manager hoạt động hoặc chromedriver đúng vị trí
                driver = webdriver.Chrome(options=chrome_options)
                time.sleep(1) # Chờ chút để profile khởi tạo
                update_status(status_textbox_create, f"  [{i}/{total_profiles}] -> Hồ sơ '{profile_name}' OK.\n")
            except Exception as e:
                update_status(status_textbox_create, f"  [{i}/{total_profiles}] Lỗi Selenium cho '{profile_name}': {e}\n")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except Exception:
                        print(f"Lỗi nhỏ khi quit driver cho {profile_name}") # Log lỗi nhỏ
                        pass

            # Cập nhật progress bar nếu nó còn tồn tại
            if progress_bar.winfo_exists():
                progress_percentage = i / total_profiles
                progress_bar.set(progress_percentage)

        update_status(status_textbox_create, f"\nHoàn tất! Đã xử lý {total_profiles} hồ sơ.\n")

    except Exception as e:
        update_status(status_textbox_create, f"\nLỗi không xác định trong quá trình tạo: {e}\n")
    finally:
        # Kích hoạt lại nút Create và ẩn progress bar trên main thread
        if create_button.winfo_exists():
             create_button.master.after(0, lambda: create_button.configure(state="normal")) # Sửa state thành "normal"
        if progress_bar.winfo_exists():
             progress_bar.master.after(100, progress_bar.pack_forget)


def launch_profile(profile_path, chrome_path, show_error=True, status_textbox=None):
    """
    Mở một cửa sổ Chrome mới với profile được chỉ định bằng subprocess.

    Args:
        profile_path (str): Đường dẫn đến thư mục profile.
        chrome_path (str or None): Đường dẫn đến file thực thi Chrome.
        show_error (bool): Có hiển thị messagebox khi lỗi không.
        status_textbox (customtkinter.CTkTextbox, optional): Textbox để ghi log.

    Returns:
        bool: True nếu lệnh mở được thực thi, False nếu có lỗi.
    """
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
        command = [chrome_path, f"--user-data-dir={profile_path}"]
        exec_msg = f"  Đang thực thi: {' '.join(command)}\n"
        print(exec_msg.strip())
        if status_textbox: update_status(status_textbox, exec_msg)
        # Sử dụng Popen để không khóa GUI
        subprocess.Popen(command)
        return True # Lệnh đã được gửi đi
    except Exception as e:
        err_msg = f"Lỗi không thể khởi chạy Chrome cho profile:\n{profile_path}\n\nLỗi: {e}"
        print(err_msg)
        if status_textbox: update_status(status_textbox, err_msg + "\n")
        if show_error: tkinter.messagebox.showerror("Lỗi", err_msg)
        return False

def delete_profiles(profile_paths_to_delete, status_textbox_manage):
    """
    Xóa các thư mục profile được chỉ định.

    Args:
        profile_paths_to_delete (list): Danh sách đường dẫn profile cần xóa.
        status_textbox_manage: Textbox để ghi log xóa.

    Returns:
        tuple: (số lượng xóa thành công, danh sách lỗi [str])
    """
    deleted_count = 0
    errors = []
    count = len(profile_paths_to_delete)
    update_status(status_textbox_manage, f"Bắt đầu xóa {count} profiles...\n")
    for profile_path in profile_paths_to_delete:
        try:
            if os.path.isdir(profile_path): # Chỉ xóa nếu là thư mục
                 shutil.rmtree(profile_path)
                 msg = f"-> Đã xóa: {os.path.basename(profile_path)}\n"
                 update_status(status_textbox_manage, msg)
                 print(msg.strip())
                 deleted_count += 1
            else:
                 msg = f"-> Bỏ qua (không phải thư mục): {os.path.basename(profile_path)}\n"
                 update_status(status_textbox_manage, msg)
                 print(msg.strip())
        except OSError as e:
            error_msg = f"Lỗi khi xóa '{os.path.basename(profile_path)}': {e}\n"
            update_status(status_textbox_manage, error_msg)
            print(error_msg.strip())
            errors.append(f"{os.path.basename(profile_path)}: {e}")
        except Exception as e: # Bắt các lỗi khác
            error_msg = f"Lỗi không xác định khi xóa '{os.path.basename(profile_path)}': {e}\n"
            update_status(status_textbox_manage, error_msg)
            print(error_msg.strip())
            errors.append(f"{os.path.basename(profile_path)}: {e}")

    final_msg = f"Đã xóa thành công {deleted_count}/{count} profiles.\n"
    update_status(status_textbox_manage, final_msg)
    print(final_msg.strip())
    return deleted_count, errors