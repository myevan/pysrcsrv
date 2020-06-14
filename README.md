# pysrcsrv

WindowsKits Debugger Source Server Helper

## Requirements

* python2
* WindowsKits (Debugging for Windows)

## Subversion

### svn checkout

```bat
set BRANCH_URL=http://host/project/trunk
set WORK_ROOT=S:\Works\Project
svn co %BRANCH_URL% %WORK_ROOT%
```

### svn index

```bat
for /f "tokens=2" %%i in ('%SVN% info %WORK_ROOT% ^| findstr "^URL:"') do set BRANCH_URL=%%i
for /f "tokens=4" %%i in ('%SVN% info %WORK_ROOT% ^| findstr /C:"Last Changed Rev:"') do set REV=%%i

python pysrcsrv\srcsrv.py -v:svn -u:%BRANCH_URL%@%REV% -b:%WORK_ROOT% -p:%WORK_ROOT%\Binaries\Win64\*.pdb
```

## 7-Zip

### 7z archive

```bat
set VER=YYYYMMDD_hhmmss
set BRANCH=trunk
set WORK_NAME=Project
set WORK_ROOT=S:\Works\Project
set ARCH_ROOT=\\Host\Archives
set ARCH_FILE=%ARCH_ROOT%\%WORK_NAME%\%BRANCH%\%WORK_NAME%-%VER%.7z
pushd %WORK_ROOT%
"C:\Program Files\7-Zip\7z.exe" a %ARCH_FILE% -ir!*.h -ir!*.c -ir!*.hpp -ir!*.cpp
popd
```

### 7z index

```bat
set VER=YYYYMMDD_hhmmss
set BRANCH=trunk
set WORK_NAME=Project
set WORK_ROOT=S:\Works\Project
set ARCH_ROOT=\\Host\Archives
set ARCH_FILE=%ARCH_ROOT%\%WORK_NAME%\%BRANCH%\%WORK_NAME%-%VER%.7z
python pysrcsrv\srcsrv.py -v:7z -u:%ARCH_FILE% -b:%WORK_ROOT% -p:%WORK_ROOT%\Binaries\Win64\*.pdb
```

## symstore

```bat
set WORK_NAME=Project
set WORK_ROOT=S:\Works\Project
set SYM_ROOT=\\Host\Symbols
set SYM_STORE="C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\symstore.exe"
%SYM_STORE% add /r /s %SYM_ROOT% /t %WORK_NAME% /f %WORK_ROOT%\Binaries\Win64\*.pdb
```