# (c) Matti Katila, 2011
# Creates the python bindings for libvov-c
# License GNU GPL

import os
import sys
sys.path = ["./py/"] + sys.path
import CppHeaderParser
#CppHeaderParser.debug = True

just_structs = []
structs_and_types = []
init_type_ready = []
init_add_objects = []


def write(f, list_of_data):
    f = file(f, 'w+')
    f.write('''// GENERATED FILE - DO NOT EDIT! \n''')
    for i in list_of_data:
        f.write(i)
    f.close()

# lob_foo -> PyLobFoo
def pyobj(fname):
    parts = fname.split('_')
    return 'Py' + "".join([ part[0].upper()+part[1:] for part in parts[:]])

def to_c(param):
    ret = {}
    if param['type'] == 'float':
        ret['pre'] = 'PyFloat_AsDouble('
        ret['post'] = ')'
    elif param['type'].startswith('Lob') or param['type'].startswith('Vob'):
        ret['pre'] = '((PyLob*)'
        ret['post'] = ')->obj'
    else:
        print param
        raise RuntimeError('asdf'+param)
    return ret


def add_attributes(clzz):

    print 'Add attrs', clzz['name'], clzz['typedef']
    if not 'typedef' in clzz: return
    #if not 'access' in clzz['inherits'][0]: return
    attrs = ""
    obj_name = 'Py' + clzz['typedef']
    type_name = obj_name + 'Type'
    for att in clzz['properties']['public']:
        if att['type'] in ['Region *', 'Lob *', 'Lob', 'LobDelegate', 'UtilArray *', 'Size', 'Size *', 'Coordsys *','OrthoCS *','LobEv','LobModel', 'LobClickModel *', 'LobAnimModel','LobAnimModel *','LobKeyAnimModel *', 'LobSameModel *', 'LobFont *', 'VobColor *', 'Vob', 'VobFill','VobFill *']: continue

        structs_and_types.append("""
PyObject *%s_%s(PyObject *obj, void *data)
{
    %s *self = (%s *)obj;
""" % (obj_name, att['name'], obj_name, obj_name))
        if att['type'] in ['const char *', 'char *']:
            structs_and_types.append("""
    return PyString_FromString(self->obj->%s);
""" % (att['name']))
        elif att['type'] == 'float':
            structs_and_types.append("""
    return PyFloat_FromDouble(self->obj->%s);
""" % (att['name']))
        elif att['type'] == 'int':
            structs_and_types.append("""
    return PyInt_FromLong(self->obj->%s);
""" % (att['name']))
        elif att['type'] == 'unsigned long':
            structs_and_types.append("""
    return PyLong_FromUnsignedLong(self->obj->%s);
""" % (att['name']))
        elif att['type'] == 'bool':
            structs_and_types.append("""
    return PyBool_FromLong(self->obj->%s);
""" % (att['name']))
        else: raise RuntimeError('unimpl, '+att['type']+", "+att['name'])
        structs_and_types.append("""
}
""")
        attrs += """    {"%s", %s_%s, NULL, "", NULL }, \n""" %(att['name'], obj_name, att['name'])



    # callacks
    for att in clzz['methods']['public']:
        if not 'doxygen' in att or \
                not '@callback' in att['doxygen']: continue

        method_name = att['name']
        #obj_name = pyobj(clzz['name'])
        #type_name = obj_name + "Type"
        print 'cb:',method_name, obj_name, att['parameters']
        params = ", ".join(map(lambda x: x['type']+" "+x['name'], att['parameters']))
        paramNames = ", ".join(map(lambda x: x['name'], att['parameters']))

        attrs += """    {"%s", NULL, %s_%s, "", NULL }, \n""" % (method_name, obj_name, method_name)#, f['doxygen'])


        structs_and_types.append("""
static GHashTable *%s_%s_model2pyobj = NULL;
static %s %s_%s__wrap(%s)
{
    // find py obj by what? ...model
    %s *pyobj = g_hash_table_lookup(%s_%s_model2pyobj, %s);
    PyObject *arglist = Py_BuildValue("(O)", pyobj);
    PyObject_CallObject(pyobj->%s, arglist);
    Py_DECREF(arglist);
}
""" % (obj_name, method_name, att['rtnType'], obj_name, method_name, params,
       obj_name, obj_name, method_name, paramNames, method_name))

        structs_and_types.append("""
static int %s_%s(PyObject *lob, PyObject *cb, void *v)
{
    PyObject *ret = NULL;
    %s *self = (%s *)lob;
""" % (obj_name, method_name, obj_name, obj_name))
        structs_and_types.append("""
    if (!PyCallable_Check(cb)) {
        PyErr_SetString(PyExc_TypeError, "must be callable");
        return NULL;
    }
    if (%s_%s_model2pyobj == NULL)
        %s_%s_model2pyobj = g_hash_table_new(&g_direct_hash,
					      &g_direct_equal);
    g_hash_table_insert(%s_%s_model2pyobj, self->obj, self);
""" % (obj_name, method_name, obj_name, method_name, obj_name, method_name))
        structs_and_types.append("""
    Py_XINCREF(cb);           /* Add a reference to new callback */

    Py_XDECREF(self->%s);     /* Dispose of previous callback */
    self->%s = cb;            /* Remember new callback */
    self->obj->%s = &%s_%s__wrap;
    return 0;
}
""" % (method_name, method_name, method_name, obj_name, method_name))


    if attrs != "":
        structs_and_types.append("""
static PyGetSetDef %s__getters[] = {
%s
    {NULL}
};
""" %(type_name, attrs))
        init_type_ready.append(
"""        %s.tp_getset = %s__getters;
""" % (type_name, type_name))        

