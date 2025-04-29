# profile_actions.py
# -*- coding: utf-8 -*-
import os
import time
import random
import shutil
import tkinter.messagebox # Cần import ở đây nếu launch_profile dùng messagebox
import subprocess # Cần import ở đây nếu launch_profile dùng subprocess
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
             # Cảnh báo này xuất hiện nếu list rỗng HOẶC ua_load_success là False ban đầu
             update_status(status_textbox_create, f"-> Cảnh báo: Bật random UA nhưng không tải được UA từ file hoặc file rỗng. Sẽ dùng UA mặc định.\n")

        # Chỉ hiển thị progress bar nếu widget còn tồn tại
        if progress_bar.winfo_exists():
            progress_bar.set(0)
            # <<< SỬA LỖI GEOMETRY: Dùng grid thay vì pack >>>
            progress_bar.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="ew") # Đặt vào hàng 2
        else:
            print("Cảnh báo: Progress bar không tồn tại khi bắt đầu tạo profile.")


        if not os.path.exists(base_profile_dir):
            try:
                os.makedirs(base_profile_dir)
                update_status(status_textbox_create, f"Đã tạo thư mục gốc: {base_profile_dir}\n")
            except OSError as e:
                update_status(status_textbox_create, f"Lỗi: Không thể tạo thư mục gốc '{base_profile_dir}': {e}\n")
                # Kích hoạt lại nút nếu lỗi ngay từ đầu
                if create_button.winfo_exists():
                    create_button.master.after(0, lambda: create_button.configure(state="normal"))
                return # Thoát nếu không tạo được thư mục gốc

        total_profiles = num_profiles
        for i in range(1, total_profiles + 1):
            # Kiểm tra nút bấm/widget gốc có còn tồn tại không để dừng sớm nếu cần
            if not create_button.winfo_exists():
                print("Nút Tạo hoặc cửa sổ chính đã đóng, dừng tạo profile.")
                break

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
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            # Thêm tùy chọn để cố gắng đóng các process ngầm
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-features=InterestFeedContentSuggestions")


            random_ua_string = None
            if use_random_ua and LOADED_USER_AGENT_LIST:
                try:
                    print(f"DEBUG (profile_actions): Chuẩn bị chọn UA. List length = {len(LOADED_USER_AGENT_LIST)}") # Giữ lại Debug
                    random_ua_string = random.choice(LOADED_USER_AGENT_LIST)
                    chrome_options.add_argument(f'--user-agent={random_ua_string}')
                    update_status(status_textbox_create, f"  -> UA: {random_ua_string[:60]}...\n")
                except IndexError:
                     update_status(status_textbox_create, f"  Lỗi IndexError khi chọn UA ngẫu nhiên: Danh sách rỗng?\n")
                     print("ERROR: IndexError on random.choice! List is empty.")
                except Exception as e:
                    update_status(status_textbox_create, f"  Lỗi khi chọn UA ngẫu nhiên: {e}. Dùng UA mặc định.\n")
                    print(f"ERROR: Exception on random.choice: {e}")

            driver = None
            try:
                update_status(status_textbox_create, f"  [{i}/{total_profiles}] Khởi chạy Chrome...\n")
                # Cân nhắc chỉ định rõ Service nếu Selenium Manager gặp vấn đề
                # from selenium.webdriver.chrome.service import Service
                # service = Service() # Thử không cần executable_path nếu driver trong PATH
                # driver = webdriver.Chrome(service=service, options=chrome_options)
                driver = webdriver.Chrome(options=chrome_options)
                time.sleep(1)
                update_status(status_textbox_create, f"  [{i}/{total_profiles}] -> Hồ sơ '{profile_name}' OK.\n")
            except Exception as e:
                import traceback
                update_status(status_textbox_create, f"  [{i}/{total_profiles}] Lỗi Selenium cho '{profile_name}': {e}\n")
                print(f"ERROR: Lỗi Selenium khi tạo profile {profile_name}:\n{traceback.format_exc()}")
            finally:
                if driver:
                    try:
                        # Thử đóng từng cửa sổ trước khi quit
                        # for handle in driver.window_handles:
                        #    driver.switch_to.window(handle)
                        #    driver.close()
                        # time.sleep(0.5) # Chờ chút
                        driver.quit() # Quit vẫn là cần thiết để đóng chromedriver process
                    except Exception as e_quit:
                        print(f"Lỗi nhỏ khi quit driver cho {profile_name}: {e_quit}")
                        # Cố gắng kill process nếu quit lỗi (nâng cao, cần psutil)
                        # try:
                        #   import psutil
                        #   if driver.service.process:
                        #      process = psutil.Process(driver.service.process.pid)
                        #      for proc in process.children(recursive=True):
                        #           proc.kill()
                        #      process.kill()
                        #      print(f"Đã kill process cho driver lỗi {profile_name}")
                        # except ImportError:
                        #      print("Cần cài 'psutil' để kill process driver lỗi.")
                        # except Exception as e_kill:
                        #      print(f"Lỗi khi kill process driver {profile_name}: {e_kill}")
                        pass

            # Cập nhật progress bar nếu nó còn tồn tại
            if progress_bar.winfo_exists():
                progress_percentage = i / total_profiles
                progress_percentage = max(0.0, min(1.0, progress_percentage))
                progress_bar.set(progress_percentage)

        update_status(status_textbox_create, f"\nHoàn tất! Đã xử lý {total_profiles} hồ sơ.\n")

    except Exception as e:
        import traceback
        update_status(status_textbox_create, f"\nLỗi không xác định trong quá trình tạo: {e}\n")
        print(f"ERROR: Lỗi không xác định trong create_chrome_profiles_threaded:\n{traceback.format_exc()}")
    finally:
        # Kích hoạt lại nút Create và ẩn progress bar trên main thread
        if create_button.winfo_exists():
             create_button.master.after(0, lambda: create_button.configure(state="normal"))
        if progress_bar.winfo_exists():
             # <<< SỬA LỖI GEOMETRY: Dùng grid_forget thay vì pack_forget >>>
             progress_bar.master.after(100, progress_bar.grid_forget) # Phải có ()


