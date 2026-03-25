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
import copy
import Lib.GLB as GLB
G = GLB.G
from Lib.BaseLib import *
from InlineLib.ViewLib import *
import Lib.FileInfLib as FileInfLib

def replace_note_and_no_bracket_level_one_code(line):
    pre_asterisk         = 0
    pre_backslash        = 0
    cur_backslash        = 0
    cur_asterisk         = 0
    cur_quote            = 0
    in_single_line_notes = 0
    in_multi_line_notes  = 0
    in_string            = 0
    bracket_level        = 0
    pure_line            = ''
    for y,c in enumerate(line):
        # deal notes
        cur_backslash = 0
        cur_asterisk  = 0
        if(c == '/'):
            cur_backslash = 1
        elif (c == '*'):
            cur_asterisk  = 1
        # match "//"
        if ( not in_multi_line_notes and pre_backslash and cur_backslash):
            in_single_line_notes = 1
            pure_line += c 
            continue
        # match "/*"
        if ( not in_single_line_notes and pre_backslash and cur_asterisk):
            in_multi_line_notes  = 1
            pure_line += '/' # replace note to '/'
            continue
        # match "*/"
        if (pre_asterisk and cur_backslash and in_multi_line_notes):
            in_multi_line_notes = 0
            pure_line += '/'  # replace note to '/'
            continue
        # match '\n'
        if (c == '\n' and in_single_line_notes):
            in_single_line_notes = 0
            pure_line += c
            continue
        pre_backslash = cur_backslash
        pre_asterisk  = cur_asterisk
        # deal string
        if not (in_single_line_notes or in_multi_line_notes):
            if   not in_string and (c == '"'):
                in_string = 1
            elif in_string and (c == '"'):
                in_string = 0
        # get bracket level
        if not (in_single_line_notes or in_multi_line_notes or in_string):
            if c == "(":
                bracket_level += 1
            elif c == ")":
                bracket_level -= 1
                if bracket_level < 0:
                    # PrintReport("Warning: code ')' no corresponding '(' ! '%s' "%(y, line[:y+1].split('\n')[-1]))
                    bracket_level = 0 # just clear bracket_level and continue
                    pure_line += c
                    continue
        # get pure code
        if (in_single_line_notes | in_multi_line_notes):
            pure_line += ' '
        elif in_string:
            pure_line += '"'  # all """ means in string
        elif bracket_level != 0:
            pure_line += '('  # all "((" means in bracket
        elif c == '\n':
            pure_line += '\\'
        else:
            pure_line += c
    return pure_line

def current_appear_is_dest_or_source(key, code_y):
    code_line, y = code_y
    # if y is not at char 
    if (len(code_line) <= y) or (not re.match('\w', code_line[y])):
        return 'unknown'
    pure_line = replace_note_and_no_bracket_level_one_code(code_line)
    assert( len(pure_line) == len(code_line) )
    # if y is in notes, or string
    if pure_line[y] == '/' or pure_line[y] == '"':
        return 'unknown' 
    # if in condition bracket is dest
    if pure_line[y] == '(' and re.search("(\W|^)(if|case|casez|casex|for)\s*\(*", pure_line[:y]):
        return 'dest'
    # if form current pos to next ';' if has "=" or "<=";
    # PrintDebug(': %d:\n->%s\n->%s'%(y, code_line, pure_line[:y]))
    if re.search('(([^=>]|^)=([^=<]+|$)|<=)', pure_line[y:]):
        return 'source'
    # if key =/<= ...
    if re.search('(([^=]|^)=([^=]+|$)|<=)', pure_line[:y]):
        return 'dest'
    return 'unknown'

