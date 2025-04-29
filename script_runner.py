# script_runner.py
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import time
import tempfile

# Import hàm tiện ích từ utils
from utils import update_status

def run_python_script_threaded(script_path_to_run, selected_profiles, status_textbox_script, run_button, temp_file_path=None):
    """Chạy script Python (từ file hoặc file tạm) tuần tự trên các profile."""
    total_selected = len(selected_profiles)
    script_basename = os.path.basename(script_path_to_run)
    source_type = "từ file tạm (đã dán)" if temp_file_path else "từ file đã chọn"

    update_status(status_textbox_script, f"\n=== Bắt đầu chạy script {source_type}: {script_basename} ===\n")
    update_status(status_textbox_script, f"Số profile được chọn: {total_selected}\n")

    python_executable = sys.executable
    if not python_executable:
        update_status(status_textbox_script, "LỖI NGHIÊM TRỌNG: Không thể xác định đường dẫn Python executable.\n")
        if run_button.winfo_exists():
             run_button.master.after(0, lambda: run_button.configure(state="normal"))
        return # Không thể chạy nếu không biết python ở đâu

    success_count = 0
    error_count = 0

    try: # Bọc try...finally để đảm bảo xóa file tạm
        for i, profile_path in enumerate(selected_profiles):
            # Kiểm tra xem nút/app còn tồn tại không trước mỗi vòng lặp nặng
            if not run_button.winfo_exists():
                print("Nút chạy script không còn tồn tại, dừng thread.")
                break

            profile_name = os.path.basename(profile_path)
            update_status(status_textbox_script, f"\n[{i+1}/{total_selected}] Đang chạy script trên profile: '{profile_name}'\n")
            update_status(status_textbox_script, f"  Profile path: {profile_path}\n")

            if not os.path.isdir(profile_path):
                 update_status(status_textbox_script, f"  Lỗi: Thư mục profile không tồn tại. Bỏ qua.\n")
                 error_count += 1
                 continue

            try:
                command = [python_executable, script_path_to_run, profile_path]
                update_status(status_textbox_script, f"  Executing: {' '.join(command)}\n")
                # Chạy và đợi hoàn thành, timeout 10 phút (600 giây)
                # Sử dụng CREATE_NO_WINDOW trên Windows để tránh cửa sổ console thừa
                startupinfo = None
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE # Ẩn cửa sổ console

                result = subprocess.run(command,
                                        capture_output=True,
                                        text=True,
                                        encoding='utf-8',
                                        errors='replace',
                                        check=False,
                                        timeout=600,
                                        startupinfo=startupinfo) # Thêm startupinfo

                # Hiển thị stdout
                if result.stdout:
                    update_status(status_textbox_script, f"--- Output (stdout) từ script ({profile_name}) ---\n")
                    update_status(status_textbox_script, result.stdout + "\n")
                    update_status(status_textbox_script, f"--- Kết thúc Output ({profile_name}) ---\n")

                # Kiểm tra lỗi và hiển thị stderr
                if result.returncode != 0:
                    error_count += 1
                    update_status(status_textbox_script, f"  LỖI: Script trả về mã lỗi {result.returncode} cho profile '{profile_name}'.\n")
                    if result.stderr:
                        update_status(status_textbox_script, f"--- Lỗi (stderr) từ script ({profile_name}) ---\n")
                        update_status(status_textbox_script, result.stderr + "\n")
                        update_status(status_textbox_script, f"--- Kết thúc Lỗi ({profile_name}) ---\n")
                    else:
                        update_status(status_textbox_script, f"  (Không có output lỗi stderr từ script)\n")
                else:
                    success_count += 1
                    update_status(status_textbox_script, f"  -> Hoàn thành thành công cho profile '{profile_name}'.\n")

            except FileNotFoundError:
                 update_status(status_textbox_script, f"  Lỗi: Không tìm thấy Python executable '{python_executable}' hoặc script '{script_path_to_run}'.\n")
                 error_count += 1
                 break # Dừng nếu lỗi nghiêm trọng
            except subprocess.TimeoutExpired:
                 update_status(status_textbox_script, f"  LỖI: Script chạy quá thời gian cho phép (timeout) trên profile '{profile_name}'.\n")
                 error_count += 1
            except Exception as e:
                import traceback
                update_status(status_textbox_script, f"  Lỗi không xác định khi chạy subprocess cho profile '{profile_name}': {e}\n")
                print(f"ERROR: Lỗi subprocess:\n{traceback.format_exc()}") # In traceback chi tiết vào console
                error_count += 1
            time.sleep(0.1) # Nghỉ chút

    finally:
        # Xóa file tạm nếu nó được tạo
        if temp_file_path:
            try:
                os.remove(temp_file_path)
                print(f"Đã xóa file tạm: {temp_file_path}")
                update_status(status_textbox_script, f"\nĐã xóa file script tạm thời.\n")
            except OSError as e:
                print(f"Lỗi khi xóa file tạm '{temp_file_path}': {e}")
                update_status(status_textbox_script, f"\nCẢNH BÁO: Không thể xóa file script tạm '{temp_file_path}'.\n")

        update_status(status_textbox_script, f"\n=== Hoàn tất chạy script: {script_basename} ===\n")
        update_status(status_textbox_script, f"Kết quả: {success_count} thành công, {error_count} lỗi.\n")

        # Kích hoạt lại nút Run Script trên main thread một cách an toàn
        if run_button.winfo_exists():
            run_button.master.after(0, lambda: run_button.configure(state="normal"))
