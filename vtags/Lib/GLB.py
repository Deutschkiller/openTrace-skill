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
from Lib.ExceptionLib import *

#-------------------------------------------------------------------------------
# when import GLB vtags install path must already in system
#-------------------------------------------------------------------------------
def get_install_path():
    for path in sys.path:
        m_path = re.match('(?P<i_path>.*(^|\W)vtags-[^/]*)', path)
        if m_path:
            return m_path.group('i_path')
    print("Error: can not found vtags install directory at env path, please vtags-x.xx(x should be digit (0-9)!, cur env path: %s"%(path))
    exit(0)
    return ''

#-------------------------------------------------------------------------------
# get next empty frame, report,log report index, first try del Frame, Report
#-------------------------------------------------------------------------------
# this function used to del not used old run.log in vtags.db
def del_old_logs(vtags_db_folder_path):
    ls_a_f = [ f.strip('\n') for f in os.popen('ls -a ' + vtags_db_folder_path).readlines() ]
    used_log_index = set()
    for f in ls_a_f:
        match_swp = re.match('\.(Frame|Report|run)(?P<idx>\d+)(\.ZL|\.log)(\.v)?\.swp',f)
        if match_swp:
            used_log_index.add(int(match_swp.group('idx')))
    ls_f   = [ f.strip('\n') for f in os.popen('ls ' + vtags_db_folder_path).readlines() ]
    for f in ls_f:
        match_idx = re.match('(Frame|Report|run)(?P<idx>\d+)(\.ZL|\.log)(\.v)?', f)
        if not match_idx:
            continue
        cur_index = int(match_idx.group('idx'))
        if cur_index in used_log_index:
            continue
        os.system('rm %s/%s'%(vtags_db_folder_path,f) )
    return

#-------------------------------------------------------------------------------
# this function used to get the path postfix
#-------------------------------------------------------------------------------
def get_file_path_postfix(file_path):
    split_by_dot = file_path.split('.')
    if len(split_by_dot) < 2: # which means file_path has no postfix
        return ''
    post_fix = split_by_dot[-1]          # postfix care case
    return post_fix

# this function used to save env snapshort
def save_env_snapshort():
    snapshort = {}
    # 0: save cur dir path, used to quality opne snapshort
    snapshort['snapshort_dir_path'] = os.getcwd()
    # 1: save G
    snapshort['G'] = {}
    snapshort['G']['OpTraceInf']                      = {}
    snapshort['G']['OpTraceInf']['TracePoints']       = G['OpTraceInf']['TracePoints'] 
    snapshort['G']['OpTraceInf']['Nonius'     ]       = G['OpTraceInf']['Nonius'     ]
    snapshort['G']['WorkWin_Inf']                     = {}
    snapshort['G']['WorkWin_Inf']['OpenWinTrace']     = G['WorkWin_Inf']['OpenWinTrace']
    snapshort['G']['VimBufferLineFileLink' ]          = G["VimBufferLineFileLink" ]
    snapshort['G']["TraceInf"              ]          = G['TraceInf']
    snapshort['G']['CheckPointInf']                   = {}
    snapshort['G']['CheckPointInf']['CheckPoints']    = G['CheckPointInf']['CheckPoints']
    snapshort['G']['TopoInf']                         = {}
    snapshort['G']['TopoInf']['CurModule']            = G['TopoInf']['CurModule']
    snapshort['G']['ModuleTrace']                     = G['ModuleTrace']
    snapshort['G']['InLineIncFile2LogicFileDic']      = G['InLineIncFile2LogicFileDic']
    snapshort['G']['Frame_Inf']                       = { 'Frame_Path': "", 'Frame_Buffer':[] }
    snapshort['G']['Frame_Inf']['Frame_Path']         = G['Frame_Inf']['Frame_Path']
    if G['Frame_Inf']['Frame_Buffer']:
        snapshort['G']['Frame_Inf']['Frame_Buffer']   = [ l for l in G['Frame_Inf']['Frame_Buffer'] ]
    snapshort['G']['Report_Inf']                      = { "Report_Path": "", 'Report_Buffer':[] }
    snapshort['G']['Report_Inf']['Report_Path']       = G['Report_Inf']['Report_Path']
    if G['Report_Inf']['Report_Buffer']:
        snapshort['G']['Report_Inf']['Report_Buffer'] = [ l for l in G['Report_Inf']['Report_Buffer'] ]
    # 2: save act windows inf
    act_win_inf = []
    for w in vim.windows:
        c_file_path = os.path.realpath(w.buffer.name)
        if c_file_path == os.path.realpath(vim.current.buffer.name):
            continue
        c_cursor    = w.cursor
        c_size      = (w.width, w.height)
        act_win_inf.append({'path': c_file_path, 'cursor': c_cursor, 'size': c_size })
    # last is current window
    cur_file_path  = os.path.realpath(vim.current.buffer.name)
    cur_cursor     = vim.current.window.cursor   
    cur_size       = (vim.current.window.width, vim.current.window.height)
    act_win_inf.append({'path': cur_file_path, 'cursor': cur_cursor, 'size': cur_size })
    snapshort['act_win_inf'] = act_win_inf
    # in case snapshort will open by other person
    # need creat and change mod to r/w for all person for report and fram
    os.system( "touch %s; chmod 666 %s"%(G['Frame_Inf']['Frame_Path'],G['Frame_Inf']['Frame_Path']) )
    os.system( "touch %s; chmod 666 %s"%(G['Report_Inf']['Report_Path'],G['Report_Inf']['Report_Path']) )
    # save info
    pkl_output = open(G['VTagsPath'] + '/pickle/env_snapshort.pkl','wb')
    pickle.dump(snapshort, pkl_output)
    pkl_output.close()
    return True