def clear_last_trace_inf( trace_type = 'both' ):
    trace_type = 'both' # i thing each time clear all is much more friendly
    if trace_type in ['source','both']:
        G['TraceInf']['LastTraceSource']['Maybe']          = []
        G['TraceInf']['LastTraceSource']['Sure']           = []
        G['TraceInf']['LastTraceSource']['ShowIndex']      = 0
        G['TraceInf']['LastTraceSource']['SignalName']     = ''
        G['TraceInf']['LastTraceSource']['ValidLineRange'] = [-1,-1]
        G['TraceInf']['LastTraceSource']['Path']           = ''
    if trace_type in ['dest','both']:
        G['TraceInf']['LastTraceDest']['Maybe']            = []
        G['TraceInf']['LastTraceDest']['Sure']             = []
        G['TraceInf']['LastTraceDest']['ShowIndex']        = 0
        G['TraceInf']['LastTraceDest']['SignalName']       = ''
        G['TraceInf']['LastTraceDest']['ValidLineRange']   = [-1,-1]
        G['TraceInf']['LastTraceDest']['Path']             = ''


def first_word_in_range( codes , in_range ):
    code_l = len(codes)
    start_l, start_c, end_l, end_c = in_range
    s = ''
    x_offset = 0
    y_offset = 0
    for l_i in range( start_l, end_l + 1 ):
        if l_i >= code_l:
            break
        l = codes[l_i]
        if l_i == start_l:
            l = ' '*(start_c) + l[start_c:]
        if l_i == end_l:
            l = l[:end_c+1]
        search_word = re.search('\w+', l)
        if search_word:
            y_offset = search_word.span()[0]
            return ( (x_offset, y_offset) ,search_word.group())
        x_offset += 1
    return ((x_offset, y_offset), '')

