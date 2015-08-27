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

import box, ConfigParser, json, optparse, os, requests, sys

if __name__ == "__main__":
    parser = optparse.OptionParser(usage="usage: %prog box_folder_parent_id file_to_upload")
    parser.add_option("-v", action="count", dest="verbosity")

    (options, args) = parser.parse_args()
    config = ConfigParser.ConfigParser()
    settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "settings.conf")
    config.read(settings_file)

    if len(args) != 2:
        parser.print_help()
        sys.exit(1)

    folder_id = args[0]
    file = args[1]

    box = box.BoxApi()

    box_params = {}
    box_params["folder_id"] = folder_id
    box_params["filename"] = file.split(os.pathsep)[-1]
    if options.verbosity >= 2:
        sys.stderr.write("DEBUG: box_params: %s\n" % box_params)

    try:
        f = open(file, 'rb')
    except:
        sys.stderr.write("ERROR: Could not open file.\n")
        sys.exit(1)

    r = box.request("POST", "https://upload.box.com/api/2.0/files/content", append_url=False, data=box_params, files={"file": f})
    rj = r.json()

    #print r, r.text
    if options.verbosity >= 2:
        sys.stderr.write("DEBUG: status: %d\n" % r.status_code)
        try:
            json_str = json.dumps(r.json(), indent=True)
            for line in json_str.split("\n"):
                sys.stderr.write("DEBUG: resonse: %s\n" % line)
        except:
            sys.stderr.write("DEBUG: WARNING: could not cleanly display response data: %s\n" % r.text)
    if r.status_code != 201:
        sys.stderr.write("ERROR: ")
        try:
            sys.stderr.write(rj["message"])
        except:
            sys.stderr.write("An unexpected error occurred.")
        sys.stderr.write("\n")
        sys.exit(1)

    sys.stdout.write("Successfully uploaded.\n")
