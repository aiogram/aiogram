#!/bin/bash

main() {
    case "${1:-}" in
        build)
            build
            ;;
        commit)
            prepublish
            git diff origin/master
            git log --oneline | head -n5
            ;;
        publish)
            prepublish
            publish
            ;;
        shell)
            exec /bin/bash -
            ;;
        *)
            echo "No such command!" >&2
            exit 127
            ;;
    esac
}

prepare_pkgbuild() {
    sed -Ei "s/^pkgver=$/pkgver=${AIOGRAM_VERSION}/" PKGBUILD
    updpkgsums
}

build() {
    prepare_pkgbuild
    makepkg -sicC --noconfirm --noprogressbar
}

prepare_git() {
    mkdir dist && cd dist
    git init
    git remote add origin ssh://aur@aur.archlinux.org/python-aiogram.git
    git pull origin master
}

commit() {
    git add PKGBUILD .SRCINFO
    git commit -m 'New version: v'"${AIOGRAM_VERSION}"
}

prepublish() {
    prepare_pkgbuild
    prepare_git
    cp ../PKGBUILD ./
    makepkg --printsrcinfo >.SRCINFO
    commit
}

publish() {
    git push -u origin master
}

# check whether running as script or sourced by another shell (not reliable)
if [[ "$(basename $0)" = "entrypoint.sh" ]]; then
    set -euo pipefail
    main $@
fi
