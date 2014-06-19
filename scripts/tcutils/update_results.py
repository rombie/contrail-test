__version__ = '1.0'
import os
import sys
import shelve
import logging
import platform
import argparse
import subprocess
import pprint
import json

logging.basicConfig(format='%(asctime)-15s:: %(funcName)s:%(levelname)s::\
                            %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

class TestResultDB:
    def __init__(self, sku=None, dist=None, db=None):
        if not dist:
            dist = platform.linux_distribution()[0].lower()
        self.dist = dist
        if not sku:
            sku = self.find_sku()
        if not db:
            db = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resultsdb.p')
        if not sku:
            raise Exception("Unable to find the sku. Make sure contrail-install-packages is installed")

        self.sku = sku
        self.db = shelve.open(db, writeback=True)

        if self.db.has_key(dist):
            if not self.db[dist].has_key(sku):
                self.db[dist][sku] = {}
        else:
            self.db[dist] = {}
            self.db[dist][sku] = {}

    def find_sku(self):
        pkg = "contrail-install-packages"
        if self.dist in ['centos', 'fedora', 'redhat']:
            cmd = "rpm -q --queryformat '%%{RELEASE}' %s | cut -d'~' -f2 | cut -d '.' -f1" %pkg
        elif self.dist in ['ubuntu']:
            cmd = "dpkg -p %s | grep Version: | cut -d' ' -f2 | cut -d'~' -f2" %pkg
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

        if 'is not installed' in out or 'is not available' in out:
            return None
        return out.strip()

    def find_buildid(self):
        pkg = "contrail-install-packages"
        if self.dist in ['centos', 'fedora', 'redhat']:
            cmd = "rpm -q --queryformat '%%{RELEASE}' %s | cut -d'~' -f1" %pkg
        elif self.dist in ['ubuntu']:
            cmd = "dpkg -p %s | grep Version: | cut -d' ' -f2 | cut -d'-' -f2 | cut -d'~' -f1" %pkg
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

        if 'is not installed' in out or 'is not available' in out:
            return None
        return out.strip()

    def get_bugid(self, fixture, testcase):
        if not (self.db[self.dist][self.sku] and
                self.db[self.dist][self.sku].has_key(fixture) and
                self.db[self.dist][self.sku][fixture].has_key(testcase) and
                self.db[self.dist][self.sku][fixture][testcase].has_key('bugs')):
            return None
        return self.db[self.dist][self.sku][fixture][testcase]['bugs']

    def add_bugid(self, fixture, testcase, bugid):
        if not (self.db[self.dist][self.sku] and
                self.db[self.dist][self.sku].has_key(fixture) and
                self.db[self.dist][self.sku][fixture].has_key(testcase)):
            raise RuntimeError("Unable to find fixture %s/testcase %s"%(fixture, testcase))
        if not self.db[self.dist][self.sku][fixture][testcase].has_key('bugs'):
            self.db[self.dist][self.sku][fixture][testcase]['bugs'] = []
        self.db[self.dist][self.sku][fixture][testcase]['bugs'].append(bugid)
        #self.db[self.dist][self.sku][tcid]['bugs'] = sorted(set(
        #         self.db[self.dist][self.sku][tcid]['bugs']))

    def delete_bugid(self, bugid):
        if not self.db[self.dist][self.sku]:
            raise RuntimeError('Database entry not found for dist %s and sku %s'%(self.dist, self.sku))
        for fixture in self.db[self.dist][self.sku].keys():
            for testcase in self.db[self.dist][self.sku][fixture].keys():
                if self.db[self.dist][self.sku][fixture][testcase].has_key('bugs') and\
                   bugid in self.db[self.dist][self.sku][fixture][testcase]['bugs']:
                    self.db[self.dist][self.sku][fixture][testcase]['bugs'].remove(bugid)

    def update_result(self, fixture, testcase, result, buildid=None):
        if not (self.db[self.dist][self.sku] and
                self.db[self.dist][self.sku].has_key(fixture)):
            self.db[self.dist][self.sku][fixture] = {}
        if not self.db[self.dist][self.sku][fixture].has_key(testcase):
            self.db[self.dist][self.sku][fixture][testcase] = {}
        self.db[self.dist][self.sku][fixture][testcase]['result'] = result
        if not buildid:
            buildid = self.find_buildid()
        if 'pass' in result.lower():
            self.db[self.dist][self.sku][fixture][testcase]['lastpassbuild'] = buildid

    def query_result(self, fixture, testcase):
        if not (self.db[self.dist][self.sku] and
                self.db[self.dist][self.sku].has_key(fixture) and
                self.db[self.dist][self.sku][fixture].has_key(testcase) and
                self.db[self.dist][self.sku][fixture][testcase].has_key('result')):
            return (None, None)
        return (self.db[self.dist][self.sku][fixture][testcase]['result'],
                self.get_lastpass(fixture, testcase))

    def get_lastpass(self, fixture, testcase):
        if not (self.db[self.dist][self.sku] and
                self.db[self.dist][self.sku].has_key(fixture) and
                self.db[self.dist][self.sku][fixture].has_key(testcase) and
                self.db[self.dist][self.sku][fixture][testcase].has_key('lastpassbuild')):
            return None
        return self.db[self.dist][self.sku][fixture][testcase]['lastpassbuild']

    def tclist(self):
        print self.db[self.dist][self.sku].keys()

    def dump_db(self):
        print json.dumps(self.db[self.dist][self.sku])

    def close(self):
        self.db.close()

def parse_cli(args):    
    '''Define and Parse arguments for the script'''
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', '-v',
                        action='version',
                        version=__version__,
                        help='Display version and exit')
    parser.add_argument('--oper',
                        action='store',  
                        required=True,
                        help='Add or Delete a bugid or Query result of a testcase')
    parser.add_argument('--sku', 
                        action='store',
                        required=True,
                        help='sku name eg. grizzly, havana')
    parser.add_argument('--dist',
                        action='store',
                        required=True,
                        help='linux distribution eg. CentOS, ubuntu')
    parser.add_argument('--fixture',
                        action='store',
                        help='Name of the test fixture')
    parser.add_argument('--testcase',
                        action='store',
                        help='Testcase name')
    parser.add_argument('--dbfile',
                        action='store',
                        help='database file location')
    parser.add_argument('--bugid',
                        action='store',
                        help='bug id')

    pargs = parser.parse_args(args)
    if len(args) == 0:
        parser.print_help()
        sys.exit(2)
    return dict(pargs._get_kwargs())

