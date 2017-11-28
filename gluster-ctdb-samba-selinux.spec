%define selinux_variants targeted

%define moduletype apps
%define modulename gluster-ctdb-samba

Name:           %{modulename}-selinux
Version:        1.0.0
Release:        1
Summary:        SELinux policy module for a custom gluster, ctdb, and samba setup

Group:          System Environment/Base
License:        GPLv3+
URL:            http://github.com/jmontleon/gluster-ctdb-samba-selinux
Source0:        gluster-ctdb-samba.te

BuildRequires:  checkpolicy
BuildRequires:  hardlink
BuildRequires:  policycoreutils
BuildRequires:  selinux-policy-devel
BuildRequires:  /usr/bin/pod2man

BuildArch:      noarch

Requires:           selinux-policy
Requires(post):     /usr/sbin/semodule, /sbin/restorecon, /usr/sbin/setsebool, /usr/sbin/selinuxenabled, /usr/sbin/semanage
Requires(post):     policycoreutils-python
Requires(post):     selinux-policy-targeted
Requires(postun):   /usr/sbin/semodule, /sbin/restorecon

%description
%{summary}

%prep
cp %{SOURCE0} %{modulename}.te

%build
# create selinux-friendly version from VR and replace it inplace
perl -i -pe 'BEGIN { $VER = join ".", grep /^\d+$/, split /\./, "%{version}.%{release}"; } s!\@\@VERSION\@\@!$VER!g;' %{modulename}.te

# determine distribution name and version
%if 0%{?rhel} >= 6
    distver=rhel%{rhel}
%endif
%if 0%{?fedora} >= 18
    distver=fedora%{fedora}
%endif

# build policy
for selinuxvariant in %{selinux_variants}
do
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile DISTRO=${distver}
    bzip2 -9 %{modulename}.pp
    mv %{modulename}.pp.bz2 %{modulename}.ppbz2.${selinuxvariant}
    make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean DISTRO=${distver}
done

%install
# install policy modules
for selinuxvariant in %{selinux_variants}
  do
    install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
    install -p -m 644 %{modulename}.ppbz2.${selinuxvariant} \
        %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{modulename}.pp.bz2
  done

# install interfaces
install -d %{buildroot}%{_datadir}/selinux/devel/include/%{moduletype}
install -p -m 644 %{modulename}.if %{buildroot}%{_datadir}/selinux/devel/include/%{moduletype}/%{modulename}.if

# hardlink identical policy module packages together
/usr/sbin/hardlink -cv %{buildroot}%{_datadir}/selinux

%post
for selinuxvariant in %{selinux_variants}
do
  /usr/sbin/semodule -s ${selinuxvariant} -i \
    %{_datadir}/selinux/${selinuxvariant}/%{modulename}.pp.bz2 > /dev/null
done

%postun
if [ $1 -eq 0 ] ; then
  for selinuxvariant in %{selinux_variants}
  do
    /usr/sbin/semodule -s ${selinuxvariant} -r %{modulename} > /dev/null
  done
fi

%files
%attr(0600,root,root) %{_datadir}/selinux/*/%{modulename}.pp.bz2
%{_datadir}/selinux/devel/include/%{moduletype}/%{modulename}.if

%changelog
