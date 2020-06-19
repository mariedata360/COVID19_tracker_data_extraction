#!/usr/bin/env python
"""Driver script for running all registered data scrapers and writing
the output to an Excel file.
"""

import argparse
import datetime
import logging
import pandas as pd
from pathlib import Path
import sys

from covid19_scrapers import get_scraper_names, make_scraper_registry


def parse_args():
    """Process command line arguments from sys.argv and returns an options
    object.
    """
    known_scrapers = set(get_scraper_names())

    def scraper(scraper_name):
        """Type function for argparse that returns the scraper name if it is
        registered, and raises an error otherwise.
        """
        if scraper_name not in known_scrapers:
            raise ValueError('Invalid scraper:', scraper_name)
        return scraper_name

    def output_file(filename):
        """Type function for argparse that returns the output file name if we
        know how to write it, and raises an error otherwise.
        Recognized filenames are - for printing to stdout, csv suffix,
        and xlsx suffix.
        """
        if (
                not filename.endswith('.xlsx')
                and not filename.endswith('.csv')
                and filename != '-'):
            raise ValueError('Invalid output files: ' + filename)
        return filename

    # Set up command-line arguments
    parser = argparse.ArgumentParser(description='Run some or all scrapers')
    parser.add_argument('--list_scrapers', action='store_true',
                        help='List the known scraper names')
    parser.add_argument('scrapers', metavar='SCRAPER', type=scraper, nargs='*',
                        help='List of scrapers to run, or all if omitted')
    parser.add_argument('--work_dir', metavar='DIR', default='work',
                        action='store',
                        help='Write working outputs to subdirectories of DIR.')
    parser.add_argument('--output', dest='outputs', metavar='FILE',
                        action='append', type=output_file,
                        help='Write output to FILE (must be -, or have csv' +
                             ' or xlsx extension)')
    parser.add_argument('--log_file', type=str, metavar='FILE',
                        action='store', default='run_scrapers.log',
                        help='Write logs to FILE')
    parser.add_argument('--log_level', type=str, metavar='LEVEL',
                        action='store', default='DEBUG',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                 'DEBUG'],
                        help='Set log level for the log_file to LEVEL')
    parser.add_argument('--no_log_to_stderr', dest='log_to_stderr',
                        action='store_false',
                        help='Disable logging to stderr.')
    parser.add_argument('--log_to_stderr_level', type=str,
                        action='store', default='INFO',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                 'DEBUG'],
                        help='Set log level for stderr to LEVEL')
    parser.add_argument('--google_api_key', type=str, metavar='KEY',
                        action='store',
                        help='Provide a key for accessing Google APIs.')
    parser.add_argument('--use_beta_scrapers', action='store_true',
                        help='Include beta scrapers when not specifying scrapers manually.')
    # Parse command-line arguments
    return parser.parse_args()


def setup_logging(log_file, log_level, log_to_stderr, log_to_stderr_level):
    """Set up logging to file and/or stderr."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.NOTSET)
    if log_file:
        handler = logging.FileHandler(filename=log_file, mode='w')
        handler.setLevel(getattr(logging, log_level.upper()))
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s:  %(message)s'))
        root_logger.addHandler(handler)
    if log_to_stderr:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(getattr(logging, log_to_stderr_level.upper()))
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s:  %(message)s'))
        root_logger.addHandler(handler)


def write_output(df, output):
    """Given a dataframe, write it to one of the output files."""
    logging.info(f'Writing {output}')
    if output == '-':
        # Set pandas options for stdout
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        print(df)
    elif output.endswith('.csv'):
        df.to_csv(output, index=False, date_format='%m/%d/%Y')
    elif output.endswith('.xlsx'):
        df.to_excel(output, index=False)


def main():
    # Get command line options
    opts = parse_args()

    if opts.list_scrapers:
        print('Known scrapers: ', end='')
        for scraper_name in get_scraper_names():
            print(f'{scraper_name} ', end='')
        exit(0)

    # Set up logging
    setup_logging(opts.log_file, opts.log_level, opts.log_to_stderr,
                  opts.log_to_stderr_level)

    # Run scrapers
    scraper_registry = make_scraper_registry(
        home_dir=Path(opts.work_dir),
        scraper_args=dict(google_api_key=opts.google_api_key),
        use_beta_scrapers=opts.use_beta_scrapers,
    )
    if not opts.scrapers:
        logging.info('Running all scrapers')
        df = scraper_registry.run_all_scrapers()
    else:
        logging.info('Running selected scrapers')
        df = scraper_registry.run_scrapers(opts.scrapers)

    # When run without outputs specified, we will write to today's
    # default CSV and XLSX files
    today = datetime.date.today()
    default_outputs = [f'output/xlsx/covid_disparities_output_{today}.xlsx',
                       f'output/csv/covid_disparities_output_{today}.csv']

    # Write output files
    for output in opts.outputs or default_outputs:
        write_output(df, output)


if __name__ == '__main__':
    main()