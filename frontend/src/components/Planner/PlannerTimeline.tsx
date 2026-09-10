import React, { useRef, useEffect, useMemo, type FC } from 'react';
import { TimelineAxis } from './TimelineAxis';
import { CurrentTimeIndicator } from './CurrentTimeIndicator';
import { TimelineTaskCard } from './TimelineTaskCard';
import {
  PIXELS_PER_MINUTE,
  timeToPixels,
  calculateDurationPixels,
  parseTimeToMinutes,
} from './TimelineUtils';

import { Task, FixedBlock } from '../../types';
import { useTemplates } from '../../contexts/TemplateContext';

interface PlannerTimelineProps {
  tasks: Task[];
  fixedBlocks: FixedBlock[];
  plannerDate: string;
  editTask: (task: Task) => void;
  deleteTask: (taskId: string) => void;
  onCheckin: (taskId: string, data: any) => void;
  onAddToTemplate?: (task: Task) => void;
  highlightedTaskId?: string | null;
  setMessage: (msg: string) => void;
}

const TOTAL_HEIGHT = 24 * 60 * PIXELS_PER_MINUTE; // 2880px

/**
 * Column-layout algorithm for overlapping tasks.
 * Extracted outside the component so it is never recreated per-render.
 */
function calculateLayouts(tasksToLayout: Task[]): Record<string, { left: number; width: number }> {
  const sorted = [...tasksToLayout].sort(
    (a, b) => parseTimeToMinutes(a.start_time) - parseTimeToMinutes(b.start_time)
  );
  const layouts: Record<string, { left: number; width: number }> = {};

  let currentCluster: Task[] = [];
  let clusterEnd = 0;

  /**
   * Process Cluster.
   */
  const processCluster = (cluster: Task[]) => {
    const columns: Task[][] = [];
    for (const t of cluster) {
      const start = parseTimeToMinutes(t.start_time);
      let placed = false;
      for (const col of columns) {
        const lastTask = col[col.length - 1];
        const lastStart = parseTimeToMinutes(lastTask.start_time);
        const lastDuration = parseTimeToMinutes(lastTask.due_date) - lastStart;
        const lastEnd = lastStart + Math.max(lastDuration, 40);
        if (lastEnd <= start) {
          col.push(t);
          placed = true;
          break;
        }
      }
      if (!placed) columns.push([t]);
    }
    const numCols = columns.length;
    for (let colIdx = 0; colIdx < numCols; colIdx++) {
      for (const t of columns[colIdx]) {
        layouts[t.id] = { left: colIdx / numCols, width: 1 / numCols };
      }
    }
  };

  for (const t of sorted) {
    if (!t.start_time || !t.due_date) continue;
    const start = parseTimeToMinutes(t.start_time);
    const duration = parseTimeToMinutes(t.due_date) - start;
    const end = start + Math.max(duration, 40);

    if (currentCluster.length === 0) {
      currentCluster.push(t);
      clusterEnd = end;
    } else {
      if (start < clusterEnd) {
        currentCluster.push(t);
        clusterEnd = Math.max(clusterEnd, end);
      } else {
        processCluster(currentCluster);
        currentCluster = [t];
        clusterEnd = end;
      }
    }
  }
  if (currentCluster.length > 0) processCluster(currentCluster);

  return layouts;
}

const PlannerTimelineComponent: FC<PlannerTimelineProps> = ({
  tasks,
  fixedBlocks,
  plannerDate,
  editTask,
  deleteTask,
  onCheckin,
  onAddToTemplate,
  highlightedTaskId,
  setMessage
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to current time on mount
  useEffect(() => {
    if (containerRef.current) {
      const now = new Date();
      const currentMinutes = now.getHours() * 60 + now.getMinutes();
      const offset = Math.max(0, (currentMinutes * PIXELS_PER_MINUTE) - 200);
      containerRef.current.scrollTop = offset;
    }
  }, []);

  const { activeTemplate } = useTemplates();

  const activeBlocks = useMemo(() => {
    const dayOfWeek = new Date(plannerDate).getDay();
    return (fixedBlocks || []).filter(b => {
      if (!b.days_of_week.includes(dayOfWeek)) return false;
      if (b.apply_all) return true;
      if (activeTemplate && b.template_ids?.includes(activeTemplate.id)) return true;
      return false;
    });
  }, [fixedBlocks, plannerDate, activeTemplate]);

  /**
   * Pre-compute the Set of task IDs that fall entirely inside a fixed block.
   * O(tasks × blocks) total — replaces per-render per-task callback invocations.
   */
  const tasksInsideBlockIds = useMemo<Set<string>>(() => {
    const ids = new Set<string>();
    for (const task of tasks || []) {
      if (!task.start_time || !task.due_date) continue;
      const taskStart = parseTimeToMinutes(task.start_time);
      const taskEnd = parseTimeToMinutes(task.due_date);
      const inside = activeBlocks.some(block => {
        const blockStart = parseTimeToMinutes(block.start_time);
        const blockEnd = parseTimeToMinutes(block.end_time);
        return taskStart >= blockStart && taskEnd <= blockEnd;
      });
      if (inside) ids.add(task.id);
    }
    return ids;
  }, [tasks, activeBlocks]);

  const taskLayouts = useMemo(() => calculateLayouts(tasks || []), [tasks]);

  return (
    <div 
      ref={containerRef}
      className="relative w-full h-full overflow-y-auto bg-zinc-50/50 dark:bg-zinc-900/50 rounded-xl border border-border shadow-inner"
    >
      <div className="flex" style={{ height: TOTAL_HEIGHT }}>
        {/* Left Axis */}
        <TimelineAxis />
        
        {/* Right Planner Area */}
        <div className="relative flex-1 bg-[linear-gradient(to_bottom,#f1f5f9_1px,transparent_1px)]" style={{ backgroundSize: `100% ${60 * PIXELS_PER_MINUTE}px` }}>
          
          <CurrentTimeIndicator pixelsPerMinute={PIXELS_PER_MINUTE} />
          
          {/* Render Fixed Blocks Backgrounds */}
          {activeBlocks.map(block => {
            const top = timeToPixels(block.start_time);
            const height = calculateDurationPixels(block.start_time, block.end_time);
            return (
              <div 
                key={block.id}
                className="absolute left-0 right-0 bg-zinc-200/50 dark:bg-zinc-800/60 border-l-4 border-zinc-400 dark:border-zinc-500 opacity-60 dark:opacity-80 pointer-events-none flex flex-col justify-center items-center"
                style={{ top, height }}
              >
                <span className="text-zinc-500 dark:text-zinc-400 font-medium tracking-widest uppercase text-sm drop-shadow-sm">{block.name}</span>
              </div>
            );
          })}

          {/* Render Tasks */}
          {(tasks || []).map(task => {
            if (!task.start_time || !task.due_date) return null;
            return (
              <TimelineTaskCard
                key={task.id}
                task={task}
                pixelsPerMinute={PIXELS_PER_MINUTE}
                onEdit={editTask}
                onDelete={deleteTask}
                onCheckin={onCheckin}
                onAddToTemplate={onAddToTemplate}
                isHighlighted={highlightedTaskId === task.id}
                isSubtask={tasksInsideBlockIds.has(task.id)}
                tasks={tasks}
                plannerDate={plannerDate}
                setMessage={setMessage}
                layout={taskLayouts[task.id] || { left: 0, width: 1 }}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
};

export const PlannerTimeline = React.memo(PlannerTimelineComponent);
