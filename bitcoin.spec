%define _hardened_build 1
%global selinux_variants mls strict targeted
%global _compldir %{_datadir}/bash-completion/completions

# Comment to use official
%global segwit uasfsegwit1.0

Name:       bitcoin
Version:    0.14.2
Release:    2%{?dist}
Summary:    Peer to Peer Cryptographic Currency
License:    MIT
URL:        http://bitcoin.org/

Source0:    http://github.com/%{?segwit:UASF}%{!?segwit:bitcoin}/%{name}/archive/v%{version}%{?segwit:-%{segwit}}.tar.gz#/%{name}-%{version}%{?segwit:-%{segwit}}.tar.gz
Source1:    bitcoind.tmpfiles
Source2:    bitcoin.sysconfig
Source3:    bitcoin.service
Source4:    bitcoin.init
Source5:    bitcoin.te
Source6:    bitcoin.fc
Source7:    bitcoin.if
Source8:    README.server.redhat
Source9:    README.utils.redhat
Source10:   README.gui.redhat

Patch1: bitcoin-0.13.0-test-unicode.patch
Patch2: bitcoin-0.14.1-test-timeout.patch

# Dest change address patch for Lamassu Bitcoin machine
Patch99: bitcoin-0.14.0-destchange.patch

BuildRequires:  qt5-qtbase-devel qt5-linguist
BuildRequires:  qrencode-devel miniupnpc-devel protobuf-devel openssl-devel
BuildRequires:  desktop-file-utils autoconf automake
BuildRequires:  checkpolicy selinux-policy-devel selinux-policy-doc
BuildRequires:  boost-devel libdb4-cxx-devel libevent-devel
BuildRequires:  libtool java

# There's one last Python 2 script left in the test suite, so we still need
# both Python 2 and 3 to run all tests.
%if 0%{?fedora}
BuildRequires: python2
%endif
%if 0%{?rhel}
BuildRequires: python
%endif

# ZeroMQ not testable yet on RHEL due to lack of python3-zmq so
# enable only for Fedora
%if 0%{?fedora}
BuildRequires:  python3-zmq zeromq-devel
%endif

# Python tests still use OpenSSL for secp256k1, so we still need this to run
# the testsuite on RHEL7, until Red Hat fixes OpenSSL on RHEL7. It has already
# been fixed on Fedora. Bitcoin itself no longer needs OpenSSL for secp256k1.
%if 0%{?rhel}
BuildRequires:  openssl-compat-bitcoin-libs
BuildRequires:  python34
%endif

# python3-zmq not available on RHEL/CentOS, so don't build it yet
%if 0%{?fedora}
BuildRequires:  zeromq-devel python3-zmq
%endif

Conflicts:  bitcoinxt bitcoinclassic


%description
Bitcoin is a digital cryptographic currency that uses peer-to-peer technology to
operate with no central authority or banks; managing transactions and the
issuing of bitcoins is carried out collectively by the network.


%package core
Summary:    Peer to Peer Cryptographic Currency
Obsoletes:  %{name} < %{version}-%{release}
Provides:   %{name} = %{version}-%{release}


%package libs
Summary:    Peer-to-peer digital currency
Conflicts:  bitcoinxt-libs bitcoinclassic-libs


%package devel
Summary:    Peer-to-peer digital currency
Requires:   bitcoin-libs%{?_isa} = %{version}-%{release}
Conflicts:  bitcoinxt-devel bitcoinclassic-devel


%package utils
Summary:    Peer-to-peer digital currency
Obsoletes:  bitcoin-cli <= 0.9.3
Conflicts:  bitcoinxt-utils bitcoinclassic-utils


%package server
Summary:    Peer-to-peer digital currency
Requires(post): systemd
Requires(preun):    systemd
Requires(postun):   systemd
BuildRequires:  systemd
Requires(pre):  shadow-utils
Requires(post): /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles
Requires(postun):   /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles
Requires:   selinux-policy
Requires:   policycoreutils-python
Requires:   openssl-libs
Requires:   bitcoin-utils%{_isa} = %{version}
Conflicts:  bitcoinxt-server bitcoinclassic-server


%description core
Bitcoin is a digital cryptographic currency that uses peer-to-peer technology to
operate with no central authority or banks; managing transactions and the
issuing of bitcoins is carried out collectively by the network.

This package contains the Qt based graphical client and node. If you are looking
to run a Bitcoin wallet, this is probably the package you want.


