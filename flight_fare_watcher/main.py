# -*- coding: utf-8 -*-

import datetime
import random
import sys

import dateutil.parser
import requests
import time
from lxml import html


class WeProbablyGotCaught(Exception):
    pass


class FlightFareWatcher:

    _url_pattern = 'https://www.kayak.com/flights/{departure_airport}-{arrival_airport}/{search_date}-flexible'  # Also "origin_airport" and "destination_airport"
    _parser_info = dateutil.parser.parserinfo(dayfirst=False, yearfirst=True)

    # TODO (duyn): dependency injection
    def __init__(self):
        self._user_agents = get_common_user_agents()
        self.daily_prices = {}

    def start(self, departure_airport, arrival_airport, start_date, stop_date):
        departure_airport = departure_airport.upper().strip()
        arrival_airport = arrival_airport.upper().strip()
        start_date = dateutil.parser.parse(start_date)
        stop_date = dateutil.parser.parse(stop_date)

        search_date = start_date + datetime.timedelta(days=3)
        url = FlightFareWatcher._url_pattern.format(
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            search_date=search_date.date().isoformat())
        # This is the equivalent XPath:
        # //div[contains(@class, \"keel-grid\") and contains(@class, \"row\") and not(contains(@class, \"headerRow\"))]
        #   /div[contains(@class, \"col-cell\") and contains(@class, \"valid\")]
        #       /a
        selector = 'div.keel-grid.row:not(.headerRow) div.col-cell.valid a'

        while search_date < stop_date:
            # TODO (duyn): debugging mode
            headers = {'User-Agent': random.choice(self._user_agents)}
            response = requests.get(url=url, headers=headers)

            if response.status_code != requests.codes.OK:
                raise WeProbablyGotCaught(response.url)

            nodes = html.fromstring(response.content).cssselect(selector)
            for node in nodes:
                datetime_stamp = dateutil.parser.parse(
                    node.get('data-x-filter-code'),
                    parserinfo=FlightFareWatcher._parser_info)
                daily_price = int(node.text.replace('$', '').strip())
                self.daily_prices[datetime_stamp] = daily_price

            search_date += datetime.timedelta(weeks=1)
            time.sleep(random.randrange(600))


def get_common_user_agents():

    url = 'https://techblog.willshouse.com/2012/01/03/most-common-user-agents/'
    selector = 'table.make-html-table.most-common-user-agents td.useragent'

    response = requests.get(url=url)

    if response.status_code != requests.codes.OK:
        raise WeProbablyGotCaught(response.url)

    # Many websites have code supporting outdated clients.  Often the
    # DOM's implementation is vastly different.
    nodes = html.fromstring(response.content).cssselect(selector)
    user_agents = [node.text for node in nodes][:5]

    return user_agents


def main(departure_airport, arrival_airport, start_date, stop_date):

    flight_fare_watcher = FlightFareWatcher()
    flight_fare_watcher.start(departure_airport=departure_airport,
                              arrival_airport=arrival_airport,
                              start_date=start_date,
                              stop_date=stop_date)


if __name__ == '__main__':
    main(departure_airport=sys.argv[1],
         arrival_airport=sys.argv[2],
         start_date=sys.argv[3],
         stop_date=sys.argv[4])
