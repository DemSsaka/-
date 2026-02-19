"use client";

import { useEffect, useState } from "react";

import { useLocale } from "@/components/locale-provider";
import { Toast } from "@/components/toast";
import { api } from "@/lib/api";
import { UserProfile } from "@/lib/types";

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState("");
  const [nickname, setNickname] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [bio, setBio] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const { locale } = useLocale();
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const profile = await api.get<UserProfile>("/api/profile/me");
        setNickname(profile.nickname ?? "");
        setAvatarUrl(profile.avatar_url ?? "");
        setBio(profile.bio ?? "");
        setBirthDate(profile.birth_date ?? "");
      } catch {
        window.location.href = "/";
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function uploadAvatar(file: File) {
    setUploading(true);
    try {
      const uploaded = await api.uploadImage(file);
      setAvatarUrl(uploaded.url);
      setToast(locale === "ru" ? "Аватар загружен" : "Avatar uploaded");
    } catch (e) {
      setToast((e as Error).message);
    } finally {
      setUploading(false);
    }
  }

  async function save() {
    try {
      const payload = {
        nickname: nickname || null,
        avatar_url: avatarUrl || null,
        bio: bio || null,
        birth_date: birthDate || null
      };
      await api.patch<UserProfile>("/api/profile/me", payload);
      setToast(locale === "ru" ? "Настройки сохранены" : "Settings saved");
    } catch (e) {
      setToast((e as Error).message);
    }
  }

  if (loading) {
    return <main className="mx-auto max-w-3xl px-4 py-8">Loading...</main>;
  }

  return (
    <main className="mx-auto max-w-3xl space-y-5 px-4 py-8">
      <header>
        <h1 className="text-3xl font-black">{locale === "ru" ? "Настройки профиля" : "Profile settings"}</h1>
      </header>

      <section className="card space-y-4 p-5">
        <div className="grid gap-2">
          <label className="text-sm font-medium">{locale === "ru" ? "Никнейм" : "Nickname"}</label>
          <input className="input" value={nickname} onChange={e => setNickname(e.target.value)} />
        </div>
        <div className="grid gap-2">
          <label className="text-sm font-medium">{locale === "ru" ? "Аватар (URL)" : "Avatar (URL)"}</label>
          <input className="input" value={avatarUrl} onChange={e => setAvatarUrl(e.target.value)} />
          <label className="btn-secondary inline-flex w-fit cursor-pointer" htmlFor="avatar-upload">
            {uploading ? (locale === "ru" ? "Загрузка..." : "Uploading...") : (locale === "ru" ? "Загрузить файл" : "Upload file")}
          </label>
          <input
            id="avatar-upload"
            type="file"
            accept="image/*"
            className="hidden"
            onChange={e => {
              const file = e.target.files?.[0];
              if (file) void uploadAvatar(file);
            }}
          />
        </div>
        <div className="grid gap-2">
          <label className="text-sm font-medium">{locale === "ru" ? "Описание профиля" : "Profile description"}</label>
          <textarea className="input min-h-28" value={bio} onChange={e => setBio(e.target.value)} />
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          <div className="grid gap-2">
            <label className="text-sm font-medium">{locale === "ru" ? "Дата рождения" : "Birth date"}</label>
            <input className="input" type="date" value={birthDate} onChange={e => setBirthDate(e.target.value)} />
          </div>
        </div>
        <button className="btn-primary" onClick={save}>
          {locale === "ru" ? "Сохранить" : "Save"}
        </button>
      </section>
      {toast ? <Toast message={toast} onDone={() => setToast("")} /> : null}
    </main>
  );
}
