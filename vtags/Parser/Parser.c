#include <stdio.h>
#include <stdlib.h>
#include <memory.h>
#include <string.h>
#include <assert.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <dirent.h>
#include "uthash.h"

//---------------------------------------------------------------
// Define
//---------------------------------------------------------------
// #define DEBUG
// for search tree
#define EOF_CHAR          0
#define PRINT_INDENTATION 0


//---------------------------------------------------------------
// enum
//---------------------------------------------------------------
typedef enum reture_state {
      FATAL           = -2
    , ERROR           = -1
    , FAILED          = 0
    , SUCCESS         = 1
    , PARTIAL_SUCCESS = 2 
    , PAIR_EXIST      = 3   // used for seatch tree add pair
}RetureState;

typedef enum as_space {
     NONE   = 0
    ,MACRO  = 1
    ,STRING = 2
    ,TIME   = 4
    ,ALL    = 7
}AsSpace;

//---------------------------------------------------------------
// void ptr link list
//---------------------------------------------------------------
typedef void (*VoidFuncPtr)(void*);
typedef void (*SerializeFuncPtr)(int head_space_num, FILE* fp, void* value);

typedef struct void_ptr_link_node{
    void*  value;
    struct void_ptr_link_node* next;
    struct void_ptr_link_node* pre;
} VoidPtrLinkNode;

// after get new node need assign value and free_value function
VoidPtrLinkNode* new_vpll_node(void* value);
void  free_vpll_node(VoidFuncPtr free_value_func, VoidPtrLinkNode* node);

typedef struct void_ptr_link_list{
    VoidPtrLinkNode* head;
    VoidPtrLinkNode* tail;
    int              length;
    VoidFuncPtr      free_value_func;
    SerializeFuncPtr serialize_value_func;
} VoidPtrLinkList;

VoidPtrLinkList* new_vpll(VoidFuncPtr free_value_func, SerializeFuncPtr serialize_value_func);
void             clear_vpll(VoidPtrLinkList* list);
void             free_vpll(VoidPtrLinkList* list);
void             vpll_push(VoidPtrLinkList* list, void* value);
void*            vpll_peek(VoidPtrLinkList* list);
void*            vpll_pop(VoidPtrLinkList* list);
void*            vpll_pop_front(VoidPtrLinkList* list);
VoidPtrLinkList* vpll_cat(VoidPtrLinkList* a, VoidPtrLinkList* b);
void             vpll_serialize(int head_space_num, FILE* fp, void* v_vpll);

//---------------------------------------------------------------
// hash function
//---------------------------------------------------------------
typedef struct hash_node{
    char* key;          /* key */
    void* value;
    UT_hash_handle hh;  /* makes this structure hashable */
}HashNode;

HashNode*        new_hash_node(void);
void             free_hash_node(VoidFuncPtr free_value_func, void* vhn);

typedef struct hash_table{
    HashNode*         table_node;
    HashNode**        table_node_ptr;
    VoidFuncPtr       free_value_func;
    SerializeFuncPtr  serialize_value_func;
}HashTable;

HashTable*  new_hash_table(void* free_value_func, void* serialize_value_func);
void        free_hash_table(void* vht);
RetureState hash_add_pair(HashTable* ht, char* key, void* value);
void        hash_remove_key(HashTable* ht, char* key);
HashNode*   hash_search(HashTable* ht, char* key);
void        hash_table_serialize(int head_space_num, FILE* fp, void* vht);

//---------------------------------------------------------------
// local struct
//---------------------------------------------------------------
typedef struct file_info{
    long  last_modify_time;
    char* serialize_file_name;
} FileInfo;

FileInfo* new_file_info(void);
void free_file_info(void* vfi);
void file_info_serialize(int head_space_num, FILE* fp, void* vfi);

//---------------------------------------------------------------
typedef struct parser_result{
    VoidPtrLinkList* file_inf_list;
    VoidPtrLinkList* mdefile_pair_list;
    VoidPtrLinkList* father_inst_pair_list;
}ParserResult;
ParserResult* new_parser_rseult(void);
void          free_parser_rseult(void* pr);

//---------------------------------------------------------------
typedef struct file_state{
    char* file_path;
    long  last_modify_time;
}FileState;

FileState* new_file_state(void);
void       free_file_state( void* fs );
char*      file_path_to_name(char* file_path );
FileState* copy_file_state(FileState* fs);
void       file_state_serialize(int head_space_num, FILE* fp, void* vfs);

//---------------------------------------------------------------
typedef struct str_range{
    char* str;
    int   range[4];
}StrRange;

StrRange*   new_str_range(void);
void        str_range_serialize(int head_space_num, FILE* fp, void* vsr);

void        free_str_range(void * sr);
StrRange*   str_range_copy(StrRange* a);
RetureState str_range_cat(StrRange* a, StrRange* b);


//---------------------------------------------------------------
typedef struct cnt_inf
{
    StrRange*  sub_name_sr;
    int        cnt_name_range[4];
}CntInf;

CntInf* new_cnt_inf(void);
void    cnt_inf_serialize(int head_space_num, FILE* fp, void* vcnt);
void    free_cnt_inf(void* cnt_inf);


//---------------------------------------------------------------
typedef struct inst_inf{
    StrRange*  submodule_name_sr;
    StrRange*  inst_name_sr;
    int        inst_line_range[2];
    VoidPtrLinkList* iocnt_inf_list;
    VoidPtrLinkList* parm_cnt_inf_list;
} InstInf;

InstInf* new_inst_inf(void);
void     inst_inf_serialize(int head_space_num, FILE* fp, void* vinst);
void     free_inst_inf(void* i_inf);


//---------------------------------------------------------------
typedef enum io_type {
      NOT_IO   = 0
    , INPUT    = 1
    , OUTPUT   = 2
    , INOUT    = 3
}IOType;

typedef struct io_inf {
    StrRange*  name_sr;
    IOType     type;
}IOInf;

IOInf* new_io_inf(void);
void   free_io_inf(void* i_inf);
void   io_inf_serialize(int head_space_num, FILE* fp, void* vio);

//---------------------------------------------------------------
typedef struct module_inf{
    int        module_end;
    StrRange*  module_name_sr;
    int        module_line_range[2];
    VoidPtrLinkList* inst_inf_list;
    VoidPtrLinkList* io_inf_list;
    VoidPtrLinkList* parm_inf_list;
    VoidPtrLinkList* code_inf_list;
} ModuleInf;

ModuleInf* new_module_inf(void);
void       module_inf_serialize(int head_space_num, FILE* fp, void* vmodele);
void       free_module_inf(void* m_inf);


//---------------------------------------------------------------
typedef struct macro_define{
    StrRange*  name_sr;
    FileState* file_state; // maybe in some incl file need full path
    char*      value;
}MacroDefine;

MacroDefine* new_macro_define(void);
MacroDefine* copy_macro_define(MacroDefine* md);
void         free_macro_define(void* m_inf);
void         macro_define_serialize(int head_space_num, FILE* fp, void* vmacro);

//---------------------------------------------------------------
typedef struct code_line_boundry{
    long start;
    long offset;
    long repeat_times;

    long last_end;    
    long repeat_break;
} CodeLineBoundry;

CodeLineBoundry* new_code_line_boundry(void);
void             free_code_line_boundry( void* vb);
void             code_line_boundry_serialize(int head_space_num, FILE* fp, void* vb);
void             add_new_line_boundry(VoidPtrLinkList* b_list, long line_end);
CodeLineBoundry* copy_code_line_boundry(CodeLineBoundry* b);
VoidPtrLinkList* code_boundry_slice(VoidPtrLinkList* blist, long start, long end);

typedef struct code_block_info{
    int              logic_line_range[2];
    int              real_line_range [2];
    VoidPtrLinkList* real_code_line_boundry; 
    char*            file_path;
} CodeBlockInfo;

CodeBlockInfo* new_code_block_info(void);
void           free_code_block_info( void* vinfo);
void           code_block_info_serialize(int head_space_num, FILE* fp, void* vinfo);

//---------------------------------------------------------------
typedef struct file_inf{
    FileState*       file_state;     // incase free same area multi times, just free at file_inf
    VoidPtrLinkList* code_inf_list;  // provide for include other file case
    VoidPtrLinkList* module_inf_list;
    VoidPtrLinkList* macro_inf_list;
    VoidPtrLinkList* wild_inst_inf_list;
} FileInf;

FileInf* new_file_inf(void);
void     free_file_inf( void* f_inf);
void     file_inf_serialize(int head_space_num, FILE* fp, void* vfile);

typedef RetureState (*Action)(void);

//---------------------------------------------------------------
typedef struct define_pair{
    char* name;
    char* value;
} DefinePair;

typedef struct parser_file_info{
    char*        file_path;
    char*        out_path;
    char*        log_path;
    int          num_define_list;
    DefinePair** define_list;
    int          num_incdir_list;
    char**       incdir_list;
}ParserFileInfo;

//---------------------------------------------------------------
typedef struct father_inst_inf{
    char*     father_module_name;
    char*     inst_name;
}FatherInstInf;

FatherInstInf* new_father_inst_inf(void);
void           free_father_inst_inf(void* u_inf);
void           father_inst_serialize(int head_space_num, FILE* fp, void* vfi);

typedef struct file_context{
    char*            code_buf         ; // NULL;
    int              old_code_buf_i   ; // 0;
    int              code_buf_i       ; // 0;
    long             code_buf_size    ; // 0;
    int              line_num         ; // 0;
    int              calm_num         ; // 0;
    FileInf*         file_inf         ; // NULL
    char*            file_path        ; // NULL
    long             last_modify_time ;
    VoidPtrLinkList* line_boundry_list;
}FileContext;

FileContext* new_empty_file_context(void);
FileContext* new_file_context( char* path , int include_file_inf);

// carefull not free file_inf
void         free_file_context(void* ctx);
void         free_file_context_no_file_inf(void* ctx);
void         active_file_context(FileContext*, int include_file_inf);
FileContext* file_context_snapshot(void);

//---------------------------------------------------------------
typedef struct file_list_file_inf{
    char* file_path;
    char* out_name;
}FileListFileInf;

FileListFileInf* new_file_list_file_inf(void);
void             free_file_list_file_inf(void* vfs);
//---------------------------------------------------------------

typedef struct file_list_inf{
    char*            parser_out_dir;
    int              parser_file_standalone;
    VoidPtrLinkList* file_inf_list;
    VoidPtrLinkList* incdir_list;
    VoidPtrLinkList* define_list;
}FileListInf;

FileListInf* new_file_list_inf(void);
void         free_file_list_inf(void*);


//---------------------------------------------------------------
// local variable
//---------------------------------------------------------------
// const int poolsize = 256 * 1024; // arbitrary size
char*             glb_code_buf               = NULL;
VoidPtrLinkList*  glb_line_boundry_list      = NULL;
int               glb_old_code_buf_i         = -1;
int               glb_code_buf_i             = 0;
long              glb_code_buf_size          = 0;
int               logic_line_num             = 0;  // used for include file case
int               line_num                   = 0;
int               calm_num                   = 0;
int               glb_parser_file_standalone = 1;
FileInf*          glb_file_inf               = NULL;
char*             glb_cur_file_path          = NULL;
long              glb_cur_last_modify_time   = 0;
FileContext*      glb_file_context           = NULL;

FILE *            glb_log_out                = NULL;
HashTable*        full_token_dic             = NULL;
HashTable*        macro_cond_token_dic       = NULL;
FileListInf*      glb_file_list_inf          = NULL;
VoidPtrLinkList*  glb_file_context_stack     = NULL;
HashTable*        glb_mdefine_dic            = NULL;
HashTable*        glb_father_insts_dic       = NULL;
HashTable*        glb_child_module_dic       = NULL;
HashTable*        glb_module_path_dic        = NULL;
HashTable*        glb_file_info_dic          = NULL;
VoidPtrLinkList*  glb_incdir_list            = NULL;

// add this to speed up incase out module include parser mulity times
HashTable*        glb_not_in_module_include_file_dic = NULL;

int               glb_mcond_stack[1024];     // max supported depth is 1024
int               glb_mcnd_meet              =  0;
int               glb_mcnd_top               = -1;

//------------------------------------------------
// function define
//------------------------------------------------
void  long_serialize(int head_space_num, FILE* fp, void* l_int);

char* gen_space(int len);
char* str_copy(char* in_s, long start, long end);
char* str_cat(char* a, char* b);
char* str_cat_free(char* a, int free_a, char* b, int free_b);
void  str_serialize(int head_space_num, FILE* fp, void* str);


char* char_replace(char* str, char c, char* r, int free_old );
    
RetureState  push_file_context_stack(void);
RetureState  pop_file_context_stack(void);
void         push_mcnd_stack(void);

RetureState  pop_mcnd_stack(void);
int*         get_LCI(void);
void         set_LCI(int* LCI);
FileContext* file_context_snapshot(void);
RetureState  replace_notes(long buf_size, char* code_buf);

VoidPtrLinkList* get_verilog_line_boundry(long buf_size, char* code_buf);

// not move char index
char         peek_char(int i);
char         next_char(void);
// go to next m_c pass
RetureState  skip_pass(char m_c);
// go to next m_c not pass
RetureState  skip_to(char m_c);
StrRange*    peek_word(int include_macro);
StrRange*    next_word(int include_macro);
char*        next_word_str(char* buf, long* start, long end);
void         skip_space( AsSpace as_space );
void         real_skip_space(void);
long         skip_space_str( char* buf, long start, long end );
//RetureState  skip_pass_word(char* str);
RetureState  skip_pass_pair_end(char* start, char* end);
RetureState  skip_pass_pairs_end(int start_n, char** start, int end_n, char** end);
//RetureState  skip_pass_pairs_end_first_word(int start_n, char** start, int end_n, char** end);
// return int[4] has range
int*         pair_range(char left_p, char right_p);
// return int[4] has range
//RetureState  skip_char_pair(char left_p, char right_p);
StrRange*    match_pair(char left_p, char right_p);
int          char_hash( char c );
int          char_hash1( char c );
int          visible_char_hash( char c );
RetureState  gen_verilog_token_tree(void);
// for simple range include ',' or ';'
int*         cnt_str_range(void);
RetureState  rec_match_terminals( VoidPtrLinkList* list, int terminal_type );
InstInf*     match_one_install(void);
RetureState  match_subcall(StrRange* submodule_name);
// need deal with '/\n' should continue pass, not pass '\n'
RetureState  next_line( int pass );
RetureState  token_if_act(void);
RetureState  token_next_line_act(void);
RetureState  token_always_act(void);
RetureState  token_begin_act(void);
RetureState  token_primitive_act(void);
RetureState  token_case_act(void);
RetureState  token_task_act(void);
RetureState  token_function_act(void);
RetureState  token_specify_act(void);
RetureState  token_next_semicolon_act(void);
RetureState  token_module_act(void);
RetureState  token_endmodule_act(void);
RetureState  rec_real_io_act(ModuleInf* m_inf, IOType io_type);
RetureState  token_input_act(void);
RetureState  token_output_act(void);
RetureState  token_inout_act(void);
RetureState  token_parameter_act(void);

// -----------------------------------
char*            str_to_next_line(int rep_line_beak);
char*            strip_space(char* str, int free_old);
char*            strip_char_and_empty(char* str, char s_char, int free_old);
RetureState      token_mdefine_act(void);
RetureState      token_mundef_act(void);
RetureState      skip_to_endif(void);
RetureState      skip_to_next_mcnd(void);
RetureState      token_minclude_act(void);
RetureState      token_mifdef_act(void);
RetureState      token_mifndef_act(void);
RetureState      token_melsif_act(void);
RetureState      token_melse_act(void);
RetureState      token_mendif_act(void);
RetureState      parser_one_file(void);
char*            search_incdir(VoidPtrLinkList* incdir_list, char* file_name);
VoidPtrLinkList* list_dirs_files(VoidPtrLinkList* in_dir_list);
FileListInf*     new_file_list_inf(void);
void             free_file_list_inf(void* fl_inf);
char*            str_to_next_char(char c, char* buf, long* start, long end);
char*            str_to_next_space(char* buf, long* start, long end);
RetureState      paser_vcs_cmd(FileListInf* fl_inf, char* buf, long start, long end, int type);
void             gather_mix_merge_inf(void);
FileListInf*     parser_file_list( char* file_list_path);

RetureState      api_parser_from_file_list(char* fl_path, char* log_path);
// FileInf*         api_parser_from_file_path(ParserFileInfo* pf_info);

int main(int argc, char **argv)
{
    argc--;
    argv++;
    
    assert(argc == 2); // need 2 input filelist path and log path
    if ( api_parser_from_file_list(argv[0], argv[1]) == SUCCESS){
        return 0;
    }
    return 1;
    // for debug
    //    ParserFileInfo pf_info;
    //    pf_info.file_path       = "/Users/CaoJun/Desktop/VMShare/example/OpenSPARCT2.1.3/design/sys/iop/tcu/rtl/tcu_dbg_ctl.v";
    //    pf_info.out_path        = "/Users/CaoJun/VMShare/example/OpenSPARCT2.1.3/test_include/aaa.py";
    //    pf_info.log_path        = "/Users/CaoJun/VMShare/example/OpenSPARCT2.1.3/test_include/parser.log";
    //    pf_info.num_define_list = 0;
    //    pf_info.num_incdir_list = 1;
    //    char*                 a = "/Users/CaoJun/VMShare/example/OpenSPARCT2.1.3/test_include/";
    //    pf_info.incdir_list     = &a;
    //    api_parser_from_file_path(&pf_info);
//     api_parser_from_file_list("/Users/CaoJun/VMShare/example/OpenSPARCT2.1.3/vtags.db/parser_out/parser_pub.fileslist", "/Users/CaoJun/VMShare/example/OpenSPARCT2.1.3/mmm.log");
}


//-------------------------------------------------------------------------------------
// function
//-------------------------------------------------------------------------------------
char* gen_space(int len){
    assert(len >= 0);
    char* space = malloc(sizeof(char) * (len + 1) );
    int i = 0;
    for (i = 0; i < len; i++) {
        space[i] = ' ';
    }
    space[i] = '\0';
    return space;
}

char* str_copy(char* in_s, long start, long end){
    if (!in_s) {
        return NULL;
    }
    if (end == -1) {
        end = (int)strlen(in_s);
    }
    if (end < start) {
        return NULL;
    }
    char* n_s = malloc(sizeof(char) * (end - start + 2) );
    if (!n_s) {
        exit(FATAL);
    }
    long i;
    for (i = start; i <= end; i++) {
        n_s[i-start] = in_s[i];
    }
    n_s[i-start] = '\0';
    return n_s;
}

char* str_cat(char* a, char* b){
    if (!a) {
        return str_copy(b, 0, -1);
    }
    if (!b) {
        return str_copy(a, 0, -1);
    }
    long a_l = strlen(a);
    long b_l = strlen(b);
    char* n_s = malloc(sizeof(char) * (a_l + b_l + 1));
    if (!n_s) {
        exit(FATAL);
    }
    long i;
    for (i = 0; i < a_l; i++) {
        n_s[i] = a[i];
    }
    for (i=0; i < b_l; i++) {
        n_s[a_l + i] = b[i];
    }
    n_s[a_l + i] = '\0';
    return n_s;
}

char* str_cat_free(char* a, int free_a, char* b, int free_b){
    char* s = NULL;
    if (!a) {
        s = str_copy(b, 0, -1);
        if (free_b) {
            free(b);
        }
        return s;
    }
    if (!b) {
        s = str_copy(a, 0, -1);
        if (free_a) {
            free(a);
        }
        return s;
    }
    long a_l = strlen(a);
    long b_l = strlen(b);
    char* n_s = malloc(sizeof(char) * (a_l + b_l + 1));
    if (!n_s) {
        exit(FATAL);
    }
    long i;
    for (i = 0; i < a_l; i++) {
        n_s[i] = a[i];
    }
    for (i=0; i < b_l; i++) {
        n_s[a_l + i] = b[i];
    }
    n_s[a_l + i] = '\0';
    if (free_a) {
        free(a);
    }
    if (free_b) {
        free(b);
    }
    return n_s;
}

void  long_serialize(int head_space_num, FILE* fp, void* vl_int){
    char* head_space = gen_space(head_space_num);
    if (!vl_int) {
        fprintf(fp, "%sNone\n",head_space);
        free(head_space);
        return;
    }
    long* l_int = vl_int;
    fprintf(fp, "%s%ld\n",head_space, *l_int);
    free(head_space);
}

void  str_serialize(int head_space_num, FILE* fp, void* vstr){
    char* head_space = gen_space(head_space_num);
    if (!vstr) {
        fprintf(fp, "%s''\n",head_space);
        free(head_space);
        return;
    }
    char* str = vstr;
    fprintf(fp, "%s'%s'\n",head_space, str);
    free(head_space);
}

VoidPtrLinkNode* new_vpll_node(void* value){
    VoidPtrLinkNode* node = malloc(sizeof(VoidPtrLinkNode));
    if (node == NULL){
        return NULL;
    }
    node->value        = value;
    node->next         = NULL;
    node->pre          = NULL;
    return node;
}

void free_vpll_node(VoidFuncPtr free_value_func, VoidPtrLinkNode* node){
    if (!node) {
        return;
    }
    assert(free_value_func);
    free_value_func(node->value); node->value = NULL;
    free(node);
}

