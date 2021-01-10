#!/usr/bin/env python3
# encoding: utf-8

# This is a technical demo and teaching example for the turberfield-catchphrase library.
# Copyright (C) 2021 D. Haynes

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from collections import defaultdict

from turberfield.dialogue.model import SceneScript

from tas.tea import Motivation
from tas.tea import Location
from tas.tea import TeaTime
from tas.types import Character


class TeaAndSympathy(TeaTime):

    @property
    def folder(self):
        return SceneScript.Folder(
            pkg="tas.dlg",
            description="Tea and Sympathy",
            metadata={},
            paths=["early.rst", "kettle.rst", "made.rst", "pause.rst", "quit.rst"],
            interludes=None
        )

    def build(self):
        yield from super().build()
        yield from [
            Character(names=["Sophie"]).set_state(Motivation.acting),
            Character(names=["Louise"]).set_state(Motivation.player),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = defaultdict(bool)
        self.active.add(self.do_quit)

    def __call__(self, fn, *args, **kwargs):
        lines = list(super().__call__(fn, *args, **kwargs))
        if any(self.refusal in i for i in lines):
            yield from self.do_refuse(self.do_refuse, self.input_text, **kwargs)
        else:
            yield from lines
        try:
            mugs = [i for i in self.lookup["mug"] if i.get_state(Location) == Location.counter]
            contents = [i.contents(self.ensemble) for i in mugs]
            self.outcomes["brewed"] = self.outcomes["brewed"] or any(i for i in self.lookup["tea"] if i.state == 100)
            self.outcomes["untidy"] = any(i for c in contents for i in c if "tea" in getattr(i, "names", []))
            self.outcomes["stingy"] = not any(i for c in contents for i in c if "milk" in getattr(i, "names", []))
            self.outcomes["sugary"] = any(i for c in contents for i in c if "sugar" in getattr(i, "names", []))
            self.outcomes["served"] = (
                self.outcomes["brewed"] and not self.outcomes["untidy"] and not self.outcomes["stingy"]
            )
            self.outcomes["finish"] = all(
                i.get_state(Motivation) == Motivation.paused
                for i in self.ensemble if isinstance(i, Character)
            )
            self.outcomes["paused"] = (
                any(i.get_state(Motivation) == Motivation.paused
                for i in self.ensemble if isinstance(i, Character))
                and not self.outcomes["finish"]
            )
        except StopIteration:
            pass

    def do_help(self, this, text, /, **kwargs):
        """
        help | ?

        """
        for i in self.ensemble:
            if isinstance(i, Character) and i.get_state(Motivation) != Motivation.player:
                i.state = Motivation.paused

        yield "**Help**"
        yield "You are woken early one Sunday morning."
        yield "Your flatmate is up and anxious."
        yield "Maybe you could make her a cup of tea."
        yield from super().do_help(this, text)
        yield "Start with *look around*."
        yield "The character dialogue may give you some hints."
        yield "To see how things are coming along, use the *check* command."

    def do_refuse(self, this, text, /, **kwargs):
        """
        refuse

        """
        self.prompt = "If you're stuck, try 'help' or 'history'."
        for i in self.ensemble:
            if isinstance(i, Character) and i.get_state(Motivation) != Motivation.player:
                i.state = Motivation.paused

        yield text
        yield self.refusal

    def do_quit(self, this, text, /, **kwargs):
        """
        exit | finish | stop | quit

        """
        for i in self.ensemble:
            if isinstance(i, Character):
                i.state = Motivation.paused
        yield ""
