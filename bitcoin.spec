%define _hardened_build 1
%global _compldir %{_datadir}/bash-completion/completions

Name:       bitcoin
Version:    0.21.0
Release:    3%{?dist}
Summary:    Peer to Peer Cryptographic Currency
License:    MIT
URL:        https://bitcoin.org/

Source0:    https://bitcoincore.org/bin/bitcoin-core-%{version}/%{name}-%{version}.tar.gz
Source1:    %{name}-tmpfiles.conf
Source2:    %{name}.sysconfig
Source3:    %{name}.service
Source4:    %{name}-qt.desktop
Source5:    %{name}-qt.protocol

# In .gitignore, so no chance to commit to SCM:
Source6:    %{url}/bin/bitcoin-core-%{version}/SHA256SUMS.asc
# To recreate:
# export key=01EA5486DE18A882D4C2684590C8019E36C2E964
# gpg2 --keyserver hkp://keyserver.ubuntu.com --recv-keys $key
# gpg2 --export --export-options export-minimal $key > gpgkey-$key.gpg
Source7:    gpgkey-01EA5486DE18A882D4C2684590C8019E36C2E964.gpg

# Documentation
Source11:   %{name}.conf.example
Source12:   README.gui.redhat
Source13:   README.utils.redhat
Source14:   README.server.redhat

BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  checkpolicy
BuildRequires:  desktop-file-utils
BuildRequires:  gnupg2
BuildRequires:  libdb-cxx-devel
BuildRequires:  libevent-devel
BuildRequires:  libtool
BuildRequires:  miniupnpc-devel
BuildRequires:  procps-ng
BuildRequires:  python3
BuildRequires:  qrencode-devel
BuildRequires:  qt5-linguist
BuildRequires:  qt5-qtbase-devel
BuildRequires:  systemd
BuildRequires:  zeromq-devel

%if 0%{?rhel} == 7
BuildRequires:  python36-zmq
BuildRequires:  devtoolset-9-gcc-c++
BuildRequires:  devtoolset-9-libatomic-devel
%else
BuildRequires:  python3-zmq
%endif

%if 0%{?rhel}
BuildRequires:  boost169-devel
%else
BuildRequires:  boost-devel
%endif

%description
Bitcoin is a digital cryptographic currency that uses peer-to-peer technology to
operate with no central authority or banks; managing transactions and the
issuing of bitcoins is carried out collectively by the network.

%package core
Summary:    Peer to Peer Cryptographic Currency
Provides:   %{name} = %{version}-%{release}
Provides:   bundled(secp256k1) = 0.1
Provides:   bundled(univalue) = 1.1.3
Provides:   bundled(leveldb) = 1.22.0

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

Unless you know you need this package, you probably do not.

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
%if 0%{?rhel} >= 8 || 0%{?fedora}
Requires:           (%{name}-selinux if selinux-policy-%{selinuxtype})
%endif
Provides:           bundled(secp256k1) = 0.1
Provides:           bundled(univalue) = 1.1.3
Provides:           bundled(leveldb) = 1.22.0

%description server
This package provides a stand-alone bitcoin-core daemon. For most users, this
package is only needed if they need a full-node without the graphical client.

Some third party wallet software will want this package to provide the actual
bitcoin-core node they use to connect to the network.

If you use the graphical bitcoin-core client then you almost certainly do not
need this package.

%prep
# Signature verification
gpgv2 -q --keyring=%{SOURCE7} %{SOURCE6}
grep -q $(sha256sum %{SOURCE0}) %{SOURCE6}

%autosetup -p1

# Documentation (sources can not be directly reference with doc)
cp -p %{SOURCE11} %{SOURCE12} %{SOURCE13} %{SOURCE14} .

# No network tests in mock
sed -i -e '/rpc_bind.py/d' test/functional/test_runner.py

%build
%if 0%{?rhel} == 7
. /opt/rh/devtoolset-9/enable
export BOOST_CPPFLAGS="-I%{_includedir}/boost169"
%endif