VoidPtrLinkList* new_vpll(VoidFuncPtr free_value_func, SerializeFuncPtr serialize_value_func){
    VoidPtrLinkList* list = malloc(sizeof(VoidPtrLinkList));
    if (list == NULL){
        return NULL;
    }
    list->head                 = NULL;
    list->tail                 = NULL;
    list->length               = 0;
    list->free_value_func      = free_value_func;
    list->serialize_value_func = serialize_value_func;
    return list;
}

void clear_vpll(VoidPtrLinkList* list){
    if (list == NULL || list->length == 0){
        return;
    }
    VoidPtrLinkNode* temp_node;
    VoidPtrLinkNode* cur_node  = list->head;
    while( cur_node != NULL ){
        list->length--;
        temp_node = cur_node;
        cur_node  = temp_node->next;
        free_vpll_node(list->free_value_func, temp_node); temp_node = NULL;
    }
    assert(list->length == 0);
    return;
}

void free_vpll(VoidPtrLinkList* list){
    clear_vpll(list);
    free(list); 
}

void vpll_push(VoidPtrLinkList* list, void* value){
    VoidPtrLinkNode* node = new_vpll_node(value);
    if (list->length == 0){
        list->tail = node;
        list->head = node;
    } else {
        list->tail->next = node;
        node->pre        = list->tail;
        list->tail       = node;
    }
    list->length++;
}

void* vpll_peek(VoidPtrLinkList* list){
    if (!list) {
        return NULL;
    }
    VoidPtrLinkNode* node = list->tail;
    if (!node) {
        return NULL;
    }
    return node->value;
}

void* vpll_pop(VoidPtrLinkList* list){
    if (!list) {
        return NULL;
    }
    VoidPtrLinkNode* node = list->tail;
    if (!node){
        return NULL;
    }
    list->tail       = node->pre;
    if (list->tail) {
        list->tail->next = NULL;
    }
    list->length--;
    void* value = node->value;
    free(node);
    return value;
}

void* vpll_pop_front(VoidPtrLinkList* list){
    if (!list) {
        return NULL;
    }
    VoidPtrLinkNode* node = list->head;
    if (!node){
        return NULL;
    }
    list->head = node->next;
    if (list->head) {
        list->head->pre = NULL;
    }
    list->length--;
    void* value = node->value;
    free(node);
    return value;
}

VoidPtrLinkList* vpll_cat(VoidPtrLinkList* a, VoidPtrLinkList* b ){
    if (a == NULL || a->length == 0){
        return b;
    }
    if (b == NULL || b->length == 0 ){
        return a;
    }
    // a+b , and free b list , not node
    a->length = a->length + b->length;
    a->tail->next = b->head;
    b->head->pre  = a->tail;
    a->tail       = b->tail;
    free(b); b = NULL;
    return a;
}

FileState* new_file_state(){
    FileState* fs = malloc( sizeof(FileState) );
    if (!fs){
        exit(FATAL);
    }
    fs->file_path   = NULL;
    fs->last_modify_time = 0;
    return fs;
}

void file_state_serialize(int head_space_num, FILE* fp, void* vfs){
    char* head_space = gen_space(head_space_num);
    if (!vfs) {
        fprintf(fp, "%s{}\n",head_space);
        free(head_space);
        return;
    }
    FileState* fs = vfs;

    fprintf(fp, "%s{\n",head_space);
    fprintf(fp, "%s 'file_path'        : '%s'\n", head_space, fs->file_path);
    fprintf(fp, "%s,'last_modify_time' : %ld\n", head_space, fs->last_modify_time);

    fprintf(fp, "%s}\n", head_space);
    free(head_space);
}

FileState* copy_file_state(FileState* fs){
    FileState* new_fs = malloc(sizeof(FileState));
    new_fs->last_modify_time = fs->last_modify_time;
    new_fs->file_path   = malloc(sizeof(char) * (strlen(fs->file_path) + 1) );
    if (!new_fs->file_path) {
        exit(FATAL);
    }
    assert(strcpy(new_fs->file_path, fs->file_path));
    return new_fs;
}

void free_file_state( void* fs ){
    if (!fs){
        return;
    }
    FileState* c_fs = fs;
    free(c_fs->file_path); c_fs->file_path = NULL;
    free(c_fs);
}

char* replace_no_word_char_to_space(char* s, int free_old){
    if (!free_old) {
        s = str_copy(s, 0, -1);
    }
    int i = 0;
    for (i = 0; i<strlen(s); i++) {
        char c = s[i];
        if ((c>='a' && c<='z') || (c>='A' && c<='Z') || (c>='0'&&c<='9' ) || (c=='_')) {
            continue;
        }
        s[i] = '_';
    }
    return s;
}

char* file_path_to_name(char* file_path ){
    if (!file_path || strlen(file_path) == 0 ){
        return NULL;
    }
    long fp_len = strlen(file_path);
    long i;
    for (i = fp_len - 1; i >= 0; i--){
        if(file_path[i] == '/'){
            break;
        }
    }
    return str_copy(file_path, i+1, fp_len-1);
}

StrRange* new_str_range(){
    StrRange* sr = malloc( sizeof(StrRange) );
    if (sr == NULL){
        exit(FATAL);
    }
    sr->str = NULL;
    sr->range[0] = -1;
    sr->range[1] = -1;
    sr->range[2] = -1;
    sr->range[3] = -1;
    return sr;
}

void str_range_serialize(int head_space_num, FILE* fp, void* vsr){
    char* head_space = gen_space(head_space_num);
    if (!vsr) {
        fprintf(fp, "%s{}\n",head_space);
        free(head_space);
        return;
    }
    StrRange* sr = vsr;
    fprintf(fp, "%s{\n",head_space);
    fprintf(fp, "%s 'str'   : '%s'\n", head_space, sr->str);
    fprintf(fp, "%s,'range' : (%d,%d,%d,%d)\n", head_space, sr->range[0], sr->range[1], sr->range[2], sr->range[3]);
    fprintf(fp, "%s}\n", head_space);
    free(head_space);
}

void free_str_range(void * sr){
    if (sr == NULL){
        return;
    }
    StrRange* c_sr = sr;
    free(c_sr->str); c_sr->str = NULL;
    free(c_sr); 
}

StrRange* str_range_copy(StrRange* a){
    if (a == NULL) {
        return NULL;
    }
    StrRange* sr = malloc( sizeof(StrRange) );
    if (sr == NULL){
        exit(FATAL);
    }
    if (a->str) {
        sr->str = str_copy(a->str, 0, -1);
    }
    sr->range[0] = a->range[0];
    sr->range[1] = a->range[1];
    sr->range[2] = a->range[2];
    sr->range[3] = a->range[3];
    return sr;
}

RetureState str_range_cat(StrRange* a, StrRange* b){
    if (b == NULL){
        return SUCCESS;
    }
    if (a == NULL){
        a = b;
        b = NULL;
    }
    
    char* new_str = str_cat(a->str, b->str);
    free(a->str);
    a->str      = new_str;
    a->range[2] = b->range[2];
    a->range[3] = b->range[3];
    free_str_range( b ); b = NULL;
    return SUCCESS;
}

CntInf* new_cnt_inf(){
    CntInf* c_inf = malloc(sizeof(CntInf));
    if (c_inf == NULL){
        exit(FATAL);
    }
    c_inf->sub_name_sr       = NULL;
    c_inf->cnt_name_range[0] = -1;
    c_inf->cnt_name_range[1] = -1;
    c_inf->cnt_name_range[2] = -1;
    c_inf->cnt_name_range[3] = -1;
    return c_inf;
}

void cnt_inf_serialize(int head_space_num, FILE* fp, void* vcnt){
    char * head_space = gen_space(head_space_num);
    if (!vcnt) {
        fprintf(fp, "%s{}\n", head_space);
        free(head_space);
        return;
    }
    CntInf* c_inf = vcnt;
    fprintf(fp, "%s{\n", head_space);

    fprintf(fp, "%s 'sub_name_sr'    : \n", head_space);
    str_range_serialize(head_space_num+PRINT_INDENTATION, fp, c_inf->sub_name_sr);

    fprintf(fp, "%s,'cnt_name_range' : (%d,%d,%d,%d)\n", head_space, c_inf->cnt_name_range[0], c_inf->cnt_name_range[1], c_inf->cnt_name_range[2], c_inf->cnt_name_range[3]);

    fprintf(fp, "%s}\n", head_space);
    free(head_space);
}

void free_cnt_inf(void* cnt_inf){
    if (cnt_inf == NULL){
        return;
    }
    CntInf* c_inf = cnt_inf;
    free_str_range( c_inf->sub_name_sr ); c_inf->sub_name_sr = NULL;
    free(c_inf);
}

InstInf* new_inst_inf(){
    InstInf* c_inf = malloc( sizeof(InstInf) );
    if (c_inf == NULL){
        exit(FATAL);
    }
    c_inf->submodule_name_sr    = NULL;
    c_inf->inst_name_sr         = NULL;
    c_inf->inst_line_range[0]   = -1;
    c_inf->inst_line_range[1]   = -1;
    c_inf->parm_cnt_inf_list    = new_vpll(free_cnt_inf, cnt_inf_serialize);
    c_inf->iocnt_inf_list       = new_vpll(free_cnt_inf, cnt_inf_serialize);
    return c_inf;
}

void inst_inf_serialize(int head_space_num, FILE* fp, void* vi_inf){
    char * head_space = gen_space(head_space_num);
    if (!vi_inf) {
        fprintf(fp, "%s{}\n", head_space);
        free(head_space);
        return;
    }

    InstInf* i_inf = vi_inf;
    fprintf(fp, "%s{\n", head_space);
 
    fprintf(fp, "%s 'submodule_name_sr' : \n", head_space);
    str_range_serialize(head_space_num+PRINT_INDENTATION, fp, i_inf->submodule_name_sr);

    fprintf(fp, "%s,'inst_name_sr'      : \n", head_space);
    str_range_serialize(head_space_num+PRINT_INDENTATION, fp, i_inf->inst_name_sr);

    fprintf(fp, "%s,'inst_line_range'   : (%d,%d)\n", head_space, i_inf->inst_line_range[0], i_inf->inst_line_range[1]);

    fprintf(fp, "%s,'parm_cnt_inf_list' : \n", head_space);
    vpll_serialize(head_space_num+PRINT_INDENTATION, fp, i_inf->parm_cnt_inf_list);

    fprintf(fp, "%s,'iocnt_inf_list'    : \n", head_space);
    vpll_serialize(head_space_num+PRINT_INDENTATION, fp, i_inf->iocnt_inf_list);

    fprintf(fp, "%s}\n", head_space);
    free(head_space);
}

void free_inst_inf(void* i_inf){
    if (i_inf == NULL){
        return;
    }
    InstInf* c_inf = i_inf;
    free_vpll(       c_inf->iocnt_inf_list    ); c_inf->iocnt_inf_list    = NULL;
    free_vpll(       c_inf->parm_cnt_inf_list ); c_inf->parm_cnt_inf_list = NULL;
    free_str_range(  c_inf->inst_name_sr      ); c_inf->inst_name_sr      = NULL;
    free_str_range(  c_inf->submodule_name_sr ); c_inf->submodule_name_sr = NULL;
    free(c_inf); 
}

IOInf* new_io_inf(){
    IOInf* c_inf = malloc( sizeof(IOInf) );
    if (c_inf == NULL){
        exit(FATAL);
    }
    c_inf->name_sr          = NULL;
    c_inf->type             = NOT_IO;
    return c_inf;
}

void io_inf_serialize(int head_space_num, FILE* fp, void* vio){
    char* head_space = gen_space(head_space_num);
    if (!vio) {
        fprintf(fp, "%s{}\n", head_space);
        free(head_space);
        return;
    }

    IOInf* io_inf = vio;


    fprintf(fp, "%s{\n", head_space);

    fprintf(fp, "%s 'name_sr' : \n", head_space);
    str_range_serialize(head_space_num+PRINT_INDENTATION, fp, io_inf->name_sr);

    fprintf(fp, "%s,'type'    : %d\n", head_space, io_inf->type);

    fprintf(fp, "%s}\n", head_space);
    free(head_space);
}

void free_io_inf(void* i_inf){
    if (i_inf == NULL){
        return;
    }
    IOInf* c_inf = i_inf;
    free_str_range( c_inf->name_sr ); c_inf->name_sr = NULL;
    free(c_inf); 
}

ModuleInf* new_module_inf(){
    ModuleInf* c_inf = malloc(sizeof(ModuleInf));
    if (c_inf == NULL){
        exit(FATAL);
    }
    c_inf->module_end           = 0;
    c_inf->module_name_sr       = NULL;
    c_inf->module_line_range[0] = -1;
    c_inf->module_line_range[1] = -1;

    c_inf->inst_inf_list       = new_vpll(&free_inst_inf, inst_inf_serialize);
    c_inf->io_inf_list         = new_vpll(&free_io_inf, io_inf_serialize);
    c_inf->parm_inf_list       = new_vpll(&free_str_range, str_range_serialize);
    c_inf->code_inf_list       = new_vpll(&free_code_block_info, code_block_info_serialize);
    return c_inf;
}

void module_inf_serialize(int head_space_num, FILE* fp, void* vm_inf){
    char* head_space = gen_space(head_space_num);
    if (!vm_inf) {
        fprintf(fp, "%s{}\n", head_space);
        free(head_space);
        return;
    }
    ModuleInf* m_inf = vm_inf;

    fprintf(fp, "%s{\n", head_space);

    fprintf(fp, "%s 'module_name_sr'    : \n", head_space);
    str_range_serialize(head_space_num+PRINT_INDENTATION, fp, m_inf->module_name_sr);

    fprintf(fp, "%s,'module_line_range' : (%d,%d)\n", head_space, m_inf->module_line_range[0], m_inf->module_line_range[1]);

    fprintf(fp, "%s,'inst_inf_list'     : \n", head_space);
    vpll_serialize(head_space_num+PRINT_INDENTATION, fp, m_inf->inst_inf_list);

    fprintf(fp, "%s,'parm_inf_list'     : \n", head_space);
    vpll_serialize(head_space_num+PRINT_INDENTATION, fp, m_inf->parm_inf_list);
    
    fprintf(fp, "%s,'io_inf_list'       : \n", head_space);
    vpll_serialize(head_space_num+PRINT_INDENTATION, fp, m_inf->io_inf_list);
    
    fprintf(fp, "%s,'code_inf_list'     : \n", head_space);
    vpll_serialize(head_space_num+PRINT_INDENTATION, fp, m_inf->code_inf_list);
    
    fprintf(fp, "%s}\n",head_space);
    free(head_space);
}

void free_module_inf(void* m_inf){
    if (m_inf == NULL){
        return;
    }
    ModuleInf* c_inf = m_inf;
    free_vpll(      c_inf->inst_inf_list    );   c_inf->inst_inf_list    = NULL;
    free_vpll(      c_inf->io_inf_list      );   c_inf->io_inf_list      = NULL;
    free_vpll(      c_inf->parm_inf_list      ); c_inf->parm_inf_list    = NULL;
    free_vpll(      c_inf->code_inf_list );      c_inf->code_inf_list    = NULL;
    free_str_range( c_inf->module_name_sr   );   c_inf->module_name_sr   = NULL;
    free(c_inf);
}

MacroDefine* new_macro_define(){
    MacroDefine* c_inf = malloc(sizeof(MacroDefine));
    if (c_inf == NULL){
        exit(FATAL);
    }
    c_inf->name_sr          = NULL;
    c_inf->file_state       = NULL;
    if (glb_file_inf){
        c_inf->file_state = glb_file_inf->file_state;
    } // else is filelist define
    c_inf->value            = NULL;
    return c_inf;
}

MacroDefine* copy_macro_define(MacroDefine* md){
    if (!md) {
        return NULL;
    }
    MacroDefine* c_inf = malloc(sizeof(MacroDefine));
    if (c_inf == NULL){
        exit(FATAL);
    }
    c_inf->name_sr          = str_range_copy(md->name_sr);
    c_inf->file_state       = copy_file_state(md->file_state);
    c_inf->value            = str_copy(md->value, 0, -1);
    return c_inf;
}

void free_macro_define(void* m_inf){
    if (m_inf == NULL){
        return;
    }
    MacroDefine* c_inf = m_inf;
    free_str_range( c_inf->name_sr ); c_inf->name_sr = NULL;
    free(c_inf->value     );       c_inf->value      = NULL;
    free(c_inf); 
}


void macro_define_serialize(int head_space_num, FILE* fp, void* vmd){
    char* head_space = gen_space(head_space_num);
    if (!vmd) {
        fprintf(fp, "%s{}\n", head_space);
        free(head_space);
        return;
    }
    MacroDefine* md  = vmd;
    fprintf(fp, "%s{\n", head_space);
    fprintf(fp, "%s 'name_sr'    : \n",head_space);
    str_range_serialize(head_space_num+PRINT_INDENTATION, fp, md->name_sr);
    fprintf(fp, "%s,'file_state' : \n",head_space);
    file_state_serialize(head_space_num+PRINT_INDENTATION, fp, md->file_state);
    if (!md->value) {
        fprintf(fp, "%s,'value'      : None \n",head_space);
    } else {
        char* print_str = char_replace(md->value, '\'', "\\'", 0);
        fprintf(fp, "%s,'value'      : '%s' \n",head_space, print_str);
        free(print_str);
    }
    fprintf(fp, "%s}\n", head_space);
    free(head_space);
}

FileInf* new_file_inf(){
    FileInf* c_inf = malloc( sizeof(FileInf) );
    if (c_inf == NULL){
        exit(FATAL);
    }
    c_inf->file_state          = new_file_state();
    c_inf->code_inf_list       = new_vpll(&free_code_block_info, code_block_info_serialize);
    c_inf->module_inf_list     = new_vpll(&free_module_inf, module_inf_serialize);
    c_inf->macro_inf_list      = new_vpll(&free_macro_define, macro_define_serialize);
    c_inf->wild_inst_inf_list  = new_vpll(&free_inst_inf, inst_inf_serialize);
    return c_inf;
}

void free_file_inf( void* f_inf){
    if (f_inf == NULL){
        return;
    }
    FileInf* c_inf = f_inf;
    free_vpll( c_inf->code_inf_list      ); c_inf->code_inf_list       = NULL;
    free_vpll( c_inf->module_inf_list    ); c_inf->module_inf_list     = NULL;
    free_vpll( c_inf->macro_inf_list     ); c_inf->macro_inf_list      = NULL;
    free_vpll( c_inf->wild_inst_inf_list ); c_inf->wild_inst_inf_list  = NULL;
    free_file_state(c_inf->file_state    ); c_inf->file_state          = NULL;
    free(c_inf); 
}

void file_inf_serialize(int head_space_num, FILE* fp, void* vf_inf){
    char* head_space = gen_space(head_space_num);
    if (!vf_inf) {
        fprintf(fp, "%s{}\n", head_space);
        free(head_space);
        return;
    }
    fprintf(fp, "%s{\n", head_space);
    FileInf* f_inf = vf_inf;
   
    fprintf(fp, "%s 'file_state'         :\n", head_space);
    file_state_serialize(head_space_num+PRINT_INDENTATION, fp, f_inf->file_state);

    fprintf(fp, "%s,'code_inf_list'      :\n", head_space);
    vpll_serialize(head_space_num+PRINT_INDENTATION, fp, f_inf->code_inf_list);
    
    fprintf(fp, "%s,'module_inf_list'    :\n", head_space);
    vpll_serialize(head_space_num+PRINT_INDENTATION, fp, f_inf->module_inf_list);

    fprintf(fp, "%s,'macro_inf_list'     :\n", head_space);
    vpll_serialize(head_space_num+PRINT_INDENTATION, fp, f_inf->macro_inf_list);

    fprintf(fp, "%s,'wild_inst_inf_list' :\n", head_space);
    vpll_serialize(head_space_num+PRINT_INDENTATION, fp, f_inf->wild_inst_inf_list);

    fprintf(fp, "%s}\n", head_space);
    free(head_space);
}

FatherInstInf* new_father_inst_inf(){
    FatherInstInf* c_inf = malloc( sizeof(FatherInstInf) );
    if (c_inf == NULL){
        exit(FATAL);
    }
    c_inf->father_module_name = NULL;
    c_inf->inst_name          = NULL;
    return c_inf;
}

void free_father_inst_inf( void* u_inf){
    if (u_inf == NULL){
        return;
    }
    FatherInstInf* c_inf = u_inf;
    free(c_inf->father_module_name);  c_inf->father_module_name = NULL;
    free(c_inf->inst_name); c_inf->inst_name = NULL;
    free(c_inf); 
}

void free_file_context(void* ctx){
    if (!ctx){
        return;
    }
    FileContext* fc = ctx;
    free(fc->code_buf); fc->code_buf = NULL;
    free(fc->file_path); fc->file_path = NULL;
    free_vpll(fc->line_boundry_list); fc->line_boundry_list = NULL;
    free_file_inf(fc->file_inf); fc->file_inf = NULL;
    free(fc); fc = NULL;
}

void free_file_context_no_file_inf(void* ctx){
    if (!ctx){
        return;
    }
    FileContext* fc = ctx;
    free(fc->code_buf); fc->code_buf = NULL;
    free(fc->file_path); fc->file_path = NULL;
    free_vpll(fc->line_boundry_list); fc->line_boundry_list = NULL;
    free(fc); fc = NULL;
}

