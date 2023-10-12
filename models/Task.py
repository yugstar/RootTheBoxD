# -*- coding: utf-8 -*-
"""
Created on Mar 12, 2012

@author: moloch

    Copyright 2012 Root the Box

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
# pylint: disable=no-member


import xml.etree.cElementTree as ET

import os
import imghdr
import io

from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, desc
from sqlalchemy.orm import relationship, backref
from sqlalchemy.types import Integer, Unicode, String, Boolean
from models import dbsession
from models.BaseModels import DatabaseObject
from models.User import User
from models.GameHistory import GameHistory
# from models.Relationships import (
#     team_to_box,
#     team_to_item,
#     team_to_flag,
#     team_to_game_level,
#     team_to_source_code,
#     team_to_hint,
# )
from libs.BotManager import BotManager
from libs.XSSImageCheck import is_xss_image, get_new_avatar
from libs.XSSImageCheck import MAX_AVATAR_SIZE, MIN_AVATAR_SIZE, IMG_FORMATS
from libs.ValidationError import ValidationError
from tornado.options import options
from PIL import Image
from resizeimage import resizeimage
from random import randint
from libs.StringCoding import encode
from builtins import str


class Task(DatabaseObject):

    """Task definition"""

    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    _name = Column(Unicode(24), unique=True, nullable=False)
    _description = Column(Unicode(512))
    _locked = Column(Boolean, default=False, nullable=False)
    _avatar = Column(String(64))

    # files = relationship(
    #     "FileUpload",
    #     backref=backref("task", lazy="select"),
    #     cascade="all,delete,delete-orphan",
    # )
    # pastes = relationship(
    #     "PasteBin",
    #     backref=backref("task", lazy="select"),
    #     cascade="all,delete,delete-orphan",
    # )

    # members = relationship(
    #     "User",
    #     backref=backref("task", lazy="select"),
    #     cascade="all,delete,delete-orphan",
    # )

    # flags = relationship(
    #     "Flag", secondary=task_to_flag, backref=backref("task", lazy="select")
    # )

    # boxes = relationship(
    #     "Box", secondary=task_to_box, back_populates="task", lazy="select"
    # )

    # items = relationship(
    #     "MarketItem", secondary=task_to_item, backref=backref("task", lazy="joined")
    # )

    # purchased_source_code = relationship(
    #     "SourceCode",
    #     secondary=team_to_source_code,
    #     backref=backref("team", lazy="select"),
    # )

    # hints = relationship(
    #     "Hint", secondary=team_to_hint, backref=backref("team", lazy="select")
    # )

    # game_levels = relationship(
    #     "GameLevel", secondary=team_to_game_level, back_populates="teams", lazy="select"
    # )

    # game_history = relationship(
    #     "GameHistory",
    #     backref=backref("team", lazy="select"),
    #     cascade="all,delete,delete-orphan",
    # )

    @classmethod
    def all(cls):
        """Returns a list of all objects in the database"""
        return dbsession.query(cls).all()

    @classmethod
    def by_id(cls, _id):
        """Returns a the object with id of _id"""
        return dbsession.query(cls).filter_by(id=_id).first()

    @classmethod
    def by_uuid(cls, _uuid):
        """Return and object based on a uuid"""
        return dbsession.query(cls).filter_by(uuid=_uuid).first()

    @classmethod
    def by_name(cls, name):
        """Return the team object based on "team_name" """
        return dbsession.query(cls).filter_by(_name=str(name)).first()

    @property
    def description(self):
        if self._description is None:
            return ""
        return self._description

    @description.setter
    def description(self, value):
        if 512 < len(value):
            raise ValidationError("Description cannot be greater than 512 characters")
        self._description = str(value)

    @property
    def locked(self):
        """Determines if an admin has locked an corp."""
        if self._locked == None:
            return False
        return self._locked

    @locked.setter
    def locked(self, value):
        """Setter method for _lock"""
        if value is None:
            value = False
        elif isinstance(value, int):
            value = value == 1
        elif isinstance(value, str):
            value = value.lower() in ["true", "1"]
        assert isinstance(value, bool)
        self._locked = value

    @classmethod
    def count(cls):
        return dbsession.query(cls).count()

    @property
    def name(self):
        return self._name


    def set_bot(self, botcount):
        bot_update = GameHistory(type="bot_count", value=botcount)
        self.game_history.append(bot_update)

    def add_flag(self, flag):
        self.flags.append(flag)
        add_flag = GameHistory(type="flag_count", value=len(self.flags))
        self.game_history.append(add_flag)

    def get_history(self, _type=None):
        history = []
        for item in self.game_history:
            if _type == "bots":
                if item.type == "bot_count":
                    history.append(item.to_dict())
            elif _type == "flags":
                if item.type == "flag_count":
                    history.append(item.to_dict())
            elif item.type != "flag_count" and item.type != "bot_count":
                history.append(item.to_dict())
        return history

    @name.setter
    def name(self, value):
        if not 3 <= len(value) <= 24:
            raise ValidationError("Team name must be 3 - 24 characters")
        else:
            self._name = str(value)




    # @property
    # def locked(self):
    #     # Hides team from scoreboard if all users are locked or no users
    #     if len(self.members) > 0:
    #         for user in self.members:
    #             if not user.locked:
    #                 return False
    #     return True

    @property
    def avatar(self):
        if self._avatar is not None:
            return self._avatar
        else:
            if options.teams:
                avatar = get_new_avatar("team")
            else:
                avatar = get_new_avatar("user", True)
            if not avatar.startswith("default_"):
                self._avatar = avatar
                dbsession.add(self)
                dbsession.commit()
            return avatar

    @avatar.setter
    def avatar(self, image_data):
        if MIN_AVATAR_SIZE < len(image_data) < MAX_AVATAR_SIZE:
            ext = imghdr.what("", h=image_data)
            if ext in IMG_FORMATS and not is_xss_image(image_data):
                try:
                    if self._avatar is not None and os.path.exists(
                        options.avatar_dir + "/upload/" + self._avatar
                    ):
                        os.unlink(options.avatar_dir + "/upload/" + self._avatar)
                    file_path = str(
                        options.avatar_dir + "/upload/" + self.uuid + "." + ext
                    )
                    image = Image.open(io.BytesIO(image_data))
                    cover = resizeimage.resize_cover(image, [500, 250])
                    cover.save(file_path, image.format)
                    self._avatar = "upload/" + self.uuid + "." + ext
                except Exception as e:
                    raise ValidationError(e)

            else:
                raise ValidationError(
                    "Invalid image format, avatar must be: %s"
                    % (", ".join(IMG_FORMATS))
                )
        else:
            raise ValidationError(
                "The image is too large must be %d - %d bytes"
                % (MIN_AVATAR_SIZE, MAX_AVATAR_SIZE)
            )

    @property
    def levels(self):
        """Sorted game_levels"""
        return sorted(self.game_levels)

    def last_scored(self):
        for item in reversed(self.game_history):
            if item.type == "flag_count":
                return item.created.strftime("%s")
        return datetime.now().strftime("%s")

    def level_flags(self, lvl):
        """Given a level number return all flags captured for that level"""
        return [flag for flag in self.flags if flag.game_level.number == lvl]

    def box_flags(self, box):
        """Given a box return all flags captured for that box"""
        return [flag for flag in self.flags if flag.box == box]

    @property
    def bot_count(self):
        bot_manager = BotManager.instance()
        return bot_manager.count_by_team_uuid(self.uuid)

    def file_by_file_name(self, file_name):
        """Return file object based on file_name"""
        ls = self.files.filter_by(file_name=file_name)
        return ls[0] if 0 < len(ls) else None

    def to_dict(self):
        """Use for JSON related tasks; return public data only"""
        return {
            "uuid": self.uuid,
            "name": self.name,
            "avatar": self.avatar,
            "description": self.description,
        }

    def to_xml(self, parent):
        team_elem = ET.SubElement(parent, "task")
        ET.SubElement(team_elem, "name").text = self.name
        ET.SubElement(corp_elem, "description").text = self.description
        ET.SubElement(corp_elem, "locked").text = str(self.locked)
        users_elem = ET.SubElement(team_elem, "users")
        users_elem.set("count", "%s" % str(len(self.members)))
        for user in self.members:
            user.to_xml(users_elem)


    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

