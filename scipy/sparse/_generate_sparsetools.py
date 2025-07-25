#!/usr/bin/env python3
"""
python generate_sparsetools.py

Generate manual wrappers for C++ sparsetools code.

Type codes used:

    'i':  integer scalar
    'I':  integer array
    'T':  data array
    'B':  boolean array
    'V':  std::vector<integer>*
    'W':  std::vector<data>*
    '*':  indicates that the next argument is an output argument
    'v':  void
    'l':  64-bit integer scalar

See sparsetools.cxx for more details.

"""
import argparse
import os
from stat import ST_MTIME


#
# List of all routines and their argument types.
#
# The first code indicates the return value, the rest the arguments.
#

# bsr.h
BSR_ROUTINES = """
bsr_diagonal        v iiiiiIIT*T
bsr_tocsr           v iiiiIIT*I*I*T
bsr_scale_rows      v iiiiII*TT
bsr_scale_columns   v iiiiII*TT
bsr_sort_indices    v iiii*I*I*T
bsr_transpose       v iiiiIIT*I*I*T
bsr_matmat          v iiiiiiIITIIT*I*I*T
bsr_matvec          v iiiiIITT*T
bsr_matvecs         v iiiiiIITT*T
bsr_elmul_bsr       v iiiiIITIIT*I*I*T
bsr_eldiv_bsr       v iiiiIITIIT*I*I*T
bsr_plus_bsr        v iiiiIITIIT*I*I*T
bsr_minus_bsr       v iiiiIITIIT*I*I*T
bsr_maximum_bsr     v iiiiIITIIT*I*I*T
bsr_minimum_bsr     v iiiiIITIIT*I*I*T
bsr_ne_bsr          v iiiiIITIIT*I*I*B
bsr_lt_bsr          v iiiiIITIIT*I*I*B
bsr_gt_bsr          v iiiiIITIIT*I*I*B
bsr_le_bsr          v iiiiIITIIT*I*I*B
bsr_ge_bsr          v iiiiIITIIT*I*I*B
"""

# csc.h
CSC_ROUTINES = """
csc_matvec          v iiIITT*T
csc_matvecs         v iiiIITT*T
"""

# csr.h
CSR_ROUTINES = """
csr_matmat_maxnnz   l iiIIII
csr_matmat          v iiIITIIT*I*I*T
csr_diagonal        v iiiIIT*T
csr_tocsc           v iiIIT*I*I*T
csr_tobsr           v iiiiIIT*I*I*T
csr_todense         v iiIIT*T
csr_matvec          v iiIITT*T
csr_matvecs         v iiiIITT*T
csr_elmul_csr       v iiIITIIT*I*I*T
csr_eldiv_csr       v iiIITIIT*I*I*T
csr_plus_csr        v iiIITIIT*I*I*T
csr_minus_csr       v iiIITIIT*I*I*T
csr_maximum_csr     v iiIITIIT*I*I*T
csr_minimum_csr     v iiIITIIT*I*I*T
csr_ne_csr          v iiIITIIT*I*I*B
csr_lt_csr          v iiIITIIT*I*I*B
csr_gt_csr          v iiIITIIT*I*I*B
csr_le_csr          v iiIITIIT*I*I*B
csr_ge_csr          v iiIITIIT*I*I*B
csr_scale_rows      v iiII*TT
csr_scale_columns   v iiII*TT
csr_sort_indices    v iI*I*T
csr_eliminate_zeros v ii*I*I*T
csr_sum_duplicates  v ii*I*I*T
get_csr_submatrix   v iiIITiiii*V*V*W
csr_row_index       v iIIIT*I*T
csr_row_slice       v iiiIIT*I*T
csr_column_index1   v iIiiII*I*I
csr_column_index2   v IIiIT*I*T
csr_sample_values   v iiIITiII*T
csr_count_blocks    i iiiiII
csr_sample_offsets  i iiIIiII*I
csr_hstack          v iiIIIT*I*I*T
expandptr           v iI*I
test_throw_error    i
csr_has_sorted_indices    i iII
csr_has_canonical_format  i iII
"""

# coo.h, dia.h, csgraph.h
OTHER_ROUTINES = """
coo_tocsr           v iiiIIT*I*I*T
coo_todense         v iilIIT*Ti
coo_todense_nd      v IllIT*Ti
coo_matvec          v lIITT*T
coo_matvec_nd       v llIITT*T
coo_matmat_dense    v llIITT*T
coo_matmat_dense_nd v lllIIITT*T
dia_tocsr           i iiiiITI*T*I*I
dia_matmat          v iiiiITiiiIT*V*W
dia_matvec          v iiiiITT*T
dia_matvecs         v iiiiITiT*T
cs_graph_components i iII*I
"""

# List of compilation units
COMPILATION_UNITS = [
    ('bsr', BSR_ROUTINES),
    ('csr', CSR_ROUTINES),
    ('csc', CSC_ROUTINES),
    ('other', OTHER_ROUTINES),
]

