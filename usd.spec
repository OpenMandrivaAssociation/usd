%define libname %mklibname usd
%define devname %mklibname -d usd

Summary:	Universal Scene Description (OpenUSD)
Name:		usd
Version:	26.03
Release:	2
Group:		Graphics
License:	TOST-1.0
URL:		https://openusd.org/
Source0:	https://github.com/PixarAnimationStudios/OpenUSD/archive/v%{version}/OpenUSD-%{version}.tar.gz

BuildSystem:	cmake
BuildOption:	-DBUILD_SHARED_LIBS:BOOL=ON
BuildOption:	-DPXR_BUILD_MONOLITHIC:BOOL=ON
BuildOption:	-DPXR_BUILD_IMAGING:BOOL=ON
BuildOption:	-DPXR_BUILD_USD_IMAGING:BOOL=ON
BuildOption:	-DPXR_BUILD_USD_TOOLS:BOOL=ON
BuildOption:	-DPXR_BUILD_EXAMPLES:BOOL=OFF
BuildOption:	-DPXR_BUILD_TUTORIALS:BOOL=OFF
BuildOption:	-DPXR_BUILD_TESTS:BOOL=OFF
BuildOption:	-DPXR_BUILD_USDVIEW:BOOL=OFF
BuildOption:	-DPXR_BUILD_HTML_DOCUMENTATION:BOOL=OFF
BuildOption:	-DPXR_BUILD_PYTHON_DOCUMENTATION:BOOL=OFF
BuildOption:	-DPXR_BUILD_ALEMBIC_PLUGIN:BOOL=OFF
BuildOption:	-DPXR_BUILD_DRACO_PLUGIN:BOOL=OFF
BuildOption:	-DPXR_BUILD_EMBREE_PLUGIN:BOOL=OFF
BuildOption:	-DPXR_BUILD_PRMAN_PLUGIN:BOOL=OFF
BuildOption:	-DPXR_BUILD_OPENIMAGEIO_PLUGIN:BOOL=ON
BuildOption:	-DPXR_BUILD_OPENCOLORIO_PLUGIN:BOOL=ON
BuildOption:	-DPXR_ENABLE_MATERIALX_SUPPORT:BOOL=ON
BuildOption:	-DPXR_ENABLE_OPENVDB_SUPPORT:BOOL=OFF
BuildOption:	-DPXR_ENABLE_OSL_SUPPORT:BOOL=OFF
BuildOption:	-DPXR_ENABLE_PTEX_SUPPORT:BOOL=OFF
BuildOption:	-DPXR_ENABLE_HDF5_SUPPORT:BOOL=OFF
BuildOption:	-DPXR_ENABLE_PYTHON_SUPPORT:BOOL=ON
BuildOption:	-DPXR_ENABLE_MALLOCHOOK_SUPPORT:BOOL=OFF
BuildOption:	-DPXR_VALIDATE_GENERATED_CODE:BOOL=OFF
BuildOption:	-DPYTHON_EXECUTABLE=/usr/bin/python
BuildOption:	-DPython3_EXECUTABLE=/usr/bin/python
BuildOption:	-DPXR_ENABLE_GL_SUPPORT:BOOL=ON
BuildOption:	-DCMAKE_CXX_STANDARD=17

BuildRequires:	pkgconfig(tbb)
BuildRequires:	cmake(OpenSubdiv)
BuildRequires:	cmake(OpenImageIO)
BuildRequires:	cmake(OpenColorIO)
BuildRequires:	cmake(MaterialX)
BuildRequires:	materialx-data
BuildRequires:	python-materialx
BuildRequires:	cmake(Imath)
BuildRequires:	pkgconfig(python)
BuildRequires:	pkgconfig(gl)
BuildRequires:	pkgconfig(x11)
# OpenSubdiv's GPU lib is built with OpenCL; ninja needs the .so at link time.
BuildRequires:	pkgconfig(OpenCL)
# pxr/base/arch/stackTrace.cpp includes <unwind.h> (LLVM libunwind, not nongnu).
BuildRequires:	pkgconfig(libunwind-llvm)
BuildRequires:	python%{pyver}dist(jinja2)

