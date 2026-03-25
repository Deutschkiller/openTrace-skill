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
# import vim, when gen vtags it will no vim,so use try 
try:
    import vim
except: 
    pass
# import normal lib
import re
import Lib.GLB as GLB
G          = GLB.G

# following lib will update inline
BaseLib    = None
ViewLib    = None
CodeLib    = None
FrameLib   = None
FileInfLib = None

#-------------------------------------------------------------------------------
# function to load local library
#-------------------------------------------------------------------------------
def load_local_libs():
    global BaseLib    
    global ViewLib    
    global CodeLib    
    global FrameLib   
    global FileInfLib 
    import Lib.BaseLib           as BaseLib
    import InlineLib.ViewLib     as ViewLib
    import Lib.CodeLib           as CodeLib
    import InlineLib.FrameLib    as FrameLib
    import Lib.FileInfLib        as FileInfLib
    return True

# shortcut key: <Space>r
def reload_env_snapshort_full():
    # current G['InlineActive'] should be False
    if G['InlineActive']:
        ViewLib.PrintReport('Warning: vtags already active, switch to snapshort will close current open files !')
    # current must has vtags.db
    if not G['VTagsPath']:
        return False 
    # update local lib
    load_local_libs()
    # try active InlineActive
    G['InlineActive'] = True
    # find env snapshort
    import pickle
    # vtags.db maybe found form current dir, or follow by gvim ...
    env_snapshort_path = G['VTagsPath'] + '/pickle/env_snapshort.pkl'
    loaded_snapshort   = None
    if os.path.isfile(env_snapshort_path):
        pkl_input        = open(env_snapshort_path,'rb')
        loaded_snapshort = pickle.load(pkl_input)
        pkl_input.close()
    else:
        ViewLib.PrintReport('Warning: no vtags snapshort found at: %s , do nonthings!'%(env_snapshort_path))
        return False
    # start load G
    GLB.reload_env_snapshort(loaded_snapshort, G)
    # start replay window
    if G['EnvSnapshortWinsInf']:
        # snapshort's work window trace
        OldOpenWinTrace = [p for p in G['WorkWin_Inf']['OpenWinTrace']]
        # add cur buffer in cur work window trace
        G['WorkWin_Inf']['OpenWinTrace'].insert(0, os.path.realpath(vim.current.buffer.name))
        # for all snapshort window(include work win, hold win ...)
        OpenWindows = ViewLib.replay_windows(G['EnvSnapshortWinsInf'], OldOpenWinTrace)
        # because base module may be changed so refresh topo and show base
        if G['Frame_Inf']['Frame_Path'] in OpenWindows:
            FrameLib.refresh_topo()
            FrameLib.show_base_module()
        ViewLib.PrintReport('Note: reload snapshort finish !')
    return True

def try_reload_env_snapshort():
    if G['Debug']:
        reload_env_snapshort_full()
    else:
        try: 
            reload_env_snapshort_full()
        except: pass

