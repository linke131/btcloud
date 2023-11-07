import os
import sys

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel/plugin/total")
sys.path.insert(0, "/www/server/panel/class")

import public

def test_write_public_conf(write_item, write_vals):
    file_path = "/www/server/panel/vhost/nginx/public.conf"
    change = False
    if os.path.exists(file_path):
        public_data = public.readFile(file_path)
        _lines = public_data.split("\n")
        found = False
        for i in range(0, len(_lines)):
            line = _lines[i]
            if line.startswith(write_item):
                found = True
                # print(line)
                if write_item == "lua_package_path":
                    k, val_str = line.split(" ")
                    if val_str.endswith(";"):
                        val_str = val_str[0:-1]
                    val_str = val_str.replace("\"", '')
                    # print(val_str)
                    values = [x for x in val_str.split(";") if x]
                    # print(values)
                    _change = False
                    for write_val in write_vals:
                        if write_val not in values:
                            values.insert(0, write_val)
                            _change = True
                    if _change:
                        line = write_item +" \""+";".join(values)+";;\";"
                        # print("line: {}".format(line))
                        change = True
                        _lines[i] = line
        if not found:
            new_line = ""
            if write_item == "lua_package_path":
                new_line = write_item + " \""+";".join(write_vals) + ";;\";"
            if new_line:
                _lines.append(new_line)
                change = True

        if change:
            public_data = "\n".join(_lines).strip()
            print(public_data)
            public.writeFile(file_path, public_data)
    else:
        # 新增
        if write_item == "lua_package_path":
            new_line = write_item + " \""+";".join(write_vals) + ";;\";"
            public.writeFile(file_path, new_line)

if __name__ == "__main__":
    write_item = "lua_package_path"
    item1 = "/www/server/btwaf/?.lua"
    item2 = "/www/server/total/?.so"
    write_vals = [item1, item2]

    conf_path = "/www/server/panel/vhost/nginx/public.conf"
    if os.path.exists(conf_path):
        os.remove(conf_path)

    test_write_public_conf(write_item, write_vals)
    assert os.path.exists(conf_path)
    data = public.readFile(conf_path).split("\n")
    for item in write_vals:
        for line in data:
            if line.startswith(write_item):
                assert line.find(item)!=-1

    write_vals.append("/www/server/btwaf/?.so")
    test_write_public_conf(write_item, write_vals)
    data = public.readFile(conf_path).split("\n")
    for item in write_vals:
        for line in data:
            if line.startswith(write_item):
                assert line.find(item)!=-1           
    
