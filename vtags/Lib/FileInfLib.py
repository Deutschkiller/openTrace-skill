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

import sys
import re
import os
import re
import Lib.GLB as GLB
G = GLB.G
from Lib.BaseLib import *
import Parser.Parser as Parser
from InlineLib.ViewLib import *

def line_num_r2l( path, real_i, code_inf_list ):
    if len(code_inf_list) == 1:
        return real_i;
    for code_inf in code_inf_list:
        if (path == code_inf['file_path']) and \
           (code_inf['real_line_range'][0] <= real_i) and \
           (code_inf['real_line_range'][1] == -1 or code_inf['real_line_range'][1] >= real_i ):
           return code_inf['logic_line_range'][0] - code_inf['real_line_range'][0] + real_i
    return -1

def location_r2l( real_path, real_pos, code_inf_list ):
    for code_inf in code_inf_list:
        if (real_path == code_inf['file_path']) and \
           (code_inf['real_line_range'][0] <= real_pos[0]) and \
           (code_inf['real_line_range'][1] == -1 or code_inf['real_line_range'][1] >= real_pos[0]):
           logic_line = code_inf['logic_line_range'][0] - code_inf['real_line_range'][0] + real_pos[0]
           return {"pos" : (logic_line, real_pos[1]), "path": code_inf_list[0]['file_path']}
    return {}

def location_l2r(logic_pos, code_inf_list):
    for code_inf in code_inf_list:
        if (code_inf['logic_line_range'][0] <= logic_pos[0]) and \
           (code_inf['logic_line_range'][1] == -1 or code_inf['logic_line_range'][1] >= logic_pos[0]):
            real_line = logic_pos[0] - (code_inf['logic_line_range'][0] - code_inf['real_line_range'][0])
            return { "pos" : (real_line, logic_pos[1]) , "path": code_inf['file_path'] }
    return {}

def get_module_inf_from_pos(real_path, real_pos, logic_pos = [0,0]):
    file_module_inf = {"file_inf": None, "module_inf": None}
    # first get the logic file path
    logic_path = real_path
    if real_path in G['InLineIncFile2LogicFileDic']:
        logic_path = G['InLineIncFile2LogicFileDic'][real_path]
    # get code inf to get the logic pos
    file_inf = loading_file_inf(logic_path)
    if not file_inf:
        PrintDebug('Trace: get_module_inf_from_pos: logic_path=%s, real_path=%s has no file database !'%(logic_path, real_path) )
        return file_module_inf
    file_module_inf["file_inf"] = file_inf
    # get logic path and pos, all module inf use logic encode
    logic_loction = location_r2l(real_path, real_pos, file_inf['code_inf_list'])
    if not logic_loction:
        PrintDebug('Trace: get_module_inf_from_pos: real_path=%s, real_pos=%s no logic location code_inf_list = %s !'%(real_path, real_pos, file_inf['code_inf_list']) )
        return file_module_inf
    assert(G['InLineFileInfDic'][logic_path]["file_state"]['last_modify_time'] == get_sec_mtime(logic_path))
    assert( logic_path == logic_loction['path'] )
    logic_pos[0] = logic_loction['pos'][0]
    logic_pos[1] = logic_loction['pos'][1]
    # first get current line module inf
    for module_inf in file_inf['module_inf_list']:
        cur_module_line_range = module_inf['module_line_range']
        if cur_module_line_range[1] < logic_pos[0]:
            continue
        if logic_pos[0] < cur_module_line_range[0]:
            break
        pos_module_inf = get_module_inf( module_inf["module_name_sr"]['str'] )
        assert( pos_module_inf )
        file_module_inf["module_inf"] = pos_module_inf
        return file_module_inf
    return file_module_inf

def get_module_io_inf_from_pos(path, pos, logic_pos = [0,0]):
    result = get_module_inf_from_pos(path, pos, logic_pos)
    result["io_inf"] = None
    if not result['module_inf']:
        return result
    io_inf_list = result['module_inf']['io_inf_list']
    for idx, io_inf in enumerate( io_inf_list ):
        cur_io_range = io_inf['name_sr']["range"]
        # check line
        if cur_io_range[2] < logic_pos[0]:
            continue
        if logic_pos[0] < cur_io_range[0]:
            break
        # check calum
        if cur_io_range[3] < logic_pos[1]:
            continue
        if logic_pos[1] < cur_io_range[1]:
            break
        result["io_inf"]        = copy.copy(io_inf)
        result["io_inf"]['idx'] = idx
        return result
    return result

def get_module_inst_inf_from_pos(path, pos, logic_pos = [0,0]):
    result = get_module_inf_from_pos(path, pos, logic_pos)
    result["inst_inf"] = None
    if not result['module_inf']:
        return result
    for inst_inf in result['module_inf']['inst_inf_list']:
        cur_inst_line_range = inst_inf['inst_line_range']
        if cur_inst_line_range[1] < logic_pos[0]:
            continue
        if logic_pos[0] < cur_inst_line_range[0]:
            break
        result["inst_inf"] = inst_inf
        return result
    return result

