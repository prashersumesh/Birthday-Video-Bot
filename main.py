import multiprocessing
import os
import sys
from datetime import datetime
from pathlib import Path
import logging

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from moviepy.config import change_settings
from moviepy.editor import concatenate_videoclips

from src.utils import ProcessWorkbooks, convert_keys, count_files_in_directory
from src.video_generator import Animate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler(sys.stdout)],
)

if sys.platform != "linux":
    change_settings(
        {
            "IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
        }
    )


def process_workbook(df: pd.DataFrame, workbook_name: str):
    workbook_filter = ProcessWorkbooks(df=df)
    workbook_dict = workbook_filter.convert_to_dict()
    for k, v in workbook_dict.items():
        if len(v) > 0:
            logging.info(f"Total {len(v)} birthdays on {k}")
            for _, v_ in v.items():
                v_ = convert_keys(v_)
                party_kid_name = v_["birthday_child"]

                workbook_name = workbook_name.lower().replace(" ", "_")

                party_kid_name = party_kid_name.split()[0].upper()

                save_pth_pr = Path(f"video/{str(k)}")
                save_pth_pr.mkdir(parents=True, exist_ok=True)

                save_dir = f"{save_pth_pr}/{party_kid_name}.mp4"
                save_dir = Path(save_dir)

                if save_dir.exists():
                    logging.info(
                        f"Video already exists for {party_kid_name} for {str(k)}. Skipping."
                    )
                else:
                    animate = Animate(template_vid_pth="template.mp4")
                    final_video = animate.generate_bday_vid(
                        kid_name=party_kid_name, animation="roll"
                    )

                    final_video = concatenate_videoclips([final_video] * 5)
                    final_video.write_videofile(
                        str(save_dir),
                        fps=30,
                        codec="libx264",
                        threads=multiprocessing.cpu_count(),
                    )

                    logging.info(f"Video saved for {party_kid_name} on {workbook_name}")
        else:
            logging.info(f"No birthdays on {k}")


def get_workbooks_from_google_sheets(sheet_id: str):
    os.makedirs(
        "worksheets",
        exist_ok=True,
    )

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file("static/creds.json", scopes=scopes)
    client = gspread.authorize(creds)
    workbook = client.open_by_key(sheet_id)

    mapp = {}
    for worksheet in workbook.worksheets():
        data = worksheet.get_all_values()
        if data:
            df = pd.DataFrame(data[1:], columns=data[0])
        else:
            df = pd.DataFrame()

        filename = "".join(
            [c for c in worksheet.title if c.isalnum() or c in (" ", "_")]
        ).rstrip()

        csv_path = os.path.join("worksheets", f"{filename}.csv")

        df.to_csv(csv_path, index=False)
        mapp[filename] = pd.read_csv(csv_path, header=None)

    return mapp


if __name__ == "__main__":
    sheet_id = "1gVJP3Locqtp5k0tpI2XOWKEZHMp5yHt4m2A5gb5BZdU"
    workbooks_mapp = get_workbooks_from_google_sheets(sheet_id=sheet_id)

    for k, v in workbooks_mapp.items():
        if "print" in k.lower():
            pass
        else:
            process_workbook(df=v, workbook_name=k)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Task complete for today's date: {current_time}")