Requires:	%{libname} = %{EVRD}
# Most CLI tools are Python scripts that import pxr.
Requires:	%{name}-python = %{EVRD}

%description
Universal Scene Description (OpenUSD) is Pixar's time-sampled scene
description for interchange between graphics applications. Hydra is the
imaging framework shipped in the same tree. Blender uses this for USD
import/export and Hydra 2.0.

This build is the 26.03 release Blender 5.2 LTS was developed against,
as a shared monolithic library (libusd_ms) so Blender's FindUSD module
can locate it.

%package -n %{libname}
Summary:	Shared OpenUSD/Hydra library
Group:		System/Libraries

%description -n %{libname}
The shared monolithic OpenUSD library (libusd_ms) including Hydra.

%package -n %{devname}
Summary:	Development files for OpenUSD
Group:		Development/C++
Requires:	%{libname} = %{EVRD}
Requires:	pkgconfig(tbb)
Requires:	cmake(OpenSubdiv)
Provides:	%{name}-devel = %{EVRD}
Provides:	OpenUSD-devel = %{EVRD}

%description -n %{devname}
Headers and CMake config (pxrConfig) for developing applications that
use OpenUSD and Hydra.

%package python
Summary:	Python bindings for OpenUSD
Group:		Development/Python
Requires:	%{libname} = %{EVRD}

%description python
The pxr Python modules for OpenUSD.

%install -a
# OpenUSD hardcodes DESTINATION lib/ (not lib64). Move the 64-bit
# library and its sibling plugin tree so ld.so can find libusd_ms.so
# and PXR_BUILD_LOCATION=usd still resolves next to it.
if [ "%{_libdir}" != "%{_prefix}/lib" ]; then
	mkdir -p %{buildroot}%{_libdir}
	mv %{buildroot}%{_prefix}/lib/libusd_ms.so %{buildroot}%{_libdir}/
	mv %{buildroot}%{_prefix}/lib/usd %{buildroot}%{_libdir}/
fi
# OpenUSD hardcodes lib/python/pxr (not the distro site-packages).
mkdir -p %{buildroot}%{python_sitelib}
echo '%{_prefix}/lib/python' > %{buildroot}%{python_sitelib}/usd.pth
# CMake config lands in /usr/pxrConfig.cmake + /usr/cmake/; relocate
# so find_package(pxr) works, then fix the generated prefix walks.
mkdir -p %{buildroot}%{_libdir}/cmake/pxr
mv %{buildroot}%{_prefix}/pxrConfig.cmake %{buildroot}%{_libdir}/cmake/pxr/
mv %{buildroot}%{_prefix}/cmake/pxrTargets*.cmake %{buildroot}%{_libdir}/cmake/pxr/
rmdir %{buildroot}%{_prefix}/cmake
python - <<'PY'
from pathlib import Path
root = Path(r"%{buildroot}%{_libdir}/cmake/pxr")
cfg = root / "pxrConfig.cmake"
t = cfg.read_text()
t = t.replace(
	'include("${PXR_CMAKE_DIR}/cmake/pxrTargets.cmake")',
	'include("${PXR_CMAKE_DIR}/pxrTargets.cmake")',
)
t = t.replace(
	'set(PXR_INCLUDE_DIRS "${PXR_CMAKE_DIR}/include")',
	'get_filename_component(PXR_INCLUDE_DIRS "${PXR_CMAKE_DIR}/../../../include" ABSOLUTE)',
)
cfg.write_text(t)
tgt = root / "pxrTargets.cmake"
t = tgt.read_text()
old = '''get_filename_component(_IMPORT_PREFIX "${CMAKE_CURRENT_LIST_FILE}" PATH)
get_filename_component(_IMPORT_PREFIX "${_IMPORT_PREFIX}" PATH)
if(_IMPORT_PREFIX STREQUAL "/")'''
new = '''get_filename_component(_IMPORT_PREFIX "${CMAKE_CURRENT_LIST_FILE}" PATH)
get_filename_component(_IMPORT_PREFIX "${_IMPORT_PREFIX}" PATH)
get_filename_component(_IMPORT_PREFIX "${_IMPORT_PREFIX}" PATH)
get_filename_component(_IMPORT_PREFIX "${_IMPORT_PREFIX}" PATH)
if(_IMPORT_PREFIX STREQUAL "/")'''
if old not in t:
	raise SystemExit("pxrTargets.cmake prefix-walk block not found")
