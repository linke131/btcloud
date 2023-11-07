#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwl
# +-------------------------------------------------------------------
import sys, os
os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel")
sys.path.insert(0, "/www/server/panel/class/")

class LuaMaker:
    """
    lua 处理器
    """
    @staticmethod
    def makeLuaTable(table):
        """
        table 转换为 lua table 字符串
        """
        _tableMask = {}
        _keyMask = {}
        def analysisTable(_table, _indent, _parent):
            cell = []
            if isinstance(_table, tuple):
                _table = list(_table)
            if isinstance(_table, list):
                if _table and type(_table[0]) != dict:
                    _table = dict(zip(_table, range(1, len(_table) + 1)))
                else:
                    _table = dict(zip(range(1, len(_table) + 1), _table))

            if isinstance(_table, dict):
                _tableMask[id(_table)] = _parent
                thisIndent = _indent + "    "
                for k in _table:
                    if sys.version_info[0] == 2:
                        if type(k) not in [int,float,bool,list,dict,tuple]: 
                            k = k.encode()

                    if not (isinstance(k, str) or isinstance(k, int) or isinstance(k, float)):
                        return
                    key = isinstance(k, int) and "[" + str(k) + "]" or "[\"" + str(k) + "\"]"
                    if _parent + key in _keyMask.keys():
                        print("{} --not in key mask.".format(_parent+key))
                        return
                    _keyMask[_parent + key] = True
                    var = None
                    v = _table[k]
                    if sys.version_info[0] == 2:
                        if type(v) not in [int,float,bool,list,dict,tuple]: 
                            v = v.encode()
                    if isinstance(v, str):
                        var = "\"" + v + "\""
                    elif isinstance(v, bool):
                        var = v and "true" or "false"
                    elif isinstance(v, int) or isinstance(v, float):
                        var = str(v)
                    else:
                        var = analysisTable(v, thisIndent, _parent + key)
                    cell.append(thisIndent + key + " = " + str(var))
                lineJoin = ",\n"
            else:
                return ''
            return "{\n" + lineJoin.join(cell) + "\n" + _indent +"}"
        return analysisTable(table, "", "root") 