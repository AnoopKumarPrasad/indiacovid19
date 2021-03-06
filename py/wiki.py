#!/usr/bin/python3

# The MIT License (MIT)
#
# Copyright (c) 2020 Susam Pal
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import argparse
import datetime
import difflib
import html
import sys

from py import archive, log, mohfw


"""Generate Wikipedia markup code.

There are two templates used in the Wikipedia article
https://en.wikipedia.org/wiki/COVID-19_pandemic_in_India
to display charts related to case numbers:

  1. https://en.wikipedia.org/wiki/Template:COVID-19_pandemic_data/India_medical_cases_chart
  2. https://en.wikipedia.org/wiki/Template:COVID-19_pandemic_data/India_medical_cases

This script generates Wikipedia markup code for both charts. Enter these
commands at the top-level directory of this project to generate the
corresponding markups:

    python3 -m py.wiki -1
    python3 -m py.wiki -2

"""


import datetime
import re
import urllib
import urllib.request


WIKI_SRC1 = 'Template:COVID-19_pandemic_data/India_medical_cases_chart'
WIKI_SRC2 = 'Template:COVID-19_pandemic_data/India_medical_cases_by_state_and_union_territory'
WIKI_SRC3 = 'COVID-19_pandemic_in_India/Statistics'


def fetch_wiki_source(article_name):
    """Return Wikitext from specified Wikipedia article."""
    src_url = ('https://en.wikipedia.org/w/index.php?title={}&action=edit'
               .format(article_name))
    log.log('Fetching wikitext for {} ...', src_url)
    response = urllib.request.urlopen(src_url).read().decode('utf-8')
    source = re.search(r'(?s)<textarea .*?>(.*)</textarea>', response).group(1)
    source = html.unescape(source)
    return source


def replace_within(begin_re, end_re, source, data):
    """Replace text in source between two delimeters with specified data."""
    pattern = r'(?s)(' + begin_re + r')(?:.*?)(' + end_re + r')'
    source = re.sub(pattern, r'\1@@REPL@@\2' , source)
    if '@@REPL@@' in source:
        source = source.replace('@@REPL@@', data)
    else:
        log.log('')
        log.log('ERROR: Cannot match /{}/ and /{}/'.format(begin_re, end_re))
        log.log('')
    return source


def diff(a, b):
    """Return unified diff between two strings."""
    out = difflib.unified_diff(a.splitlines(True), b.splitlines(True),
                               fromfile='old', tofile='new')
    return ''.join(out)


def cf(x):
    """Return tick label for Indian-style comma delimited numbers."""
    x = str(int(x))
    result = x[-3:]
    i = len(x) - 3
    while i > 0:
        i -= 2
        j = i + 2
        if i < 0: i = 0
        result = x[i:j] + ',' + result
    return result


def wiki1():
    """Generate Wikipedia markup code for medical cases chart template."""
    ignore_dates = ('2020-02-04', '2020-02-21', '2020-02-27')
    data = archive.load(ignore_dates=ignore_dates)
    update = source = fetch_wiki_source(WIKI_SRC1)
    update = replace_within('Total confirmed -->\n',
                            '\n<!-- Date',
                            update, wiki1_data(data))
    open('wiki1.txt', 'w').write(update)
    open('wiki1.diff', 'w').write(diff(source, update))


def wiki1_data(data):
    """Generate data entries for medical cases chart template."""
    out = []

    for i, (date, total, cured, death) in enumerate(zip(
            data.dates, data.total_cases, data.cured_cases, data.death_cases)):

        # date;deaths;cured;total
        out.append('{};{};{};{}'.format(date, death, cured, total))

        # Print continuation lines.
        curr_index = data.dates.index(date)
        if curr_index < len(data.dates) - 1:
            curr_datetime = data.datetimes[curr_index]
            next_datetime = data.datetimes[curr_index + 1]
            if (next_datetime - curr_datetime).days != 1:
                month = next_datetime.strftime('%b')
                out.append(';{};{};{}'.format('' if death == 0 else death,
                                              '' if cured == 0 else cured,
                                              '' if total == 0 else total))
    return '\n'.join(out)