#
# List of the supported index typenums and the corresponding C++ types
#
I_TYPES = [
    ('NPY_INT32', 'npy_int32'),
    ('NPY_INT64', 'npy_int64'),
]

#
# List of the supported data typenums and the corresponding C++ types
#
T_TYPES = [
    ('NPY_BOOL', 'npy_bool_wrapper'),
    ('NPY_BYTE', 'npy_byte'),
    ('NPY_UBYTE', 'npy_ubyte'),
    ('NPY_SHORT', 'npy_short'),
    ('NPY_USHORT', 'npy_ushort'),
    ('NPY_INT', 'npy_int'),
    ('NPY_UINT', 'npy_uint'),
    ('NPY_LONG', 'npy_long'),
    ('NPY_ULONG', 'npy_ulong'),
    ('NPY_LONGLONG', 'npy_longlong'),
    ('NPY_ULONGLONG', 'npy_ulonglong'),
    ('NPY_FLOAT', 'npy_float'),
    ('NPY_DOUBLE', 'npy_double'),
    ('NPY_LONGDOUBLE', 'npy_longdouble'),
    ('NPY_CFLOAT', 'npy_cfloat_wrapper'),
    ('NPY_CDOUBLE', 'npy_cdouble_wrapper'),
    ('NPY_CLONGDOUBLE', 'npy_clongdouble_wrapper'),
]

#
# Code templates
#

THUNK_TEMPLATE = """
static PY_LONG_LONG %(name)s_thunk(int I_typenum, int T_typenum, void **a)
{
    %(thunk_content)s
}
"""

METHOD_TEMPLATE = """
PyObject *
%(name)s_method(PyObject *self, PyObject *args)
{
    return call_thunk('%(ret_spec)s', "%(arg_spec)s", %(name)s_thunk, args);
}
"""

GET_THUNK_CASE_TEMPLATE = """
static int get_thunk_case(int I_typenum, int T_typenum)
{
    %(content)s;
    return -1;
}
"""


#
# Code generation
#


def newer(source, target):
    """
    Return true if 'source' exists and is more recently modified than
    'target', or if 'source' exists and 'target' doesn't.  Return false if
    both exist and 'target' is the same age or younger than 'source'.
    """
    if not os.path.exists(source):
        raise ValueError(f"file '{os.path.abspath(source)}' does not exist")
    if not os.path.exists(target):
        return 1

    mtime1 = os.stat(source)[ST_MTIME]
    mtime2 = os.stat(target)[ST_MTIME]

    return mtime1 > mtime2


def get_thunk_type_set():
    """
    Get a list containing cartesian product of data types, plus a getter routine.

    Returns
    -------
    i_types : list [(j, I_typenum, None, I_type, None), ...]
         Pairing of index type numbers and the corresponding C++ types,
         and an unique index `j`. This is for routines that are parameterized
         only by I but not by T.
    it_types : list [(j, I_typenum, T_typenum, I_type, T_type), ...]
         Same as `i_types`, but for routines parameterized both by T and I.
    getter_code : str
         C++ code for a function that takes I_typenum, T_typenum and returns
         the unique index corresponding to the lists, or -1 if no match was
         found.

    """
    it_types = []
    i_types = []

    j = 0

    getter_code = "    if (0) {}"

    for I_typenum, I_type in I_TYPES:
        piece = """
        else if (I_typenum == %(I_typenum)s) {
            if (T_typenum == -1) { return %(j)s; }"""
        getter_code += piece % dict(I_typenum=I_typenum, j=j)

        i_types.append((j, I_typenum, None, I_type, None))
        j += 1

        for T_typenum, T_type in T_TYPES:
            piece = """
            else if (T_typenum == %(T_typenum)s) { return %(j)s; }"""
            getter_code += piece % dict(T_typenum=T_typenum, j=j)

            it_types.append((j, I_typenum, T_typenum, I_type, T_type))
            j += 1

        getter_code += """
        }"""

    return i_types, it_types, GET_THUNK_CASE_TEMPLATE % dict(content=getter_code)


