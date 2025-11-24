"use client";

import { useEffect, useState, useRef } from "react";
import { apiClient } from "@/lib/api";
import type { NotificationItem } from "@/types/notifications";
import { useRouter } from "next/navigation";

export function NotificationsBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const dropdownRef = useRef<HTMLDivElement>(null);

  async function load() {
    setLoading(true);
    try {
      const res = await apiClient.getNotifications(false, 20);
      setItems(res.items);
      setUnreadCount(res.unread_count);
    } catch (err) {
      console.error("Error loading notifications:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // Poll every 60 seconds
    const id = setInterval(load, 60000);
    return () => clearInterval(id);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [open]);

  async function handleClickItem(n: NotificationItem) {
    if (!n.is_read) {
      try {
        const updated = await apiClient.updateNotification(n.id, { is_read: true });
        setItems((prev) => prev.map((x) => (x.id === n.id ? updated : x)));
        setUnreadCount((c) => Math.max(0, c - 1));
      } catch (err) {
        console.error("Error updating notification:", err);
      }
    }
    if (n.target_url) {
      router.push(n.target_url);
    }
    setOpen(false);
  }

  async function handleMarkAllRead() {
    try {
      await apiClient.markAllNotificationsRead();
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error("Error marking all as read:", err);
    }
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        className="relative p-2 rounded-full hover:bg-gray-100 transition-colors"
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
      >
        <span className="text-xl">🔔</span>
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] font-semibold rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white border rounded-lg shadow-lg z-50 max-h-96 flex flex-col">
          <div className="flex justify-between items-center px-4 py-3 border-b">
            <span className="text-sm font-semibold">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Mark all as read
              </button>
            )}
          </div>

          <div className="overflow-y-auto flex-1">
            {loading && (
              <div className="px-4 py-8 text-xs text-gray-500 text-center">
                Loading…
              </div>
            )}
            {!loading && items.length === 0 && (
              <div className="px-4 py-8 text-xs text-gray-500 text-center">
                No notifications yet.
              </div>
            )}
            {!loading &&
              items.map((n) => (
                <button
                  key={n.id}
                  className={
                    "w-full text-left px-4 py-3 border-b last:border-b-0 text-xs hover:bg-gray-50 transition-colors " +
                    (n.is_read ? "bg-white" : "bg-blue-50")
                  }
                  onClick={() => handleClickItem(n)}
                >
                  <div className="font-medium mb-1">{n.title}</div>
                  {n.body && (
                    <div className="text-gray-600 truncate mb-1">{n.body}</div>
                  )}
                  <div className="text-gray-400 text-[10px]">
                    {new Date(n.created_at).toLocaleString()}
                  </div>
                </button>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