def launch_profile(profile_path, chrome_path, show_error=True, status_textbox=None):
    """
    Mở một cửa sổ Chrome mới với profile được chỉ định bằng subprocess.
    """
    # --- Code mở profile giữ nguyên như trước ---
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
            # Thêm cờ này có thể giúp tách biệt process tốt hơn
            # "--disable-features=RendererCodeIntegrity" # Cân nhắc nếu gặp vấn đề treo
            ]
        exec_msg = f"  Đang thực thi: {' '.join(command)}\n"
        print(exec_msg.strip())
        if status_textbox: update_status(status_textbox, exec_msg)
        # Sử dụng Popen để không khóa GUI
        subprocess.Popen(command)
        return True
    except Exception as e:
        err_msg = f"Lỗi không thể khởi chạy Chrome cho profile:\n{profile_path}\n\nLỗi: {e}"
        print(err_msg)
        if status_textbox: update_status(status_textbox, err_msg + "\n")
        if show_error: tkinter.messagebox.showerror("Lỗi", err_msg)
        return False


def delete_profiles(profile_paths_to_delete, status_textbox_manage):
    """
    Xóa các thư mục profile được chỉ định.
    """
    # --- Code xóa profile giữ nguyên như trước ---
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

                 # Thử xóa nhiều lần nếu lỗi (ví dụ: file đang bị khóa tạm thời)
                 max_retries = 3
                 retries = 0
                 while retries < max_retries:
                     try:
                         shutil.rmtree(profile_path)
                         msg = f"-> Đã xóa: {os.path.basename(profile_path)}\n"
                         update_status(status_textbox_manage, msg)
                         print(msg.strip())
                         deleted_count += 1
                         break # Thoát vòng lặp retry nếu thành công
                     except OSError as e_retry:
                         retries += 1
                         if retries >= max_retries:
                              raise e_retry # Ném lại lỗi nếu hết lần thử
                         print(f"Lỗi tạm thời khi xóa '{os.path.basename(profile_path)}' (thử lại {retries}/{max_retries}): {e_retry}")
                         time.sleep(0.5) # Chờ chút trước khi thử lại
            else:
                 msg = f"-> Bỏ qua (không phải thư mục): {os.path.basename(profile_path)}\n"
                 update_status(status_textbox_manage, msg)
                 print(msg.strip())
        except OSError as e: # Lỗi sau khi đã thử lại
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