def reload_env_snapshort(snapshort, G):
    # 1: reload G
    snapshort_G = snapshort['G']
    G['OpTraceInf']['TracePoints']    = snapshort_G['OpTraceInf']['TracePoints'] 
    G['OpTraceInf']['Nonius'     ]    = snapshort_G['OpTraceInf']['Nonius'     ]
    G['WorkWin_Inf']['OpenWinTrace']  = snapshort_G['WorkWin_Inf']['OpenWinTrace']
    G['VimBufferLineFileLink' ]       = snapshort_G["VimBufferLineFileLink" ]
    G["TraceInf"              ]       = snapshort_G['TraceInf']
    G['CheckPointInf']['CheckPoints'] = snapshort_G['CheckPointInf']['CheckPoints']
    G['TopoInf']['CurModule']         = snapshort_G['TopoInf']['CurModule']
    G['ModuleTrace']                  = snapshort_G['ModuleTrace']
    G['InLineIncFile2LogicFileDic']   = snapshort_G['InLineIncFile2LogicFileDic']
    G['Frame_Inf']['Frame_Buffer']    = snapshort_G['Frame_Inf']['Frame_Buffer']
    if 'Frame_Path' in snapshort_G['Frame_Inf']: # incase early version not save this
        G['Frame_Inf']['Frame_Path']      = snapshort_G['Frame_Inf']['Frame_Path']
    G['Report_Inf']['Report_Buffer']  = snapshort_G['Report_Inf']['Report_Buffer']
    if 'Report_Path' in snapshort_G['Report_Inf']:
        G['Report_Inf']['Report_Path']    = snapshort_G['Report_Inf']['Report_Path']
    # 4: reload act windows inf need re open at API.py
    G['EnvSnapshortWinsInf']          = snapshort['act_win_inf']
    return

