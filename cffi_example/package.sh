# Set current directory to PWD
current_dir=$PWD
# Create source distribution package
python setup.py sdist
# Set package name
name=daslic
version=1.0
package=${name}-${version}
# Extract package contents
tar zxvf dist/${package}.tar.gz
# Create build directory
mkdir -p dist/${package}/build/
# Change directory to build directory
cd dist/${package}/build/
# Get python major and minor version command line, like 3.10
python_version=$(python -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')

# Write a loop, arch should be aarch64, mips64el, x86_64
for arch in aarch64 mips64el x86_64; do
    # Set folder name
    folder=lib.linux-${arch}-${python_version}
    # Print folder name
    echo $folder
    # Create folder
    mkdir -p $folder
    # Change directory to folder
    cd $folder
    # Remove existing libdasapi.so
    rm libdasapi.so
    # Create symbolic link to libdasapi.so
    echo "Create symbolic link to libdasapi.so------------"
    ln -s ../../daslic/${arch}/libdasapi.so libdasapi.so
    echo "List contents of libdasapi.so-------------------"
    # List contents of libdasapi.so
    ls -l libdasapi.so
    # Change directory to build directory
    cd ../
done

# Change directory to dist
cd $current_dir/dist
# Create compressed package
tar zcvf ${package}.tar.gz ${package}
pip uninstall -y ${name}
pip install ${package}.tar.gz
