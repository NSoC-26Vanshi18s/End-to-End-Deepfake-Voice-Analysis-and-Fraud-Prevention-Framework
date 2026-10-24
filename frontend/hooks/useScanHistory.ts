"use client";

import { useEffect, useState } from "react";

export interface ScanHistoryItem {
  id: string;
  filename: string;
  timestamp: string;
  fake_probability: number;
  risk_level: string;
  status: string;
  details?: Record<string, unknown>;
}

const STORAGE_KEY = "voxshield_scan_history_v1";
const MAX_HISTORY = 30;

export function useScanHistory() {
  const [history, setHistory] = useState<ScanHistoryItem[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setHistory(JSON.parse(stored));
      }
    } catch {
      setHistory([]);
    } finally {
      setIsLoaded(true);
    }
  }, []);

  const saveItem = (item: Omit<ScanHistoryItem, "id" | "timestamp">) => {
    const newItem: ScanHistoryItem = {
      ...item,
      id: `SCAN-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      timestamp: new Date().toISOString(),
    };

    setHistory((prev) => {
      const updated = [newItem, ...prev.filter((p) => p.filename !== item.filename)].slice(0, MAX_HISTORY);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch {
        // storage quota exceeded or disabled
      }
      return updated;
    });

    return newItem;
  };

  const removeItem = (id: string) => {
    setHistory((prev) => {
      const updated = prev.filter((item) => item.id !== id);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch {
        // ignore
      }
      return updated;
    });
  };

  const clearHistory = () => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    setHistory([]);
  };

  return {
    history,
    isLoaded,
    saveItem,
    removeItem,
    clearHistory,
  };
}