def init_G_from_vtagsDB( vtags_db_folder_path = '', allow_from_glb = True ):
    import vim_glb_config as glb_config
    #-------------------------------------------------------------------------------
    # get vtags.db
    # find most resent vtags path from current folder to upper
    #-------------------------------------------------------------------------------
    if not vtags_db_folder_path:
        cur_path = os.getcwd()
        level = glb_config.vtags_db_search_level
        while cur_path and cur_path[0] == '/':
            if os.path.isdir(cur_path + '/vtags.db'):
                vtags_db_folder_path = cur_path + '/vtags.db'
                break
            cur_path = re.sub('/[^/]*$','',cur_path)
            level -= 1
            if level == 0:
                break
    # if not found a valid vtags db and need raise except to speed up 
    # none vtags vim open
    if (not allow_from_glb) and (not os.path.isdir(vtags_db_folder_path)):
        # raise VtagsDBNotFoundExcept
        return {} 
    #-------------------------------------------------------------------------------
    # get config
    # get finial config, if has vtag.db local config use local, if not use install
    # path glable config 
    #-------------------------------------------------------------------------------
    config          = None
    config_from_glb = False
    # if has local config try load local
    if vtags_db_folder_path:
        vtags_db_folder_path = os.path.realpath(vtags_db_folder_path) # incase for link
        sys.path.insert(0,vtags_db_folder_path)
        # if already import vim_local_config del it
        try:
            del vim_local_config
        except:
            pass
        # re import vim_local_config
        try:
            import vim_local_config
            config   = vim_local_config
            from_glb = False
        except:
            pass
    # if local config failed and alow load glb config
    if not config and allow_from_glb:
        config = glb_config
        config_from_glb = True

    #-------------------------------------------------------------------------------
    # init get the supported design file postfix
    # real supported postfix is config.support_verilog_postfix add postfix geted by 
    # the input file list
    #-------------------------------------------------------------------------------
    support_design_postfix_set = set(config.support_verilog_postfix)
    # find the minimum number current not used as the next log postfix
    valid_log_index = 0
    if vtags_db_folder_path:
        del_old_logs(vtags_db_folder_path)
        all_file_names_in_vtags_db = " ".join( os.listdir(vtags_db_folder_path) )
        while re.search( "(^|\s)(\.)?(debug%d\.log)(\W|$)"%(valid_log_index), all_file_names_in_vtags_db):
            valid_log_index += 1
    # stale now # file link used as a link to space option:
    # stale now # ----------------------------------------------------------------------------------------------------------------------
    # stale now # | type        | go_path       | go_pos          | go_word     | fold_status | fold_level | last_modify_time | discription
    # stale now # |-------------|---------------|-----------------|-------------|-------------|------------|------------------|--------------
    # stale now # | topo        | module path   | module name pos | module name | on/off      | n          | n                | Frame : link to topo line module
    # stale now # | base_module | module path   | module name pos | module name | on/off      | n          | n                | Frame : link to base module
    # stale now # | check_point | cp added path | cursor pos      | cursor word | on/off      | n          | n                | Frame : link to check point location
    # stale now # | trace result| result path   | result match pos| trace signal|             |            |                  | Report: link to trace source dest
    # stale now # ---------------------------------------------------------------------------------------------------------------------------
    # stale now # all vim buffer line file link, a path to file link list dic
    VimBufferLineFileLink = {}
    
    
    Frame_Inf = {
         "Frame_Win_x"        : config.frame_window_width      # frame window width
        ,"Frame_Path"         : ''
        ,"Frame_Buffer"       : None
        ,"FoldLevelSpace"     : config.frame_fold_level_space
    }
    if vtags_db_folder_path:
        Frame_Inf["Frame_Path"] = vtags_db_folder_path + '/' + 'Frame'
    
    
    Report_Inf = {
         "Report_Win_y"       : config.report_window_height        # report window height
        ,"Report_Path"        : None
        ,"Report_Buffer"      : None
    }
    if vtags_db_folder_path:
        Report_Inf["Report_Path"] = vtags_db_folder_path + '/' + 'Report.v'
    
    WorkWin_Inf ={
         "MaxNum"       : config.max_open_work_window_number
        ,"OpenWinTrace" : []
    }
    
    TraceInf = {
         'LastTraceSource' : {'Maybe':[], 'Sure':[], 'ShowIndex': 0, 'SignalName':'', 'ValidLineRange':[-1,-1], 'Path':'' } # Maybe[{'show':'', 'file_link':{ 'key':'','pos':(l,c),'path':'' } }] 
        ,'LastTraceDest'   : {'Maybe':[], 'Sure':[], 'ShowIndex': 0, 'SignalName':'', 'ValidLineRange':[-1,-1], 'Path':'' }
        ,'TraceSourceOptimizingThreshold' : config.trace_source_optimizing_threshold
    }
    
    # operation trace
    OpTraceInf = {
         'TracePoints' : [] # {'path':'', "pos":(line, colum), 'key':''}
        ,'TraceDepth'  : config.max_roll_trace_depth
        ,'Nonius'      : -1  # roll nonius 
    }
    
    TopoInf       = {
         'CurModule'    : ''
        ,'TopFoldLevel' : 0
    }
    
    CheckPointInf = {
         "MaxNum"         : config.max_his_check_point_num
        ,"CheckPoints"    : []  #{}--- key: '', link: {}
        ,"TopFoldLevel"   : 0
    }
    
    #-------------------------------------------------------------------------------
    # init the base module inf
    #-------------------------------------------------------------------------------
    BaseModules   = set()
    # get base module inf
    if not config_from_glb:
        try:
            pkl_input     = open(vtags_db_folder_path + '/pickle/all_basemodule_name_set.pkl','rb')
            BaseModules   = pickle.load(pkl_input)
            pkl_input.close()
        except:
            pass
    
    BaseModuleInf = {
         "BaseModuleThreshold"  : config.base_module_threshold  # when module inst BaseModuleThreshold times, then default set it to base module
        ,"BaseModules"          : BaseModules # module name set()
        ,"TopFoldLevel"         : 0
    }

    # max file name length in current os    
    try: # valid in vtags-2.22
        MaxFileNameLength = config.max_file_name_length # max file file name length
    except: # for pre version's local config
        MaxFileNameLength = glb_config.max_file_name_length

    # incase old version no this
    try:
        ShowTopModuleNum = config.gvim_vtags_db_list_top_module_numbers
    except:
        ShowTopModuleNum = glb_config.gvim_vtags_db_list_top_module_numbers

    G = {
        # 'InlineActive'                        : True  # set latter
         'OfflineActive'                       : True  # set latter
        ,'SupportVHDLPostfix'                  : set([])
        ,'SupportVerilogPostfix'               : support_design_postfix_set # 1.23 add filelist postfix and config postfix
        ,'InLineModuleInfDic'                  : {}
        ,'InLineFileInfDic'                    : {}
        ,'InLineCodeInfDic'                    : {} # {"file_path": {"code":[], "line_range":[] } }
        ,'InLineIncFile2LogicFileDic'          : {} # real file name to logic file path dic
        ,'FileListInf'                         : None
        ,'OffLineModulePathDic'                : None 
        ,'OffLineFileInfoDic'                  : None
        ,'OffLineMacroInfDic'                  : None
        ,"OffLineFatherInstListDic"            : None
        ,"OffLineChildModuleListDic"           : None
        ,"OffLineModifyMask"                   : {  "OffLineModulePathDic"      : False 
                                                   ,"OffLineFileInfoDic"        : False   
                                                   ,"OffLineMacroInfDic"        : False  
                                                   ,"OffLineFatherInstListDic"  : False
                                                   ,"OffLineChildModuleListDic" : False }
        ,'ModuleTrace'                         : {}    # {module_name: father_inst_inf }
        ,'OpTraceInf'                          : OpTraceInf
        ,"Debug"                               : config.debug_mode    # debug mode
        ,"RefreshDBValid"                      : config.dynamic_update_vtags_db
        ,"ShowReport"                          : config.show_report
        # ,"PrintDebug_F"                      : None         # function to print debug ,not change and set at begining
        ,"Frame_Inf"                           : Frame_Inf    # Frame window inf
        ,"Report_Inf"                          : Report_Inf   # report window inf
        ,"WorkWin_Inf"                         : WorkWin_Inf  # win config
        ,"VimBufferLineFileLink"               : VimBufferLineFileLink
        ,"TraceInf"                            : TraceInf
        ,"CheckPointInf"                       : CheckPointInf
        ,"BaseModuleInf"                       : BaseModuleInf
        ,'TopoInf'                             : TopoInf
        ,"FixExtraSpace"                       : True         # some situation come extra space, need do nonthing
        ,"IgnoreNextSpaceOp"                   : False        # just fold has a else space, not do space op
        ,"EnvSnapshortWinsInf"                 : []
        ,"SaveEnvSnapshort_F"                  : save_env_snapshort
        ,"VTagsPath"                           : vtags_db_folder_path
        ,"ParserOutPath"                       : ''
        ,"RunLogPath"                          : ''
        # add for path reduce
        ,"Short2RealPathMap"                   : None # some times pickle file name is too long to creat a file, so use this map to reduce it.
        ,"Real2ShortPathMap"                   : {}
        ,"MaxFileNameLength"                   : MaxFileNameLength # max file file name length
        # ,"InstallPath"                       : get_install_path()  # set latter
        # ,"LoadSnapShortPending"              : False               # set latter
        # ,"LoadTopModulePending"              : False               # set latter
        ,"ShowTopModuleNum"                    : ShowTopModuleNum
    }
    if vtags_db_folder_path:
        G["ParserOutPath"] = vtags_db_folder_path + '/parser_out/pub'
        G["RunLogPath"]    = vtags_db_folder_path + '/run.log'+str(valid_log_index)
    return G

