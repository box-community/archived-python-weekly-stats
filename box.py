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

import ConfigParser, json, logging, os, requests, sys, time, urlparse

class BoxApiError(Exception):
    pass

class BoxApi(object):
    def __init__(self, config_dir=None, **config):
        self._logger = logging.getLogger("box.api")
        if self._logger.getEffectiveLevel() <= logging.DEBUG:
            # turn on HTTP logging if log level is DEBUG
            import httplib
            httplib.HTTPConnection.debuglevel = 1

            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(self._logger.getEffectiveLevel())
            requests_log.propagate = True
        if config_dir is not None:
            self._config_dir = config_dir
        else:
            self._config_dir = os.path.dirname(os.path.realpath(__file__))

        self._settings_file = os.path.join(self._config_dir, "settings.conf")
        self._auth_file = os.path.join(self._config_dir, "auth.conf")
        config_files = (self._settings_file, self._auth_file)
        self._logger.debug("config_files: %s" % str(config_files))

        config_from_file = ConfigParser.RawConfigParser()
        config_from_file.read(config_files)

        # TODO config validation:
        self._config = dict(config_from_file.items("box") + config.items())

        self._session = requests.Session()

        try:
            self._auth = dict(config_from_file.items("box auth"))
            self._session.headers.update({"Authorization": "Bearer {access}".format(access=self.get_access_token())})
        except:
            msg = "initialization: could not set auth"
            self._logger.error(msg)
        self._session.headers.update({"Accept": "application/json"})

    def v1query(self, action, params=None):
        """A convenience method to make using the legacy V1 API easier to use."""

        from xml.dom import minidom
        class BoxApiV1Response(object):
            def __init__(self, resp):
                self._dom = minidom.parseString(resp.text)
            def find(self, node):
                return self._dom.getElementsByTagName(node)[0].firstChild.nodeValue

        if params is None:
            params = {}

        params['action'] = action
        params['api_key'] = self._config["client_id"]
        params['auth_token'] = self._auth["v1auth.token"]

        resp = requests.get("https://www.box.net/api/1.0/rest", params=params)
        return BoxApiV1Response(resp)

    def request(self, method, url, append_url=True, retry_on=(429,), max_attempts=10, **kwargs):
        if append_url:
            url = "https://api.box.com/2.0/"+ url.strip("/")

        self._logger.debug("URL: %s" % url)
        self._logger.debug("method: %s" % method)

        attempt_count = 0
        sleep_time = 0

        # retry the request until a good status code is received or we exhausted our attempt limit:
        while attempt_count < max_attempts:
            attempt_count += 1
            if attempt_count > 1:
                # set the sleep time to an exponentially increasing value in case we're being throttled:
                sleep_time = 2 ** attempt_count;
                self._logger.warn("Response code \"%d \"from \"%s\". Sleeping for %d seconds before retrying." % (r.status_code, r.url, sleep_time))
                #time.sleep(sleep_time)

            r = self._session.request(method, url, **kwargs)
            if r.status_code == 401:
                if self.refresh_tokens():
                    self._logger.info("Response code \"%d \"from \"%s\". Tokens refreshed, retrying." % (r.status_code, r.url))
                    attempt_count -= 1
            elif r.status_code not in retry_on:
                return r

        msg = "Response code \"%d \"from \"%s\". Giving up after %d attempts." % (r.status_code, r.url, attempt_count)
        self._logger.error(msg)
        raise BoxApiError(msg)

    def get_access_token(self):
        expires = time.strptime(self._auth["access.token.expires"], "%Y-%m-%dT%H:%M:%S")
        if time.mktime(expires) - time.mktime(time.localtime()) < 60:
            self.refresh_tokens()

        return self._auth["access.token"]

    def refresh_tokens(self):
        self._logger.info("refreshing tokens")
        tokens_resp = requests.request("POST", "https://www.box.com/api/oauth2/token", data={"grant_type": "refresh_token", "refresh_token": self._auth["refresh.token"], "client_id": self._config["client_id"], "client_secret": self._config["client_secret"]})
        tokens = json.loads(tokens_resp.text)
        if tokens_resp.status_code == requests.codes.ok:
            self.save_tokens(tokens)
            return True
        else:
            msg = "Refreshing tokens failed (\"%s\").\n" % tokens["error_description"]
            self._logger.error(msg)
            raise BoxApiError(msg)

    def save_tokens(self, tokens=None, v1token=None):
        # Create new config section
        auth_config = ConfigParser.RawConfigParser()
        auth_config.add_section("box auth")

        # populate with existing auth values
        if hasattr(self, "_auth"):
            for k in sorted(self._auth.keys()):
                auth_config.set("box auth", k, self._auth[k])

        if v1token:
            user = json.loads(requests.request("GET", "https://api.box.com/2.0/users/me", params={"fields": "login,role"}, headers={"Authorization": "BoxAuth api_key={api_key}&auth_token={auth_token}".format(api_key=self._config["client_id"], auth_token=v1token)}).text)

            auth_config.set("box auth", "v1auth.token.user.role", user["role"])
            auth_config.set("box auth", "v1auth.token.user.login", user["login"])

            auth_config.set("box auth", "v1auth.token", v1token)

        if tokens:
            self._session.headers.update({"Authorization": "Bearer {access}".format(access=tokens["access_token"])})
            user = json.loads(self.request("GET", "/users/me", params={"fields": "login,role"}).text)

            auth_config.set("box auth", "user.role", user["role"])
            auth_config.set("box auth", "user.login", user["login"])

            auth_config.set("box auth", "access.token", tokens["access_token"])
            auth_config.set("box auth", "access.token.expires", time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() + tokens["expires_in"])))

            auth_config.set("box auth", "refresh.token", tokens["refresh_token"])
            auth_config.set("box auth", "refresh.token.expires", time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() + 1209600)))

        self._auth = dict(auth_config.items("box auth"))
        save_to = self._auth_file

        save_to_fp = open(save_to, "w")
        save_to_fp.write("# This file is maintained by the box python module. DO NOT MODIFY.\n\n")
        auth_config.write(save_to_fp)