def get_module_inst_cnt_sub_inf_from_pos(path, pos, logic_pos = [0,0]):
    result = get_module_inst_inf_from_pos(path, pos, logic_pos)
    result["cnt_sub_inf"] = None
    if not result["inst_inf"]:
        return result
    # check parm
    pos_cnt_inf = None
    pos_cnt_idx = 0
    for pos_cnt_idx, cnt_inf in enumerate( result["inst_inf"]["parm_cnt_inf_list"] ):
        cur_cnt_range = list( cnt_inf['cnt_name_range'] )
        if cnt_inf["sub_name_sr"]:
            cur_cnt_range[0] = cnt_inf["sub_name_sr"]["range"][0]
            cur_cnt_range[1] = cnt_inf["sub_name_sr"]["range"][1]
        # check line
        if cur_cnt_range[2] < logic_pos[0]:
            continue
        if logic_pos[0] < cur_cnt_range[0]:
            break
        # check calum
        if cur_cnt_range[3] < logic_pos[1]:
            continue
        if logic_pos[1] < cur_cnt_range[1]:
            break
        pos_cnt_inf         = copy.copy( cnt_inf )
        pos_cnt_inf['type'] = 'parmcnt'
    if not pos_cnt_inf:
        # check io
        for pos_cnt_idx, cnt_inf in enumerate(result["inst_inf"]["iocnt_inf_list"]):
            cur_cnt_range = list( cnt_inf['cnt_name_range'] )
            if cnt_inf["sub_name_sr"]:
                cur_cnt_range[0] = cnt_inf["sub_name_sr"]["range"][0]
                cur_cnt_range[1] = cnt_inf["sub_name_sr"]["range"][1]
            # check line
            if cur_cnt_range[2] < logic_pos[0]:
                continue
            if logic_pos[0] < cur_cnt_range[0]:
                break
            # check calum
            if cur_cnt_range[3] < logic_pos[1]:
                continue
            if logic_pos[1] < cur_cnt_range[1]:
                break
            pos_cnt_inf         = copy.copy( cnt_inf ) # incase influence offline inf
            pos_cnt_inf['type'] = 'iocnt'
            break
    if not pos_cnt_inf:
        return result
    # PrintDebug("^_^ 11:%d %s %s\n iocnt_inf_list = %s"%( pos_cnt_idx, logic_pos, pos_cnt_inf, result["inst_inf"]["iocnt_inf_list"] ))
    # try get submodule cnt inf
    submodule_name = result["inst_inf"]["submodule_name_sr"]['str']
    submodule_inf  = get_module_inf(submodule_name)
    if not submodule_inf:
        return result
    if pos_cnt_inf["type"] == "parmcnt":
        # get sub inf from name
        if pos_cnt_inf["sub_name_sr"]:
            if "parm_name_to_parm_sr_dic" not in submodule_inf:
                parm_name_to_parm_sr_dic = {}
                for parm_sr in submodule_inf["parm_inf_list"]:
                    parm_name_to_parm_sr_dic[ parm_sr['str'] ] = parm_sr
                submodule_inf['parm_name_to_parm_sr_dic'] = parm_name_to_parm_sr_dic
            if pos_cnt_inf["sub_name_sr"]['str'] not in submodule_inf['parm_name_to_parm_sr_dic']:
                PrintReport("Warning: Inst cnt at %s, Param: '%s' not found in submodule %s !"%(pos_cnt_inf['cnt_name_range'], pos_cnt_inf["sub_name_sr"]['str'], submodule_inf["module_name_sr"]["str"]))
                return result
            sub_inf = { "name_sr" : submodule_inf['parm_name_to_parm_sr_dic'][ pos_cnt_inf["sub_name_sr"]['str'] ], "type": 'parm' }
        else: # use idx find io_inf
            parm_inf_list = submodule_inf["parm_inf_list"]
            if len(parm_inf_list) < pos_cnt_idx:
                PrintReport("Warning: Inst cnt at %s not found in submodule %s !"%(pos_cnt_inf['cnt_name_range'], submodule_inf["module_name_sr"]["str"]))
                return result
            # get name from pos
            sub_inf = { "name_sr": parm_inf_list[pos_cnt_idx], "type": 'parm' }
    else: # io cnt
        assert( pos_cnt_inf["type"] == 'iocnt' )
        # get sub inf from name
        if pos_cnt_inf["sub_name_sr"]:
            if "io_name_to_io_inf_dic" not in submodule_inf:
                io_name_to_io_inf_dic = {}
                for io_inf in submodule_inf["io_inf_list"]:
                    io_name_to_io_inf_dic[ io_inf["name_sr"]['str'] ] = io_inf
                submodule_inf['io_name_to_io_inf_dic'] = io_name_to_io_inf_dic
            if pos_cnt_inf["sub_name_sr"]['str'] not in submodule_inf['io_name_to_io_inf_dic']:
                PrintReport("Warning: Inst cnt at %s, IO: '%s' not found in submodule %s !"%(pos_cnt_inf['cnt_name_range'], pos_cnt_inf["sub_name_sr"]['str'], submodule_inf["module_name_sr"]["str"]))
                return result
            sub_inf = copy.copy( submodule_inf['io_name_to_io_inf_dic'][ pos_cnt_inf["sub_name_sr"]['str'] ] )
        else: # use idx find io_inf
            sub_io_list = submodule_inf["io_inf_list"]
            if len(sub_io_list) < pos_cnt_idx:
                PrintReport("Warning: Inst cnt at %s not found in submodule %s !"%(pos_cnt_inf['cnt_name_range'], submodule_inf["module_name_sr"]["str"]))
                return result
            # get name from pos
            sub_inf = copy.copy( sub_io_list[pos_cnt_idx] )
        # if sub io inf add other inf
    sub_inf["file_path"]      = submodule_inf["file_path"]
    sub_inf["module_name_sr"] = submodule_inf["module_name_sr"]
    sub_inf["module_inf"]     = submodule_inf
    result["cnt_sub_inf"]     = sub_inf
    return result

