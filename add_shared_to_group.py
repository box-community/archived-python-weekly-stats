""" Copyright 2015 Kris Steinhoff, The University of Michigan

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. 
"""

import box
import ConfigParser, csv, optparse, os, re, sys, json
from pprint import pprint

def update_counter(message):
    sys.stdout.write("\r"+ message)
    sys.stdout.flush()
    # sys.stdout.write("\n")

def human_file_size(size): # http://stackoverflow.com/a/1094933/70554
    format = "%3.1f %s"
    tiers = ["bytes","KB","MB","GB"]
    
    for t in tiers[:-1]:
        if size < 1024.0:
            return format % (size, t)
        size /= 1024.0
    return format % (size, tiers[-1])

def median(values):
    values.sort()
    count = len(values)
    if count % 2 == 1:
        return values[count/2]
    else:
        return ( values[(count/2)-1] + values[count/2] ) / 2.0

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-d", "--dry-run", action="store_true", dest="dry_run", default=False, help="simulate changes")

    (options, args) = parser.parse_args()

    box = box.BoxApi()
    config = ConfigParser.ConfigParser()
    settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "settings.conf")
    config.read(settings_file)

    try:
        group_id = config.get("add_shared_to_group", "group_id")
    except:
        print "group_id not configured (in add_shared_to_group section)"
        sys.exit(1)

    if len(args) > 0:
        infile = csv.reader(open(args[0], "rb"))
    else:
        infile = csv.reader(sys.stdin)

    headers = infile.next()

    role_rules = {
            "student": re.compile(r"(Enrolled)?Student(AA|DBRN|FLNT)"),
            "staff": re.compile(r"(Regular|Temporary)Staff(AA|DBRN|FLNT)"),
            "faculty": re.compile(r"Faculty(AA|DBRN|FLNT)"),
            "sponsored": re.compile(r"SponsoredAffiliate(AA|DBNR|FLNT)")
            }

    types = ("user", "shared")
    storage = ([], [])
    affiliations = {}
    roles = dict.fromkeys(role_rules.keys(), 0)

    ids = []
    for attr_values in infile:
        attrs = dict(zip(headers, attr_values))
        id = attrs["box_id"]
        if attrs["box_account_type"].lower() == "shared":
            ids.append(id)

    for id in ids:
        data = json.dumps({ "user": {"id": id}, "group": {"id": group_id, "role": "member"}})
        if options.dry_run:
            print data
        else:
            r = box.request("POST", "/group_memberships", data=data)
            if r.status_code == 201:
                print "User ID %s added to group." % id
            elif r.status_code == 409:
                print "User ID %s NOT added to group already exists." % id
            else:
                print "WARNING: Received an unexpected response:"
                print r.text
