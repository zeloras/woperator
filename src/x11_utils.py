import asyncio
import logging
from typing import List, Optional, Tuple
import time

logger = logging.getLogger(__name__)

# Store last mouse position to avoid redundant moves
_last_mouse_pos: Tuple[int, int] = (0, 0)
_last_move_time: float = 0
MOVE_THROTTLE = 1/60  # Возвращаем к 60Hz для стабильности

async def run_xdotool(cmd: List[str], throttle: bool = False) -> bool:
    """Выполняет команду xdotool с опциональным троттлингом

    Args:
        cmd: Список аргументов для xdotool
        throttle: Применять ли троттлинг (для движений мыши)

    Returns:
        bool: True если команда выполнена успешно
    """
    global _last_mouse_pos, _last_move_time
    
    try:
        # For mouse moves, check if we should throttle
        if throttle and cmd[0] == 'mousemove':
            current_time = time.time()
            if current_time - _last_move_time < MOVE_THROTTLE:
                return True
            
            new_pos = (int(cmd[1]), int(cmd[2]))
            if new_pos == _last_mouse_pos:
                return True
                
            _last_mouse_pos = new_pos
            _last_move_time = current_time
        
        process = await asyncio.create_subprocess_exec(
            'xdotool', *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={'DISPLAY': ':99'}
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"xdotool error: {stderr.decode()}")
            return False
        return True
        
    except Exception as e:
        logger.error(f"Error running xdotool: {str(e)}")
        return False

async def move_mouse(x: int, y: int) -> bool:
    """Перемещает курсор мыши с троттлингом

    Args:
        x: X координата
        y: Y координата

    Returns:
        bool: True если перемещение выполнено успешно
    """
    # Используем абсолютные координаты
    return await run_xdotool(['mousemove', str(x), str(y)], throttle=True)

async def click_mouse(x: int, y: int, button: int = 1) -> bool:
    """Выполняет клик мышью

    Args:
        x: X координата
        y: Y координата
        button: Номер кнопки (1=левая, 2=средняя, 3=правая)

    Returns:
        bool: True если клик выполнен успешно
    """
    if await move_mouse(x, y):
        return await run_xdotool(['click', str(button)])
    return False

async def type_text(text: str) -> bool:
    """Вводит текст

    Args:
        text: Текст для ввода

    Returns:
        bool: True если ввод выполнен успешно
    """
    return await run_xdotool(['type', text])

async def send_key(key: str) -> bool:
    """Отправляет нажатие клавиши

    Args:
        key: Название клавиши в формате xdotool (например, 'Return', 'Tab', etc.)

    Returns:
        bool: True если нажатие выполнено успешно
    """
    return await run_xdotool(['key', key]) 