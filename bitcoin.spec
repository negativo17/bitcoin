%define _hardened_build 1
%global selinux_variants mls strict targeted
%global _compldir %{_datadir}/bash-completion/completions

Name:       bitcoin
Version:    0.17.0.1
Release:    1%{?dist}
Summary:    Peer to Peer Cryptographic Currency
License:    MIT
URL:        http://bitcoin.org/

Source0:    http://github.com/%{name}/%{name}/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:    %{name}-tmpfiles.conf
Source2:    %{name}.sysconfig
Source3:    %{name}.service
Source4:    https://github.com/bitcoin-core/packaging/archive/bd5cc05d8b1a9122406a7b6aec006351a6f0e6d5.zip
Source8:    README.server.redhat
Source9:    README.utils.redhat
Source10:   README.gui.redhat

Patch0:     https://github.com/bitcoin/bitcoin/commit/a9cf5c9623ad547d9aeebea2b51c2afcfc0f3f4f.patch
Patch1:     https://patch-diff.githubusercontent.com/raw/bitcoin/bitcoin/pull/14403.patch

BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  boost-devel
BuildRequires:  checkpolicy
BuildRequires:  desktop-file-utils
BuildRequires:  java
BuildRequires:  libdb4-cxx-devel
BuildRequires:  libevent-devel
BuildRequires:  libtool
BuildRequires:  miniupnpc-devel
BuildRequires:  openssl-devel
BuildRequires:  protobuf-devel
BuildRequires:  qrencode-devel
BuildRequires:  qt5-linguist
BuildRequires:  qt5-qtbase-devel
BuildRequires:  selinux-policy-devel
BuildRequires:  selinux-policy-doc
BuildRequires:  systemd

%if 0%{?fedora}
BuildRequires:  python3
%endif
%if 0%{?rhel}
BuildRequires:  python34
%endif

# ZeroMQ not testable yet on RHEL due to lack of python3-zmq so
# enable only for Fedora
%if 0%{?fedora}
BuildRequires:  python3-zmq
BuildRequires:  zeromq-devel
%endif

%description
Bitcoin is a digital cryptographic currency that uses peer-to-peer technology to
operate with no central authority or banks; managing transactions and the
issuing of bitcoins is carried out collectively by the network.

%package core
Summary:    Peer to Peer Cryptographic Currency
Obsoletes:  %{name} < %{version}-%{release}
Provides:   %{name} = %{version}-%{release}

%description core
Bitcoin is a digital cryptographic currency that uses peer-to-peer technology to
operate with no central authority or banks; managing transactions and the
issuing of bitcoins is carried out collectively by the network.

This package contains the Qt based graphical client and node. If you are looking
to run a Bitcoin wallet, this is probably the package you want.

%package libs
Summary:    Peer-to-peer digital currency

%description libs
This package provides the bitcoinconsensus shared libraries. These libraries
may be used by third party software to provide consensus verification
functionality.

Unless you know need this package, you probably do not.

%package devel
Summary:    Peer-to-peer digital currency
Requires:   %{name}-libs%{?_isa} = %{version}-%{release}

%description devel
This package contains the header files and static library for the
bitcoinconsensus shared library. If you are developing or compiling software
that wants to link against that library, then you need this package installed.

Most people do not need this package installed.

%package utils
Summary:    Peer-to-peer digital currency

%description utils 
Bitcoin is an experimental new digital currency that enables instant payments to
anyone, anywhere in the world. Bitcoin uses peer-to-peer technology to operate
with no central authority: managing transactions and issuing money are carried
out collectively by the network.

This package provides bitcoin-cli, a utility to communicate with and
control a Bitcoin server via its RPC protocol, and bitcoin-tx, a utility
to create custom Bitcoin transactions.

%package server
Summary:            Peer-to-peer digital currency
Requires(pre):      shadow-utils
Requires(post):     /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles
Requires(postun):   /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles
Requires:           selinux-policy
Requires:           policycoreutils-python
Requires:           %{name}-utils%{_isa} = %{version}

%description server
This package provides a stand-alone bitcoin-core daemon. For most users, this
package is only needed if they need a full-node without the graphical client.

Some third party wallet software will want this package to provide the actual
bitcoin-core node they use to connect to the network.

If you use the graphical bitcoin-core client then you almost certainly do not
need this package.