def parse_routine(name, args, types):
    """
    Generate thunk and method code for a given routine.

    Parameters
    ----------
    name : str
        Name of the C++ routine
    args : str
        Argument list specification (in format explained above)
    types : list
        List of types to instantiate, as returned `get_thunk_type_set`

    """

    ret_spec = args[0]
    arg_spec = args[1:]

    def get_arglist(I_type, T_type):
        """
        Generate argument list for calling the C++ function
        """
        args = []
        next_is_writeable = False
        j = 0
        for t in arg_spec:
            const = '' if next_is_writeable else 'const '
            next_is_writeable = False
            if t == '*':
                next_is_writeable = True
                continue
            elif t == 'i':
                args.append(f"*({const + I_type}*)a[{j}]")
            elif t == 'I':
                args.append(f"({const + I_type}*)a[{j}]")
            elif t == 'T':
                args.append(f"({const + T_type}*)a[{j}]")
            elif t == 'B':
                args.append(f"(npy_bool_wrapper*)a[{j}]")
            elif t == 'V':
                if const:
                    raise ValueError("'V' argument must be an output arg")
                args.append(f"(std::vector<{I_type}>*)a[{j}]")
            elif t == 'W':
                if const:
                    raise ValueError("'W' argument must be an output arg")
                args.append(f"(std::vector<{T_type}>*)a[{j}]")
            elif t == 'l':
                args.append(f"*({const}npy_int64*)a[{j}]")
            else:
                raise ValueError(f"Invalid spec character {t!r}")
            j += 1
        return ", ".join(args)

    # Generate thunk code: a giant switch statement with different
    # type combinations inside.
    thunk_content = """int j = get_thunk_case(I_typenum, T_typenum);
    switch (j) {"""
    for j, I_typenum, T_typenum, I_type, T_type in types:
        arglist = get_arglist(I_type, T_type)

        piece = """
        case %(j)s:"""
        if ret_spec == 'v':
            piece += """
            (void)%(name)s(%(arglist)s);
            return 0;"""
        else:
            piece += """
            return %(name)s(%(arglist)s);"""
        thunk_content += piece % dict(j=j, I_type=I_type, T_type=T_type,
                                      I_typenum=I_typenum, T_typenum=T_typenum,
                                      arglist=arglist, name=name)

    thunk_content += """
    default:
        throw std::runtime_error("internal error: invalid argument typenums");
    }"""

    thunk_code = THUNK_TEMPLATE % dict(name=name,
                                       thunk_content=thunk_content)

    # Generate method code
    method_code = METHOD_TEMPLATE % dict(name=name,
                                         ret_spec=ret_spec,
                                         arg_spec=arg_spec)

    return thunk_code, method_code


def main():
    p = argparse.ArgumentParser(usage=(__doc__ or '').strip())

    p.add_argument("--no-force", action="store_false",
                   dest="force", default=True)
    p.add_argument("-o", "--outdir", type=str,
                   help="Relative path to the output directory")
    options = p.parse_args()

    names = []

    i_types, it_types, getter_code = get_thunk_type_set()

    # Generate *_impl.h for each compilation unit
    for unit_name, routines in COMPILATION_UNITS:
        thunks = []
        methods = []

        # Generate thunks and methods for all routines
        for line in routines.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            try:
                name, args = line.split(None, 1)
            except ValueError as e:
                raise ValueError(f"Malformed line: {line!r}") from e

            args = "".join(args.split())
            if 't' in args or 'T' in args:
                thunk, method = parse_routine(name, args, it_types)
            else:
                thunk, method = parse_routine(name, args, i_types)

            if name in names:
                raise ValueError(f"Duplicate routine {name!r}")

            names.append(name)
            thunks.append(thunk)
            methods.append(method)

        # Produce output
        if options.outdir:
            # Used by Meson (options.outdir == scipy/sparse/sparsetools)
            outdir = os.path.join(os.getcwd(), options.outdir)

        dst = os.path.join(outdir,
                           unit_name + '_impl.h')
        if newer(__file__, dst) or options.force:
            if not options.outdir:
                # Be silent if we're using Meson. TODO: add --verbose option
                print(f"[generate_sparsetools] generating {dst!r}")
            with open(dst, 'w') as f:
                write_autogen_blurb(f)
                f.write(getter_code)
                for thunk in thunks:
                    f.write(thunk)
                for method in methods:
                    f.write(method)
        else:
            if not options.outdir:
                # Be silent if we're using Meson
                print(f"[generate_sparsetools] {dst!r} already up-to-date")

    # Generate code for method struct
    method_defs = ""
    for name in names:
        method_defs += (f"PyObject *{name}"
                        f"_method(PyObject *, PyObject *);\n")

    method_struct = """\nstatic struct PyMethodDef sparsetools_methods[] = {"""
    for name in names:
        method_struct += ("""
            {{"{name}", (PyCFunction){name}_method, METH_VARARGS, NULL}},"""
            .format(**dict(name=name))
        )
    method_struct += """
        {NULL, NULL, 0, NULL}
    };"""

    # Produce sparsetools_impl.h
    dst = os.path.join(outdir, 'sparsetools_impl.h')
    if newer(__file__, dst) or options.force:
        if not options.outdir:
            # Be silent if we're using Meson.
            print(f"[generate_sparsetools] generating {dst!r}")
        with open(dst, 'w') as f:
            write_autogen_blurb(f)
            f.write(method_defs)
            f.write(method_struct)
    else:
        if not options.outdir:
            # Be silent if we're using Meson
            print(f"[generate_sparsetools] {dst!r} already up-to-date")


def write_autogen_blurb(stream):
    stream.write("""\
/* This file is autogenerated by generate_sparsetools.py
 * Do not edit manually or check into VCS.
 */
""")


if __name__ == "__main__":
    main()
