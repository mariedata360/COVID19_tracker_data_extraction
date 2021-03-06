import datetime
import logging
import re

from covid19_scrapers.scraper import ScraperBase
from covid19_scrapers.utils.html import url_to_soup
from covid19_scrapers.utils.misc import to_percentage
from covid19_scrapers.utils.parse import raw_string_to_int


_logger = logging.getLogger(__name__)


class Minnesota(ScraperBase):
    """Minnesota publishes demographic breakdowns of COVID-19 cases and
    deaths on a reporting website.  We scrape the tables for totals
    and AA counts, and compute percentages.
    """

    REPORTING_URL = 'https://www.health.state.mn.us/diseases/coronavirus/situation.html#raceeth1'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _scrape(self, **kwargs):
        soup = url_to_soup(self.REPORTING_URL)

        # find date
        strong = soup.find('strong', string=re.compile('Updated '))
        date_text = re.search(r'[A-Z][a-z][a-z]+ \d(\d)?, 20\d\d',
                              strong.text).group()

        # find total number of confirmed cases
        strong = soup.find('strong',
                           string=re.compile(r'Total positive( cases)?:'))
        num_cases = raw_string_to_int(str(strong.next_sibling))

        # find total number of deaths
        strong = soup.find('strong', string=re.compile('(Total )?[Dd]eaths:'))
        num_deaths = raw_string_to_int(strong.next_sibling)

        date_obj = datetime.datetime.strptime(date_text, '%B %d, %Y').date()
        _logger.info(f'Processing data for {date_obj}')
        _logger.debug(f'Number Cases: {num_cases}')
        _logger.debug(f'Number Deaths: {num_deaths}')

        # find number of Black/AA cases and deaths
        table = soup.find('table', attrs={'id': 'raceethtable'})
        if not table:
            raise ValueError('Unable to locate race/ethnicity table')
        th = table.find(lambda elt: elt.name == 'th'
                        and elt.text.find('Black') >= 0)
        if not th:
            raise ValueError('Unable to locate Black/AA data row')
        tds = th.find_next_siblings('td')
        cnt_aa_cases = raw_string_to_int(tds[0].text)
        cnt_aa_deaths = raw_string_to_int(tds[1].text)
        pct_aa_cases = to_percentage(cnt_aa_cases, num_cases)
        pct_aa_deaths = to_percentage(cnt_aa_deaths, num_deaths)

        _logger.debug(f'Number Black/AA Cases: {cnt_aa_cases}')
        _logger.debug(f'Number Black/AA Deaths: {cnt_aa_deaths}')

        return [self._make_series(
            date=date_obj,
            cases=num_cases,
            deaths=num_deaths,
            aa_cases=cnt_aa_cases,
            aa_deaths=cnt_aa_deaths,
            pct_aa_cases=pct_aa_cases,
            pct_aa_deaths=pct_aa_deaths,
            pct_includes_unknown_race=True,
            pct_includes_hispanic_black=True,
        )]