def add_methods(func, funcs, clzz):
    print 'fakename', func

    type_name = ""
    proto = ""
    for f in funcs:
        if f['name'] == func or not f['name'].startswith(func): continue
        if not '@classmethod' in f['doxygen']: continue
        if 'used' in f: continue
        f['used'] = True
        method_name = f['name'][len(func)+1:]
        obj_name = pyobj(func)
        type_name = obj_name + "Type"
        print 'poddible f:',method_name, obj_name, f

        proto += """    {"%s", (PyCFunction)%s_%s, METH_VARARGS | METH_CLASS, "" },
""" % (method_name, obj_name, method_name)#, f['doxygen'])

        structs_and_types.append("""
static PyObject *%s_%s(PyObject *a, PyObject *b)
{
    PyObject *ret = NULL;
""" % (obj_name, method_name))

        print f.keys()
        if f['return'] == 'void':
            structs_and_types.append("""
    %s();
    Py_INCREF(Py_None);
    ret = Py_None;
""" % (f['name']));

        if '@return UtilArray' in f['doxygen']:
            params = []
            if len(f['parameters']) == 1 \
                    and f['parameters'][0]['type'] == 'Region *':
                params.append('region')

            structs_and_types.append("""
    UtilArray *val = %s(%s);
    ret = PyTuple_New(val->size);
    Py_ssize_t i;
    for (i=0; i<val->size; i++) {
        PyLobFont *item = PyLobFontType.tp_alloc(&PyLobFontType, 0);
        item->obj = util_arr_get(val, i);
        PyTuple_SetItem(ret, i, item);
    }
""" % (f['name'], ",".join(params)))

        structs_and_types.append("""
    return ret;
}
""")
    if type_name != "":
        structs_and_types.append("""
static PyMethodDef %s__methods[] = {
%s
    {NULL}
};
"""% (type_name, proto))
        init_type_ready.append(
"""        %s.tp_methods = %s__methods;
""" % (type_name, type_name))        

