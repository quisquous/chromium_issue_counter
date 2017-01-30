#!/usr/bin/env python
# Copyright (c) 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Merge a directory of json files together into a csv file

Header file has one fieldname per line in order.
"""

import csv
import json
import optparse
import os
import sys

def usage():
  return "Usage: %s [header file] [directory of json]" % sys.argv[0]

def main():
  if len(sys.argv) != 3:
    return usage()

  header_file_name = sys.argv[1]
  json_dir_name = sys.argv[2]

  with open(header_file_name) as header_file:
    header = [line.strip() for line in header_file.readlines()]

  out_file = sys.stdout
  writer = csv.DictWriter(out_file, fieldnames=header, extrasaction='ignore')
  writer.writeheader()

  (_, _, filenames) = os.walk(json_dir_name).next()
  for filename in sorted([f for f in filenames if f.endswith('.json')]):
    with open(os.path.join(json_dir_name, filename)) as json_file:
      writer.writerow(json.load(json_file))

  return 0


if __name__ == '__main__':
  try:
    sys.exit(main())
  except KeyboardInterrupt:
    sys.stderr.write('interrupted\n')
    sys.exit(1)