# typedef enum io_type {
#       NOT_IO   = 0
#     , INPUT    = 1
#     , OUTPUT   = 2
#     , INOUT    = 3
# }IOType;
# this function trace the signal when need crose module from
# submodule io line to upper module subcall line
def trace_io_signal(trace_type, cursor_inf, report_level = 1):
    trace_signal_name  = cursor_inf['word']
    module_io_inf      = FileInfLib.get_module_io_inf_from_pos(cursor_inf["file_path"], cursor_inf['pos'])
    io_inf             = module_io_inf["io_inf"]
    if not io_inf:
        PrintDebug('Trace: trace_io_signal: not io signal')
        return False # not io signal
    # check io type and trace type
    if (trace_type is 'dest') and (io_inf["type"] == 1):
        PrintDebug('Trace: trace_io_signal: not output signal, not dest')
        return False # not output signal, not dest
    if (trace_type is 'source') and (io_inf["type"] == 2):
        PrintDebug('Trace: trace_io_signal: not input signal, not source')
        return False # not input signal, not source
    # clear pre trace dest/source result
    clear_last_trace_inf( trace_type )  
    # get module's father check value
    father_inst_list  = []
    cur_module_name   = module_io_inf["module_inf"]["module_name_sr"]['str']
    # 1. check module trace
    trace_father_inst = FileInfLib.track_module_trace(cur_module_name)
    if trace_father_inst:
        father_inst_list.append( trace_father_inst )
    # 2. if not 1, get all father inst location
    if not trace_father_inst:
        father_inst_list = FileInfLib.get_father_inst_list(cur_module_name)
    if not father_inst_list:
        PrintReport("Note: module:'%s' IO:'%s', no father module !"%(cur_module_name, io_inf["name_sr"]['str']))
        return True
    # 3. if only one choise father inst, do trace
    if len(father_inst_list) == 1:
        father_module_name, inst_name = father_inst_list[0].split('.')
        father_inst_cnt_inf = FileInfLib.get_module_inst_iocnt_inf(father_module_name, inst_name, io_inf["name_sr"]['str'], io_inf['idx'])
        if not father_inst_cnt_inf["iocnt_inf"]:
            PrintReport("Note: module:'%s' IO:'%s', no connect found at %s!"%(cur_module_name, io_inf["name_sr"]['str'], father_inst_list[0]))
            return True
        father_module_inf    = father_inst_cnt_inf["module_inf"]
        father_module_name   = father_module_inf["module_name_sr"]["str"]
        iocnt_inf            = father_inst_cnt_inf["iocnt_inf"]
        logic_cnt_name_range = iocnt_inf["cnt_name_range"]
        # need logic to real
        real_location = FileInfLib.location_l2r(logic_cnt_name_range, father_module_inf['code_inf_list'])
        if not real_location:
            PrintReport("Note: get iocnt location %s failed ! file: '%s' "%(logic_cnt_name_range, father_module_inf["file_path"]))
            PrintDebug("ERROR: logic to real failed ! iocnt_inf=%s father_module_inf=%s "%(iocnt_inf, father_module_inf))
            return True
        l2roffset = logic_cnt_name_range[0] - real_location['pos'][0]
        real_cnt_name_range = [ logic_cnt_name_range[0]-l2roffset, logic_cnt_name_range[1], logic_cnt_name_range[2]-l2roffset, logic_cnt_name_range[3] ]
        # read lines        
        father_module_codes = read_file_lines(real_location['path'], real_cnt_name_range[0], real_cnt_name_range[2])
        relative_range      = [0, real_cnt_name_range[1], real_cnt_name_range[2] - real_cnt_name_range[0], real_cnt_name_range[3]]
        if not father_module_codes:
            PrintReport("Note: file read connect line %d-%d failed ! file: '%s' "%(real_cnt_name_range[0], real_cnt_name_range[2], father_module_inf["file_path"]))
            return True
        show_str            = '%s %d : %s'%(father_module_name, real_cnt_name_range[0]+1, father_module_codes[0] )
        go_word_offset, go_word = first_word_in_range(father_module_codes, relative_range)
        file_link_parm_dic  = { 'type'             : 'trace_result'
                               ,'last_modify_time' : get_sec_mtime( real_location['path'] )
                               ,'go_path'          : real_location['path']
                               ,'go_pos'           : [ real_location['pos'][0] + go_word_offset[0], go_word_offset[1]] # go_word_offset[1] is calum pos
                               ,'go_word'          : go_word }
        # PrintDebug(":%s"%([file_link_parm_dic, father_module_codes, relative_range, real_location['path'], real_cnt_name_range, logic_cnt_name_range]))
        file_link           = gen_hyperlink('go_file_action', file_link_parm_dic) # logic to real
        trace_result        = {'show': show_str, 'file_link': file_link}
        if trace_type is 'dest':
            G['TraceInf']['LastTraceDest']['Sure'].append(trace_result)
            G['TraceInf']['LastTraceDest']['SignalName']       = cursor_inf['word']
            G['TraceInf']['LastTraceDest']['ValidLineRange']   = module_io_inf["module_inf"]['module_line_range']
            G['TraceInf']['LastTraceDest']['Path']             = cursor_inf['file_path']
        else :
            G['TraceInf']['LastTraceSource']['Sure'].append(trace_result)
            G['TraceInf']['LastTraceSource']['SignalName']     = cursor_inf['word']
            G['TraceInf']['LastTraceSource']['ValidLineRange'] = module_io_inf["module_inf"]['module_line_range']
            G['TraceInf']['LastTraceSource']['Path']           = cursor_inf['file_path']
        # show dest/source to report win, and go first trace
        PrintReport(spec_case = trace_type)
        show_next_trace_result(trace_type)
        return True
    # has mulity father list all of it and, user choise
    link_list = []
    line_list = []
    # pre inf
    line_list.append('Knock "<Space>" to choise upper module you want trace to: ')
    line_list.append('')
    link_list.append( {} )
    link_list.append( {} )
    for i,father_inst in enumerate(father_inst_list):
        c_file_link_parm_dic    = {  'type'                : 'possible_trace_upper'
                                    # for trace_io_signal_action
                                    ,'trace_type'          : trace_type
                                    ,'cursor_inf'          : cursor_inf
                                    ,'report_level'        : report_level
                                    # for add_to_module_trace
                                    ,'module_name'         : cur_module_name
                                    ,'father_inst'         : father_inst }
        c_file_link_parm_dic['cursor_inf']['codes'] = None # fix bug for vim.buffer cannot pickle when <Space>+s
        c_file_link = gen_hyperlink(['add_to_module_trace', 'trace_io_signal_action'], c_file_link_parm_dic, 'possible_trace_upper')
        link_list.append(c_file_link)
        c_print_str = '%d : %s(%s)'%(i, father_inst, cur_module_name)
        line_list.append(c_print_str)
    mounted_line_inf  = MountPrintLines(line_list, label = 'Possible Trace Upper', link_list = link_list)
    mounted_line_list = mounted_line_inf['line_list']
    mounted_link_list = mounted_line_inf['link_list']
    # add a empty line below
    mounted_line_list.append('')
    mounted_link_list.append({})
    add_trace_point()
    assert( len(mounted_line_list) == len(mounted_link_list) )
    PrintReport(mounted_line_list, mounted_link_list, MountPrint = True )
    # len(mounted_line_list) + 1 is the lines relative to the last report line
    # -4 is skip first 4 unused line
    go_win( G['Report_Inf']['Report_Path'] , (-(len(mounted_line_list) + 1 -4), 57) ) # no need logic to real
    return True # this dest/source but not found upper module

