import { CHECKIN_STATUSES } from '../../utils/constants';
import { styles } from '../../utils/styles';

export const Badge = ({ status }) => {
  const config = CHECKIN_STATUSES.find((s) => s.value === status) || {
    label: status,
    color: '#667085',
  };

  return (
    <span
      style={{
        ...styles.badge,
        background: config.color + '18',
        color: config.color,
        border: `1px solid ${config.color}40`,
      }}
    >
      {config.label}
    </span>
  );
};
