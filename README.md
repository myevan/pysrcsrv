# pysrcsrv

WindowsKits Debugger Source Server Helper

## Requirements

* python2
* WindowsKits (Debugging for Windows)

## Subversion

### svn checkout

```bat
svn co http://host/project/trunk S:\Works\Project
```

### svn index

```bat
for /f "tokens=2" %%i in ('%SVN% info %WORK_ROOT% ^| findstr "^URL:"') do set SVN_BRANCH_URL=%%i
for /f "tokens=4" %%i in ('%SVN% info %WORK_ROOT% ^| findstr /C:"Last Changed Rev:"') do set SVN_REV=%%i

python pysrcsrv\srcsrv.py -v:svn -u:%SVN_BRANCH_URL%@%SVN_REV% -b:S:\Works\Project -p:S:\Works\Project\Binaries\Win64\*.pdb
```

## 7-Zip

### 7z archive

```bat
pushd S:\Works\Project
"C:\Program Files\7-Zip\7z.exe" a \\Host\Archives\Project\trunk\Project-ver.7z -ir!*.h -ir!*.c -ir!*.hpp -ir!*.cpp
popd
```

### 7z index

```bat
python pysrcsrv\srcsrv.py -v:7z -u:\\Host\Archives\Project\trunk\Project-ver.7z -b:S:\Works\Project -p:S:\Works\Project\Binaries\Win64\*.pdb
```

## symstore

```bat
set WORK_NAME=Project
set WORK_ROOT=S:\Works\Project
set SYM_ROOT=\\Host\Symbols
set SYM_STORE="C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\symstore.exe"
%SYM_STORE% add /r /s %SYM_ROOT% /t %WORK_NAME% /f %WORK_ROOT%\Binaries\Win64\*.pdb
```