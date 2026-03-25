import sys
import re
import os
import re
from ctypes import *
from platform import *
import Lib.GLB as GLB
G = GLB.G
from Lib.BaseLib import *

# #----------------------------------------------------------
# # Parser function
# #----------------------------------------------------------
# # #For Linux
# # gcc -shared -Wl,-soname,parser_linux -o parser_linux.so -fPIC Parser.c

# # #For Mac
# # gcc -shared -Wl,-install_name,parser_mac.so -o parser_mac.so -fPIC Parser.c

# # #For windows
# # gcc -shared -Wl,-soname,parser_win -o parser_win.dll -fPIC Parser.c

# cdll_names = {  'Darwin' : G["InstallPath"] + '/Parser/parser_mac.so'
#                ,'Linux'  : G["InstallPath"] + '/Parser/parser_linux.so'
#                # ,'Windows': G["InstallPath"] + '/Parser/parser_win.dll' 
# }

# try:
#     parser = cdll.LoadLibrary( cdll_names[system()] )
# except:
#     print("Error: c-parser dynamic link library not work, please compiler it again and overlap old one. use following command:")
#     print("     cd %s"%(G["InstallPath"] + '/Parser/'))
#     print("     // For Linux:")
#     print("     gcc -shared -Wl,-soname,parser_linux -o parser_linux.so -fPIC Parser.c")
#     print("     // For Mac:")
#     print("     gcc -shared -Wl,-install_name,parser_mac.so -o parser_mac.so -fPIC Parser.c")
#     exit(0)

#----------------------------------------------------------
# Parser function
#----------------------------------------------------------
parser_bin = G["InstallPath"] + '/Parser/parser'

def compile_c_parser():
    cur_dir = os.getcwd()
    os.chdir(G["InstallPath"] + '/Parser/')
    if os.system("gcc Parser.c -o parser") != 0:
        print("Error: c-parser compile failed, please compiler it use following command manually:")
        print("     cd %s"%(G["InstallPath"] + '/Parser/'))
        print("     gcc Parser.c -o parser")
        exit(0)
    os.chdir(cur_dir)

# type only have "pub" and "tmp"
def parser_from_file_list(compile_define_list, incdir_list, design_list, log_path, ftype = "tmp"):
    parser_file_list = []
    # generate file list code
    # 1. add define
    for define_pair in compile_define_list:
        name, value = define_pair
        c_l = '+define+' + name
        if value:
            c_l += '=' + value
        parser_file_list.append(c_l)
    # 2. add inc dir
    for incdir in incdir_list:
        parser_file_list.append( '+incdir+' + incdir )
    # 3. add design file
    for f,s in design_list:
        parser_file_list.append( '-v %s -s %s'%(f,s) )
    # write file list
    parser_pub_out_path    = G["VTagsPath"] + '/parser_out/pub/'
    if ftype == 'pub':
        print("\nParsering Design Files ...")
        parser_file_list_path  = G["VTagsPath"] + '/parser_out/parser_pub.fileslist'
        parser_file_standalone = 0
    else:
        assert(ftype == 'tmp')
        parser_file_list_path  = G["VTagsPath"] + '/parser_out/parser_tmp.fileslist'
        parser_file_standalone = 1
    parser_files_list_ptr      = open( parser_file_list_path ,"w")
    parser_files_list_ptr.write("+parser_out_dir+%s\n"%(parser_pub_out_path))
    parser_files_list_ptr.write("+parser_file_standalone+%d\n"%(parser_file_standalone))
    for l in parser_file_list:
        parser_files_list_ptr.write("%s\n"%(l.rstrip('\n')))
    parser_files_list_ptr.close()
    # do c parser
    PrintDebug("parser_from_file_list: %s"%("%s %s %s"%(parser_bin, parser_file_list_path, log_path)))
    if os.system("%s %s %s"%(parser_bin, parser_file_list_path, log_path)) != 0:
        if ftype == 'pub':
            print("\nCall C-Parser Failed, Try Compiling C-parser ...")
        else:
            PrintDebug("Call C-Parser Failed, Try Compiling C-parser ...")
        compile_c_parser()
        if ftype == 'pub':
            print("Compile C-parser Success !")
        else:
            PrintDebug("Compile C-parser Success !")
        if os.system("%s %s %s"%(parser_bin, parser_file_list_path, log_path)) != 0:
            if ftype == 'pub':
                print('\nRun C-parser Failed Cmd: "%s" '%("%s %s %s"%(parser_bin, parser_file_list_path, log_path)))
            else:
                PrintDebug('Run C-parser Failed Cmd: "%s" '%("%s %s %s"%(parser_bin, parser_file_list_path, log_path)))
            return False
    return True
             
    




