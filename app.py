import functools
import logging
import os
import typing

from flask import Flask, request
from signalbot import SignalBot

app = Flask(__name__)


@functools.lru_cache(1)
def _load_configs() -> typing.Dict:
    logging.info("Reading config from Environment Variables")
    config_dict = {
        "SIGNAL_HOST": os.environ["SIGNAL_HOST"],
        "SIGNAL_PHONE_NUMBER": os.environ["SIGNAL_PHONE_NUMBER"],
        "SIGNAL_GROUP_ID": os.environ["SIGNAL_GROUP_ID"],
    }
    logging.debug(f"{config_dict=}")

    return config_dict


@functools.lru_cache(1)
def _setup_signal_bot(signal_service: str, phone_number: str) -> SignalBot:
    logging.info("Setting up Signal bot")
    config = {
        "signal_service": signal_service,
        "phone_number": phone_number,
        "storage": None,
    }
    logging.debug(f"{config=}")
    bot = SignalBot(config)

    return bot


@app.route('/sns', methods=['POST'])
def sns_notification():
    # Extract the SNS message from the request
    sns_message = request.get_json()
    logging.debug(f"{sns_message=}")

    # Process the SNS message
    # You can add your custom logic here to handle the message
    config = _load_configs()
    bot = _setup_signal_bot(config["SIGNAL_HOST"], config["SIGNAL_PHONE_NUMBER"])

    # Forming the message
    notification_message = f"""
    **{sns_message['Subject']}**
    
    {sns_message['Message']}
    """

    bot.send(config["SIGNAL_GROUP_ID"], notification_message, listen=False)

    # Return a response to acknowledge receipt of the message
    return 'Notification received'


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s-%(module)s.%(funcName)s [%(levelname)s]: %(message)s')
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    app.run()