RetureState push_file_context_stack(){
    if (glb_file_context_stack->length >= 24) {
        fprintf(glb_log_out, "RTL ERROR %d-%d: %s nested include deep beyond 24\n", line_num, calm_num, glb_file_inf->file_state->file_path);
        // pending can print all include flow
        return FAILED;
    }
    vpll_push(glb_file_context_stack, file_context_snapshot());
    return SUCCESS;
}

RetureState pop_file_context_stack(){
    if (glb_file_context_stack->length == 0) {
        return FAILED;
    }
    FileContext* new_cnt = vpll_pop(glb_file_context_stack);
    if (!new_cnt) {
        return FAILED;
    }
    // end file and module old code block
    // 1. adjust logic and line_num
    if (peek_char(-1) == '\n') { // normal EOF has a '\n' ignore it
        logic_line_num--;
        line_num--;
    }
    // 2. end pre file code block
    CodeBlockInfo* pre_file_code_inf            = vpll_peek(glb_file_inf->code_inf_list);
    assert(pre_file_code_inf != NULL);
    pre_file_code_inf->logic_line_range[1]      = logic_line_num;
    pre_file_code_inf->real_line_range[1]       = line_num;
    assert( (pre_file_code_inf->logic_line_range[1] - pre_file_code_inf->logic_line_range[0]) == (pre_file_code_inf->real_line_range[1] - pre_file_code_inf->real_line_range[0]) );

    // 3. end pre module code inf
    ModuleInf* c_m_inf = vpll_peek(glb_file_inf->module_inf_list);
    if (c_m_inf && c_m_inf->module_end == 0) {
        // match include set old block range end
        CodeBlockInfo* pre_module_code_inf = vpll_peek(c_m_inf->code_inf_list);
        assert(pre_module_code_inf != NULL);
        pre_module_code_inf->logic_line_range[1] = logic_line_num;
        pre_module_code_inf->real_line_range[1]  = line_num;
        // update last code line boundry inf
        pre_module_code_inf->real_code_line_boundry = code_boundry_slice(glb_line_boundry_list, pre_module_code_inf->real_line_range[0], pre_module_code_inf->real_line_range[1]);
        
        assert( (pre_module_code_inf->logic_line_range[1] - pre_module_code_inf->logic_line_range[0]) == (pre_module_code_inf->real_line_range[1] - pre_module_code_inf->real_line_range[0]) );
    }
    // new add file and module old code block
    // 1. adjust logic line num
    logic_line_num++;
    // 2. add new file code inf
    CodeBlockInfo* new_file_code_info       = new_code_block_info();
    new_file_code_info->file_path           = str_copy(new_cnt->file_path, 0, -1);
    new_file_code_info->logic_line_range[0] = logic_line_num;
    new_file_code_info->real_line_range[0]  = new_cnt->line_num;
    vpll_push(glb_file_inf->code_inf_list, new_file_code_info);
    // 3. add new module code inf
    if (c_m_inf && c_m_inf->module_end == 0) {
        CodeBlockInfo* new_module_code_info       = new_code_block_info();
        new_module_code_info->file_path           = str_copy(new_cnt->file_path, 0, -1);
        new_module_code_info->logic_line_range[0] = logic_line_num;
        new_module_code_info->real_line_range[0]  = new_cnt->line_num;
        vpll_push(c_m_inf->code_inf_list, new_module_code_info);
    }
    // add new code block inf
    active_file_context(new_cnt, 0);
    return SUCCESS;
}

void push_mcnd_stack(){
    // fprintf(glb_log_out, "`if(n)def %d-%d meet: depth %d\n", line_num, calm_num, glb_mcnd_top);
    if (glb_mcnd_top == 1023){
        fprintf(glb_log_out, "RTL ERROR: mcnd stack overflow! `if(n)def %d-%d meet: depth %d\n", line_num, calm_num, glb_mcnd_top);
        exit(FATAL);
    }
    glb_mcond_stack[++glb_mcnd_top] = glb_mcnd_meet;
}

RetureState pop_mcnd_stack(){
    // fprintf(glb_log_out, "`endif %d-%d meet depth:%d\n", line_num, calm_num, glb_mcnd_top);
    if (glb_mcnd_top < 0) {
        fprintf(glb_log_out, "RTL ERROR: mcnd stack underflow! `endif %d-%d meet depth:%d\n", line_num, calm_num, glb_mcnd_top);
        return FAILED;
    }
    glb_mcnd_meet = glb_mcond_stack[glb_mcnd_top--];
    return SUCCESS;
}

int* get_LCI(){
    int* LCI = malloc( sizeof(int) * 7 );
    if (LCI == NULL){
        exit(FATAL);
    }
    LCI[0] = logic_line_num;
    LCI[1] = line_num;
    LCI[2] = calm_num;
    LCI[3] = glb_old_code_buf_i;
    LCI[4] = glb_code_buf_i;
    LCI[5] = glb_mcnd_meet;
    LCI[6] = glb_mcnd_top;
    // fprintf(glb_log_out, "get LCI %d-%d: glb_mcnd_top=%d\n",line_num, calm_num, glb_mcnd_top);
    return LCI;
}

void set_LCI(int* LCI){
    logic_line_num     = LCI[0];
    line_num           = LCI[1];
    calm_num           = LCI[2];
    glb_old_code_buf_i = LCI[3];
    glb_code_buf_i     = LCI[4];
    glb_mcnd_meet      = LCI[5];
    glb_mcnd_top       = LCI[6];
    // fprintf(glb_log_out, "set LCI %d-%d: glb_mcnd_top=%d\n",line_num, calm_num, glb_mcnd_top);
}

void active_file_context(FileContext* fc, int include_file_inf){
    glb_code_buf              = fc->code_buf        ;
    glb_old_code_buf_i        = fc->old_code_buf_i  ;
    glb_code_buf_i            = fc->code_buf_i      ;
    glb_code_buf_size         = fc->code_buf_size   ;
    line_num                  = fc->line_num        ;
    calm_num                  = fc->calm_num        ;
    glb_cur_file_path         = fc->file_path       ;
    glb_cur_last_modify_time  = fc->last_modify_time;
    glb_line_boundry_list     = fc->line_boundry_list;
    if (include_file_inf) {
        logic_line_num = fc->line_num      ;
        glb_file_inf   = fc->file_inf      ;
    }
    glb_file_context   = fc;
}
void deactive_file_context(){
    glb_code_buf             = NULL;
    glb_old_code_buf_i       =   -1;
    glb_code_buf_i           =   -1;
    glb_code_buf_size        =    0;
    line_num                 =    0;
    logic_line_num           =    0;
    calm_num                 =    0;
    glb_file_inf             = NULL;
    glb_cur_file_path        = NULL;
    glb_cur_last_modify_time = 0   ;
    glb_file_context         = NULL;
    glb_line_boundry_list    = NULL;
}

FileContext* file_context_snapshot(){
    FileContext* fc      = new_empty_file_context();
    fc->code_buf         = glb_code_buf            ;
    fc->old_code_buf_i   = glb_old_code_buf_i      ;
    fc->code_buf_i       = glb_code_buf_i          ;
    fc->code_buf_size    = glb_code_buf_size       ;
    fc->line_num         = line_num                ;
    fc->calm_num         = calm_num                ;
    fc->file_path        = glb_cur_file_path       ;
    fc->last_modify_time = glb_cur_last_modify_time;
    fc->file_inf         = NULL                    ;
    fc->line_boundry_list= glb_line_boundry_list   ;
    return fc;
}

RetureState replace_notes(long buf_size, char* code_buf){
    // two buffer ready replace note to ' '
    int  i;
    int  pre_asterisk  = 0;
    int  pre_backslash = 0;
    int  cur_backslash = 0;
    int  cur_asterisk  = 0;
    int  in_single_line_notes = 0;
    int  in_multi_line_notes  = 0;
    char c;
    for (i = 0; i < buf_size; ++i){
        cur_backslash = 0;
        cur_asterisk  = 0;
        c = code_buf[i];
        if(c == '/'){
            cur_backslash = 1;
        } else if (c == '*'){
            cur_asterisk  = 1;
        }
        // match "//"
        if ( !in_multi_line_notes && pre_backslash && cur_backslash){ 
            in_single_line_notes = 1;
            code_buf[i-1] = ' '; // clear pre "/"
        }
        // match "/*"
        if ( !in_single_line_notes && pre_backslash && cur_asterisk){
            in_multi_line_notes = 1;
            code_buf[i-1] = ' '; // clear pre "/"
        }
        // match '\n'
        if (c == '\n' && in_single_line_notes){
            in_single_line_notes = 0;
        }
        // match "*/"
        if (pre_asterisk && cur_backslash && in_multi_line_notes){
            in_multi_line_notes = 0;
            code_buf[i] = ' '; // include cur '/'
        }
        // in note change to ' '
        if (in_single_line_notes || in_multi_line_notes){
            if ( !( c == '\n' || c == EOF_CHAR) ){   // skip '\n' incase calm_num not correct
                code_buf[i] = ' '; 
            }
        }
        pre_backslash = cur_backslash;
        pre_asterisk  = cur_asterisk;
    }
    return SUCCESS;
}

FileContext* new_empty_file_context(void){
    FileContext* fc_inf = malloc( sizeof(FileContext) );
    if (!fc_inf){
        exit(FATAL);
    }
    fc_inf->calm_num          = -1  ;
    fc_inf->code_buf          = NULL;
    fc_inf->code_buf_i        = -1  ;
    fc_inf->code_buf_size     = 0   ;
    fc_inf->file_inf          = NULL;
    fc_inf->file_path         = NULL;
    fc_inf->line_num          = -1  ;
    fc_inf->old_code_buf_i    = -1  ;
    fc_inf->last_modify_time  = 0   ;
    fc_inf->line_boundry_list = NULL;
    return fc_inf;
}

FileContext* new_file_context( char* path, int include_file_inf ){
    FILE * c_fp;    
    int    c_fd;    
    struct stat c_buf; 
    long   size = 0;
    long   read_size = 0;

// #ifdef DEBUG
    fprintf(glb_log_out, "FILE:%s\n", path);
// #endif
    // open file
    c_fp=fopen(path, "r");    
    if(c_fp == NULL) {
        fprintf(glb_log_out, "ERROR: cannot open file:'%s'\n", path);
        return NULL;
    }
    // get file state
    c_fd        =fileno(c_fp);        
    fstat(c_fd, &c_buf);
    size        =c_buf.st_size; // get file size (byte)

    // malloc data buffer
    char* code_buf = malloc(size+1);
    if( !code_buf ) {
        printf("FATAL: cannot malloc(%ld) for file: %s \n", size, path);
        // free(mem_file_path); mem_file_path = NULL;
        exit(FATAL);
    }
    // read data
    if ((read_size = read(c_fd, code_buf, size+1)) <= 0) {
        fprintf(glb_log_out, "ERROR: cannot read() data for file: %s \n", path);
        return NULL;
    }
    assert( read_size <= size);
    code_buf[read_size] = EOF_CHAR;
    assert( replace_notes(read_size, code_buf) == SUCCESS );
    // gen file_context
    FileContext* fc_inf           = new_empty_file_context();
    // initial file context
    fc_inf->code_buf              = code_buf;
    fc_inf->old_code_buf_i        = -1;
    fc_inf->code_buf_i            = 0;
    fc_inf->code_buf_size         = read_size;
    fc_inf->line_num              = 0;
    fc_inf->calm_num              = 0;
    fc_inf->file_path             = str_copy(path, 0, -1);
    fc_inf->last_modify_time      = c_buf.st_mtime;
    fc_inf->line_boundry_list     = get_verilog_line_boundry(read_size, code_buf);
    if (include_file_inf) {
        FileInf* cur_file_inf = new_file_inf();
        cur_file_inf->file_state->file_path        = str_copy(path, 0, -1);
        cur_file_inf->file_state->last_modify_time = c_buf.st_mtime; // latest modification time
        //(seconds passed from 01/01/00:00:00 1970 UTC)
        fc_inf->file_inf        = cur_file_inf;
        // code info
        CodeBlockInfo* cur_info = new_code_block_info();
        cur_info->file_path     = str_copy(path, 0, -1);
        cur_info->logic_line_range[0] = 0;
        cur_info->real_line_range[0]  = 0;
        vpll_push(fc_inf->file_inf->code_inf_list, cur_info);
        // update file info dic
        HashNode* c_node = hash_search(glb_file_info_dic, path);
        if (!c_node) {
            FileInfo* fi = new_file_info();
            hash_add_pair(glb_file_info_dic, path, fi);
        }
        c_node          = hash_search(glb_file_info_dic, path);
        assert(c_node);
        FileInfo* fi         = c_node->value;
        fi->last_modify_time = c_buf.st_mtime;
    }
    fclose(c_fp);
    return fc_inf;
}

char peek_char(int i){
    int  real_i = glb_code_buf_i + i;
    char c      = EOF_CHAR; // default EOF

    if (real_i < 0){
        return 0;
    }

    if (real_i < glb_code_buf_size){
        c = glb_code_buf[real_i];
    }
#ifdef DEBUG
        // printf("peek_char(%d) %d-%d = %c\n",i, c, line_num, calm_num);
#endif
    return c; // peek failed, cause by: i is cross 2 buf, or EOF
}

char real_next_char(){
    // end buffer
    if (glb_code_buf_i >= glb_code_buf_size){
        return EOF_CHAR;  // EOF
    }    
    // check next char
    char c  = peek_char(0);
    if (c == '\n'){
        line_num ++;
        logic_line_num++;
        calm_num = -1;
    }
    glb_code_buf_i++;
    calm_num++;
    return c;
}

// next char with macro in count: `ifdef `ifndef `else `elsif `endif
char next_char(){
    // check macro condition
    char c1 = peek_char(1);
    if (c1 == '`') {
        int  i = 0;
        char word[8];
        char ci;
        // look ahead 9 = (len(ifndef )+1) char see if it's macro condition
        for (i = 2; i <= 8; i++) {
            ci = peek_char(i);
            if ( 'a' <= ci && ci <= 'z') {
                word[i-2] = ci;
                continue;
            }
            break;
        }
        word[i-2] = '\0';
        // if len(word) < len(else) or len(word) > len(ifndef) not macro condition
        if ( i < 4 + 2 || i > 6 + 2 ) {
            return real_next_char();
        }
        // try match macro cond and to action
        int* LCI = get_LCI();
        HashNode* node = hash_search(macro_cond_token_dic, word);
        // if not hit not macro condition
        if (!node) {
            free(LCI); LCI = NULL;
            return real_next_char();
        }
        // if match macro condition, just pass this word
        char   c0  = peek_char(0);  // will return current char
        int    k   = 0;
        for (k = 0; k < i; k++) {
            real_next_char();
        }
        // do macro condition
        Action act = node->value;
        if ((*act)() != SUCCESS){
            set_LCI(LCI);
            free(LCI); LCI = NULL;
            fprintf(glb_log_out, "RTL ERROR: %d-%d `%s action failed !\n", line_num, calm_num, word);
            return real_next_char();
        }
        free(LCI); LCI = NULL;
        // action must already forward to `xxx next char
        return c0;
    }
    // no macro cond just real_next_char()
    return real_next_char();
}


RetureState skip_pass(char m_c){
    char c;
    while (1) {
        c = next_char();
        if (c == m_c){
            if (c == '"' && peek_char(-2) == '\\') {
                continue;
            }
            return SUCCESS;
        }
        if (c == EOF_CHAR) {
            break; // EOF
        }
    }
    return FAILED;
}

RetureState skip_to(char m_c){
    char c;
    while (1) {
        c = peek_char(0);
        if (c == m_c){
            return SUCCESS;
        }
        if (c == EOF_CHAR) {
            break; // EOF
        }
        assert(next_char() != EOF_CHAR);
    }
    return FAILED;
}

StrRange* peek_word(int include_macro){
    int  word_len = 0;
    char c        = peek_char(word_len);
    while ( (c>='a' && c<='z') || (c>='A' && c<='Z') || (c>='0'&&c<='9' ) || (c=='_') || (include_macro && (c == '`')) ){
        word_len++;
        c = peek_char(word_len);
    }
    if (word_len == 0){
        return NULL;
    }
    StrRange* sr = new_str_range();
    sr->str      = str_copy(glb_code_buf, glb_code_buf_i, glb_code_buf_i + word_len - 1);
    sr->range[0] = logic_line_num;
    sr->range[1] = calm_num;
    sr->range[2] = logic_line_num;
    sr->range[3] = calm_num + word_len - 1;
    return sr;
}

StrRange* next_word(int include_macro){
    int  i;
    StrRange* sr     = new_str_range();
    sr->range[0]     = logic_line_num;
    sr->range[1]     = calm_num;
    int  word_len    = 0;
    // verilog special case: "\..." - the '\' is an escape character,
    // which escapes the entire string of ascii characters until next space character
    char* escape_word = NULL;
    char c            = peek_char(0);
    if (c == '\\'){
        // '\\' special care means '\' so no word found reture NULL
        if (peek_char(1) == '\\'){
            return NULL;
        }
        real_next_char(); // skip '\'
        word_len = 0;
        c        = peek_char(0);
        while( (c != EOF_CHAR) && (c != ' ') ){
            word_len++;
            c = peek_char(word_len);
        }
        if (c != ' '){
            fprintf(glb_log_out, "ERL ERROR %d-%d: '\\' used as escapes not follow a space ' ' !\n", line_num, calm_num);
        }
        escape_word = malloc( sizeof(char) * (word_len+2) );
        if (escape_word == NULL){
            exit(FATAL);
        }
        for (i = 0; i < word_len; ++i){
            escape_word[i] = real_next_char();
        }
        escape_word[i]   = '\0';
        // for '\' as escapes case if has "'" need change to "\'" because we serilize to py str
        escape_word      = char_replace(escape_word, '\'', "\\'", 1);
        real_next_char();     // skip ' ', because the first space work together with escape '\'
                         // so not part of code should remove and continue match word  
    }
    // normal word use: a-z A-Z 0-9 _ or `
    word_len = 0;
    c   = peek_char(word_len);
    while ( (c != EOF_CHAR) &&
            ((c>='a' && c<='z') ||
             (c>='A' && c<='Z') ||
             (c>='0' && c<='9') ||
             (c=='_') || (include_macro && (c == '`')))){
        word_len++;
        c = peek_char(word_len);
    }
    // no word return NULL
    if (!escape_word && word_len == 0){
        free_str_range(sr);
        return NULL;
    }
    // copy word and return
    char* normal_word = malloc( sizeof(char) * (word_len+2) );
    if (normal_word == NULL){
        exit(FATAL);
    }
    for (i = 0; i < word_len; ++i){
        normal_word[i] = real_next_char();
    }
    normal_word[i]   = '\0';
    // if has escape part need connect it
    sr->str      = str_cat_free(escape_word, 1, normal_word, 1);
    sr->range[2] = logic_line_num;
    sr->range[3] = calm_num - 1;
    return sr;
}

// only used in filelist current not care escape '\'
char* next_word_str(char* buf, long* start, long end){
    int  word_len = 0;
    if (*start >= end) {
        *start = end;
        return NULL;
    }
    char c = buf[*start + word_len];
    while ( (c>='a' && c<='z') || (c>='A' && c<='Z') || (c>='0'&&c<='9' ) || (c=='_') ){
        word_len++;
        c = buf[*start + word_len];
    }
    if (word_len == 0){
        return NULL;
    }
    
    char* word = str_copy(buf, *start, *start + word_len - 1);
    *start = *start + word_len;
    return word;
}

void real_skip_space(){
    char c;
    // always look back 1 char, because need look ahead 1 char to deciside token end.
    c = peek_char(0);
    while ( c=='\t' || c=='\n' || c==' ' || c=='\r' ){
        real_next_char();
        c = peek_char(0);
    }
}

void skip_space( AsSpace as_space ){
    char c;
    int  i,j;
    // always look back 1 char, because need look ahead 1 char to deciside token end.
    c = peek_char(0);
    while ( c=='\t' || c=='\n' || c==' ' || c=='\r' ){
        next_char();
        c = peek_char(0);
    }
    // match TIME_SKIP just get next token
    if ( (as_space & TIME) && (c == '#') ){
        i = 1;
        c = peek_char(i);
        while (('0' <= c && c <= '9') || c == '.') {
            i++;
            c = peek_char(i);
        }
        if (i > 1) {
            for (j = 0; j < i; j++) {
                next_char();
            }
            skip_space(as_space);
            return;
        }
    } else if( (as_space & STRING) && (c == '"') ){
        next_char();
        skip_pass('"');
        skip_space(as_space);
        return;
    } else if( c == '`' ){ // also skip `ifdef part space
        int*      LCI    = get_LCI();
        StrRange* n_word = next_word(1);
        char*     maybe_mcnd = str_copy(n_word->str, 1, -1);
        free_str_range(n_word); n_word = NULL;
        // try match macro cond and to action
        HashNode* node = hash_search(macro_cond_token_dic, maybe_mcnd);
        free(maybe_mcnd); maybe_mcnd = NULL;
        // if not hit not macro condition
        if (!node) {
            set_LCI(LCI);
            free(LCI); LCI = NULL;
            return;
        }
        // do macro condition
        Action act = node->value;
        if ((*act)() != SUCCESS){
            set_LCI(LCI);
            free(LCI); LCI = NULL;
            fprintf(glb_log_out, "RTL ERROR: %d-%d `%s action failed !\n", line_num, calm_num, node->key);
            return;
        }
        free(LCI); LCI = NULL;
        skip_space(as_space);
        return;
    }
    return;
}