# use this function to get the module inf from module name
def get_module_inf(module_name, report_level = 1):
    def get_module_inf_from_module_inf_dic(module_name):
        # if module already load in
        if module_name in G['InLineModuleInfDic']:
            module_inf = G['InLineModuleInfDic'][module_name]
            # check inf fresh
            if check_inf_valid(module_inf['file_path'], module_inf['last_modify_time']):
                return module_inf
            # inf stale delate it
            del G['InLineModuleInfDic'][module_name]
        return {}
    def get_module_inf_from_file_inf(module_name):
        onload_G_OffLineModulePathDic()
        if module_name in G['OffLineModulePathDic']:
            file_path = G['OffLineModulePathDic'][module_name]
            loading_file_inf(file_path)
        return get_module_inf_from_module_inf_dic(module_name)
    def get_module_inf_after_refresh_database(module_name):
        if not G['RefreshDBValid']:
            return {}
        update_offline_file_db()
        return get_module_inf_from_file_inf(module_name)
    # new inf at module inf dic
    module_inf = get_module_inf_from_module_inf_dic(module_name)
    # no valid module inf in G['InLineModuleInfDic'] load it from file int
    if not module_inf:
        module_inf = get_module_inf_from_file_inf(module_name)
    # not found module inf at file inf, need update data base
    if not module_inf:
        module_inf = get_module_inf_after_refresh_database(module_name)
    # add inc file to logic file dic, all vtags base on module_inf so this
    # will trace newest include file path
    if module_inf:
        module_logic_path = module_inf['file_path']
        for code_inf in module_inf["code_inf_list"]:
            m_file_path = code_inf['file_path']
            if m_file_path == module_logic_path:
                continue
            G['InLineIncFile2LogicFileDic'][m_file_path] = module_logic_path
    return module_inf

# this function used to save last call upper module inf
# hyperlink action add_to_module_trace
# father_inst is "father_module_name.inst_name"
def add_to_module_trace(module_name, father_inst):
    G["ModuleTrace"][module_name] = father_inst
register_hyperlink_action( add_to_module_trace, description = 'this link function add module trace' )

def get_inst_inf_from_module(module_name, inst_name):
    # get father module inf
    module_inf = get_module_inf(module_name)
    if not module_inf:
        return False
    # if module_inf no inst_name to inst_inf dic add it
    if 'inst_name_to_inst_inf_dic' not in module_inf:
        inst_name_to_inst_inf_dic = {}
        for inst_inf in module_inf['inst_inf_list']:
            inst_name_to_inst_inf_dic[ inst_inf['inst_name']['str'] ] = inst_inf
        module_inf['inst_name_to_inst_inf_dic'] = inst_name_to_inst_inf_dic
    # get inst inf
    if inst_name in module_inf['inst_name_to_inst_inf_dic']:
        return module_inf['inst_name_to_inst_inf_dic'][inst_name]
    return False

# if module_inf no inst_name to inst_inf dic add it
def add_inst_name_to_inst_inf_dic_to_module( module_inf ):
    if module_inf and ('inst_name_to_inst_inf_dic' not in module_inf):
        inst_name_to_inst_inf_dic = {}
        for inst_inf in module_inf['inst_inf_list']:
            inst_name_to_inst_inf_dic[ inst_inf['inst_name_sr']['str'] ] = inst_inf
        module_inf['inst_name_to_inst_inf_dic'] = inst_name_to_inst_inf_dic
    return

def get_module_inst_inf(module_name, inst_name ):
    result = { "module_inf" : {}, "inst_inf": {} }
    # get module_inf
    module_inf = get_module_inf(module_name)
    if not module_inf:
        PrintDebug("get_module_inst_inf: no module_inf ! module = %s\n"%(module_name))
        return False
    result["module_inf"] = module_inf;
    add_inst_name_to_inst_inf_dic_to_module(module_inf)
    # get inst inf
    if inst_name not in module_inf['inst_name_to_inst_inf_dic']:
        PrintDebug("get_module_inst_inf: inst_name = %s not in module =%s inst list= %s\n"%(inst_name, module_name, list(module_inf['inst_name_to_inst_inf_dic'])))
        return False
    inst_inf = module_inf['inst_name_to_inst_inf_dic'][inst_name]
    result["inst_inf"] = inst_inf;
    return result

def get_module_inst_iocnt_inf(module_name, inst_name, io_name, io_idx):
    result = { "module_inf": {}, "inst_inf": {}, "iocnt_inf": {} }
    module_inst_inf      = get_module_inst_inf(module_name, inst_name )
    inst_inf             = module_inst_inf["inst_inf"]
    result["module_inf"] = module_inst_inf["module_inf"]
    result["inst_inf"]   = inst_inf
    if not inst_inf :
        return result
    # get cnt inf from io_name, io_idx
    iocnt_inf_list = inst_inf["iocnt_inf_list"]
    if 'subio_name_to_iocnt_inf_dic' not in inst_inf:
        subio_name_to_iocnt_inf_dic = {}
        for iocnt_inf in iocnt_inf_list:
            if iocnt_inf["sub_name_sr"]:
                subio_name = iocnt_inf["sub_name_sr"]['str']
                subio_name_to_iocnt_inf_dic[ subio_name ] = iocnt_inf
        inst_inf["subio_name_to_iocnt_inf_dic"] = subio_name_to_iocnt_inf_dic
    # check if can found by name
    if io_name in inst_inf["subio_name_to_iocnt_inf_dic"]:
        result["iocnt_inf"] = inst_inf["subio_name_to_iocnt_inf_dic"][io_name]
        return result
    # need get it by idx
    # current can not deal merge ".A(a), b, c" case
    if (not inst_inf["subio_name_to_iocnt_inf_dic"]) and (io_idx < len(iocnt_inf_list)) :
        result["iocnt_inf"] = iocnt_inf_list[io_idx]
        return result
    PrintReport("Warning: can not get io:'%s(n = %d)' at '%s.%s' 's connect !"%(io_name, io_idx, module_name, inst_name) )
    return result

