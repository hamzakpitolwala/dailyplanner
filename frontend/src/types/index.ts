export interface UserProfile {
  id: string;
  email: string;
  name: string;
  active_planner_id?: string;
  [key: string]: any;
}

export interface Subtask {
  id: string;
  task_id: string;
  title: string;
  is_completed: boolean | number;
}

export interface TaskCheckin {
  id?: string;
  task_id?: string;
  status: string;
  missed_reason_id?: string;
  alternate_activity_id?: string;
  missed_reason?: any;
  alternate_activity?: any;
  notes?: string;
  created_at?: string;
}

export interface Task {
  id: string;
  user_id?: string;
  category_id?: string;
  title: string;
  description?: string;
  priority: number;
  status: string;
  start_time?: string;
  due_date?: string;
  completed_at?: string;
  source?: string;
  external_event_id?: string;
  visibility?: string;
  subtasks?: Subtask[];
  checkins?: TaskCheckin[];
  source_template_id?: string;
  source_template_name?: string;
  source_template_task_id?: string;
  requires_reason?: boolean;
  allows_alternate?: boolean;
  missed_reason?: string;
  alternate_activity?: string;
}

export interface PlannerTemplate {
  id: string;
  name: string;
  description?: string;
  template_tasks?: any[];
}

export interface FixedBlock {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  days_of_week: number[];
}
