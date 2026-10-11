$ErrorActionPreference = "Stop"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher is missing. Install Python 3.11 x64 first."
}

$python = (py -3.11 -c "import sys; print(sys.executable)").Trim()
if (-not $python) {
    throw "Python 3.11 was not found. Install Python 3.11 x64 and reopen PowerShell."
}

$venv = Join-Path $PSScriptRoot ".venv311"
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) {
    & $python -m venv $venv
}

$venvPython = Join-Path $venv "Scripts\python.exe"
& $venvPython -c "import sys; assert sys.version_info[:2] == (3, 11), sys.version"
if ($LASTEXITCODE -ne 0) { throw "The virtual environment is not Python 3.11." }
& $venvPython -m pip install --upgrade pip "setuptools<70" wheel
if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip tooling." }
& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Base dependencies failed to install." }

# QuickUMLS lists leveldb as a dependency, but leveldb has no usable
# Windows/Python 3.11 wheel. QuickUMLS 1.4 supports unqlite instead.
$env:PYTHONUTF8 = "1"
& $venvPython -m pip install "Cython<3" unidecode six
if ($LASTEXITCODE -ne 0) { throw "QuickUMLS build tooling failed to install." }
& $venvPython -m pip install --no-build-isolation "unqlite==0.9.5" "pysimstring==1.3.0"
if ($LASTEXITCODE -ne 0) { throw "QuickUMLS native dependencies failed to install." }
& $venvPython -m pip install --no-deps "quickumls==1.4.2"
if ($LASTEXITCODE -ne 0) { throw "QuickUMLS failed to install." }

# AlignScore 0.1.3 publishes a torch<2 metadata restriction although its
# scorer is usable with the Python 3.11-compatible Torch version above.
& $venvPython -m pip install --no-deps "git+https://github.com/yuh-zha/AlignScore@a0936d5afee642a46b22f6c02a163478447aa493"
if ($LASTEXITCODE -ne 0) { throw "AlignScore failed to install." }
& $venvPython -m pip install "pytorch-lightning==1.9.5" "jsonlines==2.0.0" "tensorboard==2.14.0" "protobuf==3.20.3"
if ($LASTEXITCODE -ne 0) { throw "AlignScore runtime dependencies failed to install." }
& $venvPython -m pip install "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.4.1/en_core_web_sm-3.4.1.tar.gz"
if ($LASTEXITCODE -ne 0) { throw "The spaCy English model failed to install." }
& $venvPython -c "import nltk; nltk.download('punkt', quiet=True)"
if ($LASTEXITCODE -ne 0) { throw "NLTK punkt data failed to install." }

& $venvPython -c "import sys, alignscore, bert_score, evaluate, spacy, torch; print('Ready:', torch.__version__, sys.version.split()[0])"
if ($LASTEXITCODE -ne 0) { throw "Metric import verification failed." }
Write-Host ""
Write-Host "Environment ready: $venvPython"
Write-Host "Next: .\run_evaluation.ps1 -MaxCases 5"
