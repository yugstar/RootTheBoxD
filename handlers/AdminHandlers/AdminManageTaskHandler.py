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


Handlers for user-related tasks.
"""
# pylint: disable=unused-wildcard-import
# pylint: disable=no-member


import logging
# added models
from models.FileUpload import FileUpload
# new models above
from models.Team import Team
from models.Box import Box
from models.Flag import Flag
from models.EmailToken import EmailToken
from models.Corporation import Corporation
from models.User import User, ADMIN_PERMISSION
from models.Permission import Permission
from models.GameLevel import GameLevel
from handlers.BaseHandlers import BaseHandler
from libs.SecurityDecorators import *
from libs.ValidationError import ValidationError
from libs.EventManager import EventManager
from libs.Identicon import identicon
from libs.ConfigHelpers import save_config
from builtins import str
from tornado.options import options
from netaddr import IPAddress

# added var below
MAX_UPLOADS = 5

class AdminManagetaskHandler(BaseHandler):
    @restrict_ip_address
    @authenticated
    @authorized(ADMIN_PERMISSION)
    def get(self, *args, **kwargs):
        self.render("admin/view/managetask.html", errors=None)


class AdminEditTeamsUploadHandler(BaseHandler):
    @restrict_ip_address
    @authenticated
    @authorized(ADMIN_PERMISSION)
    def post(self, *args, **kwargs):
        try:
            group = self.get_argument("team_uuid", "all")
            message = self.get_argument("message", "")
            value = int(self.get_argument("money", 0))
            if group == "all":
                teams = Team.all()
                for team in teams:
                    team.set_score("admin", value + team.money)
                    self.dbsession.add(team)
            else:
                team = Team.by_uuid(group)
                team.set_score("admin", value + team.money)
                self.dbsession.add(team)
            self.dbsession.commit()
            self.event_manager.admin_score_update(team, message, value)
            self.redirect("/admin/managetask")
        except ValidationError as error:
            self.render("admin/view/managetask.html", errors=[str(error)])



# new class for admin upload 
class AdminFileDownloadHandler(BaseHandler):

    """Download shared files from here"""

    @authenticated
    def get(self, *args, **kwargs):
        if options.team_sharing:
            """Get a file and send it to the user"""
            user = self.get_current_user()
            shared_file = FileUpload.by_uuid(self.get_argument("uuid", ""))
            if user.is_admin() or (
                shared_file is not None and shared_file in user.team.files
            ):
                self.set_header("Content-Type", shared_file.content_type)
                self.set_header("Content-Length", shared_file.byte_size)
                self.set_header(
                    "Content-Disposition",
                    "attachment; filename=%s" % (shared_file.file_name),
                )
                self.write(shared_file.data)
            else:
                self.render("public/404.html")
        else:
            self.redirect("/404")


class AdminFileDeleteHandler(BaseHandler):

    """Delete shared files"""

    @authenticated
    def post(self, *args, **kwargs):
        if options.team_sharing:
            user = self.get_current_user()
            shared_file = FileUpload.by_uuid(self.get_argument("uuid", ""))
            if user.is_admin():
                logging.info(
                    "%s deleted a shared file %s" % (user.handle, shared_file.uuid)
                )
                shared_file.delete_data()
                self.dbsession.delete(shared_file)
                self.dbsession.commit()
                self.redirect("/admin/managetask")
            elif shared_file is not None and shared_file in user.team.files:
                logging.info(
                    "%s deleted a shared file %s" % (user.handle, shared_file.uuid)
                )
                shared_file.delete_data()
                self.dbsession.delete(shared_file)
                self.dbsession.commit()
                self.redirect("/user/share/files")
            else:
                self.redirect("/404")
        else:
            self.redirect("/404")
######33333 added new classes for admin uploads page above

class AdminAjaxUserManagetasksHandler(BaseHandler):
    @restrict_ip_address
    @authenticated
    @authorized(ADMIN_PERMISSION)
    def post(self, *args, **kwargs):
        uri = {"user": self.user_details, "team": self.team_details}
        if len(args) and args[0] in uri:
            uri[args[0]]()

    def team_details(self):
        # print(self.get_argument('uuid', ''))
        team = Team.by_uuid(self.get_argument("uuid", ""))
        if team is not None:
            self.write(team.to_dict())
        else:
            self.write({})

    def user_details(self):
        user = User.by_uuid(self.get_argument("uuid", ""))
        # print(user)
        if user is not None:
            self.write(user.to_dict())
        else:
            self.write({})
