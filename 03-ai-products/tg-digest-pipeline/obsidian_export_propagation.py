"""Экспорт графа распространения story_clusters в Obsidian vault.

Источник данных для верификации:
- messages.forwarded_from_id = "channel{numeric_id}"
- collector_queue.channel_id  = "{numeric_id}"
=> JOIN: 'channel' || cq.channel_id = m.forwarded_from_id
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "data" / "messages.db"
VAULT_DIR = HERE / "obsidian_vault_propagation"

MIN_CHANNELS = 2


def _sanitize(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", (name or "без_названия").strip()) or "без_названия"


def _channel_name(row: dict) -> str:
    return row.get("channel_title") or row.get("channel_username") or row.get("channel_id") or "Неизвестный"


def _link(name: str) -> str:
    return f"[[{name}]]"


def load_saved_by_channel(con: sqlite3.Connection) -> dict[str, dict[str, int]]:
    """
    Возвращает {channel_numeric_id: {"saved_vitaliy": N, "saved_andrey": M}}.
    Считает сколько раз посты из каждого канала сохранены в Избранном.
    """
    cur = con.execute("""
        SELECT
            SUBSTR(forwarded_from_id, 8) AS channel_id,
            source,
            COUNT(*) AS cnt
        FROM messages
        WHERE source IN ('saved_vitaliy', 'saved_andrey')
          AND forwarded_from_id IS NOT NULL
          AND forwarded_from_id LIKE 'channel%'
        GROUP BY forwarded_from_id, source
    """)
    result: dict[str, dict[str, int]] = {}
    for channel_id, source, cnt in cur.fetchall():
        if channel_id not in result:
            result[channel_id] = {}
        result[channel_id][source] = cnt
    return result


def load_telegram_verified(con: sqlite3.Connection) -> dict[str, tuple[str, int]]:
    """
    Возвращает {channel_numeric_id: (channel_name, forward_count)}.
    Канал считается Telegram-верифицированным источником, если на него
    есть forwarded_from_id в таблице messages.
    """
    cur = con.execute("""
        SELECT
            SUBSTR(forwarded_from_id, 8) AS channel_id,
            forwarded_from,
            COUNT(*) AS cnt
        FROM messages
        WHERE forwarded_from_id IS NOT NULL
          AND forwarded_from_id LIKE 'channel%'
        GROUP BY forwarded_from_id
    """)
    result: dict[str, tuple[str, int]] = {}
    for row in cur.fetchall():
        cid, name, cnt = row
        result[cid] = (name or "", cnt)
    return result


def load_clusters(con: sqlite3.Connection) -> list[dict]:
    cur = con.execute("""
        SELECT id, label, niche, post_count, channel_count, total_views, max_views, score
        FROM story_clusters
        WHERE channel_count >= ?
        ORDER BY score DESC
    """, (MIN_CHANNELS,))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def load_posts_for_cluster(con: sqlite3.Connection, cluster_id: int) -> list[dict]:
    cur = con.execute("""
        SELECT channel_id, channel_title, channel_username, message_id,
               date, text, views, forwards
        FROM collector_queue
        WHERE cluster_id = ?
        ORDER BY date ASC
    """, (cluster_id,))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def write_cluster(
    cluster: dict,
    posts: list[dict],
    verified: dict[str, tuple[str, int]],
    saved_by_channel: dict[str, dict[str, int]],
    out_dir: Path,
) -> str:
    cid = cluster["id"]
    label = (cluster.get("label") or "").strip()[:80] or f"Кластер {cid}"
    niche = cluster.get("niche") or ""
    views = cluster.get("total_views") or 0
    score = cluster.get("score") or 0
    file_slug = f"cluster_{cid:04d}"

    lines = [
        f"# {label}",
        "",
        f"Ниша: {niche} | Постов: {len(posts)} | Каналов: {cluster['channel_count']} | "
        f"Просмотры: {views:,} | Score: {score:.1f}",
        "",
        "## Ветка распространения",
        "",
    ]

    # Ищем Telegram-верифицированный первоисточник среди постов кластера
    tg_source_idx: int | None = None
    for i, post in enumerate(posts):
        if post.get("channel_id") in verified:
            tg_source_idx = i
            break

    for i, post in enumerate(posts):
        ch = _channel_name(post)
        ch_id = post.get("channel_id") or ""
        dt = (post.get("date") or "")[:16].replace("T", " ")
        v = post.get("views") or 0
        fwd = post.get("forwards") or 0
        snippet = (post.get("text") or "").replace("\n", " ")[:100]
        snippet_str = f"\n   > {snippet}" if snippet else ""

        is_tg_verified = ch_id in verified
        fwd_count_in_archive = verified.get(ch_id, ("", 0))[1]

        if i == 0 and tg_source_idx == 0:
            role = "**первоисточник** ✅ Telegram"
            confidence = f"_(подтверждён: {fwd_count_in_archive} форвардов в архиве)_"
        elif i == 0 and tg_source_idx is None:
            role = "**первоисточник** 📅 по дате"
            confidence = "_(не верифицирован через Telegram)_"
        elif i == 0 and tg_source_idx is not None:
            role = "**первоисточник** 📅 по дате"
            confidence = f"_(возможный первоисточник: #{tg_source_idx + 1})_"
        elif is_tg_verified and tg_source_idx == i:
            role = "**первоисточник** ✅ Telegram"
            confidence = f"_(подтверждён: {fwd_count_in_archive} форвардов в архиве)_"
        elif is_tg_verified:
            role = f"распространитель #{i} ✅ Telegram"
            confidence = f"_(известный источник: {fwd_count_in_archive} форвардов в архиве)_"
        else:
            role = f"распространитель #{i}"
            confidence = ""

        conf_str = f" {confidence}" if confidence else ""
        lines.append(
            f"{i + 1}. `{dt}` — {_link(ch)} ({role}){conf_str} — {v:,} 👁 {fwd} 🔁{snippet_str}"
        )

    lines += ["", "## Каналы"]
    unique_channels = list(dict.fromkeys(_channel_name(p) for p in posts))
    lines.append(" · ".join(_link(ch) for ch in unique_channels))

    # Избранное: проверяем, сохранял ли Виталий/Андрей посты из каналов этого кластера
    saved_hits: list[str] = []
    for post in posts:
        ch_id = post.get("channel_id") or ""
        ch = _channel_name(post)
        saved = saved_by_channel.get(ch_id)
        if not saved:
            continue
        parts = []
        if saved.get("saved_vitaliy"):
            parts.append(f"Виталий ({saved['saved_vitaliy']} постов)")
        if saved.get("saved_andrey"):
            parts.append(f"Андрей ({saved['saved_andrey']} постов)")
        saved_hits.append(f"- {_link(ch)} — {', '.join(parts)}")

    if saved_hits:
        lines += ["", "## Отметки из Избранного", ""]
        lines += saved_hits

    path = out_dir / f"{file_slug}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return file_slug


def write_channel(
    name: str,
    as_source: list[tuple[str, str]],
    as_distributor: list[tuple[str, str]],
    tg_fwd_count: int,
    out_dir: Path,
) -> None:
    tg_badge = f" | В архиве форвардов: **{tg_fwd_count}** ✅" if tg_fwd_count else ""
    lines = [
        f"# {name}",
        "",
        f"Первоисточник в: **{len(as_source)}** историях | "
        f"Распространитель в: **{len(as_distributor)}** историях{tg_badge}",
        "",
    ]
    if as_source:
        lines += ["## Истории (первоисточник)", ""]
        for slug, dt, conf in as_source[:50]:
            badge = " ✅" if conf == "tg" else " 📅"
            lines.append(f"- {_link(slug)} · {dt}{badge}")
        lines.append("")
    if as_distributor:
        lines += ["## Истории (распространитель)", ""]
        for slug, dt, conf in as_distributor[:50]:
            lines.append(f"- {_link(slug)} · {dt}")
        lines.append("")

    path = out_dir / f"{_sanitize(name)}.md"
    path.write_text("\n".join(lines), encoding="utf-8")


def write_index(clusters: list[dict], total_channels: int, out_path: Path) -> None:
    lines = [
        "# Граф распространения — ИнфоПовод",
        "",
        f"Историй: **{len(clusters)}** | Каналов: **{total_channels}**",
        "",
        "## Легенда",
        "- **первоисточник** ✅ Telegram — подтверждён через messages.forwarded_from",
        "- **первоисточник** 📅 по дате — первый в кластере по дате, не верифицирован",
        "- **распространитель** ✅ Telegram — канал известен как источник в архиве",
        "",
        "## Топ историй по охвату",
        "",
    ]
    for c in clusters[:50]:
        cid = c["id"]
        label = (c.get("label") or "").strip()[:60] or f"Кластер {cid}"
        slug = f"cluster_{cid:04d}"
        views = c.get("total_views") or 0
        ch_count = c.get("channel_count") or 0
        lines.append(f"- {_link(slug)} — {ch_count} каналов · {views:,} 👁")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    print(f"Читаем {DB_PATH} ...")
    con = sqlite3.connect(DB_PATH)

    print("Загружаем Telegram-верификацию из messages.forwarded_from_id ...")
    verified = load_telegram_verified(con)
    print(f"Telegram-верифицированных каналов-источников: {len(verified)}")

    print("Загружаем данные Избранного (saved_vitaliy, saved_andrey) ...")
    saved_by_channel = load_saved_by_channel(con)
    print(f"Каналов с постами в Избранном: {len(saved_by_channel)}")

    clusters = load_clusters(con)
    print(f"Кластеров (>= {MIN_CHANNELS} каналов): {len(clusters)}")

    clusters_dir = VAULT_DIR / "кластеры"
    channels_dir = VAULT_DIR / "каналы"
    clusters_dir.mkdir(parents=True, exist_ok=True)
    channels_dir.mkdir(parents=True, exist_ok=True)

    # channel_name -> {as_source, as_distributor, tg_fwd_count}
    channel_roles: dict[str, dict] = {}

    for cluster in clusters:
        posts = load_posts_for_cluster(con, cluster["id"])
        if len(posts) < MIN_CHANNELS:
            continue

        # Определяем Telegram-верифицированный первоисточник
        tg_source_idx: int | None = None
        for i, post in enumerate(posts):
            if post.get("channel_id") in verified:
                tg_source_idx = i
                break

        file_slug = write_cluster(cluster, posts, verified, saved_by_channel, clusters_dir)

        for i, post in enumerate(posts):
            ch = _channel_name(post)
            ch_id = post.get("channel_id") or ""
            dt = (post.get("date") or "")[:10]
            tg_fwd = verified.get(ch_id, ("", 0))[1]

            if ch not in channel_roles:
                channel_roles[ch] = {"as_source": [], "as_distributor": [], "tg_fwd_count": tg_fwd}

            # Источник = либо первый по дате, либо Telegram-верифицированный
            if i == 0 or i == tg_source_idx:
                conf = "tg" if ch_id in verified else "date"
                channel_roles[ch]["as_source"].append((file_slug, dt, conf))
            else:
                channel_roles[ch]["as_distributor"].append((file_slug, dt, ""))

    print(f"Уникальных каналов: {len(channel_roles)}")

    for ch_name, roles in channel_roles.items():
        write_channel(
            ch_name,
            roles["as_source"],
            roles["as_distributor"],
            roles["tg_fwd_count"],
            channels_dir,
        )

    write_index(clusters, len(channel_roles), VAULT_DIR / "_Главная.md")
    con.close()
    print(f"\nVault готов: {VAULT_DIR}")


if __name__ == "__main__":
    main()