# hyperlink action trace_io_signal_action
def trace_io_signal_action(trace_type, cursor_inf, report_level):
    trace_io_signal(trace_type, cursor_inf, report_level)
register_hyperlink_action( trace_io_signal_action, description = 'this link function use to trace input cursor io ' )


# NOT_IO   = 0
# INPUT    = 1
# OUTPUT   = 2
# INOUT    = 3
# this function used to trace signal at subcall lines 
def trace_signal_at_subcall_lines(trace_type, cursor_inf, report_level = 1):
    module_inst_cnt_sub_inf = FileInfLib.get_module_inst_cnt_sub_inf_from_pos(cursor_inf['file_path'], cursor_inf['pos'])
    if not module_inst_cnt_sub_inf["inst_inf"]:
        PrintDebug('Trace: trace_signal_at_subcall_lines: cursor not at subcall lines !')
        return False # not in module call io
    if not module_inst_cnt_sub_inf["cnt_sub_inf"]:
        PrintDebug('Trace: trace_signal_at_subcall_lines: is module call , no connect subio found!')
        return False    
    # start add sub io trace inf
    cnt_sub_inf = module_inst_cnt_sub_inf["cnt_sub_inf"]
    assert(trace_type in ['source', 'dest'])
    if trace_type == 'source' and cnt_sub_inf['type'] == 1:
        return False # submodule not source, just pass
    elif trace_type == 'dest' and cnt_sub_inf['type'] == 2:
        return False # submodule not source, just pass
    # must a trace no matter success or not clear old trace result 
    clear_last_trace_inf( trace_type )
    # has sub module and in submodule signal is out, then it's source
    submodule_name      = cnt_sub_inf['module_name_sr']['str']
    submodule_path      = cnt_sub_inf['file_path']
    subio_name          = cnt_sub_inf['name_sr']['str']
    subio_range         = cnt_sub_inf['name_sr']['range']
    subio_line          = read_file_line(submodule_path, subio_range[0])
    show_str            = '%s %d : %s'%(submodule_name, subio_range[0], subio_line)
    # need logic to real
    real_location = FileInfLib.location_l2r(subio_range, cnt_sub_inf['module_inf']['code_inf_list'])
    if not real_location:
        PrintReport("Warning: IO:'%s' not found at file %s"%(subio_name, submodule_path))
        PrintDebug("ERROR: trace_signal_at_subcall_lines: logic to real failed ! cnt_sub_inf=%s"%(cnt_sub_inf))
        return True
    file_link_parm_dic  = { 'type'             : 'trace_result'
                           ,'last_modify_time' : get_sec_mtime( real_location['path'] )
                           ,'go_path'          : real_location['path']
                           ,'go_pos'           : real_location['pos']
                           ,'go_word'          : subio_name }
    file_link           = gen_hyperlink('go_file_action', file_link_parm_dic) # logic to real
    trace_result        = {'show': show_str, 'file_link': file_link}
    if trace_type == 'source':
        G['TraceInf']['LastTraceSource']['Sure'].append(trace_result)
        G['TraceInf']['LastTraceSource']['SignalName']     = cursor_inf['word']
        G['TraceInf']['LastTraceSource']['ValidLineRange'] = ( cursor_inf['line_num'], cursor_inf['line_num'] )
        G['TraceInf']['LastTraceSource']['Path']           = cursor_inf['file_path']
    else: # dest
        G['TraceInf']['LastTraceDest']['Sure'].append(trace_result)
        G['TraceInf']['LastTraceDest']['SignalName']     = cursor_inf['word']
        G['TraceInf']['LastTraceDest']['ValidLineRange'] = ( cursor_inf['line_num'], cursor_inf['line_num'] )
        G['TraceInf']['LastTraceDest']['Path']           = cursor_inf['file_path']
    # will go to sub module code now, so cur module is the sub module last call
    FileInfLib.add_to_module_trace(submodule_name, '%s.%s'%(module_inst_cnt_sub_inf["module_inf"]["module_name_sr"]['str'], 
                                                 module_inst_cnt_sub_inf["inst_inf"]["inst_name_sr"]['str']))
    # show source to report win, and go first trace
    PrintReport(spec_case = trace_type)
    show_next_trace_result(trace_type)
    return True

