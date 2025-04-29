# utils.py
# -*- coding: utf-8 -*-
import os
import sys
import shutil
import importlib.util
import subprocess
import tkinter.messagebox
import tkinter
import psutil # <<< Thêm import psutil

# --- Biến toàn cục cho User Agents ---
UA_FILENAME = "user_agents.txt"

def load_user_agents():
    # ... (Giữ nguyên code tải UA như trước) ...
    loaded_list = []
    try:
        utils_dir = os.path.dirname(os.path.abspath(__file__))
        ua_file_path = os.path.join(utils_dir, UA_FILENAME)
        print(f"Đang đọc User Agents từ: {ua_file_path}")
        if not os.path.exists(ua_file_path):
             print(f"Lỗi: File không tồn tại '{ua_file_path}'")
             return []
        with open(ua_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                ua = line.strip()
                if ua and not ua.startswith("#"):
                    loaded_list.append(ua)
        if loaded_list:
            print(f"Đã tải thành công {len(loaded_list)} User Agents.")
        else:
            print(f"Cảnh báo: File '{UA_FILENAME}' trống hoặc chỉ chứa comment.")
        return loaded_list
    except FileNotFoundError:
        print(f"Lỗi FileNotFoundError: Không tìm thấy file '{UA_FILENAME}' tại '{ua_file_path}'.")
        return []
    except Exception as e:
        import traceback
        print(f"Lỗi không xác định khi đọc file User Agent: {e}\n{traceback.format_exc()}")
        return []

# --- Hàm tìm Chrome (Giữ nguyên) ---
def get_chrome_executable_path():
    # ... (Giữ nguyên code) ...
    chrome_executable = None
    try:
        if sys.platform == "win32":
            chrome_executable = shutil.which("chrome.exe")
        elif sys.platform == "darwin":
             chrome_executable = shutil.which("Google Chrome")
             if not chrome_executable:
                 default_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                 if os.path.exists(default_path):
                     chrome_executable = default_path
        elif sys.platform.startswith("linux"):
            chrome_executable = shutil.which("google-chrome") or shutil.which("chrome")
        if not chrome_executable and sys.platform == "win32":
            possible_paths = [
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Google\\Chrome\\Application\\chrome.exe"),
                os.path.join(os.environ.get("LocalAppData", ""), "Google\\Chrome\\Application\\chrome.exe"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    chrome_executable = path
                    break
    except Exception as e:
        print(f"Lỗi khi tìm Chrome: {e}")
    if chrome_executable:
        print(f"Đã tìm thấy Chrome tại: {chrome_executable}")
    else:
        print("Không tìm thấy Chrome executable.")
    return chrome_executable

# --- Hàm update_status (Giữ nguyên) ---
def update_status(textbox, message):
    # ... (Giữ nguyên code) ...
    def _update():
        safe_message = str(message)
        if textbox.winfo_exists():
            textbox.insert(tkinter.END, safe_message)
            textbox.see(tkinter.END)
        else:
            print(f"Cảnh báo update_status: Textbox không còn tồn tại.")
    try:
        widget_to_schedule_on = textbox
        while widget_to_schedule_on.master is not None and hasattr(widget_to_schedule_on.master, 'after'):
            widget_to_schedule_on = widget_to_schedule_on.master
            if isinstance(widget_to_schedule_on, (tkinter.Tk, tkinter.Toplevel)) or not widget_to_schedule_on.winfo_exists():
                 break
        if widget_to_schedule_on.winfo_exists():
             widget_to_schedule_on.after(0, _update)
        elif textbox.winfo_exists():
             textbox.after(0, _update)
        else:
             print(f"Cảnh báo update_status: Không thể lên lịch cập nhật cho textbox đã bị hủy.")
    except Exception as e:
        import traceback
        print(f"Lỗi trong update_status khi gọi after: {e}\n{traceback.format_exc()}")

# --- Hàm check_and_install_dependencies (Thêm thư viện mới) ---
def check_and_install_dependencies(required_libs):
    """Kiểm tra và cài đặt dependencies."""
    # ... (Phần lớn code giữ nguyên, chỉ thay đổi list và thông báo nếu cần) ...
    all_ok = True
    missing_libs = []
    print("--- Kiểm tra Dependencies ---")
    for lib_name in required_libs:
        try:
            spec = importlib.util.find_spec(lib_name)
            if spec is None:
                print(f"-> Thư viện '{lib_name}' bị thiếu.")
                missing_libs.append(lib_name)
            else:
                print(f"-> Thư viện '{lib_name}' đã được cài đặt.")
        except ModuleNotFoundError:
             print(f"-> Thư viện '{lib_name}' bị thiếu (ModuleNotFoundError).")
             missing_libs.append(lib_name)
        except Exception as e:
             print(f"Lỗi khi kiểm tra thư viện '{lib_name}': {e}")
             missing_libs.append(lib_name)
    if not missing_libs:
        print("Tất cả dependencies cần thiết đã có.")
        return True
    libs_str = ", ".join(missing_libs)
    root = None
    user_confirm = False
    try:
        root = tkinter.Tk()
        root.withdraw()
        user_confirm = tkinter.messagebox.askyesno(
            "Thiếu Dependencies",
            f"Các thư viện sau bị thiếu: {libs_str}\n\n"
            f"Bạn có muốn tự động cài đặt chúng bằng pip không?\n"
            f"(Yêu cầu kết nối internet và quyền cài đặt)"
        )
    except Exception as e:
        print(f"Lỗi hiển thị messagebox hỏi cài đặt: {e}. Giả sử người dùng từ chối.")
    finally:
        if root:
            root.destroy()
    if not user_confirm:
        print("Người dùng đã từ chối cài đặt tự động.")
        root_err = None
        try:
            root_err = tkinter.Tk()
            root_err.withdraw()
            tkinter.messagebox.showerror("Lỗi Dependencies", f"Không thể tiếp tục vì thiếu thư viện: {libs_str}\nVui lòng cài đặt thủ công bằng lệnh:\npip install {' '.join(missing_libs)}")
        except Exception as e:
             print(f"Lỗi hiển thị messagebox lỗi dependencies: {e}")
        finally:
            if root_err:
                root_err.destroy()
        return False
    print(f"\n--- Bắt đầu cài đặt thư viện bị thiếu: {libs_str} ---")
    for lib_name in missing_libs:
        print(f"\nĐang cài đặt '{lib_name}'...")
        try:
            command = [sys.executable, "-m", "pip", "install", lib_name]
            print(f"Executing: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', check=False, timeout=300)
            if result.returncode == 0:
                print(f"-> Cài đặt '{lib_name}' thành công!")
                importlib.invalidate_caches()
            else:
                all_ok = False
                print(f"*** Lỗi khi cài đặt '{lib_name}' ***")
                print("--- Pip Output (Last 1000 chars) ---")
                print(result.stdout[-1000:])
                print("--- Pip Error (Last 1000 chars) ---")
                print(result.stderr[-1000:])
                print("------------------------------------")
                root_err_pip=None
                try:
                    root_err_pip = tkinter.Tk()
                    root_err_pip.withdraw()
                    tkinter.messagebox.showerror("Lỗi Cài Đặt", f"Không thể tự động cài đặt '{lib_name}'.\nLỗi pip (kiểm tra console).\n\nVui lòng thử cài đặt thủ công:\npip install {lib_name}")
                except Exception as e:
                     print(f"Lỗi hiển thị messagebox lỗi pip: {e}")
                finally:
                    if root_err_pip:
                        root_err_pip.destroy()
        except subprocess.TimeoutExpired:
            all_ok = False
            print(f"Lỗi: Cài đặt '{lib_name}' vượt quá thời gian chờ.")
            root_err_timeout=None
            try:
                root_err_timeout = tkinter.Tk()
                root_err_timeout.withdraw()
                tkinter.messagebox.showerror("Lỗi Cài Đặt", f"Quá trình cài đặt '{lib_name}' mất quá nhiều thời gian.\nKiểm tra mạng và thử cài đặt thủ công.")
            except Exception as e:
                 print(f"Lỗi hiển thị messagebox timeout: {e}")
            finally:
                if root_err_timeout:
                    root_err_timeout.destroy()
        except Exception as e:
            all_ok = False
            print(f"Lỗi nghiêm trọng khi chạy pip cho '{lib_name}': {e}")
            root_err_sys=None
            try:
                root_err_sys = tkinter.Tk()
                root_err_sys.withdraw()
                tkinter.messagebox.showerror("Lỗi Cài Đặt", f"Lỗi hệ thống khi cố gắng cài đặt '{lib_name}':\n{e}\n\nVui lòng thử cài đặt thủ công.")
            except Exception as e_msg:
                 print(f"Lỗi hiển thị messagebox lỗi hệ thống: {e_msg}")
            finally:
                if root_err_sys:
                    root_err_sys.destroy()
    if all_ok:
        print("\n--- Hoàn tất cài đặt dependencies ---")
        root_ok = None
        try:
            root_ok = tkinter.Tk()
            root_ok.withdraw()
            tkinter.messagebox.showinfo("Cài đặt thành công", "Các thư viện cần thiết đã được cài đặt.\nBạn có thể cần khởi động lại ứng dụng để thay đổi có hiệu lực hoàn toàn.")
        except Exception as e:
             print(f"Lỗi hiển thị messagebox thành công: {e}")
        finally:
            if root_ok:
                root_ok.destroy()
    else:
         print("\n*** Có lỗi xảy ra trong quá trình cài đặt dependencies ***")
    return all_ok

# --- Hàm mới: Đóng tiến trình Chrome theo Profile Path ---
def close_chrome_process_by_profile(profile_path, status_textbox=None):
    """
    Cố gắng tìm và đóng tiến trình Chrome đang sử dụng profile_path cụ thể.

    Args:
        profile_path (str): Đường dẫn tuyệt đối đến thư mục profile.
        status_textbox: Textbox để ghi log (tùy chọn).

    Returns:
        bool: True nếu tìm thấy và cố gắng đóng thành công, False nếu không tìm thấy hoặc lỗi.
    """
    if not psutil: # Kiểm tra xem psutil đã được import thành công chưa
        msg = "Lỗi: Thư viện 'psutil' không khả dụng để đóng tiến trình Chrome."
        print(msg)
        if status_textbox: update_status(status_textbox, msg + "\n")
        return False

    target_arg = f"--user-data-dir={profile_path}"
    # Chuẩn hóa đường dẫn để so sánh tốt hơn (ví dụ: xử lý dấu / và \)
    normalized_target_arg = f"--user-data-dir={os.path.normpath(profile_path)}"
    found_process = None
    process_closed = False

    print(f"Đang tìm tiến trình Chrome sử dụng: {normalized_target_arg}")
    if status_textbox: update_status(status_textbox, f"Đang tìm tiến trình cho profile: {os.path.basename(profile_path)}...\n")

    try:
        # Lặp qua các tiến trình đang chạy
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'username']):
            try:
                # Lấy thông tin tiến trình, bỏ qua nếu lỗi (vd: process đã chết)
                cmdline = proc.info.get('cmdline')
                proc_name = proc.info.get('name', '').lower()

                # Kiểm tra tên tiến trình (có thể khác nhau tùy HĐH)
                is_chrome = 'chrome' in proc_name

                if is_chrome and cmdline:
                    # Kiểm tra command line arguments
                    normalized_cmdline = [os.path.normpath(arg) for arg in cmdline]
                    # print(f"DEBUG: Checking PID {proc.info['pid']} - Cmdline: {' '.join(normalized_cmdline)}") # Debug nếu cần
                    if normalized_target_arg in normalized_cmdline:
                        found_process = proc
                        print(f"Tìm thấy tiến trình Chrome (PID: {found_process.pid}, User: {proc.info.get('username')}) khớp với profile.")
                        if status_textbox: update_status(status_textbox, f"  -> Tìm thấy tiến trình PID: {found_process.pid}. Đang thử đóng...\n")
                        break # Tìm thấy là đủ

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue # Bỏ qua các process không truy cập được hoặc đã chết
            except Exception as e_iter:
                 print(f"Lỗi nhỏ khi lặp qua tiến trình: {e_iter}") # Ghi log lỗi nhỏ

        # Nếu tìm thấy, cố gắng đóng
        if found_process:
            try:
                print(f"Đang thử terminate PID: {found_process.pid}")
                found_process.terminate() # Gửi tín hiệu đóng nhẹ nhàng trước
                try:
                    # Chờ tối đa 2 giây xem nó có tự đóng không
                    found_process.wait(timeout=2)
                    print(f"PID {found_process.pid} đã tự đóng sau terminate.")
                    process_closed = True
                    if status_textbox: update_status(status_textbox, f"  -> Đã đóng tiến trình PID: {found_process.pid} (terminate).\n")
                except psutil.TimeoutExpired:
                     # Nếu vẫn chạy sau 2 giây, kill mạnh
                     print(f"PID {found_process.pid} không đóng sau terminate. Đang thử kill...")
                     found_process.kill()
                     found_process.wait(timeout=1) # Chờ chút sau khi kill
                     print(f"PID {found_process.pid} đã bị kill.")
                     process_closed = True
                     if status_textbox: update_status(status_textbox, f"  -> Đã đóng tiến trình PID: {found_process.pid} (kill).\n")
            except psutil.NoSuchProcess:
                print(f"PID {found_process.pid} đã đóng trước khi kịp xử lý.")
                process_closed = True # Coi như đã đóng thành công
                if status_textbox: update_status(status_textbox, f"  -> Tiến trình PID: {found_process.pid} đã tự đóng.\n")
            except psutil.AccessDenied:
                 err_msg = f"Lỗi: Không có quyền đóng tiến trình Chrome (PID: {found_process.pid}).\n"
                 print(err_msg)
                 if status_textbox: update_status(status_textbox, err_msg)
            except Exception as e_close:
                 err_msg = f"Lỗi không xác định khi đóng tiến trình (PID: {found_process.pid}): {e_close}\n"
                 print(err_msg)
                 if status_textbox: update_status(status_textbox, err_msg)
        else:
            msg = f"Không tìm thấy tiến trình Chrome nào đang chạy với profile này.\n"
            print(msg.strip())
            if status_textbox: update_status(status_textbox, msg)
            # Không tìm thấy cũng không phải là lỗi trong ngữ cảnh này
            process_closed = True # Coi như không cần đóng

    except Exception as e_main:
        # Lỗi chung khi tìm kiếm process
        err_msg = f"Lỗi khi sử dụng psutil để tìm tiến trình: {e_main}\n"
        print(err_msg)
        if status_textbox: update_status(status_textbox, err_msg)

    return process_closed # Trả về True nếu đã đóng hoặc không tìm thấy, False nếu lỗi quyền/lỗi khác