def wiki2():
    """Generate Wikipedia markup for region table."""
    data = mohfw.load_home_data()
    reassigned = str(data.regions['reassigned'][0])
    update = source = fetch_wiki_source(WIKI_SRC2)
    update = replace_within('\\|- class="sorttop"\n',
                            '\n\\|- class="sortbottom"',
                            update, region_table_head(data) + '\n' +
                                    region_table_body(data))
    update = replace_within('nationals\n\|', r' cases are being reassigned',
                            update, reassigned)
    open('wiki2.txt', 'w').write(update)
    open('wiki2.diff', 'w').write(diff(source, update))


def region_table_head(data):
    """Generate header row for region table."""
    style_center = '! style="text-align:center; padding: 0 2px;" |'
    style_right = '! style="text-align:right; padding: 0 2px;" |'
    out = [
        style_center + '35 / 36',
        style_right + cf(data.regions_total),
        style_right + cf(data.regions_death),
        style_right + cf(data.regions_cured),
        style_right + cf(data.regions_active),
    ]
    return '\n'.join(out)


def region_table_body(data):
    """Generate data rows for region table."""
    region_names = (
        'Andaman and Nicobar Islands',
        'Andhra Pradesh',
        'Arunachal Pradesh',
        'Assam',
        'Bihar',
        'Chandigarh',
        'Chhattisgarh',
        'Dadra and Nagar Haveli and Daman and Diu',
        'Delhi',
        'Goa',
        'Gujarat',
        'Haryana',
        'Himachal Pradesh',
        'Jammu and Kashmir',
        'Jharkhand',
        'Karnataka',
        'Kerala',
        'Ladakh',
        'Lakshadweep',
        'Madhya Pradesh',
        'Maharashtra',
        'Manipur',
        'Meghalaya',
        'Mizoram',
        'Nagaland',
        'Odisha',
        'Puducherry',
        'Punjab',
        'Rajasthan',
        'Sikkim',
        'Tamil Nadu',
        'Telangana',
        'Tripura',
        'Uttarakhand',
        'Uttar Pradesh',
        'West Bengal',
    )
    out = []
    for i, name in enumerate(region_names, 1):
        matches = difflib.get_close_matches(name, list(data.regions), 1)
        key = None

        if len(matches) != 0:
            key = matches[0]
        elif name == 'Dadra and Nagar Haveli and Daman and Diu':
            candidates = ['Dadar Nagar Haveli', 'Dadra and Nagar Haveli']
            for candidate in candidates:
                if candidate in data.regions:
                    key = candidate
                    break

        if key is None:
            total, active, cured, death = 0, 0, 0, 0
        else:
            total, active, cured, death = data.regions[key]

        total, active, cured, death = (cf(total), cf(active),
                                       cf(cured), cf(death))

        if name == 'Assam':
            total = str(total) + open('layout/fn1.txt').read().strip()
        elif name == 'Kerala':
            death = str(death) + open('layout/fn2.txt').read().strip()

        out.append('|-')
        out.append('! scope="row" |{}'.format(markup_region(name)))
        out.append('|{}'.format(markup_num(total)))
        out.append('|{}'.format(markup_num(death)))
        out.append('|{}'.format(markup_num(cured)))
        out.append('|{}'.format(markup_num(active)))
    out = '\n'.join(out)
    return out


