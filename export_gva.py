from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import time
import tempfile
import shutil
import logging
from typing import Optional
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

BASE = "https://www.gunviolencearchive.org"
REPORTS_PATH = "/reports/mass-shooting"


@dataclass
class ExportConfig:
    """Configuration for CSV export."""
    year: int
    out_dir: str
    prefix: str
    overwrite: bool = False
    timeout: int = 300
    wait_timeout: int = 30


def setup_headless_browser(download_dir: str) -> webdriver.Chrome:
    """Configure headless Chrome with download settings."""
    options = Options()
    
    # Essential headless configuration
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Minimal logging suppression
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    
    # Anti-detection essentials
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Download settings
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    
    # Use webdriver manager to get the correct ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Set user agent via CDP for comprehensive anti-detection
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": user_agent
    })
    
    return driver


def wait_for_download(download_dir: str, timeout: int = 60) -> Optional[str]:
    """Wait for CSV file to download and return its path."""
    start_time = time.time()
    initial_files = set(os.listdir(download_dir))
    
    while time.time() - start_time < timeout:
        current_files = set(os.listdir(download_dir))
        new_files = current_files - initial_files
        
        if new_files:
            for filename in new_files:
                if filename.endswith('.csv') and not filename.endswith('.crdownload'):
                    return os.path.join(download_dir, filename)

        time.sleep(1)
        
    return None


def export_data(config: ExportConfig, logger: Optional[logging.Logger] = None) -> str:
    """Download mass shooting data CSV file."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    temp_dir = tempfile.mkdtemp()
    driver = setup_headless_browser(temp_dir)
    wait = WebDriverWait(driver, config.wait_timeout)
    
    try:
        logger.info(f"Loading reports page for {config.year}...")
        url = f"{BASE}{REPORTS_PATH}?year={config.year}"
        driver.get(url)
        
        # Wait for page to load by checking for a key element
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except TimeoutException:
            logger.warning("Page load timeout, continuing anyway...")
        
        logger.info("Looking for export link...")
        
        # Look for export link
        export_link = None
        try:
            export_link = driver.find_element(By.CSS_SELECTOR, "a[href*='export-csv']")
        except NoSuchElementException:
            # Try alternative selectors
            try:
                export_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Export') or contains(text(), 'export')]")
            except NoSuchElementException:
                raise RuntimeError("Could not find export link on page")
        
        logger.info("Starting export process...")
        driver.execute_script("arguments[0].click();", export_link)
        
        logger.info("Waiting for export to complete...")
        
        # Custom wait condition for export completion
        def is_complete(driver):
            current_url = driver.current_url
            if "export-finished" in current_url:
                return True
            elif "batch" in current_url:
                return False
            else:
                return False
        
        try:
            wait.until(is_complete)
        except TimeoutException:
            raise RuntimeError(f"Timed out waiting for export to finish after {config.timeout}s")
        
        logger.info("Looking for download link...")
        
        try:
            download_link = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'download') or contains(text(), 'Download')]"))
            )
            
            # Click download
            driver.execute_script("arguments[0].click();", download_link)
            
        except TimeoutException:
            raise RuntimeError("Could not find download link on export-finished page")
        
        logger.info("Downloading file...")
        
        # Wait for file to download (use wait_timeout * 2 for download timeout)
        downloaded_file = wait_for_download(temp_dir, timeout=config.wait_timeout * 2)
        if not downloaded_file:
            raise RuntimeError(f"Download did not complete within {config.wait_timeout * 2}s timeout")
        
        # Move file to target directory with proper naming
        os.makedirs(config.out_dir, exist_ok=True)
        timestamp = dt.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
        target_filename = f"{config.prefix}_{config.year}_{timestamp}.csv"
        target_path = os.path.join(config.out_dir, target_filename)
        
        if os.path.exists(target_path) and not config.overwrite:
            raise ValueError(f"Target file already exists: {target_path}")
        
        shutil.move(downloaded_file, target_path)
        logger.info(f"File saved: {target_path}")
        return target_path
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise
        
    finally:
        logger.info("Closing browser...")
        driver.quit()
        
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir)
        except (OSError, FileNotFoundError):
            pass


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    current_year = dt.datetime.now().year
    p = argparse.ArgumentParser(description="Download GVA mass shooting CSV export using headless browser automation.")
    p.add_argument("--year", type=int, default=current_year, help=f"Year to export (default: {current_year})")
    p.add_argument("--out-dir", default="temp", help="Output directory (default: temp)")
    p.add_argument("--prefix", default="gvatemp", help="Output filename prefix (default: gvatemp)")
    p.add_argument("--timeout", type=int, default=300, help="Export timeout in seconds (default: 300)")
    p.add_argument("--wait-timeout", type=int, default=30, help="WebDriverWait timeout in seconds (default: 30)")
    p.add_argument("--overwrite", action="store_true", help="Overwrite if file already exists")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point."""
    # Check for required dependencies
    try:
        import selenium
        import webdriver_manager
    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("Please install with: pip install selenium webdriver-manager")
        return 1
    
    args = parse_args(argv)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('gva.log', encoding='utf-8')
        ]
    )
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting GVA export...")
        
        config = ExportConfig(
            year=args.year,
            out_dir=args.out_dir,
            prefix=args.prefix,
            overwrite=args.overwrite,
            timeout=args.timeout,
            wait_timeout=args.wait_timeout
        )
        
        result_path = export_data(config, logger)
        
        logger.info(f"Export complete: {result_path}")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
