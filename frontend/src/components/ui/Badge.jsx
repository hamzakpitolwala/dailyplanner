import { TASK_STATUSES } from '../../utils/constants';

export const Badge = ({ status }) => {
  const config = TASK_STATUSES.find((s) => s.value === status) || {
    label: status,
    color: '#667085',
  };

  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold whitespace-nowrap"
      style={{
        background: config.color + '18',
        color: config.color,
        border: `1px solid ${config.color}40`,
      }}
    >
      {config.label}
    </span>
  );
};