def markup_region(name):
    """Generate Wikipedia markup to display region name in region table."""
    if name in (
        'Andhra Pradesh',
        'Arunachal Pradesh',
        'Assam',
        'Bihar',
        'Chandigarh',
        'Chhattisgarh',
        'Dadra and Nagar Haveli and Daman and Diu',
        'Delhi',
        'Goa',
        'Gujarat',
        'Haryana',
        'Himachal Pradesh',
        'Jammu and Kashmir',
        'Jharkhand',
        'Karnataka',
        'Kerala',
        'Ladakh',
        'Madhya Pradesh',
        'Maharashtra',
        'Manipur',
        'Meghalaya',
        'Mizoram',
        'Nagaland',
        'Odisha',
        'Puducherry',
        'Rajasthan',
        'Sikkim',
        'Tamil Nadu',
        'Telangana',
        'Tripura',
        'Uttarakhand',
        'Uttar Pradesh',
        'West Bengal'
    ):
        return ('[[COVID-19 pandemic in {}|{}]]'
                .format(name, name))

    if name in ('Andaman and Nicobar Islands'):
        return ('[[COVID-19 pandemic in the {}|{}]]'
                .format(name, name))

    if name in ('Punjab'):
        return ('[[COVID-19 pandemic in {}, India|{}]]'
                .format(name, name))

    return name


def markup_num(n_str):
    """Generate Wikipedia markup for case numbers in region table."""
    return ' style="color:gray;" |0' if n_str == '0' else n_str


def wiki3():
    """Generate Wikipedia markup code for statistics charts."""
    ignore_dates = ('2020-02-04', '2020-02-27')
    data = archive.load(ignore_dates=ignore_dates)
    update = source = fetch_wiki_source(WIKI_SRC3)

    mini_dates = ', '.join(x.strftime('%d %b %Y').lstrip('0')
                           for x in data.datetimes)
    full_dates = ', '.join(x.strftime('%d %b %Y').lstrip('0')
                           for x in data.datetimes)
    # Cases.
    total_cases = ', '.join(str(y) for y in data.total_cases)
    active_cases = ', '.join(str(y) for y in data.active_cases)
    cured_cases = ', '.join(str(y) for y in data.cured_cases)
    death_cases = ', '.join(str(y) for y in data.death_cases)
    # New cases.
    total_dates, total_diffs = clean_data(data.datetimes, data.total_diffs)
    cured_dates, cured_diffs = clean_data(data.datetimes, data.cured_diffs)
    death_dates, death_diffs = clean_data(data.datetimes, data.death_diffs)
    # CFR
    cfr_start = data.dates.index('2020-03-12')
    cfr_dates = ', '.join(x.strftime('%d %b %Y').lstrip('0')
                      for x in data.datetimes[cfr_start:])
    cfr_percents = ', '.join('{:.2f}'.format(y) for
                             y in data.cfr_percents[cfr_start:])

    # For testing regex matches only.
    """
    mini_dates = '@@mini_dates@@'
    full_dates = '@@full_dates@@'
    total_cases = '@@total_cases@@'
    active_cases = '@@active_cases@@'
    cured_cases = '@@cured_cases@@'
    death_cases = '@@death_cases@@'
    total_dates, total_diffs = '@@total_dates@@', '@@total_diffs@@'
    cured_dates, cured_diffs = '@@cured_dates@@', '@@cured_diffs@@'
    death_dates, death_diffs = '@@death_dates@@', '@@death_diffs@@'
    cfr_dates, cfr_percents = '@@cfr_dates@@', '@@cfr_percents@@'
    """

    # Linear graph.
    update = replace_within('= Total confirmed.*?x = ', '\n',
                            update, full_dates)
    update = replace_within('= Total confirmed.*?y1 =.*?--> ', '\n',
                            update, total_cases)
    update = replace_within('= Total confirmed.*?y2 =.*?--> ', '\n',
                            update, active_cases)
    update = replace_within('= Total confirmed.*?y3 =.*?--> ', '\n',
                            update, cured_cases)
    update = replace_within('= Total confirmed.*?y4 =.*?--> ', '\n',
                            update, death_cases)

    # Logarithmic graph.
    update = replace_within('= Total confirmed.*?log.*?x = ', '\n',
                            update, full_dates)
    update = replace_within('= Total confirmed.*?log.*?y1 =.*?--> ', '\n',
                            update, total_cases)
    update = replace_within('= Total confirmed.*?log.*?y2 =.*?--> ', '\n',
                            update, active_cases)
    update = replace_within('= Total confirmed.*?log.*?y3 =.*?--> ', '\n',
                            update, cured_cases)
    update = replace_within('= Total confirmed.*?log.*?y4 =.*?--> ', '\n',
                            update, death_cases)

    # Daily new cases.
    update = replace_within('= Daily new cases.*?x = ', '\n',
                            update, total_dates)
    update = replace_within('= Daily new cases.*?y = ', '\n',
                            update, total_diffs)

    # Daily new deaths.
    update = replace_within('= Daily new deaths.*?x = ', '\n',
                            update, death_dates)
    update = replace_within('= Daily new deaths.*?y = ', '\n',
                            update, death_diffs)

    # Daily new recoveries.
    update = replace_within('= Daily new recoveries.*?x = ', '\n',
                            update, cured_dates)
    update = replace_within('= Daily new recoveries.*?y = ', '\n',
                            update, cured_diffs)

    # CFR.
    update = replace_within('= Case fatality rate.*?x = ', '\n',
                            update, cfr_dates)
    update = replace_within('= Case fatality rate.*?y = ', '\n',
                            update, cfr_percents)

    open('wiki3.txt', 'w').write(update)
    open('wiki3.diff', 'w').write(diff(source, update))


