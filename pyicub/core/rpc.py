# BSD 2-Clause License
#
# Copyright (c) 2022, Social Cognition in Human-Robot Interaction,
#                     Istituto Italiano di Tecnologia, Genova
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import yarp
from pyicub.core.logger import YarpLogger

class RpcClient:

    def __init__(self, rpc_server_name):
        self.__logger__ = YarpLogger.getLogger()
        self.__rpc_client__ = yarp.RpcClient()
        self.__rpc_client_port_name__ = rpc_server_name + "/rpc_client/commands"
        self.__rpc_client__.open(self.__rpc_client_port_name__)
        self.__logger__.debug("Connecting %s with %s" % (self.__rpc_client_port_name__, rpc_server_name))
        res = self.__rpc_client__.addOutput(rpc_server_name)
        self.__logger__.debug("Result: %s" % res)

    def execute(self, cmd):
        ans = yarp.Bottle()
        self.__logger__.debug("Executing RPC command %s" % cmd.toString())
        self.__rpc_client__.write(cmd, ans)
        self.__logger__.debug("Result: %s" % ans.toString())
        return ans

    def __del__(self):
        self.__rpc_client__.interrupt()
        self.__rpc_client__.close()