def gen(name, clzz, funcs):
    print 'Gen: '+name+", "+clzz['name']

    fakename = name
    # faked struct..
    if clzz not in all_classes.values():
        fakename = clzz['inherits'][0]['typedef']

    region = ""
    if 'doxygen' in clzz and '@model' in clzz['doxygen']:
        region = 'Region *pyRegion;'

    callbacks = ""
    for att in clzz['methods']['public']:
        if not 'doxygen' in att or \
                not '@callback' in att['doxygen']: continue

        method_name = att['name']
        obj_name = pyobj(clzz['name'])
        params = ", ".join(map(lambda x: "PyObject *"+x['name'], att['parameters']))
        callbacks += """%s (*%s)(%s);
""" %(att['rtnType'], method_name, params)
        type_name = obj_name + "Type"
        print 'cb:',method_name, obj_name, 


    struct = 'Py'+name
    typee = 'Py'+name+'Type'
    py_name = 'libvob.'+name
    nice_name = name
    pre_str = 'libvob'
    if name.startswith('Lob'):
        pre_str = 'lob'
        if len(name) > 3:
            nice_name = name[3:]
        py_name = 'libvob.lob.'+nice_name
    if name.startswith('Vob'):
        pre_str = 'vob' 
        if len(name) > 3:
            nice_name = name[3:]
        py_name = 'libvob.vob.'+nice_name
    
    just_structs.append("""
    /* *********************
    * %s stucture 
    ************************ */

    typedef struct {
        PyObject_HEAD
        %s
        %s *obj;
        %s
    } %s;

    static PyTypeObject %s = {
        PyObject_HEAD_INIT(NULL)
        0,\t\t\t\t\t/*ob_size*/
        "%s",\t\t\t/*tp_name*/
        sizeof(%s),\t\t\t/*tp_basicsize*/
    };

""" % ( struct, region, fakename, callbacks, struct, typee, py_name, struct))

    for f in funcs:
        if f['name'] == clzz['name']:
            print 'gen', f
            types = ''
            params = ''
            s = ''

            if len(f['parameters']) == 0:
                structs_and_types.append("""
PyObject *%s_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    //printf("%s_new\\n");

    %s *self;

    self = (%s *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->obj = %s();
    }
    return self;
}
""" % (typee, struct, struct, struct, f['name']))

                init_type_ready.append(
                    "        %s.tp_new = %s_new;\n" % (typee, typee))

            elif len(f['parameters']) >= 1 \
                    and f['parameters'][0]['type'] == 'Region *':
                structs_and_types.append("""
PyObject *%s_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    //printf("%s_new\\n");

    %s *self;

    self = (%s *)type->tp_alloc(type, 0);
    if (self != NULL) {
""" % (typee, struct, struct, struct))

                adder = None
                for func in funcs:
                    if func['name'] == clzz['name']+'_add':
                        adder = func
                        print 'adder', adder
                        break

                for idx in range(len(f['parameters'])):
                    param = f['parameters'][idx]
                    if idx == 0 and param['type'] == 'Region *':
                        if 'doxygen' in clzz and '@model' in clzz['doxygen']:
                            s += '        self->pyRegion = util_regs_create("'+py_name+'");\n'              
                            s += '        Region *p0 = self->pyRegion;\n'
                        else:
                            s += '        Region *p0 = region;\n'
                    else:
                        if param['type'] == 'float':
                            s += '        float p'+str(idx)+';\n' 
                            types += 'f'
                            params += '&p'+str(idx)+', '
                        elif param['type'].startswith('Lob') \
                                and 'Model' in param['type']:
                            s += '        PyLobModel *p'+str(idx)+';\n' 
                            types += 'O'
                            params += '&p'+str(idx)+', '
                        elif param['type'].startswith('Lob') \
                                or param['type'].startswith('Vob'):
                            s += '        PyLob *p'+str(idx)+';\n' 
                            types += 'O'
                            params += '&p'+str(idx)+', '
                        elif param['type'] == 'Size *':
                            s += '        PySize *p'+str(idx)+';\n' 
                            types += 'O'
                            params += '&p'+str(idx)+', '
                        elif param['type'] == 'char *':
                            s += '        const char *p'+str(idx)+';\n' 
                            types += 's'
                            params += '&p'+str(idx)+', '
                        elif param['type'] == 'bool':
                            s += '        bool p'+str(idx)+';\n' 
                            types += 'i'
                            params += '&p'+str(idx)+', '
                        elif param['type'].startswith('enum '):
                            s += '        int p'+str(idx)+';\n' 
                            types += 'i'
                            params += '&p'+str(idx)+', '
                        else:
                            print param
                            raise RuntimeError('asdf'+param)
                if adder != None:
                    s += '        PyObject *list = NULL;\n'
                    types += 'O'
                    params += '&list  '

                if len(f['parameters']) > 1 or adder != None:
                    s += '        if (! PyArg_ParseTuple(args, "%s", %s)) {\n' \
                        %(types, params[:-2])
                    s += '            Py_DECREF(self);\n'
                    s += '            return NULL;\n'
                    s += '        }\n'
                s += '        self->obj = '+f['name']+'('
                for i in range(len(f['parameters'])): 
                    if i > 0:
                        s += ', '
                    s+= 'p'+str(i)
                    if f['parameters'][i]['type'].startswith('Lob') \
                            or f['parameters'][i]['type'].startswith('Vob') \
                            or f['parameters'][i]['type'].startswith('Size'):
                        s += '->obj'
                s += ');\n'
                if adder != None:
                    s += """
        if (list != NULL && PySequence_Check(list)) {
            Py_ssize_t len = PySequence_Size(list);
            Py_ssize_t idx = 0;
            for (; idx<len; idx++) {
                //printf("got arg...%i\\n", idx);
"""
                    pars = ""
                    for i in range(len(adder['parameters'][2:])):
                        p = adder['parameters'][2:][i]
                        if i > 0:
                            s += \
