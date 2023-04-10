## probolem

[pip download just the source packages without build, metadata etc](https://discuss.python.org/t/pip-download-just-the-source-packages-no-building-no-metadata-etc/4651)

+ The user wants to download only the source for a package without its dependencies, but the current implementation of pip requires building the package even with the --no-deps and --no-build-isolation flags.
+ The reason for this is that pip needs to verify the metadata of the package for data integrity, and building the package is the only way to do so with the current state of sdist metadata.
+ A possible solution is to standardize the sdist format, or to use the new resolver feature in pip which may avoid the build step.

The user is trying to download the source code for the pandas package without its dependencies, but is still encountering a long process of building wheel data. There is discussion among other users about the reasons for this, including the need for metadata integrity checks and the lack of standardization for sdist filenames. Suggestions are made for possible solutions, such as using the new resolver or implementing a --no-integrity-check option for source downloads.

## solution

This amazing script facilitates the download of specified packages along with their dependencies. In case a pure python wheel package is not available, it would also download the source package.
这个惊人的脚本有助于下载指定的包及其依赖项。 如果没有纯 python wheel 包，它也会下载源码包。

install unearth

```bash
pip install unearth
```