# shortcut key: gi
def go_into_submodule(): 
    cursor_inf          = ViewLib.get_cur_cursor_inf()
    module_inst_cnt_inf = FileInfLib.get_module_inst_cnt_sub_inf_from_pos(cursor_inf["file_path"], cursor_inf["pos"])
    # if match cnt inf, jump to cnt io
    file_inf            = module_inst_cnt_inf["file_inf"]
    module_inf          = module_inst_cnt_inf["module_inf"]
    inst_inf            = module_inst_cnt_inf["inst_inf"]
    if inst_inf:
        # will go to sub module code now, so cur module is the sub module last call
        submodule_name = inst_inf["submodule_name_sr"]['str']
        submodule_inf  = FileInfLib.get_module_inf(submodule_name)
        father_inst    = '%s.%s'%(module_inf["module_name_sr"]['str'], inst_inf["inst_name_sr"]['str'])
        cnt_sub_inf    = module_inst_cnt_inf["cnt_sub_inf"]
        # go to io
        if cnt_sub_inf:
            ViewLib.add_trace_point()
            FileInfLib.add_to_module_trace(submodule_name, father_inst)
            assert(submodule_inf) # has cnt_sub_inf must has submodule_inf
            real_location = FileInfLib.location_l2r(cnt_sub_inf["name_sr"]["range"], submodule_inf['code_inf_list'])
            if real_location:
                ViewLib.go_win( real_location["path"], real_location["pos"], cnt_sub_inf["name_sr"]["str"]) # logic to real
                return True
            BaseLib.PrintDebug("ERROR: go_into_submodule: real_location failed! cnt_sub = %s, submodule_inf=%s"%(cnt_sub_inf["name_sr"], submodule_inf.__str__()))
        # go to module define
        if submodule_inf:
            ViewLib.add_trace_point()
            FileInfLib.add_to_module_trace(submodule_name, father_inst)
            real_location = FileInfLib.location_l2r(submodule_inf["module_name_sr"]["range"], submodule_inf['code_inf_list'])
            if real_location:
                ViewLib.go_win( real_location["path"], real_location["pos"], submodule_inf["module_name_sr"]["str"]) # logic to real
                return True
            BaseLib.PrintDebug("ERROR: go_into_submodule: real_location failed ! submodule_inf=%s"%(submodule_inf.__str__()))
        BaseLib.PrintDebug("ERROR: go_into_submodule: cnt_sub_inf and submodule_inf failed! inst_inf = %s"%(inst_inf.__str__()))
    elif file_inf:
        match_include = re.match('\s*`include\W*"(?P<path>.*)"', cursor_inf['line'])
        if match_include:
            # test if it's include line if is go into include file
            logic_location = FileInfLib.location_r2l( cursor_inf['file_path'], cursor_inf["pos"], file_inf["code_inf_list"] )
            assert(logic_location)
            # if is include line, include file should be logic line + 1
            inc_pos = (logic_location['pos'][0] + 1, 0)
            inc_real_location = FileInfLib.location_l2r(inc_pos, file_inf["code_inf_list"])
            assert(inc_real_location),"%s"%([inc_pos,file_inf["code_inf_list"],inc_real_location].__str__())
            file_name = match_include.group('path').strip().split('/')[-1]
            if re.search( '(^|/)%s\s*$'%(file_name), inc_real_location['path']):
                ViewLib.add_trace_point()
                ViewLib.go_win( inc_real_location['path'], inc_real_location["pos"] ) # logic to real
                # add include file to logic path, because baybe file not in module and not add when get module inf
                G["InLineIncFile2LogicFileDic"][inc_real_location['path']] = logic_location['path']
                return True
        elif mopen(cursor_inf['word']):
            return True
    ViewLib.PrintReport('Warning: %s go to inst module or include file failed, do nonthing !'%( str(cursor_inf["pos"]) ))
    return True

def try_go_into_submodule():
    if not G['InlineActive']: return
    if G['Debug']:
        go_into_submodule()
    else:
        try: go_into_submodule()
        except: pass

