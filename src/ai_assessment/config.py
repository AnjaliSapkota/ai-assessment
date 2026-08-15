from pathlib import Path

SOURCE_DOCUMENTS = {
    "source_1": {
        "name": "AM2-P1 datasheet",
        "url": "https://www.deyeinverter.com/deyeinverter/2023/10/07/datasheet_sun-4-12k-g06p3-eu-am2-p1_231007_en.pdf",
    },
    "source_2": {
        "name": "AM2 datasheet",
        "url": "https://www.deyeinverter.com/deyeinverter/2024/03/20/datasheet_sun-4-15k-g06p3-eu-am2_240318_en.pdf",
    },
}

TARGET_MODEL = "SUN-5K-G06P3"


DATA_DIR = Path("data")
RAW_DATA_DIR = DATA_DIR / "raw"
EXTRACTED_DATA_DIR = DATA_DIR / "extracted"
PARSED_DATA_DIR = DATA_DIR / "parsed"
NORMALIZED_DATA_DIR = DATA_DIR / "normalized"
OUTPUT_DIR = Path("output")