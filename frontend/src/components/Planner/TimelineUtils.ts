import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Shared scale: 2 pixels per minute → 24-hour canvas is 2 880px tall */
export const PIXELS_PER_MINUTE = 2;

export function parseTimeToMinutes(timeString: string | null | undefined): number {
  if (!timeString) return 0;
  // Handle formats like "YYYY-MM-DDTHH:MM:SS" or "HH:MM:SS" or "HH:MM"
  let timePart = timeString;
  if (timeString.includes('T')) {
    timePart = new Date(timeString).toTimeString().substring(0, 5);
  }
  const [h, m] = timePart.split(':').map(Number);
  return (h || 0) * 60 + (m || 0);
}

export function timeToPixels(timeString: string | null | undefined, pixelsPerMinute = PIXELS_PER_MINUTE): number {
  return parseTimeToMinutes(timeString) * pixelsPerMinute;
}

export function calculateDurationMinutes(startTime: string, endTime: string): number {
  const start = parseTimeToMinutes(startTime);
  const end = parseTimeToMinutes(endTime);
  return Math.max(0, end - start);
}

export function calculateDurationPixels(startTime: string, endTime: string, pixelsPerMinute = PIXELS_PER_MINUTE): number {
  return calculateDurationMinutes(startTime, endTime) * pixelsPerMinute;
}

/**
 * Format an ISO datetime string to "HH:MM" in local time.
 * Returns an empty string for falsy input.
 */
export function formatIsoTime(isoString?: string | null): string {
  if (!isoString) return '';
  return new Date(isoString).toTimeString().substring(0, 5);
}

export function getStatusColor(status: string) {
  switch (status?.toLowerCase()) {
    case 'pending':
    case 'pending_not_done':
      return 'bg-amber-100 text-amber-800 border-amber-200';
    case 'in_progress':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'partial':
    case 'partial_not_done':
      return 'bg-purple-100 text-purple-800 border-purple-200';
    case 'done':
      return 'bg-green-100 text-green-800 border-green-200';
    case 'not_done':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'rescheduled':
      return 'bg-zinc-100 text-zinc-800 border-zinc-200';
    default:
      return 'bg-zinc-100 text-zinc-800 border-zinc-200';
  }
}

export function getPriorityLabel(priority: number) {
  switch (priority) {
    case 1:
      return '🔥🔥🔥';
    case 2:
      return '🔥🔥';
    case 3:
      return '🔴';
    case 4:
      return '🟡';
    case 5:
      return '🟢';
    default:
      return '⚪';
  }
}
