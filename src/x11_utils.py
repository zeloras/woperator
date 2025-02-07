import asyncio
import logging

logger = logging.getLogger(__name__)

async def run_xdotool(cmd):
    """Выполняет команду xdotool"""
    try:
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