# shortcut key: gu
def go_upper_module(): 
    cursor_inf      = ViewLib.get_cur_cursor_inf()
    file_module_inf = FileInfLib.get_module_inf_from_pos(cursor_inf['file_path'], cursor_inf['pos'])
    cur_file_inf    = file_module_inf['file_inf']
    # if in include file first go to include position
    if cursor_inf['file_path'] in G['InLineIncFile2LogicFileDic']:
        logic_location = FileInfLib.location_r2l( cursor_inf['file_path'], (0,0), cur_file_inf["code_inf_list"] )
        assert(logic_location)
        # include position must logic line -1
        inc_pos = (logic_location['pos'][0] -1, 0)
        inc_real_location = FileInfLib.location_l2r(inc_pos, cur_file_inf["code_inf_list"])
        assert(inc_real_location)
        ViewLib.add_trace_point()
        ViewLib.go_win( inc_real_location['path'], inc_real_location["pos"], 'include') # logic to real
        return
    # get cur module name
    cur_module_inf  = file_module_inf["module_inf"]
    if not cur_module_inf:
        ViewLib.PrintReport('Note: current cursor not in valid module, do-nothing !')
        return
    # get cur module last call upper module inf
    cur_module_name = cur_module_inf['module_name_sr']['str']
    father_inst     = FileInfLib.track_module_trace(cur_module_name)
    if father_inst:
        father_module, inst_name = father_inst.split('.')
        module_inst_inf = FileInfLib.get_module_inst_inf(father_module, inst_name)
        if module_inst_inf["inst_inf"]:
            father_path  = module_inst_inf["module_inf"]["file_path"]
            inst_name_sr = module_inst_inf["inst_inf"]["inst_name_sr"]
            ViewLib.add_trace_point()
            # logic to real pos
            real_location = FileInfLib.location_l2r(inst_name_sr["range"], module_inst_inf["module_inf"]['code_inf_list'])
            if not real_location:
                ViewLib.PrintReport('Warning: get inst "%s" real location failed !'%(inst_name_sr['str']))
                BaseLib.PrintDebug("ERROR: go_upper_module: real_location failed! inst_inf=%s, module_inf = %s"%(module_inst_inf["inst_inf"].__str__(), module_inst_inf["module_inf"].__str__()))
                return
            ViewLib.go_win( real_location['path'], real_location["pos"], inst_name_sr["str"]) # logic to real
            return
    # if no inline trace, get all possible father
    line_and_link_list = CodeLib.get_father_inst_line_and_link_list( cur_module_name )
    # no valid father
    if not line_and_link_list:
        ViewLib.PrintReport('Note: module %s not called by father module before !'%(cur_module_name))
        return
    # only one father , just go to it
    if len(line_and_link_list['link_list']) == 1:
        ViewLib.add_trace_point()
        BaseLib.do_hyperlink(line_and_link_list['link_list'][0], ['go_file_action', 'add_to_module_trace']) # first valid link
        return
    # has multi father, user to choise
    assert( len(line_and_link_list['link_list']) > 1 )
    # i = 0 
    link_list = []
    line_list = []
    # pre inf
    line_list.append('Knock "<Space>" to choise upper module you want: ')
    line_list.append('')
    link_list.append( {} )
    link_list.append( {} )
    line_list += line_and_link_list['line_list']
    link_list += line_and_link_list['link_list']
    mounted_line_inf  = BaseLib.MountPrintLines(line_list, label = 'Possible Upper', link_list = link_list)
    mounted_line_list = mounted_line_inf['line_list']
    mounted_link_list = mounted_line_inf['link_list']
    # add a empty line below
    mounted_line_list.append('')
    mounted_link_list.append({})
    ViewLib.add_trace_point()
    assert( len(mounted_line_list) == len(mounted_link_list) )
    ViewLib.PrintReport(mounted_line_list, mounted_link_list, MountPrint = True )
    # len(mounted_line_list) + 1 is the lines relative to the last report line
    # -4 is skip first 4 unused line
    ViewLib.go_win( G['Report_Inf']['Report_Path'] , (-(len(mounted_line_list) + 1 -4), 49) ) # no need logic to real
    return

def try_go_upper_module():
    if not G['InlineActive']: return
    if G['Debug']:
        go_upper_module()
    else:
        try: go_upper_module()
        except: pass

# shortcut key: mt
def print_module_trace(): 
    cursor_inf         = ViewLib.get_cur_cursor_inf()
    # get cur module name
    cur_module_inf     = FileInfLib.get_module_inf_from_pos(cursor_inf['file_path'], cursor_inf['pos'])["module_inf"]
    if not cur_module_inf:
        ViewLib.PrintReport('Note: current cursor not in valid module, do-nothing !')
        return
    cur_module_name = cur_module_inf['module_name_sr']['str']
    # recursion get all trace
    full_traces = []
    FileInfLib.recursion_get_module_trace(cur_module_name, [], full_traces)
    print_strs = []
    print_link = []
    i_offset = 0 # used to control multi same trace case
    for i, r_trace in enumerate(full_traces):
        trace             = r_trace[::-1]
        father_inst_chain = trace[0]
        for father_inst in trace[1:]:
            father, inst  = father_inst.split('.')
            father_inst_chain += '(%s).%s'%(father, inst)
        father_inst_chain += '(%s)'%(cur_module_name)
        print_strs.append( '%d : %s'%(i, father_inst_chain) )
        # generate link
        c_mt_link_parm = {
              'Type'             : 'mt_trace'
             ,'go_module_name'   : None  # inline parm
             ,'go_inst_name'     : None  # inline parm
        }
        c_mt_link = BaseLib.gen_hyperlink(['go_module_inst_action'], c_mt_link_parm, Type = 'mt_trace')
        print_link.append( c_mt_link )
    mounted_list = BaseLib.MountPrintLines(print_strs, label = 'Module Trace', link_list=print_link)
    mounted_line_list = mounted_list['line_list']
    mounted_line_list.append('')
    mounted_line_list.append('')
    mounted_link_list = mounted_list['link_list']
    mounted_link_list.append({})
    mounted_link_list.append({})
    ViewLib.PrintReport(mounted_line_list, mounted_link_list, MountPrint = True )
    # ViewLib.edit_vim_buffer_and_file_link(G['Report_Inf']['Report_Path'], mounted_line_list)
    return