def track_module_trace(module_name):
    if module_name not in G["ModuleTrace"]:
        return False
    return G["ModuleTrace"][module_name]

# only search all vtags_incdir to see if add new files
# if incdir and compile define change need re generate vtags.db
def update_offline_file_db():
    # 1 get current all vtags_incdir design file
    onload_G_FileListInf()
    new_vtags_incdir_design_files = []
    for dir_path in G["FileListInf"]["VtagsIncdirList"]:
        new_vtags_incdir_design_files += recursive_search_all_deisgn_file(dir_path)
    # vtags_incdir_list  = filelist_info['vtags_incdir_list']
    # 2. for file current del, just skip will remove when used
    #    so just care about the new add files
    onload_G_OffLineFileInfoDic()
    new_file_path_set = set(new_vtags_incdir_design_files) - set( G['OffLineFileInfoDic'] )
    # when refresh just do it one by one, not use filelist function
    for f in new_file_path_set:
        cur_serialize_file_name = gen_serialize_file_name(G["OffLineFileInfoDic"]["@next_serialize_postfix"], f)
        G["OffLineFileInfoDic"]["@next_serialize_postfix"] += 1
        add_to_offline_file_db(f, cur_serialize_file_name)
    store_G_OffLineInf()
    return True



def add_to_inline_file_db( file_inf ):
    if not file_inf:
        return
    # add file inf
    G["InLineFileInfDic"][ file_inf["file_state"]["file_path"] ] = file_inf
    # change code_inf_list to real path
    for code_inf in file_inf["code_inf_list"]:
        code_inf['file_path'] = get_real_path( code_inf['file_path'] )
    # add module inf
    for m_inf in file_inf["module_inf_list"]:
        c_m_inf                     = copy.copy(m_inf) # incase influence offline db
        c_m_inf["last_modify_time"] = file_inf["file_state"]["last_modify_time"]
        c_m_inf["file_path"]        = file_inf["file_state"]["file_path"]
        # change code_inf_list to real path
        for code_inf in c_m_inf["code_inf_list"]:
            code_inf['file_path'] = get_real_path( code_inf['file_path'] )
        G["InLineModuleInfDic"][m_inf["module_name_sr"]["str"]] = c_m_inf
    return

def remove_from_offline_file_db(file_inf):

    HasModifyOffLineModulePathDic      = False   
    HasModifyOffLineFileInfoDic        = False 
    HasModifyOffLineMacroInfDic        = False 
    HasModifyOffLineFatherInstListDic  = False       
    HasModifyOffLineChildModuleListDic = False       

    onload_G_OffLineFileInfoDic()
    onload_G_OffLineModulePathDic()
    onload_G_OffLineFatherInstListDic()
    onload_G_OffLineChildModuleListDic()

    file_path = file_inf["file_state"]["file_path"]
    # remove OffLineFileInfoDic
    if file_path in G["OffLineFileInfoDic"]:
        HasModifyOffLineFileInfoDic = True
        del G["OffLineFileInfoDic"][file_path]
    # remove OffLineMacroInfDic no need remove, delate when used
    # remove OffLineModulePathDic
    for module_inf in file_inf["module_inf_list"]:
        module_name = module_inf["module_name_sr"]["str"]
        if module_name in G["OffLineModulePathDic"]:
            HasModifyOffLineModulePathDic = True
            del G["OffLineModulePathDic"][module_name]
    # remove OffLineFatherInstListDic
    for module_inf in file_inf["module_inf_list"]:
        for inst_inf in module_inf["inst_inf_list"]:
            submodule_name = inst_inf["submodule_name_sr"]["str"]
            if (submodule_name in G["OffLineFatherInstListDic"]):
                if file_path in G["OffLineFatherInstListDic"][submodule_name]:
                    HasModifyOffLineFatherInstListDic = True
                    del G["OffLineFatherInstListDic"][submodule_name][file_path]
                if not G["OffLineFatherInstListDic"][submodule_name]:
                    HasModifyOffLineFatherInstListDic = True
                    del G["OffLineFatherInstListDic"][submodule_name]
    # remove OffLineChildModuleListDic
    for module_inf in file_inf["module_inf_list"]:
        module_name = module_inf["module_name_sr"]["str"]
        if module_name in G["OffLineChildModuleListDic"]:
            HasModifyOffLineChildModuleListDic = True
            del G['OffLineChildModuleListDic'][module_name]

    G['OffLineModifyMask']["OffLineModulePathDic"]      |= HasModifyOffLineModulePathDic
    G['OffLineModifyMask']["OffLineFileInfoDic"]        |= HasModifyOffLineFileInfoDic
    G['OffLineModifyMask']["OffLineMacroInfDic"]        |= HasModifyOffLineMacroInfDic
    G['OffLineModifyMask']["OffLineFatherInstListDic"]  |= HasModifyOffLineFatherInstListDic
    G['OffLineModifyMask']["OffLineChildModuleListDic"] |= HasModifyOffLineChildModuleListDic
    return