%prep
%autosetup -a 4 -p1
mv packaging-*/rpm contrib/
mv packaging-*/debian/* contrib/debian/

# Install README files
cp -p %{SOURCE8} %{SOURCE9} %{SOURCE10} .

# Prepare sample configuration as example
mv contrib/debian/examples/%{name}.conf %{name}.conf.example

# No network tests in mock
sed -i -e '/rpc_bind.py/d' test/functional/test_runner.py

%build
autoreconf -vif
%configure \
    --disable-silent-rules \
    --enable-reduce-exports

%make_build

# Build SELinux policy
pushd contrib/rpm
for selinuxvariant in %{selinux_variants}
do
  make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile
  mv %{name}.pp %{name}.pp.${selinuxvariant}
  make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile clean
done
popd

%check
# Run all the tests
make check

test/functional/test_runner.py --extended

%install
%make_install

# TODO: Upstream puts bitcoind in the wrong directory. Need to fix the
# upstream Makefiles to install it in the correct place.
mkdir -p -m 755 %{buildroot}%{_sbindir}
mv %{buildroot}%{_bindir}/bitcoind %{buildroot}%{_sbindir}/bitcoind

# Temporary files
mkdir -p %{buildroot}%{_tmpfilesdir}
install -m 0644 %{SOURCE1} %{buildroot}%{_tmpfilesdir}/%{name}.conf

# Install ancillary files
install -D -m644 -p contrib/debian/%{name}-qt.protocol %{buildroot}%{_datadir}/kde4/services/%{name}-qt.protocol
install -D -m600 -p %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/%{name}
install -D -m644 -p %{SOURCE3} %{buildroot}%{_unitdir}/%{name}.service
install -d -m750 -p %{buildroot}%{_localstatedir}/lib/%{name}
install -d -m750 -p %{buildroot}%{_sysconfdir}/%{name}

# Desktop file
desktop-file-install \
    --dir=%{buildroot}%{_datadir}/applications \
    --remove-key=Encoding \
    --set-key=Icon --set-value="%{name}" \
    contrib/debian/%{name}-qt.desktop
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}-qt.desktop

# Icons
for size in 16 32 64 128 256; do
    install -p -D -m 644 share/pixmaps/%{name}${size}.png \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png
done
rm -f %{buildroot}%{_datadir}/pixmaps/%{name}*

# Bash completion
install -D -m644 -p contrib/%{name}-cli.bash-completion %{buildroot}%{_compldir}/%{name}-cli
install -D -m644 -p contrib/bitcoind.bash-completion %{buildroot}%{_compldir}/bitcoind

# Man pages
mkdir -p %{buildroot}%{_mandir}/man1/
for i in bitcoind %{name}-cli %{name}-qt; do
    install -m644 -p doc/man/$i.1 %{buildroot}%{_mandir}/man1/
    gzip %{buildroot}%{_mandir}/man1/$i.1
done

# Remove test files so that they aren't shipped. Tests have already been run.
rm -f %{buildroot}%{_bindir}/test_*

# We don't ship bench_bitcoin right now
rm -f %{buildroot}%{_bindir}/bench_%{name}

# Install SELinux policy
for selinuxvariant in %{selinux_variants}
do
    install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
    install -p -m 644 contrib/rpm/%{name}.pp.${selinuxvariant} \
        %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{name}.pp
done

%pre server
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null ||
    useradd -r -g %{name} -d /var/lib/%{name} -s /sbin/nologin \
    -c "Bitcoin wallet server" %{name}
exit 0

%post core
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

%postun core
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans core
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%ldconfig_scriptlets libs

%post server
%systemd_post %{name}.service
for selinuxvariant in %{selinux_variants}
do
    /usr/sbin/semodule -s ${selinuxvariant} -i \
        %{_datadir}/selinux/${selinuxvariant}/%{name}.pp \
        &> /dev/null || :
done
# FIXME This is less than ideal, but until dwalsh gives me a better way...
/usr/sbin/semanage port -a -t %{name}_port_t -p tcp 8332 2> /dev/null
/usr/sbin/semanage port -a -t %{name}_port_t -p tcp 8333 2> /dev/null
/usr/sbin/semanage port -a -t %{name}_port_t -p tcp 18332 2> /dev/null
/usr/sbin/semanage port -a -t %{name}_port_t -p tcp 18333 2> /dev/null
/sbin/fixfiles -R %{name}-server restore &> /dev/null || :
/sbin/restorecon -R %{_localstatedir}/lib/%{name} || :

%posttrans server
/usr/bin/systemd-tmpfiles --create

%preun server
%systemd_preun %{name}.service

%postun server
%systemd_postun_with_restart %{name}.service
if [ $1 -eq 0 ] ; then
    # FIXME This is less than ideal, but until dwalsh gives me a better way...
    /usr/sbin/semanage port -d -p tcp 8332
    /usr/sbin/semanage port -d -p tcp 8333
    /usr/sbin/semanage port -d -p tcp 18332
    /usr/sbin/semanage port -d -p tcp 18333
    for selinuxvariant in %{selinux_variants}
    do
        /usr/sbin/semodule -s ${selinuxvariant} -r %{name} \
        &> /dev/null || :
    done
    /sbin/fixfiles -R %{name}-server restore &> /dev/null || :
    [ -d %{_localstatedir}/lib/%{name} ] && \
        /sbin/restorecon -R %{_localstatedir}/lib/%{name} \
        &> /dev/null || :
fi

%files core
%license COPYING
%doc README.md README.gui.redhat %{name}.conf.example
%doc doc/assets-attribution.md doc/bips.md doc/files.md doc/reduce-traffic.md doc/release-notes.md doc/tor.md
%{_bindir}/%{name}-qt
%{_datadir}/applications/%{name}-qt.desktop
%{_datadir}/kde4/services/%{name}-qt.protocol
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_mandir}/man1/%{name}-qt.1*

%files libs
%license COPYING
%doc doc/README.md
%{_libdir}/libbitcoinconsensus.so.*

%files devel
%doc doc/README.md doc/developer-notes.md doc/shared-libraries.md
%{_includedir}/bitcoinconsensus.h
%{_libdir}/libbitcoinconsensus.a
%{_libdir}/libbitcoinconsensus.la
%{_libdir}/libbitcoinconsensus.so
%{_libdir}/pkgconfig/libbitcoinconsensus.pc

%files utils
%license COPYING
%doc README.utils.redhat %{name}.conf.example
%doc doc/README.md
%{_bindir}/%{name}-cli
%{_bindir}/%{name}-tx
%{_compldir}/%{name}-cli
%{_mandir}/man1/%{name}-cli.1*
%{_mandir}/man1/%{name}-tx.1*

%files server
%license COPYING
%doc %{name}.conf.example README.server.redhat doc/README.md doc/REST-interface.md doc/bips.md doc/dnsseed-policy.md doc/files.md doc/reduce-traffic.md doc/release-notes.md doc/tor.md doc/zmq.md
%dir %attr(750,%{name},%{name}) %{_localstatedir}/lib/%{name}
%dir %attr(750,%{name},%{name}) %{_sysconfdir}/%{name}
%ghost %dir /run/%{name}/
%ghost /run/%{name}.pid
%config(noreplace) %attr(644,root,root) %{_sysconfdir}/sysconfig/%{name}
%{_compldir}/bitcoind
%{_datadir}/selinux/*/%{name}.pp
%{_mandir}/man1/bitcoind.1*
%{_sbindir}/bitcoind
%{_tmpfilesdir}/%{name}.conf
%{_unitdir}/%{name}.service