%description libs
This package provides the bitcoinconsensus shared libraries. These libraries
may be used by third party software to provide consensus verification
functionality.

Unless you know need this package, you probably do not.


%description devel
This package contains the header files and static library for the
bitcoinconsensus shared library. If you are developing or compiling software
that wants to link against that library, then you need this package installed.

Most people do not need this package installed.


%description utils 
Bitcoin is an experimental new digital currency that enables instant
payments to anyone, anywhere in the world. Bitcoin uses peer-to-peer
technology to operate with no central authority: managing transactions
and issuing money are carried out collectively by the network.

This package provides bitcoin-cli, a utility to communicate with and
control a Bitcoin server via its RPC protocol, and bitcoin-tx, a utility
to create custom Bitcoin transactions.


%description server
This package provides a stand-alone bitcoin-core daemon. For most users, this
package is only needed if they need a full-node without the graphical client.

Some third party wallet software will want this package to provide the actual
bitcoin-core node they use to connect to the network.

If you use the graphical bitcoin-core client then you almost certainly do not
need this package.


%prep
%setup -q -n %{name}-%{version}%{?segwit:-%{segwit}}
%patch1 -p1
%patch2 -p1
%patch99 -p1

# Install README files
cp -p %{SOURCE8} %{SOURCE9} %{SOURCE10} .

# Prep SELinux policy
mkdir SELinux
cp -p %{SOURCE5} %{SOURCE6} %{SOURCE7} SELinux


%build
# Build Bitcoin
./autogen.sh
%configure --enable-reduce-exports --enable-glibc-back-compat

make %{?_smp_mflags}

# Build SELinux policy
pushd SELinux
for selinuxvariant in %{selinux_variants}
do
  make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile
  mv bitcoin.pp bitcoin.pp.${selinuxvariant}
  make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile clean
done
popd


%check
# Run all the tests
make check
# Run all the other tests
pushd src
srcdir=. test/bitcoin-util-test.py
popd
#LD_LIBRARY_PATH=/opt/openssl-compat-bitcoin/lib PYTHONUNBUFFERED=1 qa/pull-tester/rpc-tests.py


%install
cp contrib/debian/examples/bitcoin.conf bitcoin.conf.example

make INSTALL="install -p" CP="cp -p" DESTDIR=%{buildroot} install

# TODO: Upstream puts bitcoind in the wrong directory. Need to fix the
# upstream Makefiles to relocate it.
mkdir -p -m 755 %{buildroot}%{_sbindir}
mv %{buildroot}%{_bindir}/bitcoind %{buildroot}%{_sbindir}/bitcoind

# Install ancillary files
mkdir -p -m 755 %{buildroot}%{_datadir}/pixmaps
install -D -m644 -p share/pixmaps/bitcoin*.{png,xpm,ico} %{buildroot}%{_datadir}/pixmaps/
install -D -m644 -p contrib/debian/bitcoin-qt.desktop %{buildroot}%{_datadir}/applications/bitcoin-qt.desktop
desktop-file-validate %{buildroot}%{_datadir}/applications/bitcoin-qt.desktop
install -D -m644 -p contrib/debian/bitcoin-qt.protocol %{buildroot}%{_datadir}/kde4/services/bitcoin-qt.protocol
install -D -m644 -p %{SOURCE1} %{buildroot}%{_tmpfilesdir}/bitcoin.conf
install -D -m600 -p %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/bitcoin
install -D -m644 -p %{SOURCE3} %{buildroot}%{_unitdir}/bitcoin.service
install -d -m750 -p %{buildroot}%{_localstatedir}/lib/bitcoin
install -d -m750 -p %{buildroot}%{_sysconfdir}/bitcoin
install -D -m644 -p contrib/bitcoin-cli.bash-completion %{buildroot}%{_compldir}/bitcoin-cli
install -D -m644 -p contrib/bitcoind.bash-completion %{buildroot}%{_compldir}/bitcoind
install -D -m644 -p doc/man/bitcoind.1 %{buildroot}%{_mandir}/man1/bitcoind.1
install -D -m644 -p doc/man/bitcoin-cli.1 %{buildroot}%{_mandir}/man1/bitcoin-cli.1
install -D -m644 -p doc/man/bitcoin-qt.1 %{buildroot}%{_mandir}/man1/bitcoin-qt.1
gzip %{buildroot}%{_mandir}/man1/bitcoind.1
gzip %{buildroot}%{_mandir}/man1/bitcoin-cli.1
gzip %{buildroot}%{_mandir}/man1/bitcoin-qt.1

