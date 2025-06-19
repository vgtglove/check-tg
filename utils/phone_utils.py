import asyncio
from typing import List

from telethon import TelegramClient
from telethon.tl.types import InputPhoneContact, UserStatusOnline, UserStatusOffline, UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth
from telethon.tl.functions.contacts import ImportContactsRequest


# 核心功能函数，移植自TelegramPhoneNumberRegisteredScript.py
def format_phone_number(phone: str) -> str:
    """
    格式化电话号码，统一格式
    
    Args:
        phone: 输入的电话号码字符串
    
    Returns:
        格式化后的电话号码（只保留数字）
    """
    # 移除所有空格、加号和其他非数字字符
    formatted = ''.join(filter(str.isdigit, phone))
    return formatted


def normalize_phone_number(number: str) -> str:
    """统一号码格式,移除所有非数字字符"""
    digits = ''.join(filter(str.isdigit, number))
    if digits.startswith('1') and len(digits) > 10:
        return '+' + digits
    elif len(digits) > 10:
        return '+' + digits
    elif len(digits) == 10:
        return '+1' + digits
    else:
        return '+' + digits


def load_registered_numbers() -> set:
    """
    加载已经检测过的号码
    
    Returns:
        已注册号码的集合
    """
    registered = set()
    try:
        with open('phone_register.txt', 'r') as f:
            for line in f:
                number = line.strip()
                if number:
                    registered.add(number)
    except FileNotFoundError:
        # 如果文件不存在，返回空集合
        pass
    return registered


async def check_phone_numbers(client: TelegramClient, message, phone_numbers: List[str], max_retries=3) -> List[str]:
    """
    检查一批手机号是否在Telegram上注册
    
    Args:
        client: Telegram客户端实例
        phone_numbers: 要检查的手机号列表
        max_retries: 最大重试次数
    
    Returns:
        已注册的手机号列表
    """
    global client_id_counter
    registered_numbers = []
    check_numbers = []

    # 加载已经检测过的号码
    existing_registered = load_registered_numbers()

    # 过滤掉已经检测过的号码
    new_numbers = [
        num for num in phone_numbers if num not in existing_registered]

    if not new_numbers:
        return []

    # 将手机号转换为InputPhoneContact对象
    for phone in new_numbers:
        check_numbers.append(
            InputPhoneContact(client_id=client_id_counter, phone=phone, first_name="",
                              last_name=""))
        client_id_counter += 1

    retry_count = 0
    while retry_count < max_retries:
        try:
            # 检查连接状态并尝试重连
            if not client.is_connected():
                await client.connect()
                if not client.is_connected():
                    raise ConnectionError("无法连接到Telegram服务器")

            # 通过导入联系人的方式检查手机号
            result = await client(ImportContactsRequest(check_numbers))
            # 从结果中提取用户信息
            resList = result.to_dict().get("users", [])
            # 获取已注册用户的手机号
            new_registered = {res.get("phone") for res in resList}

            # 记录每个号码的检测结果
            log_handler = None
            if hasattr(client, '_log_handler') and callable(client._log_handler):
                log_handler = client._log_handler

            # 处理结果
            for phone in new_numbers:
                is_registered = phone in new_registered or phone in existing_registered

                # 记录日志
                if log_handler:
                    if is_registered:
                        log_handler(f"【注册状态】 {phone} - 已注册✓")
                    else:
                        log_handler(f"【注册状态】 {phone} - 未注册✗")

                # 添加到结果列表
                if phone in new_registered and phone not in existing_registered:
                    registered_numbers.append(phone)

            return registered_numbers

        except Exception as e:
            retry_count += 1
            # 返回错误，由GUI处理
            if retry_count >= max_retries:
                raise

            # 等待后重试
            await asyncio.sleep(2)

            # 如果客户端断开，尝试重新连接
            try:
                if not client.is_connected():
                    await client.connect()
            except Exception as conn_err:
                raise ConnectionError(f"重新连接失败: {str(conn_err)}")

    return []


def clean_phone_numbers(file_content):
    """
    清理和格式化电话号码列表
    Args:
        file_content: 从文件读取的原始行列表
    Returns:
        清理后的电话号码列表
    """
    cleaned_numbers = []
    for line in file_content:
        numbers = line.strip().split()
        for number in numbers:
            if number:
                formatted = normalize_phone_number(number)
                if formatted:
                    cleaned_numbers.append(formatted)
    return cleaned_numbers
