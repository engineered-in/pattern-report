# -*- coding: utf-8 -*-
import logging
import re
import string
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import fitz  # PyMuPDF
import toml
from pandas import DataFrame, ExcelWriter, concat
from tqdm import tqdm

BASE_DIR = Path(__file__).parent
SCAN_DIR = BASE_DIR / "Documents"
LOG_DIR = BASE_DIR / "logs"
if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = BASE_DIR / "Reports"
OUTPUT_FILE = OUTPUT_DIR / datetime.now().strftime("Report_%Y-%m-%d_%H-%M-%S.xlsx")
CONFIG_FILE = BASE_DIR / "config.toml"

CONFIG = {"PATTERNS": ["HOLD \\d+"], "DOCUMENT_PATH": "", "EXPORT_ALL_TEXT": False}
logger = logging.getLogger("main")

file_handler = TimedRotatingFileHandler(
    "logs/app.log",  # Log file path
    when="midnight",  # Rotate at midnight
    interval=1,  # Every 1 day
    backupCount=7,  # Keep last 7 log files
    encoding="utf-8",
)
file_handler.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[file_handler, stream_handler],
)


def remove_non_readable(text: str) -> str:
    allowed_chars = (
        string.ascii_letters + string.digits + string.punctuation + string.whitespace
    )
    return "".join(char for char in text if char in allowed_chars)


def get_texts(page: fitz.Page):
    """Extracts text from a PDF page and returns it in a structured format.
    This function processes a PDF page to extract text blocks, their bounding boxes,

    Args:
        page (fitz.Page): The PDF page from which to extract text.
        scale (float, optional): Scale factor. Defaults to 1.0.

    Returns:
        List: A list of dictionaries, each containing text and its bounding box coordinates.
        The structure of each dictionary is:
        {
            "text": str,  # The extracted text
            "x1": float,  # x-coordinate of the top-left corner
            "y1": float,  # y-coordinate of the top-left corner
            "x2": float,  # x-coordinate of the bottom-right corner
            "y2": float,  # y-coordinate of the bottom-right corner
            "score": int,  # Confidence score (default is 100)
        }
    """
    page_number = page.number + 1  # Get the page number
    file = Path(page.parent.name).resolve()
    hyperlink = f'''=HYPERLINK("{file.as_uri()}#page={page_number}", "{file.stem}")'''
    texts = []
    text_dict = page.get_text("dict")
    for block in text_dict["blocks"]:
        if block["type"] == 0:  # text blocks
            for line in block["lines"]:
                text_match = {}
                text = " ".join(
                    [span["text"] for span in line["spans"]]
                )  # TODO check SPACE delimiter
                text_match["File"] = hyperlink
                text_match["Page"] = page_number
                text_match["Text"] = remove_non_readable(text)
                x1, y1, x2, y2 = line["bbox"]
                text_match["x1"] = x1
                text_match["y1"] = y1
                text_match["x2"] = x2
                text_match["y2"] = y2
                text_match["Score"] = 100

                texts.append(text_match)
    return DataFrame(texts)


