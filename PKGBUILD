pkgname=fastflowlm-gtk
pkgver=1.2.0
pkgrel=1
pkgdesc="A minimalist, modern desktop interface for FastFlowLM, built with GTK 4 and Libadwaita."
arch=('any')
url="https://github.com/marleylinux/FastFlowLM-GTK"
license=('MIT')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'libsoup3' 'gtksourceview5' 'python-psutil' 'fastflowlm' 'python-build' 'python-installer')
makedepends=('python-build' 'python-installer' 'python-setuptools' 'python-wheel')
source=("fastflowlm-gtk.desktop"
        "flm-gtk.png"
        "app.py"
        "pyproject.toml"
        "src/"
        "README.md")
sha256sums=('SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP')

build() {
  cd "$srcdir"
  python -m build --wheel --no-isolation
}

package() {
  cd "$srcdir"
  python -m installer --destdir="$pkgdir" dist/*.whl
  install -Dm644 fastflowlm-gtk.desktop "$pkgdir/usr/share/applications/fastflowlm-gtk.desktop"
  install -Dm644 flm-gtk.png "$pkgdir/usr/share/icons/hicolor/256x256/apps/fastflowlm-gtk.png"
}
