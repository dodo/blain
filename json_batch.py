###############################################################################
##
## digger - Digging into some data mines
## Copyright (C) 2010  Thammi
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
###############################################################################

from warnings import warn
import os.path

from json_hack import json

def change_batch(change, file_name):
    if os.path.exists(file_name):
        # read in old data
        try:
            inp = file(file_name)
            batch = json.load(inp)
            inp.close()
        except:
            warn("Couldn't load old data")
            batch = {}
    else:
        batch = {}

    # apply changes
    change(batch)

    # writing back
    out = file(file_name, 'w')
    json.dump(batch, out)
    out.close()

def update_batch(update, file_name):
    change_batch(lambda batch: batch.update(update), file_name)

def save_batch(item, data, file_name):
    def save(batch):
        batch[item] = data

    change_batch(save, file_name)

def load_batch(file_name):
    inp = file(file_name)
    data = json.load(inp)
    inp.close()
    return data