def try_print_module_trace():
    if not G['InlineActive']: return
    if G['Debug']:
        print_module_trace()
    else:
        try: print_module_trace()
        except: pass

# shortcut key: <Space><Left>
def trace_signal_sources():
    if G['IgnoreNextSpaceOp']:
        G['IgnoreNextSpaceOp'] = False
        BaseLib.PrintDebug('Trace: not do this trace source op ,bucause <space> is come from unknow reason !')
        return
    cursor_inf        = ViewLib.get_cur_cursor_inf()
    trace_signal_name = cursor_inf['word']
    if not trace_signal_name:
        ViewLib.PrintReport("Note: current cursor not on signal name, do-nothing !")
        return
    # case0: if cur cursor on a macro, go macro define
    if CodeLib.trace_glb_define_signal('source', cursor_inf): return
    # case1: if cur cursor on io signal, need cross to upper module
    if CodeLib.trace_io_signal('source', cursor_inf, report_level = 0 ): return
    # case2: if cur cursor on module call io line go to submodule io
    if CodeLib.trace_signal_at_subcall_lines('source', cursor_inf, report_level = 0 ): return
    # case3: trace signal same as pre trace signal, just show next result
    if (G['TraceInf']['LastTraceSource']['Path'] == cursor_inf['file_path']) \
        and (G['TraceInf']['LastTraceSource']['SignalName'] == trace_signal_name) \
        and (G['TraceInf']['LastTraceSource']['ValidLineRange'][0] <= cursor_inf['line_num']) \
        and (G['TraceInf']['LastTraceSource']['ValidLineRange'][1] >= cursor_inf['line_num']) :
        ViewLib.show_next_trace_result('source')
        BaseLib.PrintDebug('Trace: trace_signal_sources, just show next result!')
        return
    # case4: trace a new normal(not io, sub call io) signal
    if CodeLib.trace_normal_signal('source', cursor_inf): return

def try_trace_signal_sources():
    if not G['InlineActive']: return
    if G['Debug']:
        trace_signal_sources()
    else:
        try: trace_signal_sources()
        except: pass


# shortcut key: <Space><Right>
def trace_signal_destinations():
    if G['IgnoreNextSpaceOp']:
        G['IgnoreNextSpaceOp'] = False
        BaseLib.PrintDebug('Trace: not do this trace source op ,bucause <space> is come from unknow reason !')
        return
    cursor_inf = ViewLib.get_cur_cursor_inf()
    trace_signal_name = cursor_inf['word']
    if not trace_signal_name:
        ViewLib.PrintReport("Note: Current cursor not on signal name, can not trace dest!")
        return
    # case0: if cur cursor on io signal, need cross to upper module
    if CodeLib.trace_io_signal('dest', cursor_inf, report_level = 0 ): return
    # case1: if cur cursor on module call io line go to submodule io
    if CodeLib.trace_signal_at_subcall_lines('dest', cursor_inf): return
    # case2: trace signal same as pre trace signal, just show next result
    if (G['TraceInf']['LastTraceDest']['Path'] == cursor_inf['file_path']) \
        and (G['TraceInf']['LastTraceDest']['SignalName'] == trace_signal_name) \
        and (G['TraceInf']['LastTraceDest']['ValidLineRange'][0] <= cursor_inf['line_num']) \
        and (G['TraceInf']['LastTraceDest']['ValidLineRange'][1] >= cursor_inf['line_num']) :
        ViewLib.show_next_trace_result('dest')
        return
    # case3: if cur cursor on a macro, go macro define
    if CodeLib.trace_glb_define_signal('dest', cursor_inf): return
    # case4: trace a new normal(not io, sub call io) signal
    CodeLib.trace_normal_signal('dest', cursor_inf)

