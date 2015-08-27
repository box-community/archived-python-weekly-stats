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

import box, ConfigParser, csv, json, ldap, logging, optparse, os, requests, sys, time

class LdapLookup(object):
    def __init__(self, **settings):
        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, False)
        self._ldapconn = ldap.initialize(settings["host"])
        self._ldapconn.protocol_version = ldap.VERSION3
        self._ldapconn.simple_bind_s(settings["user"], settings["passwd"])

        self._search_base = settings["search_base"]

    def user_info(self, username, attrs=[]):
        result = self._ldapconn.search_s(self._search_base, ldap.SCOPE_SUBTREE, 'uid=%s' % username, attrs)
        values = {}
        for attr in attrs:
            try:
                values[attr] = ",".join(result[0][1][attr])
            except:
                values[attr] = None

        return values

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-f", "--file", dest="filename", help="write data to FILE", metavar="FILE")
    parser.add_option("-v", action="count", default=0, dest="verbosity")

    (options, args) = parser.parse_args()

    logging.basicConfig()
    logger = logging.getLogger("box.fetch_user_data")
    logger.setLevel(logging.WARN - int(options.verbosity) * 10)

    # set logging level of "box.api"
    logging.getLogger("box.api").setLevel(logger.getEffectiveLevel())

    config = ConfigParser.ConfigParser()
    settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "settings.conf")
    config.read(settings_file)

    if options.filename:
        out = csv.writer(open(options.filename, "wb"))
    else:
        out = csv.writer(sys.stdout)

    box = box.BoxApi()
    lookup = LdapLookup(**dict(config.items("ldap")))

    box_attrs = [f.strip() for f in config.get("user_lookup", "box_attrs").split(",")]
    local_attrs = [f.strip() for f in config.get("user_lookup", "ldap_lookup_attrs").split(",")]

    #change title of column from "box_tracking_codes" to "box_account_type"  
    headers = box_attrs[:]
    index = headers.index("tracking_codes")
    headers[index] = "account_type" 
    out.writerow(["username", "retrieved_at"] + ["box_%s" % s for s in headers] + ["ldap_%s" % s for s in local_attrs])

    box_params = {}
    box_params["fields"] = ",".join(box_attrs)
    try:
        box_params["limit"] = config.get("user_lookup", "box_request_limit")
    except:
        box_params["limit"] = 100
    box_params["offset"] = 0
    fetched_count = 0

    storage_list = []

    while True:
        get_box_users = box.request("GET", "/users", params=box_params)
        if get_box_users.status_code != requests.codes.ok:
            logger.warn("Response code \"%d \"from \"%s\"\n" % (get_box_users.status_code, get_box_users.url))
        body = get_box_users.text
        box_users = json.loads(body)
        if len(box_users["entries"]) < 1:
            break
        fetched_count += len(box_users["entries"])
        logger.info("Fetched %d out of %d." % (fetched_count, box_users["total_count"]))
        for box_user in box_users["entries"]:
            username = box_user["login"].split("@")[0].lower()
            attrs = [username, time.strftime("%Y-%m-%dT%H:%M:%S%z")]
            for key in box_attrs:
		if key == "tracking_codes":
		    if box_user[key] != []:     
			for tracking_code in box_user[key]:
			    if tracking_code["name"] == "account_type":
			        attrs.append(tracking_code["value"].lower())
		    else:
			attrs.append("individual")
		    continue
		attrs.append(box_user[key])
                #print "\t  BOX {key}: {val}".format(key=key, val=user[key])

            local_user = lookup.user_info(username, local_attrs)
            for key in local_attrs:
                attrs.append(local_user[key])
                #print "\tMCOMM {key}: {val}".format(key=key, val=local_results[key])
            
            out.writerow([unicode(s).encode("ascii", "replace") for s in attrs])
            storage_list.append(box_user["space_used"])

        box_params["offset"] += box_params["limit"]
