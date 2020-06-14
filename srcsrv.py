import logging
import os
import re
import time
import subprocess

from glob import glob

HEAD = r"""SRCSRV: ini ------------------------------------------------

VERSION=1
INDEXVERSION=2
VERCTRL={1}
DATETIME={0}
SRCSRV: variables ------------------------------------------
EXTRACT_TARGET=%targ%\%fnbksl%(%var3%)\%var4%\%fnfile%(%var1%)
EXTRACT_CMD=cmd /c "{2} > "%EXTRACT_TARGET%""
SRCSRVTRG=%EXTRACT_TARGET%
SRCSRVCMD=%EXTRACT_CMD%"""

BODY = r"SRCSRV: source files ---------------------------------------"
TAIL = r"SRCSRV: end ------------------------------------------------"

class Program:
    this_dir_path = os.path.normpath(os.path.dirname(os.path.realpath(__file__)))

    @classmethod
    def get_builtin_path(cls, rel_path):
        return os.path.normpath(os.path.join(cls.this_dir_path, rel_path))

    def __init__(self, exe_paths):
        for exe_path in exe_paths:
            if os.path.isfile(exe_path):
                self.exe_path = exe_path
                break
        else:
            raise RuntimeError("NO_EXE_PATH:" + repr(exe_paths))

    def read_pipe(self, args):
        logging.debug("{0} {1}".format(self.exe_path, ' '.join(args)))
        proc = subprocess.Popen([self.exe_path] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if err:
            raise RuntimeError(err)
        return out

    def write_pipe(self, args, data):
        logging.debug("{0} {1}".format(self.exe_path, ' '.join(args)))
        proc = subprocess.Popen([self.exe_path] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        out, err = proc.communicate(input=data)
        if err:
            raise RuntimeError(err)
        return out

class SrcTool:
    def __init__(self):
        self.program = Program([
            Program.get_builtin_path(r"10\Debuggers\x64\srcsrv\srctool.exe"), 
            r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\srcsrv\srctool.exe"])

    def gen_matched_paths(self, pdb_path, prefix):
        lower_prefix = prefix.lower()
        try:
            lines = self.program.read_pipe(["-r", pdb_path]).splitlines()
        except RuntimeError as exc:
            logging.warning("src_tool_read_pdb:{0}".format(str(exc)))
            return

        for src_path in lines[:-1]:
            if src_path.startswith(lower_prefix):
                yield src_path

class PDBStr:
    def __init__(self):
        self.program = Program([
            Program.get_builtin_path(r"10\Debuggers\x64\srcsrv\pdbstr.exe"), 
            r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\srcsrv\pdbstr.exe"])

    def bind_index_data(self, pdb_path, ini_data):
        return self.program.write_pipe(['-w', '-s:srcsrv', '-p:' + pdb_path], data=ini_data)

    def bind_index_file(self, pdb_path, ini_path):
        return self.program.read_pipe(['-w', '-s:srcsrv', '-p:' + pdb_path, '-i:' + ini_path])

    def dump_index(self, pdb_path):
        return self.program.read_pipe(['-r', '-s:srcsrv', '-p:' + pdb_path])

class Subversion:
    def __init__(self):
        self.program = Program([
            r"C:\Program Files\TortoiseSVN\bin\svn.exe",
            Program.get_builtin_path(r"..\svn\Win64\svn.exe")])

    def ls(self, uri):
        return self.program.read_pipe(['ls', '-R', uri]).splitlines()

class VCSManager:
    def __init__(self, base_path, vcs_name, vcs_addr, vcs_leaf, vcs_cat):
        logging.info("vcs:{0} addr:{1} leaf:{2} base:{3}".format(vcs_name, vcs_addr, vcs_leaf, base_path))
        self.base_path = base_path
        self.vcs_name = vcs_name
        self.vcs_addr = vcs_addr
        self.vcs_leaf = vcs_leaf
        self.vcs_cat = vcs_cat

    def dump_index(self, pdb_path, src_paths):
        def gen_index_blocks():
            yield HEAD.format(time.asctime(), self.vcs_name, self.vcs_cat)

            yield BODY

            vcs_count = 0
            for src_path in src_paths:
                rel_path = src_path[len(self.base_path) + 1:]
                vcs_path = self._convert_vcs_path(rel_path)
                if vcs_path:
                    yield '*'.join((src_path, self.vcs_addr, vcs_path, self.vcs_leaf))
                    vcs_count += 1

            yield TAIL
            logging.info("index_pdb:{0} vcs_count:{1}".format(pdb_path, vcs_count))

        logging.info("index_pdb:{0} src_count:{1}".format(pdb_path, len(src_paths)))
        return "\n".join(gen_index_blocks())

    def _convert_vcs_path(self, rel_path):
        return rel_path

class SevenZipManager(VCSManager):
    def __init__(self, base_path, arch_path):
        dir_names = arch_path.split(os.sep)
        VCSManager.__init__(self, base_path,
            vcs_name = 'SevenZip', 
            vcs_addr = os.sep.join(dir_names[:-1]), 
            vcs_leaf = dir_names[-1],
            vcs_cat = r'"C:\Program Files\7-Zip\7z.exe" e -so "%var2%\%var4%" "%var3%"')

class SubversionManager(VCSManager):
    def __init__(self, base_path, repo_uri):
        vcs_addr, vcs_leaf = repo_uri.split('@')
        VCSManager.__init__(self, base_path,
            vcs_name = 'Subversion', 
            vcs_addr = vcs_addr, 
            vcs_leaf = vcs_leaf,
            vcs_cat = r'svn.exe cat "%var2%/%var3%@%var4%" --non-interactive')

        svn = Subversion()
        key_paths = dict((path.lower(), path) for path in svn.ls(vcs_addr))
        self.key_paths = key_paths

    def _convert_vcs_path(self, rel_path):
        key = rel_path.replace(os.sep, '/')
        return self.key_paths.get(key, '')

class ArgumentParser:
    def __init__(self, args):
        self.args = args
        self.base_path = ""
        self.pdb_patterns = []
        self.src_dirs = []
        self.vcs_uri = ""
        self.debug = False

    def parse(self):
        if len(self.args) == 1:
            return False

        for arg in self.args[1:]:
            if arg.startswith("-p:"):
                self.pdb_patterns.append(arg[3:])
            elif arg.startswith("-s:"):
                self.src_dirs = arg[3:]
            elif arg.startswith("-b:"):
                self.base_path = arg[3:]
            elif arg.startswith("-u:"):
                self.vcs_uri = arg[3:]
            elif arg.startswith("-v:"):
                self.vcs_mode = arg[3:]
            elif arg == "--debug":
                self.debug = True
            else:
                logging.error("UNKNOWN_ARGUMENT:'{0}'".format(arg))
                return False

        return True

    def gen_pdb_paths(self):
        for pdb_pattern in self.pdb_patterns:
            for pdb_path in glob(pdb_pattern):
                yield pdb_path

    @property
    def program(self):
        return os.path.basename(self.args[0])

def main(args):
    arg_parser = ArgumentParser(args)
    if not arg_parser.parse():
        print("{0} [--debug] [-b:BASE_PATH] [-p:PDB_PATH] [-v:VCS] [-u:URI]".format(arg_parser.program))
        return -1

    if arg_parser.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if arg_parser.vcs_mode == "svn":
        vcs_mgr = SubversionManager(arg_parser.base_path, arg_parser.vcs_uri)
    elif arg_parser.vcs_mode == "7z":
        vcs_mgr = SevenZipManager(arg_parser.base_path, arg_parser.vcs_uri)
    else:
        logging.error("UNKNOWN_VCS: {0}".format(arg_parser.vcs_mode))
        return -2

    pdb_paths = list(arg_parser.gen_pdb_paths())
    if not pdb_paths:
        logging.error("NOT_FOUND_PDB: {0}".format('+'.join(arg_parser.pdb_patterns)))
        return -3

    pdb_str = PDBStr()
    src_tool = SrcTool()
    for pdb_path in pdb_paths:
        src_paths = list(src_tool.gen_matched_paths(pdb_path, prefix=arg_parser.base_path))
        if src_paths:
            idx_data = vcs_mgr.dump_index(pdb_path, src_paths)
            idx_path = pdb_path + '.srcsrv'
            with open(idx_path, 'w') as idx_file:
                idx_file.write(idx_data)
            pdb_str.bind_index_file(pdb_path, idx_path)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))