def try_trace_signal_destinations():
    if not G['InlineActive']: return
    if G['Debug']:
        trace_signal_destinations()
    else:
        try: trace_signal_destinations()
        except: pass


# shortcut key: <Space><Down> 
def roll_back():
    if G['IgnoreNextSpaceOp']:
        G['IgnoreNextSpaceOp'] = False
        BaseLib.PrintDebug('Trace: not do this trace source op ,bucause <space> is come from unknow reason !')
        return
    cur_nonius        = G['OpTraceInf']['Nonius'] - 1
    TracePoints       = G['OpTraceInf']['TracePoints']
    # if reach to the oldest trace point just return
    if cur_nonius < 0:
        ViewLib.PrintReport("Note: roll backed to the oldest trace point now !")
        return
    # go to the trace point
    cur_point = TracePoints[cur_nonius]
    G['OpTraceInf']['Nonius'] = cur_nonius
    ViewLib.go_win( cur_point['path'], cur_point['pos'], cur_point['key']) # no need logic to real
    return

def try_roll_back():
    if not G['InlineActive']: return
    if G['Debug']:
        roll_back()
    else:
        try: roll_back()
        except: pass


# shortcut key: <Space><Up> 
def go_forward():
    if G['IgnoreNextSpaceOp']:
        G['IgnoreNextSpaceOp'] = False
        BaseLib.PrintDebug('Trace: not do this trace source op ,bucause <space> is come from unknow reason !')
        return
    cur_nonius        = G['OpTraceInf']['Nonius'] + 1
    TracePoints       = G['OpTraceInf']['TracePoints']
    if cur_nonius >= len(TracePoints):
        ViewLib.PrintReport("Note: go forward to the newest trace point now !")
        return
    cur_point = TracePoints[cur_nonius]
    G['OpTraceInf']['Nonius'] = cur_nonius
    ViewLib.go_win( cur_point['path'], cur_point['pos'], cur_point['key']) # no need logic to real
    return

def try_go_forward():
    if not G['InlineActive']: return
    if G['Debug']:
        go_forward()
    else:
        try: go_forward()
        except: pass


