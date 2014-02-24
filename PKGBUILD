# Maintainer: demian <mikar ατ gmx δοτ de>
pkgname=blockify
pkgver=0.5
pkgrel=1
pkgdesc="mute spotify ads"
arch=('any')
url="https://github.com/mikar/blockify"
license=('WTFPL')
depends=('wmctrl' 'alsa-utils')
optdepends=('tk: for ui-support')

source=("$pkgname-$pkgver.tar.gz::https://github.com/mikar/${pkgname}/archive/master.tar.gz")
sha256sums=('85de4ee9757542cc8da6b717f4386af377332c4bafc722edc9195493c2e595db')

package() {
    cd "$srcdir"/${pkgname}-master

    install -d  ${pkgdir}/usr/bin
    install -d  ${pkgdir}/usr/lib/python2.7/site-packages/${pkgname}
    install -m755 * ${pkgdir}/usr/lib/python2.7/site-packages/${pkgname}/
    ln -s /usr/lib/python2.7/site-packages/${pkgname}/${pkgname} ${pkgdir}/usr/bin/
    ln -s /usr/lib/python2.7/site-packages/${pkgname}/${pkgname}-ui ${pkgdir}/usr/bin/
}