def main():
    logger.info(f"Configuration file: {CONFIG_FILE}")
    logger.info(f"Scanning files under folder: {SCAN_DIR}")
    logger.info(f"Using pattern: {CONFIG['PATTERNS']}")
    dfs = []
    results = []
    pdf_files = []

    # Scan the directory for PDF files
    for root, dirs, files in SCAN_DIR.walk():
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_files.append(root / file)

    # Process each PDF file
    for file in tqdm(pdf_files, desc="Processing PDFs", unit="file"):
        logger.debug(f"Processing file: {file}")
        doc = fitz.open(file)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            dfs.append(get_texts(page))
        doc.close()

    logger.info(f"Total files processed: {len(pdf_files)}")

    # Short-circuit if no text blocks are extracted
    if not dfs or all(df.empty for df in dfs):
        logger.info("No text blocks extracted. Exiting without searching for patterns.")
        return 1

    df = concat(dfs, ignore_index=True)
    logger.info(f"Total text blocks extracted: {len(df)}")
    logger.info("Searching for patterns in extracted text...")
    for i, record in tqdm(
        df.iterrows(), desc="Searching Patterns", total=len(df), unit="text block"
    ):
        for j, pattern in enumerate(CONFIG["PATTERNS"], start=1):
            for match in re.findall(pattern, record["Text"], re.IGNORECASE):
                data = record.to_dict()
                data["Pattern"] = f"Pattern_{j}"
                data["Match"] = match
                results.append(data)

    logger.info(f"Total matches found: {len(results)}")
    logger.info("Generating Report...")
    columns = [
        "File",
        "Page",
        "Text",
        "x1",
        "y1",
        "x2",
        "y2",
        "Score",
        "Pattern",
        "Match",
    ]
    df_results = DataFrame(results, columns=columns)

    # Short-circuit if no matches found
    if df_results.empty:
        logger.info("No matches found. Exiting without generating report.")
        return 1

    # Group by File, Page, and Match and get the count of matches
    df_summary = df_results.loc[:, ["File", "Page", "Pattern", "Match"]]
    df_summary = (
        df_summary.groupby(["File", "Page", "Pattern", "Match"])
        .size()
        .reset_index(name="Count")
        .sort_values(
            by=["File", "Page", "Pattern", "Count", "Match"],
            ascending=[True, True, True, False, True],
        )
    )

    df_legend = [
        [f"Pattern_{i}", pattern]
        for i, pattern in enumerate(CONFIG["PATTERNS"], start=1)
    ]
    df_legend.append(["", ""])
    df_legend.append(["Generated by PDF Pattern Search", ""])
    df_legend.append(
        [
            '=HYPERLINK("https://github.com/engineered-in/pattern-report?tab=readme-ov-file#pattern-report","Readme")',
            "",
        ]
    )
    df_legend.append(["", ""])
    df_legend.append(["Have a problem or suggestion?", ""])
    df_legend.append(
        [
            '=HYPERLINK("https://github.com/engineered-in/pattern-report/issues/new", "Report an issue")',
            "",
        ]
    )
    df_legend.append(["or", ""])
    df_legend.append(
        ['=HYPERLINK("https://www.linkedin.com/in/swarupselvaraj/", "Contact me")', ""]
    )

    df_legend = DataFrame(df_legend, columns=["Pattern Id", "Regular Expression"])

    # Save the results to different sheets in an Excel file
    with ExcelWriter(f"{OUTPUT_FILE}", engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Summary", index=False)
        df_results.to_excel(writer, sheet_name="Details", index=False)
        if CONFIG.get("EXPORT_ALL_TEXT", False):
            df.to_excel(writer, sheet_name="Text Blocks", index=False)
        df_legend.to_excel(writer, sheet_name="Legend", index=False)

    logger.info(f"Report generated: {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory created: {OUTPUT_DIR}")

    if CONFIG_FILE.exists():
        try:
            CONFIG.update(toml.load(CONFIG_FILE))
            logger.info(f"Configuration loaded from {CONFIG_FILE}")
        except toml.TomlDecodeError as e:
            logger.error(f"Error decoding TOML file: {e}")
            logger.info("Using default factory configuration instead.")
    else:
        logger.warning(f"Configuration file not found: {CONFIG_FILE}")
        logger.info("Using default factory configuration instead.")

    if CONFIG.get("DOCUMENT_PATH", ""):
        SCAN_DIR = BASE_DIR / CONFIG["DOCUMENT_PATH"]

    # Short-circuit if the scan directory does not exist
    if not SCAN_DIR.exists():
        logger.error(f"Scan directory does not exist: {SCAN_DIR}")
        SCAN_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created scan directory: {SCAN_DIR}")
        logger.info("Please place your documents in the 'Documents' directory.")
        sys.exit(1)

    code = main()
    sys.exit(code)
