import pathlib

import tomlkit.exceptions
import tomlkit.toml_document
import tomlkit.toml_file

from . import check, show

DEFAULT_CONFIG_PATH = pathlib.Path("~/.config/molim/config.toml")


def load(config_path_str: str = None, section: str = None):
    if config_path_str is not None:
        config_path = pathlib.Path(config_path_str)
        check.ensure_file(config_path)
    else:
        config_path = DEFAULT_CONFIG_PATH.expanduser()
    if config_path.exists():
        check.ensure_file(config_path)
        cfg = tomlkit.toml_file.TOMLFile(config_path)
        doc = cfg.read()
        show.normal(f"Loaded configuration file {config_path}")
        return ConfigReader(doc, section)
    else:
        show.normal("No configuration file, proceeding normally without it.")


class ConfigReader:
    GLOBAL_SECTION = "global"

    def __init__(self, document: tomlkit.toml_document.TOMLDocument, section: str):
        if document is not None:
            check.ensure_type(document, tomlkit.toml_document.TOMLDocument)
        if section is not None:
            check.ensure_type(section, str)
        self.__doc = document
        self.__section = section

    def _get_or_none(self, section, key):
        if not self.__doc or not section or not key:
            return None
        try:
            return self.__doc[section][key]
        except tomlkit.exceptions.NonExistentKey:
            return None

    def _get(self, key: str):
        check.ensure_type(key, str)

        if not self.__doc:
            return None
        return self._get_or_none(self.__section, key) or self._get_or_none(ConfigReader.GLOBAL_SECTION, key)

    def __call__(self, key: str):
        return self._get(key)