def update_inline_code_inf(file_path, codes = None):
    last_modify_time = get_sec_mtime(file_path)
    if file_path in G["InLineCodeInfDic"]:
        # check valid
        if last_modify_time == G["InLineCodeInfDic"][file_path]["last_modify_time"]:
            return
    # need add new
    if codes == None:
        codes = open(file_path,'r').readlines()
    G["InLineCodeInfDic"][file_path] = { 'codes': codes, "last_modify_time":last_modify_time }
    return

def read_file_lines(file_path, start_x, end_x):
    update_inline_code_inf(file_path)
    if file_path not in G["InLineCodeInfDic"]:
        return []
    codes              = G["InLineCodeInfDic"][file_path]['codes']
    return codes[start_x:end_x+1]

def read_file_line(file_path, x):
    update_inline_code_inf(file_path)
    if file_path not in G["InLineCodeInfDic"]:
        return ''
    codes              = G["InLineCodeInfDic"][file_path]['codes']
    if x < 0 or (x > len(codes) - 1):
        PrintReport("Warning: read line num:%d out of file line range, file:%s !"%(x,file_path))
        return ''
    return codes[x].rstrip('\n')

def get_code_logic_full_line(file_path, pos, logic_line_boundry_list_list):
    update_inline_code_inf(file_path)
    if file_path not in G["InLineCodeInfDic"]:
        return '', 0
    codes              = G["InLineCodeInfDic"][file_path]['codes']

    x,y = pos

    line_range = [x,x]
    stop       = 0
    for line_boundry_list in logic_line_boundry_list_list:
        if stop:
            break
        for line_boundry in line_boundry_list:
            if stop:
                break
            line_start        = line_boundry[0]    # include
            line_offset       = line_boundry[1]
            line_repeat_times = line_boundry[2]
            line_end          = line_start - 1 + line_offset * line_repeat_times # include
            if line_end < x:
                continue
            if line_start > x: # signal line
                stop       = 1
                break
            # match start to end
            for i in range(line_start, line_end+1, line_offset):
                if (i <= x) and (x < i + line_offset):
                    line_range = [i, i + line_offset -1]
                    stop       = 1
                    break
                continue
    # clean first line
    logic_lines       = copy.deepcopy(codes[line_range[0]:line_range[1]+1])
    logic_line        = ''.join(logic_lines)
    new_y             = 0
    for i,l in enumerate(logic_lines):
        if i < x - line_range[0]:
            new_y += len(l)
        elif i == x - line_range[0]:
            new_y += y
            break
    # PrintDebug('%s: %d : "%s"'%(pos, new_y, logic_line))
    return logic_line, new_y

