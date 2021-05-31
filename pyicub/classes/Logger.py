#   Copyright (C) 2021  Davide De Tommaso
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>

import sys
import yarp

class YarpLogger:

    DEBUG = "DEBUG"
    ERROR = "ERROR"
    NONE = "NONE"

    def __init__(self, logtype=NONE):
        self.__logtype__ = logtype
        self.__yarp_logger__ = yarp.Log()

    def error(self, msg):
        self.__yarp_logger__.error(msg)

    def warning(self, msg):
        self.__yarp_logger__.warning(msg)

    def debug(self, msg):
        self.__yarp_logger__.debug(msg)

    def info(self, msg):
        self.__yarp_logger__.info(msg)