#-------------------------------------------------------------------------------
# if not open vim inline turn off
# if open a unsupport rtl vtags db load pending
#-------------------------------------------------------------------------------
vim_opened           = False
vim_start_open_file  = ''
try:
    import vim
    vim_start_open_file = os.path.realpath(vim.current.buffer.name)
    vim_opened  = True
except:
    pass

#-------------------------------------------------------------------------------
# if gvim with a vtags.db snapshort, ask whether to open that snapshort
#-------------------------------------------------------------------------------
LoadSnapShortPending = False
LoadTopModulePending = False
if vim_opened and vim_start_open_file.rstrip('/')[-8:] == 'vtags.db':
    env_snapshort_path = vim_start_open_file.rstrip('/') + '/pickle/env_snapshort.pkl'
    if os.path.isfile(env_snapshort_path):
        os.system('echo \'Reload Work Snapshort at: "%s" (Y/N): \''%(env_snapshort_path))
        if sys.version_info[0] < 3:
            yes_or_no = raw_input()
        else:
            yes_or_no = input()
        if yes_or_no.lower() in ['y','yes']:
            LoadSnapShortPending = True
    else:
        LoadTopModulePending = True

#-------------------------------------------------------------------------------
# init G 
#-------------------------------------------------------------------------------
# if no vim opened means it's Offline function, so even if no vtags.db
# found in init_G_from_vtagsDB() it must not raise VtagsDBNotFoundExcept 
# except because user can set vtags db use set_vtags_db_path()
# if vim has opened, must has a valid vtags db, if not found just raise
# VtagsDBNotFoundExcept and terminate the python run
# if vim opened and not open a supported rtl design not active inline function

