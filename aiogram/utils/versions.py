import datetime
import os
import subprocess

from .helper import Helper, HelperMode, Item


# Based on https://github.com/django/django/blob/master/django/utils/version.py


class Version:
    def __init__(self, major=0, minor=0, maintenance=0, stage='final', build=0):
        self.__raw_version = None
        self.__version = None

        self.version = (major, minor, maintenance, stage, build)

    @property
    def version(self):
        if self.__version is None:
            self.__version = self.get_version()
        return self.__version

    @version.setter
    def version(self, version):
        assert isinstance(version, (tuple, list))
        self.__raw_version = version
        self.__version = None

    @property
    def major(self):
        return self.__raw_version[0]

    @property
    def minor(self):
        return self.__raw_version[1]

    @property
    def maintenance(self):
        return self.__raw_version[2]

    @property
    def stage(self):
        return self.__raw_version[3]

    @property
    def build(self):
        return self.__raw_version[4]

    @property
    def raw_version(self):
        return self.raw_version

    @property
    def pypi_development_status(self):
        if self.stage == Stage.DEV:
            status = '2 - Pre-Alpha'
        elif self.stage == Stage.ALPHA:
            status = '3 - Alpha'
        elif self.stage == Stage.BETA:
            status = '4 - Beta'
        elif self.stage == Stage.FINAL:
            status = '5 - Production/Stable'
        else:
            status = '1 - Planning'
        return f"Development Status :: {status}"

    def get_version(self):
        """
        Returns a PEP 440-compliant version number from VERSION.
        :param:
        :return:
        """
        version = self.__raw_version

        # Now build the two parts of the version number:
        # app = X.Y[.Z]
        # sub = .devN - for pre-alpha releases
        #     | {a|b|rc}N - for alpha, beta, and rc releases

        main = self.get_main_version()

        sub = ''
        if version[3] == Stage.DEV and version[4] == 0:
            git_changeset = self.get_git_changeset()
            if git_changeset:
                sub = '.dev{0}'.format(git_changeset)
        elif version[3] != Stage.FINAL:
            mapping = {Stage.ALPHA: 'a', Stage.BETA: 'b', Stage.RC: 'rc', Stage.DEV: 'dev'}
            sub = mapping[version[3]] + str(version[4])

        return str(main + sub)

    def get_main_version(self):
        """
        Returns app version (X.Y[.Z]) from VERSION.
        :param:
        :return:
        """
        version = self.__raw_version
        parts = 2 if version[2] == 0 else 3
        return '.'.join(str(x) for x in version[:parts])

    def get_git_changeset(self):
        """Return a numeric identifier of the latest git changeset.
        The result is the UTC timestamp of the changeset in YYYYMMDDHHMMSS format.
        This value isn't guaranteed to be unique, but collisions are very unlikely,
        so it's sufficient for generating the development version numbers.
        """
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        git_log = subprocess.Popen(
            'git log --pretty=format:%ct --quiet -1 HEAD',
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, cwd=repo_dir, universal_newlines=True,
        )
        timestamp = git_log.communicate()[0]
        try:
            timestamp = datetime.datetime.utcfromtimestamp(int(timestamp))
        except ValueError:
            return None
        return timestamp.strftime('%Y%m%d%H%M%S')

    def __str__(self):
        return self.version

    def __repr__(self):
        return '<Version:' + str(self) + '>'


class Stage(Helper):
    mode = HelperMode.lowercase

    FINAL = Item()
    ALPHA = Item()
    BETA = Item()
    RC = Item()
    DEV = Item()
