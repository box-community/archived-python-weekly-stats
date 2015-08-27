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

import ConfigParser, csv, optparse, re, sys
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
    (options, args) = parser.parse_args()

    config = ConfigParser.ConfigParser()
    config.read('settings.cfg')

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

    types = ("user", "shared", "admin", "inactive")
    storage = ([], [], [], [])
    affiliations = {}
    roles = dict.fromkeys(role_rules.keys(), 0)

    for attr_values in infile:
        attrs = dict(zip(headers, attr_values))
        box_space_used = long(attrs["box_space_used"])
        active_shared_acct = 0
	active_individual_acct = 0
	if attrs["box_status"] == "active":
	    if attrs["box_account_type"] == "individual":
                # active user quota
                storage[0].append(box_space_used)
            elif attrs["box_account_type"] == "shared":
                # active shared quota
                storage[1].append(box_space_used)
	    elif attrs["box_account_type"] == "admin":
	        # active admin quota
		storage[2].append(box_space_used)
	else:
	    # total inactive quota
	    storage[3].append(box_space_used)
	#affils = [s.strip() for s in attrs["ldap_umichInstRoles"].split(",")]
        #for a in affils:
        #    try:
        #        affiliations[a] += 1
        #    except KeyError:
        #        affiliations[a] = 1
        #    for (role, rule) in role_rules.items():
        #        if rule.match(a):
        #            # TODO only count each role once
        #            roles[role] += 1



    for i in range(0, len(types)):
        print "Summary for " + ("active " if i < 3 else "") +  "%s accounts" % types[i]
	
	s = storage[i]
        stats = {}
        stats["total_count"] = len(s)
        stats["space_total"] = human_file_size(sum(s))
        stats["space_mean"] = human_file_size(sum(s)/float(len(s)))
        stats["space_median"] = human_file_size(median(s))

        non_zero_storage = [x for x in s if x != 0]
        stats["non_zero_space_total"] = human_file_size(sum(non_zero_storage))
        stats["non_zero_space_mean"] = human_file_size(sum(s)/float(len(non_zero_storage)))
        stats["non_zero_space_median"] = human_file_size(median(non_zero_storage))

        stats["user_count_zero"] = s.count(0)

        to_50_percent_usage = []
        s.sort(reverse=True)

        print """\tTotal accounts: {total_count} 
        Total storage used: {space_total}
        Mean storage used: {space_mean}
        Median storage used: {space_median}\n""".format(**stats)
       
    all_storage = []
    for sublist in storage:
	for item in sublist:
	    all_storage.append(item)
    all_storage.sort(reverse=True)
    top_1_percent = round((sum(all_storage[0:len(s)/100]) / float(sum(all_storage))) * 100, 2)
    top_10_percent = round((sum(all_storage[0:len(s)/10]) / float(sum(all_storage))) * 100, 2)
    top_25_percent = round((sum(all_storage[0:len(s)/4]) / float(sum(all_storage))) * 100, 2)

    print "Summary for all accounts:"
    print """\tTop 1% of users account for: {0}% of space used   
    \tTop 10% of users account for: {1}% of space used 
    \tTop 25% of users account for: {2}% of space used""".format(top_1_percent, top_10_percent, top_25_percent)

    #print roles
    #print affiliations