# shortcut key: <space>
def space_operation():
    if G['IgnoreNextSpaceOp']:
        G['IgnoreNextSpaceOp'] = False
        BaseLib.PrintDebug('Trace: not do this trace source op ,bucause <space> is come from unknow reason !')
        return
    cursor_inf = ViewLib.get_cur_cursor_inf()
    # if cur in Frame or Report, show file link files
    if cursor_inf['file_path'] in [ G['Frame_Inf']['Frame_Path'], G['Report_Inf']['Report_Path'] ]:
        # bug fix if no link add before here will out of range
        cur_frame_link = {}
        if cursor_inf['line_num'] < len( G['VimBufferLineFileLink'][cursor_inf['file_path']] ):
            cur_frame_link = G['VimBufferLineFileLink'][cursor_inf['file_path']][cursor_inf['line_num']]
        ViewLib.add_trace_point()
        if not cur_frame_link:
            ViewLib.PrintReport('Note: No file link in current line ! ')
            return
        # for single_action_link
        if cur_frame_link['type'] == 'single_action_link':
            BaseLib.do_hyperlink(cur_frame_link)
            ViewLib.add_trace_point()
            return
        # for topo and base_module, need refresh
        if cur_frame_link['type'] in ['topo', 'base_module']:
            # need update module trace first
            if BaseLib.do_hyperlink(cur_frame_link, 'go_module_action'):
                BaseLib.do_hyperlink(cur_frame_link, 'add_to_module_trace')
            else:
                BaseLib.do_hyperlink(cur_frame_link, 'go_file_action')
                
            ViewLib.add_trace_point()
            return
        # for check_point
        if cur_frame_link['type'] == 'check_point':
            BaseLib.do_hyperlink(cur_frame_link, 'go_file_action')
            ViewLib.add_trace_point()
            return
        # for possible_upper
        if cur_frame_link['type'] == 'possible_upper':
            BaseLib.do_hyperlink(cur_frame_link, ['go_file_action', 'add_to_module_trace'])
            ViewLib.add_trace_point()
            return
        # for possible_trace_upper
        if cur_frame_link['type'] == 'possible_trace_upper':
            BaseLib.do_hyperlink(cur_frame_link, ['add_to_module_trace', 'trace_io_signal_action'])
            ViewLib.add_trace_point()
            return
        # for mt go inst action
        if cur_frame_link['type'] == 'mt_trace':
            l   = cursor_inf['line']
            x,y = cursor_inf['pos']
            #exp:"* 0 : a.b(b_inst).c(c_inst)  *
            l_split = l.split('.')
            # get pos position
            s_start = 0
            s_end   = -1
            x_idx   = 0
            for i,s in enumerate(l_split):
                s_end = s_start + len(s)
                if s_start <= y and y < s_end:
                    x_idx = i
                    break
                s_start = s_end + 1 # +1 for '.'
            # get each split's module and inst name
            m_i_list = []
            for i, s in enumerate(l_split):
                s = re.sub('.*:\s*','',s)
                s = re.sub('\s*\*\s*','',s).strip()
                if i == 0:
                    m_i_list.append( [None, s] )
                    continue
                m_inst = re.match('(?P<inst>.*)\((?P<mod>.*)\)' ,s)
                if not m_inst:
                    ViewLib.PrintReport('Warning: mt trace format error ! should be "a.i_b(m_b).i_c(m_c)...".')
                    return
                inst = m_inst.group('inst').strip()
                mod  = m_inst.group('mod').strip()
                m_i_list.append( [inst, mod] )
            if x_idx == 0:
                cur_frame_link['action_parm_dic']['go_module_name'] = m_i_list[x_idx][1]
                cur_frame_link['action_parm_dic']['go_inst_name']   = None
            else:
                cur_frame_link['action_parm_dic']['go_module_name'] = m_i_list[x_idx-1][1]
                cur_frame_link['action_parm_dic']['go_inst_name']   = m_i_list[x_idx][0]
            BaseLib.do_hyperlink(cur_frame_link, ['go_module_inst_action'])
            ViewLib.add_trace_point()
            return
    return

def try_space_operation():
    if not G['InlineActive']: return
    if G['Debug']:
        space_operation()
    else:
        try: space_operation()
        except: pass


# shortcut key: <Space>v
def show_frame():
    G["IgnoreNextSpaceOp"] = G['FixExtraSpace']
    if ViewLib.cur_in_frame():
        cursor_line = vim.current.window.cursor[0] - 1 
        FrameLib.frame_line_fold_operation(cursor_line)
    else:
        FrameLib.show_topo()
        FrameLib.show_check_point(False)
        FrameLib.show_base_module(False)
    return

def act_vtags_inline():
    if G['InlineActive']:
        return True
    if not os.path.isfile(vim.current.buffer.name):
        return False
    load_local_libs()
    real_path = FileInfLib.get_real_path(vim.current.buffer.name)
    if os.system("python %s/vtags.py -v %s +vtags_incdir+%s"%(G['InstallPath'], real_path, re.sub('[^/]*$', '', real_path.strip() ) )) != 0:
        BaseLib.PrintDebug("build vtags inline at current dir failed,use command replay: 1:'%s', 2:'%s' "%('cd '+os.getcwd(), "vtags -v "+ real_path))
        return False
    # build vtags.db at cur_dir success
    new_vtags_db = os.getcwd().rstrip('/') + '/vtags.db'
    if not os.path.isdir( new_vtags_db ):
        BaseLib.PrintDebug("build success, but not found vtags.db at '%s'" %(os.getcwd()))
        return False
    # reset glb
    new_G = GLB.init_G_from_vtagsDB( new_vtags_db, allow_from_glb = False )
    for key in new_G:
        G[key] = new_G[key]
    G['InlineActive']  = True
    return True