def clean_data(datetimes, numbers):
    """Remove zero entries from specified dates and numbers."""
    formatted_dates = [d.strftime('%d %b').lstrip('0') for d in datetimes]
    cleaned_dates = []
    cleaned_numbers = []

    mode = 'LEADING_ZEROS'
    multiple_zeros_allowed = True

    def normal_append(d, n):
        nonlocal mode
        mode = 'NORMAL'
        cleaned_dates.append(d)
        cleaned_numbers.append(n)

    for i, (d, n) in enumerate(zip(formatted_dates, numbers)):
        if mode == 'LEADING_ZEROS':
            if n == 0:
                continue
            else:
                normal_append(d, n)
        elif mode == 'NORMAL':
            if multiple_zeros_allowed and n == 0:
                mode = 'SINGLE_ZERO'
                continue
            else:
                normal_append(d, n)
        elif mode == 'SINGLE_ZERO':
            if n == 0:
                mode = 'MULTIPLE_ZEROS'
                cleaned_dates.append('...')
                cleaned_numbers.append(0)
            else:
                normal_append(formatted_dates[i - 1], 0)
                normal_append(d, n)
        elif mode == 'MULTIPLE_ZEROS':
            if n == 0:
                continue
            else:
                multiple_zeros_allowed = False
                normal_append(d, n)

    return (', '.join(str(x) for x in cleaned_dates),
            ', '.join(str(x) for x in cleaned_numbers))


def diffs():
    """Generate Wikipedia markup code to plot new cases."""
    print('\nNew cases per day:\n')
    print('y =', ', '.join(str(y) for y in data.total_diffs))
    print('\nNew recoveries per day:\n')
    print('y =', ', '.join(str(y) for y in data.cured_diffs))
    print('\nNew deaths per day:\n')
    print('y =', ', '.join(str(y) for y in data.death_diffs))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-1', action='store_true',
                        help='Markup for medical cases chart')
    parser.add_argument('-2', action='store_true',
                        help='Markup for medical cases table')
    parser.add_argument('-3', action='store_true',
                        help='Markup for charts')
    args = vars(parser.parse_args())

    if not any((args['1'], args['2'], args['3'])):
        parser.print_help()
        sys.exit(1)

    if args['1']:
        wiki1()

    if args['2']:
        wiki2()

    if args['3']:
        wiki3()


if __name__ == '__main__':
    main()
