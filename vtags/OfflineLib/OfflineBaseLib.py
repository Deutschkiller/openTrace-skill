"""
http://www.vim.org/scripts/script.php?script_id=5494
"""
#===============================================================================
# BSD 2-Clause License

# Copyright (c) 2016, CaoJun
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

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
#===============================================================================

import os
import sys
import re
import pickle
import inspect
import copy

#-------------------------------------------------------------------------------
# import base libary
#-------------------------------------------------------------------------------
import Lib.GLB as GLB
G = GLB.G
from Lib.BaseLib import *
import Lib.CodeLib as CodeLib
import Lib.FileInfLib as FileInfLib
import InlineLib.WinLib as WinLib

#-------------------------------------------------------------------------------
# function get for user
#-------------------------------------------------------------------------------
# this function used to open module and go to some lines
def mopen(module_name):
    cur_module_inf  = FileInfLib.get_module_inf(module_name)
    if not cur_module_inf:
        print('Error: module %s not found! \n'%(module_name))
        return False
    file_path = cur_module_inf['file_path']
    if not os.path.isfile(file_path):
        print('Error: module file %s not exist! \n'%(file_path))
        return False
    WinLib.open_file_separately(file_path, cur_module_inf['module_name_sr']['range'][0])

def get_module_filelist(module_name):
    def rec_gen_module_filelist(module_name, trace_file):
        cur_module_inf  = FileInfLib.get_module_inf(module_name)
        if not cur_module_inf:
            print('Warning: module %s not found! \n'%(module_name))
            return
        cur_module_path = cur_module_inf['file_path']
        if (module_name, cur_module_path) in trace_file:
            return
        trace_file.add( (module_name, cur_module_path) )
        inst_inf_list = cur_module_inf['inst_inf_list']
        if not inst_inf_list:
            return
        for inst_inf in inst_inf_list:
            submodule_name =  inst_inf['submodule_name_sr']['str']
            rec_gen_module_filelist(submodule_name, trace_file)
    # if no data base return []
    if not G['OfflineActive']:
        return []
    trace_file = set()
    rec_gen_module_filelist(module_name, trace_file)

    return list( set( [ name_file[1] for name_file in trace_file ] ) )





