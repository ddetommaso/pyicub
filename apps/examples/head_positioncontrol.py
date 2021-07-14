#   Copyright (C) 2019  Davide De Tommaso
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

from pyicub.iCubHelper import iCub, JointPose, ICUB_PARTS

icub = iCub()

a = JointPose(ICUB_PARTS.HEAD, target_position=[-15.0, 20.0, 5.0, 0.0, 0.0, 5.0])
b = JointPose(ICUB_PARTS.HEAD, target_position=[0.0, 0.0, 0.0, 0.0, 0.0, 5.0])
icub.move(a, req_time=1.0)
icub.move(b, req_time=1.0)

icub.close()
