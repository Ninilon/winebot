import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Router, types, html, F
from aiogram.filters import Command, CommandObject
from utils.language_manager import language_manager

router = Router()

@router.message(Command("whois"))
async def cmd_whois_sys(message: types.Message, command: CommandObject):
    if not command.args:
        error_text = language_manager.get_text('error', message.from_user.id)
        return await message.answer(f"{error_text}: Please provide domain/IP: `/whois 8.8.8.8`")

    target = command.args.strip()
    
    # Run system whois command
    proc = await asyncio.create_subprocess_exec(
        'whois', target,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    
    # Whois outputs a lot of text, take first 20 lines or search for important fields
    full_output = stdout.decode(errors='ignore')
    important_info = []
    for line in full_output.splitlines():
        if any(key in line.lower() for key in ["country:", "organization:", "netname:", "isp:", "as:"]):
            important_info.append(line.strip())

    if not important_info:
        # If nothing important found, show a piece of output
        result_text = html.code(full_output[:500] + "...")
    else:
        result_text = html.code("\n".join(important_info))

    whois_text = language_manager.get_text('whois_info', message.from_user.id)
    await message.answer(f"🔍 {html.bold(whois_text + ' ' + target + ':')}\n\n{result_text}", parse_mode="HTML")

@router.message(Command("status"))
async def cmd_status(message: types.Message, command: CommandObject):
    if not command.args:
        error_text = language_manager.get_text('error', message.from_user.id)
        return await message.answer(f"{error_text}: Please provide domain/IP: `/status example.com`")

    target = command.args.strip()
    checking_text = language_manager.get_text('status_checking', message.from_user.id)
    await message.answer(f"{checking_text} {target}...")
    
    # Simple ping/trace to check status
    proc = await asyncio.create_subprocess_exec(
        'ping', '-c', '3', target,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    
    if proc.returncode == 0:
        # Parse ping output for basic stats
        output = stdout.decode(errors='ignore')
        lines = output.splitlines()
        
        # Extract useful information
        result_text = "✅ " + language_manager.get_text('success', message.from_user.id) + "\n"
        result_text += html.code(output[:300] + "..." if len(output) > 300 else output)
    else:
        error_text = language_manager.get_text('not_found', message.from_user.id)
        result_text = f"❌ {error_text}\n" + html.code(stderr.decode(errors='ignore')[:200])

    await message.answer(result_text, parse_mode="HTML")
