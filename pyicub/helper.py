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
yarp.Network().init()

from pyicub.controllers.gaze import GazeController
from pyicub.controllers.position import JointPose, PositionController
from pyicub.actions import PyiCubCustomCall, JointsTrajectoryCheckpoint, LimbMotion, GazeMotion, iCubFullbodyStep, iCubFullbodyAction
from pyicub.modules.emotions import emotionsPyCtrl
from pyicub.modules.speech import iSpeakPyCtrl
from pyicub.modules.face import facePyCtrl
from pyicub.modules.faceLandmarks import faceLandmarksPyCtrl
from pyicub.core.ports import BufferedReadPort
from pyicub.core.logger import PyicubLogger, YarpLogger
from pyicub.requests import iCubRequestsManager, iCubRequest
from pyicub.rest import iCubRESTManager
from pyicub.utils import SingletonMeta, getPublicMethods

from collections import deque
import threading
import os
import time
import json


class ICUB_PARTS:
    HEAD       = 'head'
    FACE       = 'face'
    TORSO      = 'torso'
    LEFT_ARM   = 'left_arm'
    RIGHT_ARM  = 'right_arm'
    LEFT_LEG   = 'left_leg'
    RIGHT_LEG  = 'right_leg'

class iCubPart:
    def __init__(self, name, joints_n):
        self.name = name
        self.joints_n = joints_n
        self.joints_list = range(0, joints_n)


class PyiCubApp(metaclass=SingletonMeta):

    def __init__(self, logging=False, logging_path=None, rest_manager_host=None, rest_manager_port=None):
        
        PYICUB_LOGGING = os.getenv('PYICUB_LOGGING')
        PYICUB_LOGGING_PATH = os.getenv('PYICUB_LOGGING_PATH')
        PYICUB_API = os.getenv('PYICUB_API')
        PYICUB_API_BACKEND_HOST = os.getenv('PYICUB_API_BACKEND_HOST')
        PYICUB_API_BACKEND_PORT = os.getenv('PYICUB_API_BACKEND_PORT')
    
        if PYICUB_LOGGING:
            if PYICUB_LOGGING == 'true':
                logging = True
        
        self._logging_ = logging
        self._logger_ = PyicubLogger.getLogger() #YarpLogger.getLogger()

        if self._logging_:
            self._logger_.enable_logs()
            self._logger_ = PyicubLogger.getLogger() #YarpLogger.getLogger()

            if PYICUB_LOGGING_PATH:
                logging_path = PYICUB_LOGGING_PATH

            if os.path.isdir(logging_path):
                if isinstance(self._logger_, PyicubLogger):
                    self._logger_.configure(PyicubLogger.LOGGING_LEVEL, PyicubLogger.FORMAT, True, logging_path)
            else:
                if isinstance(self._logger_, PyicubLogger):
                    self._logger_.configure(PyicubLogger.LOGGING_LEVEL, PyicubLogger.FORMAT)
        else:
            self._logger_.disable_logs()

        self._request_manager_ = iCubRequestsManager(self._logger_, self._logging_, logging_path)

        if PYICUB_API:
            if PYICUB_API == 'true':
                if PYICUB_API_BACKEND_HOST:
                    rest_manager_host = PYICUB_API_BACKEND_HOST
                    if PYICUB_API_BACKEND_PORT:
                        rest_manager_port = PYICUB_API_BACKEND_PORT
                    else:
                        rest_manager_port = 5000
                else:
                    rest_manager_host = "0.0.0.0"

        if rest_manager_host:
            self._rest_manager_ = iCubRESTManager(icubrequestmanager=self._request_manager_, rule_prefix="/pyicub",  host=rest_manager_host, port=rest_manager_port)
        else:
            self._rest_manager_ = None

    @property
    def logger(self):
        return self._logger_

    @property
    def request_manager(self):
        return self._request_manager_

    @property
    def rest_manager(self):
        return self._rest_manager_

class iCubSingleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls.robot_name not in cls._instances.keys():
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls.robot_name] = instance
        return cls._instances[cls.robot_name]