def add_to_offline_file_db(path, serialize_file_name):
    HasModifyOffLineModulePathDic      = False   
    HasModifyOffLineFileInfoDic        = False
    HasModifyOffLineMacroInfDic        = False 
    HasModifyOffLineFatherInstListDic  = False
    HasModifyOffLineChildModuleListDic = False

    onload_G_FileListInf()
    # remove old
    ser_path = G['ParserOutPath'] + '/' + serialize_file_name
    os.system("rm -rf "+ ser_path)
    assert( not os.path.exists(ser_path) )
    # do passer
    Parser.parser_from_file_list(G["FileListInf"]["DefineList"], 
        G["FileListInf"]["IncdirList"], 
        [ (path,serialize_file_name) ], 
        G['RunLogPath'], 'tmp' )
    # try load parser result
    new_file_inf = load_python_inf( ser_path )
    if not new_file_inf:
        PrintDebug("add_to_offline_file_db: parser failed ! %s"%( [path,serialize_file_name] ))
        return False
    file_path = new_file_inf["file_state"]["file_path"]
    # update offline information
    onload_G_OffLineFileInfoDic()
    onload_G_OffLineMacroInfDic()
    onload_G_OffLineModulePathDic()
    onload_G_OffLineFatherInstListDic()
    onload_G_OffLineChildModuleListDic()
    # add to OffLineFileInfoDic
    # need Struct Sync to C-Parser
    G["OffLineFileInfoDic"][file_path] = {"last_modify_time": new_file_inf["file_state"]["last_modify_time"], 
        "serialize_file_name": serialize_file_name}
    HasModifyOffLineFileInfoDic = True
    # add to OffLineMacroInfDic
    for macro_inf in new_file_inf["macro_inf_list"]:
        G["OffLineMacroInfDic"][macro_inf["name_sr"]["str"]] = macro_inf
        HasModifyOffLineMacroInfDic = True
    # add to OffLineModulePathDic
    for module_inf in new_file_inf["module_inf_list"]:
        module_name = module_inf["module_name_sr"]["str"]
        G["OffLineModulePathDic"][module_name] = file_path
        HasModifyOffLineModulePathDic = True
    # add to OffLineFatherInstListDic
    for module_inf in new_file_inf["module_inf_list"]:
        for inst_inf in module_inf["inst_inf_list"]:
            submodule_name = inst_inf["submodule_name_sr"]["str"]
            # need Struct Sync to C-Parser
            father_inst = "%s.%s"%(module_inf["module_name_sr"]["str"], inst_inf["inst_name_sr"]["str"])
            file_dic    = G["OffLineFatherInstListDic"].setdefault( submodule_name, {} )
            father_inst_list = file_dic.setdefault( file_path, [] )
            father_inst_list.append( father_inst )
            HasModifyOffLineFatherInstListDic = True
    # add to OffLineChildModuleListDic
    for module_inf in new_file_inf["module_inf_list"]:
        module_name = module_inf["module_name_sr"]["str"]
        if module_name not in G['OffLineChildModuleListDic']:
            HasModifyOffLineChildModuleListDic = True
        child_dic = G['OffLineChildModuleListDic'].setdefault(module_name, {} )
        for inst_inf in module_inf['inst_inf_list']:
            submodule_name = inst_inf["submodule_name_sr"]['str']
            child_dic.setdefault( submodule_name, "" )
            HasModifyOffLineChildModuleListDic = True
    G['OffLineModifyMask'][ "OffLineModulePathDic"]      |= HasModifyOffLineModulePathDic
    G['OffLineModifyMask'][ "OffLineFileInfoDic"]        |= HasModifyOffLineFileInfoDic
    G['OffLineModifyMask'][ "OffLineMacroInfDic"]        |= HasModifyOffLineMacroInfDic
    G['OffLineModifyMask'][ "OffLineFatherInstListDic"]  |= HasModifyOffLineFatherInstListDic
    G['OffLineModifyMask'][ "OffLineChildModuleListDic"] |= HasModifyOffLineChildModuleListDic
    return new_file_inf


def refresh_file_info(path, add_inline = False):
    onload_G_OffLineFileInfoDic()
    if path not in G["OffLineFileInfoDic"]:
        PrintDebug("Error: Offline DataBase not coherence ! file not in FileInf ! %s "%(path))
        return False
    file_info = G["OffLineFileInfoDic"][path]
    # file is new and valid
    if check_inf_valid(path, file_info["last_modify_time"]):
        return True
    # file is modefy or delate, loading again
    loading_file_inf(path, add_inline)
    return True

def loading_file_inf(path, add_inline = True):
    # if file already in fileinf dic need check if not valid remove stale
    if (path in G["InLineFileInfDic"]):
        if check_inf_valid(path, G["InLineFileInfDic"][path]["file_state"]['last_modify_time']):
            return G["InLineFileInfDic"][path]
        del G["InLineFileInfDic"][path]
    # generate new file inf 
    onload_G_OffLineFileInfoDic()
    serialize_file_name = ''
    if path in G["OffLineFileInfoDic"]:
        cur_file_info = G["OffLineFileInfoDic"][path]
        ser_path = G['ParserOutPath'] + '/' + cur_file_info['serialize_file_name']
        cur_file_inf  = load_python_inf( ser_path )
        if cur_file_inf:
            # check fileinfo consistence with file_inf
            assert( cur_file_info["last_modify_time"] == cur_file_inf["file_state"]["last_modify_time"] ),"%s\n %s\n%s ,\n %s"%(path, ser_path, cur_file_info, cur_file_inf["file_state"] )
            # file inf fresh
            if check_inf_valid(path, G["OffLineFileInfoDic"][path]['last_modify_time']):
                if add_inline:
                    add_to_inline_file_db(cur_file_inf)
                return cur_file_inf
            # file inf stale
            remove_from_offline_file_db(cur_file_inf)
        else:
            PrintDebug('Trace: OffLineFileInfoDic exit, not get file_inf: %s'%(cur_file_info.__str__()))
            # means some reason OffLineFileInfoDic not consistent with Parser file inf, remove from OffLineFileInfoDic
            del G["OffLineFileInfoDic"][path]
            G["OffLineModifyMask"]["OffLineFileInfoDic"] = True
        # already remove old file inf, generate a new fileinfo
        serialize_file_name = cur_file_info['serialize_file_name']
    else:
        serialize_file_name = gen_serialize_file_name(G["OffLineFileInfoDic"]["@next_serialize_postfix"], path)
        G["OffLineFileInfoDic"]["@next_serialize_postfix"] += 1
    # no file exist anywhere, parser new path
    # not updata for a non exist file
    if not os.path.isfile(path):
        PrintDebug('Trace: loading_file_inf: file not exit ! file: %s'%(path))
        return False
    new_file_inf = add_to_offline_file_db(path, serialize_file_name)
    store_G_OffLineInf()
    if not new_file_inf:
        return False
    # add to inline file db
    if add_inline:
        add_to_inline_file_db(new_file_inf)
    return new_file_inf

