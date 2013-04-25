#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import types
sys.path.insert(0, 'path_to_api')
from inventory import Inventory, InventoryIce
import ldap
import urllib2
import json


class CheckHostName(object):
    def __init__(self):
        self.inventory = Inventory()
        self.inv = self.inventory.proxy
        self.host_name = None
        self.verbosity = None
        self.ldap_url = ldap.initialize("ldap://url")
        self.bold = "\033[1m"
        self.normal = "\033[0;0m"
        self.in_use = '\033[91m'
        self.available = '\033[92m'

    def parseArgument(self):
        """
        Parse the arguments!
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('hostname',
                            help="Add hostname(s) to search",
                            nargs='+',
                            )
        parser.add_argument('--verbosity', '-v',
                            help="Show URL information",
                            default=False,
                            action='store_true',
                            )
        args = parser.parse_args()
        self.host_name = args.hostname
        self.verbosity = args.verbosity

    def returnUrl(self, url):
        """
        Build URL's
        """
        url_string = ''
        if isinstance(url, types.ListType):
            if len(url) > 1:
                for u in url:
                    if u == url[0]:
                        url_string += u + '\n'
                    else:
                        url_string += '\t     ' + u + '\n'
            else:
                url_string = url[0]
        else:
            url_string = url
        return url_string


    def returnStatement(self, category, host_name, url, success):
        """
        Returns if formatted text if hostname exists or not.
        """
        if success:
            if url and self.verbosity:
                statement = "{5}{0}: {1}{2} Exists{3} \n\tURL: {4}".format(
                                                           category,
                                                           self.bold,
                                                           host_name,
                                                           self.normal,
                                                           self.returnUrl(url),
                                                           self.in_use)
            else:
                statement = "{4}{0}: {1}{2} Exists{3}".format(category,
                                                               self.bold,
                                                               host_name,
                                                               self.normal,
                                                               self.in_use)

            return statement

    def returnSeparator(self):
        if self.host_name > 1:
            print '-' * 70

    def checkInventory(self, host_name):
        """
        Check hostname in Inventory via the Inventory API
        """
        url = ''
        try:
            check = self.inv.getMachineDetails(host_name)
            check = self.returnStatement('Inventory', host_name, url, True)
        except InventoryIce.InventoryIceException, e:
            check = self.returnStatement('Inventory', host_name, url, False)

        return check

    def checkLdap(self, host_name):
        """
        Check hostname in LDAP
        """
        url = ''
        listed = "params"

        check = self.ldap_url.search_s(listed,
                           ldap.SCOPE_ONELEVEL,
                           attrlist=['cn'])
        for cn in check:
            if cn[1]['cn'][0] == host_name:
                url = "{0}/special/url".format(host_name)
                return self.returnStatement('LDAP', host_name, url, True)

    def checkMunki(self, host_name):
        """
        """
        url = "http://internal/munki/url/{0}".format(host_name)
        response = urllib2.urlopen(url)
        html = response.read()
        url = json.loads(html)
        if html != '[]':
            return self.returnStatement('Munki', host_name, url, True)

    def run(self):
        for host_name in self.host_name:
            if not self.checkInventory(host_name) and\
               not self.checkLdap(host_name) and\
               not self.checkMunki(host_name):
                print "{1}Hostname: {3}{0}{2}{1} is available for use!{2}".format(host_name,
                                                         self.available,
                                                         self.normal,
                                                         self.bold)
                self.returnSeparator()
            elif not self.verbosity:
                if self.checkInventory(host_name) or\
                   self.checkLdap(host_name) or\
                   self.checkMunki(host_name):
                    print "{0}Hostname: {1}{2}{3}{0} is in use{3}".format(self.in_use,
                                                   self.bold,
                                                   host_name,
                                                   self.normal)
                self.returnSeparator()
            else:
                if self.checkInventory(host_name):
                    print self.checkInventory(host_name)
                if self.checkLdap(host_name):
                    print self.checkLdap(host_name)
                if self.checkMunki(host_name):
                    print self.checkMunki(host_name)
                self.returnSeparator()

if __name__ == '__main__':
    chn = CheckHostName()
    chn.parseArgument()
    chn.run()
