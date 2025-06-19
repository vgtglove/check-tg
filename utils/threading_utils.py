import asyncio
import time
import gc
from PyQt5.QtCore import QThread, pyqtSignal
from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
from telethon import functions
from utils.session_utils import SessionStatus
from utils.activity_utils import UserActivityStatus
from utils.phone_utils import check_phone_numbers, normalize_phone_number

# 这里只迁移线程类的定义和信号，不迁移主窗口的UI绑定


class CheckThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    session_status_signal = pyqtSignal(str, str, str)
    check_complete_signal = pyqtSignal(list)

    def __init__(self, phone_numbers, message, sessions, parent=None):
        super().__init__(parent)
        self.phone_numbers = phone_numbers
        self.message = message
        self.sessions = sessions
        self.is_running = True
        self.parent = parent
        self.batch_size = 5000
        self.processed_numbers = set()
        self.registered_numbers = []

    async def check_numbers(self):
        try:
            self.log_signal.emit("【初始化】开始筛选号码初始化...")
            total = len(self.phone_numbers)
            checked = 0
            available_sessions = []
            api_id = self.parent.config.getint('API', 'api_id', fallback=2040)
            api_hash = self.parent.config.get(
                'API', 'api_hash', fallback='b18441a1ff607e10a989891a5462e627')
            session_batches = [self.sessions[i:i + 10]
                               for i in range(0, len(self.sessions), 10)]
            for batch_idx, batch in enumerate(session_batches):
                self.log_signal.emit(
                    f"【初始化】检查会话批次 {batch_idx+1}/{len(session_batches)}...")
                batch_tasks = []
                for session in batch:
                    batch_tasks.append(self.initialize_session(
                        session, api_id, api_hash))
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                for session, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        error_msg = f"Session {session.name} 初始化失败: {str(result)}"
                        self.log_signal.emit(f"【初始化失败】{error_msg}")
                        session.add_error(error_msg)
                        session.status = "错误"
                        self.session_status_signal.emit(
                            session.file_path, "错误", error_msg)
                    elif result:
                        available_sessions.append(session)
                        self.log_signal.emit(f"【初始化成功】{session.name} 可用")
                await asyncio.sleep(0.5)
            if not available_sessions:
                error_msg = "错误：没有可用的Session"
                self.log_signal.emit(f"【严重错误】{error_msg}")
                for session in self.sessions:
                    if session.status not in ["未授权", "错误"]:
                        session.add_error("初始化后不可用")
                return []
            self.log_signal.emit(f"【开始检测】准备检测 {total} 个号码是否注册...")

            def phone_number_generator():
                for i in range(0, len(self.phone_numbers), self.batch_size):
                    if not self.is_running:
                        break
                    batch = [p for p in self.phone_numbers[i:i +
                                                           self.batch_size] if p not in self.processed_numbers]
                    if batch:
                        yield batch

            async def process_batch(batch):
                nonlocal checked
                current_phones = batch.copy()
                batch_registered = []
                while current_phones and self.is_running:
                    for session in available_sessions:
                        if not self.is_running or not current_phones:
                            break
                        if not session.can_use():
                            continue
                        session_batch_size = min(
                            session.batch_size, len(current_phones))
                        current_batch = current_phones[:session_batch_size]
                        current_phones = current_phones[session_batch_size:]
                        self.processed_numbers.update(current_batch)
                        try:
                            client = TelegramClient(
                                session.file_path, api_id, api_hash)
                            await client.connect()
                            if not await client.is_user_authorized():
                                error_msg = f"Session {session.name} 检查时未授权"
                                self.log_signal.emit(f"【授权错误】{error_msg}")
                                session.add_error(error_msg)
                                session.status = "未授权"
                                self.session_status_signal.emit(
                                    session.file_path, "未授权", error_msg)
                                current_phones.extend(current_batch)
                                self.processed_numbers.difference_update(
                                    current_batch)
                                continue
                            session.status = "正在运行"
                            self.session_status_signal.emit(
                                session.file_path, "正在运行", "")
                            self.log_signal.emit(
                                f"【使用会话】使用 {session.name} 检查号码批次: {len(current_batch)} 个，批量大小: {session_batch_size}")
                            if len(current_batch) > 0:
                                display_nums = current_batch[:min(
                                    5, len(current_batch))]
                                for phone in display_nums:
                                    self.log_signal.emit(f"【检测号码】检测: {phone}")
                                if len(current_batch) > 5:
                                    self.log_signal.emit(
                                        f"【检测号码】... 以及其他 {len(current_batch) - 5} 个号码")
                            client._log_handler = lambda msg: self.log_signal.emit(
                                msg)
                            result = await check_phone_numbers(client, self.message, current_batch)
                            if result:
                                batch_registered.extend(result)
                                self.log_signal.emit(
                                    f"【发现注册】发现已注册号码: {len(result)} 个")
                            checked += len(current_batch)
                            self.progress_signal.emit(checked, total)
                            session.status = "空闲"
                            session.last_used = time.time()
                            session.total_checks += 1
                            self.session_status_signal.emit(
                                session.file_path, "空闲", "")
                            self.log_signal.emit(
                                f"【进入冷却】{session.name} 进入冷却状态，冷却时间: {session.cooldown_time}秒")
                        except Exception as e:
                            error_msg = f"Session {session.name} 检查出错: {str(e)}"
                            self.log_signal.emit(f"【检查错误】{error_msg}")
                            session.add_error(error_msg)
                            session.status = "错误"
                            self.session_status_signal.emit(
                                session.file_path, "错误", error_msg)
                            current_phones.extend(current_batch)
                            self.processed_numbers.difference_update(
                                current_batch)
                        finally:
                            try:
                                await client.disconnect()
                            except:
                                pass
                        if self.is_running and current_phones and session.cooldown_time > 0:
                            await asyncio.sleep(3)
                    if current_phones and self.is_running:
                        min_cooldown = min(
                            [s.cooldown_time for s in available_sessions if s.cooldown_time > 0], default=180)
                        self.log_signal.emit(
                            f"【等待冷却】所有session正在冷却中，需等待 {min_cooldown} 秒后继续...")
                        wait_started = time.time()
                        while self.is_running and current_phones:
                            found_available = False
                            for s in available_sessions:
                                if s.can_use():
                                    self.log_signal.emit(
                                        f"【会话可用】{s.name} 已冷却完毕，继续检测")
                                    found_available = True
                                    break
                            if found_available:
                                break
                            wait_time = time.time() - wait_started
                            if int(wait_time) % 15 == 0 and int(wait_time) > 0:
                                remaining = max(0, min_cooldown - wait_time)
                                self.log_signal.emit(
                                    f"【等待中】已等待 {int(wait_time)} 秒，预计还需 {int(remaining)} 秒...")
                            await asyncio.sleep(1)
                return batch_registered
            for batch_idx, phone_batch in enumerate(phone_number_generator()):
                if not self.is_running:
                    break
                self.log_signal.emit(
                    f"【开始批次】批次 {batch_idx+1}，大小: {len(phone_batch)} 个号码")
                batch_result = await process_batch(phone_batch)
                self.registered_numbers.extend(batch_result)
                gc.collect()
            return self.registered_numbers
        except Exception as e:
            error_msg = f"检测线程发生错误: {str(e)}"
            self.log_signal.emit(f"【线程错误】{error_msg}")
            return []

    async def initialize_session(self, session, api_id, api_hash):
        try:
            client = TelegramClient(session.file_path, api_id, api_hash)
            await client.connect()
            if not await client.is_user_authorized():
                error_msg = f"Session {session.name} 未授权"
                self.log_signal.emit(f"【授权错误】{error_msg}")
                session.add_error(error_msg)
                session.status = "未授权"
                self.session_status_signal.emit(
                    session.file_path, "未授权", error_msg)
                await client.disconnect()
                return False
            session.status = "空闲"
            await client.disconnect()
            return True
        except Exception as e:
            raise e

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            registered_numbers = loop.run_until_complete(self.check_numbers())
            self.check_complete_signal.emit(registered_numbers)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"【线程错误】筛选号码线程错误: {str(e)}\n详细信息:\n{error_details}"
            self.log_signal.emit(error_msg)
            self.check_complete_signal.emit([])
        finally:
            try:
                loop.close()
            except Exception as close_error:
                self.log_signal.emit(f"【关闭错误】关闭事件循环时出错: {str(close_error)}")

    def stop(self):
        try:
            self.is_running = False
            self.log_signal.emit("【停止信号】正在结束当前检测批次...")
        except Exception as e:
            self.log_signal.emit(f"【停止错误】停止过程中出错: {str(e)}")


