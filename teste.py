
import flet as ft
import mysql.connector
import dotenv
import os, hashlib
import sys
from datetime import datetime, date
from importlib.metadata import version

print("Flet:", ft.__version__)
print("MySQL Connector:", mysql.connector.__version__)

print("Python-Dotenv:", version("python-dotenv"))

print("Python:", sys.version)