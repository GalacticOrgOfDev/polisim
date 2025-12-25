# PowerShell script to build Sphinx documentation on Windows
# Usage: .\make.ps1 html

param(
    [string]$Target = "help"
)

$SPHINXBUILD = "sphinx-build"
$SOURCEDIR = "source"
$BUILDDIR = "build"

if ($Target -eq "help") {
    Write-Host "Please use one of the following targets:"
    Write-Host "  html       to make standalone HTML files"
    Write-Host "  dirhtml    to make HTML files named index.html in directories"
    Write-Host "  singlehtml to make a single large HTML file"
    Write-Host "  clean      to remove build directory"
    exit 0
}

if ($Target -eq "clean") {
    if (Test-Path $BUILDDIR) {
        Remove-Item -Recurse -Force $BUILDDIR
        Write-Host "Build directory cleaned."
    }
    exit 0
}

# Build the documentation
& $SPHINXBUILD -M $Target $SOURCEDIR $BUILDDIR
