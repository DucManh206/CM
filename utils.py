# utils.py
# -*- coding: utf-8 -*-
import os
import sys
import shutil
import importlib.util
import subprocess
import tkinter.messagebox
import tkinter # Cần cho root tạm thời của messagebox

# --- Biến toàn cục cho User Agents ---
LOADED_USER_AGENT_LIST = []
UA_FILENAME = "user_agents.txt"

def load_user_agents():
    """Tải danh sách User Agent từ file vào biến toàn cục."""
    global LOADED_USER_AGENT_LIST
    LOADED_USER_AGENT_LIST = [] # Reset trước khi tải
    try:
        utils_dir = os.path.dirname(os.path.abspath(__file__))
        ua_file_path = os.path.join(utils_dir, UA_FILENAME)

        print(f"Đang đọc User Agents từ: {ua_file_path}")
        with open(ua_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                ua = line.strip()
                if ua and not ua.startswith("#"):
                    LOADED_USER_AGENT_LIST.append(ua)

        if LOADED_USER_AGENT_LIST:
            print(f"Đã tải thành công {len(LOADED_USER_AGENT_LIST)} User Agents.")
            return True
        else:
            print(f"Cảnh báo: File '{UA_FILENAME}' trống hoặc chỉ chứa comment.")
            return False
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file '{UA_FILENAME}' trong cùng thư mục với utils.py.")
        print(f"(Thư mục hiện tại được kiểm tra: {os.path.dirname(os.path.abspath(__file__))})")
        return False
    except Exception as e:
        print(f"Lỗi không xác định khi đọc file User Agent: {e}")
        return False

def get_chrome_executable_path():
    """Cố gắng tìm đường dẫn đến file thực thi của Google Chrome."""
    chrome_executable = None
    try:
        if sys.platform == "win32":
            chrome_executable = shutil.which("chrome.exe")
        elif sys.platform == "darwin": # macOS
             chrome_executable = shutil.which("Google Chrome")
             if not chrome_executable:
                 default_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                 if os.path.exists(default_path):
                     chrome_executable = default_path
        elif sys.platform.startswith("linux"):
            chrome_executable = shutil.which("google-chrome") or shutil.which("chrome")

        # Fallback cho Windows nếu không có trong PATH
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

def update_status(textbox, message):
    """Cập nhật nội dung cho CTkTextbox một cách an toàn từ các thread."""
    def _update():
        safe_message = str(message)
        if textbox.winfo_exists():
            textbox.insert(tkinter.END, safe_message)
            textbox.see(tkinter.END)
        else:
            print(f"Cảnh báo update_status: Textbox không còn tồn tại.")

    try:
        # Lấy widget gốc (master) một cách an toàn hơn
        widget_to_schedule_on = textbox
        while widget_to_schedule_on.master is not None and hasattr(widget_to_schedule_on.master, 'after'):
            widget_to_schedule_on = widget_to_schedule_on.master
            # Dừng lại nếu đạt đến cửa sổ gốc hoặc widget không tồn tại
            if isinstance(widget_to_schedule_on, (tkinter.Tk, tkinter.Toplevel)) or not widget_to_schedule_on.winfo_exists():
                 break

        if widget_to_schedule_on.winfo_exists():
             widget_to_schedule_on.after(0, _update)
        elif textbox.winfo_exists(): # Fallback về chính textbox nếu không tìm được gốc phù hợp
             textbox.after(0, _update)
        else:
             print(f"Cảnh báo update_status: Không thể lên lịch cập nhật cho textbox đã bị hủy.")
    except Exception as e:
        # Ghi log lỗi chi tiết hơn nếu cần
        import traceback
        print(f"Lỗi trong update_status khi gọi after: {e}\n{traceback.format_exc()}")


def check_and_install_dependencies(required_libs):
    """Kiểm tra và cài đặt dependencies."""
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
             missing_libs.append(lib_name) # Coi như thiếu

    if not missing_libs:
        print("Tất cả dependencies cần thiết đã có.")
        return True

    libs_str = ", ".join(missing_libs)
    root = None
    user_confirm = False # Mặc định là không đồng ý
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
                root_err_pip = None
                try:
                    root_err_pip = tkinter.Tk()
                    root_err_pip.withdraw()
                    tkinter.messagebox.showerror("Lỗi Cài Đặt", f"Không thể tự động cài đặt '{lib_name}'.\nLỗi pip (kiểm tra console).\n\nVui lòng thử cài đặt thủ công:\npip install {lib_name}")
                except Exception as e:
                    print(f"Lỗi hiển thị messagebox lỗi pip: {e}")
                finally:
                    if root_err_pip:
                        root_err_pip.destroy()
                # return False # Dừng nếu muốn

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
            # return False

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