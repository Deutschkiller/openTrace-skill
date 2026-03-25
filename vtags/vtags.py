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
__version__ = "3.11"
__project_url__ = "http://www.vim.org/scripts/script.php?script_id=5494"

import os
import sys
import re
import pickle
import time # debug

# import vtags global config module
import Lib.GLB as GLB
G = GLB.G
# initial G
new_G = GLB.init_G_from_vtagsDB(allow_from_glb = True)
for key in new_G:
    G[key] = new_G[key]

#-------------------------------------------------------------------------------
#print help
#-------------------------------------------------------------------------------
help = ''
try:
    help = sys.argv[1]
except:
    pass

#-------------------------------------------------------------------------------
# Offline function
#-------------------------------------------------------------------------------
import OfflineLib.OfflineFuncLib as OfflineFuncLib
parm_str = ' '.join(sys.argv[1:])
if re.search('\(.*\)' , parm_str):
    OfflineFuncLib.function_run( parm_str )
    exit()

#-------------------------------------------------------------------------------
# when run vtags.py, create a folder named vtag.db at current dir
# and also rm the old vtags_db.log if exist.
#-------------------------------------------------------------------------------
vtags_db_folder_path = os.getcwd() + '/vtags.db'
GLB.vtags_db_log_path[0] = vtags_db_folder_path + '/vtags_db.log'

#-------------------------------------------------------------------------------
# import lib used in generate vtags.db
#-------------------------------------------------------------------------------
from Lib.BaseLib import *
import Lib.FileInfLib as FileInfLib

#-------------------------------------------------------------------------------
# print help information
#-------------------------------------------------------------------------------
if help in ['-h','-help']:
    help_str_list = []
    help_str_list.append("Version: %s, URL:%s"%(__version__, __project_url__))
    help_str_list.append("(1) build vtags at code dir, use command:")
    help_str_list.append("    \"vtags\"                     - build code at current dir"          )
    help_str_list.append("    \"<filepath>\"                - build code for current file at cur dir")
    help_str_list.append("    \"-f <filelist>\"             - build code from vcs/verdi file list"          )
    help_str_list.append("                                    file list can use \"+vtags_incdir+<dir_path>\"")
    help_str_list.append("                                    to add all design file into build filelist")
    help_str_list.append("(2) config vtags vim at vtags gen dir \"/vtags.db/vim_local_config.py\","                    )
    help_str_list.append("    config items and detail look vim_local_config.py notes;"                                 )
    help_str_list.append("(3) support action in vim window:"                                                           )
    help_str_list.append("        1)  mt                 : print the module trace from top module;"                        )
    help_str_list.append("        2)  gi                 : a. if cursor on module call, go in submodule"                   )
    help_str_list.append("                                 b. if cursor on `include file, go in file"                      )
    help_str_list.append("                                 c. if cursor on module name string, jump to module"             )
    help_str_list.append("        3)  gu                 : if cur module called before, go upper module;"                  )
    help_str_list.append("        4)  <Space><Left>      : trace cursor word signal source;"                               )
    help_str_list.append("        5)  <Space><Right>     : trace cursor word signal dest;"                                 )
    help_str_list.append("        6)  <Space><Down>      : roll back;"                                                     )
    help_str_list.append("        7)  <Space><Up>        : go forward;"                                                    )
    help_str_list.append("        8)  <Space>v           : show current module topo "                                      )
    help_str_list.append("                                 or fold/unfold sidebar items;"                                  )
    help_str_list.append("                                 inline build vtags.db for current file;"                  )
    help_str_list.append("        9)  <Space>c           : add current cursor as checkpoint, can go back directly;"        )
    help_str_list.append("        10) <Space>b           : add current cursor module as basemodule, not show in topo;"     )
    help_str_list.append("        11) <Space>            : in sidebar or report win, just go cursor line link;"            )
    help_str_list.append("        12) <Space>h           : hold cursor win, will not auto close it;"                       )
    help_str_list.append("        13) <Space>d           : in sidebar, delete valid items(base_module, checkpoint...);"    )
    help_str_list.append("        14) <Space>s           : save current vim snapshort,"                                    )
    help_str_list.append("        15) <Space>r           : when open gvim/vim use <Space>r to reload snapshort save by <Space>s")
    help_str_list.append("        16) <Space>q           : close all open windows")
    help_str_list.append("(4) support action in vim open:"                                                           )
    help_str_list.append("        1) vim/gvim <vtags.db> : a. use gvim open a <vtags.db> will choise to open the snapshort save by <Space>s at that vtags.db")
    help_str_list.append("                                 b. if no snapshort exist, will list all top module at current vtags.db, and use index number to open")
    help_str_list += OfflineFuncLib.offline_func_help()
    MountPrintLines(help_str_list, label = 'Vtags Help', Print = True)
    exit()

# special warning for case only use default 'v' as postfix
if len(G['SupportVerilogPostfix']) == 1 and 'v' in G['SupportVerilogPostfix']:
    warning_line_list = []
    warning_line_list.append('Default config only treat "xxx.v" as verilog design files.')
    warning_line_list.append('If you have other valid postfix please add it to :')
    warning_line_list.append('  vtags.db/vim_local_config.py   : support_verilog_postfix= [...] (only change local config)')
    warning_line_list.append('  or')
    warning_line_list.append('  vtags-2.xx/vim_local_config.py : support_verilog_postfix= [...] (change global config)')
    warning_line_list.append('Such as:')
    warning_line_list.append('  support_verilog_postfix= [\'v\', \'V\', \'d\'] // add xxx.V, xxx.d as valid verilog design files' )
    MountPrintLines(warning_line_list, label = 'Add Support Postfix', Print = True)
    print('')

