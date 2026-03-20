# src/modmed/modmed_main.py
import asyncio
import json
import shutil
import os
from pathlib import Path
from src.utils.logger import setup_logger
from src.utils.setting import USER_DATA_DIR, base_url
from src.utils.env_data import ENVDATA
from src.Onelogin_authentication.standalone_onelogin_auth import OneLoginAuthenticator
from src.modmed.process_statements import process_patient_statements
from src.utils.stop_signal import stop_event, reset_stop, check_stop_flag
from playwright.async_api import async_playwright

logger = setup_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
json_path = BASE_DIR / "app" / "app_id.json"

with open(json_path, "r") as f:
    practices = json.load(f)

practice_name, practice_id = list(practices.items())[0]

async def safe_wait(ms: int):
    steps = int(ms / 100)
    for _ in range(steps):
        if check_stop_flag():
            logger.info("Stopped during wait")
            return False
        await asyncio.sleep(0.1)
    return True



async def modmed_workflow():
    """Main async workflow"""
    if check_stop_flag():
        logger.info("Workflow stopped before start")
        return

    try:
        if os.path.exists(USER_DATA_DIR):
            shutil.rmtree(USER_DATA_DIR)
        os.makedirs(USER_DATA_DIR, exist_ok=True)

        async with async_playwright() as playwright:
            async with OneLoginAuthenticator(
                subdomain=ENVDATA.ONELOGIN_SUBDOMAIN,
                username=ENVDATA.ONELOGIN_USERNAME,
                password=ENVDATA.ONELOGIN_PASSWORD,
                client_id=ENVDATA.ONELOGIN_CLIENT_ID,
                client_secret=ENVDATA.ONELOGIN_CLIENT_SECRET,
                headless=False,
                user_data_dir=USER_DATA_DIR,
                enable_extension=True,
                target_app_url="dummy"
            ) as auth:

                await auth.authenticate()

                if check_stop_flag():
                    logger.info("Stopped after login")
                    return

                page = auth.page
                
                if page is None:
                    raise Exception("Authentication failed")

                logger.info("Login successful")

                full_url = f"{base_url}{practice_id}"
                await page.goto(full_url)

                if not await safe_wait(5000):
                    return

                logger.info("ModMed page loaded")

                # Dropdown
                await page.click("span.caret")
                if check_stop_flag(): return

                await page.wait_for_selector('a[data-account="practicegroup"]')

                if not await safe_wait(2000):
                    return

                await page.click('a[data-account="practicegroup"]')

                if not await safe_wait(3000):
                    return

                # Billing
                await page.click('a[href="/billing/billing_summary"]')

                if not await safe_wait(3000):
                    return

                # Patient Statements
                await page.click('a[href="/billing/patient_statements"]')

                if not await safe_wait(3000):
                    return

                logger.info("Patient Statements page opened")

                if check_stop_flag():
                    return

                await process_patient_statements(page)


    finally:
        try:
            shutil.rmtree(USER_DATA_DIR)
            logger.info("Cleaned user data directory")
        except Exception:
            pass


# Wrapper functions for server control
def run_workflow(headless=False):
    """Run workflow synchronously for thread"""
    reset_stop()
    try:
        logger.info("Starting ModMed workflow")
        asyncio.run(modmed_workflow())
        logger.info("ModMed workflow finished")
    except Exception as e:
        logger.error(f"Workflow error: {e}")


def stop_workflow():
    stop_event.set()
    logger.info("Stop signal sent")


def check_stop_flag_status():
    return stop_event.is_set()


# For standalone testing
if __name__ == "__main__":
    asyncio.run(modmed_workflow())