%changelog
* Sat Nov 10 2018 Simone Caronni <negativo17@gmail.com> - 0.17.0.1-1
- Update to 0.17.0.1.

* Thu Oct 04 2018 Simone Caronni <negativo17@gmail.com> - 0.17.0-1
- Update to 0.17.0.
- Add packaging files which are not in the packaging repository.

* Wed Sep 26 2018 Simone Caronni <negativo17@gmail.com> - 0.16.3-1
- Update to 0.16.3.

* Fri Jul 27 2018 Simone Caronni <negativo17@gmail.com> - 0.16.2-1
- Update to 0.16.2.

* Thu Jun 14 2018 Simone Caronni <negativo17@gmail.com> - 0.16.1-1
- Update to 0.16.1.
- Update SPEC file.

* Tue Feb 27 2018 Simone Caronni <negativo17@gmail.com> - 0.16.0-1
- Update to 0.16.0.

* Fri Feb 16 2018 Simone Caronni <negativo17@gmail.com> - 0.16.0rc4-1
- Update to 0.16.0rc4.

* Fri Nov 10 2017 Simone Caronni <negativo17@gmail.com> - 0.15.1-1
- Update to 0.15.1.

* Thu Oct 05 2017 Simone Caronni <negativo17@gmail.com> - 0.15.0.1-1
- Update to 0.15.0.1.

* Mon Sep 25 2017 Simone Caronni <negativo17@gmail.com> - 0.15.0-2
- Do not fork in systemd unit.

* Mon Sep 11 2017 Simone Caronni <negativo17@gmail.com> - 0.15.0-1
- Update to 0.15.0.

* Sun Jul 23 2017 Simone Caronni <negativo17@gmail.com> - 0.14.2-3
- Clean up SPEC file. Re-add license to all other subpackages that can be
  installed independently.
- Update temporary files part as per packaging guidelines.
- Update installation of desktop files and icons.
- Update build options.

