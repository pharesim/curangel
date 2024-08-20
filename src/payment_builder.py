from beem.account import Account
from beem.transactionbuilder import TransactionBuilder
from beembase.operations import Transfer


class PaymentBuilder:
    def __init__(self, source_account: Account):
        self.acct = source_account
        self.payments = []

    def add_payment(self, target, amount, memo):
        # truncate to payable amount
        amount = int(amount * 1000) / 1000
        self.payments.append((target, amount, memo))

    def has_pending(self):
        return len(self.payments) > 0

    def build_tx(self):
        txb = TransactionBuilder(expiration=120,
                                 blockchain_instance=self.acct.blockchain)
        paying = []
        tx_size = 0
        while tx_size <= 32000 and len(self.payments) > 0:
            target, amount, memo = self.payments.pop(0)
            transfer = Transfer(**{
                "from": self.acct.name,
                "to": target,
                "amount": f"{amount:.03f} HIVE",
                "memo": memo
            })
            txb.appendOps([transfer])
            txb.constructTx()
            tx_size = len(bytes(txb.tx))
            paying.append((target, amount))
        txb.appendSigner(self.acct.name, "active")
        tx = txb.sign()
        return tx, paying
