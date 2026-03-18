import json
from pathlib import Path
import asyncio
import shutil
import os
from playwright.async_api import async_playwright
from src.utils.env_data import ENVDATA
from src.login.standalone_onelogin_auth import OneLoginAuthenticator
from src.utils.setting import USER_DATA_DIR, base_url
from src.utils.logger import setup_logger
from src.modmed.process_statements import process_patient_statements

logger = setup_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
json_path = BASE_DIR / "app" / "app_id.json"

with open(json_path, "r") as f:
    practices = json.load(f)

practice_name, practice_id = list(practices.items())[0]

async def modmed_workflow():

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

                page = auth.page

                if page is None:
                    raise Exception("Authentication failed")

                logger.info("Login successful")

                full_url = f"{base_url}{practice_id}"

                await page.goto(full_url)

                await page.wait_for_timeout(10000)

                logger.info("ModMed page loaded")

                await page.wait_for_timeout(10000)

                # Click dropdown
                await page.click("span.caret")

                await page.wait_for_selector('a[data-account="practicegroup"]')

                await page.wait_for_timeout(5000)

                await page.click('a[data-account="practicegroup"]')

                await page.wait_for_timeout(10000)

                # Billing menu
                await page.click('a[href="/billing/billing_summary"]')

                await page.wait_for_timeout(7000)

                # Patient Statements
                await page.click('a[href="/billing/patient_statements"]')

                await page.wait_for_timeout(10000)

                logger.info("Patient Statements page opened")

                await process_patient_statements(page)

    finally:

        try:
            shutil.rmtree(USER_DATA_DIR)
            logger.info("Cleaned user data directory")
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(modmed_workflow())