#-------------------------------------------------------------------------------
# when run vtags.py, create a folder named vtag.db at current dir
# and also rm the old vtags_db.log if exist.
#-------------------------------------------------------------------------------
os.system('mkdir -p %s'%(vtags_db_folder_path))

#-------------------------------------------------------------------------------
# copy glable config to vtags.db to generate local config if no local config
#-------------------------------------------------------------------------------
if not os.path.isfile(vtags_db_folder_path + '/vim_local_config.py'):
    os.system("cp %s %s"%(G['InstallPath']+'/vim_glb_config.py', vtags_db_folder_path + '/vim_local_config.py'))
# set current G
GLB.set_vtags_db_path(vtags_db_folder_path)
if os.path.isfile(vtags_db_folder_path + '/vtags_db.log'):
    os.system('rm -rf '+vtags_db_folder_path+'/vtags_db.log')

#-------------------------------------------------------------------------------
# filelist support
#-------------------------------------------------------------------------------
# current vtags.db real_filelist
vtags_file_list     = vtags_db_folder_path + '/design.filelist'
filelist_filehandle = open(vtags_file_list, 'w')

arg_i = 1
found_design = False

while arg_i < len(sys.argv):
    cur_var = sys.argv[arg_i]
    if os.path.isfile(cur_var):
        filelist_filehandle.write("-v %s\n"%(cur_var))
        found_design = True
        arg_i += 1
    elif cur_var == '-f' and (arg_i+1 < len(sys.argv)):
        filelist_filehandle.write("-f %s\n"%(sys.argv[arg_i+1]))
        found_design = True
        arg_i += 2
    else:
        print("Warning: command not support or file/filelist not exist use 'vtags -h' see help. '%s' "%(cur_var))
        exit(1)

if not found_design: # generate db at local dir
    filelist_filehandle.write("+vtags_incdir+%s\n"%( os.getcwd() ))

filelist_filehandle.close()

# parser vcs filelist
filelist_info      = FileInfLib.parser_vcs_file_list(vtags_file_list)
define_pair_list   = filelist_info['define_pair_list']     
incdir_list        = filelist_info['incdir_list']
design_list        = filelist_info['design_list']
vtags_incdir_list  = filelist_info['vtags_incdir_list']

# for each dir in the filelist, try to add a vtags.db soft link to current dir's real vtags.db
has_new_postfix_added = False
if design_list:
    new_add_postfix_set = set()
    for f_inf in design_list:
        c_postfix = get_file_path_postfix(f_inf[0])
        if c_postfix:
            new_add_postfix_set.add( c_postfix )
    has_new_postfix_added       = bool(new_add_postfix_set - G['SupportVerilogPostfix'])
    G['SupportVerilogPostfix'] |= new_add_postfix_set

# give note for vtags soft link
# if has dir in file list need give warning to generate ln manully
line_list = []
line_list.append('Generated "vtags.db" put in current dir(./)                                  ')
line_list.append('If you want active vtags in other folders in filelist, you need add soft link')
line_list.append('manually.                                                                    ')
line_list.append('Folders in filelist:                                                         ')
for d in vtags_incdir_list:
    line_list.append('  %s'%(d))
line_list.append('Such as:')
for d in vtags_incdir_list:
    line_list.append('  ln -s ./vtags.db %s'%(d))
MountPrintLines(line_list, label = 'TAKE CARE', Print = True)

if not design_list:
    print("Error: no valid design file found for postfix:'%s', change postfix list at vtags.db/vim_local_config.py"%(G['SupportVerilogPostfix']))
    exit(1)

#-------------------------------------------------------------------------------
# parser file list
#-------------------------------------------------------------------------------
# build parser out dir
parser_pub_out_path = "%s/parser_out/pub/"%(vtags_db_folder_path)
os.system("mkdir -p %s"%(parser_pub_out_path))
# parser
from Parser.Parser import parser_from_file_list
parser_from_file_list(define_pair_list, incdir_list, design_list, vtags_db_folder_path+'/parser.log', 'pub' )

#-------------------------------------------------------------------------------
# pickle
#-------------------------------------------------------------------------------
os.system('mkdir -p %s'%(vtags_db_folder_path+'/pickle'))
# put parser incir and define pair at parser_out/
out_f = open("%s/file_list_inf.py"%(parser_pub_out_path), 'w')
out_f.write('data = %s'%( { 'DefineList':define_pair_list, 'IncdirList':incdir_list, "VtagsIncdirList": vtags_incdir_list}.__str__() ))
out_f.close()

# update support postfix
old_config = []
if has_new_postfix_added:
    old_config_f    = open(vtags_db_folder_path + '/vim_local_config.py', 'r')
    old_config      = old_config_f.readlines()
    old_config_f.close()
    # update newset support prefix
    change_success = False
    for i,l in enumerate(old_config):
        m_postfix = re.match('(?P<pre>support_verilog_postfix\s*=\s*)\[',l)
        if m_postfix:
            old_config[i] = m_postfix.group('pre') + str( list(G['SupportVerilogPostfix']) ) + '\n'
            change_success = True
            break
    assert(change_success)
    # finial update
    old_config_f = open(vtags_db_folder_path + '/vim_local_config.py', 'w')
    for l in old_config:
        old_config_f.write(l)
    old_config_f.close()
