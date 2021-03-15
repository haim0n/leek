import time
from urllib.parse import urljoin

import requests
from kombu.mixins import ConsumerMixin
from kombu import Exchange, Queue, Connection

from leek.agent.logger import get_logger

logger = get_logger(__name__)


class LeekConsumer(ConsumerMixin):
    PREFETCH_COUNT = 20
    MAX_RETRIES = 1000
    SUCCESS_STATUS_CODES = [200, 201]
    BACKOFF_STATUS_CODES = [400, 404, 503]
    DOWN_DELAY_S = 20
    BACKOFF_DELAY_S = 5
    LEEK_WEBHOOKS_ENDPOINT = "/v1/events/process"

    def __init__(
            self,
            subscription_name,
            # API
            api_url: str = "http://api:5000",
            org_name: str = "leek",
            app_name: str = "leek",
            app_key: str = "secret",
            app_env: str = "qa",
            # BROKER
            broker: str = "amqp://guest:guest@localhost//",
            backend: str = None,
            exchange: str = "celeryev",
            queue: str = "leek.fanout",
            routing_key: str = "#",
    ):
        """
        :param api_url: The URL of the API where to fanout events
        :param org_name: Leek org name, GMail username for standard users and domain name for GSuite users
        :param app_name: Leek app name, chosen when creating application
        :param app_key: Leek app key, provided after the application has been created
        :param app_env: Leek app env, broker messages env name
        :param broker: Broker url
        :param exchange: Exchange name, should be the same as workers event exchange
        :param queue: Queue name
        :param routing_key: Routing key
        """

        # API
        self.subscription_name = subscription_name
        logger.info(f"Building consumer for subscription [{subscription_name}]...")

        self.api_url = api_url
        self.headers = {
            "x-requested-with": "leek-agent",
            "x-agent-version": "1.0.0",
            "x-leek-org-name": org_name,
            "x-leek-app-name": app_name,
            "x-leek-app-key": app_key,
            "x-leek-app-env": app_env
        }

        # BROKER
        self.broker = broker
        self.connection = Connection(self.broker)
        self.event_type = "fanout" if self.connection.transport.driver_type == "redis" else "topic"
        self.exchange = Exchange(exchange, self.event_type, durable=True, auto_delete=False)
        self.queue = Queue(queue, exchange=self.exchange, routing_key=routing_key, durable=False, auto_delete=True)

        # CONNECTION TO BROKER
        self.ensure_connection_to_broker()

        # CONNECTION TO API
        self.ensure_connection_to_api()

    def ensure_connection_to_broker(self):
        logger.info(f"Ensure connection to the broker {self.connection.as_uri()}...")
        self.connection.ensure_connection(max_retries=10)
        logger.info("Broker is up!")

    def ensure_connection_to_api(self):
        logger.info(f"Ensure connection to the API {self.api_url}...")
        requests.options(
            url=urljoin(self.api_url, self.LEEK_WEBHOOKS_ENDPOINT),
            headers=self.headers
        ).raise_for_status()
        logger.info("API is up!")

    def get_consumers(self, Consumer, channel):
        """
        Build events consumer
        """
        logger.info("Configuring channel...")
        if self.connection.transport.driver_type == "redis":
            channel.basic_qos(prefetch_size=0, prefetch_count=self.PREFETCH_COUNT)
        else:
            channel.basic_qos(prefetch_size=0, prefetch_count=self.PREFETCH_COUNT, a_global=False)
        logger.info("Channel Configured...")

        logger.info("Declaring Exchange/Queue and binding them...")
        self.queue.declare(channel=channel)
        logger.info("Exchange/Queue declared and bound!")

        logger.info("Creating consumer...")
        consumer = Consumer(self.queue, callbacks=[self.on_message],
                            accept=['json', 'application/x-python-serialize'])
        logger.info("Consumer created!")
        return [consumer]

    def on_message(self, body, message):
        """
        Callbacks used to send message to Leek API Webhooks endpoint
        :param body: Message body
        :param message: Message
        """
        # print(message.properties)
        for i in range(self.MAX_RETRIES):
            try:
                response = requests.post(
                    url=urljoin(self.api_url, self.LEEK_WEBHOOKS_ENDPOINT),
                    json=body,
                    headers=self.headers
                )
                response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                logger.error("Failed to connect to Leek API, Leek is Down.")
                time.sleep(self.DOWN_DELAY_S)
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code
                if status_code in self.BACKOFF_STATUS_CODES:
                    logger.warning(e.response.content)
                    logger.warning(
                        f"Failed to send message with status code {status_code}, "
                        f"backoff for {self.BACKOFF_DELAY_S} seconds."
                    )
                    time.sleep(self.BACKOFF_DELAY_S)
                else:
                    logger.error(e.response.content)
                    time.sleep(self.DOWN_DELAY_S)
            else:
                if response.status_code in self.SUCCESS_STATUS_CODES:
                    message.ack()
                    return