if __name__ == "__main__":

    def get_oauth2_tokens(api):
        import BaseHTTPServer, random, webbrowser

        http_server_address = ("127.0.0.1", 8000)
        global oauth_info
        oauth_info = {}
        oauth_info["code"] = ""
        oauth_info["state"] = str(random.randint(876546, 34567898765))
        auth_url = "https://www.box.com/api/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri=http://{redirect_server}:{redirect_port}/&state={state}".format(client_id=api._config["client_id"], state=oauth_info["state"], redirect_server=http_server_address[0], redirect_port=http_server_address[1])
        print "Authenticate here: {url}".format(url=auth_url)
        webbrowser.open(auth_url)

        class auth_code_handler(BaseHTTPServer.BaseHTTPRequestHandler):
            def do_GET(self):
                global oauth_info
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                qs = urlparse.parse_qs(self.path)
                try:
                    if oauth_info["state"] != qs["/?state"][0]: #  "/?" prefix is a hack, TODO: fix it maybe
                        self.wfile.write("ERROR: state parameter mismatch.")
                        print "ERROR: state parameter mismatch"
                        print "state parameter mismatch"
                        sys.exit(1)
                    oauth_info["code"] = qs["code"][0]
                except:
                    self.wfile.write("ERROR: parameters (\"state\" and \"code\") not found")
                    print "ERROR: parameters (\"state\" and \"code\") not found"
                    sys.exit(1)

                self.wfile.write("return to {script_name}\n".format(script_name=sys.argv[0]))

            def log_message(self, format, *args):
                # supress log messages to stderr
                return


        httpd = BaseHTTPServer.HTTPServer(('127.0.0.1', 8000), auth_code_handler)
        httpd.handle_request()
        tokens = json.loads(requests.post("https://www.box.com/api/oauth2/token", data={"grant_type": "authorization_code", "code": oauth_info["code"], "client_id": api._config["client_id"], "client_secret": api._config["client_secret"]}).text)
        api.save_tokens(tokens) # TODO make this optional and add param to save_tokens, to specify path
        print "SUCCESS: auth tokens saved."

    def get_auth_token(api):
        from xml.dom import minidom
        import webbrowser

        get_ticket = requests.get("https://www.box.net/api/1.0/rest?action=get_ticket&api_key={api_key}".format(api_key=api._config["client_id"]))
        ticket_dom = minidom.parseString(get_ticket.text)
        ticket = ticket_dom.getElementsByTagName('ticket')[0].firstChild.nodeValue

        auth_url = "https://www.box.com/api/1.0/auth/{ticket}".format(ticket=ticket)
        print "Authenticate here: {url}".format(url=auth_url)
        webbrowser.open(auth_url)

        raw_input("Then press enter...")
        print ""

        get_token = requests.get("https://www.box.net/api/1.0/rest?action=get_auth_token&api_key={api_key}&ticket={ticket}".format(api_key=api._config["client_id"], ticket=ticket))
        token_dom = minidom.parseString(get_token.text)
        auth_token = token_dom.getElementsByTagName("auth_token")[0].firstChild.nodeValue

        api.save_tokens(v1token=auth_token) # TODO make this optional and add param to save_tokens, to specify path
        print "SUCCESS: auth tokens saved."



    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog [ auth | v1auth | access_token | get ] [options]")

    parser.add_option("-v", action="count", default=0, dest="verbosity")
    (options, args) = parser.parse_args()

    logging.basicConfig() # you need to initialize logging, otherwise sys.argvyou will not see anything from requests
    logging.getLogger().setLevel(logging.WARN - int(options.verbosity) * 10)

    api = BoxApi()
    if len(args) >= 1:
        if args[0] == "auth":
            get_oauth2_tokens(api)
        elif args[0] == "v1auth":
            get_auth_token(api)
        elif args[0] == "access_token":
            print api._auth["access.token"]
        elif args[0] == "get":

            r = api.request("GET", args[1])
            print json.dumps(r.json(), indent=True)
        elif args[0] == "refresh":
            api.refresh_tokens()
        else:
            parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)