long skip_space_str( char* buf, long start, long end ){
    char c;
    // always look back 1 char, because need look ahead 1 char to deciside token end.
    if (start >= end) {
        return end;
    }
    c = buf[start];
    while ( c=='\t' || c=='\n' || c==' ' || c=='\r' ){
        start++;
        if (start >= end) {
            return end;
        }
        c = buf[start];
    }
    return start;
}

//RetureState skip_pass_word(char* str){
//    if (str == NULL || strlen(str) == 0){
//        return SUCCESS;
//    }
//    StrRange* n_word = NULL;
//    int success = 0;
//    while(1){
//        n_word = next_word(1);
//        if (n_word && strcmp(n_word->str, str) == 0){
//            success = 1;
//            free_str_range(n_word); n_word = NULL;
//            break;
//        }
//        free_str_range(n_word); n_word = NULL;
//        if ( next_char() == EOF_CHAR ){
//            break;
//        };
//    }
//    if (success == 0){
//        fprintf(glb_log_out, "RTL ERROR: not found '%s' at end !\n", str);
//        return FAILED;
//    }
//    return SUCCESS;
//}

RetureState skip_pass_pair_end(char* start, char* end){
    if (   start == NULL || strlen(start) == 0 
        || end   == NULL || strlen(end)   == 0){
        return SUCCESS;
    }
    StrRange* n_word = NULL;
    int level        = 1;
    int c_line_num   = line_num;
    int c_calm_num   = calm_num;
    int* LCI = get_LCI();
    while(level){
        skip_space(ALL);
        n_word = next_word(1);
        if (n_word){
            if( strcmp(n_word->str, start) == 0){
                level++;
            } else if(strcmp(n_word->str, end) == 0) {
                level--;
            }
            free_str_range(n_word); n_word = NULL; 
            continue;
        }
        // not word continue
        if (peek_char(0) == '"' && peek_char(-1) != '\\'){
            next_char();
            skip_pass('"');
            continue;
        }
        // continue
        if ( next_char() == EOF_CHAR ){
            break;
        };
    }
    if (level == 0){
        free(LCI); LCI = NULL;
        return SUCCESS;
    }
    fprintf(glb_log_out, "RTL ERROR %d-%ld: not found paired '%s' end '%s' !\n", c_line_num, c_calm_num - strlen(start), start, end);
    set_LCI(LCI);
    free(LCI); LCI = NULL;
    return FAILED;
}

RetureState skip_pass_pairs_end(int start_n, char** start, int end_n, char** end){
    if (start == NULL || end == NULL){
        return SUCCESS;
    }
    int* LCI = get_LCI();
    StrRange* n_word = NULL;
    int level        = 1;
    int c_line_num   = line_num;
    int c_calm_num   = calm_num;
    int i;
    while(level){
        n_word = next_word(1);
        if (n_word){
            for (i = 0; i < start_n; ++i){
                if(strcmp(n_word->str, start[i]) == 0){
                    level++;
                    break;
                }
            }
            for (i = 0; i < end_n; ++i){
                if(strcmp(n_word->str, end[i]) == 0){
                    level--;
                    break;
                }
            }
            free_str_range(n_word); n_word = NULL; 
            continue;
        }
        // not word continue
        if (peek_char(0) == '"'){
            next_char();
            skip_pass('"');
            continue;
        }
        // continue
        if ( next_char() == EOF_CHAR ){
            break;
        };
    }
    if (level == 0){
        free(LCI);
        return SUCCESS;
    }
    fprintf(glb_log_out, "RTL ERROR %d-%d: not found pairs !\n", c_line_num, c_calm_num);
    set_LCI(LCI); free(LCI);
    return FAILED;
}

//RetureState skip_pass_pairs_end_first_word(int start_n, char** start, int end_n, char** end){
//    if (start == NULL || end == NULL){
//        return SUCCESS;
//    }
//    int* LCI = get_LCI();
//    StrRange* n_word = NULL;
//    int level        = 1;
//    int c_line_num = line_num;
//    int c_calm_num = calm_num;
//    int i;
//    while(level){
//        skip_space(NONE);
//        n_word = next_word(1);
//        if (n_word){
//            for (i = 0; i < start_n; ++i){
//                if(strcmp(n_word->str, start[i]) == 0){
//                    level++;
//                    break;
//                }
//            }
//            for (i = 0; i < end_n; ++i){
//                if(strcmp(n_word->str, end[i]) == 0){
//                    level--;
//                    break;
//                }
//            }
//            free_str_range(n_word); n_word = NULL;
//            continue;
//        }
//        // not word continue
//        if (peek_char(0) == '"'){
//            next_char();
//            skip_pass('"');
//            continue;
//        }
//        // continue
//        if ( next_line(1) != SUCCESS ){
//            break;
//        };
//    }
//    if (level == 0){
//        free(LCI);
//        return SUCCESS;
//    }
//    fprintf(glb_log_out, "RTL ERROR %d-%d: not found pairs !\n", c_line_num, c_calm_num);
//    set_LCI(LCI); free(LCI);
//    return FAILED;
//}

int* pair_range(char left_p, char right_p){
    int level = 1;
    char c    = peek_char(0);
    if (c != left_p){
        return NULL;
    }
    int* range = malloc(sizeof(int)*4);
    if (range == NULL){
        exit(FATAL);
    }
    range[0] =logic_line_num;
    range[1] =calm_num;
    assert(next_char() == left_p);

    while ( 1 ) {
        range[2] = logic_line_num;
        range[3] = calm_num;
        c    = next_char();
        // if c is '"' need skip to next '"'
        if (c == '"'){
            skip_pass('"');
            continue;
        }
        // not string
        if (c == left_p) {
            level++;
        }
        if (c == right_p) {
            level--;
            if (level == 0) {
                break;
            }
        }
        if( c == EOF_CHAR){ // forward peek index
            break;
        };
    }
    if(level == 0) {
        return range;
    }
    fprintf(glb_log_out, "RTL ERROR %d-%d: %c has no corresponding %c !\n", range[0], range[1], left_p, right_p);
    return NULL;
}

//RetureState skip_char_pair(char left_p, char right_p){
//    int level = 1;
//    char c;
//    while ( 1 ) {
//        c    = next_char();
//        if (c == left_p) {
//            level++;
//        }
//        if (c == right_p) {
//            level--;
//            if (level == 0) {
//                break;
//            }
//        }
//        if( c == EOF_CHAR){ // forward peek index
//            break;
//        };
//    }
//    if(level == 0) {
//        return SUCCESS;
//    }
//    return FAILED;
//}

StrRange* match_pair(char left_p, char right_p){
    int  range[4];
    int  level       = 0;
    int  start_buf_i = glb_code_buf_i;
    char c           = peek_char(0);
    if (c != left_p){
        return NULL;
    }
    range[0] =logic_line_num;
    range[1] =calm_num;
    while ( 1 ) {
        range[2] = logic_line_num;
        range[3] = calm_num;
        c        = next_char();
        if (c == left_p) {
            level++;
        }
        if (c == right_p) {
            level--;
            if (level == 0){
                break;
            }
        }
        if( c == EOF_CHAR){ // forward peek index
            break;
        };
    }
    if(level == 0) {
        StrRange* r  = new_str_range();
        r->range[0]  = range[0];
        r->range[1]  = range[1];
        r->range[2]  = range[2];
        r->range[3]  = range[3];
        r->str       = str_copy(glb_code_buf, start_buf_i, glb_code_buf_i - 1);
        return r;
    }
    fprintf(glb_log_out, "RTL ERROR %d-%d: %c has no corresponding %c !\n", range[0], range[1], left_p, right_p);
    return NULL;
}

RetureState gen_verilog_token_tree(){
    // register token
    hash_add_pair(full_token_dic, "module"         , token_module_act      );
    hash_add_pair(full_token_dic, "endmodule"      , token_endmodule_act   );

    hash_add_pair(full_token_dic, "generate"       , token_next_line_act   );
    hash_add_pair(full_token_dic, "endgenerate"    , token_next_line_act   );

    hash_add_pair(full_token_dic, "function"       , token_function_act    );
    hash_add_pair(full_token_dic, "endfunction"    , token_next_line_act   );

    hash_add_pair(full_token_dic, "specify"        , token_specify_act     );
    hash_add_pair(full_token_dic, "endspecify"     , token_next_line_act   );

    hash_add_pair(full_token_dic, "case"           , token_case_act        );
    hash_add_pair(full_token_dic, "casez"          , token_case_act        );
    hash_add_pair(full_token_dic, "casex"          , token_case_act        );
    hash_add_pair(full_token_dic, "endcase"        , token_next_line_act   );
 
    hash_add_pair(full_token_dic, "always"         , token_always_act      );

    hash_add_pair(full_token_dic, "begin"          , token_begin_act       );
    hash_add_pair(full_token_dic, "end"            , token_next_line_act   );

    hash_add_pair(full_token_dic, "task"           , token_task_act        );
    hash_add_pair(full_token_dic, "endtask"        , token_next_line_act   );

    hash_add_pair(full_token_dic, "primitive"      , token_primitive_act   );
    hash_add_pair(full_token_dic, "endprimitive"   , token_next_line_act   );

    hash_add_pair(full_token_dic, "fork"           , token_next_line_act   );
    hash_add_pair(full_token_dic, "join"           , token_next_line_act   );
    hash_add_pair(full_token_dic, "join_none"      , token_next_line_act   );
    hash_add_pair(full_token_dic, "join_any"       , token_next_line_act   );

    hash_add_pair(full_token_dic, "if"             , token_if_act          );
    hash_add_pair(full_token_dic, "else"           , NULL                  );

    hash_add_pair(full_token_dic, "`define"        , token_mdefine_act     );
    hash_add_pair(full_token_dic, "`undef"         , token_next_line_act   ); // remove undefine to not miss any macro define
    hash_add_pair(full_token_dic, "`timescale"     , token_next_line_act   );
    hash_add_pair(full_token_dic, "`include"       , token_minclude_act    );
    hash_add_pair(full_token_dic, "`celldefine"    , token_next_line_act   );
    hash_add_pair(full_token_dic, "`endcelldefine" , token_next_line_act   );
    hash_add_pair(full_token_dic, "`protect"       , token_next_line_act   );
    hash_add_pair(full_token_dic, "`endprotect"    , token_next_line_act   );
    hash_add_pair(full_token_dic, "`resetall"      , token_next_line_act   );

    hash_add_pair(macro_cond_token_dic, "ifdef"    , token_mifdef_act      );
    hash_add_pair(macro_cond_token_dic, "ifndef"   , token_mifndef_act     );
    hash_add_pair(macro_cond_token_dic, "elsif"    , token_melsif_act      );
    hash_add_pair(macro_cond_token_dic, "else"     , token_melse_act       );
    hash_add_pair(macro_cond_token_dic, "endif"    , token_mendif_act      );

    // port declarations
    hash_add_pair(full_token_dic, "input"          , token_input_act       );
    hash_add_pair(full_token_dic, "output"         , token_output_act      );
    hash_add_pair(full_token_dic, "inout"          , token_inout_act       );

    hash_add_pair(full_token_dic, "import"         , token_next_line_act      );
    hash_add_pair(full_token_dic, "display"        , token_next_semicolon_act );
    hash_add_pair(full_token_dic, "assign"         , token_next_semicolon_act );
    hash_add_pair(full_token_dic, "defparam"       , token_next_semicolon_act );

    hash_add_pair(full_token_dic, "genvar"         , token_next_line_act   );
    hash_add_pair(full_token_dic, "for"            , token_next_line_act   );
    hash_add_pair(full_token_dic, "initial"        , NULL   );
    hash_add_pair(full_token_dic, "default"        , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "integer"        , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "logic"          , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "real"           , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "time"           , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "int"            , token_next_semicolon_act);

    hash_add_pair(full_token_dic, "force"          , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "event"          , token_next_semicolon_act);
    
    // sturct data type
    hash_add_pair(full_token_dic, "parameter"      , token_parameter_act     );
    hash_add_pair(full_token_dic, "wire"           , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "localparam"     , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "wand"           , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "wor"            , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "tri"            , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "supply0"        , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "supply1"        , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "reg"            , token_next_semicolon_act);

    // gate=level modeling
    hash_add_pair(full_token_dic, "and"            , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "nand"           , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "or"             , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "nor"            , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "xor"            , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "xnor"           , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "buf"            , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "not"            , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "tran"           , token_next_semicolon_act);

    // three-state buffer
    hash_add_pair(full_token_dic, "bufif0"         , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "bufif1"         , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "notif0"         , token_next_semicolon_act);
    hash_add_pair(full_token_dic, "notif1"         , token_next_semicolon_act);

    // Unsupported Gate-Level Constructs
    hash_add_pair(full_token_dic, "nmos"           , token_next_semicolon_act);   
    hash_add_pair(full_token_dic, "pmos"           , token_next_semicolon_act);   
    hash_add_pair(full_token_dic, "cmos"           , token_next_semicolon_act);   
    hash_add_pair(full_token_dic, "rnmos"          , token_next_semicolon_act);   
    hash_add_pair(full_token_dic, "rpmos"          , token_next_semicolon_act);   
    hash_add_pair(full_token_dic, "rcmos"          , token_next_semicolon_act);   
    hash_add_pair(full_token_dic, "pullup"         , token_next_semicolon_act);   
    hash_add_pair(full_token_dic, "pulldown"       , token_next_semicolon_act);   
    hash_add_pair(full_token_dic, "tranif0"        , token_next_semicolon_act);  
    hash_add_pair(full_token_dic, "tranif1"        , token_next_semicolon_act);  
    hash_add_pair(full_token_dic, "rtran"          , token_next_semicolon_act); 
    hash_add_pair(full_token_dic, "rtranif0"       , token_next_semicolon_act);  
    hash_add_pair(full_token_dic, "rtranif"        , token_next_semicolon_act); 

    return SUCCESS;
}

int* cnt_str_range(){  // for simple range include ',' or ';'
    int*      range = malloc( sizeof(int) * 4 );
    if (range == NULL){
        exit(FATAL);
    }

    int*      tmp_r  = NULL;
    char      tmp_c;
    skip_space(ALL);  // skip pre space
    if (peek_char(0) == '.'){
        return NULL;
    }
    int start_buf_i  = glb_code_buf_i;
    range[0] = logic_line_num;
    range[1] = calm_num;
    while(1){
        tmp_c = peek_char(0);
        if (tmp_c == '['){
            tmp_r = pair_range('[', ']');
            free(tmp_r); tmp_r = NULL;
            continue;
        }
        // pass {...}
        if (tmp_c == '{'){
            tmp_r = pair_range('{', '}');
            free(tmp_r); tmp_r = NULL;
            continue;
        }
        // pass (...)
        if (tmp_c == '('){
            tmp_r = pair_range('(', ')');
            free(tmp_r); tmp_r = NULL;
            continue;
        }
        // match other level ',' ';', ')' stop
        if (tmp_c == ',' || tmp_c == ';' || tmp_c == ')'){
            break;
        }
        range[2] = logic_line_num;
        range[3] = calm_num;
        if ( next_char() == EOF_CHAR ){
            break;
        }
    }
    if (glb_code_buf_i == start_buf_i){
        free(range); range = NULL;
        return NULL;
    }
    return range;
}

// OUT1, ..
// terminal_type == -1 means new in
// terminal_type == 0  a,b,c
// terminal_type == 1  .A(), .B()
// not allow 0 to 1
RetureState rec_match_terminals( VoidPtrLinkList* list, int terminal_type ){
    // new in need match '('
    if (terminal_type == -1){
        skip_space(ALL);
        if(peek_char(0) != '('){
            return FAILED;
        }
        next_char();
    }
    // match a terminal
    // CntInf* cnt_inf = new_cnt_inf();
    skip_space(ALL);
    if(peek_char(0) == ')'){ //() empty terminal
        // free_cnt_inf(cnt_inf); cnt_inf = NULL;
        return SUCCESS;
    } else if(peek_char(0) == '.'){ //(.A(a), ...)
        // not allow terminal_type 0 -> 1
        if (terminal_type == 0){
            fprintf(glb_log_out, "RTL ERROR %d-%d: not allow '(a,b,'follow '.A(..)'\n", line_num, calm_num);
            // free_cnt_inf(cnt_inf); cnt_inf = NULL;
            return FAILED;
        }
        next_char();
        terminal_type = 1;
        // no subio inf, get by sort
        skip_space(ALL);
        StrRange* sub_name = next_word(1);
        // cnt is a (...) get pos
        skip_space(ALL);
        int* cnt_range = pair_range('(', ')');
        if (cnt_range == NULL){
            fprintf(glb_log_out, "RTL ERROR %d-%d: not match .xxx(...)\n", line_num, calm_num);
            free(sub_name); sub_name = NULL;
            return FAILED;
        }
        CntInf* cnt_inf = new_cnt_inf();
        cnt_inf->sub_name_sr       = sub_name;
        cnt_inf->cnt_name_range[0] = cnt_range[0];
        cnt_inf->cnt_name_range[1] = cnt_range[1];
        cnt_inf->cnt_name_range[2] = cnt_range[2];
        cnt_inf->cnt_name_range[3] = cnt_range[3];
        vpll_push(list, cnt_inf);
        free(cnt_range); cnt_range = NULL;
    } else {
        char cnt_first_char = peek_char(0);
        int* cnt_range      = cnt_str_range();
        if (cnt_range){
            if (cnt_first_char == '`') {
                terminal_type = 2; // not sure it's type 0 or 1.
            } else {
                terminal_type = 0;
            }
            CntInf* cnt_inf = new_cnt_inf();
            cnt_inf->cnt_name_range[0]   = cnt_range[0];
            cnt_inf->cnt_name_range[1]   = cnt_range[1];
            cnt_inf->cnt_name_range[2]   = cnt_range[2];
            cnt_inf->cnt_name_range[3]   = cnt_range[3];
            vpll_push(list, cnt_inf);
            free(cnt_range); cnt_range = NULL;
        } else {
            return FAILED;
        }
    }
    // match other part ", terminal"
    // if match ','
    skip_space(ALL);
    if (peek_char(0) == ','){
        next_char();
        return rec_match_terminals( list, terminal_type );
    }
    // // some use `else ...
    // if (peek_char(0) == '.'){
    //     return rec_match_terminals( list, terminal_type );
    // }

    // match last ")"
    if (peek_char(0) == ')'){
        next_char();
        return SUCCESS;
    }

    // if already has some type, but no ',' and no end, maybe use '`', just skip it
    if (peek_char(0) == '`'){
        StrRange* tmp = next_word(1);
        free_str_range(tmp);   tmp = NULL;
        skip_space(ALL);
        if (peek_char(0) == '.'){
            return rec_match_terminals( list, terminal_type );
        }

        if (peek_char(0) == ','){
            next_char();
            return rec_match_terminals( list, terminal_type );
        }
        // match last ")"
        if (peek_char(0) == ')'){
            next_char();
            return SUCCESS;
        }
    }
    fprintf(glb_log_out, "RTL ERROR %d-%d: terminals no ')' !\n", line_num, calm_num );
    return FAILED;
}

InstInf* match_one_install(){
    InstInf*  i_inf = new_inst_inf();

    // skip space and macro contion
    skip_space(ALL);

    // match parm "#"
    if (peek_char(0) == '#'){
        next_char();
        // match (.parm(a), parm(b))
        if( rec_match_terminals(i_inf->parm_cnt_inf_list, -1) != SUCCESS){
            free_inst_inf(i_inf); i_inf = NULL;
            return NULL;
        };
    }

    // match "inst_name"
    skip_space(ALL);
    StrRange* inst_name = next_word(1);
    if (!inst_name){
        free_inst_inf(i_inf); i_inf = NULL;
        return NULL;
    }
    i_inf->inst_name_sr       = inst_name;
    i_inf->inst_line_range[0] = logic_line_num;

    // maybe instname follow a []
    while(1){
        skip_space(ALL);
        StrRange* sb_pair = match_pair('[', ']');
        if (sb_pair){
            assert( str_range_cat(i_inf->inst_name_sr, sb_pair) == SUCCESS);
            continue;
        }
        break;
    }

    // match (.io_a(a), io_b(b))
    if( rec_match_terminals(i_inf->iocnt_inf_list, -1) != SUCCESS){
        free_inst_inf(i_inf); i_inf = NULL;
        return NULL;
    };
    i_inf->inst_line_range[1] = logic_line_num;

#ifdef DEBUG
//    fprintf(glb_log_out, "Inst: %s %d - %d\n", i_inf->inst_name_sr->str, i_inf->inst_line_range[0], i_inf->inst_line_range[1]);
//    VoidPtrLinkNode* n = i_inf->parm_cnt_inf_list->head;
//    CntInf*      c_inf = NULL;
//    while(n){
//        c_inf = n->value;
//        if (c_inf->sub_name_sr) {
//            fprintf(glb_log_out, "    Parm: %s (%d,%d)(%d,%d) <-> (%d,%d)(%d,%d)\n",
//                   c_inf->sub_name_sr->str,
//                   c_inf->sub_name_sr->range[0],
//                   c_inf->sub_name_sr->range[1],
//                   c_inf->sub_name_sr->range[2],
//                   c_inf->sub_name_sr->range[3],
//                   c_inf->cnt_name_range[0],
//                   c_inf->cnt_name_range[1],
//                   c_inf->cnt_name_range[2],
//                   c_inf->cnt_name_range[3]
//                   );
//        } else {
//            fprintf(glb_log_out, "    Parm: ... <-> (%d,%d)(%d,%d)\n",
//                   c_inf->cnt_name_range[0],
//                   c_inf->cnt_name_range[1],
//                   c_inf->cnt_name_range[2],
//                   c_inf->cnt_name_range[3]
//                   );
//        }
//        n     = n->next;
//    }
//    n = i_inf->iocnt_inf_list->head;
//    c_inf = NULL;
//    while(n){
//        c_inf = n->value;
//        if (c_inf->sub_name_sr) {
//            fprintf(glb_log_out, "    IOCnt: %s (%d,%d)(%d,%d) <-> (%d,%d)(%d,%d)\n",
//                   c_inf->sub_name_sr->str,
//                   c_inf->sub_name_sr->range[0],
//                   c_inf->sub_name_sr->range[1],
//                   c_inf->sub_name_sr->range[2],
//                   c_inf->sub_name_sr->range[3],
//                   c_inf->cnt_name_range[0],
//                   c_inf->cnt_name_range[1],
//                   c_inf->cnt_name_range[2],
//                   c_inf->cnt_name_range[3]
//                   );
//        } else {
//            fprintf(glb_log_out, "    IOCnt: ... <-> (%d,%d)(%d,%d)\n",
//                   c_inf->cnt_name_range[0],
//                   c_inf->cnt_name_range[1],
//                   c_inf->cnt_name_range[2],
//                   c_inf->cnt_name_range[3]
//                   );
//        }
//        n     = n->next;
//    }
#endif
    return i_inf;
}