autoreconf -vif
%configure \
    --disable-bench \
    --disable-silent-rules \
    --disable-static \
    --enable-reduce-exports \
    --enable-threadlocal \
    --with-incompatible-bdb \
    --with-miniupnpc \
    --with-qrencode \
    --with-utils \
    --with-libs \
    --with-daemon \
    --with-gui=qt5

%make_build

%install
%make_install

find %{buildroot} -name "*.la" -delete

# TODO: Upstream puts bitcoind in the wrong directory. Need to fix the
# upstream Makefiles to install it in the correct place.
mkdir -p -m 755 %{buildroot}%{_sbindir}
mv %{buildroot}%{_bindir}/bitcoind %{buildroot}%{_sbindir}/bitcoind

# Temporary files
mkdir -p %{buildroot}%{_tmpfilesdir}
install -m 0644 %{SOURCE1} %{buildroot}%{_tmpfilesdir}/%{name}.conf

# Install ancillary files
install -D -m600 -p %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/%{name}
install -D -m644 -p %{SOURCE3} %{buildroot}%{_unitdir}/%{name}.service
install -D -m644 -p %{SOURCE5} %{buildroot}%{_datadir}/kde4/services/%{name}-qt.protocol
install -d -m750 -p %{buildroot}%{_sharedstatedir}/%{name}
install -d -m750 -p %{buildroot}%{_sysconfdir}/%{name}

# Desktop file
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE4}

# Icons
for size in 16 32 64 128 256; do
    install -p -D -m 644 share/pixmaps/%{name}${size}.png \
        %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/%{name}.png
done
rm -f %{buildroot}%{_datadir}/pixmaps/%{name}*

# Bash completion
install -D -m644 -p contrib/%{name}-cli.bash-completion %{buildroot}%{_compldir}/%{name}-cli
install -D -m644 -p contrib/%{name}-tx.bash-completion %{buildroot}%{_compldir}/%{name}-tx
install -D -m644 -p contrib/%{name}d.bash-completion %{buildroot}%{_compldir}/%{name}d

# Server log directory
mkdir -p %{buildroot}%{_localstatedir}/log/%{name}/

# Remove test files so that they aren't shipped. Tests have already been run.
rm -f %{buildroot}%{_bindir}/test_*

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}-qt.desktop

%if 0%{?rhel} == 7
. /opt/rh/devtoolset-9/enable
%endif
export LC_ALL=en_US.UTF-8
make check
test/functional/test_runner.py --tmpdirprefix %{_tmppath} --extended

%pre server
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null ||
    useradd -r -g %{name} -d /var/lib/%{name} -s /sbin/nologin \
    -c "Bitcoin wallet server" %{name}
exit 0

%if 0%{?rhel} == 7
%post core
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

%postun core
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%posttrans core
/usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
%endif

%ldconfig_scriptlets libs

%post server
%systemd_post %{name}.service

%posttrans server
/usr/bin/systemd-tmpfiles --create

%preun server
%systemd_preun %{name}.service

%postun server
%systemd_postun_with_restart %{name}.service

%files core
%license COPYING
%doc %{name}.conf.example README.gui.redhat README.md
%doc doc/assets-attribution.md doc/bips.md doc/files.md doc/reduce-traffic.md doc/release-notes.md doc/tor.md
%{_bindir}/%{name}-qt
%{_datadir}/applications/%{name}-qt.desktop
%{_datadir}/kde4/services/%{name}-qt.protocol
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_mandir}/man1/%{name}-qt.1*

%files libs
%license COPYING
%doc doc/README.md
%{_libdir}/libbitcoinconsensus.so.0
%{_libdir}/libbitcoinconsensus.so.0.0.0

%files devel
%doc doc/README.md doc/developer-notes.md doc/shared-libraries.md
%{_includedir}/bitcoinconsensus.h
%{_libdir}/libbitcoinconsensus.so
%{_libdir}/pkgconfig/libbitcoinconsensus.pc

