# Setup Push ke GitHub (sekali saja)

Agar `git push` jalan dari laptop ini, tambahkan SSH key **laptop ini** ke akun GitHub.

## Langkah 1: Buka halaman tambah SSH key

**Link:** https://github.com/settings/ssh/new

## Langkah 2: Isi form

- **Title:** `Laptop BML105010007416` (atau nama lain)
- **Key type:** Authentication Key
- **Key:** paste **seluruh baris** di bawah ini (satu baris):

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBvh+muGjCd9GvxmuELPN+PJR8OsBgI3dLmWP07ZysNO bukitmakmur\m.rizqinovniari@BML105010007416
```

Klik **Add SSH key**.

## Langkah 3: Load key ke ssh-agent (di Git Bash)

Jalankan sekali per sesi (atau tambahkan ke `~/.bashrc`):

```bash
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_ed25519
```

Cek koneksi ke GitHub:

```bash
ssh -T git@github.com
```

Harus muncul pesan: `Hi m-rizqinovniari! You've successfully authenticated...`

## Langkah 4: Push

```bash
cd ~/project/agentic-ko-design
git push origin master
```

---

### Jika masih "Permission denied (publickey)"

- Pastikan key **di atas** sudah benar-benar ditambah di https://github.com/settings/keys (bukan key dari laptop lain).
- Jalankan lagi: `ssh-add ~/.ssh/id_ed25519` lalu `ssh -T git@github.com`.