RetureState match_subcall(StrRange* submodule_name){
    // match first instance
    InstInf* i_inf = match_one_install();
    if (i_inf == NULL){
        return FAILED;
    }
    i_inf->submodule_name_sr = submodule_name;

    ModuleInf*       m_inf     = vpll_peek(glb_file_inf->module_inf_list);
    VoidPtrLinkList* inst_list = NULL;
    if ( m_inf && !(m_inf->module_end) ){
        inst_list = m_inf->inst_inf_list;
    } else {
        inst_list = glb_file_inf->wild_inst_inf_list;
    }
    vpll_push(inst_list, i_inf);
    
    // match other instance ", #(parm...) inst_name (io...)"
    int* LCI = NULL;
    while (1) {
        // pass space and macro condition
        skip_space(ALL);
        // match ','
        if(peek_char(0) != ','){
            break;
        };
        next_char();
        LCI = get_LCI();
        i_inf = match_one_install();
        if (i_inf == NULL){
            fprintf(glb_log_out, "RTL ERROR %d-%d: has ',' no following instance !\n", line_num, calm_num);
            set_LCI(LCI);
            free(LCI); LCI = NULL;
            break;
        }
        i_inf->submodule_name_sr = str_range_copy( submodule_name );
        vpll_push(inst_list, i_inf);
        free(LCI); LCI = NULL;
    }
    return SUCCESS;
}

RetureState next_line( int pass ){
    char c;

    while (1) {
        c = peek_char(0);
        if (c == '\n'){
            if( peek_char(-1) == '\\'){
                assert(next_char() == '\n');
                continue;
            }
            if (pass == 1){
                assert( next_char() == '\n' );
            }
            return SUCCESS;
        }
        if (c == EOF_CHAR) {
            return FAILED; // EOF
        }
        assert(next_char() != EOF_CHAR);
    }
    return FAILED;
}

RetureState token_if_act(){
    skip_space(ALL);
    int* Range = pair_range('(', ')');
    if (Range != NULL){
        free(Range); Range = NULL;
        return SUCCESS;
    }
    fprintf(glb_log_out, "RTL ERROR%d-%d: not match 'if(...)'\n",line_num, calm_num);
    return FAILED;
}

RetureState token_next_line_act(){
    next_line(1);
    return SUCCESS;
}

RetureState token_always_act(){
    skip_space(ALL);
    if (peek_char(0) == '@'){
        next_char();
        skip_space(ALL);
        int* Range = pair_range('(', ')');
        if (Range != NULL){
            free(Range); Range = NULL;
            return SUCCESS;
        }
    }
    return SUCCESS;
}

RetureState token_begin_act(){
    skip_pass_pair_end("begin", "end");
    next_line(1);
    return SUCCESS;
}

RetureState token_primitive_act(){
    skip_pass_pair_end("primitive", "endprimitive");
    next_line(1);
    return SUCCESS;
}

RetureState token_case_act(){
    char* starts[3] = {"case", "casez", "casex"};
    char* ends[1]   = {"endcase"};
    skip_pass_pairs_end(3, starts, 1, ends);
    next_line(1);
    return SUCCESS;
}

RetureState token_task_act(){
    skip_pass_pair_end("task", "endtask");
    next_line(1);
    return SUCCESS;
}

RetureState token_function_act(){
    skip_pass_pair_end("function", "endfunction");
    next_line(1);
    return SUCCESS;
}

RetureState token_specify_act(){
    skip_pass_pair_end("specify", "endspecify");
    next_line(1);
    return SUCCESS;
}

RetureState token_next_semicolon_act(){
    skip_pass(';');
    return SUCCESS;
}

RetureState token_module_act(){
    assert(glb_file_inf != NULL);
    skip_space(ALL);
    StrRange* module_name = next_word(1);    
    if (module_name == NULL){
        fprintf(glb_log_out, "RTL ERROR %d-%d: 'module' not following 'module_name'\n", line_num, calm_num);
        return FAILED;
    }
    // some module use `ifdef ... so maybe has no endmodule, need report
    ModuleInf* m_inf   = vpll_peek(glb_file_inf->module_inf_list);
    if (m_inf != NULL && m_inf->module_end == 0 ){
        fprintf(glb_log_out, "Note %d-%d: module '%s' has no 'endmodule'\n",
            m_inf->module_name_sr->range[0] - (logic_line_num - line_num), m_inf->module_name_sr->range[1],  m_inf->module_name_sr->str);
        m_inf->module_line_range[1] = logic_line_num - 1;
    }
    // new module
    m_inf                        = new_module_inf();
    m_inf->module_name_sr        = module_name;
    m_inf->module_line_range[0]  = logic_line_num;
    // add new code inf to module_inf
    CodeBlockInfo* c_block       = new_code_block_info();
    c_block->logic_line_range[0] = logic_line_num;
    c_block->file_path           = str_copy(glb_cur_file_path, 0, -1);
    c_block->real_line_range[0]  = line_num;
    vpll_push(m_inf->code_inf_list, c_block);
    // push to file_inf
    vpll_push(glb_file_inf->module_inf_list, m_inf);
#ifdef DEBUG
    fprintf(glb_log_out, "Match module %s\n", m_inf->module_name_sr->str);
#endif
    return SUCCESS;
}

RetureState token_endmodule_act(){
    ModuleInf* m_inf = vpll_peek(glb_file_inf->module_inf_list);
    // match a module start, no way back
    if (m_inf == NULL){
        fprintf(glb_log_out, "RTL ERROR %d: endmodule no corresponding module define ! \n", line_num );
        return FAILED;
    }
    // if module has two endmodule use macro diff, always use last one
    m_inf -> module_line_range[1] = logic_line_num;
    // add code block end
    CodeBlockInfo* c_block = vpll_peek(m_inf->code_inf_list);
    assert(c_block != NULL);
    c_block->logic_line_range[1] = logic_line_num;
    c_block->real_line_range[1]  = line_num;

    // update last code line boundry inf
    c_block->real_code_line_boundry = code_boundry_slice(glb_line_boundry_list, c_block->real_line_range[0], c_block->real_line_range[1]);

    m_inf -> module_end                           = 1;
#ifdef DEBUG
    fprintf(glb_log_out, "match_module_end  success !endmodule \n");
#endif
    return SUCCESS;
}

// parameter [range] identifier = expression, identifier = expression;
RetureState token_parameter_act(void){
    ModuleInf* m_inf = vpll_peek(glb_file_inf->module_inf_list);
    // not in module io, just go next line and report error
    if (!m_inf || m_inf->module_end){
        fprintf(glb_log_out, "RTL WARNING %d-%d: parameter not in valid module !\n", line_num, calm_num);
        skip_pass(';');
        return FAILED;
    }
    // skip [..][..]
    int*      sb_range   = NULL;
    skip_space(ALL);
    sb_range = pair_range('[', ']');
    while(sb_range){
        free(sb_range); sb_range = NULL;
        skip_space(ALL);
        sb_range = pair_range('[', ']');
    }
    while (1) {
        // match identifier
        skip_space(ALL);
        StrRange* identifier = next_word(0);
        // maybe "parameter a =x, parameter b = x"
        if ( identifier && (strcmp(identifier->str, "parameter") == 0)){
            free_str_range(identifier);
            skip_space(ALL);
            // new parameter need skip '[...]' again
            sb_range = pair_range('[',']');
            while(sb_range){
                free(sb_range); sb_range = NULL;
                skip_space(ALL);
                sb_range = pair_range('[', ']');
            }
            identifier = next_word(0);
        }
        // maybe parameter integer integer x = xxx , skip integer
        if ( identifier && (strcmp(identifier->str, "integer") == 0)){
            free_str_range(identifier);
            skip_space(ALL);
            identifier = next_word(0);
        }
        // real identifier
        if (!identifier) {
            fprintf(glb_log_out, "RTL ERROR %d-%d: parameter with valid identifier!\n", line_num, calm_num);
            next_line(1);
            return FAILED;
        }
        // match = expression
        skip_space(ALL);
        if (peek_char(0) != '=') {
            fprintf(glb_log_out, "RTL ERROR %d-%d: parameter %s miss '= xxx' !\n", line_num, calm_num, identifier->str);
            free_str_range(identifier);
            next_line(1);
            return FAILED;
        }
        next_char();
        skip_space(ALL);
        int* expression_range = cnt_str_range();
        free(expression_range); expression_range = NULL;
        vpll_push(m_inf->parm_inf_list, identifier);
        // if match ',', rec
        skip_space(ALL);
        if (peek_char(0) != ',') {
            break;
        }
        next_char();
    }
    // no need ckeck ";" parameter maybe end with ';' or ')'
    return SUCCESS;
}

RetureState rec_real_io_act(ModuleInf* m_inf, IOType io_type){
    // not in module io, just go next line and report error
    if (!m_inf || m_inf->module_end){
        fprintf(glb_log_out, "RTL WARNING %d-%d: io not in valid module !\n", line_num, calm_num);
        next_line(1);
        return FAILED;
    }
    skip_space(ALL);
    StrRange* word_range = next_word(0);
    int*      sb_range   = NULL;
    if (word_range){
        char* word = word_range->str;
        // next, input
        if (strcmp(word, "input")  == 0){
            free_str_range(word_range); word_range = NULL;
            return rec_real_io_act(m_inf, INPUT);
        }
        if (strcmp(word, "output")  == 0){
            free_str_range(word_range); word_range = NULL;
            return rec_real_io_act(m_inf, OUTPUT);
        }
        if (strcmp(word, "inout")  == 0){
            free_str_range(word_range); word_range = NULL;
            return rec_real_io_act(m_inf, INOUT);
        }
        // wiee, logic, reg
        while (   strcmp(word, "wire")   == 0
               || strcmp(word, "logic")  == 0
               || strcmp(word, "reg")    == 0
               || strcmp(word, "signed") == 0
               || strcmp(word, "real")   == 0)
        {
            free_str_range(word_range); word_range = NULL;
            skip_space(ALL);
            word_range = next_word(0);
            if (!word_range) {
                break;
            }
            word = word_range->str;
        }
    }
    if (!word_range) {
        // skip wire [..][..]
        skip_space(ALL);
        sb_range = pair_range('[', ']');
        while(sb_range){
            free(sb_range); sb_range = NULL;
            skip_space(ALL);
            sb_range = pair_range('[', ']');
        }
        skip_space(ALL);
        word_range = next_word(0);
    }
    
    // io name
    if (word_range == NULL){
        fprintf(glb_log_out, "RTL ERROR %d-%d: io has no name !\n", line_num, calm_num);
        return FAILED;
    }
    // new io inf
    IOInf* c_inf         = new_io_inf();
    c_inf->name_sr       = word_range;
    c_inf->type          = io_type;
    // skip [..][..]
    skip_space(ALL);
    sb_range = pair_range('[', ']');
    while(sb_range){
        free(sb_range); sb_range = NULL;
        skip_space(ALL);
        sb_range = pair_range('[', ']');
    }
    vpll_push(m_inf->io_inf_list, c_inf);
#ifdef DEBUG
//    fprintf(glb_log_out, "IO: (%d-%d) - (%d-%d) %d %s \n", c_inf->name_sr->range[0]
//                                           , c_inf->name_sr->range[1]
//                                           , c_inf->name_sr->range[2]
//                                           , c_inf->name_sr->range[3]
//                                           , io_type, c_inf->name_sr->str);
#endif
    // match ',' continun to next wire
    skip_space(ALL);
    char c = peek_char(0);
    if (c == ','){
        next_char();
        return rec_real_io_act(m_inf, io_type);
    }
    if (!(c == ';' || c == ')')){
        fprintf(glb_log_out, "RTL ERROR %d-%d: io not end with ';' or ')'\n", line_num, calm_num );
        // next_line(1);
    }
    return SUCCESS;
}

RetureState token_input_act(){
    ModuleInf* cur_module_inf = vpll_peek(glb_file_inf->module_inf_list);
    return rec_real_io_act(cur_module_inf, INPUT);
}

RetureState token_output_act(){
    ModuleInf* cur_module_inf = vpll_peek(glb_file_inf->module_inf_list);
    return rec_real_io_act(cur_module_inf, OUTPUT);
}

RetureState token_inout_act(){
    ModuleInf* cur_module_inf = vpll_peek(glb_file_inf->module_inf_list);
    return rec_real_io_act(cur_module_inf, INOUT);
}

char* str_to_next_line(int rep_line_beak){
    char c;
    int  i;
    char *str = NULL;
    int str_len = 0;
    // calculate length
    while(1){
        c = peek_char(str_len);
        if (c == '\n'){
            if( peek_char(str_len-1) == '\\'){
                str_len++;
                continue;
            }
            break;
        }
        if (c == EOF_CHAR){
            break;
        }
        str_len++;
    }
    //
    if (str_len == 0) {
        return NULL;
    }
    // malloc char
    str = malloc( sizeof(char) * (str_len + 1) );
    // copy char
    for (i = 0; i < str_len; ++i){
        str[i] = peek_char(i);
        if (rep_line_beak && str[i] == '\n'){
            assert(str[i-1] == '\\');
            str[i-1] = ' ';  // replace to space
            str[i]   = ' ';
        }
    }
    str[i] = '\0';
    return str;
}

char* strip_space(char* str, int free_old){
    if (!str) {
        return NULL;
    }
    int start_i;
    int end_i;
    int str_l = (int)strlen(str);
    char c;
    for (start_i = 0; start_i < str_l; start_i++) {
        c = str[start_i];
        if (c=='\t' || c=='\n' || c==' ' || c=='\r' || c == 0) {
            continue;
        }
        break;
    }
    for (end_i = str_l; end_i >= 0; end_i--) {
        c = str[end_i];
        if (c=='\t' || c=='\n' || c==' ' || c=='\r' || c == 0) {
            continue;
        }
        break;
    }
    if (start_i<=end_i) {
        char* new_str = str_copy(str, start_i, end_i);
        if (free_old == 1) {
            free(str);
        }
        return new_str;
    }
    if (free_old == 1) {
        free(str);
    }
    return NULL;
}

// include empty char '\t', '\n', ' ', '\r', ''
char* strip_char_and_empty(char* str, char s_char, int free_old){
    if (!str) {
        return NULL;
    }
    int start_i;
    int end_i;
    int str_l = (int)strlen(str);
    char c;
    for (start_i = 0; start_i < str_l; start_i++) {
        c = str[start_i];
        if (c=='\t' || c=='\n' || c==' ' || c=='\r' || c == 0 || c == s_char) {
            continue;
        }
        break;
    }
    for (end_i = str_l; end_i >= 0; end_i--) {
        c = str[end_i];
        if (c=='\t' || c=='\n' || c==' ' || c=='\r' ||  c == 0 || c == s_char) {
            continue;
        }
        break;
    }
    if (start_i<=end_i) {
        char* new_str = str_copy(str, start_i, end_i);
        if (free_old == 1) {
            free(str);
        }
        return new_str;
    }
    if (free_old == 1) {
        free(str);
    }
    return NULL;
}


char* rstrip(char* str, char s_char, int free_old){
    if (str == NULL){
        return NULL;
    }
    int end_i;
    int str_l = (int)strlen(str);
    char c;
    for (end_i = str_l - 1; end_i >= 0; end_i--) {
        c = str[end_i];
        if (c == s_char) {
            continue;
        }
        break;
    }
    if (end_i == -1){
        return NULL;
    }

    char* new_str = str_copy(str, 0, end_i);
    if (free_old == 1) {
        free(str);
    }
    return new_str;
}

RetureState token_mdefine_act(){
    skip_space(ALL);
    StrRange* name = next_word(1);
    if (!name){
        fprintf(glb_log_out, "RTL ERROR %d-%d: '`define' should follow a words !\n", line_num, calm_num);
        next_line(1);
        return FAILED;
    }    
    MacroDefine * c_inf                 = new_macro_define();
    // name use real line not logic line
    name->range[0]                      = line_num;
    name->range[2]                      = line_num;
    c_inf->name_sr                      = name;
    c_inf->file_state                   = new_file_state();
    c_inf->file_state->file_path        = str_copy(glb_cur_file_path, 0, -1);
    c_inf->file_state->last_modify_time = glb_cur_last_modify_time;
    c_inf->value                        = strip_space(str_to_next_line(1), 1);
    if (glb_parser_file_standalone) {
        // copy one because hash will cause unknown change
        MacroDefine * fm_inf     = new_macro_define();
        fm_inf->name_sr          = str_range_copy(c_inf->name_sr);
        fm_inf->file_state       = copy_file_state(c_inf->file_state);
        fm_inf->value            = str_copy(c_inf->value, 0, -1);
        vpll_push(glb_file_inf->macro_inf_list, fm_inf);
    }
    // always add to glb mdefine dic and only parser single file add file macro_inf
    hash_add_pair(glb_mdefine_dic, name->str, c_inf);
    next_line(0); // str_to_next_line not forward

 #ifdef DEBUG
     fprintf(glb_log_out, "Macro %d-%d: `define %s %s\n",line_num, calm_num, c_inf->name_sr->str, c_inf->value);
 #endif
    
    return SUCCESS;
}

RetureState token_mundef_act(){
    skip_space(ALL);
    StrRange* name = next_word(1);
    if (!name){
        fprintf(glb_log_out, "RTL ERROR %d-%d: '`undef' should follow a words !\n", line_num, calm_num);
        next_line(1);
        return FAILED;
    }
    hash_remove_key(glb_mdefine_dic, name->str);
#ifdef DEBUG
    fprintf(glb_log_out, "Undef %d-%d: `undef %s\n",line_num, calm_num, name->str);
#endif
    free_str_range(name); name = NULL;
    return SUCCESS;
}

