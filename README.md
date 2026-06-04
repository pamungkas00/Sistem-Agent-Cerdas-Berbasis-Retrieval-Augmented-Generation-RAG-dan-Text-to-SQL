Merupakan sebuah sistem asisten kecerdasan buatan (AI Agent) yang dikembangkan untuk membantu divisi Asset dan teknisi lapangan di PT. Indonesia Comnet Plus (PLN ICON PLUS) Kawasan PLN Cawang. Sistem ini menggabungkan dua teknologi utama, yaitu Retrieval-Augmented Generation (RAG) untuk basis pengetahuan dokumen dan Text-to-SQL untuk akses data database relasional.

## 🌟 Fitur Utama
* **Text-to-SQL Otomatis**: Menerjemahkan bahasa manusia secara langsung menjadi kueri MySQL untuk mengakses data pelanggan, status perangkat, dan riwayat gangguan.
* **Retrieval-Augmented Generation (RAG)**: Menyediakan jawaban teknis berdasarkan Standar Operasional Prosedur (SOP) dan modul infrastruktur FTTH/Fiber Optic yang tersimpan dalam format PDF.
* **Dynamic Router Chain**: Menggunakan logika *routing* cerdas berbasis LCEL untuk menentukan secara otomatis apakah kueri harus diarahkan ke database (`SQL`), dokumen (`RAG`), atau obrolan umum (`GENERAL`).
* **Token Streaming**: Memberikan pengalaman respons interaktif dengan teks yang muncul kata demi kata secara *real-time*.
* **Keamanan Data Lokal**: Seluruh proses komputasi dilakukan secara lokal menggunakan Ollama, menjamin kerahasiaan data pelanggan perusahaan.

## 🛠️ Tech Stack
* **Language**: Python
* **Orchestration**: LangChain Expression Language (LCEL)
* **LLM & Embedding**: Ollama (Llama 3 & Nomic-Embed-Text)
* **Database Terstruktur**: MySQL (Database `ai_pelanggan`)
* **Database Vektor**: ChromaDB
* **Antarmuka**: Streamlit

## 📋 Prasyarat
Sebelum menjalankan sistem, pastikan perangkat Anda telah terpasang:
1.  **Python 3.10+**
2.  **Ollama** (Pastikan model `llama3` dan `nomic-embed-text` sudah di-*pull*)
3.  **MySQL Server** (XAMPP atau MySQL Installer)


## 📂 Struktur Data
* **Database Relasional**: Mencakup tabel `pelanggan_`, `gangguan_`, `perangkat_`, dan `status_`.
* **Knowledge Base**: Berisi modul fundamental internet, infrastruktur dasar, fiber optic, dan SOP instalasi (Modul 1-6).

> [!IMPORTANT]
> Proyek ini menggunakan model bahasa lokal demi menjamin privasi penuh terhadap data gangguan pelanggan perusahaan dan seluruh data yang digunakan data dummy yang formatnya dibuat semirip mungkin dengan aslinya.


## 🧑‍💻 Pengembang
* **Nama**: Gilang Putro Pamungkas
* **NIM**: 22515030711101
* **Instansi**: Program Studi Teknik Komputer, Universitas Brawijaya
* **Lokasi PKL**: PT. Indonesia Comnet Plus (PLN ICON PLUS) - Divisi NA3P Asset

---
*Proyek ini dikembangkan sebagai bagian dari persyaratan Praktik Kerja Lapangan (PKL) tahun 2025.*