# Remove test files so that they aren't shipped. Tests have already been run.
rm -f %{buildroot}%{_bindir}/test_*

# We don't ship bench_bitcoin right now
rm -f %{buildroot}%{_bindir}/bench_bitcoin

# Install SELinux policy
for selinuxvariant in %{selinux_variants}
do
    install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
    install -p -m 644 SELinux/bitcoin.pp.${selinuxvariant} \
        %{buildroot}%{_datadir}/selinux/${selinuxvariant}/bitcoin.pp
done


%clean
rm -rf %{buildroot}


%pre server
getent group bitcoin >/dev/null || groupadd -r bitcoin
getent passwd bitcoin >/dev/null ||
    useradd -r -g bitcoin -d /var/lib/bitcoin -s /sbin/nologin \
    -c "Bitcoin wallet server" bitcoin
exit 0


%post server
%systemd_post bitcoin.service
for selinuxvariant in %{selinux_variants}
do
    /usr/sbin/semodule -s ${selinuxvariant} -i \
        %{_datadir}/selinux/${selinuxvariant}/bitcoin.pp \
        &> /dev/null || :
done
# FIXME This is less than ideal, but until dwalsh gives me a better way...
/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 8332
/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 8333
/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 18332
/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 18333
/sbin/fixfiles -R bitcoin-server restore &> /dev/null || :
/sbin/restorecon -R %{_localstatedir}/lib/bitcoin || :


%posttrans server
/usr/bin/systemd-tmpfiles --create


%preun server
%systemd_preun bitcoin.service


%postun server
%systemd_postun bitcoin.service
if [ $1 -eq 0 ] ; then
    # FIXME This is less than ideal, but until dwalsh gives me a better way...
    /usr/sbin/semanage port -d -p tcp 8332
    /usr/sbin/semanage port -d -p tcp 8333
    /usr/sbin/semanage port -d -p tcp 18332
    /usr/sbin/semanage port -d -p tcp 18333
    for selinuxvariant in %{selinux_variants}
    do
        /usr/sbin/semodule -s ${selinuxvariant} -r bitcoin \
        &> /dev/null || :
    done
    /sbin/fixfiles -R bitcoin-server restore &> /dev/null || :
    [ -d %{_localstatedir}/lib/bitcoin ] && \
        /sbin/restorecon -R %{_localstatedir}/lib/bitcoin \
        &> /dev/null || :
fi


%files core
%doc README.md README.gui.redhat doc/assets-attribution.md doc/bips.md doc/files.md doc/reduce-traffic.md doc/release-notes.md doc/tor.md bitcoin.conf.example
%{_bindir}/bitcoin-qt
%{_datadir}/applications/bitcoin-qt.desktop
%{_datadir}/kde4/services/bitcoin-qt.protocol
%{_datadir}/pixmaps/*
%{_mandir}/man1/bitcoin-qt.1*


%files libs
%license COPYING
%doc doc/README.md doc/shared-libraries.md
%{_libdir}/libbitcoinconsensus.so*


%files devel
%doc doc/README.md doc/developer-notes.md doc/shared-libraries.md
%{_includedir}/bitcoinconsensus.h
%{_libdir}/libbitcoinconsensus.a
%{_libdir}/libbitcoinconsensus.la
%{_libdir}/pkgconfig/libbitcoinconsensus.pc


%files utils
%doc README.utils.redhat bitcoin.conf.example doc/README.md
%{_bindir}/bitcoin-cli
%{_bindir}/bitcoin-tx
%{_compldir}/bitcoin-cli
%{_mandir}/man1/bitcoin-cli.1*
%{_mandir}/man1/bitcoin-tx.1*


%files server
%doc bitcoin.conf.example README.server.redhat doc/README.md doc/REST-interface.md doc/bips.md doc/dnsseed-policy.md doc/files.md doc/reduce-traffic.md doc/release-notes.md doc/tor.md doc/zmq.md
%dir %attr(750,bitcoin,bitcoin) %{_localstatedir}/lib/bitcoin
%dir %attr(750,bitcoin,bitcoin) %{_sysconfdir}/bitcoin
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/sysconfig/bitcoin
%doc SELinux/*
%{_sbindir}/bitcoind
%{_unitdir}/bitcoin.service
%{_tmpfilesdir}/bitcoin.conf
%{_mandir}/man1/bitcoind.1*
%{_compldir}/bitcoind
%{_datadir}/selinux/*/bitcoin.pp


%changelog
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
