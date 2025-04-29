# utils.py
import os
import sys
import shutil
import importlib.util
import subprocess
import tkinter.messagebox
import tkinter # Cần cho root tạm thời của messagebox trong check_dependencies

# --- Biến toàn cục cho User Agents ---
LOADED_USER_AGENT_LIST = []
UA_FILENAME = "user_agents.txt"

def load_user_agents():
    """Tải danh sách User Agent từ file vào biến toàn cục."""
    global LOADED_USER_AGENT_LIST
    LOADED_USER_AGENT_LIST = [] # Reset trước khi tải
    try:
        # Xác định đường dẫn tuyệt đối đến thư mục chứa script này
        # Dùng __file__ để xác định vị trí của utils.py
        utils_dir = os.path.dirname(os.path.abspath(__file__))
        ua_file_path = os.path.join(utils_dir, UA_FILENAME) # Tìm file UA cùng thư mục với utils.py

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
            return False # Trả về False nếu không tải được UA nào
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file '{UA_FILENAME}' trong cùng thư mục với utils.py.")
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
    return chrome_executable

def update_status(textbox, message):
    """Cập nhật nội dung cho CTkTextbox một cách an toàn từ các thread."""
    def _update():
        # Đảm bảo message là string
        safe_message = str(message)
        # Kiểm tra widget còn tồn tại trước khi cập nhật
        if textbox.winfo_exists():
            textbox.insert(tkinter.END, safe_message)
            textbox.see(tkinter.END) # Cuộn xuống dưới cùng
        else:
            print(f"Cảnh báo update_status: Textbox không còn tồn tại.")

    # Lấy master widget một cách an toàn
    try:
        master = textbox.master
        if master and master.winfo_exists():
             # Đảm bảo việc cập nhật GUI luôn chạy trên main thread
             master.after(0, _update)
        elif textbox.winfo_exists(): # Nếu master không rõ ràng, thử gọi từ chính textbox
             textbox.after(0, _update)
        else: # Nếu cả hai đều không tồn tại thì không làm gì cả
             print(f"Cảnh báo update_status: Không thể lên lịch cập nhật cho textbox đã bị hủy.")
    except Exception as e:
        print(f"Lỗi trong update_status khi gọi after: {e}")


def check_and_install_dependencies(required_libs):
    """
    Kiểm tra và cài đặt dependencies.

    Returns:
        bool: True nếu OK, False nếu lỗi hoặc người dùng hủy.
    """
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
        except ModuleNotFoundError: # Xử lý trường hợp find_spec không tìm thấy package gốc
             print(f"-> Thư viện '{lib_name}' bị thiếu (ModuleNotFoundError).")
             missing_libs.append(lib_name)
        except Exception as e:
             print(f"Lỗi khi kiểm tra thư viện '{lib_name}': {e}")
             missing_libs.append(lib_name) # Coi như thiếu nếu không kiểm tra được

    if not missing_libs:
        print("Tất cả dependencies cần thiết đã có.")
        return True

    libs_str = ", ".join(missing_libs)
    root = None
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
        print(f"Lỗi hiển thị messagebox: {e}. Giả sử người dùng từ chối.")
        user_confirm = False
    finally:
        if root:
            root.destroy()

    if not user_confirm:
        print("Người dùng đã từ chối cài đặt tự động.")
        # Hiển thị lỗi bằng messagebox lần nữa nếu có thể
        root_err = None
        try:
            root_err = tkinter.Tk()
            root_err.withdraw()
            tkinter.messagebox.showerror("Lỗi Dependencies", f"Không thể tiếp tục vì thiếu thư viện: {libs_str}\nVui lòng cài đặt thủ công bằng lệnh:\npip install {' '.join(missing_libs)}")
        except Exception as e:
             print(f"Lỗi hiển thị messagebox lỗi: {e}")
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
            # Tăng timeout nếu cần thiết
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', check=False, timeout=300) # 5 phút timeout

            if result.returncode == 0:
                print(f"-> Cài đặt '{lib_name}' thành công!")
                importlib.invalidate_caches() # Thử làm mới cache
            else:
                all_ok = False
                print(f"*** Lỗi khi cài đặt '{lib_name}' ***")
                print("--- Pip Output ---")
                print(result.stdout[-1000:]) # In 1000 ký tự cuối của stdout
                print("--- Pip Error ---")
                print(result.stderr[-1000:]) # In 1000 ký tự cuối của stderr
                print("------------------")
                root_err_pip = None
                try:
                    root_err_pip = tkinter.Tk()
                    root_err_pip.withdraw()
                    tkinter.messagebox.showerror("Lỗi Cài Đặt", f"Không thể tự động cài đặt '{lib_name}'.\nLỗi pip (kiểm tra console để xem chi tiết).\n\nVui lòng thử cài đặt thủ công:\npip install {lib_name}")
                except Exception as e:
                     print(f"Lỗi hiển thị messagebox lỗi pip: {e}")
                finally:
                    if root_err_pip:
                        root_err_pip.destroy()
                # return False # Có thể dừng ngay lập tức

        except subprocess.TimeoutExpired:
            all_ok = False
            print(f"Lỗi: Cài đặt '{lib_name}' vượt quá thời gian chờ.")
            # Hiển thị messagebox Timeout
            root_err_timeout = None
            try:
                 root_err_timeout = tkinter.Tk()
                 root_err_timeout.withdraw()
                 tkinter.messagebox.showerror("Lỗi Cài Đặt", f"Quá trình cài đặt '{lib_name}' mất quá nhiều thời gian.\nVui lòng kiểm tra kết nối mạng và thử cài đặt thủ công.")
            except Exception as e:
                 print(f"Lỗi hiển thị messagebox timeout: {e}")
            finally:
                if root_err_timeout:
                    root_err_timeout.destroy()

        except Exception as e:
            all_ok = False
            print(f"Lỗi nghiêm trọng khi chạy pip cho '{lib_name}': {e}")
            # Hiển thị messagebox lỗi hệ thống
            root_err_sys = None
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
        # Hiển thị messagebox thành công
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

    return all_ok