def try_show_frame():
    if not G['InlineActive']:
        if G['Debug']:
            act_vtags_inline()
        else:
            try   : act_vtags_inline()
            except: pass
        if not G['InlineActive']: return
    if G['Debug']:
        show_frame()
    else:
        try: show_frame()
        except: pass
    return


# shortcut key: <Space>h
def hold_current_win():
    cur_path = os.path.realpath(vim.current.buffer.name)
    # just del current win frome work win, then will not auto close current win
    for i,path in enumerate(G['WorkWin_Inf']['OpenWinTrace']):
        if cur_path == path:
            del G['WorkWin_Inf']['OpenWinTrace'][i]
            break

def try_hold_current_win():
    if not G['InlineActive']: return
    if G['Debug']:
        hold_current_win()
    else:
        try: hold_current_win()
        except: pass


# shortcut key: <Space>c
def add_check_point():
    G["IgnoreNextSpaceOp"] = G['FixExtraSpace']
    cursor_inf   = ViewLib.get_cur_cursor_inf()
    level        = G['CheckPointInf']['TopFoldLevel'] + 1 
    key          = G['Frame_Inf']['FoldLevelSpace']*level + cursor_inf['word']
    link_parm = {
         'Type'             : 'check_point'            # fold_unfold_frame_action()
        ,'fold_level'       : level                    # fold_unfold_frame_action() 
        ,'fold_status'      : 'fix'                    # fold_unfold_frame_action()
        ,'go_path'          : cursor_inf['file_path']  # go_file_action()
        ,'go_pos'           : cursor_inf['pos']        # go_file_action()
        ,'go_word'          : cursor_inf['word']       # go_file_action()
        ,'last_modify_time' : BaseLib.get_sec_mtime(cursor_inf['file_path'])
    }
    link = BaseLib.gen_hyperlink(['go_file_action', 'fold_unfold_frame_action'], link_parm, Type = 'check_point') # no need logic to real
    G['CheckPointInf']['CheckPoints'].insert(0, {'key': key, 'link': link })
    if len(G['CheckPointInf']['CheckPoints']) > G['CheckPointInf']['MaxNum']:
        del G['CheckPointInf']['CheckPoints'][-1]
    FrameLib.show_check_point()

def try_add_check_point():
    if not G['InlineActive']: return
    if G['Debug']:
        add_check_point()
    else:
        try: add_check_point()
        except: pass


# shortcut key: <Space>b
def add_base_module():
    G["IgnoreNextSpaceOp"] = G['FixExtraSpace']
    cursor_inf    = ViewLib.get_cur_cursor_inf()
    cursor_module = cursor_inf['word']
    if not cursor_module:
        ViewLib.PrintReport('Note: cursor not on a valid word ! ')
        return
    if cursor_module in G['BaseModuleInf']['BaseModules']:
        ViewLib.PrintReport('Note: module %s is already base module ! '%(cursor_module))
        return
    G['BaseModuleInf']['BaseModules'].add(cursor_module)
    FrameLib.update_base_module_pickle()
    FrameLib.show_base_module()
    FrameLib.refresh_topo()

def try_add_base_module():
    if not G['InlineActive']: return
    if G['Debug']:
        add_base_module()
    else:
        try: add_base_module()
        except: pass


# shortcut key: <Space>d
def del_operation():
    if not ViewLib.cur_in_frame():
        ViewLib.PrintReport('Note: Cur file no del function ! ')
        return
    cur_path      = os.path.realpath(vim.current.buffer.name)
    cur_line_num  = vim.current.window.cursor[0] - 1
    cur_file_link = G['VimBufferLineFileLink'][cur_path][cur_line_num]
    if not cur_file_link:
        ViewLib.PrintReport('Note: Cur line no del function ! ')
        return
    # delete a check point, if link has path means a valid link
    if (cur_file_link['action_parm_dic']['Type'] == 'check_point') and (cur_file_link['action_parm_dic']['fold_level'] > G['CheckPointInf']['TopFoldLevel']):
        G["IgnoreNextSpaceOp"] = G['FixExtraSpace']
        check_point_begin_line_num = FrameLib.get_frame_range_inf()['check_point_range'][0]
        del_index = cur_line_num - check_point_begin_line_num - 1
        del G['CheckPointInf']['CheckPoints'][ del_index ]
        FrameLib.show_check_point()
        return
    # del a base module
    if (cur_file_link['action_parm_dic']['Type'] == 'base_module') and (cur_file_link['action_parm_dic']['fold_level'] > G['BaseModuleInf']['TopFoldLevel']): 
        G["IgnoreNextSpaceOp"] = G['FixExtraSpace']
        G['BaseModuleInf']['BaseModules'].remove(cur_file_link['action_parm_dic']['go_module_name'])
        FrameLib.update_base_module_pickle()
        FrameLib.show_base_module()
        FrameLib.refresh_topo()
        return
    ViewLib.PrintReport('Note: Cur line no del function ! ')