%files utils
%license COPYING
%doc %{name}.conf.example README.utils.redhat
%doc doc/README.md
%{_bindir}/%{name}-cli
%{_bindir}/%{name}-tx
%{_compldir}/%{name}-cli
%{_compldir}/%{name}-tx
%{_mandir}/man1/%{name}-cli.1*
%{_mandir}/man1/%{name}-tx.1*

%files server
%license COPYING
%doc %{name}.conf.example README.server.redhat
%doc doc/README.md doc/REST-interface.md doc/bips.md doc/dnsseed-policy.md doc/files.md doc/reduce-traffic.md doc/release-notes.md doc/tor.md doc/zmq.md
%dir %attr(750,%{name},%{name}) %{_sharedstatedir}/%{name}
%dir %attr(750,%{name},%{name}) %{_sysconfdir}/%{name}
%dir %attr(750,%{name},%{name}) %{_localstatedir}/log/%{name}
%ghost %{_localstatedir}/log/%{name}/debug.log
%ghost %dir %{_rundir}/%{name}/
%ghost %{_rundir}/%{name}.pid
%config(noreplace) %attr(644,root,root) %{_sysconfdir}/sysconfig/%{name}
%{_bindir}/%{name}-wallet
%{_compldir}/%{name}d
%{_mandir}/man1/%{name}d.1*
%{_mandir}/man1/%{name}-wallet.1*
%{_sbindir}/%{name}d
%{_tmpfilesdir}/%{name}.conf
%{_unitdir}/%{name}.service

%changelog
* Wed Mar 10 2021 Simone Caronni <negativo17@gmail.com> - 0.21.0-3
- Remove requirements for utils subpackage in server subpackage.
- Separate SELinux package in its own subpackage and use RPM rich booleans on
  Fedora and RHEL/CentOS 8+ to install the SELinux package if the base policy is
  installed.
- Update server README.

* Wed Jan 20 2021 Simone Caronni <negativo17@gmail.com> - 0.21.0-2
- Update to 0.21.0.
- Remove java build requirement.
- Use local folder for test output.

* Fri Jan 15 2021 Simone Caronni <negativo17@gmail.com> - 0.21.0-1
- Update to 0.21.0.

* Thu Nov 19 2020 Simone Caronni <negativo17@gmail.com> - 0.20.1-2
- Remove openssl/protobuf from build requirements.

* Wed Oct 21 2020 Simone Caronni <negativo17@gmail.com> - 0.20.1-1
- Update to 0.20.1.

* Wed Jul 22 2020 Simone Caronni <negativo17@gmail.com> - 0.20.0-7
- Use libdb 5.x instead of deprecated 4.x. Fixes build on RHEL/CentOS 8.

* Tue Jul 21 2020 Simone Caronni <negativo17@gmail.com> - 0.20.0-6
- Update systemd unit.
- Update configuration options.
- Declared bundled libraries/forks.

* Tue Jul 21 2020 Simone Caronni <negativo17@gmail.com> - 0.20.0-5
- Use HTTPS for url tag.
- Reorganize sources. Add cleaned files from the packaging repository directly;
  bash completion snippets are now supported in the main sources.
- Move check section after install and include desktop file validating in there.

* Sun Jul 19 2020 Simone Caronni <negativo17@gmail.com> - 0.20.0-4
- Fix tests on RHEL/CentOS 7.

* Sat Jul 18 2020 Simone Caronni <negativo17@gmail.com> - 0.20.0-3
- Add signature verification.
- Trim changelog.
- Fix typo in the libs description.

* Tue Jun 30 2020 Simone Caronni <negativo17@gmail.com> - 0.20.0-2
- Update Source0 URL.
- Do not obsolete "bitcoin", just leave the provider for it.
- Let the build install the man pages.
- Make sure old post scriptlets run only on RHEL/CentOS 7.
- Do not install static library and archive.
- Be explicit with shared object versions.
- Use macros for more directories.
- Use GCC 9 and not 7 to build on RHEL/CentOS 7.

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
