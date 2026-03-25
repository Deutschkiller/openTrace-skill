"""
http://www.vim.org/scripts/script.php?script_id=5494
"""
# ===============================================================================
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
# ===============================================================================

import os
import sys
import re
import pickle
import inspect

# -------------------------------------------------------------------------------
# import base libary
# -------------------------------------------------------------------------------
from Lib.BaseLib import *
import Lib.CodeLib as CodeLib
import Lib.FileInfLib as FileInfLib
import OfflineLib.OfflineBaseLib as OfflineBaseLib

# all function inf
custom_function_inf = {}


# offline_func_help
def offline_func_help(Print=False):
    help_str_list = []
    help_str_list.append("supported offline functions: ")
    help_str_list += show_func_help()
    help_str_list.append("offline call exp: ")
    help_str_list.append(
        "    \"vtags 'list( my_cpu )'\" # used to list all support function! "
    )
    help_str_list.append(
        "    \"vtags -db ~/design/vtags_db 'mtopo( my_cpu )'\" # used specified vtags.db to get module topo!"
    )
    if Print:
        for l in help_str_list:
            print(l)
    return help_str_list


# used for vtags to call functions
def function_run(parm_str):
    # 1 : use '-db xxx' set vtags.db path
    db_path_search = re.search("-db\s+(?P<path>\S+)", parm_str)
    if db_path_search:
        db_path = db_path_search.group("path")
        if os.path.isdir(db_path):
            GLB.set_vtags_db_path(db_path)
        else:
            print("Error: -db must follow a valid vtags_db dir path !")
            return False
    # 2 : decode function and parm list
    func_name = ""
    parm_list = []
    match_func = re.search("(?P<f_name>\w+)\s*\((?P<parms>.*)\)", parm_str.strip())
    if match_func:
        func_name = match_func.group("f_name")
        parm_list = [p.strip() for p in match_func.group("parms").split(",")]
    else:
        print("Error: func not define ! only support :")
        MountPrintLines(offline_func_help(), label="Offline Function Help", Print=True)
        return False
    # 3 : list()
    if func_name == "list":
        MountPrintLines(offline_func_help(), label="Offline Function Help", Print=True)
        return True
    # 4 : do register function
    if check_call_func_valid(func_name, parm_list):
        return real_call_custom_function(func_name, parm_list)
    return False


# used for register a function to all function
def register_function(function_class, description=""):
    if not (inspect.isfunction(function_class) and type(description) == str):
        print(
            'Error: unsupport parameters for "register_function(function_class, description_string)"'
        )
        return
    function_name = function_class.__name__
    if function_name in custom_function_inf:
        func = custom_function_inf[func_name]
        func_define = "%s(%s) : %s"(
            func_name, ", ".join(inspect.getargspec(func).args), func.description
        )
        print('func:"%s" already registered ! %s' % (function_name, func_define))
        return
    function_class.description = description
    custom_function_inf[function_name] = function_class
    return


# used to show all support function with key in name
def show_func_help(key="", Print=False):
    func_str_list = []
    func_name_list = list(custom_function_inf)
    if key:
        assert type(key) == str, "only support str parms!"
        func_name_list = [fn for fn in func_name_list if fn.find(key) != -1]
    func_name_list.sort()
    for func_name in func_name_list:
        func = custom_function_inf[func_name]
        func_define = "    %s( %s )    # %s" % (
            func_name,
            ", ".join(inspect.getargspec(func).args),
            func.description,
        )
        func_str_list.append(func_define)
    if Print:
        for l in func_str_list:
            print(l)
    return func_str_list


# decode the input call string to function and parms
def decode_call_string(call_string):
    match_func = re.match("(?P<name>\w+)\s*\((?P<parms>.*)\)\s*$", call_string.strip())
    if not match_func:
        print(
            'Error: %s not a valid function call format ! valid call is like "function_name( parm0, parm1, ...)".'
            % (call_string)
        )
        return None, []
    function_name = match_func.group("name")
    parm_list = [p.strip() for p in (match_func.group("parms")).split(",") if p.strip()]
    return function_name, parm_list


# check input parm is valid for some function
def check_call_func_valid(function_name, parm_list):
    if function_name not in custom_function_inf:
        print('Error: func: "%s" not exist ! ' % (function_name))
        return False
    func = custom_function_inf[function_name]
    arg_num = len(inspect.getargspec(func).args)
    arg_has_default = 0
    if inspect.getargspec(func).defaults:
        arg_has_default = len(inspect.getargspec(func).defaults)
    if len(parm_list) >= (arg_num - arg_has_default) and len(parm_list) <= arg_num:
        return True
    print(
        "Error: input parameters number not match function define! input:%d, need:[%s-%s]"
        % (len(parm_list), arg_num - arg_has_default, arg_num)
    )
    return False