"""                idx++;
"""
                            pars += ", "
                        s += \
"""                PyObject *lob%s = PySequence_GetItem(list, idx);
""" % (str(i))
                        pars += "%slob%s%s" % (to_c(p)['pre'], str(i), to_c(p)['post'])
                #//if (PyObject_TypeCheck(lob, &PyLobType))
                    s += \
"""                %s_add(region, (%s*)self->obj, %s);
            }
        }
""" % (clzz['name'], fakename, pars)

                s += '    }\n    return (PyObject *) self;\n}\n\n'
                structs_and_types.append(s)

                init_type_ready.append(
                    "        %s.tp_new = %s_new;\n" % (typee, typee))
            elif len(f['parameters']) > 0 \
                    and f['parameters'][0]['type'] == 'Region *' \
                    and len(filter(lambda x: x['name'] == clzz['name']+'_add', funcs)) == 1:
                structs_and_types.append("""
PyObject *%s_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    printf("%s_new\\n");

    %s *self;

    self = (%s *)type->tp_alloc(type, 0);
    if (self != NULL) {
        self->obj = %s(region);

        PyObject *list = NULL;
        if (! PyArg_ParseTuple(args, "O", &list)) {
            Py_DECREF(self);
            return NULL;
        }
        if (list != NULL && PySequence_Check(list)) {
            Py_ssize_t len = PySequence_Size(list);
            Py_ssize_t idx = 0;
            for (; idx<len; idx++) {
                printf("got arg...%%i\\n", idx);
                PyObject *lob = PySequence_GetItem(list, idx);
                //if (PyObject_TypeCheck(lob, &PyLobType))
                    %s_add(region, (%s*)self->obj, ((PyLob*)lob)->obj);
                //else printf("asdf\\n");

            }
        }
    }
    return self;
}
        
""" % (typee, typee, struct, struct, clzz['name'], clzz['name'], fakename))

                init_type_ready.append(
                    "        %s.tp_new = %s_new;\n" % (typee, typee))
                
            else:
                init_type_ready.append(
                    "        %s.tp_new = PyType_GenericNew;\n"\
                        % (typee))
                
    add_methods(clzz['name'], funcs, clzz)
    add_attributes(clzz)

    init_type_ready.append(
"""        %s.tp_flags = Py_TPFLAGS_DEFAULT;
        if (PyType_Ready(&%s) < 0)
            return;\n
""" % (typee,typee))

    init_add_objects.append("""
    Py_INCREF(&%s);
    PyModule_AddObject(%s, "%s", (PyObject *)&%s);
""" % (typee, pre_str, nice_name, typee))
                           