RetureState token_minclude_act(){
    int cur_logic_line_num = logic_line_num;
    int cur_real_line_num  = line_num;
    char* inc_file_or_path = strip_char_and_empty(str_to_next_line(1), '"', 1);
    // no next line, for include file to next logic_line_num
    next_line(1);
    if (!inc_file_or_path) {
        fprintf(glb_log_out, "RTL ERROR %d-%d: not match '`include \"xxx\"' \n", line_num, calm_num);
        return FAILED;
    }
    // if it's file
    char* inc_file_path = inc_file_or_path;
    if (inc_file_or_path[0] != '/'){
        inc_file_path = search_incdir(glb_incdir_list, inc_file_or_path);
        if (!inc_file_path) {
            fprintf(glb_log_out, "RTL WARNING %d-%d: include file not found: \"%s\"\n", line_num, calm_num, inc_file_or_path);
            free(inc_file_or_path); inc_file_or_path = NULL;
            return FAILED;
        }
        free(inc_file_or_path); inc_file_or_path = NULL;
    }
    // if include file not in module and parser before not parser again
    // if in some module add include file state to module inf
    ModuleInf* c_m_inf = vpll_peek(glb_file_inf->module_inf_list);
    if (!c_m_inf || c_m_inf->module_end == 1) {
        HashNode* m_node = hash_search(glb_not_in_module_include_file_dic, inc_file_path);
        if (m_node) { // already passed before skip
            // match include set old block range end
            CodeBlockInfo* cur_code_inf = vpll_peek(glb_file_inf->code_inf_list);
            assert(cur_code_inf != NULL);
            cur_code_inf->logic_line_range[1] = cur_logic_line_num;
            cur_code_inf->real_line_range[1]  = cur_real_line_num;
            // add new code full block inf
            CodeBlockInfo* new_code_info_full       = new_code_block_info();
            new_code_info_full->file_path           = str_copy(inc_file_path, 0, -1);
            new_code_info_full->logic_line_range[0] = logic_line_num;   // already forward
            new_code_info_full->real_line_range[0]  = 0;
            new_code_info_full->logic_line_range[1] = logic_line_num++; // forward
            new_code_info_full->real_line_range[1]  = 1;
            vpll_push( glb_file_inf->code_inf_list, new_code_info_full);
            // add new start code block inf
            CodeBlockInfo* new_code_info_start       = new_code_block_info();
            new_code_info_start->file_path           = str_copy(glb_cur_file_path, 0, -1);
            new_code_info_start->logic_line_range[0] = logic_line_num;   // already forward
            new_code_info_start->real_line_range[0]  = line_num;
            vpll_push( glb_file_inf->code_inf_list, new_code_info_start);
            fprintf(glb_log_out, "Note %d-%d: inc file not in module already parsered, skip ! %s \n",line_num, calm_num, inc_file_path);
            return SUCCESS;
        }
        hash_add_pair(glb_not_in_module_include_file_dic, inc_file_path, NULL);
    }
    // switch context
    FileContext* new_fc = new_file_context(inc_file_path, 0);
    free(inc_file_path); inc_file_path = NULL;
    if (!new_fc) {
        fprintf(glb_log_out, "RTL ERROR %d-%d: inc file cannot open ! %s \n",line_num, calm_num, inc_file_path);
        return FAILED;
    }
    // push stack
    if ( push_file_context_stack() != SUCCESS){
        free_file_context(new_fc); new_fc  = NULL;
        return FAILED;
    }
    // if in some module add incude file state to module inf
    if (c_m_inf && c_m_inf->module_end == 0) {
        // match include set old block range end
        CodeBlockInfo* m_code_inf = vpll_peek(c_m_inf->code_inf_list);
        assert(m_code_inf != NULL);
        m_code_inf->logic_line_range[1] = cur_logic_line_num;
        m_code_inf->real_line_range[1]  = cur_real_line_num;
        // update last code line boundry inf
        m_code_inf->real_code_line_boundry = code_boundry_slice(glb_line_boundry_list, m_code_inf->real_line_range[0], m_code_inf->real_line_range[1]);

        // add new code block inf
        CodeBlockInfo* new_m_code_info       = new_code_block_info();
        new_m_code_info->file_path           = str_copy(new_fc->file_path, 0, -1);
        new_m_code_info->logic_line_range[0] = logic_line_num; // already forward
        new_m_code_info->real_line_range[0]  = new_fc->line_num;
        vpll_push( c_m_inf->code_inf_list, new_m_code_info);
    }
    // match include set old block range end
    CodeBlockInfo* cur_code_inf = vpll_peek(glb_file_inf->code_inf_list);
    assert(cur_code_inf != NULL);
    cur_code_inf->logic_line_range[1] = cur_logic_line_num;
    cur_code_inf->real_line_range[1]  = cur_real_line_num;
    // add new code block inf
    CodeBlockInfo* new_code_info       = new_code_block_info();
    new_code_info->file_path           = str_copy(new_fc->file_path, 0, -1);
    new_code_info->logic_line_range[0] = logic_line_num; // already forward
    new_code_info->real_line_range[0]  = new_fc->line_num;
    vpll_push( glb_file_inf->code_inf_list, new_code_info);
    active_file_context(new_fc, 0);
    return SUCCESS;
}

RetureState skip_to_endif(){
    char      c;
    StrRange* cnd_word   = NULL;
    int       level      = 1;
    int       start_line = line_num;
    int       start_calm = calm_num;
    while ( (c = real_next_char()) != EOF_CHAR ) {
        if (c != '`') {
            continue;
        }
        cnd_word = next_word(0);
        if (!cnd_word) {
            continue;
        }
        // match nest new macro condition
        if (   strcmp(cnd_word->str, "ifdef") == 0
            || strcmp(cnd_word->str, "ifndef") == 0)
        {
            free_str_range(cnd_word); cnd_word = NULL;
            level++;
            continue;
        }
        // match end macro condition
        if ( strcmp(cnd_word->str, "endif") == 0 ){
            free_str_range(cnd_word); cnd_word = NULL;
            level--;
            if (level == 0) { // means match same level `endif pass success
                pop_mcnd_stack();
                return SUCCESS;
            }
            continue;
        }
        // other macro just continue
        free_str_range(cnd_word); cnd_word = NULL;
    }
    fprintf(glb_log_out, "RTL ERROR %d-%d: skip_to_endif failed \n", start_line, start_calm);
    return FAILED;
}

RetureState skip_to_next_mcnd(){
    char      c;
    StrRange* cnd_word = NULL;
    int       start_line = line_num;
    int       start_calm = calm_num;
    while ( (c = real_next_char()) != EOF_CHAR ) {
        if (c != '`') {
            continue;
        }
        cnd_word = next_word(0);
        if (!cnd_word) {
            continue;
        }
        // match nest new macro condition
        if (   strcmp(cnd_word->str, "ifdef") == 0
            || strcmp(cnd_word->str, "ifndef") == 0)
        {
            push_mcnd_stack();
            free_str_range(cnd_word); cnd_word = NULL;
            if( skip_to_endif() != SUCCESS ){
                break; // Failed
            }
            continue;
        }
        // match end macro condition
        if ( strcmp(cnd_word->str, "endif") == 0 ){
            free_str_range(cnd_word); cnd_word = NULL;
            return token_mendif_act();
        } else if (strcmp(cnd_word->str, "else")  == 0){
            free_str_range(cnd_word); cnd_word = NULL;
            return token_melse_act();
        } else if(strcmp(cnd_word->str, "elsif") == 0){
            free_str_range(cnd_word); cnd_word = NULL;
            return token_melsif_act();
        }
        free_str_range(cnd_word); cnd_word = NULL;
    }
    fprintf(glb_log_out, "RTL ERROR %d-%d: skip_to_next_mcnd failed \n", start_line, start_calm);
    return FAILED;
}

RetureState token_mifdef_act(){
    real_skip_space();
    StrRange* macro_name = next_word(0);
    if (!macro_name) {
        fprintf(glb_log_out, "RTL ERROR %d-%d: '`ifdef xxx' no 'xxx' \n", line_num, calm_num);
        return FAILED;
    }
    HashNode* node = hash_search(glb_mdefine_dic, macro_name->str);
    push_mcnd_stack(); // push old cnd
    // set new cond
    if (node) {
        glb_mcnd_meet = 1;
    } else {
        glb_mcnd_meet = 0;
    }
    // printf("`ifdef %d-%d %s' \n", line_num, calm_num, macro_name->str);
    free(macro_name); macro_name = NULL;
    // define
    if (glb_mcnd_meet) {
        return SUCCESS;
    }
    return skip_to_next_mcnd();
}

RetureState token_mifndef_act(){
    real_skip_space();
    StrRange* macro_name = next_word(0);
    if (!macro_name) {
        fprintf(glb_log_out, "RTL ERROR %d-%d: '`ifndef xxx' no 'xxx' \n", line_num, calm_num);
        return FAILED;
    }
    HashNode* node = hash_search(glb_mdefine_dic, macro_name->str);
    push_mcnd_stack(); // push old cnd
    // set new cond
    if (node) {
        glb_mcnd_meet = 0;
    } else {
        glb_mcnd_meet = 1;
    }
    // printf("`ifndef %d-%d %s:%d' \n", line_num, calm_num, macro_name->str, glb_mcnd_meet);
    free(macro_name); macro_name = NULL;
    // define
    if (glb_mcnd_meet) {
        return SUCCESS;
    }
    return skip_to_next_mcnd();
}

RetureState token_melsif_act(){
    if (glb_mcnd_meet) {
        return skip_to_endif();
    }
    // check condition
    real_skip_space();
    StrRange* macro_name = next_word(0);
    if (!macro_name) {
        fprintf(glb_log_out, "RTL ERROR %d-%d: not match '`elsif xxx' \n", line_num, calm_num);
        return FAILED;
    }
    HashNode* node = hash_search(glb_mdefine_dic, macro_name->str);
    // set new cnd
    if (node) {
        glb_mcnd_meet = 1;
    } else {
        glb_mcnd_meet = 0;
    }
    // printf("`elsif %d-%d %s:%d' \n", line_num, calm_num, macro_name->str, glb_mcnd_meet);
    free(macro_name); macro_name = NULL;
    if (glb_mcnd_meet) {
        return SUCCESS;
    }
    return skip_to_next_mcnd();
}

RetureState token_melse_act(){
    // not meet and `if of `elseif, must use `else code
    if (glb_mcnd_meet) {
        return skip_to_endif();
    }
    // use `else line
    return SUCCESS;
}

RetureState token_mendif_act(){
    return pop_mcnd_stack();
}

RetureState parser_one_file(){
    // init glb value
    HashNode*        reserved_node    = NULL;
    Action           reserved_act     = NULL;
    StrRange*        word             = NULL;
    int*             CLI              = NULL;
    int*             range            = NULL;
    int              unknown_word_cnt = 0;     

    assert(glb_file_context_stack->length == 0);
    assert(glb_mcnd_top == -1);
  
    while(1){
        if (glb_old_code_buf_i < glb_code_buf_i){  // continue old file centext
            glb_old_code_buf_i = glb_code_buf_i;
        } else {
            // buf not move forward, and code not parser out, parser must has bug
            if (glb_code_buf_i < glb_code_buf_size) {
                fprintf(glb_log_out, "ERROR: buf_i cannot forward! file=%s, line=%d, calum=%d",glb_cur_file_path, line_num, calm_num);
            }
            // try switch context
            FileContext* pre_file_context = glb_file_context;
            if( pop_file_context_stack() ){ // switch new file centext
                // means in some include file, current just free include file inf
                free_file_context(pre_file_context); pre_file_context = NULL;
            } else {
                // finish all file code
                break;
            }
        }
        // skip space
        // fprintf(glb_log_out, "^_^ 2: %d-%d\n", line_num, calm_num);
        skip_space(ALL);
        // fprintf(glb_log_out, "^_^ 3: %d-%d\n", line_num, calm_num);

        // get next word
        word = next_word(1);

        if (word == NULL){
            next_char();
            continue;
        }

        // match reserved function
        reserved_node = hash_search(full_token_dic, word->str);
        if (reserved_node){
            free_str_range(word); word = NULL;
            reserved_act = reserved_node->value;
            if (reserved_act == NULL){
                unknown_word_cnt = 0;
                continue;
            }
            if ( (*reserved_act)() != SUCCESS){
                continue;
            };
            unknown_word_cnt = 0;
            continue;
        }

        // match subcall
        CLI = get_LCI();
        if( match_subcall(word) == SUCCESS){
            // word is submodule no need free
            free(CLI); CLI = NULL;
            unknown_word_cnt = 0;
            continue;
        }
        // word used as subcall name not free
        set_LCI(CLI);
        free(CLI); CLI = NULL;
        // }
        skip_space(ALL);
        // match XXX <= ...
        range = pair_range('[', ']');
        while(range){
            free(range); range = NULL;
            skip_space(ALL);
            range = pair_range('[', ']');
        }
        skip_space(ALL);
        char c = peek_char(0);
        if(    c == ','   // port def 
            || c == ')'   // last port def 
            || c == '('   // function or task
            || c == '='   // nonblock assign 
            || (c == '<' & peek_char(1) == '=') // block 
        ){
            skip_pass(';');
            free_str_range(word); word = NULL;
            unknown_word_cnt = 0;
            continue;
        }
        // else unknown word report and go next line, skip speace maybe pass `ifdef so line_num maybe to much
        fprintf(glb_log_out, "WARNING %d-%d: UnKnown COMMON_WORD = %s\n", line_num, calm_num, word->str);
        free_str_range(word); word = NULL;
        // if has continue 100 unknown word just stop this file
        if ( (unknown_word_cnt++) > 100 ){
            fprintf(glb_log_out, "RTL ERROR %d-%d: too many UnKnown common word !\n", line_num, calm_num);
            clear_vpll(glb_file_context_stack);
            glb_mcnd_top = -1;
            free_file_context(glb_file_context); glb_file_context = NULL;
            return FAILED;
        }
    }

    // if at file end current module start and not end , let last line as module end
    ModuleInf*  m_inf = NULL;
    m_inf = vpll_peek(glb_file_inf->module_inf_list);
    if (m_inf && !m_inf->module_end){
        fprintf(glb_log_out, "RTL ERROR %d: module '%s' no corresponding endmodule !\n",m_inf->module_line_range[0] - (logic_line_num - line_num), m_inf->module_name_sr->str );
        m_inf ->module_line_range[1] = logic_line_num;
        CodeBlockInfo* m_code_inf = vpll_peek(m_inf->code_inf_list);
        assert(m_code_inf != NULL);
        m_code_inf->logic_line_range[1] = logic_line_num;
        m_code_inf->real_line_range[1]  = line_num;

        // update last code line boundry inf
        m_code_inf->real_code_line_boundry = code_boundry_slice(glb_line_boundry_list, m_code_inf->real_line_range[0], m_code_inf->real_line_range[1]);

    }
    // check file glb state
    if(glb_mcnd_top != -1){
        fprintf(glb_log_out, "RTL ERROR: %d-%d: file mcondition stack len = %d not empty ! %s\n", line_num, calm_num, glb_mcnd_top+1, glb_file_context->file_path);
        glb_mcnd_top = -1;
    }
    return SUCCESS;
}

char* search_incdir(VoidPtrLinkList* incdir_list, char* file_name){
    int i;
    // copy dir list
    VoidPtrLinkNode* c_node      = incdir_list->head;
    // if has relative path at file_name added to dir path
    long  start          = 0;
    long  end            = strlen(file_name);
    char* relative_path  = rstrip( str_to_next_char('/', file_name, &start, end), '/', 1 );
    char* real_file_name = NULL;
    char* real_dir_path  = NULL;
    char* c_dir_path     = NULL;
    
    if (relative_path) {
        real_file_name = malloc(sizeof(char) *  (end - start + 2) );
        if (!real_file_name) {
            exit(FATAL);
        }
        for (i = (int)start; i < end ; i++) {
            real_file_name[i-start] = file_name[i];
        }
        real_file_name[i-start] = '\0';
    } else {
        real_file_name = strip_space(file_name, 0);
    }
    
    // rec get all file
    while( c_node && (c_dir_path = rstrip(c_node->value, '/', 0) ) ){
        c_node = c_node->next;
        // get real dir path
        if (relative_path) {
            real_dir_path = malloc(sizeof(char) * ( strlen(c_dir_path) + strlen(relative_path) + 3 ));
            if (!real_dir_path) {
                exit(FATAL);
            }
            assert(strcpy(real_dir_path, c_dir_path));
            assert(strcat(real_dir_path, "/"));
            assert(strcat(real_dir_path, relative_path));
            free(c_dir_path); c_dir_path = NULL;
        } else {
            real_dir_path = c_dir_path;
            c_dir_path    = NULL;
        }
        
        struct dirent *dp;
        DIR *dir = opendir(real_dir_path);
        // Unable to open directory stream
        if (!dir) {
            free(real_dir_path); real_dir_path = NULL;
            continue;
        }
        // start get all file in current dir
        int   c_dir_path_len = (int)strlen(real_dir_path);
        char* c_full_path    = NULL;
        long  c_name_len     = 0;
        while ((dp = readdir(dir)) != NULL){
            if (strcmp(dp->d_name, real_file_name) != 0) {
                continue;
            }
            c_name_len  = strlen(real_file_name);
            c_full_path = malloc( sizeof(char) * (c_dir_path_len + c_name_len + 3) );
            if (!c_full_path){
                exit(FATAL);
            }
            assert( strcpy(c_full_path, real_dir_path) );
            assert( strcat(c_full_path, "/") );
            assert( strcat(c_full_path, real_file_name) );
            free(real_dir_path);  real_dir_path  = NULL;
            free(relative_path);  relative_path  = NULL;
            free(real_file_name); real_file_name = NULL;
            return c_full_path; // find match
        }
        closedir(dir);
    }
    free(real_dir_path);  real_dir_path  = NULL;
    free(relative_path);  relative_path  = NULL;
    free(real_file_name); real_file_name = NULL;
    return NULL; // not found
}

// Lists all files and sub-directories at given path.
VoidPtrLinkList* list_dirs_files(VoidPtrLinkList* in_dir_list){
    VoidPtrLinkList* dir_list   = new_vpll(free, NULL);
    VoidPtrLinkList* file_list  = new_vpll(free, NULL);
    // copy dir list
    char*            in_dir_path = NULL;
    char*            c_dir_path  = NULL;
    VoidPtrLinkNode* c_node = in_dir_list->head;
    while (c_node) {
        in_dir_path = c_node->value;
        c_dir_path  = malloc(sizeof(char)* (strlen(in_dir_path) + 1) );
        if (!c_dir_path) {
            exit(FATAL);
        }
        assert(strcpy(c_dir_path, in_dir_path));
        vpll_push(dir_list, c_dir_path);
        c_node = c_node->next;
    }
    
    // rec get all file
    while( (c_dir_path = vpll_pop(dir_list)) ){
        struct dirent *dp;
        DIR *dir = opendir(c_dir_path);
        // Unable to open directory stream
        if (!dir) {
            continue;
        }
        // start get all file in current dir
        int   c_dir_path_len = (int)strlen(c_dir_path);
        char* c_full_path    = NULL;
        long  c_name_len     = 0;
        int   i,j;
        while ((dp = readdir(dir)) != NULL){
            if (dp->d_name[0] == '.') {
                continue;
            }
            c_name_len  = strlen(dp->d_name);
            c_full_path = malloc( sizeof(char) * (c_dir_path_len + c_name_len + 3) );
            if (!c_full_path){
                exit(FATAL);
            }
            for (i = 0; i<c_dir_path_len; i++) {
                c_full_path[i] = c_dir_path[i];
            }
            if (c_full_path[i-1] != '/'){
                c_full_path[i] = '/';
                i++;
            }
            for (j=0; j<c_name_len; j++) {
                c_full_path[i+j] = dp->d_name[j];
            }
            c_full_path[i+j] = '\0';
            // file
            if (dp->d_type == DT_REG){
                vpll_push(file_list, c_full_path);
                continue;
            }
            // die
            if (dp->d_type == DT_DIR){
                vpll_push(dir_list, c_full_path);
            }
        }
        // Close directory stream
        free(c_dir_path); c_dir_path = NULL;
        closedir(dir);
    }
    // deal subdir
    free_vpll(dir_list); dir_list = NULL;
    // while ( (c_dir_path = vpll_pop(file_list)) ) {
    //    printf("\n%s",c_dir_path);
    // }
    return file_list;
}

FileListInf* new_file_list_inf(){
    FileListInf* fl_inf = malloc( sizeof(FileListInf) );
    if (!fl_inf){
        exit(FATAL);
    }
    fl_inf->parser_out_dir         = NULL;
    fl_inf->parser_file_standalone = 0;
    fl_inf->file_inf_list          = new_vpll(free_file_list_file_inf, NULL);
    fl_inf->incdir_list            = new_vpll(free, NULL);
    fl_inf->define_list            = new_vpll(free_macro_define, NULL);
    return fl_inf;
}

void free_file_list_inf(void* fl_inf){
    if (!fl_inf) {
        return;
    }
    FileListInf* c_inf = fl_inf;
    free(c_inf->parser_out_dir);     c_inf->parser_out_dir  = NULL;
    free_vpll(c_inf->file_inf_list); c_inf->file_inf_list   = NULL;
    free_vpll(c_inf->incdir_list);   c_inf->incdir_list     = NULL; glb_incdir_list = NULL;
    free_vpll(c_inf->define_list);   c_inf->define_list     = NULL;
    free(fl_inf);
}

char* str_to_next_char(char c, char* buf, long* start, long end){
    long c_start = *start;
    c_start      = skip_space_str(buf, c_start, end);
    long i;
    for (i = c_start; i < end; i++) {
        if (buf[i] == c) {
            break;
        }
    }
    if (i == end) {
        return NULL;
    }
    char* str = str_copy(buf, c_start, i);
    *start = i + 1; // update next pos
    return str;
}

char* str_to_next_space(char* buf, long* start, long end){
    long c_start = *start;
    c_start      = skip_space_str(buf, c_start, end);
    long i;
    char c;
    for (i = c_start; i < end; i++) {
        c = buf[i];
        if (c=='\t' || c=='\n' || c==' ' || c=='\r') {
            break;
        }
    }
    if (i == c_start) {
        return NULL;
    }
    char* str = str_copy(buf, c_start, i-1);
    *start = i; // update next pos
    return str;
}