def trace_normal_signal(trace_type, cursor_inf):
    cur_module_inf = FileInfLib.get_module_inf_from_pos(cursor_inf['file_path'], cursor_inf['pos'])["module_inf"]
    if not cur_module_inf:
        PrintDebug('Trace: cur file has no module inf, may be no database or cur line not in module, file: %s '%(cursor_inf['file_path']))
        return False
    assert(trace_type in ['source', 'dest'])
    trace_signal_name      = cursor_inf['word']
    cur_module_name        = cur_module_inf['module_name_sr']['str']
    cur_module_path        = cur_module_inf['file_path']
    # initial the trace inf
    clear_last_trace_inf(trace_type)
    if trace_type == 'source':
        G['TraceInf']['LastTraceSource']['SignalName']     = trace_signal_name
        G['TraceInf']['LastTraceSource']['ValidLineRange'] = cur_module_inf['module_line_range']
        G['TraceInf']['LastTraceSource']['Path']           = cur_module_path
    else: 
        G['TraceInf']['LastTraceDest']['SignalName']       = trace_signal_name
        G['TraceInf']['LastTraceDest']['ValidLineRange']   = cur_module_inf['module_line_range']
        G['TraceInf']['LastTraceDest']['Path']             = cur_module_path
    # first add io map to module_inf
    if 'io_name_to_io_inf_map' not in cur_module_inf:
        io_name_to_io_inf_map = {}
        for io_inf in cur_module_inf["io_inf_list"]:
            io_name_to_io_inf_map[io_inf['name_sr']['str']] = io_inf
        cur_module_inf['io_name_to_io_inf_map'] = io_name_to_io_inf_map
    io_is_only_result = False
    if trace_signal_name in cur_module_inf['io_name_to_io_inf_map']:
        cur_io_inf = cur_module_inf['io_name_to_io_inf_map'][trace_signal_name]
        if ( (trace_type == 'source') and (cur_io_inf['type'] == 1) ) or \
           ( (trace_type == 'dest'  ) and (cur_io_inf['type'] == 2) ):
            io_is_only_result = (trace_type == 'source')
            # need logic to real
            real_location = FileInfLib.location_l2r(cur_io_inf['name_sr']['range'], cur_module_inf['code_inf_list'])
            if not real_location:
                PrintReport("Warning: IO:'%s' not found at file %s"%(trace_signal_name, cur_module_path))
                PrintDebug("ERROR: trace_normal_signal: logic to real failed ! cur_io_inf=%s, cur_module_inf=%s"%(cur_io_inf, cur_module_inf))
                return True
            io_line  = read_file_line( real_location['path'], real_location['pos'][0])
            show_str = '%s %d : %s'%(cur_module_name, cur_io_inf['name_sr']['range'][0]+1, io_line)
            file_link_parm_dic = {   'type'             : 'trace_result'
                                    ,'last_modify_time' : get_sec_mtime( real_location['path'] )
                                    ,'go_path'          : real_location['path']
                                    ,'go_pos'           : real_location['pos']
                                    ,'go_word'          : trace_signal_name }
            file_link    = gen_hyperlink('go_file_action', file_link_parm_dic) # logic to real
            trace_result = {'show': show_str, 'file_link': file_link}
            if trace_type == 'source':
                G['TraceInf']['LastTraceSource']['Sure'].append(trace_result)
            else:
                G['TraceInf']['LastTraceDest']['Sure'].append(trace_result)
    # if found a io as result
    if not io_is_only_result:
        # just use grep get all signal appear in current logic file to speed up signal search
        #   1. get real file code block for module
        signal_appear_pos_line = []
        #   2. merge search real line
        path_range_map   = {}
        line_boundry_map = {}
        for code_inf in cur_module_inf['code_inf_list']:
            if code_inf['file_path'] not in path_range_map:
                path_range_map[ code_inf['file_path'] ]    = copy.deepcopy( code_inf['real_line_range'] )
                line_boundry_map[ code_inf['file_path'] ]  = [ code_inf['real_code_line_boundry'] ]
            else:
                assert( path_range_map[ code_inf['file_path'] ][1] <= code_inf['real_line_range'][1] )
                path_range_map[ code_inf['file_path'] ][1] = code_inf['real_line_range'][1]
                line_boundry_map[ code_inf['file_path'] ].append( code_inf['real_code_line_boundry'] )
        for path in path_range_map:
            signal_appear_pos_line += search_verilog_code_use_grep( cursor_inf['word'], path, path_range_map[path] )
        # appear_pos (line number, column), deal each match to find source
        for appear_path, appear_pos, appear_line in signal_appear_pos_line:
            appear_dest_or_source     = False
            appear_is_dest            = False
            appear_is_source          = False
            submodule_and_subinstance = ''
            type_known                = False
            # io already checked continue
            if re.search('(\W|^)(input|output|inout)(\W)', get_valid_code(appear_line) ):
                continue
            module_inst_cnt_sub_inf = FileInfLib.get_module_inst_cnt_sub_inf_from_pos(appear_path, appear_pos)
            inst_inf = module_inst_cnt_sub_inf['inst_inf']
            if inst_inf:
                type_known  = True
                submodule_and_subinstance = ':%s(%s)'%(inst_inf['inst_name_sr']['str'], inst_inf['submodule_name_sr']['str'])
                cnt_sub_inf = module_inst_cnt_sub_inf['cnt_sub_inf']
                if not cnt_sub_inf:
                    appear_dest_or_source = True
                else:
                    io_type = cnt_sub_inf['type']
                    if io_type != 1: # input not source
                        appear_is_source = True
                    if io_type != 2: # output not dest
                        appear_is_dest   = True
            # check is
            if not type_known:
                dest_or_source = current_appear_is_dest_or_source( trace_signal_name, get_code_logic_full_line(appear_path, appear_pos, line_boundry_map[appear_path]))
                # PrintDebug(': trace_signal_name=%s ,appear_path=%s, appear_pos=%s, dest_or_source = %s'%(trace_signal_name,appear_path ,appear_pos, dest_or_source))
                if dest_or_source   == 'source':
                    appear_is_source = True
                elif dest_or_source == 'dest':
                    appear_is_dest   = True
                elif dest_or_source == 'unknown':
                    appear_dest_or_source = True
            # not assign signal check module call
            assert(appear_is_source or appear_is_dest or appear_dest_or_source),'appear: "%s" must be some case !'%(appear_line)
            assert( not ((appear_is_source or appear_is_dest) and appear_dest_or_source) ),'appear: "%s" if is dest or source , should not be maybe'%(appear_line)
            # finial add to source/dest
            show_str = '%s %d : %s'%(cur_module_name+submodule_and_subinstance, appear_pos[0]+1, appear_line)
            file_link_parm_dic = {  'type'               : 'trace_result'
                                    ,'last_modify_time'  : get_sec_mtime( appear_path )
                                    ,'go_path'           : appear_path
                                    ,'go_pos'            : appear_pos
                                    ,'go_word'           : trace_signal_name }
            file_link    = gen_hyperlink('go_file_action', file_link_parm_dic) # on need logic to real
            trace_result = {'show': show_str, 'file_link': file_link}
            if trace_type == 'source':
                if appear_dest_or_source:
                    G['TraceInf']['LastTraceSource']['Maybe'].append(trace_result)
                elif appear_is_source:
                    G['TraceInf']['LastTraceSource']['Sure'].append(trace_result)
            else: # trace dest
                if appear_dest_or_source:
                    G['TraceInf']['LastTraceDest']['Maybe'].append(trace_result)
                elif appear_is_dest:
                    G['TraceInf']['LastTraceDest']['Sure'].append(trace_result)
            continue
    # finish get all dest/source
    if trace_type == 'source':
        finded_source_num       = len(G['TraceInf']['LastTraceSource']['Sure'])
        finded_maybe_source_num = len(G['TraceInf']['LastTraceSource']['Maybe'])
        # not find signal source
        if not (finded_source_num + finded_maybe_source_num):
            PrintReport("Note: Not find signal source !")
            return True
    else: # dest
        finded_dest_num       = len(G['TraceInf']['LastTraceDest']['Sure'])
        finded_maybe_dest_num = len(G['TraceInf']['LastTraceDest']['Maybe'])
        # not find signal dest
        if not (finded_dest_num + finded_maybe_dest_num):
            PrintReport("Note: Not find signal dest !")
            return True
    # show source to report win, and go first trace
    PrintReport(spec_case = trace_type)
    show_next_trace_result(trace_type)
    return True

