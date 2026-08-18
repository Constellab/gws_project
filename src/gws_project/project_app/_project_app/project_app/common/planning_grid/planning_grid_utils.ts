import type { GridSlot } from './planning_grid_types';

/** Pixels rendered per minute of the day axis. */
export const PX_PER_MINUTE = 1.2;

export interface DayBounds {
  dayStartMinutes: number;
  dayEndMinutes: number;
  lunchStartMinutes: number;
  lunchEndMinutes: number;
}

export function timeToMinutes(hhmm: string): number {
  const [h, m] = hhmm.split(':').map(Number);
  return h * 60 + m;
}

export function minutesToTime(totalMinutes: number): string {
  const clamped = Math.max(0, Math.round(totalMinutes));
  const h = Math.floor(clamped / 60);
  const m = clamped % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

export function snapToStep(minutes: number, step: number): number {
  return Math.round(minutes / step) * step;
}

export function dayBoundsFromSettings(
  dayStartTime: string,
  dayEndTime: string,
  lunchStartTime: string,
  lunchEndTime: string
): DayBounds {
  return {
    dayStartMinutes: timeToMinutes(dayStartTime),
    dayEndMinutes: timeToMinutes(dayEndTime),
    lunchStartMinutes: timeToMinutes(lunchStartTime),
    lunchEndMinutes: timeToMinutes(lunchEndTime),
  };
}

/** The day axis is a direct linear mapping of clock time - the lunch break renders
 * as real, colored space (see DayCell) rather than being collapsed out of it; it is
 * kept unreachable for drops/resizes via clampOutsideLunch below instead. */
export function dayColumnHeightPx(bounds: DayBounds): number {
  return Math.max(bounds.dayEndMinutes - bounds.dayStartMinutes, 0) * PX_PER_MINUTE;
}

export function clockMinutesToPixels(clockMinutes: number, bounds: DayBounds): number {
  return (clockMinutes - bounds.dayStartMinutes) * PX_PER_MINUTE;
}

export function pixelsToClockMinutes(pixels: number, bounds: DayBounds): number {
  return bounds.dayStartMinutes + pixels / PX_PER_MINUTE;
}

/**
 * Push a candidate clock time outside of the lunch break, snapping to whichever
 * edge is closer. This is what makes lunch geometrically unreachable: a drop or
 * resize that lands inside it is redirected to just before or just after it.
 */
export function clampOutsideLunch(clockMinutes: number, bounds: DayBounds): number {
  const hasLunch = bounds.lunchEndMinutes > bounds.lunchStartMinutes;
  if (!hasLunch || clockMinutes <= bounds.lunchStartMinutes || clockMinutes >= bounds.lunchEndMinutes) {
    return clockMinutes;
  }
  const distToStart = clockMinutes - bounds.lunchStartMinutes;
  const distToEnd = bounds.lunchEndMinutes - clockMinutes;
  return distToStart <= distToEnd ? bounds.lunchStartMinutes : bounds.lunchEndMinutes;
}

/**
 * Convert a pointer's Y offset within a day column into a clock time, snapped to
 * `stepMinutes` and pushed outside of lunch. Used both for drag-drop (new start
 * time) and resize (new edge time).
 */
export function pixelYToClockMinutes(pixelY: number, bounds: DayBounds, stepMinutes: number): number {
  const raw = pixelsToClockMinutes(Math.max(pixelY, 0), bounds);
  const daySpan = Math.max(bounds.dayEndMinutes - bounds.dayStartMinutes, 0);
  const snappedOffset = snapToStep(raw - bounds.dayStartMinutes, stepMinutes);
  const clampedOffset = Math.min(Math.max(snappedOffset, 0), daySpan);
  return clampOutsideLunch(bounds.dayStartMinutes + clampedOffset, bounds);
}

export function isoDateOf(datetimeString: string): string {
  return datetimeString.slice(0, 10);
}

/** "HH:MM" clock time of an ISO datetime string, ignoring its date part. */
export function clockTimeOf(datetimeString: string): string {
  const timePart = datetimeString.slice(11, 16);
  return timePart || '00:00';
}

/**
 * Lightweight client-side overlap check for two slots assigned to the same person on
 * the same day, used only for instant visual feedback during a drag before the
 * server-confirmed `is_overlapping` flag arrives on the next grid refresh.
 */
export function slotsOverlap(a: GridSlot, b: GridSlot): boolean {
  return a.start_datetime < b.end_datetime && b.start_datetime < a.end_datetime;
}