// type: 0 unknown, 1: define, 2:incdir, +++
RetureState paser_vcs_cmd(FileListInf* fl_inf, char* buf, long start, long end, int type){
    int i;
    start          = skip_space_str(buf, start, end);
    if (buf[start] != '+') {
        return FAILED; // always sep with '+'
    }
    start         = start + 1; // pass '+'
    start         = skip_space_str(buf, start, end);
    char* tmp_str = next_word_str(buf, &start, end);
    if (!tmp_str) {
        return FAILED;
    }
    // type is define
    if (strcmp(tmp_str, "define") == 0) {
        free(tmp_str); tmp_str = NULL;
        char* macro_name  = NULL;
        char* macro_value = NULL;
        start = skip_space_str(buf, start, end);
        if (buf[start] != '+') {
            return FAILED; // always sep with '+'
        }
        start   = start + 1; // pass '+'
        start   = skip_space_str(buf, start, end);
        // macro name
        macro_name = next_word_str(buf, &start, end);
        if (!macro_name){
            return FAILED;
        }
        // macro value
        start   = skip_space_str(buf, start, end);
        if (buf[start] == '='){
            start   = start + 1; // pass '='
            start   = skip_space_str(buf, start, end);
            macro_value = malloc( sizeof(char) * (end - start + 2) );
            if (!macro_value){
                exit(FATAL);
            }
            for (i = (int)start; i < end; ++i){
                macro_value[i-start] = buf[i];
            }
            macro_value[i-start] = '\0';
        }
        MacroDefine* c_def = new_macro_define();
        c_def->file_state   = NULL;
        c_def->name_sr      = new_str_range();
        c_def->name_sr->str = macro_name;
        c_def->value        = strip_space(macro_value, 1);
        hash_add_pair(glb_mdefine_dic, macro_name, c_def);
        return SUCCESS;
    }
    // type is incdir
    if (strcmp(tmp_str, "incdir") == 0){
        free(tmp_str); tmp_str =NULL;
        char* dir_path = NULL;
        start = skip_space_str(buf, start, end);
        if (buf[start] != '+') {
            return FAILED; // always sep with '+'
        }
        start = start + 1; // pass '+'
        start = skip_space_str(buf, start, end);
        dir_path = str_to_next_space(buf, &start, end);
        if (!dir_path) {
            return FAILED;
        }
        vpll_push(fl_inf->incdir_list, strip_space(dir_path, 1));
        return SUCCESS;
    }
    // type is parser_out_dir
    if (strcmp(tmp_str, "parser_out_dir") == 0){
        free(tmp_str); tmp_str =NULL;
        start = skip_space_str(buf, start, end);
        if (buf[start] != '+') {
            return FAILED; // always sep with '+'
        }
        start = start + 1; // pass '+'
        start = skip_space_str(buf, start, end);
        fl_inf->parser_out_dir = str_to_next_space(buf, &start, end);
        return SUCCESS;
    }
    // type is parser_file_standalone
    if (strcmp(tmp_str, "parser_file_standalone") == 0){
        free(tmp_str); tmp_str =NULL;
        start = skip_space_str(buf, start, end);
        if (buf[start] != '+') {
            return FAILED; // always sep with '+'
        }
        start = start + 1; // pass '+'
        start = skip_space_str(buf, start, end);
        if (buf[start] == '1') {
            fl_inf->parser_file_standalone = 1;
        } // else default = 0
        return SUCCESS;
    }
    return FAILED;
}

// use python output clean filelist, support follow format
// 1. +indir+<dir_path>\n
// 2. +define+<define>\n
// 3. +parser_out_dir+<dir_path>\n
// 4. +parser_file_standalone+<0|1>\n
// 4. -v <file_path>\n
// 5. <file_path>\n
//      file_path only support :  '/...' or '$xxx/...'
// 6. dont allow same name files(even thay have different path)
FileListInf* parser_file_list( char* file_list_path){
    
    FileListInf* c_fl_inf = new_file_list_inf();
    long  c_line_len, c_char_i;
    int   file_num    = 0;
    char  out_file_prefix[6+32];
    char* c_line;
    // generate a file list file contex
    FileContext* fl_fc = new_file_context(file_list_path, 0);
    if (!fl_fc) {
        return NULL;
    }
    active_file_context(fl_fc, 0);
    while ( (c_line = str_to_next_line(1)) ) {
        next_line(1);
        c_line_len = strlen(c_line);
        c_char_i   = 0;
        c_char_i   = skip_space_str(c_line, c_char_i, c_line_len);
        // skip '//'
        if (   (c_char_i + 1 < c_line_len - 1)
            && (c_line[c_char_i] == '/')
            && (c_line[c_char_i+1] == '/')){
            continue;
        }
        // +parser_out_dir+
        // +parser_file_standalone+
        // +define+macro=value+
        // +incdir+directory+
        if ((c_char_i< c_line_len - 1) && c_line[c_char_i] == '+') {
            if( paser_vcs_cmd(c_fl_inf, c_line, c_char_i, c_line_len, 0) != SUCCESS){
                fprintf(glb_log_out, "FILELIST WARNING: '%s':%d  unknown syntax ‘%s’ \n",file_list_path, line_num, c_line);
            }
            continue;
        }
        // -v filename 　　　　　 RTL文件列表
        if (  (c_char_i + 1 < c_line_len - 1)
            && c_line[c_char_i] == '-'
            && c_line[c_char_i+1] == 'v' ) {
            c_char_i = c_char_i + 2;
            long n_char_i = skip_space_str(c_line, c_char_i, c_line_len);
            if (n_char_i <= c_char_i) { // -v should follow a space
                fprintf(glb_log_out, "FILELIST WARNING: '%s':%d  unknown syntax ‘%s’ \n",file_list_path, line_num, c_line);
                continue;
            }
            c_char_i = n_char_i;
        }
        // file path must be start '/'
        if (   (c_char_i < c_line_len - 1)
            && c_line[c_char_i] != '/'){
            fprintf(glb_log_out, "FILELIST WARNING: '%s':%d  unknown syntax ‘%s’ \n",file_list_path, line_num, c_line);
            continue;
        }
        // add new file path to fl_inf
        char* c_file_path = str_to_next_space(c_line, &c_char_i, c_line_len);
        if (!c_file_path) {
            fprintf(glb_log_out, "FILELIST WARNING: '%s':%d  unknown syntax ‘%s’ \n",file_list_path, line_num, c_line);
            continue;
        }
        // get file inf serilation follow by "-s"
        c_char_i = skip_space_str(c_line, c_char_i, c_line_len);
        char* serilation_file_name = NULL;
        if (  (c_char_i + 1 < c_line_len - 1)
            && c_line[c_char_i] == '-'
            && c_line[c_char_i+1] == 's' ) {
            c_char_i = c_char_i + 2;
            long n_char_i = skip_space_str(c_line, c_char_i, c_line_len);
            if (n_char_i <= c_char_i) { // -s should follow a space
                fprintf(glb_log_out, "FILELIST WARNING: '%s':%d  unknown syntax ‘%s’ \n",file_list_path, line_num, c_line);
                continue;
            }
            c_char_i = n_char_i;
            serilation_file_name = str_to_next_space(c_line, &c_char_i, c_line_len);
        }
        // get file inf serilation out file name, use "parser%s_<file_name>",file_number
        if (!serilation_file_name) {
            sprintf(out_file_prefix, "parser%d_", file_num);
            serilation_file_name = str_cat_free(out_file_prefix, 0, replace_no_word_char_to_space(file_path_to_name(c_file_path), 1), 1);
            serilation_file_name = str_cat_free(serilation_file_name, 1, ".py", 0);
        }
        FileListFileInf* flf_inf = new_file_list_file_inf();
        flf_inf->file_path = c_file_path;
        flf_inf->out_name  = serilation_file_name;
        vpll_push(c_fl_inf->file_inf_list, flf_inf);
        file_num++;
    }
    deactive_file_context();
    free_file_context(fl_fc);
    
    if (!c_fl_inf->parser_out_dir) {
        free_file_list_inf(c_fl_inf);
        fprintf(glb_log_out, "FILELIST ERROR: please use +parser_out_dir+ specify out put dir path !\n");
        return NULL;
    }
    
    return c_fl_inf;
}

ParserResult* new_parser_rseult(){
    ParserResult* r = malloc( sizeof(ParserResult) );
    if (!r){
        exit(FATAL);
    }
    r->file_inf_list = NULL;
    r->mdefile_pair_list = NULL;
    r->father_inst_pair_list = NULL;
    return r;
}

void free_parser_rseult(void* pr){
    if (!pr){
        return;
    }
    ParserResult* r = pr;
    free_vpll(r->file_inf_list); r->file_inf_list = NULL;
    free_vpll(r->mdefile_pair_list); r->mdefile_pair_list = NULL;
    free_vpll(r->father_inst_pair_list); r->father_inst_pair_list = NULL;
    free(r);
}

void gather_mix_merge_inf(void){
    // update farther inst dic
    if (!glb_file_inf){
        return;
    }
    // iteration and update
    VoidPtrLinkList* module_inf_list = NULL;
    if ((module_inf_list = glb_file_inf->module_inf_list)) {
        // iteration module
        VoidPtrLinkNode* module_node = module_inf_list->head;
        ModuleInf*       module_inf = NULL;
        while (module_node) {
            module_inf  = module_node->value;
            module_node = module_node->next;
            // iteration inst
            if (!module_inf){
                continue;
            }
            // update module_file_list_dic
            HashNode* m_node = hash_search(glb_module_path_dic, module_inf->module_name_sr->str);
            if (!m_node) {
                hash_add_pair(glb_module_path_dic, module_inf->module_name_sr->str, str_copy(glb_file_inf->file_state->file_path, 0, -1));
            } else {
                char* old_path = m_node->value;
                fprintf(glb_log_out, "RTL WARNING: module:'%s' define in multi files, use first:\n    '%s'\n    '%s'\n", module_inf->module_name_sr->str, old_path, glb_file_inf->file_state->file_path);
            }
            // update father insts and child module
            HashNode* child_module_node  = NULL;
            // get child_module_dic pointer
            child_module_node = hash_search(glb_child_module_dic, module_inf->module_name_sr->str);
            // find and initial child_module_dic
            if (!child_module_node) {
                hash_add_pair(glb_child_module_dic, module_inf->module_name_sr->str, new_hash_table(free, str_serialize));
                child_module_node = hash_search(glb_child_module_dic, module_inf->module_name_sr->str);
            }
            assert(child_module_node);
            // update father insts and child module
            if( module_inf->inst_inf_list){
                VoidPtrLinkNode* inst_node          = module_inf->inst_inf_list->head;
                InstInf*         inst_inf           = NULL;
                char*            father_inst        = NULL;
                HashNode*        module_dic_node    = NULL;
                HashNode*        file_path_dic_node = NULL;
                HashTable*       file_path_dic      = NULL;
                // start update for each inst
                while (inst_node) {
                    inst_inf  = inst_node->value;
                    inst_node = inst_node->next;
                    // update child module dic
                    hash_add_pair(child_module_node->value, inst_inf->submodule_name_sr->str, NULL);
                    // start update father inst inf
                    father_inst = str_cat(module_inf->module_name_sr->str, ".");
                    father_inst = str_cat_free(father_inst, 1, inst_inf->inst_name_sr->str, 0);
                    module_dic_node = hash_search(glb_father_insts_dic, inst_inf->submodule_name_sr->str);
                    // find and initial module dic
                    if (!module_dic_node) {
                        hash_add_pair(glb_father_insts_dic, inst_inf->submodule_name_sr->str, new_hash_table(free_vpll, vpll_serialize));
                        module_dic_node  = hash_search(glb_father_insts_dic, inst_inf->submodule_name_sr->str);
                    }
                    assert(module_dic_node);
                    // find and initial filepath dic
                    file_path_dic = module_dic_node->value;
                    assert(file_path_dic);
                    file_path_dic_node = hash_search(file_path_dic, glb_file_inf->file_state->file_path);
                    if (!file_path_dic_node) {
                        hash_add_pair(file_path_dic, glb_file_inf->file_state->file_path, new_vpll(free, str_serialize));
                        file_path_dic_node  = hash_search(file_path_dic, glb_file_inf->file_state->file_path);
                    }
                    vpll_push(file_path_dic_node->value, father_inst);
                }
            }
        }
    }
}

RetureState api_parser_from_file_list(char* fl_path, char* log_path){
    // intial hash tables
    full_token_dic       = new_hash_table(NULL, NULL);
    macro_cond_token_dic = new_hash_table(NULL, NULL);
    glb_mdefine_dic      = new_hash_table(free_macro_define, macro_define_serialize);
    glb_father_insts_dic = new_hash_table(free_hash_table, hash_table_serialize);
    glb_child_module_dic = new_hash_table(free_hash_table, hash_table_serialize);
    glb_module_path_dic  = new_hash_table(free, str_serialize);
    glb_file_info_dic    = new_hash_table(free_file_info, file_info_serialize);
    glb_not_in_module_include_file_dic = new_hash_table(NULL, NULL);
    
    // genertate log file
    glb_log_out = fopen(log_path, "w");
    if (!glb_log_out) {
        printf("FATAL: cannot open parser log file '%s' !\n", log_path);
        exit(FATAL);
    }
    fprintf(glb_log_out, "Start Parser FileList: %s\n",fl_path);

    if( gen_verilog_token_tree() != SUCCESS){
        printf("FATAL: cannot generate verilog reserved word tree !\n");
        exit(FATAL); // fatal error
    }

    // initial file list inf
    glb_file_list_inf = parser_file_list(fl_path);
    if (!glb_file_list_inf) {
        printf("FATAL: parser filelist failed ! %s\n",fl_path);
        exit(FATAL); // fatal error
    }
    // set only file inf or not
    glb_parser_file_standalone = glb_file_list_inf->parser_file_standalone;
    // initial mdefine
    if (glb_file_list_inf->define_list) {
        VoidPtrLinkNode* c_node = glb_file_list_inf->define_list->head;
        MacroDefine*     c_md   = NULL;
        while (c_node) {
            c_md   = copy_macro_define(c_node->value);
            hash_add_pair(glb_mdefine_dic, c_md->name_sr->str, c_md);
            c_node = c_node->next;
        }
    }
    // initial incdir
    glb_incdir_list        = glb_file_list_inf->incdir_list;
    // initial file context stack for include context switch
    glb_file_context_stack = new_vpll(free_file_context, NULL); // verilog max `include nested level 24
    // initial macro condition stack use trace macro condition
    glb_mcnd_top           = -1;
    // gen python out dir
    char* parser_out_path  = str_cat_free(rstrip(glb_file_list_inf->parser_out_dir, '/', 0), 1, "/", 0);
    
    FileListFileInf* c_flf_inf = NULL;
    int  i        = 0;
    char bar[100] = {0};
    char *lab     = "-\\|/";
    int  file_num = glb_file_list_inf->file_inf_list->length;
    int  step     = (int)( (file_num + 58) / 59 );
    int  repeat   = (int)( (59 + file_num -1) / file_num );
    int  step_i   = 0;
    int  repeat_i = 0;
    while ((c_flf_inf = vpll_pop_front(glb_file_list_inf->file_inf_list))){
        // print progress bar
        if (!glb_parser_file_standalone) {
            if ( ((i++)%step) == 0) {
                printf("[%-59s][%d/%d][%c]\r", bar, i, file_num, lab[step_i%4]);
                fflush(stdout);
                for (repeat_i = 0; (repeat_i < repeat) && (step_i < 59); repeat_i++) {
                    bar[step_i++] = '#';
                }
                bar[step_i]   = '\0';
            }
            if (i == file_num){
                int j = 0;
                for (j = step_i; j < 59; j++) {
                    bar[j] = '#';
                }
                bar[j]   = '\0';
                printf("[%-59s][%d/%d][%c]\r", bar, i, file_num, lab[step_i%4]);
                fflush(stdout);
            }
        }
        // get current file contex
        glb_file_context = new_file_context(c_flf_inf->file_path, 1);
        if (!glb_file_context){
            fprintf(glb_log_out, "ERROR: read file failed: %s\n", c_flf_inf->file_path);
            continue;
        }
        active_file_context(glb_file_context, 1);
        // parser file and get file inf
        if(parser_one_file() != SUCCESS){
            fprintf(glb_log_out, "ERROR: parser file failed: %s\n", c_flf_inf->file_path);
            free_file_context(glb_file_context); glb_file_context = NULL;
            clear_vpll(glb_file_context_stack);
            glb_mcnd_top = -1;
            continue;
        }
        // parser success, free file contex and push file inf
        if ( glb_file_context_stack->length != 0 ){
            fprintf(glb_log_out, "RTL ERROR: glb_file_context_stack not empty: %d\n", glb_file_context_stack->length);
            clear_vpll(glb_file_context_stack);
        }
        if (glb_mcnd_top != -1){
            fprintf(glb_log_out, "RTL ERROR: glb_mcnd_top not empty: %d\n", glb_mcnd_top);
            glb_mcnd_top = -1;
        }
        // serialize file inf
        char*  py_p = str_cat(parser_out_path, c_flf_inf->out_name);
        FILE * py_f = fopen(py_p, "w");
        assert(py_f != NULL);
        free(py_p); py_p = NULL;
        fprintf(py_f, "data = ");
        file_inf_serialize(0, py_f, glb_file_inf);
        fclose(py_f);
        // gather module inf
        if (!glb_parser_file_standalone) {
            // generate father inst dic
            gather_mix_merge_inf();
            // update file info
            HashNode* c_node = hash_search(glb_file_info_dic, glb_file_inf->file_state->file_path);
            if (!c_node) {
                FileInfo* fi = new_file_info();
                hash_add_pair(glb_file_info_dic, glb_file_inf->file_state->file_path, fi);
            }
            c_node = hash_search(glb_file_info_dic, glb_file_inf->file_state->file_path);
            assert(c_node);
            FileInfo* fi            = c_node->value;
            fi->serialize_file_name = str_copy(c_flf_inf->out_name, 0, -1);
        }
        // free current file context and push file_inf
        free_file_context(glb_file_context); glb_file_context = NULL;
    }
    if (!glb_parser_file_standalone){
        // finish progress bar
        printf("\n");
        // serialize glb_file_info_dic
        char*  py_p = str_cat(parser_out_path, "parser_file_info_dic.py");
        FILE * py_f = fopen(py_p, "w");
        assert(py_f != NULL);
        free(py_p); py_p = NULL;
        fprintf(py_f, "data = ");
        hash_table_serialize(0, py_f, glb_file_info_dic);
        // serialize glb_mdefine_dic
        py_p = str_cat(parser_out_path, "parser_macro_define_dic.py");
        py_f = fopen(py_p, "w");
        assert(py_f != NULL);
        free(py_p); py_p = NULL;
        fprintf(py_f, "data = ");
        hash_table_serialize(0, py_f, glb_mdefine_dic);
        // serialize glb_father_insts_dic
        py_p = str_cat(parser_out_path, "parser_father_insts_dic.py");
        py_f = fopen(py_p, "w");
        assert(py_f != NULL);
        free(py_p); py_p = NULL;
        fprintf(py_f, "data = ");
        hash_table_serialize(0, py_f, glb_father_insts_dic);
        // serialize glb_child_module_dic
        py_p = str_cat(parser_out_path, "parser_child_module_dic.py");
        py_f = fopen(py_p, "w");
        assert(py_f != NULL);
        free(py_p); py_p = NULL;
        fprintf(py_f, "data = ");
        hash_table_serialize(0, py_f, glb_child_module_dic);
        // serialize glb_module_path_dic
        py_p = str_cat(parser_out_path, "parser_module_path_dic.py");
        py_f = fopen(py_p, "w");
        assert(py_f != NULL);
        free(py_p); py_p = NULL;
        fprintf(py_f, "data = ");
        hash_table_serialize(0, py_f, glb_module_path_dic);
    }
    free_hash_table(glb_file_info_dic); glb_file_info_dic = NULL;
    free_hash_table(glb_mdefine_dic); glb_mdefine_dic = NULL;
    free_hash_table(glb_father_insts_dic); glb_father_insts_dic = NULL;
    free_hash_table(glb_child_module_dic); glb_child_module_dic = NULL;
    free_hash_table(glb_module_path_dic); glb_module_path_dic = NULL;
    free(parser_out_path);
    free_file_list_inf(glb_file_list_inf); glb_file_list_inf = NULL;
    fclose(glb_log_out);
    return SUCCESS;
}

// FileInf* api_parser_from_file_path(ParserFileInfo* pf_info){
//     // intial hash tables
//     full_token_dic       = new_hash_table(NULL, NULL);
//     macro_cond_token_dic = new_hash_table(NULL, NULL);
//     glb_mdefine_dic      = NULL; // vtags get it from fileinf
//     glb_father_insts_dic = NULL; // vtags get it from fileinf
//     glb_module_path_dic  = NULL; // vtags get it from fileinf
//     glb_file_list_inf    = NULL; // no need for single file
//     glb_mdefine_dic      = new_hash_table(free_macro_define, macro_define_serialize);
//     glb_file_info_dic    = new_hash_table(free_file_info, file_info_serialize); // vtags get it from fileinf
//     glb_incdir_list      = new_vpll(free, str_serialize);                       // get from input pf info
// 
//     // genertate log file
//     glb_log_out = fopen(pf_info->log_path, "a");
//     if (!glb_log_out) {
//         printf("FATAL: cannot open parser log file '%s' !\n", pf_info->log_path);
//         exit(FATAL);
//     }
//     fprintf(glb_log_out, "Start Parser File: %s\n", pf_info->file_path);
//     
//     if( gen_verilog_token_tree() != SUCCESS){
//         printf("FATAL: cannot generate verilog reserved word tree !\n");
//         return NULL; // fatal error
//     }
//     
//     // initial file context stack for include context switch
//     glb_file_context_stack = new_vpll(free_file_context, NULL); // verilog max `include nested level 24
//     // initial macro condition stack use trace macro condition
//     glb_mcond_stack   = new_vpll(free, NULL);
//     // add define inf
//     int i = 0;
//     for (i = 0; i < pf_info->num_define_list; i++) {
//         DefinePair*  c_pair  = pf_info->define_list[i];
//         MacroDefine* c_def   = new_macro_define();
//         c_def->file_state    = NULL;
//         c_def->name_sr       = new_str_range();
//         c_def->name_sr->str  = strip_space(c_pair->name, 0);
//         c_def->value         = strip_space(c_pair->value, 0);
//         hash_add_pair(glb_mdefine_dic, c_pair->name, c_def);
//     }
//     // add incdir
//     for (i = 0; i < pf_info->num_incdir_list; i++) {
//         vpll_push(glb_incdir_list, strip_space(pf_info->incdir_list[i], 0));
//     }
//     // new file context
//     FileContext* c_file_context = new_file_context(pf_info->file_path, 1);
//     if (!c_file_context){
//         fprintf(glb_log_out, "ERROR: read file failed: %s\n", pf_info->file_path);
//         return NULL;
//     }
//     active_file_context(c_file_context, 1);
//     // parser file and get file_inf
//     assert( parser_one_file() == SUCCESS );
//     // parser success, free file contex and push file inf
//     assert( glb_file_context_stack->length == 0 );
//     // parser success glb_file_context_stack should be zero
//     assert( glb_file_context_stack->length == 0 );
//     // serialize file inf
//     FILE * py_f = fopen(pf_info->out_path, "w");
//     assert(py_f != NULL);
//     fprintf(py_f, "file_inf = ");
//     file_inf_serialize(0, py_f, glb_file_inf);
//     fclose(py_f);
//     // free current file context and push file_inf
//     free_file_context_no_file_inf(glb_file_context); glb_file_context = NULL;
//     free_hash_table(glb_file_info_dic);
//     free_hash_table(full_token_dic);
//     free_hash_table(macro_cond_token_dic);
//     free_vpll(glb_incdir_list);
//     
//     fclose(glb_log_out);
//     return glb_file_inf;
// }

