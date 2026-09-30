# Privacy, passwords and backups

Backups, encryption, passwords, two-factor codes, messaging and file transfer. 23 projects; 8 with a permissive code license. Sorted by reuse, then stars. Part of the [software list](../README.md), which explains the reuse classes.

| project | reuse | license | language | stars | last push | why |
|---|---|---|---|---|---|---|
| [localsend/localsend](https://github.com/localsend/localsend) | copy | Apache-2.0 | Dart | 93083 | 2026-09-29 | Sends files between phones and computers on the same network with no account, cloud or cable, on every major OS. |
| [rclone/rclone](https://github.com/rclone/rclone) | copy | MIT | Go | 60029 | 2026-09-30 | Sync and copy to dozens of cloud storage providers, with encryption. |
| [restic/restic](https://github.com/restic/restic) | copy | BSD-2-Clause | Go | 36352 | 2026-09-25 | Encrypted, deduplicating backup CLI with snapshots and restore testing; writes to local disks, SFTP, S3 and anything rclone reaches. |
| [FiloSottile/age](https://github.com/FiloSottile/age) | copy | BSD-3-Clause | Go | 23764 | 2026-08-29 | Simple modern file encryption with short keys and no configuration; replaces GPG for encrypting files, and sops supports it as one of several backends. |
| [kopia/kopia](https://github.com/kopia/kopia) | copy | Apache-2.0 | Go | 14230 | 2026-09-29 | Encrypted, deduplicated snapshots with a UI and many storage backends. |
| [borgbackup/borg](https://github.com/borgbackup/borg) | copy | BSD-3-Clause (per license file) | Python | 13793 | 2026-09-29 | Deduplicating, encrypted backups. |
| [PrivateBin/PrivateBin](https://github.com/PrivateBin/PrivateBin) | copy (see note) | Zlib (per license file) | PHP | 8637 | 2026-09-30 | Pastebin where the server cannot read what is stored. **bundled rawinflate is GPL-2.0; other bundled libraries are BSD-3-Clause, MIT or Apache-2.0; favicon, icon and logo are CC-BY** |
| [restic/rest-server](https://github.com/restic/rest-server) | copy | BSD-2-Clause | Go | 1503 | 2026-09-20 | Append-only capable HTTP backend for restic backups. |
| [getsops/sops](https://github.com/getsops/sops) | library use | MPL-2.0 | Go | 23257 | 2026-09-28 | Encrypts secret values inside config files, keeping keys readable. |
| [gorhill/uBlock](https://github.com/gorhill/uBlock) | study only | GPL-3.0 | JavaScript | 68240 | 2026-09-26 | Lightweight browser content blocker for ads, trackers and malicious domains, with filter lists you can audit. |
| [keepassxreboot/keepassxc](https://github.com/keepassxreboot/keepassxc) | study only | GPL-2.0-only OR GPL-3.0-only (per license file) | C++ | 29032 | 2026-09-30 | Offline password manager with a local encrypted database. |
| [wg-easy/wg-easy](https://github.com/wg-easy/wg-easy) | study only | AGPL-3.0 | TypeScript | 27033 | 2026-09-30 | Simplest way to run a WireGuard VPN with a web UI. |
| [simplex-chat/simplex-chat](https://github.com/simplex-chat/simplex-chat) | study only | AGPL-3.0 | Haskell | 19507 | 2026-09-30 | Messenger without user identifiers. |
| [signalapp/Signal-Desktop](https://github.com/signalapp/Signal-Desktop) | study only | AGPL-3.0 | TypeScript | 16564 | 2026-09-28 | Desktop client for end-to-end encrypted messaging. |
| [cryptomator/cryptomator](https://github.com/cryptomator/cryptomator) | study only | GPL-3.0 | Java | 16228 | 2026-09-29 | Client-side encryption for files stored in any cloud folder. |
| [beemdevelopment/Aegis](https://github.com/beemdevelopment/Aegis) | study only | GPL-3.0 | Java | 13186 | 2026-09-06 | Open Android authenticator for TOTP and HOTP codes with an encrypted vault and exportable backups. |
| [garethgeorge/backrest](https://github.com/garethgeorge/backrest) | study only | GPL-3.0 | TypeScript | 7435 | 2026-09-21 | Web UI and scheduler for restic repositories. |
| [Kunzisoft/KeePassDX](https://github.com/Kunzisoft/KeePassDX) | study only | GPL-3.0 | Kotlin | 7397 | 2026-09-25 | Android KeePass client that opens the same database file as KeePassXC, with biometric unlock and autofill. |
| [Bubka/2FAuth](https://github.com/Bubka/2FAuth) | study only | AGPL-3.0 | PHP | 4171 | 2026-09-28 | Self-hosted web app for two-factor codes. |
| [borgmatic-collective/borgmatic](https://github.com/borgmatic-collective/borgmatic) | study only | GPL-3.0 | Python | 2336 | 2026-09-29 | Config-driven wrapper that schedules and verifies Borg backups. |
| [bitwarden/server](https://github.com/bitwarden/server) | check first | AGPL-3.0 + Bitwarden License v1.0 (per license file) | C# | 20223 | 2026-09-30 | Bitwarden's own server code. **code outside bitwarden_license/ is AGPL-3.0** |
| [duplicati/duplicati](https://github.com/duplicati/duplicati) | check first | MIT + Duplicati Inc Software license (per license file) | C# | 15045 | 2026-09-30 | Encrypted scheduled backups to cloud storage with a web UI. **code outside proprietary/ is MIT** |
| [veracrypt/VeraCrypt](https://github.com/veracrypt/VeraCrypt) | check first | Apache-2.0 + TrueCrypt-3.0 (per license file) | C | 11725 | 2026-09-30 | Encrypted volumes and full-disk encryption. |

A license marked *per license file* was read from the repository's own license files, because GitHub's detector could not classify it or reported only part of it; the file and the reason are recorded in [tools/overrides.json](../../tools/overrides.json).
