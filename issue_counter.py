#!/usr/bin/env python
# Copyright (c) 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Get stats about your boogs.
"""

# This must be run with PYTHONPATH=/your/path/to/depot_tools

import auth
import csv
from datetime import datetime
import json
import optparse
import re
import sys
import urllib
from third_party import httplib2

# Google sheets isn't smart enough for T or microseconds <_<
def datetime_to_google_sheets_string(date):
  return date.replace(microsecond=0).isoformat(' ')


class QueryData(object):
  def __init__(self, data):
    self.regex = []
    if 'regex' in data:
      for search, replacelist in data['regex'].iteritems():
        pattern = re.compile(search)
        self.regex.append((pattern, ",".join(replacelist)))

    self.queries = {}

    if 'queries' in data:
      for key, query in data['queries'].iteritems():
        self.add_query(key, query)

    if 'patterns' in data:
      for _, pattern in data['patterns'].iteritems():
        for key_prefix, query_prefix in pattern['inputs'].iteritems():
          for key_suffix, query_dict in pattern['queries'].iteritems():
            query = query_dict.copy()
            if 'q' not in query:
              query['q'] = ""
            query['q'] += " " + query_prefix
            self.add_query(key_prefix + key_suffix, query)

  def add_query(self, key, query):
    assert(not key in self.queries)
    if not 'q' in query:
      return
    for pattern, rep in self.regex:
      query['q'] = re.sub(pattern, rep, query['q'])
    self.queries[key] = query


class IssueCounter(object):
  def __init__(self, options):
    self.options = options

  def issue_count(self, project, query):
    auth_config = auth.extract_auth_config_from_options(self.options)
    authenticator = auth.get_authenticator_for_host(
        "bugs.chromium.org", auth_config)
    http = authenticator.authorize(httplib2.Http())
    url = ("https://monorail-prod.appspot.com/_ah/api/monorail/v1/projects"
           "/%s/issues") % project

    query_final = query.copy()
    query_final.update({
      'maxResults': 0
    })
    _, body = http.request(url + '?' + urllib.urlencode(query_final))
    content = json.loads(body)
    if not content:
      print "Unable to parse %s response from projecthosting." % (
          instance["name"])
      return 0

    if 'totalResults' in content:
      return content['totalResults']
    return 0


def main():
  parser = optparse.OptionParser(description=sys.modules[__name__].__doc__)
  parser.add_option(
      '-a', '--auth',
      action='store_true',
      help='Ask to authenticate for instances with no auth cookie')
  parser.add_option(
      '-p', '--project', default='chromium', help='Monorail project')
  parser.add_option(
      '-f', '--file', help='json filename of inputs')
  parser.add_option(
      '-o', '--output_file', help='output filename')

  auth.add_auth_options(parser)
  parser.format_description = (
      lambda _: parser.description)  # pylint: disable=no-member

  options, args = parser.parse_args()
  if args:
    parser.error('Args unsupported')
  if not options.file:
    parser.error('--file required')

  try:
    with open(options.file) as input_file:
      data = json.load(input_file)
  except Exception as e:
    parser.error('Invalid file: %s' % e)

  queries = {}

  query_data = QueryData(data)
  issue_counter = IssueCounter(options)

  sorted_keys = sorted(query_data.queries.keys())
  output = {}

  try:
    for key in sorted_keys:
      total = issue_counter.issue_count(options.project, query_data.queries[key])
      output[key] = total
  except auth.AuthenticationError as e:
    print "auth.AuthenticationError: %s" % e
    return -1

  fieldnames = sorted_keys
  fieldnames.insert(0, 'date')
  # convince google sheets that this is a date
  date = datetime_to_google_sheets_string(datetime.today())
  output['date'] = date

  if not options.output_file:
    output_file = sys.stdout
  else:
    output_file = open(options.output_file, 'w')

  json.dump(output, output_file, separators=(',\n',':'), sort_keys=True)
  return 0

  writer = csv.DictWriter(output_file, fieldnames=sorted_keys)
  writer.writeheader()
  writer.writerow(output)

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main())
  except KeyboardInterrupt:
    sys.stderr.write('interrupted\n')
    sys.exit(1)
