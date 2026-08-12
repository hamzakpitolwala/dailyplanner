import { TaskItem } from './TaskItem';

export const TaskList = ({
  tasks,
  plannerDate,
  editTask,
  deleteTask,
  onCheckin,
  setMessage
}) => {
  if (!tasks || tasks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center bg-zinc-50 dark:bg-zinc-900/30 rounded-2xl border border-dashed border-border">
        <p className="text-zinc-500 dark:text-zinc-400 font-medium">No tasks planned for this day yet.</p>
        <p className="text-sm text-zinc-400 dark:text-zinc-500 mt-1">Add a task above to get started.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {tasks.map((task) => (
        <TaskItem
          key={task.id}
          task={task}
          tasks={tasks}
          plannerDate={plannerDate}
          editTask={editTask}
          deleteTask={deleteTask}
          onCheckin={onCheckin}
          setMessage={setMessage}
        />
      ))}
    </div>
  );
};