G                         = {}
G["InstallPath"]          = get_install_path()
G['InlineActive']         = False
G['OfflineActive']        = False # Offline will set True when set_vtags_db_path()
G["LoadSnapShortPending"] = False
G["LoadTopModulePending"] = False

if vim_opened:
    G["LoadSnapShortPending"] = LoadSnapShortPending
    if LoadSnapShortPending:
        new_G = init_G_from_vtagsDB(vim_start_open_file,  allow_from_glb = False )
        for k in new_G:
            G[k] = new_G[k]
        G['InlineActive']         = False
    else:
        new_G = init_G_from_vtagsDB( allow_from_glb = True )
        for k in new_G:
            G[k] = new_G[k]
        # if is rtl file but has no vtags.db return {} for inline active
        if new_G['VTagsPath'] and LoadTopModulePending:
            G['InlineActive']         = False
            G["LoadTopModulePending"] = True
        elif (not new_G['VTagsPath']) or (get_file_path_postfix(vim_start_open_file) not in new_G['SupportVerilogPostfix']):
            G['InlineActive']  = False
            G['OfflineActive'] = False # Offline will set True when set_vtags_db_path()
        else:
            G['InlineActive']  = True
        
#-------------------------------------------------------------------------------
# this function used to print debug inf:
# (1) generate vtags.db generate vtags.db/vtags_db.log
# (2) when debug = True generate run.logN when gvim run
#-------------------------------------------------------------------------------
# if run cmd:"vtags" in generate vtags situation, print log to vtags.db/vtags_run.log
vtags_db_log_path = ['']
# run log path
def PrintDebug( str, out_path = ''):
    if vtags_db_log_path[0]:
        output = open( vtags_db_log_path[0], 'a')
        output.write(str+'\n')
        output.close()
        return
    if not G['InlineActive'] and not G['OfflineActive'] and G['Debug']:
        print(str)
    if out_path and G['Debug']:
        output = open( out_path, 'a')
        output.write(str+'\n')
        output.close()
        return
    if G['InlineActive'] and G['Debug']:
        output = open( G['RunLogPath'] ,'a')
        output.write(str+'\n')
        output.close()
G['PrintDebug_F'] = PrintDebug
    
#-------------------------------------------------------------------------------
# Offline vtags use -db set a new vtags.db
#-------------------------------------------------------------------------------
def set_vtags_db_path(vtags_db_folder_path, InlineActive = False):
    vtags_db_folder_path = vtags_db_folder_path.rstrip('/')
    if vtags_db_folder_path[-8:] != 'vtags.db' or (not os.path.isdir(vtags_db_folder_path)):
        return False
    new_G = init_G_from_vtagsDB( vtags_db_folder_path, allow_from_glb = False )
    for key in new_G:
        G[key] = new_G[key]
    G['InlineActive']  = InlineActive
    return True