if __name__ == '__main__':

    headers = []
    for path in ['src/lob', 'src/vob']:
        for root, dirs, files in os.walk(path):
            if root.find('src/gfx') >= 0: continue

            for f in files:
                if f.endswith('.h'):
                    headers.append(root+'/'+f)

    files = []
    for hdr in headers:
        files.append(CppHeaderParser.CppHeader(hdr))

    all_funcs = []
    all_classes = {}
    for f in files:
        if f.doc != None and '@nopython' in f.doc: continue
        #print 'func: ',f
        for func in f.func_protos:
            print 'func: ',func
            all_funcs.append(func)
        for name, c in f.classes.items():
            if c['typedef'] != '':
                name = c['typedef']
            all_classes[name] = c

    for name, clzz in all_classes.items():
        #print name, clzz['typedef']
        if len(clzz['properties']['public']) > 0:
            var = clzz['properties']['public'][0]
            var_type = clzz['properties']['public'][0]['type']
            if var_type in all_classes.keys():
                inherits = all_classes[var_type]
                inherits['access'] = 'public'
                inherits['class'] = inherits['name']
                print 'inherits', inherits['name']
                clzz['inherits'].append(inherits)


    def children(name):
        for nam, clzz in all_classes.items():
            if len(clzz['inherits']) > 0:
                if name == clzz['inherits'][0]['typedef']:
                    yield clzz

    # Sort the order by parenting. This is done because of we don't
    # provide prototypes in C side. Same limitation in python as well..

    def tree(name, ind):
        gen(name, all_classes[name], all_funcs)
        #print ind, name
        for nam, clzz in all_classes.items():
            if len(clzz['inherits']) > 0:
                if name == clzz['inherits'][0]['typedef']:
                    tree(nam, ind+'   ')

    import copy
    items = copy.copy(all_classes.items())
    items = filter(lambda x: len(x[1]['inherits']) == 0, items)
    def needs(c):
        if 'doxygen' in c and '@needs' in c['doxygen']:
            s = c['doxygen'].split()
            return s[s.index('@needs')+1]
        return ""
        
    for i in range(len(items)):
        for j in range(i, len(items)):
            a, b = items[i], items[j]
            if needs(a[1]) == b[0]:
                items[j] = a
                items[i] = b

    # bind those without children
    for name, clzz in items:
        if len(list(children(name))) == 0 and len(clzz['inherits']) == 0:
            #print name
            gen(name, clzz, all_funcs)
    for name, clzz in items:
        if len(list(children(name))) > 0:
            tree(name, '')
    #print all_classes

    # Simulate missing classes by creating from functions.
    # guess class by function name, e.g. log_font -> LobFont
    for func in all_funcs:
        n = func['name']
        try:
            pass#print 'doc2', func['doxygen']
        except: pass
        if n.endswith('_add'):
            continue
        if func['return'] not in all_classes.keys():
            continue
        #print '?',n
        parts = n.split('_')
        needClzz = "".join([ part[0].upper()+part[1:] for part in parts[:]])
        nameClzz = "".join([ part[0].upper()+part[1:] for part in parts[1:]])
        if needClzz in all_classes.keys() or nameClzz in all_classes.keys():
            continue
        print 'need',needClzz
        clzz = CppHeaderParser.CppClass(['struct', parts[0].lower()])
        inherits = all_classes[func['return']]
        inherits['access'] = 'public'
        inherits['class'] = inherits['name']
        clzz['inherits'].append(inherits)
        clzz['name'] = n
        gen(needClzz, clzz, all_funcs)

    # Add static functions to classes.

    write('py/gen_protos.c', just_structs)
    write('py/gen_structs.c', structs_and_types)
    write('py/gen_init_types.c', init_type_ready)
    write('py/gen_add_obs.c', init_add_objects)