# this function used to trace macro
def trace_glb_define_signal(trace_type, cursor_inf):
    assert(trace_type in ['dest', 'source'])
    cur_word  = cursor_inf['word']
    cur_line  = cursor_inf['line']
    if cur_line.find('`') == -1: # bucause most case not trace macro, so it's worth pre check
        PrintDebug('Trace: trace_glb_define_signal: %s not macro_name !'%(cur_word))
        return False
    # ...`XXX...
    #      ^        cursor pos
    #     XXX       cur word
    # ...`XX        pre_pos_part
    pre_pos_part = cur_line[:cursor_inf['pos'][1] + 1]
    match_macro  = re.match('\w+`' , pre_pos_part[::-1])
    if not match_macro:
        PrintDebug('Trace: trace_glb_define_signal: %s not macro_name !'%(cur_word))
        return False
    # no matter get trace result or not trace done, need clear old trace result
    clear_last_trace_inf(trace_type)
    # cur_word is macro get macro inf list
    macro_inf = FileInfLib.get_macro_inf( cur_word )
    if not macro_inf:
        PrintReport('Warning: not find macro: %s define in design !'%(cur_word))
        return True
    # if trace_type == 'dest': for macro no dest just source
    if trace_type == 'dest':
        PrintReport('None: macro: %s can not trace dest, only support trace source !'%(cur_word))
        return True
    # valid trace macro source
    file_name    = re.sub('.*/', '', macro_inf['file_state']['file_path'])
    line_num     = macro_inf['name_sr']["range"][0]
    code_line    = read_file_line(macro_inf['file_state']['file_path'], line_num)
    show_str     = '%s %d : %s'%(file_name, line_num+1, code_line)
    file_link_parm_dic  = { 'type'             : 'trace_result'
                           ,'last_modify_time' : macro_inf["file_state"]["last_modify_time"]
                           ,'go_path'          : macro_inf["file_state"]['file_path']
                           ,'go_pos'           : macro_inf['name_sr']["range"]
                           ,'go_word'          : cur_word }
    file_link           = gen_hyperlink('go_file_action', file_link_parm_dic) # no need logic to real
    trace_result = {'show': show_str, 'file_link': file_link}
    G['TraceInf']['LastTraceSource']['SignalName']     = cursor_inf['word']
    G['TraceInf']['LastTraceSource']['ValidLineRange'] = (cursor_inf['line_num'], cursor_inf['line_num'])
    G['TraceInf']['LastTraceSource']['Path']           = cursor_inf['file_path']
    G['TraceInf']['LastTraceSource']['Sure'].append(trace_result)
    # show source to report win, and go first trace
    PrintReport(spec_case = trace_type)
    show_next_trace_result(trace_type)
    return True

