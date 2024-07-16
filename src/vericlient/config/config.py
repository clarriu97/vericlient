"""Configuration for the application."""
import os

from dynaconf import Dynaconf

current_directory = os.path.dirname(os.path.realpath(__file__))
basepath = os.path.dirname(__file__)
config_path = os.path.join(basepath, "config.yml")
settings = Dynaconf(
    root_path=current_directory,
    settings_files=[config_path],
    envvar_prefix="VERICLIENT",
)
