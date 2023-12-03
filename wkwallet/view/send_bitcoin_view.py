from typing import List

from db.address_data import AddressData
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.list import MDList
from kivymd.uix.textfield import MDTextField
from model.crypt_utils import bytes_to_hex, create_transaction, estimate_tx_fee
from model.exchange_rate_manager import exchange_rate_manager, toggle_currency
from model.wallet_account import WalletAccount
from view.components.select_address_list_item import SelectAddressListItem
from view.create_tx_view import CreateTxView
from view.select_addresses_view import SelectAddressesView

Builder.load_file("view/send_bitcoin_view.kv")


class SendBitcoinView(Screen):
    account: WalletAccount = ObjectProperty()
    input_addresses_list: List[AddressData] = ObjectProperty()

    address_balance_label = ObjectProperty()
    addresses_list_view: MDList = ObjectProperty()
    amount_input: MDTextField = ObjectProperty()
    fee_input: MDTextField = ObjectProperty()
    target_address_input: MDTextField = ObjectProperty()

    def __init__(self, **kw):
        self.back_view_name = "main_view"
        self.should_reset = True
        super().__init__(**kw)

    def on_pre_enter(self, *args):
        if self.should_reset:
            self.reset()
        else:
            self.should_reset = True
        self.input_list = []
        for address_data in self.input_addresses_list:
            self.input_list += list(
                (utxo, address_data.private_key) for utxo in address_data.utxos
            )
        return super().on_pre_enter(*args)

    def reset(self):
        self.currency = "sat"
        self.target_address_input.text = ""
        self.update_balance()
        self.validate_amount_and_fee_input()
        self.addresses_list_view.clear_widgets()
        for address_data in self.input_addresses_list:
            select_address_list_item = SelectAddressListItem(address_data=address_data)
            self.addresses_list_view.add_widget(select_address_list_item)

    def back(self):
        self.manager.transition.direction = "right"
        self.manager.transition.mode = "pop"
        self.manager.current = self.back_view_name

    def validate_amount_and_fee_input(self):
        if self.total_balance <= 0:
            self.ids.create_tx_button.disabled = True
            return

        try:
            amount = int(self.amount_input.text)
            self.ids.create_tx_button.disabled = False
        except ValueError:
            amount = 0
            self.ids.amount_input.text = ""
            self.ids.create_tx_button.disabled = True
            return

        try:
            sats_per_vbyte = int(self.fee_input.text)
        except ValueError:
            self.fee_input.text = "1"
            sats_per_vbyte = 1

        change_address = self.account.data.get_unused_change_address()

        # Calculate total fee and show it
        try:
            tx_fee = estimate_tx_fee(
                tx_inputs_count=len(self.input_list),
                # Assuming there will be a change output
                tx_output_addr_strs=[self.target_address_input.text, change_address],
                sats_per_vbyte=sats_per_vbyte,
            )
        except ValueError:
            return

        if amount + tx_fee >= self.total_balance:
            # If there is no change, then there would only be 1 tx_output
            tx_fee = estimate_tx_fee(
                tx_inputs_count=len(self.input_list),
                tx_output_addr_strs=[self.target_address_input.text],
                sats_per_vbyte=sats_per_vbyte,
            )
            # Reduce the send amount if the total exceeded the balance
            self.amount_input.text = str(max(self.total_balance - tx_fee, 0))
            self.ids.change_amount.text = "N/A"
            self.ids.change_address.text = "N/A"
        else:
            # Show change amount and change address
            self.ids.change_amount.text = str(self.total_balance - amount - tx_fee)
            self.ids.change_address.text = change_address
        self.ids.total_fee.text = f"Total Tx Fee: {tx_fee} sats"

    # TODO: Validate the receiver address
    def press_create_transaction(self) -> None:
        try:
            send_amount = int(self.amount_input.text)
        except ValueError:
            return
        tx_outs_list = [(send_amount, self.target_address_input.text)]

        try:
            change_amount = int(self.ids.change_amount.text)
            if change_amount > 0:
                tx_outs_list.insert(
                    0,
                    (change_amount, self.ids.change_address.text),
                )
        except ValueError:
            pass

        tx_object = create_transaction(
            input_list=self.input_list, tx_outs_list=tx_outs_list
        )
        if tx_object is None:
            return
        Logger.info(f"raw_tx: {bytes_to_hex(tx_object.serialize())}")

        self.sign_transaction(tx_object)
        create_tx_view: CreateTxView = self.manager.create_tx_view
        create_tx_view.tx_object = tx_object
        create_tx_view.back_view_name = self.name

        self.manager.transition.duration = 0.2
        self.manager.transition.direction = "left"
        self.manager.transition.mode = "push"
        self.manager.current = create_tx_view.name
        self.should_reset = False

    def press_address_balance(self):
        self.currency = toggle_currency(self.currency, allow_hidden=False)
        self.update_balance()

    def press_select_addresses(self) -> None:
        select_addresses_view: SelectAddressesView = self.manager.select_addresses_view
        select_addresses_view.account = self.account
        select_addresses_view.selected_addresses_list = self.input_addresses_list

        self.manager.transition.duration = 0.2
        self.manager.transition.direction = "left"
        self.manager.transition.mode = "push"
        self.manager.current = select_addresses_view.name

    def update_balance(self):
        self.total_balance = sum(
            (address_data.total_balance for address_data in self.input_addresses_list)
        )
        self.address_balance_label.text = exchange_rate_manager.format_balance(
            self.total_balance,
            self.currency,
        )

    def sign_transaction(self, tx_object) -> None:
        from bitcoin.core import CTxInWitness
        from bitcoin.core.key import CECKey
        from bitcoin.core.script import (
            OP_0,
            SIGHASH_ALL,
            SIGVERSION_WITNESS_V0,
            CScript,
            CScriptWitness,
            SignatureHash,
        )
        from bitcoin.wallet import P2WPKHBitcoinAddress
        from pycoin.symbols.btc import network as BTC

        hashcode = SIGHASH_ALL
        for tx_in_index, (utxo_data, priv_key) in enumerate(self.input_list):
            # script_pub_key
            pub_key_hash = BTC.parse.p2pkh_segwit(utxo_data.address.address_str)
            input_scriptPubKey = CScript([OP_0, pub_key_hash.hash160()])
            input_address = P2WPKHBitcoinAddress.from_scriptPubKey(input_scriptPubKey)
            scriptCode = input_address.to_redeemScript()

            # signature_hash
            sig_hash = SignatureHash(
                scriptCode,
                tx_object,
                tx_in_index,
                hashcode,
                amount=utxo_data.balance,
                sigversion=SIGVERSION_WITNESS_V0,
            )

            # Sign the transaction
            cec_key = CECKey()
            cec_key.set_secretbytes(priv_key._secret_exponent_bytes)
            sig = cec_key.sign(sig_hash) + bytes([hashcode])

            # Save witness data to tx
            witness = [sig, priv_key.sec()]
            ctxwitness = CTxInWitness(CScriptWitness(witness))
            tx_object.wit.vtxinwit[tx_in_index] = ctxwitness