* Wed Jul 12 2017 Simone Caronni <negativo17@gmail.com> - 0.14.2-2
- Update to segwit 1.0 release. Drop patch and use official tag as it contains a
  lot of 0.14.3 backports. Use tag and not tarball as they dropped most of the
  contrib folder from it.
- Add bash completion files.

* Sat Jun 17 2017 Simone Caronni <negativo17@gmail.com> - 0.14.2-1
- Update to 0.14.2, use official sources + UASF patch.
- Remove obsolete RPM tags.
- Leave license only on libs subpackage.
- Skip RPC tests, they do not run in mock.

* Tue May 23 2017 Simone Caronni <negativo17@gmail.com> - 0.14.1-3
- Switch to UASF sources.

* Sun May 21 2017 Michael Hampton <bitcoin@ringingliberty.com> 0.14.1-2
- Add explicit python 2 dependency for F26+

* Sat Apr 22 2017 Michael Hampton <bitcoin@ringingliberty.com> 0.14.1-1
- Update to upstream 0.14.1

* Wed Mar  8 2017 Michael Hampton <bitcoin@ringingliberty.com> 0.14.0-1
- Update to upstream 0.14.0
- Remove outdated docs and update manpages location
- On advice of upstream, don't run broken extended tests

* Tue Jan  3 2017 Michael Hampton <bitcoin@ringingliberty.com> 0.13.2-1
- Update to upstream 0.13.2

* Sat Oct 29 2016 Michael Hampton <bitcoin@ringingliberty.com> 0.13.1-1
- Update to upstream 0.13.1

* Wed Aug 24 2016 Michael Hampton <bitcoin@ringingliberty.com> 0.13.0-1
- Update to upstream 0.13.0
- Enable zeromq support

* Wed Jul 27 2016 Michael Hampton <bitcoin@ringingliberty.com> 0.13.0-0.1.rc1
- Incorporate text copy and some style changes from new upstream RPM spec file
- Rename GUI package from bitcoin to bitcoin-core per upstream
- Ship new upstream docs

* Mon Jul 11 2016 Michael Hampton <bitcoin@ringingliberty.com> 0.12.1-2
- Rebuild against EPEL miniupnpc

* Wed Feb 24 2016 Michael Hampton <bitcoin@ringingliberty.com> 0.12.0-1
- Update to upstream 0.12.0
- No longer Requires: openssl-compat-bitcoin-libs, but still BuildRequires:
  to run the testsuite on RHEL7

* Sun Jan 17 2016 Michael Hampton <bitcoin@ringingliberty.com> 0.11.2-2
- Conflict with bitcoinclassic

* Thu Oct 15 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.11.1-1
- Update to upstream 0.11.1

* Wed Sep 16 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.11.0-4
- Don't enable profiling

* Thu Aug 27 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.11.0-3
- Conflict with Bitcoin XT

* Fri Aug 21 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.11.0-2
- Removed EL6 and Fedora < 21 support
- Ensure that /etc/sysconfig/bitcoin is properly marked as a config file
- Build with system openssl on Fedora, as BZ#1021898 is resolved

* Mon Jul 27 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.11.0-1
- Update to upstream 0.11.0

* Sat May 23 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.10.2-1
- Update to upstream 0.10.2

* Thu Apr 30 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.10.1-3
- Updated SELinux policy for bitcoind PID file
- Updated systemd service and tmpfiles configuration
- Install license in new location on Fedora

* Wed Apr 29 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.10.1-2
- Ensure the daemon can write its PID file on systemd systems
- Skip tests on armhfp as testsuite does not run in a chroot
  reported upstream https://github.com/bitcoin/bitcoin/issues/5795

* Tue Apr 28 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.10.1-1
- Update to upstream 0.10.1

* Fri Feb 27 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.10.0-2
- Fixes for issue #5 reported by @kaipila:
  Provide a RuntimeDirectory to store the bitcoin pid file on systemd systems
  Fix variable quoting in bitcoin.service on systemd systems

* Sat Feb 14 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.10.0-1
- Update to upstream 0.10.0

* Sun Jan 11 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.10.0-0.2.rc1
- Add upstream patch to prevent blockchain forks on new versions of OpenSSL
- Don't patch bitcoin for configuration paths; set them in the init scripts
  This allows us to run the test suite, which chokes on the changed paths
- Run the bitcoin test suite at RPM build time

