import os
import asyncio
from pathlib import Path
from playwright.async_api import Page
from src.gsheet.statements import get_mrn_rows, update_download_status
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
DOWNLOAD_DIR = Path.home() / "Documents" / "Arya -chrono"


async def click_preview(page: Page):
    """Robust Preview click handler (Angular safe)"""

    await page.wait_for_selector("a.btn-link:has-text('Preview')", timeout=20000)

    preview_buttons = page.locator("a.btn-link:has-text('Preview')")
    count = await preview_buttons.count()
    logger.info(f"Preview buttons found: {count}")

    preview_btn = preview_buttons.first

    await preview_btn.scroll_into_view_if_needed()
    await page.wait_for_timeout(1000)

    try:
        await preview_btn.click(timeout=5000)
        logger.info("Preview clicked normally")
    except:
        logger.warning("Normal click failed → using JS click")

        await page.evaluate("""
        () => {
            const btns = Array.from(document.querySelectorAll('a.btn-link'));
            const preview = btns.find(el => el.innerText.trim() === 'Preview');
            if (preview) preview.click();
        }
        """)
        logger.info("Preview clicked using JS")

    await asyncio.sleep(4)


async def get_pdf_page(page: Page):
    """Get PDF tab reliably"""

    existing_pages = page.context.pages.copy()

    # Wait for new tab to appear
    for _ in range(5):
        if len(page.context.pages) > len(existing_pages):
            break
        await asyncio.sleep(1)

    pdf_page = page.context.pages[-1]
    await pdf_page.wait_for_load_state("domcontentloaded")

    return pdf_page


async def download_pdf(pdf_page: Page, mrn: str):
    """Download PDF using browser session (FIXED)"""

    pdf_url = pdf_page.url


    if not pdf_url.startswith("http"):
        raise Exception(f"Invalid PDF URL: {pdf_url}")

    file_path = DOWNLOAD_DIR / f"{mrn}.pdf"

    #  FIX: Use browser session request (NO expect_download)
    response = await pdf_page.request.get(pdf_url)
    pdf_bytes = await response.body()

    # Validate PDF (prevents corrupted files)
    if not pdf_bytes.startswith(b"%PDF"):
        raise Exception("Downloaded file is not a valid PDF")

    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    logger.info(f"PDF saved: {file_path}")


async def process_patient_statements(page: Page):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    mrn_rows = get_mrn_rows()
    logger.info(f"Total MRNs to process: {len(mrn_rows)}")

    for item in mrn_rows:
        mrn = item["mrn"]
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
                await page.wait_for_selector("a.btn-link:has-text('Preview')", timeout=20000)
                await asyncio.sleep(2)

                # --- Click Preview ---
                await click_preview(page)

                # --- Get PDF tab ---
                pdf_page = await get_pdf_page(page)

                # --- Download PDF ---
                await download_pdf(pdf_page, mrn)

                # --- Update Sheet ---
                update_download_status(row)
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
                else:
                    await asyncio.sleep(3)

    logger.info("Process completed for all MRNs.")