def get_father_inst_line_and_link_list( cur_module_name ):
    father_inst_list = FileInfLib.get_father_inst_list( cur_module_name )
    if father_inst_list:
        link_list = []
        line_list = []
        for i, father_inst in enumerate(father_inst_list):
            c_file_link          = None
            c_print_str          = None
            father, inst         = father_inst.split('.')
            father_inst_inf      = FileInfLib.get_module_inst_inf(father, inst)
            if not father_inst_inf["inst_inf"]:
                continue
            # logic to real 
            real_location = FileInfLib.location_l2r(father_inst_inf["inst_inf"]['inst_name_sr']['range'], father_inst_inf["module_inf"]['code_inf_list'])
            if not real_location:
                PrintDebug("ERROR: get_father_inst_line_and_link_list: real_location failed! inst_inf=%s, module_inf = %s"%(father_inst_inf["inst_inf"].__str__(), father_inst_inf["module_inf"].__str__()))
                continue
            c_file_link_parm_dic    = {  'type'                : 'possible_upper'
                                        # for go_file_action
                                        ,'last_modify_time'    : get_sec_mtime(real_location['path'])
                                        ,'go_path'             : real_location['path']
                                        ,'go_pos'              : real_location['pos']
                                        ,'go_word'             : father_inst_inf["inst_inf"]['inst_name_sr']['str'] 
                                        # for add_to_module_trace
                                        ,'module_name'         : cur_module_name
                                        ,'father_inst'         : father_inst }

            c_file_link = gen_hyperlink(['go_file_action', 'add_to_module_trace'], c_file_link_parm_dic, 'possible_upper') # logic to real 
            c_print_str = '%d : %s(%s)'%(i, father_inst, cur_module_name)
            link_list.append( c_file_link )
            line_list.append( c_print_str )
        if not link_list:
            return {}
        return {"line_list":line_list, 'link_list':link_list}
    return {}
