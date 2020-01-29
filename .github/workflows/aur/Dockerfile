FROM archlinux/base
ENV LC_ALL=C
ARG AUR_SSH_KEY
ARG GIT_EMAIL
ARG GIT_NAME
ARG aiogram_ver
ENV AIOGRAM_VERSION=${aiogram_ver}

RUN mkdir -p /etc/sudoers.d \
    && echo "makepkg ALL=(ALL) NOPASSWD: ALL" >/etc/sudoers.d/01_makepkg \
    && useradd -d /var/build -g users -mNrs /bin/bash makepkg

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && pacman -Syu base-devel pacman-contrib git openssh --noconfirm --needed \
    && rm -rf /var/cache/pacman/pkg/*

WORKDIR /var/build
USER makepkg

RUN mkdir /var/build/.ssh \
    && echo "${AUR_SSH_KEY}" >/var/build/.ssh/id_rsa \
    && chmod 400 /var/build/.ssh/id_rsa \
    && echo "aur.archlinux.org,5.9.250.164 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBOZAVWmj2k+dHTfyum7FyIivGcVUkDFHaXmPNxDwF7l8TvkAN8VDQJHEEGJhALMYtNsQ+kt0gksSh4HZqj9n5hI=" >/var/build/.ssh/known_hosts \
    && git config --global user.email ${GIT_EMAIL} \
    && git config --global user.name "${GIT_NAME}"

COPY --chown=makepkg:users PKGBUILD ./PKGBUILD

ENTRYPOINT ["/entrypoint.sh"]
