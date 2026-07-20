import { ActivityItem } from './ActivityItem';
import { styles } from '../../utils/styles';

export const ActivityList = ({
  activities,
  plannerDate,
  openCheckinModal,
  editActivity,
  deleteActivity,
  historyActivityId,
  checkinHistory,
  loadCheckinHistory
}) => {
  if (!activities || activities.length === 0) {
    return <p style={styles.muted}>No activities planned for this day yet.</p>;
  }

  return (
    <div style={styles.activityList}>
      {activities.map((activity) => (
        <ActivityItem
          key={activity.id}
          activity={activity}
          plannerDate={plannerDate}
          openCheckinModal={openCheckinModal}
          editActivity={editActivity}
          deleteActivity={deleteActivity}
          historyActivityId={historyActivityId}
          checkinHistory={checkinHistory}
          loadCheckinHistory={loadCheckinHistory}
        />
      ))}
    </div>
  );
};
