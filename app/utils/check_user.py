import gspread
import pandas as pd
import numpy as np
import configparser
import os
import logging

from typing import Union


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger.error("Starting check user")

WORKSHEET = 0
WORKSHEET_CHAT_ID = 2
HOME_DIRECTORY = os.getcwd()
TABLE_ID = os.getenv("TABLE_ID")

# prepared text for answer
text_config = configparser.ConfigParser()
text_config.read(f"{HOME_DIRECTORY}/text_settings.conf")

text_three = text_config["text_2_vet_safe"]["text_three"]
text_four = text_config["text_2_vet_safe"]["text_four"]
text_err = text_config["text_2_vet_safe"]["text_err"]


class NotUniquePhone(Exception):
    pass


def get_string_phone(text: str) -> str:
    return f"+7 ({text[1:4]}) {text[4:7]}-{text[7:9]}-{text[9:]}"


def get_int_phone(text: str) -> int:
    return (
        text.replace("+", "")
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .replace("-", "")
    )


def update_data_worksheet(table_id: str, df: pd.DataFrame, worksheet: int = 0):
    """update info data from google docs."""
    logger.error("update data_worksheet start")
    gs = gspread.service_account(filename=f"{HOME_DIRECTORY}/credits.json")
    sh = gs.open_by_key(table_id)

    logger.error("read worksheet")
    worksheet = sh.get_worksheet(worksheet)
    logger.error("update worksheet")
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    logger.error("update worksheet finish")


def get_data_wooksheet(table_id: str) -> pd.DataFrame:
    """get info data from google docs."""

    logger.error("get_data_wooksheet")
    gs = gspread.service_account(filename=f"{HOME_DIRECTORY}/credits.json")
    sh = gs.open_by_key(table_id)

    return sh


def check_user_on_his_id(user_id: int) -> Union[bool, str, str, str]:
    sh = get_data_wooksheet(table_id=TABLE_ID)

    logger.error("check_user_on_his_id")
    df_with_chat_id = pd.DataFrame(
        sh.get_worksheet(WORKSHEET_CHAT_ID).get_all_records()
    )
    if user_id in df_with_chat_id.chat_id.to_list():
        telephone = df_with_chat_id[df_with_chat_id.chat_id == user_id].Phone.values[0]
        code = df_with_chat_id[df_with_chat_id.chat_id == user_id].id.values[0]
        return True, telephone, user_id, code
    return False, "", "", ""


def input_telphone_number_and_check(
    telephone_number: str, current_chat_id: str
) -> Union[bool, str]:

    sh = get_data_wooksheet(table_id=TABLE_ID)

    df_main = pd.DataFrame(
        sh.get_worksheet(WORKSHEET).get_all_records()
    ).drop_duplicates(subset=["Phone"])

    if df_main[df_main.Phone == telephone_number].empty:
        return False, text_three
    else:
        # update if chat_id is null
        if df_main[df_main.Phone == telephone_number].shape[0] > 1:
            raise NotUniquePhone(
                f"In your google file has duplicates in phone number. {telephone_number}"
            )

        df_with_chat_id = pd.DataFrame(
            sh.get_worksheet(WORKSHEET_CHAT_ID).get_all_records()
        ).drop_duplicates(subset=["Phone"])

        logger.error(f"CHAT ID - {df_with_chat_id}")
        df = df_main.merge(
            df_with_chat_id[["Phone", "chat_id", "id"]], how="left", on=["Phone"]
        )
        df.chat_id = df.chat_id.fillna(0)

        chat_id = df[df.Phone == telephone_number].chat_id.values[0]
        code = df[df.Phone == telephone_number].id.values[0]

        # write new chat_id for new user
        if chat_id == pd.NaT or chat_id == 0 or chat_id == "":
            code = df_with_chat_id.id.max() + 1
            df = df.assign(
                chat_id=lambda x: np.where(
                    x.Phone == telephone_number, current_chat_id, x.chat_id
                ),
                id=lambda x: np.where(x.Phone == telephone_number, code, x.id),
            )
            df = df.dropna()

            logger.error(f"LOG - {df[['Phone', 'chat_id', 'id']]}")
            update_data_worksheet(
                table_id=TABLE_ID,
                df=df[["Phone", "id", "chat_id"]],
                worksheet=WORKSHEET_CHAT_ID,
            )

            return True, f"{text_four} : {code}"
        # check chat_id
        else:
            if current_chat_id == chat_id:
                return True, f"{text_four} : {code}"
            else:
                return False, text_three
