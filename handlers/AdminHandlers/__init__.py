# -*- coding: utf-8 -*-
"""
Created on Nov 24, 2014

@author: moloch

    Copyright 2014 Root the Box

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.


This file contains all of the administrative functions.
There's a lot of code in here ... and it's mostly ugly validation code...

Guidelines for writing code in this file:
    - GET requests should NEVER alter application state
    - All functions should check authentication/IP address/permission
"""
from .AdminGameHandlers import *
from .AdminGameObjectHandlers import *
from .AdminUploadsHandlers import *
from .AdminUserHandlers import *
from .AdminManageTaskHandler import *
# from .UserInstructionsHandlers import *