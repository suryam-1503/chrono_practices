import os
import asyncio
from pathlib import Path
from playwright.async_api import Page
from src.gsheet.statements import get_mrn_rows, update_download_status
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
DOWNLOAD_DIR = Path.home() / "Documents" / "Arya -chrono"


async def get_pdf_page(page: Page):
   
    existing_pages = page.context.pages.copy()

    for _ in range(5):
        if len(page.context.pages) > len(existing_pages):
            break
        await asyncio.sleep(1)

    pdf_page = page.context.pages[-1]
    await pdf_page.wait_for_load_state("domcontentloaded")

    return pdf_page


async def download_pdf(pdf_page: Page, mrn: str):
    

    pdf_url = pdf_page.url

    if not pdf_url.startswith("http"):
        raise Exception(f"Invalid PDF URL: {pdf_url}")

    file_path = DOWNLOAD_DIR / f"{mrn}.pdf"

    response = await pdf_page.request.get(pdf_url)
    pdf_bytes = await response.body()

    if not pdf_bytes.startswith(b"%PDF"):
        raise Exception("Downloaded file is not a valid PDF")

    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    logger.info(f"PDF saved: {file_path}")


async def find_matching_row(page: Page, mrn: str, balance: str):
    

    table = page.locator("div.table_container table").first
    rows = table.locator("tbody tr")

    count = await rows.count()
    logger.info(f"Rows found: {count}")

    for i in range(count):
        row = rows.nth(i)
        cells = row.locator("td")

        cell_count = await cells.count()

        # Safety check
        if cell_count < 14:
            continue

        #  Based on YOUR table structure
        chart_id = (await cells.nth(2).inner_text()).strip()
        stmt_bal = (await cells.nth(12).inner_text()).strip()

        if chart_id == mrn:
            logger.info(f"MRN matched: {mrn}")

            # Normalize balance (remove - sign differences)
            clean_ui_bal = stmt_bal.replace("-", "").strip()
            clean_sheet_bal = balance.replace("-", "").strip()

            if clean_ui_bal == clean_sheet_bal:
                logger.info("Balance matched")
                return row, "MATCH"
            else:
                logger.warning(f"Balance mismatch: UI={stmt_bal}, Sheet={balance}")
                return None, "BALANCE_MISMATCH"

    return None, "MRN_NOT_FOUND"


async def process_patient_statements(page: Page):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    mrn_rows = get_mrn_rows()
    logger.info(f"Total MRNs to process: {len(mrn_rows)}")

    for item in mrn_rows:
        mrn = item["mrn"]
        balance = item["balance"]
        row = item["row"]

        for attempt in range(3):
            try:
                logger.info(f"Processing MRN: {mrn} (Attempt {attempt+1})")

                # --- Search patient ---
                await page.fill("#id-patient-search", "")
                await page.fill("#id-patient-search", mrn)

                await page.wait_for_timeout(1500)
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("Enter")

                await page.wait_for_timeout(1000)
                await page.locator("button.btn-primary:has-text('Search')").click()

                # Wait for results
                await page.wait_for_load_state("networkidle")

                rows = page.locator("table tbody tr")
                await rows.first.wait_for(state="attached", timeout=20000)

                await asyncio.sleep(2)

                count = await rows.count()
                

                if count == 0:
                        raise Exception("No rows found after search")

                # --- Find matching row ---
                matched_row, status = await find_matching_row(page, mrn, balance)

                if status == "MRN_NOT_FOUND":
                    update_download_status(row, "MRN not found")
                    break

                if status == "BALANCE_MISMATCH":
                    update_download_status(row, "Balance not matching")
                    break

                # --- Click Preview (CORRECT WAY) ---
                preview_btn = matched_row.locator("a.btn-link:has-text('Preview')")

                await preview_btn.wait_for(state="visible", timeout=10000)
                await preview_btn.scroll_into_view_if_needed()

                try:
                    await preview_btn.click(timeout=5000)
                    logger.info("Preview clicked (normal)")
                except:
                    logger.warning("Normal click failed → using force click")
                    await preview_btn.click(force=True)

                await asyncio.sleep(4)

                # --- Get PDF tab ---
                pdf_page = await get_pdf_page(page)

                # --- Download PDF ---
                await download_pdf(pdf_page, mrn)

                # --- Update Sheet ---
                update_download_status(row, "Download Completed")
                logger.info(f"Updated Google Sheet for row {row}")

                # Close PDF tab
                if pdf_page != page:
                    await pdf_page.close()

                await asyncio.sleep(2)
                break

            except Exception as e:
                logger.error(f"Attempt {attempt+1} failed for MRN {mrn}: {e}")

                if attempt == 2:
                    logger.error(f"Final failure for MRN {mrn}")
                    update_download_status(row, "Download failed")
                else:
                    await asyncio.sleep(3)

    logger.info("Process completed for all MRNs.")

    