"""
Each node is printed as:

<status>--<flags> <name><opts> <type> <if-features>

  <status> is one of:
    +  for current
    x  for deprecated
    o  for obsolete

  <flags> is one of:
    rw  for configuration data
    ro  for non-configuration data, output parameters to rpcs
        and actions, and notification parameters
    -w  for input parameters to rpcs and actions
    -u  for uses of a grouping
    -x  for rpcs and actions
    -n  for notifications

  <name> is the name of the node
    (<name>) means that the node is a choice node
   :(<name>) means that the node is a case node

   If the node is augmented into the tree from another module, its
   name is printed as <prefix>:<name>.

  <opts> is one of:
    ?  for an optional leaf, choice, anydata or anyxml
    !  for a presence container
    *  for a leaf-list or list
    [<keys>] for a list's keys

    <type> is the name of the type for leafs and leaf-lists, or
           "<anydata>" or "<anyxml>" for anydata and anyxml, respectively

    If the type is a leafref, the type is printed as "-> TARGET", where
    TARGET is the leafref path, with prefixes removed if possible.

  <if-features> is the list of features this node depends on, printed
    within curly brackets and a question mark "{...}?"
"""
#!/usr/bin/env python
import json
import re
import numpy as np
 
 
path_list = []
with open('vrouter.tree') as file:
    while (line := file.readline()):
        pos = line.find('+')
        #print(f"{pos} : {line} ")
        data={}
        data['pos'] = (pos + 1) // 3
        #print(f"line:{line}")
        if pos == -1:
            line = line.strip()
            #print(line.split(':'))
            if line.split(':')[0]  == 'module':
                module_name=line.split(':')[1].strip()
                data['keyword'] = 'module'
                data['name'] = module_name
            elif line.split(':')[0]  == 'rpcs':
                data['keyword'] = 'rpcs'
        else:
            line = ' '.join(line[pos:].split())
            item = line.split(' ')
           # print(str(len(item)) + line[(pos):])
            if len(item) == 2: #container
                #print(f"container {item[0]} name {item[1]}")
                data['keyword'] = 'container'
                data['name'] = item[1]
            elif len(item) == 3:
                if item[1][-1] == '*':
                    data['keyword'] = 'key'
                    data['name'] = item[1][:-1]
                    data['key'] = item[2]
                    #print(f"key {item[1][:-1]}")
                elif item[1][-1] == '?':
                    data['keyword'] = 'leaf'
                    data['name'] = item[1][:-1]
                    data['type'] = item[2]
                    #print(f"leaf {item[1][:-1]}")
                else:
                    data['keyword'] = 'leaf'
                    data['name'] = item[1]
                    data['type'] = item[2]
                    #print(f"leaf {item[1][:-1]}")
            elif  len(item) == 4:
            #+--rw vrouter-interface:policer?          -> /vrouter:config/vrouter-qos:qos/policer/name
            #rw vrouter-qos:shaper* [name] {advanced}?
                if item[3] == '{advanced}?':
                    data['option'] = 'advanced'
                    if item[1][-1] == '?':
                        data['keyword'] = 'leaf'
                        data['name'] = item[1][:-1]
                        data['type'] = item[2]
                    elif item[1][-1] == '*':
                        data['keyword'] = 'key'
                        data['name'] = item[1][:-1]
                        data['key'] = item[2]
                        #print(f"{data['name']} key:{data['key']}")
                elif item[2] == '->':
                    data['keyword'] = 'leaf'
                    data['type'] = 'link'
                    data['link'] = item[3]
                    if item[1][-1] == '?':
                        data['name'] = item[1][:-1]
                    else:
                        data['name'] = item[1][:-1]
                       
                    #print(f"leaf {data['name']}")
                else:    
                    print(f"error: unidentify 4 {line}")
            elif len(item) == 5:                   
            #:+--rw vrouter-fast-path:hardware-queue-map* [port index queue]
            #+--rw vrouter-interface:shaper? -> /vrouter:config/vrouter-qos:qos/shaper/name {advanced}?
                if item[4] == '{advanced}?':
                    data['option'] = 'advanced'
                    if item[2] == '->':
                        data['keyword'] = 'leaf'
                        data['type'] = 'link'
                        data['link'] = item[3]
                        if item[1][-1] == '?':
                            data['name'] = item[1][:-1]
                        else:
                            data['name'] = item[1][:-1]
                else:
                    if item[1][-1] == '*':
                        data['keyword'] = 'key'
                        data['name'] = item[1][:-1]
                        if item[2][0] == '[' and item[4][-1] == ']' :
                            data['key'] = item[2]+'-' + item[3] + '-' +item[4]  
                        else:
                            data['key'] = item[2]   
                        #print(f"key {data['key']}")
                    else:
                        print(f"unexpected 5 {line}")   
            else:
                print(f"other: {len(item)} {line}")
        if 'keyword' in data:
            path_list.append(data)                
for data in path_list:
    print(data)       
 
root = {}
module_name=""
 
path = "/"
 
sec_list = {}
pos_path = {}
name=""
pos = 0
path_array = np.empty([15], dtype='U64')
 
for data in path_list:
    #print(data)
   
    if data['pos'] < pos: #rearrange path
        path = ""
        for i in range(1, data['pos'] - 1):
            path = path + str(path_array[i]) + '/';
       
    pos = data['pos']   
    
    if data['keyword'] == 'module' :
        module_name = data['name']
 
    elif data['keyword'] == 'container':
        if len(data['name'].split(':')) > 1:
            name = data['name']
        else:
            name = module_name + ':' + data['name']
        #print(f"path_array: {path_array}")   
        path_array[pos] = name
        path= path + name + '/'
        sec_list['/'+path+name] = {'name': {'type':'container' }}
        print(f"/{path}")
    elif data['keyword'] == 'leaf':
        if len(data['name'].split(':')) > 1:
            name = data['name']
        else:
            name = module_name + ':' + data['name']
        sec_list['/'+path+name] = {data['name']: {'type':data['type'] }}
        print(f"/{path}{name} , type: {data['type']}")
        
    elif data['keyword'] == 'key':
        if len(data['name'].split(':')) > 1:
            name = data['name']
        else:
            name = module_name + ':' + data['name']
        path_array[pos] = name + '/'+ data['key']              
        path= path + name +'/'+ data['key'] +'/'
    elif data['keyword'] == 'rpcs': 
        print(f"rpcs: {module_name}")
    else:
        print(f"2nd: unexpected keyword:{data['keyword']} ")     

for path in sec_list:
    print(f"{path}  : {sec_list[path]}")       