#--------------------------------------------------------
# Offline glb inf
#--------------------------------------------------------
def onload_G_OffLineMacroInfDic():
    # if OffLineMacroInfDic not updata get from pickle
    if G['OffLineMacroInfDic'] == None:
        G['OffLineMacroInfDic'] = load_python_inf( G['ParserOutPath'] + '/parser_macro_define_dic.py' )
        if not G['OffLineMacroInfDic']:
            G['OffLineMacroInfDic'] = {}

def store_G_OffLineMacroInfDic():
    assert( G['OffLineMacroInfDic'] != None )
    f = open(G['ParserOutPath'] + '/parser_macro_define_dic.py', 'w')
    f.write('data = %s'%( G['OffLineMacroInfDic'].__str__() ))
    f.close()

def onload_G_OffLineModulePathDic():
    if G['OffLineModulePathDic'] == None:
        G['OffLineModulePathDic'] = load_python_inf( G['ParserOutPath'] + '/parser_module_path_dic.py' )
        if not G['OffLineModulePathDic']:
            G['OffLineModulePathDic'] = {}
    return

def store_G_OffLineModulePathDic():
    assert( G['OffLineModulePathDic'] != None )
    f = open(G['ParserOutPath'] + '/parser_module_path_dic.py', 'w')
    f.write('data = %s'%( G['OffLineModulePathDic'].__str__() ))
    f.close()

def onload_G_OffLineFatherInstListDic():
    if G['OffLineFatherInstListDic'] == None:
        G['OffLineFatherInstListDic'] = load_python_inf( G['ParserOutPath'] + '/parser_father_insts_dic.py' )
        if not G['OffLineFatherInstListDic']:
            G['OffLineFatherInstListDic'] = {}
    return

def onload_G_OffLineChildModuleListDic():
    if G['OffLineChildModuleListDic'] == None:
        G['OffLineChildModuleListDic'] = load_python_inf( G['ParserOutPath'] + '/parser_child_module_dic.py')
        if not G['OffLineChildModuleListDic']:
            G['OffLineChildModuleListDic'] = {}
    return

def store_G_OffLineFatherInstListDic():
    assert( G['OffLineFatherInstListDic'] != None )
    f = open(G['ParserOutPath'] + '/parser_father_insts_dic.py', 'w')
    f.write('data = %s'%( G['OffLineFatherInstListDic'].__str__() ))
    f.close()

def store_G_OffLineChildModuleListDic():
    assert( G['OffLineChildModuleListDic'] != None )
    f = open(G['ParserOutPath'] + '/parser_child_module_dic.py', 'w')
    f.write('data = %s'%( G['OffLineChildModuleListDic'].__str__() ))
    f.close()

def onload_G_OffLineFileInfoDic():
    if G['OffLineFileInfoDic'] == None:
        G['OffLineFileInfoDic'] = load_python_inf( G['ParserOutPath'] + '/parser_file_info_dic.py' )
        if not G['OffLineFileInfoDic']:
            G['OffLineFileInfoDic'] = {}
        # add a next serialize name postfix nomber if not
        if "@next_serialize_postfix" not in G['OffLineFileInfoDic']:
            G['OffLineFileInfoDic']["@next_serialize_postfix"] = len(G['OffLineFileInfoDic'])
    return

def store_G_OffLineFileInfoDic():
    assert( G['OffLineFileInfoDic'] != None )
    f = open(G['ParserOutPath'] + '/parser_file_info_dic.py', 'w')
    f.write('data = %s'%( G['OffLineFileInfoDic'].__str__() ))
    f.close()

def store_G_OffLineInf():
    for name in G["OffLineModifyMask"]:
        if G["OffLineModifyMask"][name]:
            exec('store_G_%s()'%(name))
            G["OffLineModifyMask"][name] = False
    return

def get_father_inst_list( module_name ):
    # 1. skip BaseModule
    if module_name in G["BaseModuleInf"]["BaseModules"]:
        PrintReport('module "%s" is base module, has too many father not show it !'%(module_name))
        return []
    onload_G_OffLineFatherInstListDic()
    # 2. check intime
    if module_name in G['OffLineFatherInstListDic']:
        file_list = set( G['OffLineFatherInstListDic'][module_name] )
        for f in file_list:
            if refresh_file_info(f): 
                continue
            del G['OffLineFatherInstListDic'][module_name][f]
    # 3. merge father inst
    insts_list = []
    if module_name in G['OffLineFatherInstListDic']:
        for f in set( G['OffLineFatherInstListDic'][module_name] ):
            insts_list += G['OffLineFatherInstListDic'][module_name][f]
    return list( set(insts_list) )

# need special care to loop case
def recursion_get_module_trace( module_name, cur_trace, full_traces ):
    father_inst_list = get_father_inst_list( module_name )
    if not father_inst_list:
        if cur_trace:
            full_traces.append( cur_trace )
        return
    for father_inst in father_inst_list:
        new_trace = [ t for t in cur_trace]
        # need special care to loop case
        for pre_inst in new_trace:
            if pre_inst != father_inst:
                continue
            new_trace.append( father_inst )
            full_traces.append( new_trace )
            return
        new_trace.append( father_inst )
        # recursion go upper
        recursion_get_module_trace( father_inst.split('.')[0], new_trace, full_traces )
    return

