import asyncio
import json
from threading import Thread
from typing import List

from android_utils import android_open_file, android_save_string_to_file
from db.address_data import AddressData
from db.tx_data import TxData
from db.wallet_data import WalletData
from kivy import platform
from kivy.logger import Logger
from kivy.logger import LoggerHistory
from datetime import datetime


def get_logs() -> str:
    logs = ""
    for log_record in reversed(LoggerHistory.history):
        log_time = datetime.utcfromtimestamp(int(log_record.created)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        logs += f"{log_time} {log_record.message} \n"
    return logs


def limit_length(text, max_length):
    if len(text) > max_length:
        text = text[: max_length - 2] + "..."
    return text


def bip_329_record(type, ref, label):
    return json.dumps(
        {
            "type": type,
            "ref": ref,
            "label": label,
        }
    )


def export_labels_to_file(label_lines: List[str]):
    content_str = ""
    for line in label_lines:
        content_str += line + "\n"
    Logger.info(content_str)

    if platform == "android":
        android_save_string_to_file(
            file_name="wkwallet_labels.jsonl", content_str=content_str
        )


def import_labels_from_file(target_wallet_data: WalletData = None):
    def import_labels(label_jsonl_list: List[str]):
        Logger.info(f"Importing labels to wallet {target_wallet_data.name}")
        for label_jsonl in label_jsonl_list:
            import_label_jsonl(json.loads(label_jsonl), target_wallet_data)

    if platform == "android":
        android_open_file(callback=import_labels)


def import_label_jsonl(label_jsonl, target_wallet_data: WalletData):
    type, ref, label = (
        label_jsonl["type"],
        label_jsonl["ref"],
        label_jsonl["label"],
    )
    Logger.info(f"{type}, {ref}, {label}")

    if type == "tx":
        for tx_data in TxData.select().where(TxData.tx_id == ref):
            if target_wallet_data is None or tx_data.wallet == target_wallet_data:
                tx_data.label = label
                tx_data.save()
                Logger.debug(f"Tx label saved: {label} -> {ref}")
    elif type == "addr":
        for addr_data in AddressData.select().where(AddressData.address_str == ref):
            if (
                target_wallet_data is None
                or addr_data.account.wallet == target_wallet_data
            ):
                addr_data.label = label
                addr_data.save()
                Logger.debug(f"Addr label saved: {label} -> {ref}")
    elif type == "xpub":
        if target_wallet_data.accounts[0].xpub == ref:
            target_wallet_data.name = label
            target_wallet_data.save()
            Logger.debug(f"Xpub label saved: {label} -> {ref}")


def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


def create_async_io_background_loop():
    bg_loop = asyncio.new_event_loop()
    Thread(target=start_background_loop, args=(bg_loop,), daemon=True).start()
    return bg_loop