class ResultCLI:
    def __init__(self, **kwargs):
        self.oper = kwargs.get('oper', None).lower()
        self.fixture = kwargs.get('fixture', None)
        self.testcase = kwargs.get('testcase', None)
        self.sku = kwargs.get('sku', None)
        self.dist = kwargs.get('dist', None)
        self.dbfile = kwargs.get('dbfile', None)
        self.bugid = kwargs.get('bugid', None)
        self.db = TestResultDB(sku=self.sku, db=self.dbfile, dist=self.dist)

    def setup(self):
        if self.oper in 'add':
            if not (self.fixture and self.testcase and self.bugid):
                log.error("Please specify fixture name, testcase name and bugid for add operation")
                sys.exit(2)
            self.db.add_bugid(self.fixture, self.testcase, self.bugid)
        elif self.oper in 'delete':
            if not self.bugid:
                log.error("Please specify bugid for delete operation")
                sys.exit(2)
            self.db.delete_bugid(self.bugid)
        elif self.oper in 'query':
            if not (self.fixture and self.testcase):
                log.error("Please specify fixture name and testcase name for query operation")
                sys.exit(2)
            (result, buildid) = self.db.query_result(self.fixture, self.testcase)
            log.info("Result is %s for buildid %s for %s on %s", result, buildid, self.sku, self.dist)
        elif self.oper in 'dump':
            self.db.dump_db()
        elif self.oper in 'tclist':
            self.db.tclist()
        else:
            log.error("Unsupport operation, use either of add, delete or query")

    def cleanup(self):
        self.db.close()

def main():
    pargs = parse_cli(sys.argv[1:])
    cli = ResultCLI(**pargs)
    cli.setup()
    cli.cleanup()

if __name__ == "__main__":
    main()