# get top module list, which not father module
def get_all_top_modules():
    # 1 load father module inf
    onload_G_OffLineModulePathDic()
    onload_G_OffLineFatherInstListDic()
    onload_G_OffLineChildModuleListDic()
    # old version list top 100
    if not G['OffLineChildModuleListDic']:
        top_set  = set(G['OffLineModulePathDic']) - set(G['OffLineFatherInstListDic'])
        top_list = list(top_set)
        top_list.sort( key=lambda x: len(x) )
        top_list = top_list[:G['ShowTopModuleNum']]
        top_list.sort()
        return top_list
    # new version list top deeper
    top_set = set(G['OffLineChildModuleListDic']) - set(G['OffLineFatherInstListDic'])
    if len(top_set) <= G['ShowTopModuleNum']:
        top_list = list(top_set)
        top_list.sort()
        return top_list
    # get the most
    top_module_tree = {}
    for top in top_set:
        if G["OffLineChildModuleListDic"][top]:
            top_module_tree[top] = {"pass_module":set([top]), "same_level_submodules": set( G['OffLineChildModuleListDic'][top] ) }
    while len(top_module_tree) > G['ShowTopModuleNum']:
        top_need_del = set()
        for top in top_module_tree:
            pass_module               = top_module_tree[top]["pass_module"]
            same_level_submodules     = top_module_tree[top]["same_level_submodules"]
            new_same_level_submodules = set()
            for sm in same_level_submodules:
                if sm in pass_module:
                    continue
                pass_module.add(sm)
                if (sm in G['OffLineChildModuleListDic']) and G['OffLineChildModuleListDic'][sm]:
                    new_same_level_submodules |= set( G['OffLineChildModuleListDic'][sm] )
            if not new_same_level_submodules:
                top_need_del.add(top)
                continue
            top_module_tree[top]["same_level_submodules"] = new_same_level_submodules
        # all at same level
        if len(top_need_del) == len(top_module_tree):
            break
        # gose to next level
        for top in top_need_del:
            del top_module_tree[top]
    # return lst
    top_list = list(top_module_tree)
    top_list.sort( key=lambda x : len(x) )
    top_list = top_list[:G['ShowTopModuleNum']]
    top_list.sort()
    return top_list

def get_macro_inf( name ):
    onload_G_OffLineMacroInfDic()
    if name not in G["OffLineMacroInfDic"]:
        return None
    macro_inf = G["OffLineMacroInfDic"][name]
    if check_inf_valid( macro_inf["file_state"]["file_path"], macro_inf["file_state"]["last_modify_time"] ):
        return macro_inf
    # stale reload file try again
    del G["OffLineMacroInfDic"][name]
    loading_file_inf( macro_inf["file_state"]["file_path"] )
    if name not in G["OffLineMacroInfDic"]:
        if not G['RefreshDBValid']:
            return None
        update_offline_file_db()
        if name not in G["OffLineMacroInfDic"]:
            return None
    macro_inf = G["OffLineMacroInfDic"][name]
    assert( check_inf_valid( macro_inf["file_state"]["file_path"], macro_inf["file_state"]["last_modify_time"] ) )
    return macro_inf

def recursive_search_all_deisgn_file(dir_path):
    real_dir_path = get_real_path(dir_path)
    if not os.path.isdir(real_dir_path):
        PrintDebug("recursive_search_all_deisgn_file: dir path not dir ! %s"%(dir_path))
        return []
    postfix_patten = '|'.join(list(G['SupportVerilogPostfix']))
    cur_dir_all_files    = os.popen('find %s -path \'*vtags.db\' -a -prune -o -type f 2>/dev/null | egrep "\.(%s)$"'%(real_dir_path,postfix_patten)).readlines()
    cur_dir_all_files    = [ d_l.rstrip('\n') for d_l in cur_dir_all_files ]
    return cur_dir_all_files

def recursive_search_all_deisgn_file_smart(dir_path):
    real_dir_path = get_real_path(dir_path)
    if not os.path.isdir(real_dir_path):
        PrintDebug("recursive_search_all_deisgn_file_smart: dir path not dir ! %s"%(dir_path))
        return []
    # get all files, check at most 10 file to make sure if it's verlog design
    design_patten        = "(" \
                         + "(^\s*endmodule\s)"   \
                         + "|(^\s*wire\s)"   \
                         + "|(^\s*reg\s)"    \
                         + "|(^\s*logic\s)"  \
                         + "|(^\s*assign\s)" \
                         + "|(^\s*always\W)" \
                         + "|(^\s*define\s)" \
                         + ")"
    cur_dir_all_files    = os.popen('find %s -path \'*vtags.db\' -a -prune -o -type f 2>/dev/null'%(real_dir_path)).readlines()
    postfix_design_map   = {}
    new_found_design_postfix = []
    for f in cur_dir_all_files:
        f = f.strip()
        f_postfix = os.path.splitext(f)[-1]
        if not f_postfix or (f_postfix.lstrip(".") in G['SupportVerilogPostfix']):
            continue
        f_postfix_inf = postfix_design_map.setdefault( f_postfix, [0, False] ) # test number and if is design inf
        if f_postfix_inf[0] > 10 or f_postfix_inf[1] == True:
            continue
        # test if is design
        f_postfix_inf[0] += 1
        if os.popen("egrep -l \"%s\" %s 2>/dev/null"%(design_patten, f)).readlines():
            f_postfix_inf[1] = True
            new_found_design_postfix.append( f_postfix.lstrip(".") )
    # choise postfix for design
    if new_found_design_postfix:
        print("Found new file with postfix has design : ")
        for i, p in enumerate(new_found_design_postfix):
            print("  %-3d : '.%s'"%(i,p))
        choise_postfix_idxs = []
        choise = raw_input("Add to design ('0 ... %d' or 'Entry to skip') : "%(len(new_found_design_postfix)-1))
        while 1:
            choise = choise.strip()
            if not choise:
                break
            try:
                choise_postfix_idxs = [ int(idx) for idx in re.split("\W+", choise) ]
                assert( min(choise_postfix_idxs) >= 0 and max(choise_postfix_idxs) < len(new_found_design_postfix) )
                break
            except:
                choise = raw_input("illegal input try again ('0 ... %d' or 'Entry to skip') : ")
                continue
        for idx in choise_postfix_idxs:
            postfix = new_found_design_postfix[idx]
            print("Add files with postfix '.%s' as design !"%(postfix))
            G["SupportVerilogPostfix"].add( postfix )
    # get all design files
    postfix_patten = '|'.join(list(G['SupportVerilogPostfix']))
    cur_dir_all_files    = os.popen('find %s -path \'*vtags.db\' -a -prune -o -type f 2>/dev/null | egrep "\.(%s)$"'%(real_dir_path,postfix_patten)).readlines()
    cur_dir_all_files    = [ d_l.rstrip('\n') for d_l in cur_dir_all_files ]
    return cur_dir_all_files