* Fri Jan 09 2015 Michael Hampton <bitcoin@ringingliberty.com> 0.10.0-0.1.rc1
- Update to upstream 0.10.0rc1
- Revised README.utils.redhat to address bitcoin-tx command
- Renamed bitcoin-cli subpackage to bitcoin-utils
- Revised systemd unit with some upstream changes
- Create new bitcoin-libs and bitcoin-devel packages for libbitcoinconsensus
- Added /etc/sysconfig/bitcoin for user-provided options

* Sat Sep 27 2014 Michael Hampton <bitcoin@ringingliberty.com> 0.9.3-1
- Update to upstream 0.9.3

* Sun Jul 20 2014 Michael Hampton <bitcoin@ringingliberty.com> 0.9.2.1-3
- Workaround for upstream issue with GUI crashing when trying to create
- datadir in wrong diretcory

* Sat Jul 19 2014 Michael Hampton <bitcoin@ringingliberty.com> 0.9.2.1-2
- Fixed error which caused Bitcoin GUI to propose wrong data directory

* Thu Jun 19 2014 Michael Hampton <bitcoin@ringingliberty.com> 0.9.2.1-1
- Update to upstream 0.9.2.1.
- Add port 18332 to SELinux managed ports; allows RPC on testnet

* Tue Jun 17 2014 Michael Hampton <bitcoin@ringingliberty.com> 0.9.2-1
- Update to upstream 0.9.2.

* Tue Jun 10 2014 Michael Hampton <bitcoin@ringingliberty.com> 0.9.1-2
- Fix a logic error when installing bitcoin service on RHEL 7 or Fedora 21+

* Wed Apr 9 2014 Michael Hampton <bitcoin@ringingliberty.com> 0.9.1-1
- Update to upstream 0.9.1. This release doesn't actually make any
  changes in the code; upstream released it solely because they
  bundle OpenSSL with their shipped binaries.
- We now use a single spec file for RHEL and Fedora.

* Thu Mar 27 2014 Michael Hampton <bitcoin@ringingliberty.com> 0.9.0-3
- Fix typo causing a nonexistent dependency to be pulled, fixes #11

* Sat Mar 22 2014 Michael Hampton <bitcoin@ringingliberty.com> 0.9.0-2
- Fix default paths for Bitcoin GUI
- Added README.redhat file

* Thu Mar 20 2014 Michael Hampton <bitcoin@ringingliberty.com> 0.9.0-1
- Update for Bitcoin 0.9.0.
- Combine RHEL and Fedora specs into a single spec file.
- Initial changes to support upcoming RHEL 7.

* Mon Dec 9 2013 Michael Hampton <bitcoin@ringingliberty.com> 0.8.6-1
- Update for Bitcoin 0.8.6.

* Wed Oct 16 2013 Michael Hampton <bitcoin@ringingliberty.com> 0.8.5-2
- Remove bitcoind and bitcoin-qt launcher scripts no longer used upstream
- Ship upstream example config file

* Sat Oct 05 2013 Michael Hampton <bitcoin@ringingliberty.com> 0.8.5-1
- Update for Bitcoin 0.8.5.

* Wed Sep 04 2013 Michael Hampton <bitcoin@ringingliberty.com> 0.8.4-1
- Update for Bitcoin 0.8.4.
- Use default SELinux context for /etc/bitcoin directory itself;
  fixes SELinux denial against updatedb.

* Fri Jul 05 2013 Michael Hampton <bitcoin@ringingliberty.com> 0.8.3-1
- Update for Bitcoin 0.8.3.

* Sun Jun 02 2013 Michael Hampton <bitcoin@ringingliberty.com> 0.8.2-1
- Update for Bitcoin 0.8.2.

* Fri Mar 29 2013 Michael Hampton <bitcoin@ringingliberty.com> 0.8.1-3
- Added missing openssl and boost Requires for bitcoin-server

* Sun Mar 24 2013 Michael Hampton <bitcoin@ringingliberty.com> 0.8.1-2
- Added missing SELinux dependencies
- Updated for RHEL: Now build against a private copy of Boost

* Thu Mar 21 2013 Michael Hampton <bitcoin@ringingliberty.com> 0.8.1-1
- Update for Bitcoin 0.8.1.
- Removed Patch2 (qt 4.6 compatibility) as it has been accepted upstream

* Tue Jan 29 2013 Michael Hampton <bitcoin@ringingliberty.com> 0.7.2-3
- Mass rebuild for corrected package signing key

* Mon Dec 17 2012 Michael Hampton <bitcoin@ringingliberty.com> 0.7.2-1
- Update for Bitcoin 0.7.2.
- Update for separate OpenSSL package openssl-compat-bitcoin.

* Wed Aug 22 2012 Michael Hampton <bitcoin@ringingliberty.com> 0.6.3-1
- Initial package.
