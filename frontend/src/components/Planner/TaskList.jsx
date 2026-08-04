import { TaskItem } from './TaskItem';
import { styles } from '../../utils/styles';

export const TaskList = ({
  tasks,
  plannerDate,
  editTask,
  deleteTask,
  onCheckin,
  setMessage
}) => {
  if (!tasks || tasks.length === 0) {
    return <p style={styles.muted}>No tasks planned for this day yet.</p>;
  }

  return (
    <div style={styles.activityList}>
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