def gen_serialize_file_name(n, path):
    file_name = path.strip().split('/')[-1]
    serialize_file_name =  'parser_' + re.sub('\W', '_', file_name) + '_%d.py'%(n)
    return serialize_file_name

def parser_vcs_file_list(vcs_file_list):
    print("Parsering FileList ...")
    if not os.path.isfile(vcs_file_list):
        return []
    lines = open(vcs_file_list, 'r').readlines()
    define_pair_list  = []
    incdir_list       = []
    design_list       = []
    design_set        = set()
    vtags_incdir_list = []
    passed_file_list  = set() # in case filelist cyclic  
    i = 0
    while(i < len(lines)):
        l = lines[i].strip()
        i += 1
        # match +define+
        find_define = re.findall('\+define\+(\S+)', l)
        for n_v in find_define:
            split_v = n_v.split('=')
            name    = split_v[0].strip()
            value   = ''
            if len(split_v) >= 2:
                value = ''.join(split_v[1:])
            define_pair_list.append( (name, value) )
        # match +incdir+
        find_incdir = re.findall('\+incdir\+([^+]+)', l)
        for incdir in find_incdir:
            dir_path      = re.sub('\s.*', '', incdir)
            dir_real_path = get_real_path(dir_path)
            if os.path.isdir(dir_real_path):
                incdir_list.append( dir_real_path )
            else:
                print("+incdir+'%s' - not a dir !"%(dir_path))
        # match -f
        find_filelist = re.findall('-f\s+(\S+)', l)
        for path in find_filelist:
            real_path = get_real_path( path.strip() )
            if real_path in passed_file_list:
                continue
            passed_file_list.add(real_path)
            if os.path.isfile(real_path):
                new_lines = open(real_path, 'r').readlines()
                lines     = lines[:i] + new_lines + lines[i:]
            else:
                print("-f '%s' - not exists !"%(path))
        #-v filename : Specifies a Verilog library file. VCS looks in this file for module and UDP 
        #   definitions for the module and UDP instances that VCS found in your source code but for which it did not 
        #   find the corresponding module or UDP definitions in your source code.
        find_filepath = re.findall('-v\s+(\S+)', l)
        for path in find_filepath:
            real_path = get_real_path( path.strip() )
            if os.path.isfile(real_path):
                if real_path not in design_set:
                    design_list.append( (real_path, gen_serialize_file_name(len(design_list), real_path) ) )
                    design_set.add(real_path)
            else:
                print("-v '%s' - not exists !"%(path))
        # all line is a filename
        real_path_l = get_real_path( l )
        if os.path.isfile(real_path_l):
            if real_path_l not in design_set:
                design_list.append( (real_path_l, gen_serialize_file_name(len(design_list), real_path_l) ) )
                design_set.add(real_path_l)
            continue
        # +vtags_incdir+dir_path :  recursive search all file below dir
        find_vtags_incdir = re.findall('\+vtags_incdir\+([^+]+)', l)
        for vtags_incdir in find_vtags_incdir:
            dir_path      = re.sub('\s.*', '', vtags_incdir)
            if os.path.isdir(dir_path):
                vtags_incdir_list.append( dir_path )
                for r_f in recursive_search_all_deisgn_file_smart(dir_path):

                    if r_f not in design_set:
                        design_list.append( (r_f, gen_serialize_file_name(len(design_list), r_f) ) )
                        design_set.add(r_f)
            else:
                print("+vtags_incdir+'%s' not a dir !"%(dir_path))
    return { "define_pair_list"   : define_pair_list     
            ,"incdir_list"        : incdir_list
            ,"design_list"        : design_list
            ,"vtags_incdir_list"  : vtags_incdir_list }

def onload_G_FileListInf():
    if G['FileListInf'] != None:
        return
    file_list_inf    = load_python_inf( G['ParserOutPath'] + '/file_list_inf.py')
    if file_list_inf:
        G['FileListInf'] = file_list_inf
        return
    G['FileListInf'] = { 'DefineList':[], 'IncdirList':[], "VtagsIncdirList": []}
    PrintDebug("onload_G_FileListInf: failed ! %s"%(G['ParserOutPath'] + '/file_list_inf.py'))
    return







