#!/usr/bin/env python3
"""Generate PDF from HTML using available tools."""

import subprocess
import sys
from pathlib import Path

def try_playwright():
    """Try using playwright for PDF generation."""
    try:
        from playwright.sync_api import sync_playwright

        html_file = Path(__file__).parent / "cashflow-architecture.html"
        pdf_file = Path(__file__).parent / "cashflow-architecture.pdf"

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_file.absolute()}")

            # Wait for mermaid to be defined and rendered
            page.wait_for_function("typeof mermaid !== 'undefined'")
            page.wait_for_timeout(3000)  # Extra time for rendering

            # Wait for SVG to appear (mermaid renders to SVG)
            page.wait_for_selector("svg", timeout=10000)
            page.wait_for_timeout(1000)  # Extra settling time

            page.pdf(
                path=str(pdf_file),
                format="A4",
                landscape=True,
                print_background=True,
                margin={
                    "top": "20px",
                    "right": "20px",
                    "bottom": "20px",
                    "left": "20px"
                }
            )
            browser.close()

        print(f"✅ PDF generated successfully: {pdf_file}")
        return True
    except ImportError:
        print("⚠️  Playwright not available")
        return False
    except Exception as e:
        print(f"⚠️  Playwright failed: {e}")
        return False

def try_weasyprint():
    """Try using weasyprint for PDF generation."""
    try:
        from weasyprint import HTML

        html_file = Path(__file__).parent / "cashflow-architecture.html"
        pdf_file = Path(__file__).parent / "cashflow-architecture.pdf"

        HTML(filename=str(html_file)).write_pdf(pdf_file)

        print(f"✅ PDF generated successfully: {pdf_file}")
        return True
    except ImportError:
        print("⚠️  WeasyPrint not available")
        return False
    except Exception as e:
        print(f"⚠️  WeasyPrint failed: {e}")
        return False

def try_chrome_headless():
    """Try using Chrome/Chromium in headless mode."""
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "google-chrome",
        "chromium",
        "chromium-browser"
    ]

    html_file = Path(__file__).parent / "cashflow-architecture.html"
    pdf_file = Path(__file__).parent / "cashflow-architecture.pdf"

    for chrome_path in chrome_paths:
        try:
            result = subprocess.run(
                [
                    chrome_path,
                    "--headless",
                    "--disable-gpu",
                    "--print-to-pdf=" + str(pdf_file),
                    "--no-margins",
                    str(html_file.absolute())
                ],
                capture_output=True,
                timeout=10
            )

            if result.returncode == 0 and pdf_file.exists():
                print(f"✅ PDF generated successfully: {pdf_file}")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        except Exception as e:
            print(f"⚠️  Chrome at {chrome_path} failed: {e}")
            continue

    print("⚠️  Chrome/Chromium not available or failed")
    return False

def main():
    """Try different methods to generate PDF."""
    print("Attempting to generate PDF from HTML...")
    print()

    methods = [
        ("Playwright", try_playwright),
        ("Chrome Headless", try_chrome_headless),
        ("WeasyPrint", try_weasyprint),
    ]

    for name, method in methods:
        print(f"Trying {name}...")
        if method():
            return 0
        print()

    print("❌ Could not generate PDF with any available method.")
    print()
    print("To generate the PDF, you can:")
    print("1. Install playwright: pip install playwright && playwright install chromium")
    print("2. Open cashflow-architecture.html in your browser and use Print to PDF")
    print("3. Install Chrome and we'll use headless mode")

    return 1

if __name__ == "__main__":
    sys.exit(main())
