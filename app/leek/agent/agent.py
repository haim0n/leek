import json

import gevent

from leek.agent.logger import get_logger
from leek.agent.consumer import LeekConsumer

logger = get_logger(__name__)


class LeekAgent:
    """Main server object, which:
        - Load subscriptions from config file.
        - Orchestrates capturing of celery events.
        - Fanout to API webhooks endpoints
    """

    def __init__(self):
        self.consumers = []
        self.subscriptions = self.load_subscriptions()

        if not len(self.subscriptions):
            logger.warning("No subscriptions found, Consider adding subscriptions through environment variable or UI.")
            return

        logger.info("Building consumers...")
        for subscription_name, subscription_config in self.subscriptions.items():
            consumer = LeekConsumer(subscription_name, **subscription_config)
            self.consumers.append(consumer)
        logger.info("Consumers built...")

    def start(self, wait=True):
        if not len(self.consumers):
            return

        logger.info("Starting Leek Agent...")
        gs = []

        for consumer in self.consumers:
            gs.append(gevent.spawn(consumer.run()))

        if wait:
            gevent.joinall(gs)
            logger.info("Leek Agent stopped!")
            return
        else:
            return gs

    @staticmethod
    def load_subscriptions():
        logger.info(f"Loading subscriptions...")

        # FROM JSON FILE
        subscriptions_file = "/opt/app/conf/subscriptions.json"
        with open(subscriptions_file) as json_file:
            subscriptions = json.load(json_file)

        logger.info(f"Found {len(subscriptions)} subscriptions!")
        return subscriptions


if __name__ == '__main__':
    LeekAgent().start()