def try_del_operation():
    if not G['InlineActive']: return
    if G['Debug']:
        del_operation()
    else:
        try: del_operation()
        except: pass

# shortcut key: <Space>s
def try_save_env_snapshort():
    if not G['InlineActive']: return
    if G['Debug']:
        if G['SaveEnvSnapshort_F']():
            ViewLib.PrintReport('Note: save env snapshort success !')
    else:
        try: 
            if G['SaveEnvSnapshort_F']():
                ViewLib.PrintReport('Note: save env snapshort success !')
        except: pass

# shortcut key: ct - clear all trace
def clear_trace():
    if not G['InlineActive']: return
    G['ModuleTrace'] = {}

def try_close_all_windows():
    if not G['InlineActive']: return
    ViewLib.close_all_windows()

# -------------------------------------------------------------------
def mopen(module_name):
    cur_module_inf = FileInfLib.get_module_inf(module_name)
    if not cur_module_inf:
        ViewLib.PrintReport('Note: module %s not found! \n'%(module_name))
        return False
    file_path = cur_module_inf['file_path']
    if not os.path.isfile(file_path):
        ViewLib.PrintReport('Note: module file %s not exist! \n'%(file_path))
        return False
    ViewLib.add_trace_point()
    ViewLib.go_win(file_path, cur_module_inf['module_name_sr']['range'], module_name)
    return True

# -------------------------------------------------------------------
if G['InlineActive']:
    # load local lib
    load_local_libs()
    # treat the first win as work win , if cur win is hdl code, and add first trace point
    first_cursor_inf = ViewLib.get_cur_cursor_inf()
    if first_cursor_inf['hdl_type'] == 'verilog':
        G['WorkWin_Inf']['OpenWinTrace'].append(first_cursor_inf['file_path'])
        ViewLib.add_trace_point()
elif G['LoadSnapShortPending']:
    reload_env_snapshort_full()
elif G["LoadTopModulePending"]:
    load_local_libs()
    top_list = FileInfLib.get_all_top_modules()
    if not top_list:
        os.system('echo \'Current vtags.db no top module found, vtags do nonthing ! \'')
    else:
        top_str = ''
        for i, top in enumerate(top_list):
            top_str += "\n%-4d: %s"%(i, top)
        os.system('echo \'----------------Top Module List-------------%s\nChoise Top Module To Open (0-%d): \''%(top_str, len(top_list)-1))
        if sys.version_info[0] < 3:
            top_idx_str = raw_input()
        else:
            top_idx_str = input()
        try:
            top_idx = int(top_idx_str)
        except:
            top_idx = -1
        if top_idx >= 0 and top_idx < len(top_list):
            top_module = top_list[top_idx]
            cur_module_inf = FileInfLib.get_module_inf(top_module)
            if cur_module_inf:
                file_path = cur_module_inf['file_path']
                if os.path.isfile(file_path):
                    ViewLib.go_win(file_path, cur_module_inf['module_name_sr']['range'], top_module)
                    G['InlineActive'] = True
                    ViewLib.close_other_windows()
                else:
                    os.system('echo \'Error: module "%s" at "%s" not found, please generate vtags.db and try again, vtags do nonthing ! \''%(top_module, file_path))
            else:
                os.system('echo \'Error: module "%s" inf in vtags.db not full, please generate vtags.db and try again, vtags do nonthing ! \''%(top_module))
        else:
            os.system('echo \'Top Module number "%s" illegal, vtags do nonthing ! \''%(top_idx_str))



