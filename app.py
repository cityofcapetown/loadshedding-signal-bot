import dataclasses
import functools
import logging
import os

from flask import Flask, request
import requests

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s-%(module)s.%(funcName)s [%(levelname)s]: %(message)s')

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)


@dataclasses.dataclass
class SignalConfig:
    signal_host: str
    signal_phone_number: str
    signal_group_id: str


@dataclasses.dataclass
class SnsConfig:
    sns_topic_arn: str


@functools.lru_cache(1)
def _load_configs() -> (SignalConfig, SnsConfig):
    for env_var in ["SIGNAL_HOST", "SIGNAL_PHONE_NUMBER", "SIGNAL_GROUP_ID", "SNS_TOPIC_ARN"]:
        assert env_var in os.environ, f"expected '{env_var}' environmental variable needs to be set!"

    app.logger.info("Reading config from Environment Variables")
    signal_config = SignalConfig(
        signal_host=os.environ["SIGNAL_HOST"],
        signal_phone_number=os.environ["SIGNAL_PHONE_NUMBER"],
        signal_group_id=os.environ["SIGNAL_GROUP_ID"],
    )
    app.logger.debug(f"{signal_config=}")

    sns_config = SnsConfig(
        sns_topic_arn=os.environ["SNS_TOPIC_ARN"]
    )
    app.logger.debug(f"{sns_config=}")

    return signal_config, sns_config


def _send_to_signal_group(message: str, signal_config: SignalConfig, http_session: requests.Session):
    payload = {
        "message": message,
        "number": signal_config.signal_phone_number,
        "recipients": [signal_config.signal_group_id]
    }
    app.logger.debug(f"{payload=}")

    resp = http_session.post(
        f"http://{signal_config.signal_host}/v2/send",
        json=payload
    )
    resp.raise_for_status()


def _sync_signal(signal_config: SignalConfig, http_session: requests.Session):
    resp = http_session.get(
        f"http://{signal_config.signal_host}/v1/receive/{signal_config.signal_phone_number}",
    )
    resp.raise_for_status()


@app.route('/sns', methods=['POST'])
def sns_notification():
    # Extract the SNS message from the request
    sns_message = request.get_json(force=True)
    app.logger.debug(f"{sns_message=}")

    signal_config, sns_config = _load_configs()

    # Light validation of request
    if 'TopicArn' not in sns_message or sns_message['TopicArn'] != sns_config.sns_topic_arn:
        return "Invalid request", 403
    elif 'SubscribeURL' in sns_message:
        app.logger.info(f"Visit '{sns_message['SubscribeURL']}' to confirm subscription")
        return "Subscription URL in server logs", 201
    elif 'Subject' not in sns_message or 'Message' not in sns_message:
        return "Key fields missing", 400

    # Processing the SNS message
    # Forming the message
    notification_message = f"""
    **{sns_message['Subject']}**
    
    {sns_message['Message']}
    """
    app.logger.debug(f"notification_message=\n{notification_message}")
    with requests.Session() as http_session:
        _sync_signal(signal_config, http_session)
        _send_to_signal_group(notification_message, signal_config, http_session)

    # Return a response to acknowledge receipt of the message
    return f'Notification received and sent to Signal Group', 200


if __name__ == '__main__':
    # loading config on start
    _load_configs()

    app.run()
