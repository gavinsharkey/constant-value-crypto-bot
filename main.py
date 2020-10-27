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
        self.amount_asset = pw.WAVES
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
        waves_usdn = pw.AssetPair(self.amount_asset, self.price_asset)
        prev_order = None

        while True:
            waves_balance = address.balance() # WAVES (10 ** 8)
            waves_price = float(waves_usdn.last()) # Denormalized

            # Find value of user's WAVES in USDN
            waves_balance_denormalized = float(waves_balance) * (10 ** -8)
            value_of_users_waves = waves_balance_denormalized * waves_price

            # Calculate difference and value to sell/buy
            difference = abs(value_of_users_waves - self.target_value)
            to_exchange = int((difference / waves_price) * 10 ** 8)

            if difference > self.threshold_value:
                if prev_order:
                    prev_order.cancel()

                if value_of_users_waves > self.target_value:
                    print("Waves Price: ", waves_price)
                    print("Waves Balance (pre-sell): ", waves_balance)
                    print("To Sell: ", to_exchange - self.order_fee)

                    prev_order = address.sell(assetPair=waves_usdn, amount=to_exchange - self.order_fee, price=waves_price, matcherFee=self.order_fee)
                elif value_of_users_waves < self.target_value:
                    print("Waves Price: ", waves_price)
                    print("Waves Balance (pre-buy): ", waves_balance)
                    print('To Buy: ', to_exchange + self.order_fee)
                    
                    prev_order = address.buy(assetPair=waves_usdn, amount=to_exchange + self.order_fee, price=waves_price, matcherFee=self.order_fee)
                print("Order: ", prev_order.status())
            else:
                print('Pass: Threshold has not been reached')
                print('Threshold: ', self.threshold_value)
                print('Current Value/Target Value Difference: ', difference)
            
            sleep(self.time_to_sleep)

if __name__ == '__main__':
    bot = Bot()
    bot.run()
    
