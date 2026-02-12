import os
import asyncio
from playwright.async_api import async_playwright

async def get_playwright_chromium_path():
    """
    Uses Playwright's async API to obtain the path to the Chromium binary.
    If the binary is not present, installs it via Playwright.
    """
    async with async_playwright() as p:
        chromium_path = p.chromium.executable_path

    if not os.path.exists(chromium_path):
        print(f"Chromium not found at {chromium_path}. Installing via Playwright...")
        # Run the playwright install command asynchronously
        process = await asyncio.create_subprocess_exec(
            "playwright", "install", "chromium",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise Exception(f"Playwright install failed: {stderr.decode()}")
        async with async_playwright() as p:
            chromium_path = p.chromium.executable_path
    return chromium_path
