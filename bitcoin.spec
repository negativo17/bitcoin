%define _hardened_build 1
%global selinux_variants mls strict targeted
%global _compldir %{_datadir}/bash-completion/completions

Name:       bitcoin
Version:    0.20.0
Release:    1%{?dist}
Summary:    Peer to Peer Cryptographic Currency
License:    MIT
URL:        http://bitcoin.org/

Source0:    http://github.com/%{name}/%{name}/archive/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:    %{name}-tmpfiles.conf
Source2:    %{name}.sysconfig
Source3:    %{name}.service
Source4:    https://github.com/bitcoin-core/packaging/archive/a48094dca1113fb6096768993d1b80d1a4ab5871.zip
Source5:    %{name}.te
Source6:    %{name}.fc
Source7:    %{name}.if
Source8:    README.server.redhat
Source9:    README.utils.redhat
Source10:   README.gui.redhat

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
BuildRequires:  procps-ng
BuildRequires:  python3
BuildRequires:  qrencode-devel
BuildRequires:  qt5-linguist
BuildRequires:  qt5-qtbase-devel
BuildRequires:  selinux-policy-devel
BuildRequires:  selinux-policy-doc
BuildRequires:  systemd
BuildRequires:  zeromq-devel

%if 0%{?rhel} == 7
BuildRequires:  python36-zmq
BuildRequires:  devtoolset-7-gcc-c++
BuildRequires:  devtoolset-7-libatomic-devel
%else
BuildRequires:  python3-zmq
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
Requires(post):     policycoreutils
Requires(postun):   policycoreutils
Requires:           selinux-policy
%if 0%{?rhel} == 7
Requires:           policycoreutils-python
%else
Requires:           python3-policycoreutils
%endif
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
mv packaging-*/debian/* contrib/debian/

# SELinux policy
cp -p %{SOURCE5} %{SOURCE6} %{SOURCE7} .

# Install README files
cp -p %{SOURCE8} %{SOURCE9} %{SOURCE10} .

# Prepare sample configuration as example
mv contrib/debian/examples/%{name}.conf %{name}.conf.example

# No network tests in mock
sed -i -e '/rpc_bind.py/d' test/functional/test_runner.py

%build
%if 0%{?rhel} == 7
. /opt/rh/devtoolset-7/enable
%endif

autoreconf -vif
%configure \
    --disable-silent-rules \
    --enable-reduce-exports

%make_build

# Build SELinux policy
for selinuxvariant in %{selinux_variants}
do
  make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile
  mv %{name}.pp %{name}.pp.${selinuxvariant}
  make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile clean
done

%if 0%{?fedora}

%check
# Run all the tests
export LC_ALL=C.UTF-8
make check

test/functional/test_runner.py --extended

%endif

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

# Server log directory
mkdir -p %{buildroot}%{_var}/log/%{name}/

# Remove test files so that they aren't shipped. Tests have already been run.
rm -f %{buildroot}%{_bindir}/test_*

# We don't ship bench_bitcoin right now
rm -f %{buildroot}%{_bindir}/bench_%{name}

# Install SELinux policy
for selinuxvariant in %{selinux_variants}
do
    install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
    install -p -m 644 %{name}.pp.${selinuxvariant} \
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
%dir %attr(750,%{name},%{name}) %{_var}/log/%{name}
%ghost %{_var}/log/%{name}/debug.log
%ghost %dir /run/%{name}/
%ghost /run/%{name}.pid
%config(noreplace) %attr(644,root,root) %{_sysconfdir}/sysconfig/%{name}
%{_bindir}/bitcoin-wallet
%{_compldir}/bitcoind
%{_datadir}/selinux/*/%{name}.pp
%{_mandir}/man1/bitcoind.1*
%{_mandir}/man1/bitcoin-wallet.1*
%{_sbindir}/bitcoind
%{_tmpfilesdir}/%{name}.conf
%{_unitdir}/%{name}.service

%changelog
* Fri Jun 26 2020 Simone Caronni <negativo17@gmail.com> - 0.20.0-1
- Update to 0.20.0.

* Mon May 04 2020 Simone Caronni <negativo17@gmail.com> - 0.19.1-1
- Update to 0.19.1.
- Fix deprecation message with Python tests.
- Trim changelog.

* Fri Feb 21 2020 Simone Caronni <negativo17@gmail.com> - 0.19.0.1-2
- Fix dependencies with Python SELinux interfaces.

* Tue Nov 19 2019 Simone Caronni <negativo17@gmail.com> - 0.19.0.1-1
- Update to 0.19.0.1.

* Sun Nov 17 2019 Simone Caronni <negativo17@gmail.com> - 0.19.0-1
- Update to 0.19.0.

* Thu Sep 12 2019 Simone Caronni <negativo17@gmail.com> - 0.18.1-1
- Update to 0.18.1.

* Tue May 07 2019 Simone Caronni <negativo17@gmail.com> - 0.18.0-2
- Update systemd unit.

* Mon May 06 2019 Simone Caronni <negativo17@gmail.com> - 0.18.0-1
- Update to 0.18.0.
- Force C.UTF-8 for tests on Fedora and disable EPEL 7 test run.

* Thu Jan 24 2019 Simone Caronni <negativo17@gmail.com> - 0.17.1-1
- Update to 0.17.1.

* Sat Dec 08 2018 Simone Caronni <negativo17@gmail.com> - 0.17.0.1-3
- Fix typo.

* Thu Dec 06 2018 Simone Caronni <negativo17@gmail.com> - 0.17.0.1-2
- Separate log file from working directory.

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
