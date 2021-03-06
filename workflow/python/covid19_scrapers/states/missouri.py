import logging

from covid19_scrapers.scraper import ScraperBase
from covid19_scrapers.utils.arcgis import (
    make_geoservice_stat, query_geoservice)
from covid19_scrapers.utils.misc import to_percentage


_logger = logging.getLogger(__name__)


class Missouri(ScraperBase):
    """Missouri has an ArcGIS dashboard that includes demographic
    breakdowns of confirmed cases and deaths.  We identified the
    underlying FeatureServer calls to populate this, and invoke those
    directly.

    The dashboard is at:
    http://mophep.maps.arcgis.com/apps/MapSeries/index.html?appid=8e01a5d8d8bd4b4f85add006f9e14a9d
    """

    # Services are at https://services6.arcgis.com/Bd4MACzvEukoZ9mR
    TOTAL = dict(
        flc_url='https://services6.arcgis.com/Bd4MACzvEukoZ9mR/ArcGIS/rest/services/county_MOHSIS_map/FeatureServer',
        layer_name='county_mohsis_map_temp',
        stats=[
            make_geoservice_stat('sum', 'Cases', 'Cases'),
            make_geoservice_stat('sum', 'Deaths', 'Deaths'),
        ],
    )

    RACE_CASE = dict(
        flc_url='https://services6.arcgis.com/Bd4MACzvEukoZ9mR/arcgis/rest/services/Case_by_Race_Automated/FeatureServer',
        layer_name='CasesByRace_Temp',
        out_fields=['RACE', 'Frequency as Cases'],
    )

    RACE_DEATH = dict(
        flc_url='https://services6.arcgis.com/Bd4MACzvEukoZ9mR/ArcGIS/rest/services/Death_by_Race_Automated/FeatureServer',
        layer_name='DeathByRace_Temp',
        out_fields=['RACE', 'Frequency as Deaths'],
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _scrape(self, **kwargs):
        # Download and extract the case and death totals
        date, totals = query_geoservice(**self.TOTAL)
        _logger.info(f'Processing data for {date}')
        total_cases = totals.loc[0, 'Cases']
        total_deaths = totals.loc[0, 'Deaths']

        # Extract by-race data
        _, cases_race = query_geoservice(**self.RACE_CASE)
        cases_race = cases_race.set_index('RACE').dropna().astype(int)
        known_cases = cases_race.drop(
            ['REFUSED TO ANSWER RACE', 'UNKNOWN RACE'],
            errors='ignore'
        ).sum()['Cases']
        aa_cases = cases_race.loc['BLACK', 'Cases']
        aa_cases_pct = to_percentage(aa_cases, known_cases)

        _, deaths_race = query_geoservice(**self.RACE_DEATH)
        deaths_race = deaths_race.set_index('RACE').dropna().astype(int)
        known_deaths = deaths_race.drop(
            ['REFUSED TO ANSWER RACE', 'UNKNOWN RACE'],
            errors='ignore'
        ).sum()['Deaths']
        aa_deaths = deaths_race.loc['BLACK', 'Deaths']
        aa_deaths_pct = to_percentage(aa_deaths, known_deaths)

        return [self._make_series(
            date=date,
            cases=total_cases,
            deaths=total_deaths,
            aa_cases=aa_cases,
            aa_deaths=aa_deaths,
            pct_aa_cases=aa_cases_pct,
            pct_aa_deaths=aa_deaths_pct,
            pct_includes_unknown_race=False,
            pct_includes_hispanic_black=True,
            known_race_cases=known_cases,
            known_race_deaths=known_deaths,
        )]
