import os
from time import sleep
from dotenv import load_dotenv
import pywaves as pw
import code

load_dotenv()

class Bot():
    def __init__(self):
        self.node = "https://nodes.waves.exchange"
        self.chain = "mainnet"
        self.matcher = "https://waves.exchange/api/v1/forward/matcher"
        self.amount_asset = pw.Asset(os.environ.get('AMOUNT_ASSET') or '')
        self.order_fee = int(0.003 * 10 ** 8)
        self.time_to_sleep = float(os.environ.get('SECONDS_TO_WAIT'))
        self.target_value = float(os.environ.get('TARGET_VALUE'))
        self.threshold_value = self.target_value * float(os.environ.get('THRESHOLD_PERCENT'))
        self.private_key = os.environ.get('PRIVATE_KEY')
        self.price_asset_id = os.environ.get('PRICE_ASSET_ID') # USDN
        self.price_asset = pw.Asset(self.price_asset_id)

        pw.setNode(self.node, 'mainnet')
        pw.setMatcher(self.matcher)

    def run(self):
        address = pw.Address(privateKey=self.private_key)
        amount_price_pair = pw.AssetPair(self.amount_asset, self.price_asset)
        prev_order = None

        while True:
            amount_asset_balance = address.balance()
            amount_asset_price = amount_price_pair.ticker()['data']['lastPrice'] # Denormalized

            # Find value of user's WAVES in USDN
            amount_asset_balance_denormalized = float(amount_asset_balance) * 10 ** -(self.amount_asset.decimals)
            current_amount_asset_value = amount_asset_balance_denormalized * amount_asset_price

            # Calculate difference and value to sell/buy
            difference = abs(current_amount_asset_value - self.target_value)
            to_exchange = int((difference / amount_asset_price) * 10 ** self.amount_asset.decimals)

            if difference > self.threshold_value:
                if prev_order:
                    prev_order.cancel()

                if current_amount_asset_value > self.target_value:
                    print("Waves Price: ", amount_asset_price)
                    print("Waves Balance (pre-sell): ", amount_asset_balance)
                    print("To Sell: ", to_exchange - self.order_fee)

                    prev_order = address.sell(assetPair=amount_price_pair, 
                        amount=to_exchange - self.order_fee, 
                        price=amount_asset_price, 
                        matcherFee=self.order_fee)
                elif current_amount_asset_value < self.target_value:
                    print("Waves Price: ", amount_asset_price)
                    print("Waves Balance (pre-buy): ", amount_asset_balance)
                    print('To Buy: ', to_exchange + self.order_fee)
                    
                    prev_order = address.buy(assetPair=amount_price_pair, 
                        amount=to_exchange + self.order_fee, 
                        price=amount_asset_price, 
                        matcherFee=self.order_fee)
                print("Order: ", prev_order.status())
            else:
                print('Pass: Threshold has not been reached')
                print('Threshold: ', self.threshold_value)
                print('Current Value/Target Value Difference: ', difference)
            
            sleep(self.time_to_sleep)

if __name__ == '__main__':
    bot = Bot()
    bot.run()
    