tgt.write_text(t.replace(old, new, 1))
lib = "%{_lib}"
for p in root.glob("pxrTargets-*.cmake"):
	p.write_text(p.read_text().replace(
		"${_IMPORT_PREFIX}/lib/libusd_ms.so",
		"${_IMPORT_PREFIX}/%s/libusd_ms.so" % lib,
	))
PY

%pgo
# Tools abort in the uninstalled tree (ArDefaultResolver plugInfo).
# Stage an install so PXR_BUILD_LOCATION / ../plugin/usd resolve.
_b=_OMV_rpm_build
dest="$PWD/pgo-root"
DESTDIR="$dest" cmake --install "$_b"
export LD_LIBRARY_PATH="$dest%{_prefix}/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PXR_PLUGINPATH_NAME="$dest%{_prefix}/lib/usd:$dest%{_prefix}/plugin/usd"
cat > pgo-scene.usda <<'EOF'
#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Y"
    startTimeCode = 1
    endTimeCode = 24
)
def Xform "World" {
    def Sphere "sphere" {
        double radius = 2
        float3 xformOp:translate = (0, 1, 0)
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }
    def Cube "cube" {
        double size = 1
        float3 xformOp:translate = (3, 0, 0)
        uniform token[] xformOpOrder = ["xformOp:translate"]
    }
    def Mesh "mesh" {
        int[] faceVertexCounts = [4]
        int[] faceVertexIndices = [0, 1, 2, 3]
        point3f[] points = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        normal3f[] normals = [(0, 0, 1), (0, 0, 1), (0, 0, 1), (0, 0, 1)]
        texCoord2f[] primvars:st = [(0, 0), (1, 0), (1, 1), (0, 1)] (
            interpolation = "vertex"
        )
    }
}
EOF
"$dest%{_bindir}/usdcat" pgo-scene.usda >/dev/null
"$dest%{_bindir}/usdcat" -o pgo-scene.usdc pgo-scene.usda
"$dest%{_bindir}/usdcat" pgo-scene.usdc >/dev/null
"$dest%{_bindir}/usdtree" -a pgo-scene.usda >/dev/null
"$dest%{_bindir}/usdchecker" pgo-scene.usda
"$dest%{_bindir}/sdfdump" pgo-scene.usda >/dev/null
"$dest%{_bindir}/sdffilter" pgo-scene.usda >/dev/null

%files -n %{libname}
%license LICENSE.txt
%doc README.md NOTICE.txt
# Unversioned soname; extra Hydra/Hio plugins stay at /usr/plugin/usd
# (PXR_PLUGIN_BUILD_LOCATION=../plugin/usd relative to the library).
%{_libdir}/libusd_ms.so
%{_libdir}/usd/
%{_prefix}/plugin/usd/

%files -n %{devname}
%{_includedir}/pxr/
%{_libdir}/cmake/pxr/

%files python
%{python_sitelib}/usd.pth
%{_prefix}/lib/python/pxr/

%files
%{_bindir}/usd*
%{_bindir}/sdf*
%{_bindir}/hd*