# real call custom function
def real_call_custom_function(function_name, parm_list):
    # the max number of custom function is 10
    if len(parm_list) == 0:
        return custom_function_inf[function_name]()
    elif len(parm_list) == 1:
        return custom_function_inf[function_name](parm_list[0])
    elif len(parm_list) == 2:
        return custom_function_inf[function_name](parm_list[0], parm_list[1])
    elif len(parm_list) == 3:
        return custom_function_inf[function_name](
            parm_list[0], parm_list[1], parm_list[2]
        )
    elif len(parm_list) == 4:
        return custom_function_inf[function_name](
            parm_list[0], parm_list[1], parm_list[2], parm_list[3]
        )
    elif len(parm_list) == 5:
        return custom_function_inf[function_name](
            parm_list[0], parm_list[1], parm_list[2], parm_list[3], parm_list[4]
        )
    elif len(parm_list) == 6:
        return custom_function_inf[function_name](
            parm_list[0],
            parm_list[1],
            parm_list[2],
            parm_list[3],
            parm_list[4],
            parm_list[5],
        )
    elif len(parm_list) == 7:
        return custom_function_inf[function_name](
            parm_list[0],
            parm_list[1],
            parm_list[2],
            parm_list[3],
            parm_list[4],
            parm_list[5],
            parm_list[6],
        )
    elif len(parm_list) == 8:
        return custom_function_inf[function_name](
            parm_list[0],
            parm_list[1],
            parm_list[2],
            parm_list[3],
            parm_list[4],
            parm_list[5],
            parm_list[6],
            parm_list[7],
        )
    elif len(parm_list) == 9:
        return custom_function_inf[function_name](
            parm_list[0],
            parm_list[1],
            parm_list[2],
            parm_list[3],
            parm_list[4],
            parm_list[5],
            parm_list[6],
            parm_list[7],
            parm_list[8],
        )
    elif len(parm_list) == 10:
        return custom_function_inf[function_name](
            parm_list[0],
            parm_list[1],
            parm_list[2],
            parm_list[3],
            parm_list[4],
            parm_list[5],
            parm_list[6],
            parm_list[7],
            parm_list[8],
            parm_list[9],
        )
    else:
        print(
            'Error: current custom func max support 10 parameters, "%d" give!'
            % (len(parm_list))
        )
    return False


# --------------------------------------------------------------------------------
# custom function
# --------------------------------------------------------------------------------
# this function print module and all submodule's filelist
def mfilelist(module_name):
    if not G["OfflineActive"]:
        print("Error: no vtags.db found !")
        return
    filelist = OfflineBaseLib.get_module_filelist(module_name)
    filelist.sort()
    for file_path in filelist:
        print(file_path)
    print("")


# this function get input module's instance trace
# user define parameter:
#    to_module   : trace finish to this module
def mtrace(to_module):
    full_traces = []
    FileInfLib.recursion_get_module_trace(to_module, [], full_traces)
    print_strs = []
    for i, r_trace in enumerate(full_traces):
        trace = r_trace[::-1]
        father_inst_chain = trace[0]
        for father_inst in trace[1:]:
            father, inst = father_inst.split(".")
            father_inst_chain += "(%s).%s" % (father, inst)
        father_inst_chain += "(%s)" % (to_module)
        print_strs.append("%d : %s" % (i, father_inst_chain))
    MountPrintLines(print_strs, label="Module Trace", Print=True)


# this function show module's topology
def mtopo(module_name, depth=None, mask=0, space=None):
    # valid when has vtags.db
    if not G["OfflineActive"]:
        print("Error: no vtags.db found !")
        return
    if depth == None:
        print("Note: not set depth default == 1 !")
        depth = 1
    else:
        depth = int(depth)
    mask = int(mask)
    if not space:
        space = "    "

    def rec_print_module_topo(module_name, instance_name, cur_depth):
        if instance_name:
            print("%s%s(%s)" % (space * cur_depth, instance_name, module_name))
        else:
            print("%s%s:" % (space * cur_depth, module_name))
        if (cur_depth + 1 > depth) and (depth != 0):
            return
        tmp_module_inf = FileInfLib.get_module_inf(module_name)
        # for the submodule set the masked module, and instance times
        mask_module_set = set()
        if mask != 0:
            mask_module_set |= G["BaseModuleInf"]["BaseModules"]
        instance_times_count = {}
        module_instance_pair = []
        for inst_inf in tmp_module_inf["inst_inf_list"]:
            submodule_name = inst_inf["submodule_name_sr"]["str"]
            instance_name = inst_inf["inst_name_sr"]["str"]
            module_instance_pair.append((submodule_name, instance_name))
            instance_times_count.setdefault(submodule_name, 0)
            instance_times_count[submodule_name] += 1
            if instance_times_count[submodule_name] >= mask and mask != 0:
                mask_module_set.add(submodule_name)
        # sep masked and unmasked module
        unmask_pairs = []
        masked_module = set()
        for module, instance in module_instance_pair:
            if module in mask_module_set:
                masked_module.add(module)
            else:
                unmask_pairs.append((module, instance))
        # first print unmask topo
        for module, instance in unmask_pairs:
            rec_print_module_topo(module, instance, cur_depth + 1)
        # then for the masked module
        if masked_module:
            print("%s------------" % (space * (cur_depth + 1)))
        for module in masked_module:
            print(
                "%s%s(%d)"
                % (space * (cur_depth + 1), module, instance_times_count[module])
            )

    rec_print_module_topo(module_name, "", 0)


# -------------------------------------------------------------------------------
# register vtags -func function
# -------------------------------------------------------------------------------
register_function(mtrace, description="this function get input module's instance trace")
register_function(
    mfilelist, description="this function print module and all submodule's filelist"
)
register_function(mtopo, description="this function print module topology!")
register_function(
    OfflineBaseLib.mopen,
    description="this function used to open module and go to some lines",
)
