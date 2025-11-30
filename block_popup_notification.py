# 使用 Win32 API 实现希沃管家弹窗拦截器，并集成 loguru 日志
import win32gui
import win32process
import psutil
import threading
import time
import win32con
import traceback
from logger_config import logger
import threading

# 可由外部调用以停止拦截器
stop_event = threading.Event()

def stop():
    """外部调用以请求拦截器停止"""
    stop_event.set()

# 配置参数 - 精确匹配条件
TARGET_WINDOW_TITLE = "希沃管家"  # 窗口标题必须完全匹配
TARGET_PROCESS_NAME = "seewoserviceassistant.exe"  # 进程名必须完全匹配
TARGET_WIDTH = 328
TARGET_HEIGHT = 146
SIZE_TOLERANCE = 5


class Win32Interceptor:
    def __init__(self):
        self.intercepted_windows = set()
        self.prev_all_hwnds = set()
        self.first_scan = True
        self.lock = threading.Lock()
        self.last_process_running = None
        self.prev_intercepted_count = 0
        self._last_scan_log_ts = 0.0

    def get_window_dimensions(self, hwnd):
        try:
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            return width, height
        except Exception as e:
            logger.debug(f"获取窗口尺寸失败 (句柄: {hwnd}): {e}")
            return 0, 0

    def get_process_name_from_hwnd(self, hwnd):
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError) as e:
            logger.debug(f"获取进程名失败 (句柄: {hwnd}): {e}")
            return ""
        except Exception as e:
            logger.debug(f"未知错误获取进程名 (句柄: {hwnd}): {e}")
            return ""

    def find_and_close_target_windows(self):
        try:
            all_windows = []  # list of (hwnd, title, process_name, width, height)

            def enum_cb(hwnd, _):
                try:
                    if not win32gui.IsWindowVisible(hwnd):
                        return True
                    title = win32gui.GetWindowText(hwnd) or ""
                    proc = self.get_process_name_from_hwnd(hwnd)
                    w, h = self.get_window_dimensions(hwnd)
                    all_windows.append((hwnd, title, proc, w, h))
                except Exception:
                    logger.debug(f"枚举时处理窗口 {hwnd} 出错: {traceback.format_exc()}")
                return True

            win32gui.EnumWindows(enum_cb, 0)

            current_hwnds = {hwnd for hwnd, *_ in all_windows}

            # 首次扫描时，DEBUG 级别下展示完整窗口列表
            if self.first_scan:
                logger.debug("首次扫描：列出所有可见窗口信息:")
                for idx, (hwnd, title, proc, w, h) in enumerate(all_windows, start=1):
                    logger.debug(f"   [{idx}] 句柄={hwnd} | 标题='{title}' | 进程={proc} | 尺寸={w}x{h}")
            else:
                # 后续扫描只在 DEBUG 下提示新增/移除窗口
                added = current_hwnds - self.prev_all_hwnds
                removed = self.prev_all_hwnds - current_hwnds
                if added:
                    for hwnd in added:
                        entry = next((e for e in all_windows if e[0] == hwnd), None)
                        if entry:
                            logger.debug(f"   [+] 新窗口 句柄={entry[0]} 标题='{entry[1]}' 进程={entry[2]} 尺寸={entry[3]}x{entry[4]}")
                if removed:
                    for hwnd in removed:
                        logger.debug(f"   [-] 窗口已消失 句柄={hwnd}")

            # 查找并关闭匹配窗口
            matching_this_scan = 0
            for hwnd, title, proc, w, h in all_windows:
                try:
                    if title != TARGET_WINDOW_TITLE:
                        continue
                    if proc != TARGET_PROCESS_NAME:
                        continue
                    size_match = (abs(w - TARGET_WIDTH) <= SIZE_TOLERANCE and abs(h - TARGET_HEIGHT) <= SIZE_TOLERANCE)
                    if size_match:
                        matching_this_scan += 1
                        with self.lock:
                            if hwnd not in self.intercepted_windows:
                                self.intercepted_windows.add(hwnd)
                        logger.debug(f"检测到匹配窗口 句柄={hwnd} 标题='{title}' 进程={proc} 尺寸={w}x{h}")
                        try:
                            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                            logger.debug(f"尝试关闭窗口 {hwnd}")
                        except Exception as e:
                            logger.debug(f"关闭窗口失败 (句柄: {hwnd}): {e}")
                except Exception as e:
                    logger.debug(f"检查窗口特征时出错 (句柄: {hwnd}): {e} {traceback.format_exc()}")

            # INFO 级别：仅在已拦截数量发生变化时提示汇总
            try:
                current_count = len(self.intercepted_windows)
                if current_count != self.prev_intercepted_count:
                    logger.info(f"已拦截 {current_count} 个希沃管家弹窗拦截提示")
                    self.prev_intercepted_count = current_count
            except Exception:
                # 若 logger 在初始化前调用会抛异常，静默忽略
                pass

            # 更新状态
            self.prev_all_hwnds = current_hwnds
            self.first_scan = False

            return matching_this_scan
        except Exception as e:
            logger.debug(f"窗口扫描过程出错: {e} {traceback.format_exc()}")
            return 0

    def run(self):
        logger.debug("Win32 拦截器启动，开始监控窗口...")
        # 只要没有收到停止请求就持续运行
        while not stop_event.is_set():
            try:
                # 不再输出“执行窗口扫描”提示以减少噪声
                now_ts = time.time()
                self._last_scan_log_ts = now_ts
                # 检查目标进程是否存在（仅在状态变化时记录）
                proc_running = self.is_target_process_running()
                if self.last_process_running is None:
                    # 初始状态，仅记录一次
                    if not proc_running:
                        logger.debug(f"未找到进程 {TARGET_PROCESS_NAME}，但仍将继续监控")
                    else:
                        logger.debug(f"检测到目标进程: {TARGET_PROCESS_NAME}")
                else:
                    if proc_running != self.last_process_running:
                        if not proc_running:
                            logger.info(f"目标进程 '{TARGET_PROCESS_NAME}' 已停止运行")
                        else:
                            logger.info(f"目标进程 '{TARGET_PROCESS_NAME}' 已启动，继续监控")
                self.last_process_running = proc_running
                self.find_and_close_target_windows()
                time.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("拦截器停止")
                break
            except Exception as e:
                logger.debug(f"监控循环出错: {e} {traceback.format_exc()}")
                time.sleep(1)

    def is_target_process_running(self):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == TARGET_PROCESS_NAME:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False


def interceptor_main():
    """拦截器主函数"""
    logger.debug("检查目标进程是否存在...")
    target_process_found = False
    running_processes = []
    for proc in psutil.process_iter(['name']):
        try:
            proc_name = (proc.info['name'] or "").lower()
            running_processes.append(proc_name)
            if proc_name == TARGET_PROCESS_NAME:
                target_process_found = True
                logger.debug(f"检测到目标进程: {TARGET_PROCESS_NAME}")
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    if not target_process_found:
        logger.debug(f"未找到进程 {TARGET_PROCESS_NAME}，但仍将继续监控。示例进程 (前10)：{running_processes[:10]}")

    interceptor = Win32Interceptor()
    interceptor.run()


if __name__ == "__main__":
    interceptor_main()