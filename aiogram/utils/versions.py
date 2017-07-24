from .helper import Helper, HelperMode, Item


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

        if version[3] != 'final':
            mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'rc'}
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