class PhoneNumberImportThread(QThread):
    progress_signal = pyqtSignal(int, int)
    result_signal = pyqtSignal(list)
    log_signal = pyqtSignal(str)

    def __init__(self, file_path=None, text_content=None, existing_numbers=None, registered_numbers=None):
        super().__init__()
        self.file_path = file_path
        self.text_content = text_content
        self.existing_numbers = set(existing_numbers or [])
        self.registered_numbers = set(registered_numbers or [])
        self.is_running = True

    def normalize_phone_number(self, number):
        digits = ''.join(filter(str.isdigit, number))
        if digits.startswith('1') and len(digits) > 10:
            return '+' + digits
        elif len(digits) > 10:
            return '+' + digits
        elif len(digits) == 10:
            return '+1' + digits
        else:
            return '+' + digits

    def run(self):
        try:
            all_numbers = []
            processed_count = 0
            batch_size = 10000
            if self.file_path:
                try:
                    with open(self.file_path, 'r', encoding='utf-8') as f:
                        content = f.readlines()
                except UnicodeDecodeError:
                    with open(self.file_path, 'r', encoding='latin-1') as f:
                        content = f.readlines()
                total_lines = len(content)
                self.log_signal.emit(f"开始处理文件中的 {total_lines} 行内容...")
                for i, line in enumerate(content):
                    if not self.is_running:
                        break
                    numbers_in_line = line.strip().split()
                    for number in numbers_in_line:
                        if number:
                            normalized = self.normalize_phone_number(number)
                            if normalized not in self.existing_numbers and normalized not in self.registered_numbers:
                                all_numbers.append(normalized)
                    processed_count += 1
                    if processed_count % 1000 == 0 or processed_count == total_lines:
                        self.progress_signal.emit(processed_count, total_lines)
            elif self.text_content:
                lines = self.text_content.split('\n')
                total_lines = len(lines)
                self.log_signal.emit(f"开始处理输入的 {total_lines} 行文本...")
                for i, line in enumerate(lines):
                    if not self.is_running:
                        break
                    if line.strip():
                        normalized = self.normalize_phone_number(line.strip())
                        if normalized not in self.existing_numbers and normalized not in self.registered_numbers:
                            all_numbers.append(normalized)
                    processed_count += 1
                    if processed_count % 1000 == 0 or processed_count == total_lines:
                        self.progress_signal.emit(processed_count, total_lines)
            if self.is_running:
                self.log_signal.emit(f"处理完成，共找到 {len(all_numbers)} 个有效号码")
                self.result_signal.emit(all_numbers)
            else:
                self.log_signal.emit("导入操作被取消")
        except Exception as e:
            self.log_signal.emit(f"导入过程出错: {str(e)}")
            self.result_signal.emit([])

    def stop(self):
        self.is_running = False


class ActivityCheckThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    session_status_signal = pyqtSignal(str, str, str)
    check_complete_signal = pyqtSignal(list)

    def __init__(self, phone_numbers, sessions, parent=None, active_days=30):
        super().__init__(parent)
        self.phone_numbers = phone_numbers
        self.sessions = sessions
        self.is_running = True
        self.parent = parent
        self.active_days = active_days
        self.activity_results = []
        self.batch_size = 5000
        if parent and hasattr(parent, 'config'):
            memory_batch_size = parent.config.getint(
                'Settings', 'memory_batch_size', fallback=5000)
            self.batch_size = memory_batch_size
        self.processed_numbers = set()

    async def check_user_activity(self, client, phone_numbers):
        results = []
        processed_phones = set()
        for phone in phone_numbers:
            if not self.is_running:
                break
            if phone in processed_phones:
                continue
            processed_phones.add(phone)
            try:
                activity_status = UserActivityStatus(phone)
                try:
                    contact = InputPhoneContact(
                        client_id=0, phone=phone, first_name="", last_name="")
                    contacts_result = await client(ImportContactsRequest([contact]))
                    if contacts_result and contacts_result.users:
                        user = contacts_result.users[0]
                        user_id = user.id
                        try:
                            full_user = await client(functions.users.GetFullUserRequest(id=user))
                            user = full_user.user if hasattr(
                                full_user, 'user') else user
                            activity_status.update_from_user(user)
                            activity_status.username = user.username if hasattr(
                                user, 'username') and user.username else ""
                            activity_status.first_name = user.first_name if hasattr(
                                user, 'first_name') and user.first_name else ""
                            activity_status.last_name = user.last_name if hasattr(
                                user, 'last_name') and user.last_name else ""
                            self.log_signal.emit(
                                f"【活跃度-状态】{phone} - {activity_status.activity_status}")
                            results.append(activity_status)
                        except Exception as e:
                            self.log_signal.emit(
                                f"【活跃度-获取失败】{phone} 获取详细信息失败: {str(e)}")
                            activity_status.activity_status = "检测失败"
                            results.append(activity_status)
                    else:
                        activity_status.activity_status = "未注册"
                        self.log_signal.emit(f"【活跃度-未注册】{phone} 未注册Telegram")
                        results.append(activity_status)
                except Exception as e:
                    self.log_signal.emit(
                        f"【活跃度-获取失败】{phone} 用户信息获取失败: {str(e)}")
                    activity_status.activity_status = "检测失败"
                    results.append(activity_status)
                await asyncio.sleep(0.5)
            except Exception as e:
                self.log_signal.emit(f"【活跃度-检测出错】{phone} 活跃度检测出错: {str(e)}")
                activity_status = UserActivityStatus(phone)
                activity_status.activity_status = "检测出错"
                results.append(activity_status)
        return results

    async def check_activity(self):
        try:
            self.log_signal.emit("【初始化】开始活跃度检测初始化...")
            total = len(self.phone_numbers)
            checked = 0
            all_results = []
            self.progress_signal.emit(0, total)
            available_sessions = []
            api_id = self.parent.config.getint('API', 'api_id', fallback=2040)
            api_hash = self.parent.config.get(
                'API', 'api_hash', fallback='b18441a1ff607e10a989891a5462e627')
            session_batches = [self.sessions[i:i + 5]
                               for i in range(0, len(self.sessions), 5)]
            for batch_idx, batch in enumerate(session_batches):
                self.log_signal.emit(
                    f"【初始化】检查会话批次 {batch_idx+1}/{len(session_batches)}...")
                batch_tasks = []
                for session in batch:
                    batch_tasks.append(self.initialize_session(
                        session, api_id, api_hash))
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                for session, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        error_msg = f"Session {session.name} 初始化失败: {str(result)}"
                        self.log_signal.emit(f"【初始化失败】{error_msg}")
                        session.add_error(error_msg)
                        session.status = "错误"
                        self.session_status_signal.emit(
                            session.file_path, "错误", error_msg)
                    elif result:
                        available_sessions.append(session)
                        self.log_signal.emit(f"【初始化成功】{session.name} 可用")
                await asyncio.sleep(1)
            if not available_sessions:
                error_msg = "错误：没有可用的Session"
                self.log_signal.emit(f"【严重错误】{error_msg}")
                return []
            self.log_signal.emit(f"【开始检测】准备检测 {total} 个号码活跃度...")

            def phone_batch_generator():
                for i in range(0, total, self.batch_size):
                    if not self.is_running:
                        break
                    batch = [p for p in self.phone_numbers[i:i +
                                                           self.batch_size] if p not in self.processed_numbers]
                    if batch:
                        yield batch

            async def process_batch(phone_batch):
                nonlocal checked
                batch_results = []
                current_phones = phone_batch.copy()
                while current_phones and self.is_running:
                    session = None
                    for s in available_sessions:
                        if s.can_use():
                            session = s
                            break
                    if not session:
                        min_cooldown = min(
                            [s.cooldown_time for s in available_sessions if s.cooldown_time > 0], default=180)
                        self.log_signal.emit(
                            f"【等待冷却】所有session正在冷却中，需等待 {min_cooldown} 秒后继续...")
                        wait_started = time.time()
                        while self.is_running:
                            found_available = False
                            for s in available_sessions:
                                if s.can_use():
                                    session = s
                                    self.log_signal.emit(
                                        f"【会话可用】{s.name} 已冷却完毕，继续检测")
                                    found_available = True
                                    break
                            if found_available:
                                break
                            wait_time = time.time() - wait_started
                            if int(wait_time) % 15 == 0 and int(wait_time) > 0:
                                remaining = max(0, min_cooldown - wait_time)
                                self.log_signal.emit(
                                    f"【等待中】已等待 {int(wait_time)} 秒，预计还需 {int(remaining)} 秒...")
                            await asyncio.sleep(1)
                        if not session:
                            self.log_signal.emit("【等待中断】等待被用户中断，跳过当前批次")
                            break
                    try:
                        current_batch_size = session.batch_size
                        current_batch = current_phones[:current_batch_size]
                        current_phones = current_phones[current_batch_size:]
                        self.log_signal.emit(
                            f"【使用会话】使用 {session.name} 处理 {len(current_batch)} 个号码，批量大小: {current_batch_size}")
                        client = TelegramClient(
                            session.file_path, api_id, api_hash)
                        await client.connect()
                        if not await client.is_user_authorized():
                            error_msg = f"Session {session.name} 未授权"
                            self.log_signal.emit(f"【授权错误】{error_msg}")
                            session.add_error(error_msg)
                            session.status = "未授权"
                            self.session_status_signal.emit(
                                session.file_path, "未授权", error_msg)
                            current_phones = current_batch + current_phones
                            continue
                        session.status = "正在运行"
                        self.session_status_signal.emit(
                            session.file_path, "正在运行", "")
                        self.processed_numbers.update(current_batch)
                        mini_results = await self.check_user_activity(client, current_batch)
                        batch_results.extend(mini_results)
                        checked += len(current_batch)
                        self.progress_signal.emit(checked, total)
                        session.status = "空闲"
                        session.last_used = time.time()
                        session.total_checks += 1
                        self.session_status_signal.emit(
                            session.file_path, "空闲", "")
                        self.log_signal.emit(
                            f"【进入冷却】{session.name} 进入冷却状态，冷却时间: {session.cooldown_time}秒")
                        if session.cooldown_time > 0:
                            await asyncio.sleep(min(session.cooldown_time/10, 3))
                    except Exception as e:
                        error_msg = f"Session {session.name} 检查出错: {str(e)}"
                        self.log_signal.emit(f"【检查错误】{error_msg}")
                        session.add_error(error_msg)
                        session.status = "错误"
                        self.session_status_signal.emit(
                            session.file_path, "错误", error_msg)
                        current_phones = current_batch + current_phones
                    finally:
                        try:
                            await client.disconnect()
                        except:
                            pass
                gc.collect()
                return batch_results
            for batch_idx, phone_batch in enumerate(phone_batch_generator()):
                if not self.is_running:
                    break
                self.log_signal.emit(
                    f"【开始批次】批次 {batch_idx+1}，大小: {len(phone_batch)} 个号码")
                batch_results = await process_batch(phone_batch)
                all_results.extend(batch_results)
                if self.is_running and batch_idx < len(self.phone_numbers) // self.batch_size:
                    self.log_signal.emit(f"【批次完成】已完成批次 {batch_idx+1}，休息片刻...")
                    await asyncio.sleep(5)
            return all_results
        except Exception as e:
            error_msg = f"活跃度检测线程发生错误: {str(e)}"
            self.log_signal.emit(f"【线程错误】{error_msg}")
            return []

    async def initialize_session(self, session, api_id, api_hash):
        try:
            client = TelegramClient(session.file_path, api_id, api_hash)
            await client.connect()
            if not await client.is_user_authorized():
                error_msg = f"Session {session.name} 未授权"
                self.log_signal.emit(f"【授权错误】{error_msg}")
                session.add_error(error_msg)
                session.status = "未授权"
                self.session_status_signal.emit(
                    session.file_path, "未授权", error_msg)
                await client.disconnect()
                return False
            session.status = "空闲"
            await client.disconnect()
            return True
        except Exception as e:
            raise e

    def progress_signal_handler(self, checked, total):
        progress = (checked / total) * 100 if total > 0 else 0
        if int(progress) % 5 == 0 or checked == total or checked == 1:
            self.log_signal.emit(
                f"【活跃度-进度】已检测: {checked}/{total} ({progress:.1f}%)")

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self.progress_signal.connect(self.progress_signal_handler)
            activity_results = loop.run_until_complete(self.check_activity())
            self.activity_results = activity_results
            self.check_complete_signal.emit(activity_results)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"【线程错误】活跃度检测线程错误: {str(e)}\n详细信息:\n{error_details}"
            self.log_signal.emit(error_msg)
            self.check_complete_signal.emit([])
        finally:
            try:
                loop.close()
            except Exception as close_error:
                self.log_signal.emit(f"【关闭错误】关闭事件循环时出错: {str(close_error)}")

    def stop(self):
        try:
            self.is_running = False
            self.log_signal.emit("【停止信号】正在结束当前检测批次...")
        except Exception as e:
            self.log_signal.emit(f"【停止错误】停止过程中出错: {str(e)}")


class SendMsgThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    session_status_signal = pyqtSignal(str, str, str)
    send_complete_signal = pyqtSignal(dict)

    def __init__(self, phone_numbers, message, sessions, parent=None):
        super().__init__(parent)
        self.phone_numbers = phone_numbers
        self.message = message
        self.sessions = sessions
        self.is_running = True
        self.parent = parent
        self.batch_size = 5000
        self.processed_numbers = set()
        self.result = {"success": 0, "fail": 0, "fail_detail": []}

    async def send_messages(self):
        """
        异步发送消息给指定的手机号列表，支持未注册统计、去重、失败重试、进度优化。
        """
        try:
            self.log_signal.emit("【初始化】开始批量发送消息...")

            # 1. 手机号去重
            unique_phones = list(set(self.phone_numbers))
            total = len(unique_phones)
            sent = 0

            api_id = self.parent.config.getint('API', 'api_id', fallback=2040)
            api_hash = self.parent.config.get(
                'API', 'api_hash', fallback='b18441a1ff607e10a989891a5462e627')

            # 记录未注册号码
            not_registered = set()
            # 记录已成功发送的号码，避免多 session 重复发
            already_sent = set()
            # 失败重试队列
            retry_queue = []

            for session in self.sessions:
                try:
                    client = TelegramClient(
                        session.file_path, api_id, api_hash)
                    await client.connect()
                    if not await client.is_user_authorized():
                        await client.disconnect()
                        self.log_signal.emit(f"Session {session.name} 未授权，跳过")
                        continue

                    # 只对未发送过的号码导入
                    phones_to_send = [
                        p for p in unique_phones if p not in already_sent]
                    if not phones_to_send:
                        await client.disconnect()
                        continue

                    contacts = [InputPhoneContact(
                        client_id=i, phone=phone, first_name="", last_name="") for i, phone in enumerate(phones_to_send)]
                    try:
                        result = await client(ImportContactsRequest(contacts))
                    except Exception as e:
                        self.log_signal.emit(f"导入联系人失败: {e}")
                        await client.disconnect()
                        continue

                    users = result.users
                    # 记录已注册号码
                    registered_phones = set()
                    user_map = {}
                    for user in users:
                        # user.phone 可能不存在，需兼容
                        phone = getattr(user, 'phone', None)
                        if phone:
                            registered_phones.add(phone)
                            user_map[phone] = user

                    # 统计未注册号码
                    for phone in phones_to_send:
                        if phone not in registered_phones:
                            not_registered.add(phone)

                    # 只对未发送过且已注册的号码发消息
                    for phone in registered_phones:
                        if not self.is_running:
                            break
                        if phone in already_sent:
                            continue
                        user = user_map[phone]
                        try:
                            entity = await client.get_entity(user.id)
                            await client.send_message(entity, self.message)
                            self.result["success"] += 1
                            already_sent.add(phone)
                        except Exception as e:
                            self.result["fail"] += 1
                            self.result["fail_detail"].append(f"{phone}: {e}")
                            retry_queue.append(
                                (session, phone, user.id, str(e)))
                            self.log_signal.emit(f"发送消息失败: {phone} - {e}")
                        sent += 1
                        self.progress_signal.emit(sent, total)
                    await client.disconnect()
                except Exception as e:
                    self.log_signal.emit(f"Session {session.name} 发送消息出错: {e}")

            # 失败重试一次
            if retry_queue:
                self.log_signal.emit("【重试】开始对失败号码重试一次...")
                for session, phone, user_id, err in retry_queue:
                    if not self.is_running:
                        break
                    try:
                        client = TelegramClient(
                            session.file_path, api_id, api_hash)
                        await client.connect()
                        if not await client.is_user_authorized():
                            await client.disconnect()
                            continue
                        try:
                            await client.send_message(user_id, self.message)
                            self.result["success"] += 1
                            self.result["fail"] -= 1
                            self.log_signal.emit(f"重试成功: {phone}")
                        except Exception as e:
                            self.log_signal.emit(f"重试仍失败: {phone} - {e}")
                        await client.disconnect()
                    except Exception as e:
                        self.log_signal.emit(f"重试时Session出错: {phone} - {e}")

            # 发送完成后发送完成信号，附带未注册号码
            self.send_complete_signal.emit({
                **self.result,
                "not_registered": list(not_registered)
            })
        except Exception as e:
            self.log_signal.emit(f"【线程错误】发送消息线程错误: {str(e)}")
            self.send_complete_signal.emit(self.result)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.send_messages())
        except Exception as e:
            self.log_signal.emit(f"【线程错误】发送消息线程run出错: {str(e)}")
        finally:
            try:
                loop.close()
            except Exception as close_error:
                self.log_signal.emit(f"【关闭错误】关闭事件循环时出错: {str(close_error)}")

    def stop(self):
        self.is_running = False
        self.log_signal.emit("【停止信号】正在结束当前消息发送批次...")

    def send_msg_completed(self, result):
        self.start_btn.setEnabled(True)
        self.check_activity_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        msg = f"消息发送完成！成功: {result.get('success', 0)}，失败: {result.get('fail', 0)}"
        if result.get('fail_detail'):
            msg += "\n失败详情：\n" + "\n".join(result['fail_detail'][:10])
            if len(result['fail_detail']) > 10:
                msg += f"\n...共{len(result['fail_detail'])}条失败"
        if result.get('not_registered'):
            msg += f"\n未注册号码({len(result['not_registered'])}):\n" + \
                ", ".join(result['not_registered'][:10])
            if len(result['not_registered']) > 10:
                msg += f"\n...共{len(result['not_registered'])}个未注册"
        # QMessageBox.information(self, '完成', msg)
