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

from pyicub.helper import iCub, JointPose, JointsTrajectoryCheckpoint, LimbMotion, iCubFullbodyAction, iCubFullbodyStep, ICUB_PARTS

icub = iCub()
action = icub.createAction()
up = JointsTrajectoryCheckpoint(JointPose(target_joints=[20.0, 0.0, 0.0, 0.0, 0.0, 5.0]), duration=3.0)
down = JointsTrajectoryCheckpoint(JointPose(target_joints=[-20.0, 0.0, 0.0, 0.0, 0.0, 5.0]), duration=3.0)
home = JointsTrajectoryCheckpoint(JointPose(target_joints=[0.0, 0.0, 0.0, 0.0, 0.0, 5.0]), duration=3.0)
    
example_motion = LimbMotion(ICUB_PARTS.HEAD)
example_motion.addCheckpoint(up)
example_motion.addCheckpoint(down)
example_motion.addCheckpoint(home)
    
step = icub.createStep()
step.setLimbMotion(example_motion)
action.addStep(step)

req = icub.play(action, wait_for_completed=False)
print("Doing some stuff in parallel...")
print("...waiting for action completation...")
req.wait_for_completed()