class iCub(metaclass=iCubSingleton):

    def __init__(self, robot_name="icub"):
        SIMULATION = os.getenv('ICUB_SIMULATION')

        self._position_controllers_ = {}
        self._services_ = {}
        self._gaze_ctrl_            = None
        self._emo_                  = None
        self._speech_               = None
        self._face_                 = None
        self._facelandmarks_        = None
        self._monitors_             = []
        self._logger_               = PyiCubApp().logger

        self._icub_parts_ = {}
        self._icub_parts_[ICUB_PARTS.FACE       ]   = iCubPart(ICUB_PARTS.FACE      , 1)
        self._icub_parts_[ICUB_PARTS.HEAD       ]   = iCubPart(ICUB_PARTS.HEAD      , 6)
        self._icub_parts_[ICUB_PARTS.LEFT_ARM   ]   = iCubPart(ICUB_PARTS.LEFT_ARM  , 16)
        self._icub_parts_[ICUB_PARTS.RIGHT_ARM  ]   = iCubPart(ICUB_PARTS.RIGHT_ARM , 16)
        self._icub_parts_[ICUB_PARTS.TORSO      ]   = iCubPart(ICUB_PARTS.TORSO     , 3)
        self._icub_parts_[ICUB_PARTS.LEFT_LEG   ]   = iCubPart(ICUB_PARTS.LEFT_LEG  , 6)
        self._icub_parts_[ICUB_PARTS.RIGHT_LEG  ]   = iCubPart(ICUB_PARTS.RIGHT_LEG , 6)

        self._imported_actions_ = {}

        if SIMULATION:
            if SIMULATION == 'true':
                robot_name = "icubSim"

        self._robot_name_ = robot_name

        self._initPositionControllers_()
        self._initGazeController_()

        if PyiCubApp().rest_manager:
            self._registerDefaultServices_()
    
    def __del__(self):
        self.close()
        yarp.Network().init()
        yarp.Network().fini()

    def _initPositionControllers_(self):
        for part_name in self._icub_parts_.keys():
            self._initPositionController_(part_name)

    def _initPositionController_(self, part_name):
        ctrl = PositionController(self._robot_name_, part_name, self._logger_)
        if ctrl.isValid():
            self._position_controllers_[part_name] = ctrl
            self._position_controllers_[part_name].init()
        else:
            self._logger_.warning('PositionController <%s> not callable! Are you sure the robot part is available?' % part_name)

    def _initGazeController_(self):
        gaze_ctrl = GazeController(self._robot_name_, self._logger_)
        if gaze_ctrl.isValid():
            gaze_ctrl.init()
            self._gaze_ctrl_ = gaze_ctrl
        else:
            self._logger_.warning('GazeController not correctly initialized! Are you sure the controller is available?')
            self._gaze_ctrl_ = None

    def _registerDefaultServices_(self):
        PyiCubApp().rest_manager.register(self.importActionFromJSON, robot_name=self.robot_name, app_name='utils')
        PyiCubApp().rest_manager.register(self.playAction, robot_name=self.robot_name, app_name='utils')

        if self.gaze:
            for method in getPublicMethods(self.gaze):
                self.rest_manager.register(getattr(self.gaze, method), robot_name=self.robot_name, app_name='gaze')
        if self.speech:
            for method in getPublicMethods(self.speech):
                self.rest_manager.register(getattr(self.speech, method), robot_name=self.robot_name, app_name='speech')
        if self.emo:
            for method in getPublicMethods(self.emo):
                self.rest_manager.register(getattr(self.emo, method), robot_name=self.robot_name, app_name='emotions')

    def close(self):
        if len(self._monitors_) > 0:
            for v in self._monitors_:
                v.stop()

    @property
    def gaze(self):
        if self._gaze_ctrl_ is None:
            self._initGazeController_()
        return self._gaze_ctrl_
        

    @property
    def face(self):
        if self._face_ is None:
            try:
                self._face_ = facePyCtrl(self.robot_name)
            except:
                self._logger_.warning('facePyCtrl not correctly initialized!')
                return None
        return self._face_

    @property
    def facelandmarks(self):
        if self._facelandmarks_ is None:
            try:
                self._facelandmarks_ = faceLandmarksPyCtrl()
            except:
                self._logger_.warning('facePyCtrl not correctly initialized!')
                return None
        return self._facelandmarks_

    @property
    def rest_manager(self):
        return PyiCubApp().rest_manager

    @property
    def request_manager(self):
        return PyiCubApp().request_manager

    @property
    def emo(self):
        if self._emo_ is None:
            try:
                self._emo_ = emotionsPyCtrl(self.robot_name)
            except:
                self._logger_.warning('emotionsPyCtrl not correctly initialized!')
                return None
        return self._emo_

    @property
    def speech(self):
        if self._speech_ is None:
            try:
                self._speech_ = iSpeakPyCtrl()
            except:
                self._logger_.warning('iSpeakPyCtrl not correctly initialized!')
                return None
        return self._speech_

    @property
    def parts(self):
        return self._icub_parts_

    @property
    def robot_name(self):
        return self._robot_name_

    def createStep(self, name='step', offset_ms=None, timeout=iCubRequest.TIMEOUT_REQUEST):
        return iCubFullbodyStep(name, offset_ms)

    def createAction(self, name='action', JSON_file=None):
        return iCubFullbodyAction(name, JSON_file)

    def execCustomCall(self, custom_call: PyiCubCustomCall, prefix='', ts_ref=0.0):
        calls = custom_call.target.split('.')
        foo = self
        for call in calls:
            foo = getattr(foo, call)
        req = self.request_manager.create(timeout=iCubRequest.TIMEOUT_REQUEST,
                                          target=foo, 
                                          name=prefix + '/%s' % str(custom_call.target), 
                                          ts_ref=ts_ref)
        self.request_manager.run_request(req, True, *custom_call.args)
        req.wait_for_completed()

    def execCustomCalls(self, calls, prefix='', ts_ref=0.0):
        for call in calls:
            self.execCustomCall(call, prefix, ts_ref)

    def getPositionController(self, part_name):
        if part_name in self._position_controllers_.keys():
            return self._position_controllers_[part_name]
        self._logger_.error('PositionController <%s> non callable! Are you sure the robot part is available?' % part_name)
        return None

    def moveGaze(self, gaze_motion: GazeMotion, prefix='', ts_ref=0.0):
        requests = []

        for i in range(0, len(gaze_motion.checkpoints)):
            req = self.request_manager.create(timeout=iCubRequest.TIMEOUT_REQUEST, 
                                              target=getattr(self.gaze, gaze_motion.lookat_method), 
                                              name=prefix + '/%s' % str(gaze_motion.lookat_method), 
                                              ts_ref=ts_ref)
            self.request_manager.run_request(req, True, *gaze_motion.checkpoints[i])
            requests.append(req)
        
        self.request_manager.join_requests(requests)
        
        return requests

    def movePart(self, limb_motion: LimbMotion, prefix='', ts_ref=0.0):
        requests = []
        ctrl = self.getPositionController(limb_motion.part_name)
        for i in range(0, len(limb_motion.checkpoints)):
            if ctrl is None:
                self._logger_.warning('movePart <%s> ignored!' % limb_motion.part_name)
            else:
                req = self.request_manager.create(timeout=limb_motion.checkpoints[i].timeout, 
                                                  target=ctrl.move,
                                                  name=prefix + '/' + limb_motion.part_name,
                                                  ts_ref=ts_ref)

                self.request_manager.run_request(req,
                                                 wait_for_completed=True,
                                                 pose=limb_motion.checkpoints[i].pose,
                                                 req_time=limb_motion.checkpoints[i].duration,
                                                 tag=req.tag)
                
                requests.append(req)

        self.request_manager.join_requests(requests)       
        return requests


    def moveStep(self, step, prefix='', ts_ref=0.0):
        if ts_ref == 0.0:
            ts_ref = round(time.perf_counter(), 4)
        requests = []
        self._logger_.debug('Step <%s> STARTED!' % step.name)
        if step.offset_ms:
            time.sleep(step.offset_ms/1000.0)
        if step.gaze_motion:
            req = self.request_manager.create(timeout=iCubRequest.TIMEOUT_REQUEST,
                                              target=self.moveGaze,
                                              name=prefix + '/gaze',
                                              ts_ref=ts_ref)
            requests.append(req)
            self.request_manager.run_request(req,
                                             False,
                                             step.gaze_motion,
                                             req.tag,
                                             ts_ref)
        if step.custom_calls:
            req = self.request_manager.create(timeout=iCubRequest.TIMEOUT_REQUEST,
                                              target=self.execCustomCalls,
                                              name=prefix + '/custom',
                                              ts_ref=ts_ref)
            requests.append(req)
            self.request_manager.run_request(req,
                                             False,
                                             step.custom_calls,
                                             req.tag,
                                             ts_ref)
        for part, limb_motion in step.limb_motions.items():
            req = self.request_manager.create(timeout=iCubRequest.TIMEOUT_REQUEST,
                                              target=self.movePart,
                                              name=prefix + '/limb',
                                              ts_ref=ts_ref)
            requests.append(req)
            self.request_manager.run_request(req,
                                             False,
                                             limb_motion,
                                             req.tag,
                                             ts_ref)
        self.request_manager.join_requests(requests)
        self._logger_.debug('Step <%s> COMPLETED!' % step.name)
        return requests
    
    def moveSteps(self, steps, prefix):
        requests = []
        t0 = round(time.perf_counter(), 4)
        for step in steps:
            prefix = "%s/%s" % (prefix, step.name)
            req = self.request_manager.create(timeout=iCubRequest.TIMEOUT_REQUEST,
                                              target=self.moveStep,
                                              name=prefix,
                                              ts_ref=t0)
            requests.append(req)
            self.request_manager.run_request(req,
                                             True,
                                             step,
                                             req.tag,
                                             t0)
        self.request_manager.join_requests(requests)
        return requests

    def importActionFromJSON(self, action_json):
        action_id = len(self._imported_actions_.values()) + 1
        action = iCubFullbodyAction()
        action.fromJSON(action_json)
        self._imported_actions_[action_id] = action
        return action_id

    def playAction(self, action_id):
        self.play(self._imported_actions_[action_id])

    def playActionFromJSON(self, json_file):
        imported_action = iCubFullbodyAction(JSON_file=json_file)
        self.play(imported_action)

    def play(self, action: iCubFullbodyAction, wait_for_completed=True):
        t0 = round(time.perf_counter(), 4)
        self._logger_.debug('Playing action <%s>' % action.name)
        prefix = "/%s" % action.name
        req = self.request_manager.create(timeout=iCubRequest.TIMEOUT_REQUEST,
                                          target=self.moveSteps,
                                          name=prefix,
                                          ts_ref=t0)
        
        self.request_manager.run_request(req,
                                         wait_for_completed,
                                         action.steps,
                                         prefix)
        if wait_for_completed:
            self._logger_.debug('Action <%s> finished!' % action.name)
        return req

    def portmonitor(self, yarp_src_port, activate_function, callback):
        self._monitors_.append(PortMonitor(yarp_src_port, activate_function, callback, period=0.01, autostart=True))