HashNode* new_hash_node(){
    HashNode* hn = malloc(sizeof(HashNode));
    if (!hn) {
        exit(FATAL);
    }
    hn->key   = NULL;
    hn->value = NULL;
    return hn;
}

void free_hash_node(VoidFuncPtr free_value_func, void* vhn){
    if (!vhn) {
        return;
    }
    HashNode* hn = vhn;
    free(hn->key); hn->key = NULL;
    free_value_func(hn->value); hn->value = NULL;
    free(hn);
}

FileListFileInf* new_file_list_file_inf(void){
    FileListFileInf* fs = malloc(sizeof(FileListFileInf));
    if (!fs) {
        exit(FATAL);
    }
    fs->file_path = NULL;
    fs->out_name  = NULL;
    return fs;
}

void free_file_list_file_inf( void* vfs ){
    if (!vfs) {
        return;
    }
    FileListFileInf* fs = vfs;
    free(fs->file_path); fs->file_path = NULL;
    free(fs->out_name);  fs->out_name = NULL;
    free(fs);
}

HashTable* new_hash_table(void* free_value_func, void* serialize_value_func){
    HashTable* ht = malloc(sizeof(HashTable));
    if (!ht) {
        exit(FATAL);
    }
    ht->free_value_func      = free_value_func;
    ht->serialize_value_func = serialize_value_func;
    ht->table_node = NULL;
    ht->table_node_ptr = &(ht->table_node);
    return ht;
}

void free_hash_table(void* vht){
    if (!vht) {
        return;
    }
    HashTable* ht     = vht;
    HashNode*  iter   = NULL;
    HashNode*  c_node = NULL;
    HASH_ITER(hh, ht->table_node, c_node, iter) {
        HASH_DEL(ht->table_node, c_node);
        if (ht->free_value_func) {
            ((VoidFuncPtr)(ht->free_value_func))(c_node->value);
        }
        free(c_node->key); c_node->key = NULL;
        free(c_node); c_node = NULL;
    }
}

RetureState hash_add_pair(HashTable* ht, char* key, void* value){
    // find if exists
    if (!ht) {
        return FAILED;
    }
    HashNode* old_hn = NULL;
    HASH_FIND_STR( ht->table_node, key, old_hn);
    if (old_hn){
        HASH_DEL(ht->table_node, old_hn);
        free_hash_node(ht->free_value_func, old_hn);
    }
    HashNode* new_hn          = NULL;
    new_hn                    = new_hash_node();
    new_hn->key               = str_copy(key, 0, -1);
    new_hn->value             = value;
    HASH_ADD_KEYPTR( hh, ht->table_node, new_hn->key, strlen(new_hn->key), new_hn );
    return SUCCESS;
}

void hash_remove_key(HashTable* ht, char* key){
    // find if exists
    HashNode* hn = NULL;
    HASH_FIND_STR( ht->table_node, key, hn);
    if (!hn){
        return;
    }
    HASH_DEL(ht->table_node, hn);
    free_hash_node(ht->free_value_func, hn);
}

HashNode* hash_search(HashTable* ht, char* key){
    if (!ht) {
        return NULL;
    }
    HashNode* hn = NULL;
    HASH_FIND_STR( ht->table_node, key, hn);
    if (!hn){
        return NULL;
    }
    return hn;
}

void hash_table_serialize(int head_space_num, FILE* fp, void* vht){
    char* head_space = gen_space(head_space_num);
    if (!vht) {
        fprintf(fp, "%s{}\n", head_space);
        free(head_space);
        return;
    }
    HashTable* ht = vht;
    fprintf(fp, "%s{\n", head_space);
    
    HashNode* c_node     = NULL;
    HashNode* iter       = NULL;
    int       first_pair = 1;
    HASH_ITER(hh, ht->table_node, c_node, iter) {
        fprintf(fp, "%s", head_space);
        if (first_pair) {
            fprintf(fp, " ");
            first_pair = 0;
        }else{
            fprintf(fp, ",");
        }
        fprintf(fp, "'%s' : \n", c_node->key );
        ht->serialize_value_func(head_space_num+PRINT_INDENTATION, fp, c_node->value);
    }
    
    fprintf(fp, "%s}\n", head_space);
    free(head_space); head_space = NULL;
}

void vpll_serialize(int head_space_num, FILE* fp, void* v_vpll){
    char* head_space       = gen_space(head_space_num);
    VoidPtrLinkList * vpll = v_vpll;
    if (!vpll || vpll->length == 0) {
        fprintf(fp, "%s[]\n", head_space);
        free(head_space);
        return;
    }
    
    fprintf(fp, "%s[\n", head_space);
    
    VoidPtrLinkNode* c_node     = NULL;
    int i = 0;
    
    for (i = 0; i < vpll->length; i++) {
        if (i == 0) {
            c_node = vpll->head;
        } else {
            c_node = c_node->next;
            char* indentation = gen_space(PRINT_INDENTATION);
            fprintf(fp, "%s%s,\n", head_space, indentation);
            free(indentation);
        }
        vpll->serialize_value_func(head_space_num+PRINT_INDENTATION, fp, c_node->value);
    }
    
    fprintf(fp, "%s]\n", head_space);
    free(head_space); head_space = NULL;
}

void father_inst_serialize(int head_space_num, FILE* fp, void* vfi){
    char* head_space = gen_space(head_space_num);
    if (!vfi) {
        fprintf(fp, "%s{}\n", head_space);
        free(head_space);
        return;
    }
    FatherInstInf * fi    = vfi;
    fprintf(fp, "%s{\n", head_space);
    fprintf(fp, "%s 'father_module_name' : '%s'\n", head_space, fi->father_module_name);
    fprintf(fp, "%s,'inst_name'          : '%s'\n", head_space, fi->inst_name);
    fprintf(fp, "%s}\n", head_space);
    free(head_space);
}

char* char_replace(char* str, char c, char* r, int free_old){
    char* new_str = NULL;
    
    if (!str) {
        return NULL;
    }
    long str_l = strlen(str);
    long rep_l = strlen(r);
    long match_num = 0;
    int i = 0;
    for (i = 0; i < str_l; i++) {
        if (str[i] == c) {
            match_num++;
        }
    }
    if (match_num == 0) {
        if (free_old) {
            return str;
        }
        return str_copy(str, 0, -1);
    }
    long new_str_l = str_l - match_num + match_num * rep_l;
    new_str = malloc(sizeof(char) * (new_str_l + 1));
    if (!new_str) {
        exit(FATAL);
    }
    int j = 0;
    int k = 0;
    for (i = 0; i < str_l; i++) {
        if (str[i] == c) {
            for (j = 0; j < rep_l; j++) {
                new_str[k++] = r[j];
            }
            continue;
        }
        new_str[k++] = str[i];
    }
    assert(k == new_str_l);
    new_str[k] = '\0';
    if (free_old) {
        free(str);
    }
    return new_str;
}

FileInfo* new_file_info(){
    FileInfo* fi = malloc(sizeof(FileInfo));
    if (!fi) {
        exit(FATAL);
    }
    fi->last_modify_time    = 0;
    fi->serialize_file_name = NULL;
    return fi;
}

void free_file_info(void* vfi){
    if (!vfi) {
        return;
    }
    FileInfo* fi = vfi;
    free(fi->serialize_file_name); fi->serialize_file_name = NULL;
    free(fi);
}

void file_info_serialize(int head_space_num, FILE* fp, void* vfi){
    char* head_space = gen_space(head_space_num);
    if (!vfi) {
        fprintf(fp, "%s{}\n", head_space);
        free(head_space);
        return;
    }
    
    FileInfo* fi = vfi;
    
    
    fprintf(fp, "%s{\n", head_space);
    
    fprintf(fp,     "%s 'last_modify_time'    : %ld\n", head_space, fi->last_modify_time);
    if (!fi->serialize_file_name) {
        fprintf(fp, "%s,'serialize_file_name' : ''\n", head_space);
    } else {
        fprintf(fp, "%s,'serialize_file_name' : '%s'\n", head_space, fi->serialize_file_name);
    }
    
    fprintf(fp, "%s}\n", head_space);
    free(head_space);
}

//typedef struct code_block_info{
//    long  start_line;
//    long  file_offset;
//    char* file_path;
//} CodeBlockInfo;

CodeBlockInfo* new_code_block_info(void){
    CodeBlockInfo* info = malloc( sizeof(CodeBlockInfo) );
    if (!info) {
        exit(FATAL);
    }
    info->file_path              = NULL;
    info->logic_line_range[0]    =  0;
    info->logic_line_range[1]    = -1;
    info->real_line_range[0]     =  0;
    info->real_line_range[1]     = -1;
    info->real_code_line_boundry = NULL;
    return info;
}

void free_code_block_info( void* vinfo){
    if (!vinfo) {
        return;
    }
    CodeBlockInfo* info = vinfo;
    free(info->file_path); info->file_path = NULL;
    free_vpll( info->real_code_line_boundry ); info->real_code_line_boundry      = NULL;
    free(info);
}

void code_block_info_serialize(int head_space_num, FILE* fp, void* vinfo){
    char* head_space = gen_space(head_space_num);
    if (!vinfo) {
        fprintf(fp, "%s{}\n", head_space);
        free(head_space);
        return;
    }
    CodeBlockInfo* info = vinfo;
    fprintf(fp, "%s{\n", head_space);
    fprintf(fp,     "%s 'logic_line_range'       : [%d, %d]\n" , head_space, info->logic_line_range[0], info->logic_line_range[1]);
    fprintf(fp,     "%s,'real_line_range'        : [%d, %d]\n" , head_space, info->real_line_range[0], info->real_line_range[1]);
    if (!info->file_path) {
        fprintf(fp, "%s,'file_path'              : ''\n"  , head_space);
    } else {
        fprintf(fp, "%s,'file_path'              : '%s'\n", head_space, info->file_path);
    }
    fprintf(fp,     "%s,'real_code_line_boundry' :\n", head_space);
    vpll_serialize(head_space_num+PRINT_INDENTATION, fp, info->real_code_line_boundry);
    
    fprintf(fp, "%s}\n", head_space);
    free(head_space);
}

CodeLineBoundry* new_code_line_boundry(void){
    CodeLineBoundry* boundry = malloc( sizeof(CodeLineBoundry) );
    if (!boundry) {
        exit(FATAL);
    }
    // print to python 
    boundry->start        =  -1; // current valid code line start
    boundry->offset       =  -1; // number of real line current valid code line cross, must > 1(1 is skip to save space) 
    boundry->repeat_times =   0; // continue repeat same line offset valid code lines
    // not print 
    boundry->last_end     =  -1; // last repeat line end, to help test repeat times 
    boundry->repeat_break =   0; // repeat break if new valid line offset not equal current offset
    return boundry;
}

void free_code_line_boundry( void* vboundry){
    if (!vboundry) {
        return;
    }
    CodeLineBoundry* boundry = vboundry;
    free(boundry);
}

void code_line_boundry_serialize(int head_space_num, FILE* fp, void* vb){

    char* head_space = gen_space(head_space_num);
    if (!vb) {
        fprintf(fp, "%s[]\n", head_space);
        free(head_space);
        return;
    }
    CodeLineBoundry* b = vb;
    fprintf(fp, "%s[%ld, %ld, %ld]\n", head_space, b->start, b->offset, b->repeat_times);
    free(head_space);
}

// if empty list first line start default is form 0
void add_new_line_boundry(VoidPtrLinkList* b_list, long line_end){
    assert(b_list != NULL);
    long new_line_offset = line_end + 1; // if first line, offset need +1
    long now_line_start  = 0;            // if first line
    // try get last boundry
    CodeLineBoundry* last_b = vpll_peek(b_list);  // must not be NULL
    if( last_b != NULL) {
        if (line_end <= last_b->last_end){ // new line already passed
            return;
        }
        new_line_offset = line_end - last_b->last_end;  // not +1 because last_b->last_end is pre line end
        // check if signal line code, just skip and update last_end and repeat break
        if(new_line_offset == 1){
            last_b->repeat_break = 1;
            last_b->last_end     = line_end;
            return;
        }
        // no bleck check if repeat
        if(    ( last_b->repeat_break == 0 )
            && ( new_line_offset == last_b->offset )
       ){
            assert(new_line_offset > 1);
            last_b->repeat_times++;
            last_b->last_end = line_end;
            return;
        }
        // offset not eq, or repeat break and not offset == 1, need new boundry
        // bleck old boundry
        last_b->repeat_break = 1;
        now_line_start = last_b->last_end + 1;
    }
    // add new boundry
    CodeLineBoundry* cur_line_boundry     = new_code_line_boundry();  
    cur_line_boundry->start               = now_line_start;
    cur_line_boundry->offset              = new_line_offset; 
    cur_line_boundry->repeat_times        = 1;
    cur_line_boundry->last_end            = line_end;
    vpll_push(b_list, cur_line_boundry);
    return;
}

int is_word_char(char c){
    return ( (c>='a' && c<='z') ||
             (c>='A' && c<='Z') ||
             (c>='0' && c<='9') ||
             (c=='_'));
}

int is_empty_char(char c){
    return (c=='\t' || c=='\n' || c==' ' || c=='\r' || c == 0);
}

int match_whole_word(long buf_size, char* code_buf, long cmp_size, char* cmp_word, long start){
    assert(start >= 0 && start < buf_size && cmp_size > 0);
    // check i-1 char is not word char
    if (start > 0 && is_word_char(code_buf[start-1])){
        return 0;
    }
    // if cmp_size bigger than left char return 0
    if( cmp_size > buf_size - start ){
        return 0;
    }
    // comp str
    long i = 0;
    for (i = 0; i < cmp_size; i++) {
        if (code_buf[start+i] != cmp_word[i]) {
            return 0;
        }
    }
    // check next char not word
    if ( (start+i) < buf_size && is_word_char(code_buf[i])) {
        return 0;
    }
    // is whole word
    return 1;
}

long skip_to_next_level_one_bracket(long buf_size, char* code_buf, long start, long* cur_line_num_p){
    int match_left_bracket = 0;
    int brack_level        = 0;
    long i                 = 0;
    char c;
    for (i = start; i < buf_size; i++) {
        c = code_buf[i];
        if (c == '\n') {
            (*cur_line_num_p)++;
        }
        if (c == '(') {
            brack_level++;
            match_left_bracket = 1;
        }
        if (c == ')') {
            brack_level--;
        }
        if (match_left_bracket && brack_level) {
            break;
        }
    }
    return i;
}

VoidPtrLinkList* get_verilog_line_boundry(long buf_size, char* code_buf){
    VoidPtrLinkList*  code_boundry_list = new_vpll(free_code_line_boundry, code_line_boundry_serialize);
    int               in_string        = 0;
    long              cur_line_num     = 0;
    char              c                   ;
    long              i                = 0;
    int               end_at_next_line = 0; // for macro define
    int               pre_real_line_is_empty= 1;
    int               pre_code_line_is_empty= 1;
    while (i < buf_size) {
        c = code_buf[i];
        // go to next line
        if (c == '\n') {
            if (pre_code_line_is_empty) { // skip pre code empty line
                add_new_line_boundry(code_boundry_list, cur_line_num);
                pre_code_line_is_empty = 1;
                pre_real_line_is_empty = 1;
            } else {
                if (i == 0 || code_buf[i-1] != '\\') { // no '\' at line end is real line end
                    pre_real_line_is_empty = 1;
                    if (end_at_next_line == 1) {
                        end_at_next_line = 0;
                        add_new_line_boundry(code_boundry_list, cur_line_num);
                        pre_code_line_is_empty = 1;
                    }
                }
            }
            cur_line_num++;
            i++;
            continue;
        }
        // if end next line skip other check
        if (end_at_next_line) {
            i++;
            continue;
        }
        // match ""
        if (c == '"'){
            pre_real_line_is_empty = 0;
            pre_code_line_is_empty = 0;
            // current not in string just pass to next "
            if (in_string == 0) {
                in_string = 1;
                i++;
                continue;
            }
            // current in sting check current " is string end or not, check whether has \ before "
            if (code_buf[i-1] == '\\'){
                i++;
                continue;
            }
            // real string end "
            in_string = 0;
            i++;
            continue;
        }
        // match for
        if (   match_whole_word(buf_size, code_buf, 3, "for"  , i)
            || match_whole_word(buf_size, code_buf, 2, "if"   , i)
            || match_whole_word(buf_size, code_buf, 4, "case" , i)
            || match_whole_word(buf_size, code_buf, 5, "casex", i)
            || match_whole_word(buf_size, code_buf, 5, "casez", i)){
            if (cur_line_num > 0) {
                add_new_line_boundry(code_boundry_list, cur_line_num-1);
            }
            i = skip_to_next_level_one_bracket(buf_size, code_buf, i, &cur_line_num);
            add_new_line_boundry(code_boundry_list, cur_line_num);
            pre_real_line_is_empty = 0;
            pre_code_line_is_empty = 0;
            continue;
        }
        // match 'wire'
        if (match_whole_word(buf_size, code_buf, 4, "wire", i)){
            i = i+4;
            if(cur_line_num > 0){
                add_new_line_boundry(code_boundry_list, cur_line_num-1);
            }
            pre_real_line_is_empty = 0;
            pre_code_line_is_empty = 0;
            continue;
        }
        // match 'reg'
        if (match_whole_word(buf_size, code_buf, 3, "reg", i)){
            i = i+3;
            if(cur_line_num > 0){
                add_new_line_boundry(code_boundry_list, cur_line_num-1);
            }
            pre_real_line_is_empty = 0;
            pre_code_line_is_empty = 0;
            continue;
        }
        // match '`def'
        if (pre_real_line_is_empty && c == '`') {
            end_at_next_line       = 1;
            pre_real_line_is_empty = 0;
            pre_code_line_is_empty = 0;
            if (cur_line_num > 0) {
                add_new_line_boundry(code_boundry_list, cur_line_num-1);
            }
            i++;
            continue;
        }
        // match .xxx(
        if (pre_real_line_is_empty && c == '.') {
            pre_real_line_is_empty = 0;
            pre_code_line_is_empty = 0;
            if (cur_line_num > 0) {
                add_new_line_boundry(code_boundry_list, cur_line_num-1);
            }
            i++;
            continue;
        }
        // match ";"
        if (c == ';') {
            pre_real_line_is_empty = 0;
            pre_code_line_is_empty = 0;
            add_new_line_boundry(code_boundry_list, cur_line_num);
            pre_code_line_is_empty = 1;
            i++;
            continue;
        }
        // check empty
        if ( !is_empty_char(c) ) {
            pre_real_line_is_empty = 0;
            pre_code_line_is_empty = 0;
        }
        i++;
        continue;
    }
    return code_boundry_list;
}

CodeLineBoundry* copy_code_line_boundry(CodeLineBoundry* b){
    CodeLineBoundry* new_b = new_code_line_boundry();
    new_b->last_end     = b->last_end;
    new_b->offset       = b->offset;
    new_b->repeat_break = b->repeat_break;
    new_b->repeat_times = b->repeat_times;
    new_b->start        = b->start;
    return new_b;
}

VoidPtrLinkList* code_boundry_slice(VoidPtrLinkList* blist, long start, long end){
    VoidPtrLinkList* b_slice = new_vpll(free_code_line_boundry, code_line_boundry_serialize);
    int i = 0;
    VoidPtrLinkNode* c_node = NULL;
    for (i = 0; i < blist->length; i++) {
        if (i == 0) {
            c_node = blist->head;
        } else {
            c_node = c_node->next;
        }
        if (c_node == NULL) {
            break;
        }
        CodeLineBoundry* cur_b = c_node->value;
        // find first code line
        // -------------------------------------------->
        //          ^--------------^                 // cur_b->start -> cur_b->last_end
        //  ^-----^         or       ^---------^     //        start -> end
        if (start > cur_b->last_end || end < cur_b->start ) {
            continue;
        }
        // valid block
        CodeLineBoundry* sli_b = copy_code_line_boundry(cur_b);
        vpll_push(b_slice, sli_b);
    }
    return b_slice;
}
