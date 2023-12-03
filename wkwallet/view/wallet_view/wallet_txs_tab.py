from typing import List

from kivy.clock import mainthread
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.recycleview import RecycleView
from kivymd.uix.tab import MDTabsBase
from model.exchange_rate_manager import exchange_rate_manager
from tx_summary_view_model import TxSummaryRow
from utils import limit_length
from view.components.transaction_list_item import MAX_TX_LABEL_LEN
from wallet import Wallet

Builder.load_file("view/wallet_view/wallet_txs_tab.kv")


class WalletTxsTab(MDFloatLayout, MDTabsBase):
    manager: ScreenManager = ObjectProperty()
    wallet: Wallet = ObjectProperty()

    tx_history_list: RecycleView = ObjectProperty()

    @mainthread
    def update_ui(self) -> None:
        txs = self.wallet.get_txs()

        tx_history_rows: List[TxSummaryRow] = []
        for tx in sorted(txs, reverse=True):
            tx_history_row = TxSummaryRow(
                tx_data=tx,
                tx_icon=(
                    "arrow-top-right" if tx.balance_change < 0 else "arrow-bottom-right"
                ),
                tx_color="#abb8c3" if tx.balance_change < 0 else "green",
                tx_time=str(tx.timestamp) if (tx.timestamp) else "Pending",
                balance_change=exchange_rate_manager.format_balance(
                    abs(tx.balance_change),
                    self.wallet.data.currency,
                ),
            )
            tx_history_rows.append(tx_history_row)

        self.tx_history_list.data = [
            {
                "viewclass": "TransactionListItem",
                "tx_data": tx_history_row.tx_data,
                "tx_icon": tx_history_row.tx_icon,
                "tx_color": tx_history_row.tx_color,
                "tx_time": tx_history_row.tx_time,
                "label": limit_length(tx_history_row.tx_data.label, MAX_TX_LABEL_LEN),
                "balance_change": tx_history_row.balance_change,
                "manager": self.manager,
            }
            for tx_history_row in tx_history_rows
        ]