class iCubRESTApp:

    def __init__(self, app_name='iCubRESTApp', robot_name="icub"):
        self._name_ = app_name
        self._icub_ = iCub(robot_name=robot_name)

        for method in getPublicMethods(self):
            PyiCubApp().rest_manager.register(getattr(self, method), robot_name=self.icub.robot_name, app_name=app_name)

    @property
    def icub(self):
        return self._icub_

class PortMonitor:
    def __init__(self, yarp_src_port, activate_function, callback, period=0.01, autostart=False):
        self._port_ = BufferedReadPort(yarp_src_port + "_reader_" + str(id(self)), yarp_src_port,)
        self._activate_ = activate_function
        self._callback_ = callback
        self._period_ = period
        self._values_ = deque( int(1000/(period*1000))*[None], maxlen=int(1000/(period*1000))) #Values of the last second
        self._stop_thread_ = False
        self._worker_thread_ = None
        if autostart:
            self.start()

    def start(self):
        if self._stop_thread_:
            self.stop()
        self._worker_thread_ = threading.Thread(target=self.worker)
        self._worker_thread_.start()

    def stop(self):
        if not self._stop_thread_:
            self._stop_thread_ = True
        self._worker_thread_.join()
        self._stop_thread_ = False

    def worker(self):
        while not self._stop_thread_:
            res = self._port_.read(shouldWait=False)
            if not res is None:
                self._values_.append(res.toString())
                if self._activate_(self._values_):
                    self._callback_()
            yarp.delay(self._period_)
